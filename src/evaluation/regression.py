"""Deterministic accepted-baseline versus current-run comparison."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Sequence, Tuple

from pydantic import ValidationError

from src.evaluation.baseline import load_baseline_artifact, load_run_artifact
from src.evaluation.contracts import (
    BaselineClassification,
    CaseEvaluationResult,
    CaseEvaluationStatus,
    FailurePattern,
    FieldDifference,
)
from src.evaluation.corpus import REPOSITORY_ROOT, load_corpus
from src.evaluation.regression_contracts import (
    AcceptedBaselineArtifact,
    CaseRegressionResult,
    RegressionArtifact,
    RegressionExecutionSummary,
    RegressionValueChange,
)
from src.evaluation.legacy_artifacts import LegacyArtifact, load_legacy_artifact
from src.evaluation.run_contracts import EvaluationRunArtifact, ObservedCaseResult
from src.evaluation.serialization import canonical_json


REPORTS_ROOT = (REPOSITORY_ROOT / "evaluation" / "reports").resolve()


class RegressionIssueCode(str, Enum):
    OUTPUT_OUTSIDE_REPORTS = "output_outside_reports"
    INVALID_OUTPUT_EXTENSION = "invalid_output_extension"
    ARTIFACT_EXISTS = "artifact_exists"
    ARTIFACT_MISSING = "artifact_missing"
    INVALID_ARTIFACT = "invalid_artifact"
    INCOMPATIBLE_CORPUS = "incompatible_corpus"
    INCOMPATIBLE_SCHEMA = "incompatible_schema"
    INCOMPATIBLE_CASE_SET = "incompatible_case_set"


class RegressionError(ValueError):
    def __init__(self, code: RegressionIssueCode, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code.value}: {message}")


def resolve_report_path(path: str, suffix: str) -> Path:
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else REPOSITORY_ROOT / candidate).resolve()
    try:
        resolved.relative_to(REPORTS_ROOT)
    except ValueError as error:
        raise RegressionError(
            RegressionIssueCode.OUTPUT_OUTSIDE_REPORTS,
            "regression and report artifacts must be under evaluation/reports",
        ) from error
    if resolved.suffix != suffix:
        raise RegressionError(
            RegressionIssueCode.INVALID_OUTPUT_EXTENSION,
            f"artifact must use {suffix} extension",
        )
    return resolved


def _difference_key(difference: FieldDifference) -> str:
    return canonical_json(difference)


def _difference_delta(
    baseline: Sequence[FieldDifference],
    current: Sequence[FieldDifference],
) -> Tuple[Tuple[FieldDifference, ...], Tuple[FieldDifference, ...]]:
    baseline_keys = {_difference_key(item) for item in baseline}
    current_keys = {_difference_key(item) for item in current}
    introduced = tuple(item for item in current if _difference_key(item) not in baseline_keys)
    resolved = tuple(item for item in baseline if _difference_key(item) not in current_keys)
    return introduced, resolved


def _pattern_delta(
    baseline: Sequence[FailurePattern],
    current: Sequence[FailurePattern],
) -> Tuple[Tuple[FailurePattern, ...], Tuple[FailurePattern, ...]]:
    baseline_set = set(baseline)
    current_set = set(current)
    return (
        tuple(pattern for pattern in FailurePattern if pattern in current_set - baseline_set),
        tuple(pattern for pattern in FailurePattern if pattern in baseline_set - current_set),
    )


def _classification(
    baseline: CaseEvaluationResult,
    current: CaseEvaluationResult,
) -> BaselineClassification:
    if (
        baseline.status == CaseEvaluationStatus.NON_COMPARABLE
        or current.status == CaseEvaluationStatus.NON_COMPARABLE
    ):
        return BaselineClassification.INCOMPARABLE
    if baseline.status != CaseEvaluationStatus.MATCH and current.status == CaseEvaluationStatus.MATCH:
        return BaselineClassification.IMPROVED
    if baseline.status == CaseEvaluationStatus.MATCH and current.status != CaseEvaluationStatus.MATCH:
        return BaselineClassification.DEGRADED
    return BaselineClassification.UNCHANGED


def _value_change(baseline: str, current: str) -> RegressionValueChange | None:
    if baseline == current:
        return None
    return RegressionValueChange(baseline_value=baseline, current_value=current)


def _explanation(
    classification: BaselineClassification,
    baseline: CaseEvaluationResult,
    current: CaseEvaluationResult,
    introduced: Sequence[FieldDifference],
    resolved: Sequence[FieldDifference],
) -> str:
    if classification == BaselineClassification.IMPROVED:
        return "The accepted baseline mismatch is resolved and the current result matches asserted ground truth."
    if classification == BaselineClassification.DEGRADED:
        return "The accepted baseline matched asserted ground truth and the current result now has a comparable mismatch."
    if classification == BaselineClassification.INCOMPARABLE:
        return "Provider or infrastructure failure in the accepted or current observation prevents meaningful comparison."
    if baseline.status != CaseEvaluationStatus.MATCH and (introduced or resolved):
        return "The case remains mismatched; changed mismatch evidence is recorded without classifying it as improvement."
    return "The evaluation outcome and asserted-field difference evidence are unchanged."


def _case_regression(
    category: str,
    baseline_evaluation: CaseEvaluationResult,
    current_evaluation: CaseEvaluationResult,
    baseline_observed: ObservedCaseResult,
    current_observed: ObservedCaseResult,
) -> CaseRegressionResult:
    introduced, resolved = _difference_delta(
        baseline_evaluation.field_differences,
        current_evaluation.field_differences,
    )
    patterns_introduced, patterns_resolved = _pattern_delta(
        baseline_evaluation.failure_patterns,
        current_evaluation.failure_patterns,
    )
    classification = _classification(baseline_evaluation, current_evaluation)
    baseline_policy = baseline_observed.pipeline_result.policy_decision.outcome.value
    current_policy = current_observed.pipeline_result.policy_decision.outcome.value
    baseline_validation = baseline_observed.pipeline_result.validation_result.failure_stage.value
    current_validation = current_observed.pipeline_result.validation_result.failure_stage.value
    return CaseRegressionResult(
        case_id=current_evaluation.case_id,
        primary_category=category,
        baseline_outcome=baseline_evaluation.status,
        current_outcome=current_evaluation.status,
        classification=classification,
        field_differences_introduced=introduced,
        field_differences_resolved=resolved,
        baseline_failure_patterns=tuple(baseline_evaluation.failure_patterns),
        current_failure_patterns=tuple(current_evaluation.failure_patterns),
        failure_patterns_introduced=patterns_introduced,
        failure_patterns_resolved=patterns_resolved,
        baseline_policy_outcome=baseline_policy,
        current_policy_outcome=current_policy,
        baseline_validation_stage=baseline_validation,
        current_validation_stage=current_validation,
        policy_outcome_change=_value_change(baseline_policy, current_policy),
        validation_stage_change=_value_change(baseline_validation, current_validation),
        explanation=_explanation(
            classification,
            baseline_evaluation,
            current_evaluation,
            introduced,
            resolved,
        ),
    )


def _change_counts(changes: Sequence[RegressionValueChange | None]) -> Dict[str, int]:
    counts = Counter(
        f"{change.baseline_value}->{change.current_value}"
        for change in changes
        if change is not None
    )
    return {key: counts[key] for key in sorted(counts)}


def _summary(
    regressions: Sequence[CaseRegressionResult],
    current: EvaluationRunArtifact,
) -> RegressionExecutionSummary:
    classification_counts = Counter(item.classification.value for item in regressions)
    by_category: Dict[str, Counter[str]] = {}
    by_pattern: Dict[str, Counter[str]] = {}
    for item in regressions:
        by_category.setdefault(item.primary_category, Counter())[item.classification.value] += 1
        patterns = set(item.failure_patterns_introduced) | set(item.failure_patterns_resolved)
        for pattern in patterns:
            by_pattern.setdefault(pattern.value, Counter())[item.classification.value] += 1
    return RegressionExecutionSummary(
        total_cases=len(regressions),
        improved=classification_counts[BaselineClassification.IMPROVED.value],
        degraded=classification_counts[BaselineClassification.DEGRADED.value],
        unchanged=classification_counts[BaselineClassification.UNCHANGED.value],
        incomparable=classification_counts[BaselineClassification.INCOMPARABLE.value],
        regression_counts_by_category={
            category: {key: by_category[category][key] for key in sorted(by_category[category])}
            for category in sorted(by_category)
        },
        regression_counts_by_failure_pattern={
            pattern: {key: by_pattern[pattern][key] for key in sorted(by_pattern[pattern])}
            for pattern in sorted(by_pattern)
        },
        policy_outcome_changes=_change_counts([item.policy_outcome_change for item in regressions]),
        validation_stage_changes=_change_counts([item.validation_stage_change for item in regressions]),
        provider_failures=current.summary.provider_failure_count,
    )


def compare_artifacts(
    *,
    baseline: AcceptedBaselineArtifact,
    current: EvaluationRunArtifact,
    comparison_id: str,
    comparison_timestamp: datetime,
) -> RegressionArtifact:
    if (baseline.corpus_identity, baseline.corpus_version) != (
        current.corpus_identity,
        current.corpus_version,
    ):
        raise RegressionError(RegressionIssueCode.INCOMPATIBLE_CORPUS, "corpus identity or version differs")
    if baseline.evaluation_schema_version != current.evaluation_schema_version:
        raise RegressionError(RegressionIssueCode.INCOMPATIBLE_SCHEMA, "evaluation schema version differs")
    if (baseline.semantic_schema_identity, baseline.semantic_schema_version) != (
        current.semantic_schema_identity,
        current.semantic_schema_version,
    ):
        raise RegressionError(RegressionIssueCode.INCOMPATIBLE_SCHEMA, "semantic schema identity or version differs")
    if baseline.requested_case_ids != current.requested_case_ids:
        raise RegressionError(RegressionIssueCode.INCOMPATIBLE_CASE_SET, "ordered case identifiers differ")

    corpus_categories = {
        case.case_id: case.metadata.primary_category.value for case in load_corpus().cases
    }
    regressions = tuple(
        _case_regression(category, baseline_evaluation, current_evaluation, baseline_observed, current_observed)
        for category, baseline_evaluation, current_evaluation, baseline_observed, current_observed in zip(
            (corpus_categories[case_id] for case_id in current.requested_case_ids),
            baseline.case_evaluations,
            current.case_evaluations,
            baseline.observed_cases,
            current.observed_cases,
        )
    )
    return RegressionArtifact(
        comparison_id=comparison_id,
        baseline_id=baseline.baseline_id,
        baseline_run_id=baseline.accepted_run_id,
        current_run_id=current.run_id,
        baseline_repository_commit=baseline.repository_commit,
        current_repository_commit=current.repository_commit,
        corpus_identity=current.corpus_identity,
        corpus_version=current.corpus_version,
        evaluation_schema_version=current.evaluation_schema_version,
        semantic_schema_identity=current.semantic_schema_identity,
        semantic_schema_version=current.semantic_schema_version,
        comparison_timestamp=comparison_timestamp,
        requested_case_ids=current.requested_case_ids,
        case_regressions=regressions,
        summary=_summary(regressions, current),
    )


def compare_run(
    *,
    baseline_path: str,
    current_run_path: str,
    comparison_id: str,
    comparison_timestamp: datetime,
    output_path: str,
) -> RegressionArtifact:
    baseline = load_baseline_artifact(baseline_path)
    current = load_run_artifact(current_run_path)
    if isinstance(baseline, LegacyArtifact) or isinstance(current, LegacyArtifact):
        raise RegressionError(
            RegressionIssueCode.INCOMPATIBLE_SCHEMA,
            "legacy and successor artifact families are explicitly incomparable",
        )
    artifact = compare_artifacts(
        baseline=baseline,
        current=current,
        comparison_id=comparison_id,
        comparison_timestamp=comparison_timestamp,
    )
    output = resolve_report_path(output_path, ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8") as handle:
            handle.write(canonical_json(artifact) + "\n")
    except FileExistsError as error:
        raise RegressionError(RegressionIssueCode.ARTIFACT_EXISTS, f"artifact already exists: {output.name}") from error
    return artifact


def load_regression_artifact(path: str):
    source = resolve_report_path(path, ".json")
    if not source.is_file():
        raise RegressionError(RegressionIssueCode.ARTIFACT_MISSING, f"regression artifact not found: {source.name}")
    try:
        raw = source.read_text(encoding="utf-8")
        import json
        if json.loads(raw).get("evaluation_schema_version") == "1.0.0":
            return load_legacy_artifact(source, "comparison")
        return RegressionArtifact.model_validate_json(raw)
    except (OSError, ValidationError, ValueError) as error:
        raise RegressionError(RegressionIssueCode.INVALID_ARTIFACT, "regression artifact is invalid") from error
