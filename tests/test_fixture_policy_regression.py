from src.app_logic import run_analysis
from src.contracts import PolicyOutcome
from src.fixtures import SYNTHETIC_INCIDENTS
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
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
        assert first.policy_decision.outcome == second.policy_decision.outcome == PolicyOutcome.WRITE_DETECTED
        assert len(calls) == 2
