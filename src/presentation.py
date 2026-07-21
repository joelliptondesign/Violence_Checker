"""Deterministic stakeholder-facing projections of True North runtime contracts."""

from dataclasses import dataclass
from typing import Optional

from src.contracts import (
    AssertionStatus,
    Intentionality,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    TemporalScope,
    ValidationFailureStage,
    ValidationResult,
)


SALESFORCE_OPERATOR_FIELDS = (
    ("Illustrative_Incident_Identifier__c", "Incident Identifier"),
    ("Illustrative_Deterministic_Outcome__c", "Outcome"),
    ("Illustrative_Qualifying_Conduct__c", "What Happened"),
    ("Illustrative_Incident_Direction__c", "Who or What Was Involved"),
    ("Illustrative_Operational_Facts__c", "Operational Facts"),
    ("Illustrative_Evidence__c", "Evidence"),
)


def _humanize(value: object) -> str:
    rendered = getattr(value, "value", value)
    return str(rendered).replace("_", " ").title()


def operational_fact_rows(validation_result: ValidationResult) -> list[dict[str, str]]:
    """Project active facts into operator questions without internal state fields."""
    if (
        not validation_result.passed
        or validation_result.validated_envelope is None
        or validation_result.derived_semantics is None
    ):
        return []
    active_ids = set(validation_result.derived_semantics.active_fact_ids)
    rows: list[dict[str, str]] = []
    for fact in validation_result.validated_envelope.facts:
        if fact.fact_id not in active_ids:
            continue
        evidence = " ".join(item.excerpt for item in fact.evidence).casefold()
        roles = []
        if "patient" in evidence or "pt" in evidence.split():
            roles.append("Patient")
        if "registered nurse" in evidence or "rn" in evidence.split():
            roles.append("registered nurse")
        elif "nurse" in evidence:
            roles.append("nurse")
        if "technician" in evidence or "tech" in evidence.split():
            roles.append("technician")
        if "aide" in evidence:
            roles.append("aide")
        if fact.direction.value == "object_directed":
            target = next((
                label for term, label in (
                    ("medication room door", "Medication room door"),
                    ("hospital window", "Hospital window"),
                    ("window", "Window"),
                    ("side rail", "Side rail"),
                    ("door", "Door"),
                    ("wall", "Wall"),
                ) if term in evidence
            ), "Property described in the report")
            involvement_label, involvement = "What Was Targeted", target
        elif fact.direction.value == "self_directed":
            involvement_label, involvement = "Who Was Involved", roles[0] if roles else "Person described in the report"
        else:
            involvement_label = "Who Was Involved"
            involvement = " and ".join(roles[:2]) if roles else "People described in the report"
        conduct = _humanize(fact.conduct).capitalize() if fact.conduct is not None else "Reported conduct"
        if fact.assertion_status == AssertionStatus.DENIED:
            conduct = f"Reported {conduct.lower()} did not occur"
        fields = {
            "What Happened": conduct,
            involvement_label: involvement,
            "Intent": {
                "intentional": "Intentional", "accidental": "Accidental",
                "unresolved": "Not established",
            }[fact.intentionality.value],
            "When": {
                "current": "During the event being reported",
                "historical": "Before the event being reported",
                "unresolved": "Not established",
            }[fact.temporal_scope.value],
        }
        rows.append({
            "What Happened": fields["What Happened"],
            "Who Was Involved": fields.get("Who Was Involved", "—"),
            "What Was Targeted": fields.get("What Was Targeted", "—"),
            "Intent": fields["Intent"],
            "When": fields["When"],
        })
    return rows


def validated_evidence_excerpts(validation_result: ValidationResult) -> tuple[str, ...]:
    if not validation_result.passed or validation_result.validated_envelope is None:
        return ()
    excerpts: list[str] = []
    seen: set[str] = set()
    for fact in validation_result.validated_envelope.facts:
        for evidence in fact.evidence:
            if evidence.excerpt not in seen:
                seen.add(evidence.excerpt)
                excerpts.append(evidence.excerpt)
    return tuple(excerpts)


def _readable_salesforce_value(value: object) -> object:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value) if value else "None"
    return value


def salesforce_operator_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for name, label in SALESFORCE_OPERATOR_FIELDS:
        if name not in payload:
            continue
        value = payload[name]
        if name == "Illustrative_Qualifying_Conduct__c" and isinstance(value, list):
            value = [str(item).replace("_", " ").capitalize() for item in value]
        if name == "Illustrative_Incident_Direction__c":
            facts = payload.get("Illustrative_Operational_Facts__c", [])
            if isinstance(facts, list) and facts:
                parts = str(facts[0]).split("; ")
                involved = next((part.split(": ", 1)[1] for part in parts if part.startswith(("Who Was Involved:", "What Was Targeted:"))), None)
                if involved is not None:
                    value = involved
        rows.append({"Field": label, "Value": _readable_salesforce_value(value)})
    return rows


def salesforce_payload_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    return [
        {"Field": name, "Value": _readable_salesforce_value(value)}
        for name, value in payload.items()
    ]


