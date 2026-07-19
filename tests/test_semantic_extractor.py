import importlib

from src.config import AppConfig
from src.models import Incident
from src.semantic_extractor import SemanticExtractionStatus, extract_semantic_envelope
from tests.successor_helpers import envelope


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


class RaisingResponses:
    def __init__(self, error):
        self.error = error
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        raise self.error


def test_extractor_makes_exactly_one_request_and_returns_typed_candidate():
    narrative = "Patient struck the nurse."
    client = FakeClient(envelope(narrative=narrative, provider=True))
    result = extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative=narrative),
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
        client=client,
    )
    assert result.status == SemanticExtractionStatus.SUCCESS
    assert len(client.responses.calls) == 1
    assert type(result.semantic_candidate).__name__ == "ViolenceSemanticEnvelope"
    assert client.responses.calls[0]["input"] == narrative


def test_missing_configuration_fails_without_request():
    result = extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative="text"),
        config=AppConfig(openai_api_key=None, openai_model="test-model"),
    )
    assert result.status == SemanticExtractionStatus.CONFIGURATION_FAILURE
    assert result.semantic_candidate is None


def test_missing_parsed_response_is_typed_failure():
    client = FakeClient(None)
    result = extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative="text"),
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
        client=client,
    )
    assert result.status == SemanticExtractionStatus.STRUCTURED_RESPONSE_FAILURE


def test_module_import_performs_no_provider_request():
    import src.semantic_extractor as module
    importlib.reload(module)


def test_provider_exception_is_typed_request_failure_after_one_attempt():
    client = type("Client", (), {"responses": RaisingResponses(RuntimeError("provider unavailable"))})()
    result = extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative="Patient struck the nurse."),
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
        client=client,
    )
    assert result.status == SemanticExtractionStatus.REQUEST_FAILURE
    assert result.failure_message == "RuntimeError"
    assert result.semantic_candidate is None
    assert len(client.responses.calls) == 1


def test_malformed_parsed_output_is_typed_validation_failure_without_default():
    client = FakeClient({"schema_identity": "wrong"})
    result = extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative="Patient struck the nurse."),
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
        client=client,
    )
    assert result.status == SemanticExtractionStatus.VALIDATION_FAILURE
    assert result.semantic_candidate is None
    assert len(client.responses.calls) == 1


def test_request_contains_only_prompt_model_contract_and_narrative():
    narrative = "Patient struck the nurse."
    client = FakeClient(envelope(narrative=narrative, provider=True))
    extract_semantic_envelope(
        Incident(incident_id="CASE_001", narrative=narrative),
        config=AppConfig(openai_api_key="test", openai_model="test-model"),
        client=client,
    )
    call = client.responses.calls[0]
    assert set(call) == {"model", "instructions", "input", "text_format"}
    assert call["model"] == "test-model"
    assert call["input"] == narrative
    assert call["text_format"].__name__ == "ProviderStructuredResponse"
