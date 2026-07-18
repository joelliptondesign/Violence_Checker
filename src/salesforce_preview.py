from typing import Dict, List

from src.contracts import PolicyDecision, PolicyOutcome
from src.models import ViolenceFinding


def build_salesforce_preview(
    incident_id: str,
    finding: ViolenceFinding,
    policy_decision: PolicyDecision,
    *,
    validation_status: str = "success",
) -> Dict[str, object]:
    if not isinstance(finding, ViolenceFinding):
        raise TypeError("Salesforce preview requires a validated ViolenceFinding")
    if not isinstance(policy_decision, PolicyDecision):
        raise TypeError("Salesforce preview requires a PolicyDecision")
    if policy_decision.outcome == PolicyOutcome.WRITE_FAILED:
        raise ValueError("WRITE_FAILED cannot produce a Salesforce preview")

    return {
        "Illustrative_Incident_Identifier__c": incident_id,
        "Illustrative_Violence_Detected__c": finding.violence_present,
        "Illustrative_Violence_Event_Type__c": finding.event_type.value,
        "Illustrative_Actor__c": finding.actor,
        "Illustrative_Target__c": finding.target,
        "Illustrative_Contact_Occurred__c": finding.contact_occurred,
        "Illustrative_Injury_Mentioned__c": finding.injury_mentioned,
        "Illustrative_Current_Event__c": finding.current_event,
        "Illustrative_Intentionality__c": finding.intentionality.value,
        "Illustrative_Negation_Present__c": finding.negated,
        "Illustrative_Correction_Present__c": finding.correction_present,
        "Illustrative_Conflicting_Information__c": finding.conflicting_information,
        "Illustrative_Confidence__c": finding.confidence,
        "Illustrative_Evidence__c": list(finding.evidence_text),
        "Illustrative_Uncertainty_Notes__c": list(finding.uncertainty_notes),
        "Illustrative_Validation_Status__c": validation_status,
        "Illustrative_Write_Disposition__c": policy_decision.outcome.value,
    }


def preview_field_names() -> List[str]:
    return [
        "Illustrative_Incident_Identifier__c",
        "Illustrative_Violence_Detected__c",
        "Illustrative_Violence_Event_Type__c",
        "Illustrative_Actor__c",
        "Illustrative_Target__c",
        "Illustrative_Contact_Occurred__c",
        "Illustrative_Injury_Mentioned__c",
        "Illustrative_Current_Event__c",
        "Illustrative_Intentionality__c",
        "Illustrative_Negation_Present__c",
        "Illustrative_Correction_Present__c",
        "Illustrative_Conflicting_Information__c",
        "Illustrative_Confidence__c",
        "Illustrative_Evidence__c",
        "Illustrative_Uncertainty_Notes__c",
        "Illustrative_Validation_Status__c",
        "Illustrative_Write_Disposition__c",
    ]
