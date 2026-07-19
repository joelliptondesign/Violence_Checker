"""Deterministic comparison of observed pipeline results to corpus truth."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from src.contracts import PipelineFailureProvenance, PolicyOutcome, ValidationFailureStage
from src.evaluation.contracts import (
    CaseEvaluationResult,
    CaseEvaluationStatus,
    DifferenceClassification,
    DifferenceReasonCode,
    EvaluationCase,
    EvaluationCategory,
    ExpectedField,
    ExpectedSemanticOutcome,
    FailurePattern,
    FieldDifference,
    NonComparableReason,
)
from src.evaluation.run_contracts import ObservedCaseResult


_PROVIDER_FAILURES = {
    PipelineFailureProvenance.PROVIDER_CONFIGURATION,
    PipelineFailureProvenance.PROVIDER_REQUEST,
    PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE,
    PipelineFailureProvenance.PROVIDER_VALIDATION,
}

_SEMANTIC_FIELDS = (
    "violence_present",
    "event_type",
    "actor",
    "target",
    "contact_occurred",
    "injury_mentioned",
    "current_event",
    "intentionality",
    "negated",
    "correction_present",
    "conflicting_information",
    "evidence_text",
    "uncertainty_notes",
)


def _json_value(value: object) -> object:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


def _difference(field: str, expected: object, observed: object, reason: Optional[DifferenceReasonCode] = None) -> Optional[FieldDifference]:
    expected_json = _json_value(expected)
    observed_json = _json_value(observed)
    if expected_json == observed_json:
        return None
    if observed is None and expected is not None:
        classification = DifferenceClassification.OBSERVED_VALUE_MISSING
        reason_code = reason or DifferenceReasonCode.MISSING_OBSERVED_VALUE
    elif expected is None and observed is not None:
        classification = DifferenceClassification.EXPECTED_VALUE_MISSING
        reason_code = reason or DifferenceReasonCode.UNEXPECTED_OBSERVED_VALUE
    else:
        classification = DifferenceClassification.VALUE_MISMATCH
        reason_code = reason or (
            DifferenceReasonCode.COLLECTION_MISMATCH
            if isinstance(expected, (list, tuple)) or isinstance(observed, (list, tuple))
            else DifferenceReasonCode.SCALAR_MISMATCH
        )
    return FieldDifference(
        field=field,
        expected_value=expected_json,
        observed_value=observed_json,
        classification=classification,
        reason_code=reason_code,
        explanation=f"Asserted field {field} differs from the observed pipeline result.",
    )


def _expected_evidence_covered(expected: str, observed: Sequence[str]) -> bool:
    """Return whether exact observed spans cover one expected excerpt."""

    if any(expected in item for item in observed):
        return True
    for start in range(len(observed)):
        joined = ""
        for item in observed[start:]:
            joined = item if not joined else f"{joined} {item}"
            if expected in joined:
                return True
    return False


def _evidence_findings(
    expected: Sequence[str],
    observed: Sequence[str],
    narrative: str,
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Find exact missing coverage and excerpts unsupported by the narrative."""

    missing = tuple(
        item for item in expected if not _expected_evidence_covered(item, observed)
    )
    asserted = set(expected)
    unsupported = tuple(
        item for item in observed if item not in narrative and item not in asserted
    )
    return missing, unsupported


def _evidence_difference(
    expected: Sequence[str],
    observed: Sequence[str],
    narrative: str,
) -> Optional[FieldDifference]:
    missing, unsupported = _evidence_findings(expected, observed, narrative)
    if not missing and not unsupported:
        return None
    details = []
    if missing:
        details.append(f"{len(missing)} expected excerpt(s) lack exact observed coverage")
    if unsupported:
        details.append(f"{len(unsupported)} observed excerpt(s) are absent from the narrative")
    return FieldDifference(
        field="semantic_facts.evidence_text",
        expected_value=list(expected),
        observed_value=list(observed),
        classification=DifferenceClassification.VALUE_MISMATCH,
        reason_code=DifferenceReasonCode.COLLECTION_MISMATCH,
        explanation="; ".join(details) + ".",
    )


