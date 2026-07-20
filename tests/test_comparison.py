from src.app_logic import run_analysis
from src.contracts import Conduct, FactDirection, PolicyOutcome, TemporalScope
from src.models import Incident
from src.presentation import comparison_presentation
from tests.test_app_logic import candidate_for, extraction_for


def test_comparison_uses_true_north_policy_outcome():
    narrative = "Patient intentionally hit the nurse today."
    result = run_analysis(Incident(incident_id="CASE_001", narrative=narrative), extractor=extraction_for(candidate_for(narrative)))
    assert result.comparison.true_north_outcome == PolicyOutcome.VIOLENCE_DETECTED
    assert result.comparison.classification_alignment == "aligned_positive"


def test_historical_object_context_is_preserved_without_promotion():
    narrative = "Patient damaged the wall years ago."
    candidate = candidate_for(
        narrative, conduct=Conduct.PROPERTY_VIOLENCE,
        direction=FactDirection.OBJECT_DIRECTED, temporal_scope=TemporalScope.HISTORICAL,
    )
    result = run_analysis(Incident(incident_id="CASE_001", narrative=narrative), extractor=extraction_for(candidate))
    assert result.policy_decision.outcome == PolicyOutcome.NO_VIOLENCE_DETECTED
    rendered = " ".join(result.comparison.semantic_enrichment_observations).lower()
    assert "historical" in rendered and "object-directed" in rendered


def test_all_comparison_states_have_plain_presentations():
    for alignment in (
        "aligned_positive", "aligned_negative", "regex_positive_semantic_negative",
        "regex_negative_semantic_positive", "semantic_uncertain", "semantic_failure",
    ):
        value = comparison_presentation(alignment)
        assert all(value.__dict__.values())
