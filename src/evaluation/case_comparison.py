"""Identifier-addressed deterministic successor case comparison."""

from __future__ import annotations

from typing import Iterable

from src.contracts import PolicyOutcome, ValidationFailureStage, ValidationIssueCode
from src.evaluation.contracts import (
    CaseEvaluationResult,
    CaseEvaluationStatus,
    DifferenceClassification,
    DifferenceReasonCode,
    EvaluationCase,
    ExpectedSemanticOutcome,
    FailurePattern,
    FieldDifference,
    NonComparableReason,
)
from src.evaluation.run_contracts import ObservedCaseResult


def _difference(path: str, expected: object, observed: object) -> FieldDifference | None:
    if expected == observed:
        return None
    if observed is None:
        classification = DifferenceClassification.OBSERVED_VALUE_MISSING
        reason = DifferenceReasonCode.MISSING_OBSERVED_VALUE
    elif expected is None:
        classification = DifferenceClassification.EXPECTED_VALUE_MISSING
        reason = DifferenceReasonCode.UNEXPECTED_OBSERVED_VALUE
    else:
        classification = DifferenceClassification.VALUE_MISMATCH
        reason = DifferenceReasonCode.COLLECTION_MISMATCH if isinstance(expected, (list, tuple)) else DifferenceReasonCode.SCALAR_MISMATCH
    return FieldDifference(
        field=path,
        expected_value=expected,
        observed_value=observed,
        classification=classification,
        reason_code=reason,
    )


def _subject_differences(
    collection: str,
    identifier_field: str,
    expected_items: Iterable[object],
    observed_items: Iterable[object],
) -> list[FieldDifference]:
    expected = {getattr(item, identifier_field): item.model_dump(mode="json") for item in expected_items}
    observed = {getattr(item, identifier_field): item.model_dump(mode="json") for item in observed_items}
    differences: list[FieldDifference] = []
    for identifier in sorted(set(expected) | set(observed)):
        expected_value = expected.get(identifier)
        observed_value = observed.get(identifier)
        if expected_value is None or observed_value is None:
            item = _difference(f"{collection}[{identifier}]", expected_value, observed_value)
            if item:
                differences.append(item)
            continue
        for field in sorted(set(expected_value) | set(observed_value)):
            item = _difference(
                f"{collection}[{identifier}].{field}",
                expected_value.get(field),
                observed_value.get(field),
            )
            if item:
                differences.append(item)
    return differences


def _has_exact_ordered_coverage(expected_text: str, observed_texts: list[str]) -> bool:
    """Require exact containment or gap-free ordered segmentation of expected evidence."""
    if any(expected_text in observed for observed in observed_texts):
        return True
    intervals: list[tuple[int, int]] = []
    for observed in observed_texts:
        start = expected_text.find(observed)
        if start >= 0:
            intervals.append((start, start + len(observed)))
    if not intervals:
        return False
    covered = 0
    for start, end in sorted(intervals):
        if start > covered:
            return False
        covered = max(covered, end)
    return covered == len(expected_text)


