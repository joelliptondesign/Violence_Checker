from src.app_logic import run_analysis
from src.config import AppConfig
from src.contracts import (
    AssertionStatus,
    ConductKind,
    PolicyOutcome,
    PolicyReasonCode,
    TemporalScope,
)
from src.fixtures import SYNTHETIC_INCIDENTS
from src.presentation import semantic_summary
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus, extract_semantic_envelope
from tests.successor_helpers import envelope


def test_all_fixtures_execute_one_successor_pipeline_deterministically():
    for item in SYNTHETIC_INCIDENTS:
        incident = item["incident"]
        calls = []
        def executor(value):
            calls.append(value)
            return SemanticExtractionResult(
                SemanticExtractionStatus.SUCCESS,
                envelope(narrative=value.narrative, incident_id=value.incident_id),
            )
        first = run_analysis(incident, extractor=executor)
        second = run_analysis(incident, extractor=executor)
        assert first.policy_decision == second.policy_decision
        assert first.validation_result.passed and second.validation_result.passed
        assert len(calls) == 2


def test_case_003_historical_disclosure_has_direct_successor_authority():
    fixture = next(item for item in SYNTHETIC_INCIDENTS if item["incident"].incident_id == "CASE_003")
    incident = fixture["incident"]
    provider_calls = []

    class Responses:
        def parse(self, **kwargs):
            provider_calls.append(kwargs)
            return type(
                "Response",
                (),
                {
                    "output_parsed": envelope(
                        narrative=incident.narrative,
                        provider=True,
                        conduct=ConductKind.PHYSICAL_CONDUCT,
                        temporal_scope=TemporalScope.HISTORICAL,
                        assertion_status=AssertionStatus.AFFIRMED,
                    )
                },
            )()

    client = type("Client", (), {"responses": Responses()})()

    def historical_extractor(value):
        return extract_semantic_envelope(
            value,
            config=AppConfig(openai_api_key="synthetic-test-key", openai_model="synthetic-test-model"),
            client=client,
        )

    result = run_analysis(incident, extractor=historical_extractor)
    validated = result.validation_result.validated_envelope
    assert len(provider_calls) == 1
    assert provider_calls[0]["input"] == incident.narrative
    assert provider_calls[0]["text_format"].__name__ == "ProviderStructuredResponse"
    assert fixture["metadata"] not in provider_calls[0].values()
    assert validated is not None
    assert validated.envelope.incident_id == "CASE_003"
    assert validated.envelope.propositions[0].conduct_kind == ConductKind.PHYSICAL_CONDUCT
    assert validated.envelope.propositions[0].temporal_scope == TemporalScope.HISTORICAL
    assert all(item.temporal_scope != TemporalScope.CURRENT_INCIDENT for item in validated.envelope.propositions)
    assert all(item.conduct_kind not in {ConductKind.THREAT_EXPRESSION, ConductKind.THREATENING_MOVEMENT} for item in validated.envelope.propositions)
    assert not validated.policy_candidate.active_current_interpersonal_violence
    assert not validated.policy_candidate.active_current_interpersonal_affirmed
    assert result.validation_result.schema_validation.passed
    assert result.validation_result.domain_validation.passed
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_NOT_DETECTED
    assert result.policy_decision.reason_codes == [PolicyReasonCode.NO_ACTIVE_CURRENT_INTERPERSONAL_VIOLENCE]
    assert semantic_summary(validated, result.policy_decision) == "No validated active current interpersonal proposition supports a detected outcome."
    assert result.salesforce_preview is not None
    assert result.salesforce_preview["Illustrative_Write_Disposition__c"] == "WRITE_NOT_DETECTED"
