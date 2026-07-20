import json
import importlib
from pathlib import Path

import pytest

import src.app_logic as app_logic
from src.app_logic import AnalysisResult, run_analysis
from src.config import AppConfig
from src.contracts import OperatorCommunication, PipelineFailureProvenance, PolicyOutcome
from src.evaluation.corpus import load_corpus
from src.models import Incident
from src.operator_communication import construct_communication_input
from src.operator_communication_provider import (
    OperatorCommunicationResult,
    OperatorCommunicationStatus,
    generate_operator_communication,
)
from src.operator_communication_prompt import OPERATOR_COMMUNICATION_PROMPT
from src.policy import failed_policy_decision
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


CASE = load_corpus().cases[0]
PROVIDER_PAYLOAD = OperatorCommunication(
    incident_summary="A patient struck a nurse during the current incident.",
    key_findings=("Physical assault reported", "Patient involved", "Registered nurse involved"),
    why_this_result="The incident documents a patient striking a nurse, satisfying the application criteria for a workplace violence incident.",
)


class FakeResponses:
    def __init__(self, parsed=PROVIDER_PAYLOAD, *, status="completed", error=None):
        self.parsed = parsed
        self.status = status
        self.error = error
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return type("Response", (), {"output_parsed": self.parsed, "status": self.status})()


class FakeClient:
    def __init__(self, responses=None):
        self.responses = responses or FakeResponses()


def authoritative_result(*, communicator=None, candidate=None):
    semantic_calls = []

    def extractor(incident):
        semantic_calls.append(incident)
        return SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            candidate or CASE.ground_truth.semantic_envelope,
        )

    result = run_analysis(
        Incident(incident_id=CASE.case_id, narrative=CASE.narrative),
        extractor=extractor,
        communicator=communicator,
    )
    assert isinstance(result, AnalysisResult)
    return result, semantic_calls


def facts_for_provider():
    result, _ = authoritative_result()
    return construct_communication_input(
        result.validation_result,
        result.policy_decision,
        result.regex_result,
        result.comparison,
        salesforce_preview_eligible=result.salesforce_preview is not None,
    )


def configured(client):
    return lambda facts: generate_operator_communication(
        facts,
        config=AppConfig(
            openai_api_key="test-key",
            openai_model="semantic-model",
            openai_communication_model="communication-model",
        ),
        client=client,
    )


def test_provider_makes_one_strict_structured_request_from_narrow_facts():
    client = FakeClient()
    facts = facts_for_provider()
    result = configured(client)(facts)

    assert result == OperatorCommunicationResult(
        status=OperatorCommunicationStatus.SUCCESS,
        communication=PROVIDER_PAYLOAD,
    )
    assert len(client.responses.calls) == 1
    call = client.responses.calls[0]
    assert set(call) == {"model", "instructions", "input", "text_format"}
    assert call["model"] == "communication-model"
    assert call["text_format"] is OperatorCommunication
    sent = json.loads(call["input"])
    assert sent == facts.model_dump(mode="json")
    assert not any("narrative" in key.lower() for key in sent)
    assert not any("narrative" in key.lower() for key in sent["comparison"])
    assert CASE.narrative not in call["input"]


def test_default_client_disables_retries(monkeypatch):
    client = FakeClient()
    constructor_calls = []

    def fake_openai(**kwargs):
        constructor_calls.append(kwargs)
        return client

    monkeypatch.setattr("src.operator_communication_provider.OpenAI", fake_openai)
    result = generate_operator_communication(
        facts_for_provider(),
        config=AppConfig(openai_api_key="test-key", openai_communication_model="communication-model"),
    )
    assert result.succeeded
    assert constructor_calls == [{"api_key": "test-key", "max_retries": 0}]
    assert len(client.responses.calls) == 1


def test_missing_configuration_returns_failure_without_request():
    client = FakeClient()
    result = generate_operator_communication(
        facts_for_provider(),
        config=AppConfig(openai_api_key=None),
        client=client,
    )
    assert result.status == OperatorCommunicationStatus.CONFIGURATION_FAILURE
    assert client.responses.calls == []


def test_untyped_input_is_rejected_without_request():
    client = FakeClient()
    result = generate_operator_communication(
        {"policy_outcome": "WRITE_DETECTED"},
        config=AppConfig(openai_api_key="test-key"),
        client=client,
    )
    assert result.status == OperatorCommunicationStatus.VALIDATION_FAILURE
    assert client.responses.calls == []


