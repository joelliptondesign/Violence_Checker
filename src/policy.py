"""Deterministic application write-disposition policy.

The policy represents admissible findings inside this demonstration. It does not
make clinical, legal, safety, hospital workflow, or real Salesforce decisions.
"""

from typing import Optional

from src.contracts import (
    PipelineFailureProvenance,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    ValidatedSemanticFacts,
)
from src.models import Intentionality, ViolenceEventType, ViolenceFinding


POLICY_ID = "violence_checker_write_disposition"
POLICY_VERSION = "1.0.1"

_FAILURE_REASONS = {
    PipelineFailureProvenance.INPUT_VALIDATION: PolicyReasonCode.INPUT_VALIDATION_FAILED,
    PipelineFailureProvenance.PROVIDER_CONFIGURATION: PolicyReasonCode.PROVIDER_CONFIGURATION_FAILED,
    PipelineFailureProvenance.PROVIDER_REQUEST: PolicyReasonCode.PROVIDER_REQUEST_FAILED,
    PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE: PolicyReasonCode.PROVIDER_STRUCTURED_RESPONSE_FAILED,
    PipelineFailureProvenance.PROVIDER_VALIDATION: PolicyReasonCode.PROVIDER_VALIDATION_FAILED,
    PipelineFailureProvenance.SCHEMA_VALIDATION: PolicyReasonCode.SCHEMA_VALIDATION_FAILED,
    PipelineFailureProvenance.DOMAIN_VALIDATION: PolicyReasonCode.DOMAIN_VALIDATION_FAILED,
    PipelineFailureProvenance.COMPATIBILITY_CONSTRUCTION: (
        PolicyReasonCode.COMPATIBILITY_CONSTRUCTION_FAILED
    ),
    PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT: PolicyReasonCode.UNSUPPORTED_POLICY_INPUT,
}

_DETECTED_EVENT_TYPES = {
    ViolenceEventType.VERBAL_THREAT,
    ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
    ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
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
    """Map explicit typed failure provenance to WRITE_FAILED."""
    if not isinstance(failure, PipelineFailureProvenance):
        failure = PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT
    return _decision(
        PolicyOutcome.WRITE_FAILED,
        [_FAILURE_REASONS[failure]],
        "An explicit pipeline failure prevents an admissible application write representation.",
        failure,
    )


def evaluate_policy(
    *,
    validated_facts: Optional[ValidatedSemanticFacts] = None,
    finding: Optional[ViolenceFinding] = None,
    failure: Optional[PipelineFailureProvenance] = None,
) -> PolicyDecision:
    """Apply stable failure, uncertainty, detected, then not-detected precedence."""
    if failure is not None:
        return failed_policy_decision(failure)

    if not isinstance(validated_facts, ValidatedSemanticFacts) or not isinstance(
        finding, ViolenceFinding
    ):
        return failed_policy_decision(PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT)

    facts = validated_facts.facts
    if facts.model_dump(mode="json") != finding.model_dump(mode="json"):
        return failed_policy_decision(PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT)

    uncertainty_reasons: list[PolicyReasonCode] = []
    if facts.conflicting_information:
        uncertainty_reasons.append(PolicyReasonCode.CONFLICTING_INFORMATION)
    if (
        not facts.violence_present
        and facts.event_type == ViolenceEventType.VERBAL_THREAT
    ):
        uncertainty_reasons.append(PolicyReasonCode.THREAT_WITHOUT_VIOLENCE_INDICATION)
    if facts.event_type == ViolenceEventType.UNCLEAR:
        uncertainty_reasons.append(PolicyReasonCode.UNCLEAR_EVENT_TYPE)
    intentionality_is_material = (
        facts.violence_present
        or facts.contact_occurred
        or facts.event_type != ViolenceEventType.NONE
    )
    if facts.intentionality == Intentionality.UNCLEAR and intentionality_is_material:
        uncertainty_reasons.append(PolicyReasonCode.UNCLEAR_MATERIAL_INTENTIONALITY)
    # Free-form extraction caveats remain evidence for inspection, but are not
    # themselves a policy language. Material uncertainty is represented by the
    # bounded structured conditions above.
    if facts.negated and facts.violence_present:
        uncertainty_reasons.append(PolicyReasonCode.NEGATED_AFFIRMATIVE_FINDING)
    if uncertainty_reasons:
        return _decision(
            PolicyOutcome.WRITE_UNCERTAIN,
            uncertainty_reasons,
            "Validated facts contain explicit unresolved uncertainty for application representation.",
        )

    if (
        facts.violence_present
        and not facts.negated
        and facts.event_type in _DETECTED_EVENT_TYPES
    ):
        return _decision(
            PolicyOutcome.WRITE_DETECTED,
            [PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT],
            "Validated facts affirmatively represent violence or a threat.",
        )

    if (
        not facts.violence_present
        and facts.event_type == ViolenceEventType.NONE
        and not facts.conflicting_information
    ):
        reasons = [PolicyReasonCode.NO_VIOLENCE]
        if facts.negated:
            reasons.append(PolicyReasonCode.NEGATED_NON_EVENT)
        if facts.correction_present:
            reasons.append(PolicyReasonCode.CORRECTED_NON_EVENT)
        return _decision(
            PolicyOutcome.WRITE_NOT_DETECTED,
            reasons,
            "Validated facts represent no detected violence or threat.",
        )

    return failed_policy_decision(PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT)
