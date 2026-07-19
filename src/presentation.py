"""Deterministic stakeholder-facing labels for internal pipeline contracts."""

from typing import Optional

from src.contracts import (
    Completion,
    ConductKind,
    Contact,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    SemanticIntentionality,
    TemporalScope,
    UncertaintyDimension,
    ValidationFailureStage,
    ValidationResult,
    ValidatedSemanticEnvelope,
)


POLICY_OUTCOME_LABELS = {
    PolicyOutcome.WRITE_DETECTED: "Violence Detected",
    PolicyOutcome.WRITE_UNCERTAIN: "Unable to Determine",
    PolicyOutcome.WRITE_NOT_DETECTED: "No Violence Detected",
    PolicyOutcome.WRITE_FAILED: "Analysis Failed",
}

POLICY_EXPLANATIONS = {
    PolicyOutcome.WRITE_DETECTED: (
        "The narrative describes violence involving another person."
    ),
    PolicyOutcome.WRITE_UNCERTAIN: (
        "The narrative suggests possible violence, but an important detail is unclear."
    ),
    PolicyOutcome.WRITE_NOT_DETECTED: (
        "The narrative does not describe current violence involving another person."
    ),
    PolicyOutcome.WRITE_FAILED: (
        "The analysis could not be completed. No classification was produced."
    ),
}

POLICY_REASON_EXPLANATIONS = {
    PolicyReasonCode.INPUT_VALIDATION_FAILED: "The incident narrative is not valid for analysis.",
    PolicyReasonCode.PROVIDER_CONFIGURATION_FAILED: (
        "The analysis service is not configured."
    ),
    PolicyReasonCode.PROVIDER_REQUEST_FAILED: "The analysis request did not complete.",
    PolicyReasonCode.PROVIDER_STRUCTURED_RESPONSE_FAILED: (
        "The analysis service returned an incomplete result."
    ),
    PolicyReasonCode.PROVIDER_VALIDATION_FAILED: (
        "The analysis service returned an unusable result."
    ),
    PolicyReasonCode.SCHEMA_VALIDATION_FAILED: (
        "The result was missing required information."
    ),
    PolicyReasonCode.DOMAIN_VALIDATION_FAILED: (
        "The result contained inconsistent information."
    ),
    PolicyReasonCode.UNSUPPORTED_POLICY_INPUT: (
        "The result could not be classified by this version of the application."
    ),
    PolicyReasonCode.CONFLICTING_INFORMATION: "The narrative contains conflicting information.",
    PolicyReasonCode.SCOPED_SEMANTIC_UNCERTAINTY: "An important detail about the reported event is unclear.",
    PolicyReasonCode.AFFIRMED_CURRENT_INTERPERSONAL_VIOLENCE: (
        "The narrative describes current violence or a threat involving another person."
    ),
    PolicyReasonCode.NO_ACTIVE_CURRENT_INTERPERSONAL_VIOLENCE: (
        "The narrative does not describe current violence or a threat involving another person."
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
    """Summarize validated facts in short operational language."""
    if decision.outcome == PolicyOutcome.WRITE_FAILED or validated is None:
        return "The analysis could not produce a usable result."
    candidate = validated.policy_candidate
    propositions = {item.proposition_id: item for item in validated.envelope.propositions}
    if decision.outcome == PolicyOutcome.WRITE_DETECTED:
        item = propositions[candidate.active_current_interpersonal_violence[0]]
        if item.conduct_kind == ConductKind.PHYSICAL_CONDUCT:
            if item.completion == Completion.ATTEMPTED:
                return "The narrative describes an attempted physical act directed at another person."
            if item.contact == Contact.OCCURRED:
                return "The narrative describes completed physical violence involving contact."
        return "The narrative describes a threat directed at another person."
    if decision.outcome == PolicyOutcome.WRITE_NOT_DETECTED:
        if any(item.intentionality == SemanticIntentionality.ACCIDENTAL for item in propositions.values()):
            return "The narrative describes accidental contact, not violence."
        if any(item.temporal_scope == TemporalScope.HISTORICAL for item in propositions.values()):
            return "The narrative describes a past event, not violence during the current incident."
        return "The narrative does not describe current violence involving another person."
    material = [
        item for item in validated.envelope.uncertainties
        if item.uncertainty_id in candidate.active_current_interpersonal_uncertainties
    ]
    if material:
        dimension = material[0].dimension
        detail = {
            UncertaintyDimension.CONTACT: "whether physical contact occurred",
            UncertaintyDimension.COMPLETION: "whether the act was completed",
            UncertaintyDimension.ASSERTION_STATUS: "whether the reported act occurred",
            UncertaintyDimension.TEMPORAL_SCOPE: "whether the event occurred during the current incident",
            UncertaintyDimension.TARGET_IDENTITY: "whether another person was targeted",
            UncertaintyDimension.DIRECTION: "whether another person was targeted",
        }.get(dimension, "what occurred")
        return f"The narrative suggests possible violence, but it is unclear {detail}."
    return "The narrative suggests possible violence, but an important detail is unclear."


def validation_summary(validation: ValidationResult) -> str:
    return VALIDATION_SUMMARIES[validation.failure_stage]
