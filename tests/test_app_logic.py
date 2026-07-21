from src.app_logic import AnalysisResult, run_analysis
from src.contracts import (
    AssertionStatus, Conduct, FactDirection, InputValidationResult, Intentionality,
    PolicyOutcome, ProviderFactCandidate, ProviderMaterialAttribute,
    ProviderFactEvidenceCandidate, ProviderStructuredResponse, TemporalScope,
    UncertaintyDimension,
)
from src.models import Incident
from src.provider_adapter import semantic_candidate_from_provider_response
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


ALL_SUPPORTS = [
    ProviderMaterialAttribute.CONDUCT, ProviderMaterialAttribute.DIRECTION,
    ProviderMaterialAttribute.INTENTIONALITY, ProviderMaterialAttribute.TEMPORAL_SCOPE,
    ProviderMaterialAttribute.ASSERTION_STATUS,
]


def candidate_for(narrative="Patient intentionally struck the nurse today.", incident_id="CASE_001", **updates):
    values = dict(
        local_ref="fact", conduct=Conduct.PHYSICAL_CONTACT,
        direction=FactDirection.INTERPERSONAL,
        intentionality=Intentionality.INTENTIONAL,
        temporal_scope=TemporalScope.CURRENT,
        assertion_status=AssertionStatus.AFFIRMED,
        evidence=[ProviderFactEvidenceCandidate(excerpt=narrative, supports=ALL_SUPPORTS)],
        uncertainty=[],
    )
    values.update(updates)
    response = ProviderStructuredResponse(facts=[ProviderFactCandidate(**values)])
    return semantic_candidate_from_provider_response(
        response, incident=Incident(incident_id=incident_id, narrative=narrative)
    )


def extraction_for(candidate):
    return lambda _incident: SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, candidate)


def test_run_analysis_executes_true_north_pipeline_once():
    narrative = "Patient intentionally struck the nurse today."
    calls = []
    candidate = candidate_for(narrative)
    def extractor(incident):
        calls.append(incident)
        return SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, candidate)
    result = run_analysis(Incident(incident_id="CASE_001", narrative=narrative), extractor=extractor)
    assert isinstance(result, AnalysisResult)
    assert len(calls) == 1
    assert result.policy_decision.outcome == PolicyOutcome.VIOLENCE_DETECTED
    assert result.pipeline_result.validation_result == result.validation_result
    assert result.salesforce_preview is not None
    assert result.communication.incident_summary


def test_invalid_input_stops_before_extraction_and_returns_unable():
    calls = []
    result = run_analysis({"incident_id": "CASE", "narrative": "   "}, extractor=lambda value: calls.append(value))
    assert isinstance(result, InputValidationResult)
    assert calls == []
    assert result.policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE


def test_provider_failure_is_unable_without_salesforce_payload():
    result = run_analysis(
        Incident(incident_id="CASE", narrative="Patient struck a nurse."),
        extractor=lambda _: SemanticExtractionResult(SemanticExtractionStatus.REQUEST_FAILURE, failure_message="bounded"),
    )
    assert result.policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE
    assert result.salesforce_preview is None
    assert "could not be classified" in result.communication.incident_summary


def test_normalization_preserves_raw_narrative_and_uses_normalized_input():
    raw = "  Patient intentionally struck the nurse today.  "
    normalized = raw.strip()
    result = run_analysis(
        Incident(incident_id="CASE_001", narrative=raw),
        extractor=extraction_for(candidate_for(normalized)),
    )
    assert result.incident.narrative == raw
    assert result.normalized_incident.normalized_narrative == normalized
