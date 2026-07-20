import importlib

from src.config import AppConfig
from src.contracts import (
    AssertionStatus,
    Conduct,
    FactDirection,
    Intentionality,
    MaterialAttribute,
    ProviderFactCandidate,
    ProviderFactEvidenceCandidate,
    ProviderStructuredResponse,
    ResolutionStatus,
    TemporalScope,
    TrueNorthSemanticEnvelope,
)
from src.models import Incident
from src.semantic_extractor import SemanticExtractionStatus, extract_semantic_envelope


class FakeResponses:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return type("Response", (), {"output_parsed": self.parsed})()


class FakeClient:
    def __init__(self, parsed):
        self.responses = FakeResponses(parsed)


def provider_response(narrative="Patient intentionally struck the nurse today."):
    return ProviderStructuredResponse(facts=[ProviderFactCandidate(
        local_ref="strike",
        conduct=Conduct.PHYSICAL_CONTACT,
        direction=FactDirection.INTERPERSONAL,
        intentionality=Intentionality.INTENTIONAL,
        temporal_scope=TemporalScope.CURRENT,
        assertion_status=AssertionStatus.AFFIRMED,
        resolution_status=ResolutionStatus.ACTIVE,
        evidence=[ProviderFactEvidenceCandidate(
            excerpt=narrative,
            supports=list(MaterialAttribute)[:5],
        )],
        uncertainty=[],
    )])


def test_extractor_makes_exactly_one_request_and_returns_true_north_envelope():
    narrative = "Patient intentionally struck the nurse today."
    client = FakeClient(provider_response(narrative))
    result = extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative=narrative),
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
        client=client,
    )
    assert result.status == SemanticExtractionStatus.SUCCESS
    assert type(result.semantic_candidate) is TrueNorthSemanticEnvelope
    assert len(client.responses.calls) == 1
    call = client.responses.calls[0]
    assert set(call) == {"model", "instructions", "input", "text_format"}
    assert call["input"] == narrative
    assert call["text_format"] is ProviderStructuredResponse


def test_default_client_disables_sdk_retries(monkeypatch):
    narrative = "Patient intentionally struck the nurse today."
    client = FakeClient(provider_response(narrative))
    constructor_calls = []

    def fake_openai(**kwargs):
        constructor_calls.append(kwargs)
        return client

    monkeypatch.setattr("src.semantic_extractor.OpenAI", fake_openai)
    result = extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative=narrative),
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
    )
    assert result.succeeded
    assert constructor_calls == [{"api_key": "test", "max_retries": 0}]


def test_missing_configuration_and_missing_structured_output_fail_closed():
    incident = Incident(incident_id="CASE_001", narrative="text")
    missing_config = extract_semantic_envelope(
        incident,
        config=AppConfig(openai_api_key=None, openai_model="test-model"),
    )
    assert missing_config.status == SemanticExtractionStatus.CONFIGURATION_FAILURE
    missing_output = extract_semantic_envelope(
        incident,
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
        client=FakeClient(None),
    )
    assert missing_output.status == SemanticExtractionStatus.STRUCTURED_RESPONSE_FAILURE


def test_provider_bookkeeping_or_malformed_output_is_validation_failure_without_repair():
    client = FakeClient({"facts": [], "incident_id": "provider-authored"})
    result = extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative="text"),
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
        client=client,
    )
    assert result.status == SemanticExtractionStatus.VALIDATION_FAILURE
    assert len(client.responses.calls) == 1


def test_import_performs_no_provider_request():
    import src.semantic_extractor as module
    importlib.reload(module)