POLICY_EXPLANATIONS = {
    PolicyOutcome.VIOLENCE_DETECTED: "The reported event meets the workplace violence criteria.",
    PolicyOutcome.NO_VIOLENCE_DETECTED: "The reported event does not meet the workplace violence criteria.",
    PolicyOutcome.UNCERTAIN: "The available information does not establish a clear determination.",
    PolicyOutcome.UNABLE_TO_DETERMINE: "The available information was insufficient to complete a reliable analysis.",
}

POLICY_REASON_EXPLANATIONS = {
    PolicyReasonCode.QUALIFYING_CURRENT_VIOLENCE: "Active facts establish intentional qualifying conduct during the current incident.",
    PolicyReasonCode.NO_QUALIFYING_CURRENT_VIOLENCE: "No active fact establishes intentional qualifying conduct during the current incident.",
    PolicyReasonCode.MATERIAL_SEMANTIC_UNCERTAINTY: "An important incident detail remains unresolved.",
    PolicyReasonCode.UNRESOLVED_CONTRADICTION: "The incident account contains unresolved conflicting information.",
    PolicyReasonCode.INCOMPLETE_ANALYSIS: "The analysis was incomplete.",
    PolicyReasonCode.PROVIDER_FAILURE: "The analysis service did not produce usable incident facts.",
    PolicyReasonCode.SCHEMA_FAILURE: "The extracted incident facts did not satisfy the required structure.",
    PolicyReasonCode.VALIDATION_FAILURE: "The extracted incident facts were not admissible for classification.",
    PolicyReasonCode.PIPELINE_FAILURE: "The analysis pipeline could not complete.",
    PolicyReasonCode.MALFORMED_SEMANTIC_INPUT: "The semantic input was not usable for classification.",
}

VALIDATION_SUMMARIES = {
    ValidationFailureStage.NOT_RUN: "Semantic validation could not run because extraction did not complete.",
    ValidationFailureStage.NONE: "Extracted operational facts passed deterministic validation.",
    ValidationFailureStage.SCHEMA: "Extracted operational facts did not satisfy the required structure.",
    ValidationFailureStage.DOMAIN: "Extracted operational facts were internally inconsistent.",
}


@dataclass(frozen=True)
class ComparisonPresentation:
    keyword_observation: str
    ai_observation: str
    difference_explanation: str
    review_value: str


COMPARISON_PRESENTATIONS = {
    "aligned_positive": ComparisonPresentation("Keyword matching found violence-related language.", "True North facts support violence detection.", "Both methods produced a positive result.", "The contextual facts show why the result qualifies."),
    "aligned_negative": ComparisonPresentation("Keyword matching found no configured match.", "True North facts do not support violence detection.", "Both methods produced a negative result.", "The contextual facts show why no qualifying conduct was established."),
    "regex_positive_semantic_negative": ComparisonPresentation("Keyword matching found violence-related language.", "True North facts do not support violence detection.", "Context changes how the matching language applies.", "Operational facts can reduce keyword false positives."),
    "regex_negative_semantic_positive": ComparisonPresentation("Keyword matching found no configured match.", "True North facts support violence detection.", "Qualifying meaning was present without a configured match.", "Operational facts can surface indirect wording."),
    "semantic_uncertain": ComparisonPresentation("Keyword matching completed.", "True North facts preserve a material unresolved detail.", "A definitive contextual outcome would overstate the evidence.", "Uncertainty remains visible for review."),
    "semantic_failure": ComparisonPresentation("Keyword matching completed.", "True North analysis did not produce admissible facts.", "A complete contextual comparison is unavailable.", "Failure remains separate from a negative result."),
}


def comparison_presentation(classification_alignment: str, context_observations: Optional[list[str]] = None) -> ComparisonPresentation:
    base = COMPARISON_PRESENTATIONS.get(classification_alignment, COMPARISON_PRESENTATIONS["semantic_failure"])
    if not context_observations:
        return base
    return ComparisonPresentation(base.keyword_observation, f"{base.ai_observation} {' '.join(context_observations)}", base.difference_explanation, base.review_value)


def policy_outcome_label(decision: PolicyDecision) -> str:
    return decision.outcome.value


def policy_explanation(decision: PolicyDecision) -> str:
    return POLICY_EXPLANATIONS[decision.outcome]


def policy_reason_explanations(decision: PolicyDecision) -> list[str]:
    return [POLICY_REASON_EXPLANATIONS[reason] for reason in decision.reason_codes]


def semantic_summary(validation_result: ValidationResult, decision: PolicyDecision) -> str:
    if not validation_result.passed or validation_result.validated_envelope is None:
        return POLICY_EXPLANATIONS[PolicyOutcome.UNABLE_TO_DETERMINE]
    facts = validation_result.validated_envelope.facts
    if decision.outcome == PolicyOutcome.VIOLENCE_DETECTED:
        return "The reported event includes intentional conduct covered by the workplace violence criteria."
    if decision.outcome == PolicyOutcome.UNCERTAIN:
        return "The available accounts leave an important incident detail unresolved."
    if any(fact.intentionality == Intentionality.ACCIDENTAL for fact in facts):
        return "The incident describes accidental rather than intentional conduct."
    if any(fact.temporal_scope == TemporalScope.HISTORICAL for fact in facts):
        return "The reported conduct is historical rather than part of the current incident."
    if any(fact.assertion_status == AssertionStatus.DENIED for fact in facts):
        return "The account states that the potentially qualifying conduct did not occur."
    return POLICY_EXPLANATIONS[decision.outcome]
