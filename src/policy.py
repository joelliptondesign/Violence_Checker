"""Total deterministic True North policy over validated incident facts."""

from typing import Optional

from src.contracts import (
    AssertionStatus,
    CompletenessStatus,
    DerivedSemanticView,
    Intentionality,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    ProcessingStatus,
    TemporalScope,
    TrueNorthSemanticEnvelope,
    UncertaintyDimension,
)
from src.semantic_derivation import derive_semantic_views, has_unresolved_semantic_content


POLICY_ID = "violence_checker_true_north_classification"
POLICY_VERSION = "1.0.0"

_MATERIAL_DIMENSIONS = {
    UncertaintyDimension.CONDUCT,
    UncertaintyDimension.INTENTIONALITY,
    UncertaintyDimension.TEMPORAL_SCOPE,
    UncertaintyDimension.ASSERTION_STATUS,
}
_PROCESSING_FAILURE_REASONS = {
    ProcessingStatus.PROVIDER_FAILURE: PolicyReasonCode.PROVIDER_FAILURE,
    ProcessingStatus.SCHEMA_FAILURE: PolicyReasonCode.SCHEMA_FAILURE,
    ProcessingStatus.VALIDATION_FAILURE: PolicyReasonCode.VALIDATION_FAILURE,
    ProcessingStatus.PIPELINE_FAILURE: PolicyReasonCode.PIPELINE_FAILURE,
}


def _decision(
    outcome: PolicyOutcome,
    reason_codes: list[PolicyReasonCode],
    explanation: str,
) -> PolicyDecision:
    return PolicyDecision(
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        outcome=outcome,
        reason_codes=reason_codes,
        explanation=explanation,
    )


def _unable(reason: PolicyReasonCode, explanation: str) -> PolicyDecision:
    return _decision(PolicyOutcome.UNABLE_TO_DETERMINE, [reason], explanation)


def _could_change_classification(fact) -> bool:
    return (
        fact.intentionality != Intentionality.ACCIDENTAL
        and fact.temporal_scope != TemporalScope.HISTORICAL
        and fact.assertion_status != AssertionStatus.DENIED
    )


def _material_uncertainty_fact_ids(envelope, active_ids: set[str]) -> set[str]:
    return {
        fact.fact_id
        for fact in envelope.facts
        if fact.fact_id in active_ids
        and _could_change_classification(fact)
        and bool(_MATERIAL_DIMENSIONS.intersection(fact.uncertainty))
    }


def _material_contradiction_group_ids(envelope, derived, active_ids: set[str]) -> set[str]:
    fact_by_id = {fact.fact_id: fact for fact in envelope.facts}
    return {
        group.contradiction_group
        for group in derived.contradiction_groups
        if any(
            fact_id in active_ids and _could_change_classification(fact_by_id[fact_id])
            for fact_id in group.fact_ids
        )
    }


def evaluate_policy(
    *,
    validated: Optional[TrueNorthSemanticEnvelope],
    processing_status: ProcessingStatus,
    completeness_status: CompletenessStatus,
    derived: Optional[DerivedSemanticView],
) -> PolicyDecision:
    """Apply all four doctrinal outcomes without provider or presentation authority."""
    if not isinstance(processing_status, ProcessingStatus):
        return _unable(
            PolicyReasonCode.MALFORMED_SEMANTIC_INPUT,
            "Repository processing status is missing or unsupported.",
        )
    if processing_status != ProcessingStatus.SUCCESSFUL_ANALYSIS:
        return _unable(
            _PROCESSING_FAILURE_REASONS[processing_status],
            "Repository processing did not produce admissible semantic facts for deterministic classification.",
        )
    if not isinstance(completeness_status, CompletenessStatus):
        return _unable(
            PolicyReasonCode.MALFORMED_SEMANTIC_INPUT,
            "Repository completeness status is missing or unsupported.",
        )
    if completeness_status == CompletenessStatus.INCOMPLETE_ANALYSIS:
        return _unable(
            PolicyReasonCode.INCOMPLETE_ANALYSIS,
            "Repository analysis is incomplete and cannot support deterministic classification.",
        )
    if not isinstance(validated, TrueNorthSemanticEnvelope) or not isinstance(derived, DerivedSemanticView):
        return _unable(
            PolicyReasonCode.MALFORMED_SEMANTIC_INPUT,
            "Successful processing requires validated facts and deterministic semantic views.",
        )

    expected_derived = derive_semantic_views(validated)
    if derived != expected_derived or derived.incident_id != validated.incident_id:
        return _unable(
            PolicyReasonCode.MALFORMED_SEMANTIC_INPUT,
            "Deterministic semantic views do not match the validated incident facts.",
        )
    expected_completeness = (
        CompletenessStatus.UNRESOLVED_SEMANTIC_CONTENT
        if has_unresolved_semantic_content(validated, derived)
        else CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS
    )
    if completeness_status != expected_completeness:
        return _unable(
            PolicyReasonCode.MALFORMED_SEMANTIC_INPUT,
            "Repository completeness status does not match validated semantic content.",
        )

    active_ids = set(derived.active_fact_ids)
    detected_fact_ids = [
        fact.fact_id
        for fact in validated.facts
        if fact.fact_id in active_ids
        and fact.conduct is not None
        and fact.intentionality == Intentionality.INTENTIONAL
        and fact.temporal_scope == TemporalScope.CURRENT
        and fact.assertion_status == AssertionStatus.AFFIRMED
    ]
    if detected_fact_ids:
        return _decision(
            PolicyOutcome.VIOLENCE_DETECTED,
            [PolicyReasonCode.QUALIFYING_CURRENT_VIOLENCE],
            "At least one active fact affirms intentional current qualifying conduct.",
        )

    material_uncertainty = _material_uncertainty_fact_ids(validated, active_ids)
    material_contradictions = _material_contradiction_group_ids(validated, derived, active_ids)
    if material_uncertainty or material_contradictions:
        reasons: list[PolicyReasonCode] = []
        if material_contradictions:
            reasons.append(PolicyReasonCode.UNRESOLVED_CONTRADICTION)
        if material_uncertainty:
            reasons.append(PolicyReasonCode.MATERIAL_SEMANTIC_UNCERTAINTY)
        return _decision(
            PolicyOutcome.UNCERTAIN,
            reasons,
            "Admissible active facts preserve unresolved semantic content that can change classification.",
        )

    return _decision(
        PolicyOutcome.NO_VIOLENCE_DETECTED,
        [PolicyReasonCode.NO_QUALIFYING_CURRENT_VIOLENCE],
        "Complete admissible analysis contains no active affirmed intentional current qualifying conduct.",
    )