def compare_case(case: EvaluationCase, observed: ObservedCaseResult) -> CaseEvaluationResult:
    truth = case.ground_truth
    pipeline = observed.pipeline_result
    if observed.failure_provenance is not None and pipeline.validation_result.failure_stage == ValidationFailureStage.NOT_RUN:
        return CaseEvaluationResult(
            result_id=f"{observed.run_id}:{case.case_id}",
            case_id=case.case_id,
            observed_run_id=observed.run_id,
            status=CaseEvaluationStatus.NON_COMPARABLE,
            non_comparable_reason=NonComparableReason.OBSERVATION_FAILED,
            failure_patterns=[FailurePattern.PROVIDER_FAILURE],
        )

    if truth.semantic_outcome == ExpectedSemanticOutcome.FAILURE:
        differences: list[FieldDifference] = []
        if truth.validation_failure_stage is not None:
            item = _difference(
                "validation.failure_stage",
                truth.validation_failure_stage.value,
                pipeline.validation_result.failure_stage.value,
            )
            if item:
                differences.append(item)
        if truth.failure_provenance is not None:
            item = _difference(
                "failure_provenance",
                truth.failure_provenance.value,
                pipeline.policy_decision.failure_provenance.value
                if pipeline.policy_decision.failure_provenance
                else None,
            )
            if item:
                differences.append(item)
        if truth.policy_decision is not None:
            item = _difference(
                "policy.outcome",
                truth.policy_decision.outcome.value,
                pipeline.policy_decision.outcome.value,
            )
            if item:
                differences.append(item)
        return CaseEvaluationResult(
            result_id=f"{observed.run_id}:{case.case_id}",
            case_id=case.case_id,
            observed_run_id=observed.run_id,
            status=CaseEvaluationStatus.MATCH if not differences else CaseEvaluationStatus.PARTIAL_MISMATCH,
            field_differences=differences,
            failure_patterns=([] if not differences else [FailurePattern.VALIDATION_FAILURE]),
        )

    if pipeline.validation_result.failure_stage != ValidationFailureStage.NONE:
        patterns = [FailurePattern.VALIDATION_FAILURE]
        issues = (
            pipeline.validation_result.domain_validation.issues
            if pipeline.validation_result.failure_stage == ValidationFailureStage.DOMAIN
            else pipeline.validation_result.schema_validation.issues
        )
        if any(issue.code == ValidationIssueCode.EVIDENCE_NOT_CONTAINED for issue in issues):
            patterns.append(FailurePattern.UNSUPPORTED_EVIDENCE)
        return CaseEvaluationResult(
            result_id=f"{observed.run_id}:{case.case_id}",
            case_id=case.case_id,
            observed_run_id=observed.run_id,
            status=CaseEvaluationStatus.FAILURE,
            failure_patterns=patterns,
        )

    expected = truth.semantic_envelope
    actual = pipeline.semantic_envelope
    expected_derived = truth.expected_derived
    actual_derived = pipeline.derived_semantics
    if expected is None or expected_derived is None or actual is None or actual_derived is None:
        return CaseEvaluationResult(
            result_id=f"{observed.run_id}:{case.case_id}",
            case_id=case.case_id,
            observed_run_id=observed.run_id,
            status=CaseEvaluationStatus.FAILURE,
            failure_patterns=[FailurePattern.MISSING_OBSERVATION],
        )

    differences: list[FieldDifference] = []
    for path, expected_value, observed_value in (
        ("semantic.schema_identity", expected.schema_identity, actual.schema_identity),
        ("semantic.schema_version", expected.schema_version, actual.schema_version),
        ("semantic.incident_id", expected.incident_id, actual.incident_id),
    ):
        item = _difference(path, expected_value, observed_value)
        if item:
            differences.append(item)
    for collection, identifier in (
        ("entities", "entity_id"),
        ("propositions", "proposition_id"),
        ("relationships", "relationship_id"),
        ("uncertainties", "uncertainty_id"),
        ("evidence_excerpts", "evidence_id"),
        ("evidence_supports", "support_id"),
    ):
        differences.extend(_subject_differences(collection, identifier, getattr(expected, collection), getattr(actual, collection)))
    differences.extend(_subject_differences("derived.propositions", "proposition_id", expected_derived.propositions, actual_derived.propositions))
    item = _difference("derived.active_proposition_ids", expected_derived.active_proposition_ids, actual_derived.active_proposition_ids)
    if item:
        differences.append(item)
    if truth.policy_decision is not None:
        item = _difference("policy.outcome", truth.policy_decision.outcome.value, pipeline.policy_decision.outcome.value)
        if item:
            differences.append(item)
        item = _difference(
            "policy.reason_codes",
            [value.value for value in truth.policy_decision.reason_codes],
            [value.value for value in pipeline.policy_decision.reason_codes],
        )
        if item:
            differences.append(item)

    patterns: list[FailurePattern] = []
    if any(item.field.startswith(("entities", "propositions", "relationships", "uncertainties", "evidence", "derived")) for item in differences):
        patterns.append(FailurePattern.SEMANTIC_FIELD_MISMATCH)
    observed_evidence_texts = [item.text for item in actual.evidence_excerpts]
    if any(
        not _has_exact_ordered_coverage(item.text, observed_evidence_texts)
        for item in expected.evidence_excerpts
    ):
        patterns.append(FailurePattern.EVIDENCE_OMISSION)
    if any(item.field.startswith("policy") for item in differences):
        patterns.append(FailurePattern.POLICY_MISMATCH)
    status = CaseEvaluationStatus.MATCH if not differences else CaseEvaluationStatus.PARTIAL_MISMATCH
    return CaseEvaluationResult(
        result_id=f"{observed.run_id}:{case.case_id}",
        case_id=case.case_id,
        observed_run_id=observed.run_id,
        status=status,
        field_differences=differences,
        failure_patterns=patterns,
    )
