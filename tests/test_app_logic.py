from src.app_logic import AnalysisResult, run_analysis
from src.contracts import InputValidationResult, PolicyOutcome
from src.models import Incident
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from tests.successor_helpers import envelope


def executor_for(incident):
    return SemanticExtractionResult(
        SemanticExtractionStatus.SUCCESS,
        envelope(narrative=incident.narrative, incident_id=incident.incident_id),
    )


def test_run_analysis_uses_one_successor_extraction_and_aggregate():
    calls = []
    def executor(incident):
        calls.append(incident)
        return executor_for(incident)
    result = run_analysis(Incident(incident_id="CASE_001", narrative="Patient struck the nurse."), extractor=executor)
    assert isinstance(result, AnalysisResult)
    assert len(calls) == 1
    assert result.validation_result.validated_envelope is not None
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_DETECTED
    assert result.salesforce_preview is not None
    assert result.communication is not None


def test_invalid_input_stops_before_extraction():
    calls = []
    result = run_analysis({"incident_id": "CASE", "narrative": "   "}, extractor=lambda value: calls.append(value))
    assert isinstance(result, InputValidationResult)
    assert not calls
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED


def test_normalization_is_formatting_only_and_preserves_raw_narrative():
    raw = "  Patient\u00a0struck the nurse.  "
    result = run_analysis(Incident(incident_id="CASE_001", narrative=raw), extractor=executor_for)
    assert result.incident.narrative == raw
    assert result.normalized_incident.original_narrative == raw
    assert result.normalized_incident.normalized_narrative == "Patient struck the nurse."
