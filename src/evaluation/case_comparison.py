"""Deterministic comparison of operational True North expectations and observations."""

from __future__ import annotations

from src.contracts import AssertionStatus, Conduct, Intentionality, TemporalScope, ValidationFailureStage
from src.evaluation.contracts import (
    CaseEvaluationResult, CaseEvaluationStatus, DifferenceClassification,
    DifferenceReasonCode, DoctrineCompliance, EvaluationCase, ExpectedEvidence,
    ExpectedOperationalFact, FailurePattern, FieldDifference, NonComparableReason,
)
from src.evaluation.run_contracts import ObservedCaseResult


def _json(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_json(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def _difference(field: str, expected, observed, reason=DifferenceReasonCode.VALUES_DIFFER):
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
    return FieldDifference(
        field=field, expected_value=_json(expected), observed_value=_json(observed),
        classification=classification, reason_code=reason,
    )


def _operational_facts(validation) -> tuple[ExpectedOperationalFact, ...]:
    envelope = validation.validated_envelope
    if not validation.passed or envelope is None:
        return ()
    return tuple(ExpectedOperationalFact(
        conduct=fact.conduct, direction=fact.direction,
        intentionality=fact.intentionality, temporal_scope=fact.temporal_scope,
        assertion_status=fact.assertion_status, resolution_status=fact.resolution_status,
        uncertainty=tuple(fact.uncertainty),
        evidence=tuple(ExpectedEvidence(excerpt=item.excerpt, supports=tuple(item.supports)) for item in fact.evidence),
    ) for fact in envelope.facts)


def _qualifying(validation) -> tuple[Conduct, ...]:
    if not validation.passed or validation.validated_envelope is None or validation.derived_semantics is None:
        return ()
    active = set(validation.derived_semantics.active_fact_ids)
    values = {
        fact.conduct for fact in validation.validated_envelope.facts
        if fact.fact_id in active and fact.conduct is not None
        and fact.intentionality == Intentionality.INTENTIONAL
        and fact.temporal_scope == TemporalScope.CURRENT
        and fact.assertion_status == AssertionStatus.AFFIRMED
    }
    return tuple(value for value in Conduct if value in values)


def compare_case(case: EvaluationCase, observed: ObservedCaseResult) -> CaseEvaluationResult:
    pipeline = observed.pipeline_result
    validation = pipeline.validation_result
    truth = case.ground_truth
    if observed.semantic_status != "success" and validation.failure_stage == ValidationFailureStage.NOT_RUN:
        return CaseEvaluationResult(
            result_id=f"{observed.run_id}:{case.case_id}", case_id=case.case_id,
            observed_run_id=observed.run_id, status=CaseEvaluationStatus.NON_COMPARABLE,
            non_comparable_reason=NonComparableReason.OBSERVATION_FAILED,
            failure_patterns=[FailurePattern.PROVIDER_FAILURE],
        )

    actual_facts = _operational_facts(validation)
    expected_facts = tuple(fact.model_copy(update={"correction_of_fact": None, "contradiction_group": None}) for fact in truth.operational_facts)
    issue_codes = tuple(item.code for item in validation.schema_validation.issues + validation.domain_validation.issues)
    direction = validation.derived_semantics.incident_direction if validation.derived_semantics else truth.incident_direction
    doctrine = (
        DoctrineCompliance.REJECTED_VIOLATION
        if case.adversarial_condition is not None and not validation.passed
        else DoctrineCompliance.BOUNDED_NOT_PROVABLE
        if case.adversarial_condition is not None
        else DoctrineCompliance.COMPLIANT
    )
    comparisons = (
        ("deterministic_outcome", truth.deterministic_outcome, pipeline.policy_decision.outcome, DifferenceReasonCode.POLICY_OUTCOME_MISMATCH),
        ("processing_status", truth.processing_status, validation.processing_status, DifferenceReasonCode.PROCESSING_STATUS_MISMATCH),
        ("completeness_status", truth.completeness_status, validation.completeness_status, DifferenceReasonCode.COMPLETENESS_STATUS_MISMATCH),
        ("validation_failure_stage", truth.validation_failure_stage, validation.failure_stage, DifferenceReasonCode.VALUES_DIFFER),
        ("validation_issue_codes", truth.validation_issue_codes, issue_codes, DifferenceReasonCode.COLLECTION_MISMATCH),
        ("qualifying_conduct", truth.qualifying_conduct, _qualifying(validation), DifferenceReasonCode.COLLECTION_MISMATCH),
        ("incident_direction", truth.incident_direction, direction, DifferenceReasonCode.SCALAR_MISMATCH),
        ("operational_facts", expected_facts if validation.passed else (), actual_facts, DifferenceReasonCode.COLLECTION_MISMATCH),
        ("doctrine_compliance", truth.doctrine_compliance, doctrine, DifferenceReasonCode.DOCTRINE_COMPLIANCE_MISMATCH),
    )
    differences = [item for field, expected, actual, reason in comparisons if (item := _difference(field, expected, actual, reason))]
    patterns: list[FailurePattern] = []
    fields = {item.field for item in differences}
    if "operational_facts" in fields:
        patterns.append(FailurePattern.OPERATIONAL_FACT_MISMATCH)
        expected_evidence = {e.excerpt for fact in expected_facts for e in fact.evidence}
        actual_evidence = {e.excerpt for fact in actual_facts for e in fact.evidence}
        if expected_evidence - actual_evidence:
            patterns.append(FailurePattern.EVIDENCE_OMISSION)
    if "deterministic_outcome" in fields:
        patterns.append(FailurePattern.POLICY_MISMATCH)
    if "processing_status" in fields:
        patterns.append(FailurePattern.PROCESSING_STATUS_MISMATCH)
    if "completeness_status" in fields:
        patterns.append(FailurePattern.COMPLETENESS_STATUS_MISMATCH)
    if "doctrine_compliance" in fields:
        patterns.append(FailurePattern.DOCTRINE_MISMATCH)
    return CaseEvaluationResult(
        result_id=f"{observed.run_id}:{case.case_id}", case_id=case.case_id,
        observed_run_id=observed.run_id,
        status=CaseEvaluationStatus.MATCH if not differences else CaseEvaluationStatus.PARTIAL_MISMATCH,
        field_differences=differences, failure_patterns=patterns,
    )