@pytest.mark.parametrize(
    "responses,expected_status",
    [
        (FakeResponses(error=RuntimeError("unavailable")), OperatorCommunicationStatus.REQUEST_FAILURE),
        (FakeResponses(status="incomplete"), OperatorCommunicationStatus.STRUCTURED_RESPONSE_FAILURE),
        (FakeResponses(parsed=None), OperatorCommunicationStatus.STRUCTURED_RESPONSE_FAILURE),
        (FakeResponses(parsed={"incident_summary": "only one field"}), OperatorCommunicationStatus.VALIDATION_FAILURE),
        (FakeResponses(parsed={**PROVIDER_PAYLOAD.model_dump(), "outcome": "WRITE_NOT_DETECTED"}), OperatorCommunicationStatus.VALIDATION_FAILURE),
    ],
)
def test_provider_failure_states_are_bounded_and_return_no_payload(responses, expected_status):
    result = configured(FakeClient(responses))(facts_for_provider())
    assert result.status == expected_status
    assert result.communication is None
    assert len(responses.calls) == 1


def test_valid_configured_analysis_has_one_semantic_and_one_communication_request():
    client = FakeClient()
    result, semantic_calls = authoritative_result(communicator=configured(client))
    assert len(semantic_calls) == 1
    assert len(client.responses.calls) == 1
    assert result.communication == PROVIDER_PAYLOAD


def test_valid_unconfigured_analysis_has_one_semantic_and_zero_communication_requests():
    client = FakeClient()
    communicator = lambda facts: generate_operator_communication(
        facts,
        config=AppConfig(openai_api_key=None),
        client=client,
    )
    result, semantic_calls = authoritative_result(communicator=communicator)
    assert len(semantic_calls) == 1
    assert client.responses.calls == []
    assert result.communication != PROVIDER_PAYLOAD


def test_invalid_input_has_zero_semantic_and_communication_requests():
    semantic_calls = []
    communication_calls = []
    run_analysis(
        {"incident_id": "X", "narrative": " "},
        extractor=lambda item: semantic_calls.append(item),
        communicator=lambda facts: communication_calls.append(facts),
    )
    assert semantic_calls == []
    assert communication_calls == []


def test_extraction_failure_has_one_semantic_and_zero_communication_requests():
    semantic_calls = []
    communication_calls = []

    def extractor(incident):
        semantic_calls.append(incident)
        return SemanticExtractionResult(SemanticExtractionStatus.REQUEST_FAILURE, failure_message="bounded")

    result = run_analysis(
        Incident(incident_id="FAIL", narrative="synthetic input"),
        extractor=extractor,
        communicator=lambda facts: communication_calls.append(facts),
    )
    assert len(semantic_calls) == 1
    assert communication_calls == []
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED


def test_validation_failure_has_one_semantic_and_zero_communication_requests():
    communication_calls = []
    invalid = CASE.ground_truth.semantic_envelope.model_copy(update={"schema_version": "unsupported"})
    result, semantic_calls = authoritative_result(
        candidate=invalid,
        communicator=lambda facts: communication_calls.append(facts),
    )
    assert len(semantic_calls) == 1
    assert communication_calls == []
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED


def test_failed_policy_has_zero_communication_requests(monkeypatch):
    communication_calls = []
    monkeypatch.setattr(
        app_logic,
        "evaluate_policy",
        lambda **_kwargs: failed_policy_decision(PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT),
    )
    result, semantic_calls = authoritative_result(
        communicator=lambda facts: communication_calls.append(facts),
    )
    assert len(semantic_calls) == 1
    assert communication_calls == []
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED


def test_provider_failure_retains_fallback_and_authoritative_fields():
    expected, _ = authoritative_result()
    failed, _ = authoritative_result(
        communicator=configured(FakeClient(FakeResponses(error=RuntimeError("unavailable"))))
    )
    assert failed.communication == expected.communication
    assert failed.validation_result == expected.validation_result
    assert failed.policy_decision == expected.policy_decision
    assert failed.comparison == expected.comparison
    assert failed.salesforce_preview == expected.salesforce_preview


def test_provider_module_import_is_inert_and_sdk_objects_do_not_cross_boundary():
    source = Path("src/operator_communication_provider.py").read_text(encoding="utf-8")
    assert "Incident" not in source
    assert "semantic_extractor" not in source
    assert "semantic_prompt" not in source
    assert "evaluate_policy" not in source
    assert set(OperatorCommunicationResult.__annotations__) == {"status", "communication", "failure_message"}


def test_non_analysis_import_constructs_no_provider_client(monkeypatch):
    import src.operator_communication_provider as module

    constructor_calls = []
    monkeypatch.setattr(module, "OpenAI", lambda **kwargs: constructor_calls.append(kwargs))
    importlib.reload(module)
    assert constructor_calls == []


