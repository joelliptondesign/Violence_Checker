"""Non-interactive evaluation runner over the governed application pipeline."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

from src.app_logic import AnalysisResult, run_analysis
from src.contract_adapters import pipeline_result_from_analysis
from src.contracts import (
    InputValidationResult,
    PipelineFailureProvenance,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    ValidationFailureStage,
)
from src.evaluation.case_comparison import compare_case
from src.evaluation.contracts import CaseEvaluationResult, CaseEvaluationStatus, EvaluationCase, FailurePattern
from src.evaluation.corpus import EVALUATION_SCHEMA_VERSION, REPOSITORY_ROOT, CorpusDocument, load_corpus
from src.evaluation.run_contracts import (
    EvaluationExecutionSummary,
    EvaluationRunArtifact,
    EvaluationRunConfiguration,
    EvaluationRunnerMode,
    ObservedCaseResult,
    ObservedPipelineComparison,
    RunArtifactStatus,
)
from src.evaluation.serialization import canonical_json
from src.models import Incident


RUNS_ROOT = REPOSITORY_ROOT / "evaluation" / "runs"


class RunnerIssueCode(str, Enum):
    UNKNOWN_CASE_IDENTIFIER = "unknown_case_identifier"
    DUPLICATE_CASE_IDENTIFIER = "duplicate_case_identifier"
    DETERMINISTIC_EXECUTOR_REQUIRED = "deterministic_executor_required"
    EXECUTOR_NOT_ALLOWED = "executor_not_allowed"
    OUTPUT_OUTSIDE_RUNS = "output_outside_runs"
    INVALID_OUTPUT_EXTENSION = "invalid_output_extension"
    ARTIFACT_EXISTS = "artifact_exists"
    PIPELINE_RESULT_UNAVAILABLE = "pipeline_result_unavailable"


class RunnerError(ValueError):
    def __init__(self, code: RunnerIssueCode, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code.value}: {message}")


SemanticExecutor = Callable[[Incident], object]


def _resolve_output_path(output_path: str) -> Path:
    candidate = Path(output_path)
    resolved = (candidate if candidate.is_absolute() else REPOSITORY_ROOT / candidate).resolve()
    try:
        resolved.relative_to(RUNS_ROOT.resolve())
    except ValueError as error:
        raise RunnerError(
            RunnerIssueCode.OUTPUT_OUTSIDE_RUNS,
            "run artifacts must be written under evaluation/runs",
        ) from error
    if resolved.suffix != ".json":
        raise RunnerError(
            RunnerIssueCode.INVALID_OUTPUT_EXTENSION,
            "run artifact output must use .json extension",
        )
    return resolved


def select_cases(
    corpus: CorpusDocument,
    requested_case_ids: Sequence[str],
) -> Tuple[EvaluationCase, ...]:
    """Validate selection before execution and return canonical corpus order."""

    if len(requested_case_ids) != len(set(requested_case_ids)):
        raise RunnerError(
            RunnerIssueCode.DUPLICATE_CASE_IDENTIFIER,
            "requested case identifiers must not contain duplicates",
        )
    available = {case.case_id: case for case in corpus.cases}
    unknown = sorted(set(requested_case_ids) - set(available))
    if unknown:
        raise RunnerError(
            RunnerIssueCode.UNKNOWN_CASE_IDENTIFIER,
            f"unknown case identifiers: {unknown}",
        )
    if not requested_case_ids:
        return tuple(corpus.cases)
    selected = set(requested_case_ids)
    return tuple(case for case in corpus.cases if case.case_id in selected)


def validate_run_configuration(
    configuration: EvaluationRunConfiguration,
    corpus: Optional[CorpusDocument] = None,
) -> Tuple[EvaluationCase, ...]:
    """Validate selection and output boundary without semantic execution."""

    loaded = corpus or load_corpus()
    selected = select_cases(loaded, configuration.requested_case_ids)
    _resolve_output_path(configuration.output_path)
    return selected


def _observed_comparison(analysis: AnalysisResult) -> ObservedPipelineComparison:
    comparison = analysis.comparison
    return ObservedPipelineComparison(
        semantic_validation_status=comparison.semantic_validation_status,
        classification_alignment=comparison.classification_alignment,
        material_difference_detected=comparison.material_difference_detected,
        divergence_observations=tuple(comparison.divergence_observations),
        semantic_enrichment_observations=tuple(comparison.semantic_enrichment_observations),
        display_status=comparison.display_status,
        observations=tuple(comparison.observations),
    )


def _execute_case(
    case: EvaluationCase,
    configuration: EvaluationRunConfiguration,
    semantic_executor: Optional[SemanticExecutor],
) -> ObservedCaseResult:
    incident = Incident(incident_id=case.case_id, narrative=case.narrative)
    if configuration.execution_mode == EvaluationRunnerMode.DETERMINISTIC_TEST:
        result = run_analysis(incident, extractor=semantic_executor)
    else:
        result = run_analysis(incident)
    if isinstance(result, InputValidationResult) or not isinstance(result, AnalysisResult):
        raise RunnerError(
            RunnerIssueCode.PIPELINE_RESULT_UNAVAILABLE,
            f"governed pipeline did not produce AnalysisResult for {case.case_id}",
        )
    pipeline = pipeline_result_from_analysis(result)
    return ObservedCaseResult(
        case_id=case.case_id,
        run_id=configuration.run_id,
        semantic_status=result.semantic_result.status.value,
        semantic_failure_message=result.semantic_result.failure_message,
        failure_provenance=result.policy_decision.failure_provenance,
        pipeline_result=pipeline,
        pipeline_comparison=_observed_comparison(result),
    )


def _summary(
    cases: Sequence[EvaluationCase],
    observed: Sequence[ObservedCaseResult],
    evaluations: Sequence[CaseEvaluationResult],
) -> EvaluationExecutionSummary:
    status_counts = Counter(item.status.value for item in evaluations)
    pattern_counts = Counter(
        pattern.value for item in evaluations for pattern in item.failure_patterns
    )
    category_counts = Counter(case.metadata.primary_category.value for case in cases)
    outcomes_by_category: dict[str, dict[str, int]] = {}
    for case, evaluation in zip(cases, evaluations):
        category = case.metadata.primary_category.value
        outcomes_by_category.setdefault(category, {})
        outcomes_by_category[category][evaluation.status.value] = (
            outcomes_by_category[category].get(evaluation.status.value, 0) + 1
        )
    provider_failures = sum(
        item.failure_provenance
        in {
            PipelineFailureProvenance.PROVIDER_CONFIGURATION,
            PipelineFailureProvenance.PROVIDER_REQUEST,
            PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE,
            PipelineFailureProvenance.PROVIDER_VALIDATION,
        }
        for item in observed
    )
    validation_rejections = sum(
        item.pipeline_result.validation_result.failure_stage
        in {ValidationFailureStage.SCHEMA, ValidationFailureStage.DOMAIN}
        for item in observed
    )
    policy_mismatches = sum(
        FailurePattern.POLICY_MISMATCH in item.failure_patterns for item in evaluations
    )
    return EvaluationExecutionSummary(
        requested_cases=len(cases),
        executed_cases=len(observed),
        match_count=status_counts[CaseEvaluationStatus.MATCH.value],
        partial_mismatch_count=status_counts[CaseEvaluationStatus.PARTIAL_MISMATCH.value],
        failure_count=status_counts[CaseEvaluationStatus.FAILURE.value],
        non_comparable_count=status_counts[CaseEvaluationStatus.NON_COMPARABLE.value],
        provider_failure_count=provider_failures,
        validation_rejection_count=validation_rejections,
        policy_mismatch_count=policy_mismatches,
        failure_pattern_counts={key: pattern_counts[key] for key in sorted(pattern_counts)},
        cases_by_primary_category={key: category_counts[key] for key in sorted(category_counts)},
        outcomes_by_primary_category={
            category: {
                outcome: outcomes_by_category[category][outcome]
                for outcome in sorted(outcomes_by_category[category])
            }
            for category in sorted(outcomes_by_category)
        },
    )


def build_run_artifact(
    configuration: EvaluationRunConfiguration,
    corpus: CorpusDocument,
    cases: Sequence[EvaluationCase],
    observed: Sequence[ObservedCaseResult],
    evaluations: Sequence[CaseEvaluationResult],
) -> EvaluationRunArtifact:
    return EvaluationRunArtifact(
        evaluation_schema_version=EVALUATION_SCHEMA_VERSION,
        semantic_schema_identity=SEMANTIC_SCHEMA_IDENTITY,
        semantic_schema_version=SEMANTIC_SCHEMA_VERSION,
        corpus_identity=corpus.corpus_identity,
        corpus_version=corpus.corpus_version,
        run_id=configuration.run_id,
        execution_mode=configuration.execution_mode,
        repository_commit=configuration.repository_commit,
        model_identifier=configuration.model_identifier,
        extraction_configuration_identity=configuration.extraction_configuration_identity,
        run_timestamp=configuration.run_timestamp,
        requested_case_ids=tuple(case.case_id for case in cases),
        observed_cases=tuple(observed),
        case_evaluations=tuple(evaluations),
        summary=_summary(cases, observed, evaluations),
        status=RunArtifactStatus.COMPLETE,
    )


def write_run_artifact(
    artifact: EvaluationRunArtifact,
    output_path: str,
    *,
    overwrite: bool = False,
) -> Path:
    target = _resolve_output_path(output_path)
    if target.exists() and not overwrite:
        raise RunnerError(RunnerIssueCode.ARTIFACT_EXISTS, f"artifact already exists: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical_json(artifact) + "\n", encoding="utf-8")
    return target


def run_evaluation(
    configuration: EvaluationRunConfiguration,
    *,
    semantic_executor: Optional[SemanticExecutor] = None,
    write_artifact: bool = True,
) -> EvaluationRunArtifact:
    """Run selected corpus cases through the complete governed pipeline."""

    if (
        configuration.execution_mode == EvaluationRunnerMode.DETERMINISTIC_TEST
        and semantic_executor is None
    ):
        raise RunnerError(
            RunnerIssueCode.DETERMINISTIC_EXECUTOR_REQUIRED,
            "deterministic_test mode requires an explicit semantic executor",
        )
    if configuration.execution_mode == EvaluationRunnerMode.LIVE_PROVIDER and semantic_executor is not None:
        raise RunnerError(
            RunnerIssueCode.EXECUTOR_NOT_ALLOWED,
            "live_provider mode uses only the repository semantic extractor",
        )
    corpus = load_corpus()
    cases = validate_run_configuration(configuration, corpus)
    observed = tuple(
        _execute_case(case, configuration, semantic_executor) for case in cases
    )
    evaluations = tuple(
        compare_case(case, observation) for case, observation in zip(cases, observed)
    )
    artifact = build_run_artifact(configuration, corpus, cases, observed, evaluations)
    if write_artifact:
        write_run_artifact(
            artifact,
            configuration.output_path,
            overwrite=configuration.overwrite,
        )
    return artifact


def _parse_timestamp(value: Optional[str]) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include a timezone")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the synthetic evaluation corpus.")
    parser.add_argument("command", choices=("validate", "run"))
    parser.add_argument("--mode", required=True, choices=tuple(mode.value for mode in EvaluationRunnerMode))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repository-commit", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--model")
    parser.add_argument("--config-identity")
    parser.add_argument("--timestamp")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        configuration = EvaluationRunConfiguration(
            run_id=args.run_id,
            execution_mode=EvaluationRunnerMode(args.mode),
            repository_commit=args.repository_commit,
            model_identifier=args.model,
            extraction_configuration_identity=args.config_identity,
            run_timestamp=_parse_timestamp(args.timestamp),
            requested_case_ids=tuple(args.case),
            output_path=args.output,
            overwrite=args.overwrite,
        )
        selected = validate_run_configuration(configuration)
        if args.command == "validate":
            print(json.dumps({"case_count": len(selected), "mode": args.mode, "status": "valid"}, sort_keys=True))
            return 0
        if configuration.execution_mode != EvaluationRunnerMode.LIVE_PROVIDER:
            raise RunnerError(
                RunnerIssueCode.DETERMINISTIC_EXECUTOR_REQUIRED,
                "CLI deterministic_test execution requires a semantic executor supplied through code",
            )
        artifact = run_evaluation(configuration)
        print(canonical_json(artifact.summary))
        return 0
    except (RunnerError, ValueError, OSError) as error:
        code = error.code.value if isinstance(error, RunnerError) else "invalid_configuration"
        print(json.dumps({"code": code, "message": str(error), "status": "failed"}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
