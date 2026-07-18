"""Deterministic stakeholder-facing labels for internal pipeline contracts."""

from src.contracts import (
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    ValidationFailureStage,
    ValidationResult,
)


POLICY_OUTCOME_LABELS = {
    PolicyOutcome.WRITE_DETECTED: "Violence Detected",
    PolicyOutcome.WRITE_UNCERTAIN: "Uncertain",
    PolicyOutcome.WRITE_NOT_DETECTED: "No Violence Detected",
    PolicyOutcome.WRITE_FAILED: "Unable to Determine",
}

POLICY_EXPLANATIONS = {
    PolicyOutcome.WRITE_DETECTED: (
        "The validated narrative indicates violence or a threat."
    ),
    PolicyOutcome.WRITE_UNCERTAIN: (
        "The available information is insufficient for a confident violence classification."
    ),
    PolicyOutcome.WRITE_NOT_DETECTED: (
        "The validated narrative does not indicate violence or a threat."
    ),
    PolicyOutcome.WRITE_FAILED: (
        "A classification could not be produced because the analysis pipeline did not complete successfully."
    ),
}

POLICY_REASON_EXPLANATIONS = {
    PolicyReasonCode.INPUT_VALIDATION_FAILED: "The incident input could not be validated.",
    PolicyReasonCode.PROVIDER_CONFIGURATION_FAILED: (
        "Semantic analysis is unavailable because the provider is not configured."
    ),
    PolicyReasonCode.PROVIDER_REQUEST_FAILED: "The semantic analysis request did not complete.",
    PolicyReasonCode.PROVIDER_STRUCTURED_RESPONSE_FAILED: (
        "The semantic analysis response was incomplete."
    ),
    PolicyReasonCode.PROVIDER_VALIDATION_FAILED: (
        "The semantic analysis response could not be validated."
    ),
    PolicyReasonCode.SCHEMA_VALIDATION_FAILED: (
        "The extracted information did not match the required structure."
    ),
    PolicyReasonCode.DOMAIN_VALIDATION_FAILED: (
        "The extracted information contained an invalid combination of facts."
    ),
    PolicyReasonCode.COMPATIBILITY_CONSTRUCTION_FAILED: (
        "The validated facts could not be prepared for downstream representation."
    ),
    PolicyReasonCode.UNSUPPORTED_POLICY_INPUT: (
        "The validated result is not supported by this policy version."
    ),
    PolicyReasonCode.CONFLICTING_INFORMATION: "The narrative contains conflicting information.",
    PolicyReasonCode.THREAT_WITHOUT_VIOLENCE_INDICATION: (
        "The narrative indicates a threat, but the violence indicator is not affirmative."
    ),
    PolicyReasonCode.UNCLEAR_EVENT_TYPE: "The event type cannot be determined confidently.",
    PolicyReasonCode.UNCLEAR_MATERIAL_INTENTIONALITY: (
        "The available information does not establish whether the event was intentional."
    ),
    PolicyReasonCode.MATERIAL_UNCERTAINTY_NOTES: (
        "Additional information is needed before a confident classification can be made."
    ),
    PolicyReasonCode.NEGATED_AFFIRMATIVE_FINDING: (
        "The narrative negates an otherwise affirmative finding."
    ),
    PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT: (
        "The validated facts indicate violence or a threat."
    ),
    PolicyReasonCode.NO_VIOLENCE: "The validated facts indicate no violence or threat.",
    PolicyReasonCode.NEGATED_NON_EVENT: "The narrative explicitly indicates the event did not occur.",
    PolicyReasonCode.CORRECTED_NON_EVENT: "The narrative corrects an earlier statement.",
}

VALIDATION_SUMMARIES = {
    ValidationFailureStage.NOT_RUN: (
        "Semantic validation could not run because semantic extraction did not complete."
    ),
    ValidationFailureStage.NONE: "✓ Extracted semantic facts passed deterministic validation.",
    ValidationFailureStage.SCHEMA: (
        "Extracted information could not be validated because its structure was invalid."
    ),
    ValidationFailureStage.DOMAIN: (
        "Extracted information could not be validated because the facts were inconsistent."
    ),
}


def policy_outcome_label(decision: PolicyDecision) -> str:
    return POLICY_OUTCOME_LABELS[decision.outcome]


def policy_explanation(decision: PolicyDecision) -> str:
    return POLICY_EXPLANATIONS[decision.outcome]


def policy_reason_explanations(decision: PolicyDecision) -> list[str]:
    return [POLICY_REASON_EXPLANATIONS[reason] for reason in decision.reason_codes]


def validation_summary(validation: ValidationResult) -> str:
    return VALIDATION_SUMMARIES[validation.failure_stage]