def test_prompt_is_bounded_to_three_presentation_sections_and_preserved_authority():
    prompt = OPERATOR_COMMUNICATION_PROMPT.lower()
    assert all(field in prompt for field in ("incident_summary", "key_findings", "why_this_result"))
    assert "preserve the supplied result" in prompt
    assert "do not introduce, infer, or hallucinate facts" in prompt
    assert "do not provide recommendations" in prompt
    assert "presentation-only" in prompt
    assert "unsupported claims" in prompt
    assert "participant roles" in prompt
    assert "synthesize" in prompt
    assert CASE.narrative.lower() not in prompt
    assert "hospital workplace safety incident review" in prompt
    assert "hospital operations leaders" in prompt
    assert "patient safety leaders" in prompt
    assert "workplace violence reviewers" in prompt
    assert "not ai engineers" in prompt
    assert all(word in prompt for word in ("natural", "concise", "professional", "operational", "human"))
    assert "experienced incident reviewer" in prompt
    assert "not an llm" in prompt
    assert "combine related facts into coherent operational sentences" in prompt
    assert "do not produce one sentence per supplied fact" in prompt
    assert "do not translate supplied facts one-by-one" in prompt
    assert "combine related facts into natural operational prose" in prompt
    assert "communication quality matters more than exhaustive enumeration" in prompt
    assert "write only in third person or passive voice" in prompt
    assert '"i," "me," "my," "we," or "our."' in prompt
    assert all(phrase in prompt for phrase in ("the ai determined", "the model understood", "our analysis"))
    prohibited_terms = (
        "assertion",
        "active",
        "intentionality",
        "completion",
        "temporal scope",
        "validation",
        "policy",
        "repository",
        "schema",
        "reason code",
        "entity id",
        "proposition",
        "relationship",
        "bounded uncertainty",
        "classification metadata",
    )
    assert "never translate supplied fields one-by-one or directly into english" in prompt
    assert "never expose these internal implementation terms" in prompt
    assert all(term in prompt for term in prohibited_terms)
    assert "communicate only their operational meaning in natural language" in prompt
    assert prompt.count("good example") >= 3
    assert prompt.count("bad example") >= 3
    assert "a patient intentionally struck a registered nurse" in prompt
    assert "security responded and the nurse sustained a visible injury" in prompt
    assert "patient involved" in prompt
    assert "registered nurse involved" in prompt
    assert "injury documented" in prompt
    assert "satisfying the application's criteria for a workplace violence incident" in prompt
    assert "the assertion is affirmed" in prompt
    assert "physical conduct completed" in prompt
    assert "i understood intentionality intentional" in prompt
    assert "translate operational meaning" in prompt
    assert "do not translate internal fields literally" in prompt
    assert 'internal "active": omit unless operationally important' in prompt
    assert 'internal "completion = completed": prefer "physical contact occurred."' in prompt
    assert 'internal "intentionality = intentional"' in prompt
    assert 'internal "patient identified": prefer "patient involved."' in prompt
    assert 'internal "registered nurse identified": prefer "registered nurse involved."' in prompt
    assert 'internal "temporal scope = current": prefer "during the reported incident."' in prompt
    assert 'internal "assertion affirmed": omit completely' in prompt
    assert "significant consequences and responses" in prompt
    assert all(
        consequence in prompt
        for consequence in (
            "injuries",
            "visible injuries",
            "fractures",
            "loss of consciousness",
            "bleeding",
            "property damage",
            "broken doors",
            "broken windows",
            "damaged equipment",
            "security response",
            "police response",
            "restraints",
            "weapon involvement",
        )
    )
    assert "highest-priority findings" in prompt
    assert all(
        finding in prompt
        for finding in (
            "physical assault reported",
            "verbal threat identified",
            "weapon mentioned",
            "property damage documented",
            "visitor involved",
        )
    )
    assert "do not restate information already implied by stronger language" in prompt
    assert "the stronger sentence already communicates contact" in prompt
    assert "hospital executive has thirty seconds" in prompt
    assert "every sentence must improve operational understanding" in prompt
    assert "avoid filler" in prompt
    assert "prefer the most operationally meaningful information" in prompt


def test_provider_and_fallback_share_the_exact_communication_contract():
    fallback, _ = authoritative_result()
    provider, _ = authoritative_result(communicator=configured(FakeClient()))
    assert fallback.communication is not None
    assert provider.communication is not None
    assert tuple(type(fallback.communication).model_fields) == tuple(type(provider.communication).model_fields)
    assert set(provider.communication.model_dump()) == {"incident_summary", "key_findings", "why_this_result"}
