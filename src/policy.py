"""Total deterministic policy over the versioned successor policy view."""

from typing import Optional

from src.contracts import (
    AssertionStatus,
    Completion,
    ConductKind,
    Contact,
    POLICY_CANDIDATE_SCHEMA_IDENTITY,
    POLICY_CANDIDATE_SCHEMA_VERSION,
    PipelineFailureProvenance,
    PolicyCandidateView,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    UncertaintyDimension,
    ValidatedSemanticEnvelope,
)


POLICY_ID = "violence_checker_write_disposition"
POLICY_VERSION = "2.0.0"

_FAILURE_REASONS = {
    PipelineFailureProvenance.INPUT_VALIDATION: PolicyReasonCode.INPUT_VALIDATION_FAILED,
    PipelineFailureProvenance.PROVIDER_CONFIGURATION: PolicyReasonCode.PROVIDER_CONFIGURATION_FAILED,
    PipelineFailureProvenance.PROVIDER_REQUEST: PolicyReasonCode.PROVIDER_REQUEST_FAILED,
    PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE: PolicyReasonCode.PROVIDER_STRUCTURED_RESPONSE_FAILED,
    PipelineFailureProvenance.PROVIDER_VALIDATION: PolicyReasonCode.PROVIDER_VALIDATION_FAILED,
    PipelineFailureProvenance.SCHEMA_VALIDATION: PolicyReasonCode.SCHEMA_VALIDATION_FAILED,
    PipelineFailureProvenance.DOMAIN_VALIDATION: PolicyReasonCode.DOMAIN_VALIDATION_FAILED,
    PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT: PolicyReasonCode.UNSUPPORTED_POLICY_INPUT,
}


def _decision(
    outcome: PolicyOutcome,
    reason_codes: list[PolicyReasonCode],
    explanation: str,
    failure_provenance: Optional[PipelineFailureProvenance] = None,
) -> PolicyDecision:
    return PolicyDecision(
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        outcome=outcome,
        reason_codes=reason_codes,
        explanation=explanation,
        failure_provenance=failure_provenance,
    )


def failed_policy_decision(failure: PipelineFailureProvenance) -> PolicyDecision:
    if not isinstance(failure, PipelineFailureProvenance):
        failure = PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT
    return _decision(
        PolicyOutcome.WRITE_FAILED,
        [_FAILURE_REASONS[failure]],
        "An explicit pipeline failure prevents an admissible application write representation.",
        failure,
    )


def _supported_candidate(candidate: PolicyCandidateView, incident_id: str) -> bool:
    return (
        candidate.schema_identity == POLICY_CANDIDATE_SCHEMA_IDENTITY
        and candidate.schema_version == POLICY_CANDIDATE_SCHEMA_VERSION
        and candidate.incident_id == incident_id
    )


def _has_material_current_interpersonal_uncertainty(validated: ValidatedSemanticEnvelope) -> bool:
    """Return whether scoped uncertainty can still change the violence disposition."""
    candidate = validated.policy_candidate
    uncertainty_ids = set(candidate.active_current_interpersonal_uncertainties)
    if not uncertainty_ids:
        return False
    propositions = {item.proposition_id: item for item in validated.envelope.propositions}
    detected_ids = set(candidate.active_current_interpersonal_violence)
    for uncertainty in validated.envelope.uncertainties:
        if uncertainty.uncertainty_id not in uncertainty_ids:
            continue
        proposition = propositions[uncertainty.proposition_ref]
        explicit_completed_contact = (
            uncertainty.dimension == UncertaintyDimension.INTENTIONALITY
            and proposition.proposition_id in detected_ids
            and proposition.assertion_status == AssertionStatus.AFFIRMED
            and proposition.conduct_kind == ConductKind.PHYSICAL_CONDUCT
            and proposition.completion == Completion.COMPLETED
            and proposition.contact == Contact.OCCURRED
        )
        if not explicit_completed_contact:
            return True
    return False


def evaluate_policy(
    *,
    validated: Optional[ValidatedSemanticEnvelope] = None,
    failure: Optional[PipelineFailureProvenance] = None,
) -> PolicyDecision:
    """Enumerate every admissible state: failure, uncertainty, detected, otherwise not detected."""
    if failure is not None:
        return failed_policy_decision(failure)
    if not isinstance(validated, ValidatedSemanticEnvelope):
        return failed_policy_decision(PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT)
    candidate = validated.policy_candidate
    if not _supported_candidate(candidate, validated.envelope.incident_id):
        return failed_policy_decision(PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT)

    reasons: list[PolicyReasonCode] = []
    if candidate.active_conflict_relationships:
        reasons.append(PolicyReasonCode.CONFLICTING_INFORMATION)
    if (
        candidate.active_current_interpersonal_uncertain
        or _has_material_current_interpersonal_uncertainty(validated)
        or candidate.active_potential_interpersonal_uncertain
    ):
        reasons.append(PolicyReasonCode.SCOPED_SEMANTIC_UNCERTAINTY)
    if reasons:
        return _decision(
            PolicyOutcome.WRITE_UNCERTAIN,
            reasons,
            "Validated active current interpersonal propositions contain bounded uncertainty.",
        )

    if candidate.active_current_interpersonal_violence:
        return _decision(
            PolicyOutcome.WRITE_DETECTED,
            [PolicyReasonCode.AFFIRMED_CURRENT_INTERPERSONAL_VIOLENCE],
            "Validated active propositions affirm current interpersonal violence or threat.",
        )

    return _decision(
        PolicyOutcome.WRITE_NOT_DETECTED,
        [PolicyReasonCode.NO_ACTIVE_CURRENT_INTERPERSONAL_VIOLENCE],
        "No validated active proposition affirms current interpersonal violence or threat.",
    )
