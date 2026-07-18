from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from src.compatibility_finding import (
    CompatibilityFindingStatus,
    construct_compatibility_finding,
)
from src.contracts import ProviderStructuredResponse, SemanticFacts
from src.models import Intentionality, ViolenceEventType, ViolenceFinding
from src.provider_adapter import semantic_candidate_from_provider_response
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from src.semantic_validation import validate_semantic_candidate
from src.semantic_prompt import SEMANTIC_EXTRACTION_PROMPT


def fact_values(**overrides):
    values = {
        "violence_present": True,
        "event_type": ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
        "actor": "patient",
        "target": "nurse",
        "contact_occurred": False,
        "injury_mentioned": False,
        "current_event": True,
        "intentionality": Intentionality.INTENTIONAL,
        "negated": False,
        "correction_present": False,
        "conflicting_information": False,
        "evidence_text": ["patient swung at the nurse and missed"],
        "confidence": 0.82,
        "uncertainty_notes": ["No contact was described."],
    }
    values.update(overrides)
    return values


def test_provider_response_adapts_to_independent_serializable_semantic_facts():
    provider = ProviderStructuredResponse(**fact_values())

    candidate = semantic_candidate_from_provider_response(provider)
    validation = validate_semantic_candidate(candidate)
    facts = validation.validated_facts.facts

    assert type(facts) is SemanticFacts
    assert facts.model_dump(mode="json") == provider.model_dump(mode="json")
    assert facts.event_type == ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE
    assert facts.intentionality == Intentionality.INTENTIONAL
    assert facts.actor == "patient"
    assert facts.target == "nurse"
    assert facts.contact_occurred is False
    assert facts.injury_mentioned is False
    assert facts.current_event is True
    assert facts.negated is False
    assert facts.correction_present is False
    assert facts.conflicting_information is False
    assert facts.evidence_text == ["patient swung at the nurse and missed"]
    assert facts.confidence == 0.82
    assert facts.uncertainty_notes == ["No contact was described."]


def test_semantic_contracts_have_no_operational_policy_workflow_or_salesforce_fields():
    forbidden = {
        "policy_decision",
        "write_disposition",
        "salesforce_payload",
        "workflow_action",
        "operational_finding",
        "display_status",
    }

    assert forbidden.isdisjoint(SemanticFacts.model_fields)
    assert forbidden.isdisjoint(ProviderStructuredResponse.model_fields)


def test_semantic_event_type_and_intentionality_are_bounded():
    with pytest.raises(ValidationError):
        SemanticFacts(**fact_values(event_type="physical"))
    with pytest.raises(ValidationError):
        SemanticFacts(**fact_values(intentionality="maybe"))


def test_semantic_success_requires_facts_and_failures_cannot_carry_facts():
    facts = SemanticFacts(**fact_values())
    with pytest.raises(ValueError):
        SemanticExtractionResult(status=SemanticExtractionStatus.SUCCESS)
    with pytest.raises(ValueError):
        SemanticExtractionResult(
            status=SemanticExtractionStatus.REQUEST_FAILURE,
            semantic_candidate=facts,
        )


def test_compatibility_construction_maps_exactly_and_is_deterministic():
    facts = SemanticFacts(**fact_values())

    validated = validate_semantic_candidate(facts).validated_facts
    first = construct_compatibility_finding(validated)
    second = construct_compatibility_finding(validated)

    assert first == second
    assert first.status == CompatibilityFindingStatus.SUCCESS
    assert isinstance(first.finding, ViolenceFinding)
    assert first.finding.model_dump(mode="json") == facts.model_dump(mode="json")


def test_compatibility_construction_makes_no_provider_call(monkeypatch):
    provider = Mock(side_effect=AssertionError("provider must not be called"))
    monkeypatch.setattr("openai.OpenAI", provider)

    validated = validate_semantic_candidate(SemanticFacts(**fact_values())).validated_facts
    result = construct_compatibility_finding(validated)

    assert result.succeeded is True
    provider.assert_not_called()


def test_inconsistent_facts_do_not_produce_default_finding():
    facts = SemanticFacts(
        **fact_values(
            violence_present=True,
            event_type=ViolenceEventType.NONE,
        )
    )

    validation = validate_semantic_candidate(facts)
    result = construct_compatibility_finding(validation.validated_facts)

    assert validation.passed is False
    assert result.status == CompatibilityFindingStatus.VALIDATION_FAILURE
    assert result.finding is None
    assert result.failure_message == "TypeError"


def test_non_semantic_input_does_not_produce_compatibility_finding():
    result = construct_compatibility_finding(object())

    assert result.status == CompatibilityFindingStatus.VALIDATION_FAILURE
    assert result.finding is None


def test_prompt_limits_provider_to_semantic_extraction_and_preserves_grounding():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()

    assert "only structured semantic facts" in prompt
    assert "exact excerpts copied" in prompt
    assert "current_event" in prompt
    assert "historical" in prompt
    assert "negation" in prompt
    assert "corrections" in prompt
    assert "conflicting" in prompt
    assert "contact_occurred" in prompt
    assert "intentional" in prompt
    assert "actor or target" in prompt
    assert "do not make operational recommendations" in prompt
    assert "hospital workflow decisions" in prompt
    assert "salesforce write decisions" in prompt
    assert "legal, clinical, or safety recommendations" in prompt