def _patterns(
    case: EvaluationCase,
    observed: ObservedCaseResult,
    differences: List[FieldDifference],
) -> List[FailurePattern]:
    paths = {difference.field for difference in differences}
    expected_facts = case.ground_truth.semantic_facts
    observed_facts = observed.pipeline_result.semantic_facts
    primary = case.metadata.primary_category
    selected: set[FailurePattern] = set()

    if primary == EvaluationCategory.HISTORICAL_DISCLOSURE and "semantic_facts.current_event" in paths:
        selected.add(FailurePattern.HISTORICAL_CURRENT_CONFUSION)
    if primary == EvaluationCategory.CORRECTION and paths.intersection(
        {"semantic_facts.correction_present", "semantic_facts.violence_present", "semantic_facts.event_type"}
    ):
        selected.add(FailurePattern.CORRECTION_REVERSAL_FAILURE)
    if primary == EvaluationCategory.CONFLICTING_NARRATIVE and paths.intersection(
        {"semantic_facts.conflicting_information", "semantic_facts.event_type"}
    ):
        selected.add(FailurePattern.CONFLICT_RESOLUTION_FAILURE)
    if primary == EvaluationCategory.VERBAL_THREAT and paths.intersection(
        {"semantic_facts.violence_present", "semantic_facts.event_type"}
    ):
        selected.add(FailurePattern.THREAT_CLASSIFICATION_FAILURE)
    if primary == EvaluationCategory.ACCIDENTAL_CONTACT and paths.intersection(
        {"semantic_facts.violence_present", "semantic_facts.intentionality", "semantic_facts.event_type"}
    ):
        selected.add(FailurePattern.ACCIDENTAL_INTENTIONAL_CONFUSION)
    if primary == EvaluationCategory.NEGATED_EVENT and paths.intersection(
        {"semantic_facts.negated", "semantic_facts.violence_present", "semantic_facts.event_type"}
    ):
        selected.add(FailurePattern.NEGATION_FAILURE)
    if primary == EvaluationCategory.OBJECT_DIRECTED_AGGRESSION and paths.intersection(
        {"semantic_facts.violence_present", "semantic_facts.event_type", "semantic_facts.target"}
    ):
        selected.add(FailurePattern.OBJECT_DIRECTED_INTERPERSONAL_CONFUSION)
    if primary == EvaluationCategory.SELF_DIRECTED_VIOLENCE and paths.intersection(
        {"semantic_facts.violence_present", "semantic_facts.event_type", "semantic_facts.target"}
    ):
        selected.add(FailurePattern.SELF_DIRECTED_INTERPERSONAL_CONFUSION)
    if "semantic_facts.evidence_text" in paths and expected_facts is not None and observed_facts is not None:
        missing, unsupported = _evidence_findings(
            expected_facts.evidence_text,
            observed_facts.evidence_text,
            observed.pipeline_result.normalized_incident.normalized_narrative,
        )
        if missing:
            selected.add(FailurePattern.EVIDENCE_OMISSION)
        if unsupported:
            selected.add(FailurePattern.UNSUPPORTED_EVIDENCE)
    if expected_facts is not None and observed_facts is not None:
        if "semantic_facts.event_type" in paths:
            selected.add(FailurePattern.EVENT_TYPE_DISAGREEMENT)
        if "semantic_facts.uncertainty_notes" in paths:
            selected.add(FailurePattern.UNCERTAINTY_NOTE_DIFFERENCE)
    if any(path.startswith("semantic_facts.") for path in paths):
        selected.add(FailurePattern.SEMANTIC_FIELD_MISMATCH)
    if "validation.failure_stage" in paths:
        selected.add(FailurePattern.VALIDATION_REJECTION)
    if observed.failure_provenance == PipelineFailureProvenance.COMPATIBILITY_CONSTRUCTION:
        selected.add(FailurePattern.COMPATIBILITY_FAILURE)
    elif "compatibility_finding" in paths:
        selected.add(FailurePattern.COMPATIBILITY_DIFFERENCE)
    if any(path.startswith("policy_decision.") for path in paths):
        selected.add(FailurePattern.POLICY_MISMATCH)
    return [pattern for pattern in FailurePattern if pattern in selected]


