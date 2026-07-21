from pathlib import Path

import pytest
from pydantic import ValidationError

from src.app_logic import run_analysis
from src.contracts import (
    AssertionStatus,
    CommunicationFact,
    Conduct,
    FactDirection,
    IncidentDirection,
    Intentionality,
    OperatorCommunication,
    OperatorCommunicationInput,
    PolicyOutcome,
    ResolutionStatus,
    TemporalScope,
    UncertaintyDimension,
)
from src.models import Incident
from src.operator_communication import (
    build_deterministic_communication,
    communication_validation_issues,
    construct_communication_input,
)
from src.operator_communication_provider import OperatorCommunicationResult, OperatorCommunicationStatus
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from tests.test_app_logic import candidate_for, extraction_for


def analyze(narrative, **updates):
    return run_analysis(
        Incident(incident_id="CASE_001", narrative=narrative),
        extractor=extraction_for(candidate_for(narrative, **updates)),
    )


def test_projection_contains_only_validated_incident_support_needed_for_communication():
    result = analyze("Patient intentionally struck the nurse today.")
    facts = construct_communication_input(result.validation_result, result.policy_decision)
    assert set(OperatorCommunicationInput.model_fields) == {
        "outcome", "incident_direction", "active_facts", "superseded_facts",
        "has_unresolved_contradiction",
    }
    assert set(type(facts.active_facts[0]).model_fields) == {
        "conduct", "direction", "intentionality", "temporal_scope", "assertion_status",
        "resolution_status", "uncertainty", "evidence_excerpts",
    }
    assert set(OperatorCommunication.model_fields) == {
        "incident_summary", "key_findings", "why_this_result",
    }
    assert facts.active_facts[0].evidence_excerpts == (
        "Patient intentionally struck the nurse today.",
    )
    dumped = facts.model_dump(mode="json")
    assert "incident_id" not in str(dumped)
    assert "evidence_id" not in str(dumped)


@pytest.mark.parametrize(
    "narrative,updates,summary_term",
    [
        ("Patient intentionally struck the nurse today.", {}, "struck the nurse"),
        ("Patient accidentally contacted the nurse today.", {"intentionality": Intentionality.ACCIDENTAL}, "accidentally contacted"),
        ("Patient threatened the nurse years ago.", {"conduct": Conduct.VERBAL_THREAT, "temporal_scope": TemporalScope.HISTORICAL}, "years ago"),
        ("Patient intentionally harmed themself today.", {"conduct": Conduct.SELF_HARM, "direction": FactDirection.SELF_DIRECTED}, "harmed themself"),
        ("Patient intentionally damaged property today.", {"conduct": Conduct.PROPERTY_VIOLENCE, "direction": FactDirection.OBJECT_DIRECTED}, "damaged property"),
        ("Patient may have struck the nurse today.", {"intentionality": Intentionality.UNRESOLVED, "uncertainty": [UncertaintyDimension.INTENTIONALITY]}, "may have struck"),
    ],
)
def test_fallback_describes_incident_and_keeps_classification_explanation_separate(
    narrative, updates, summary_term,
):
    result = analyze(narrative, **updates)
    summary = result.communication.incident_summary.casefold()
    assert summary_term in summary
    assert result.policy_decision.outcome.value.casefold() not in summary
    assert "criteria" not in summary
    assert "workplace violence criteria" in result.communication.why_this_result.casefold()
    assert all(
        term not in " ".join(result.communication.key_findings).casefold()
        for term in ("assertion", "resolution", "criteria satisfied", "validated")
    )


def test_accidental_contact_gold_case_is_incident_first_and_concrete():
    incident = Incident(
        incident_id="CASE_004",
        narrative=(
            "pt lost balance getting off commode and grabbed rn arm. both went into wall. rn wrist "
            "sore. pt was not combative this looked accidental"
        ),
    )
    result = run_analysis(
        incident,
        extractor=extraction_for(candidate_for(
            incident.narrative,
            incident_id=incident.incident_id,
            intentionality=Intentionality.ACCIDENTAL,
        )),
    )
    assert result.policy_decision.outcome == PolicyOutcome.NO_VIOLENCE_DETECTED
    assert result.communication.incident_summary == (
        "The patient lost balance while getting up from the commode and grabbed the registered "
        "nurse's arm to maintain balance. The narrative states the patient was not combative and "
        "describes the contact as accidental."
    )
    assert result.communication.key_findings == (
        "Patient lost balance",
        "Registered nurse's arm grabbed",
        "Physical contact occurred",
        "Contact appeared accidental",
        "Patient not combative",
    )
    assert result.communication.why_this_result == (
        "Physical contact occurred during the event being reported, but the account describes "
        "the contact as accidental rather than intentional. Accidental contact does not meet the "
        "workplace violence criteria."
    )


