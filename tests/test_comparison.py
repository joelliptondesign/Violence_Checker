from src.app_logic import run_analysis
from src.contracts import EntityKind, TemporalScope
from src.models import Incident
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from src.presentation import comparison_presentation
from tests.successor_helpers import envelope


def run(value, narrative):
    return run_analysis(
        Incident(incident_id=value.incident_id, narrative=narrative),
        extractor=lambda incident: SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, value),
    )


def test_comparison_uses_policy_outcome_not_global_semantic_boolean():
    narrative = "Patient hit the nurse."
    result = run(envelope(narrative=narrative), narrative)
    assert result.comparison.classification_alignment == "aligned_positive"


def test_historical_and_object_directed_context_is_not_promoted():
    narrative = "Patient struck the wall years ago."
    value = envelope(narrative=narrative, temporal_scope=TemporalScope.HISTORICAL, target_entity_kind=EntityKind.OBJECT)
    result = run(value, narrative)
    assert result.policy_decision.outcome.value == "WRITE_NOT_DETECTED"
    assert any("historical" in item.lower() for item in result.comparison.semantic_enrichment_observations)
    assert any("object-directed" in item.lower() for item in result.comparison.semantic_enrichment_observations)


def test_comparison_makes_no_additional_semantic_request():
    calls = []
    narrative = "Patient struck the nurse."
    def executor(incident):
        calls.append(incident)
        return SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, envelope(narrative=narrative))
    run_analysis(Incident(incident_id="CASE_001", narrative=narrative), extractor=executor)
    assert len(calls) == 1


def test_every_comparison_classification_has_plain_presentation_without_changing_logic():
    alignments = {
        "aligned_positive",
        "aligned_negative",
        "regex_positive_semantic_negative",
        "regex_negative_semantic_positive",
        "semantic_failure",
    }
    for alignment in alignments:
        value = comparison_presentation(alignment)
        assert value.keyword_observation
        assert value.ai_observation
        assert value.difference_explanation
        assert value.review_value
