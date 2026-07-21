from pathlib import Path

import pytest
from pydantic import ValidationError

from src.app_logic import run_analysis
from src.contracts import (
    Conduct, FactDirection, Intentionality, OperatorCommunication,
    OperatorCommunicationInput, PolicyOutcome, TemporalScope, UncertaintyDimension,
)
from src.models import Incident
from src.operator_communication import construct_communication_input
from src.operator_communication_provider import OperatorCommunicationResult, OperatorCommunicationStatus
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from tests.test_app_logic import candidate_for, extraction_for


def analyze(narrative, **updates):
    return run_analysis(
        Incident(incident_id="CASE_001", narrative=narrative),
        extractor=extraction_for(candidate_for(narrative, **updates)),
    )


def test_projection_is_narrow_and_communication_contract_is_bounded():
    result = analyze("Patient intentionally struck the nurse today.")
    facts = construct_communication_input(result.validation_result, result.policy_decision)
    assert set(OperatorCommunicationInput.model_fields) == {
        "outcome", "incident_direction", "active_facts", "superseded_facts",
        "has_unresolved_contradiction",
    }
    assert set(OperatorCommunication.model_fields) == {"incident_summary", "key_findings", "why_this_result"}
    assert not hasattr(facts, "narrative")
    assert facts.outcome == PolicyOutcome.VIOLENCE_DETECTED


@pytest.mark.parametrize(
    "narrative,updates,expected",
    [
        ("Patient intentionally struck the nurse today.", {}, "physical violence"),
        ("Patient accidentally contacted the nurse today.", {"intentionality": Intentionality.ACCIDENTAL}, "accidental"),
        ("Patient threatened the nurse years ago.", {"conduct": Conduct.VERBAL_THREAT, "temporal_scope": TemporalScope.HISTORICAL}, "historical"),
        ("Patient intentionally harmed themself today.", {"conduct": Conduct.SELF_HARM, "direction": FactDirection.SELF_DIRECTED}, "self-directed"),
        ("Patient intentionally damaged property today.", {"conduct": Conduct.PROPERTY_VIOLENCE, "direction": FactDirection.OBJECT_DIRECTED}, "property-directed"),
        ("Patient may have struck the nurse today.", {"intentionality": Intentionality.UNRESOLVED, "uncertainty": [UncertaintyDimension.INTENTIONALITY]}, "remains unresolved"),
    ],
)
def test_fallback_covers_detected_negative_and_uncertain_states(narrative, updates, expected):
    result = analyze(narrative, **updates)
    rendered = f"{result.communication.incident_summary} {result.communication.why_this_result}".lower()
    assert expected in rendered


def test_unable_fallback_and_provider_failure_do_not_create_preview():
    result = run_analysis(
        Incident(incident_id="FAIL", narrative="Patient struck a nurse."),
        extractor=lambda _: SemanticExtractionResult(SemanticExtractionStatus.REQUEST_FAILURE, failure_message="bounded"),
    )
    assert result.policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE
    assert result.salesforce_preview is None
    assert "could not be classified" in result.communication.incident_summary


def test_contract_rejects_extra_empty_and_implementation_language():
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="", key_findings=("Fact available",), why_this_result="Reason")
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="Summary", key_findings=("Too many words in this finding here",), why_this_result="Reason")
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="A schema version was used.", key_findings=("Fact available",), why_this_result="Reason")


def test_communication_module_has_no_provider_semantic_or_network_authority():
    source = Path("src/operator_communication.py").read_text(encoding="utf-8").lower()
    assert not any(term in source for term in ("semantic_extractor", "openai", "requests", "responses.parse", "evaluate_policy", "build_salesforce_preview"))


def test_provider_prose_cannot_replace_bounded_deterministic_communication():
    narrative = "Patient intentionally harmed themself today."
    invented = OperatorCommunication(
        incident_summary="The self-harm is current and ongoing.",
        key_findings=("Ongoing harm confirmed",),
        why_this_result="The unresolved incident remains ongoing.",
    )
    result = run_analysis(
        Incident(incident_id="CASE_001", narrative=narrative),
        extractor=extraction_for(candidate_for(
            narrative,
            conduct=Conduct.SELF_HARM,
            direction=FactDirection.SELF_DIRECTED,
        )),
        communicator=lambda _: OperatorCommunicationResult(
            status=OperatorCommunicationStatus.SUCCESS,
            communication=invented,
        ),
    )
    assert result.communication != invented
    assert result.communication.incident_summary == (
        "Intentional self-directed violence was reported during the current incident."
    )
