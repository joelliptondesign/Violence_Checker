import importlib
import sys
from types import SimpleNamespace

import pytest

from src.config import DEFAULT_OPENAI_MODEL, AppConfig, load_config
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Incident, Intentionality, ViolenceEventType, ViolenceFinding
from src.semantic_extractor import (
    SemanticExtractionStatus,
    extract_violence_finding,
)


PRESENT_CREDENTIAL = "present"


def valid_payload(**overrides):
    payload = {
        "violence_present": True,
        "event_type": ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
        "actor": "pt",
        "target": "rn",
        "contact_occurred": False,
        "injury_mentioned": False,
        "current_event": True,
        "intentionality": Intentionality.INTENTIONAL,
        "negated": False,
        "correction_present": False,
        "conflicting_information": False,
        "evidence_text": ["pt swung at rn missed"],
        "confidence": 0.88,
        "uncertainty_notes": ["No contact occurred because the swing missed."],
    }
    payload.update(overrides)
    return payload


class FakeResponses:
    def __init__(self, parsed=None, exception=None):
        self.parsed = parsed
        self.exception = exception
        self.requests = []

    def parse(self, **kwargs):
        self.requests.append(kwargs)
        if self.exception is not None:
            raise self.exception
        return SimpleNamespace(output_parsed=self.parsed)


class FakeClient:
    def __init__(self, parsed=None, exception=None):
        self.responses = FakeResponses(parsed=parsed, exception=exception)


def case_008():
    return next(
        item["incident"]
        for item in SYNTHETIC_INCIDENTS
        if item["incident"].incident_id == "CASE_008"
    )


def test_semantic_module_imports_without_openai_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    module = importlib.import_module("src.semantic_extractor")

    assert hasattr(module, "extract_violence_finding")


def test_invoking_extraction_without_openai_api_key_returns_config_failure(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = extract_violence_finding(case_008(), config=AppConfig())

    assert result.status == SemanticExtractionStatus.CONFIGURATION_FAILURE
    assert result.finding is None


def test_openai_model_default_is_available(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    assert load_config().openai_model == DEFAULT_OPENAI_MODEL


def test_request_construction_uses_one_provider_request_and_original_narrative():
    incident = case_008()
    client = FakeClient(parsed=valid_payload())

    result = extract_violence_finding(
        incident,
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL, openai_model="demo-model"),
        client=client,
    )

    assert result.succeeded is True
    assert len(client.responses.requests) == 1
    request = client.responses.requests[0]
    assert request["model"] == "demo-model"
    assert request["input"] == "pt swung at rn missed. security called"
    assert request["input"] == incident.narrative
    assert request["text_format"] is ViolenceFinding
    assert "metadata" not in request


def test_valid_structured_output_returns_violence_finding_with_exact_evidence():
    client = FakeClient(parsed=valid_payload())

    result = extract_violence_finding(
        case_008(),
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    assert result.status == SemanticExtractionStatus.SUCCESS
    assert isinstance(result.finding, ViolenceFinding)
    assert result.finding.evidence_text == ["pt swung at rn missed"]


def test_provider_exception_returns_request_failure():
    client = FakeClient(exception=RuntimeError("provider unavailable"))

    result = extract_violence_finding(
        case_008(),
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    assert result.status == SemanticExtractionStatus.REQUEST_FAILURE
    assert result.finding is None


def test_missing_parsed_output_returns_structured_response_failure():
    client = FakeClient(parsed=None)

    result = extract_violence_finding(
        case_008(),
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    assert result.status == SemanticExtractionStatus.STRUCTURED_RESPONSE_FAILURE
    assert result.finding is None


def test_malformed_parsed_output_returns_validation_failure():
    client = FakeClient(parsed={"violence_present": True})

    result = extract_violence_finding(
        case_008(),
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    assert result.status == SemanticExtractionStatus.VALIDATION_FAILURE
    assert result.finding is None


def test_invalid_enum_returns_validation_failure():
    client = FakeClient(parsed=valid_payload(event_type="physical"))

    result = extract_violence_finding(
        case_008(),
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    assert result.status == SemanticExtractionStatus.VALIDATION_FAILURE
    assert result.finding is None


def test_invalid_confidence_returns_validation_failure():
    client = FakeClient(parsed=valid_payload(confidence=2.0))

    result = extract_violence_finding(
        case_008(),
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    assert result.status == SemanticExtractionStatus.VALIDATION_FAILURE
    assert result.finding is None


def test_pydantic_parse_exception_returns_validation_failure():
    with pytest.raises(Exception) as captured:
        ViolenceFinding.model_validate({"violence_present": True})
    assert captured.value is not None
    client = FakeClient(exception=captured.value)

    result = extract_violence_finding(
        case_008(),
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    assert result.status == SemanticExtractionStatus.VALIDATION_FAILURE
    assert result.finding is None


def test_no_default_finding_is_substituted_after_failure():
    client = FakeClient(parsed=valid_payload(event_type="physical"))

    result = extract_violence_finding(
        case_008(),
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    assert result.finding is None


def test_semantic_extractor_does_not_import_streamlit_or_regex_logic(monkeypatch):
    sys.modules.pop("streamlit", None)
    sys.modules.pop("src.regex_baseline", None)

    importlib.reload(importlib.import_module("src.semantic_extractor"))

    assert "streamlit" not in sys.modules
    assert "src.regex_baseline" not in sys.modules


def test_module_import_performs_no_provider_request(monkeypatch):
    class ExplodingOpenAI:
        def __init__(self, *args, **kwargs):
            raise AssertionError("provider client should not be constructed on import")

    module = importlib.import_module("src.semantic_extractor")
    monkeypatch.setattr(module, "OpenAI", ExplodingOpenAI)

    importlib.reload(module)


def test_fixture_metadata_is_not_supplied_to_provider_request():
    fixture = next(item for item in SYNTHETIC_INCIDENTS if item["incident"].incident_id == "CASE_008")
    incident = Incident(
        incident_id=fixture["incident"].incident_id,
        narrative=fixture["incident"].narrative,
    )
    client = FakeClient(parsed=valid_payload())

    extract_violence_finding(
        incident,
        config=AppConfig(openai_api_key=PRESENT_CREDENTIAL),
        client=client,
    )

    request = client.responses.requests[0]
    assert fixture["metadata"]["scenario_type"] not in str(request)
