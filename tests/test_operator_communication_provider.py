import json

import pytest

from src.app_logic import run_analysis
from src.config import AppConfig
from src.contracts import OperatorCommunication
from src.models import Incident
from src.operator_communication import construct_communication_input
from src.operator_communication_provider import (
    OperatorCommunicationResult, OperatorCommunicationStatus, generate_operator_communication,
)
from tests.test_app_logic import candidate_for, extraction_for


PAYLOAD = OperatorCommunication(
    incident_summary="Intentional physical violence was reported during the current incident.",
    key_findings=("Physical violence identified", "Current incident confirmed"),
    why_this_result="The supplied operational facts establish qualifying current conduct.",
)


class FakeResponses:
    def __init__(self, parsed=PAYLOAD, status="completed", error=None):
        self.parsed, self.status, self.error, self.calls = parsed, status, error, []
    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return type("Response", (), {"output_parsed": self.parsed, "status": self.status})()


class FakeClient:
    def __init__(self, responses=None):
        self.responses = responses or FakeResponses()


def facts_for_provider():
    narrative = "Patient intentionally struck the nurse today."
    result = run_analysis(Incident(incident_id="CASE_001", narrative=narrative), extractor=extraction_for(candidate_for(narrative)))
    return construct_communication_input(result.validation_result, result.policy_decision)


def configured(client):
    return generate_operator_communication(
        facts_for_provider(),
        config=AppConfig(openai_api_key="key", openai_communication_model="communication-model"),
        client=client,
    )


def test_provider_sends_one_strict_request_with_only_narrow_facts():
    client = FakeClient()
    result = configured(client)
    assert result == OperatorCommunicationResult(status=OperatorCommunicationStatus.SUCCESS, communication=PAYLOAD)
    assert len(client.responses.calls) == 1
    call = client.responses.calls[0]
    sent = json.loads(call["input"])
    assert set(call) == {"model", "instructions", "input", "text_format"}
    assert call["text_format"] is OperatorCommunication
    assert sent == facts_for_provider().model_dump(mode="json")
    assert "narrative" not in call["input"]


def test_missing_configuration_and_untyped_input_make_no_request():
    client = FakeClient()
    missing = generate_operator_communication(facts_for_provider(), config=AppConfig(openai_api_key=None), client=client)
    invalid = generate_operator_communication({}, config=AppConfig(openai_api_key="key"), client=client)
    assert missing.status == OperatorCommunicationStatus.CONFIGURATION_FAILURE
    assert invalid.status == OperatorCommunicationStatus.VALIDATION_FAILURE
    assert client.responses.calls == []


@pytest.mark.parametrize("responses,status", [
    (FakeResponses(error=RuntimeError("down")), OperatorCommunicationStatus.REQUEST_FAILURE),
    (FakeResponses(status="incomplete"), OperatorCommunicationStatus.STRUCTURED_RESPONSE_FAILURE),
    (FakeResponses(parsed=None), OperatorCommunicationStatus.STRUCTURED_RESPONSE_FAILURE),
    (FakeResponses(parsed={"incident_summary": "incomplete"}), OperatorCommunicationStatus.VALIDATION_FAILURE),
])
def test_provider_failures_are_bounded(responses, status):
    result = configured(FakeClient(responses))
    assert result.status == status and result.communication is None
