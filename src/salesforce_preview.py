"""Deterministic illustrative preview from validated successor views."""

from typing import Dict, List

from src.contracts import PolicyDecision, PolicyOutcome, ValidatedSemanticEnvelope


def build_salesforce_preview(
    validated: ValidatedSemanticEnvelope,
    policy_decision: PolicyDecision,
    *,
    validation_status: str = "success",
) -> Dict[str, object]:
    if not isinstance(validated, ValidatedSemanticEnvelope):
        raise TypeError("Salesforce preview requires a validated successor envelope")
    if not isinstance(policy_decision, PolicyDecision):
        raise TypeError("Salesforce preview requires a PolicyDecision")
    if policy_decision.outcome == PolicyOutcome.WRITE_FAILED:
        raise ValueError("WRITE_FAILED cannot produce a Salesforce preview")
    candidate = validated.policy_candidate
    return {
        "Illustrative_Incident_Identifier__c": validated.envelope.incident_id,
        "Illustrative_Semantic_Schema__c": f"{validated.envelope.schema_identity}@{validated.envelope.schema_version}",
        "Illustrative_Active_Propositions__c": list(validated.derived.active_proposition_ids),
        "Illustrative_Interpersonal_Propositions__c": list(candidate.active_current_interpersonal_affirmed),
        "Illustrative_Evidence__c": [item.text for item in validated.envelope.evidence_excerpts],
        "Illustrative_Validation_Status__c": validation_status,
        "Illustrative_Write_Disposition__c": policy_decision.outcome.value,
    }


def preview_field_names() -> List[str]:
    return [
        "Illustrative_Incident_Identifier__c",
        "Illustrative_Semantic_Schema__c",
        "Illustrative_Active_Propositions__c",
        "Illustrative_Interpersonal_Propositions__c",
        "Illustrative_Evidence__c",
        "Illustrative_Validation_Status__c",
        "Illustrative_Write_Disposition__c",
    ]