def compare_case(case: EvaluationCase, observed: ObservedCaseResult) -> CaseEvaluationResult:
    """Compare asserted truth only and classify one observed case deterministically."""

    truth = case.ground_truth
    if observed.failure_provenance in _PROVIDER_FAILURES:
        return CaseEvaluationResult(
            result_id=f"{observed.run_id}:{case.case_id}",
            case_id=case.case_id,
            observed_run_id=observed.run_id,
            status=CaseEvaluationStatus.NON_COMPARABLE,
            field_differences=[],
            failure_patterns=[FailurePattern.PROVIDER_FAILURE],
            non_comparable_reason=NonComparableReason.OBSERVATION_FAILED,
        )

    differences: List[FieldDifference] = []
    observed_success = observed.semantic_status == "success"
    expected_success = truth.semantic_outcome == ExpectedSemanticOutcome.SUCCESS
    semantic_difference = _difference(
        "semantic_outcome",
        expected_success,
        observed_success,
        DifferenceReasonCode.SEMANTIC_SUCCESS_MISMATCH,
    )
    if semantic_difference is not None:
        differences.append(semantic_difference)

    validation = observed.pipeline_result.validation_result
    if expected_success and validation.failure_stage != ValidationFailureStage.NONE:
        validation_difference = _difference(
            "validation.failure_stage",
            ValidationFailureStage.NONE,
            validation.failure_stage,
            DifferenceReasonCode.VALIDATION_STAGE_MISMATCH,
        )
        if validation_difference is not None:
            differences.append(validation_difference)
    elif (
        not expected_success
        and ExpectedField.VALIDATION_STAGE not in truth.intentionally_not_asserted
    ):
        validation_difference = _difference(
            "validation.failure_stage",
            truth.validation_failure_stage,
            validation.failure_stage,
            DifferenceReasonCode.VALIDATION_STAGE_MISMATCH,
        )
        if validation_difference is not None:
            differences.append(validation_difference)

    if expected_success and validation.passed and truth.semantic_facts is not None:
        observed_facts = observed.pipeline_result.semantic_facts
        for field_name in _SEMANTIC_FIELDS:
            if field_name == "evidence_text":
                continue
            expected_value = getattr(truth.semantic_facts, field_name)
            observed_value = getattr(observed_facts, field_name) if observed_facts is not None else None
            difference = _difference(
                f"semantic_facts.{field_name}",
                expected_value,
                observed_value,
            )
            if difference is not None:
                differences.append(difference)

        observed_facts = observed.pipeline_result.semantic_facts
        if observed_facts is not None:
            evidence_difference = _evidence_difference(
                truth.semantic_facts.evidence_text,
                observed_facts.evidence_text,
                observed.pipeline_result.normalized_incident.normalized_narrative,
            )
            if evidence_difference is not None:
                differences.append(evidence_difference)

    compatibility_comparable = (
        validation.passed
        or observed.failure_provenance
        == PipelineFailureProvenance.COMPATIBILITY_CONSTRUCTION
    )
    if (
        ExpectedField.COMPATIBILITY_FINDING not in truth.intentionally_not_asserted
        and compatibility_comparable
    ):
        expected_finding = (
            truth.compatibility_finding.model_dump(mode="json")
            if truth.compatibility_finding is not None
            else None
        )
        observed_finding = (
            observed.pipeline_result.operational_finding.model_dump(mode="json")
            if observed.pipeline_result.operational_finding is not None
            else None
        )
        difference = _difference("compatibility_finding", expected_finding, observed_finding)
        if difference is not None:
            differences.append(difference)

    if ExpectedField.POLICY_DECISION not in truth.intentionally_not_asserted and truth.policy_decision is not None:
        policy_outcome_difference = _difference(
            "policy_decision.outcome",
            truth.policy_decision.outcome,
            observed.pipeline_result.policy_decision.outcome,
            DifferenceReasonCode.POLICY_OUTCOME_MISMATCH,
        )
        if policy_outcome_difference is not None:
            differences.append(policy_outcome_difference)
        policy_reason_difference = _difference(
            "policy_decision.reason_codes",
            truth.policy_decision.reason_codes,
            observed.pipeline_result.policy_decision.reason_codes,
            DifferenceReasonCode.POLICY_REASON_MISMATCH,
        )
        if policy_reason_difference is not None:
            differences.append(policy_reason_difference)

    if not expected_success and ExpectedField.FAILURE_PROVENANCE not in truth.intentionally_not_asserted:
        difference = _difference(
            "failure_provenance",
            truth.failure_provenance,
            observed.failure_provenance,
            DifferenceReasonCode.FAILURE_PROVENANCE_MISMATCH,
        )
        if difference is not None:
            differences.append(difference)

    patterns = _patterns(case, observed, differences)
    pipeline_failed = (
        observed.pipeline_result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED
        or validation.failure_stage in {ValidationFailureStage.SCHEMA, ValidationFailureStage.DOMAIN}
    )
    if pipeline_failed:
        if not patterns:
            patterns = [FailurePattern.PIPELINE_FAILURE]
        status = CaseEvaluationStatus.FAILURE
    elif differences:
        status = CaseEvaluationStatus.PARTIAL_MISMATCH
    else:
        status = CaseEvaluationStatus.MATCH

    return CaseEvaluationResult(
        result_id=f"{observed.run_id}:{case.case_id}",
        case_id=case.case_id,
        observed_run_id=observed.run_id,
        status=status,
        field_differences=differences,
        failure_patterns=patterns,
    )