def test_failure_contract_and_module_authority_boundaries():
    result = run_analysis(
        Incident(incident_id="FAIL", narrative="Patient struck a nurse."),
        extractor=lambda _: SemanticExtractionResult(
            SemanticExtractionStatus.REQUEST_FAILURE, failure_message="bounded"
        ),
    )
    assert result.policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE
    assert result.salesforce_preview is None
    assert "not contain enough supported information" in result.communication.incident_summary
    assert "classified" not in result.communication.incident_summary.casefold()
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="", key_findings=("Fact available",), why_this_result="Reason")
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="Summary", key_findings=("Too many words in this finding here",), why_this_result="Reason")
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="A schema version was used.", key_findings=("Fact available",), why_this_result="Reason")
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="Summary", key_findings=("Assertion affirmed",), why_this_result="Reason")
    source = Path("src/operator_communication.py").read_text(encoding="utf-8").lower()
    assert not any(term in source for term in (
        "semantic_extractor", "openai", "requests", "responses.parse", "evaluate_policy",
        "build_salesforce_preview",
    ))


def test_supported_provider_synthesis_can_replace_fallback_but_unsupported_prose_cannot():
    narrative = "Patient intentionally harmed themself today."
    supported = OperatorCommunication(
        incident_summary="The patient intentionally harmed themself during the reported event.",
        key_findings=("Patient harmed themself", "Act was intentional"),
        why_this_result=(
            "Intentional self-directed harm meets the workplace violence criteria."
        ),
    )
    result = run_analysis(
        Incident(incident_id="CASE_001", narrative=narrative),
        extractor=extraction_for(candidate_for(
            narrative, conduct=Conduct.SELF_HARM, direction=FactDirection.SELF_DIRECTED
        )),
        communicator=lambda _: OperatorCommunicationResult(
            status=OperatorCommunicationStatus.SUCCESS, communication=supported
        ),
    )
    assert result.communication == supported

    invented = supported.model_copy(update={
        "incident_summary": "The patient intentionally harmed themself and remains under restraint."
    })
    rejected = run_analysis(
        Incident(incident_id="CASE_001", narrative=narrative),
        extractor=extraction_for(candidate_for(
            narrative, conduct=Conduct.SELF_HARM, direction=FactDirection.SELF_DIRECTED
        )),
        communicator=lambda _: OperatorCommunicationResult(
            status=OperatorCommunicationStatus.SUCCESS, communication=invented
        ),
    )
    assert rejected.communication != invented
    assert rejected.communication.incident_summary == "Patient intentionally harmed themself today."
    facts = construct_communication_input(result.validation_result, result.policy_decision)
    invalid_cases = (
        (
            supported.model_copy(update={
                "incident_summary": "The patient intentionally harmed themself in a hallway."
            }),
            "unsupported detail introduced: hallway",
        ),
        (
            supported.model_copy(update={
                "incident_summary": "Violence Detected because the patient harmed themself."
            }),
            "incident summary restates the outcome",
        ),
    )
    for communication, expected_issue in invalid_cases:
        assert expected_issue in communication_validation_issues(communication, facts)


def test_unresolved_contradiction_summary_is_understandable_without_internal_terms():
    first = "Witness A said the patient intentionally struck the nurse today."
    second = "Witness B questioned whether the patient struck the nurse today."
    projected = tuple(
        CommunicationFact(
            conduct=Conduct.PHYSICAL_CONTACT,
            direction=FactDirection.INTERPERSONAL,
            intentionality=Intentionality.INTENTIONAL,
            temporal_scope=TemporalScope.CURRENT,
            assertion_status=AssertionStatus.DISPUTED,
            resolution_status=ResolutionStatus.ACTIVE,
            uncertainty=(UncertaintyDimension.ASSERTION_STATUS,),
            evidence_excerpts=(excerpt,),
        )
        for excerpt in (first, second)
    )
    facts = OperatorCommunicationInput(
        outcome=PolicyOutcome.UNCERTAIN,
        incident_direction=IncidentDirection.INTERPERSONAL,
        active_facts=projected,
        superseded_facts=(),
        has_unresolved_contradiction=True,
    )
    communication = build_deterministic_communication(facts)
    assert "accounts disagree" in communication.incident_summary.casefold()
    assert "patient and nurse" in communication.incident_summary.casefold()
    assert all(term not in communication.incident_summary.casefold() for term in (
        "assertion", "resolution", "contradiction group", "validation",
    ))
