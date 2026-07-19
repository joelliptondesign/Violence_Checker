"""Deterministic stakeholder-facing labels for internal pipeline contracts."""

from typing import Optional

from src.contracts import (
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    ValidationFailureStage,
    ValidationResult,
    ValidatedSemanticEnvelope,
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
    PolicyReasonCode.UNSUPPORTED_POLICY_INPUT: (
        "The validated result is not supported by this policy version."
    ),
    PolicyReasonCode.CONFLICTING_INFORMATION: "The narrative contains conflicting information.",
    PolicyReasonCode.SCOPED_SEMANTIC_UNCERTAINTY: (
        "An active current interpersonal proposition has explicit bounded uncertainty."
    ),
    PolicyReasonCode.AFFIRMED_CURRENT_INTERPERSONAL_VIOLENCE: (
        "An active current interpersonal proposition affirms violence or a threat."
    ),
    PolicyReasonCode.NO_ACTIVE_CURRENT_INTERPERSONAL_VIOLENCE: (
        "No active current interpersonal proposition affirms violence or a threat."
    ),
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


def semantic_summary(
    validated: Optional[ValidatedSemanticEnvelope],
    decision: PolicyDecision,
) -> str:
    """Summarize only typed policy and derived views without semantic inference."""
    if decision.outcome == PolicyOutcome.WRITE_FAILED or validated is None:
        return "Semantic analysis was unable to produce a validated proposition envelope."
    candidate = validated.policy_candidate
    if decision.outcome == PolicyOutcome.WRITE_DETECTED:
        count = len(candidate.active_current_interpersonal_violence)
        return f"{count} active current interpersonal proposition(s) support the detected outcome."
    elif decision.outcome == PolicyOutcome.WRITE_NOT_DETECTED:
        return "No validated active current interpersonal proposition supports a detected outcome."
    return "Validated active current interpersonal propositions contain bounded uncertainty."


def validation_summary(validation: ValidationResult) -> str:
    return VALIDATION_SUMMARIES[validation.failure_stage]
