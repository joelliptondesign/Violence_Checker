import pytest
from unittest.mock import Mock

from src.contracts import PolicyDecision, PolicyOutcome, PolicyReasonCode, SemanticFacts
from src.models import Intentionality, ViolenceEventType, ViolenceFinding
from src.policy import evaluate_policy, failed_policy_decision
from src.salesforce_preview import build_salesforce_preview, preview_field_names
from src.semantic_validation import validate_semantic_candidate
from src.contracts import PipelineFailureProvenance


def valid_finding():
    return ViolenceFinding(
        violence_present=True,
        event_type=ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
        actor="pt",
        target="rn",
        contact_occurred=False,
        injury_mentioned=False,
        current_event=True,
        intentionality=Intentionality.INTENTIONAL,
        negated=False,
        correction_present=False,
        conflicting_information=False,
        evidence_text=["pt swung at rn missed"],
        confidence=0.9,
        uncertainty_notes=["missed indicates no contact"],
    )


def policy_for(finding):
    facts = SemanticFacts.model_validate(finding.model_dump())
    validated = validate_semantic_candidate(facts).validated_facts
    return evaluate_policy(validated_facts=validated, finding=finding)


def test_successful_validated_finding_produces_deterministic_dictionary():
    finding = valid_finding()
    first = build_salesforce_preview("CASE_008", finding, policy_for(finding))
    second = build_salesforce_preview("CASE_008", finding, policy_for(finding))

    assert first == second
    assert first["Illustrative_Incident_Identifier__c"] == "CASE_008"


def test_expected_illustrative_fields_are_present():
    finding = valid_finding()
    preview = build_salesforce_preview("CASE_008", finding, policy_for(finding))

    assert list(preview.keys()) == preview_field_names()


def test_evidence_remains_unchanged():
    finding = valid_finding()
    preview = build_salesforce_preview("CASE_008", finding, policy_for(finding))

    assert preview["Illustrative_Evidence__c"] == ["pt swung at rn missed"]


def test_invalid_objects_are_rejected():
    with pytest.raises(TypeError):
        build_salesforce_preview("CASE_008", None, policy_for(valid_finding()))


def test_policy_disposition_is_represented_without_independent_preview_logic():
    finding = valid_finding()
    policy = policy_for(finding)

    preview = build_salesforce_preview("CASE_008", finding, policy)

    assert policy.outcome == PolicyOutcome.WRITE_DETECTED
    assert preview["Illustrative_Write_Disposition__c"] == "WRITE_DETECTED"


def test_failed_policy_is_rejected():
    with pytest.raises(ValueError):
        build_salesforce_preview(
            "CASE_008",
            valid_finding(),
            failed_policy_decision(PipelineFailureProvenance.PROVIDER_REQUEST),
        )


def test_non_policy_object_is_rejected():
    with pytest.raises(TypeError):
        build_salesforce_preview("CASE_008", valid_finding(), object())


def test_preview_copies_authoritative_policy_without_redeciding():
    authoritative = PolicyDecision(
        policy_id="violence_checker_write_disposition",
        policy_version="1.0.1",
        outcome=PolicyOutcome.WRITE_DETECTED,
        reason_codes=[PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT],
        explanation="Validated facts affirmatively represent violence or a threat.",
    )

    preview = build_salesforce_preview("CASE_008", valid_finding(), authoritative)

    assert preview["Illustrative_Write_Disposition__c"] == "WRITE_DETECTED"


def test_preview_makes_no_provider_or_external_api_call(monkeypatch):
    provider = Mock(side_effect=AssertionError("preview must not call a provider"))
    monkeypatch.setattr("openai.OpenAI", provider)
    finding = valid_finding()

    build_salesforce_preview("CASE_008", finding, policy_for(finding))

    provider.assert_not_called()
