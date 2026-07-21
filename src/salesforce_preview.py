"""Deterministic illustrative Salesforce projection from True North facts."""

from typing import Dict, List

from src.contracts import (
    AssertionStatus,
    Intentionality,
    PolicyDecision,
    PolicyOutcome,
    TemporalScope,
    ValidationResult,
)


def _operational_fact(fact) -> str:
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
    conduct = fact.conduct.value.replace("_", " ").capitalize() if fact.conduct else "Reported conduct"
    if fact.assertion_status != AssertionStatus.AFFIRMED:
        conduct = f"Reported {conduct.lower()}"
    if fact.direction.value == "object_directed":
        label = "What Was Targeted"
        involved = next((
            value for term, value in (
                ("medication room door", "Medication room door"), ("hospital window", "Hospital window"),
                ("window", "Window"), ("side rail", "Side rail"), ("door", "Door"), ("wall", "Wall"),
            ) if term in evidence
        ), "Property described in the report")
    else:
        label = "Who Was Involved"
        involved = " and ".join(roles[:2]) if roles else "People described in the report"
    intent = {
        "intentional": "Intentional", "accidental": "Accidental", "unresolved": "Not established",
    }[fact.intentionality.value]
    timing = {
        "current": "During the event being reported",
        "historical": "Before the event being reported",
        "unresolved": "Not established",
    }[fact.temporal_scope.value]
    return (
        f"What Happened: {conduct}; {label}: {involved}; Intent: {intent}; When: {timing}"
    )


def build_salesforce_preview(
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
) -> Dict[str, object]:
    if not isinstance(validation_result, ValidationResult) or not validation_result.passed:
        raise TypeError("Salesforce preview requires successful True North validation")
    if not isinstance(policy_decision, PolicyDecision):
        raise TypeError("Salesforce preview requires a PolicyDecision")
    if policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE:
        raise ValueError("Unable to Determine cannot produce a Salesforce preview")
    envelope = validation_result.validated_envelope
    derived = validation_result.derived_semantics
    if envelope is None or derived is None:
        raise ValueError("Salesforce preview requires validated facts and deterministic views")

    active_ids = set(derived.active_fact_ids)
    active = [fact for fact in envelope.facts if fact.fact_id in active_ids]
    qualifying = [
        fact.conduct.value
        for fact in active
        if fact.conduct is not None
        and fact.intentionality == Intentionality.INTENTIONAL
        and fact.temporal_scope == TemporalScope.CURRENT
        and fact.assertion_status == AssertionStatus.AFFIRMED
    ]
    evidence: list[str] = []
    for fact in active:
        for item in fact.evidence:
            if item.excerpt not in evidence:
                evidence.append(item.excerpt)
    return {
        "Illustrative_Incident_Identifier__c": envelope.incident_id,
        "Illustrative_Semantic_Schema__c": f"{envelope.schema_identity}@{envelope.schema_version}",
        "Illustrative_Deterministic_Outcome__c": policy_decision.outcome.value,
        "Illustrative_Qualifying_Conduct__c": qualifying,
        "Illustrative_Incident_Direction__c": derived.incident_direction.value,
        "Illustrative_Operational_Facts__c": [_operational_fact(fact) for fact in active],
        "Illustrative_Evidence__c": evidence,
        "Illustrative_Processing_Status__c": validation_result.processing_status.value,
    }


def preview_field_names() -> List[str]:
    return [
        "Illustrative_Incident_Identifier__c",
        "Illustrative_Semantic_Schema__c",
        "Illustrative_Deterministic_Outcome__c",
        "Illustrative_Qualifying_Conduct__c",
        "Illustrative_Incident_Direction__c",
        "Illustrative_Operational_Facts__c",
        "Illustrative_Evidence__c",
        "Illustrative_Processing_Status__c",
    ]
