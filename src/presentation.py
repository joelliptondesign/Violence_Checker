"""Deterministic stakeholder-facing labels for internal pipeline contracts."""

from dataclasses import dataclass
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


CLINICAL_STAFF_ROLES = {
    "aide",
    "clinical staff",
    "doctor",
    "nurse",
    "nursing staff",
    "physician",
    "registered nurse",
    "staff",
    "technician",
}
SECURITY_STAFF_ROLES = {"security", "security officer", "security staff"}
VISITOR_ROLES = {"family member", "guest", "visitor"}

SALESFORCE_OPERATOR_FIELDS = (
    ("Illustrative_Incident_Identifier__c", "Incident Identifier"),
    ("Illustrative_Write_Disposition__c", "Write Disposition"),
    ("Illustrative_Evidence__c", "Evidence"),
)


def humanize_entity_role(label: Optional[str], entity_kind: object) -> str:
    """Return a readable role without exposing internal entity references."""
    if label and label.strip():
        return " ".join(word.capitalize() for word in label.replace("_", " ").split())
    kind = getattr(entity_kind, "value", str(entity_kind)).replace("_", " ")
    return " ".join(word.capitalize() for word in kind.split())


def humanize_entity_category(label: Optional[str], entity_kind: object) -> str:
    """Translate an existing entity kind and role into a stakeholder label."""
    normalized = (label or "").strip().casefold()
    kind = getattr(entity_kind, "value", str(entity_kind))
    if normalized == "patient":
        return "Patient"
    if normalized in SECURITY_STAFF_ROLES:
        return "Security Staff"
    if normalized in CLINICAL_STAFF_ROLES:
        return "Clinical Staff"
    if normalized in VISITOR_ROLES:
        return "Visitor"
    categories = {
        "person": "Person",
        "people_collective": "Group",
        "object": "Object",
        "unspecified": "Unspecified",
    }
    return categories.get(kind, "Unspecified")


def extracted_entity_rows(validation_result: ValidationResult) -> list[dict[str, str]]:
    """Project validated entities into an ordered identifier-free table."""
    if not validation_result.passed or validation_result.validated_envelope is None:
        return []
    return [
        {
            "Role": humanize_entity_role(entity.label, entity.entity_kind),
            "Category": humanize_entity_category(entity.label, entity.entity_kind),
        }
        for entity in validation_result.validated_envelope.envelope.entities
    ]


def validated_evidence_excerpts(validation_result: ValidationResult) -> tuple[str, ...]:
    """Return unique validated evidence text in deterministic source order."""
    if not validation_result.passed or validation_result.validated_envelope is None:
        return ()
    excerpts: list[str] = []
    seen: set[str] = set()
    for evidence in validation_result.validated_envelope.envelope.evidence_excerpts:
        if evidence.text not in seen:
            seen.add(evidence.text)
            excerpts.append(evidence.text)
    return tuple(excerpts)


def _readable_salesforce_value(value: object) -> object:
    """Format collection values for a table without changing payload content."""
    if isinstance(value, list):
        return "\n".join(str(item) for item in value) if value else "None"
    return value


def salesforce_operator_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    """Project important payload fields into a readable operator-facing view."""
    return [
        {"Field": label, "Value": _readable_salesforce_value(payload[field_name])}
        for field_name, label in SALESFORCE_OPERATOR_FIELDS
        if field_name in payload
    ]


def salesforce_payload_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    """Project the complete payload in its original field order for inspection."""
    return [
        {"Field": field_name, "Value": _readable_salesforce_value(value)}
        for field_name, value in payload.items()
    ]


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


@dataclass(frozen=True)
class ComparisonPresentation:
    keyword_observation: str
    ai_observation: str
    difference_explanation: str
    review_value: str


COMPARISON_PRESENTATIONS = {
    "aligned_positive": ComparisonPresentation(
        keyword_observation="The keyword detector found words or phrases associated with violence.",
        ai_observation="The AI analysis found context supporting current violence or a threat involving another person.",
        difference_explanation="Both methods point toward the same result, while the AI analysis adds event context.",
        review_value="Agreement provides a simple cross-check while preserving the details that shaped the result.",
    ),
    "aligned_negative": ComparisonPresentation(
        keyword_observation="The keyword detector did not find a matching word or phrase.",
        ai_observation="The AI analysis did not produce a confirmed current interpersonal violence result.",
        difference_explanation="Neither method produced a positive result for current interpersonal violence.",
        review_value="The comparison helps reviewers see when keyword matching and contextual analysis reach the same conclusion.",
    ),
    "regex_positive_semantic_negative": ComparisonPresentation(
        keyword_observation="The keyword detector found violence-related language.",
        ai_observation="The AI analysis found that the surrounding context did not support a confirmed current interpersonal violence result.",
        difference_explanation="The methods differ because keyword matching cannot determine how the language applies to the event.",
        review_value="Context can reduce false alerts caused by historical, accidental, corrected, or non-interpersonal language.",
    ),
    "regex_negative_semantic_positive": ComparisonPresentation(
        keyword_observation="The keyword detector did not find a matching word or phrase.",
        ai_observation="The AI analysis found context supporting current violence or a threat involving another person.",
        difference_explanation="The methods differ because the event meaning was present without an expected keyword match.",
        review_value="Context can surface relevant incidents that use unexpected or indirect wording.",
    ),
    "semantic_failure": ComparisonPresentation(
        keyword_observation="The keyword detector completed its word and phrase check.",
        ai_observation="The AI analysis did not produce usable validated information.",
        difference_explanation="A complete comparison is unavailable because the contextual analysis did not finish successfully.",
        review_value="Keeping an incomplete analysis separate prevents it from being treated as a negative result.",
    ),
}


COMPARISON_CONTEXT_NOTES = {
    "historical conduct": "AI separated historical conduct from the current incident.",
    "object-directed conduct": "AI distinguished conduct directed at an object from conduct directed at another person.",
    "self-directed conduct": "AI distinguished self-directed conduct from conduct directed at another person.",
    "correction and supersession": "AI preserved a correction instead of relying on the superseded statement.",
    "competing assertions": "AI preserved conflicting accounts without choosing one as established.",
    "bounded uncertainty": "AI kept a material detail unresolved instead of assuming what occurred.",
}


def comparison_presentation(
    classification_alignment: str,
    context_observations: Optional[list[str]] = None,
) -> ComparisonPresentation:
    presentation = COMPARISON_PRESENTATIONS.get(
        classification_alignment,
        ComparisonPresentation(
            keyword_observation="The keyword detector completed its word and phrase check.",
            ai_observation="The AI analysis completed its contextual review.",
            difference_explanation="The two views are available for incident review.",
            review_value="Showing both views helps reviewers understand how language and context contributed to the result.",
        ),
    )
    context_notes = [
        plain_text
        for source_text, plain_text in COMPARISON_CONTEXT_NOTES.items()
        if any(source_text in observation.lower() for observation in (context_observations or []))
    ]
    if not context_notes:
        return presentation
    return ComparisonPresentation(
        keyword_observation=presentation.keyword_observation,
        ai_observation=f"{presentation.ai_observation} {' '.join(context_notes)}",
        difference_explanation=presentation.difference_explanation,
        review_value=presentation.review_value,
    )


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
