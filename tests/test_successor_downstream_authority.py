from pathlib import Path

import pytest

from src.app_logic import run_analysis
from src.evaluation.corpus import load_corpus, semantic_candidate_for_case
from src.models import Incident
from src.presentation import policy_outcome_label, semantic_summary, validated_evidence_excerpts
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


CASES = {case.case_id: case for case in load_corpus().cases}


def analyze(case_id):
    case = CASES[case_id]
    calls = []
    def extractor(incident):
        calls.append((incident.incident_id, incident.narrative))
        return SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, semantic_candidate_for_case(case))
    result = run_analysis(Incident(incident_id=case.case_id, narrative=case.narrative), extractor=extractor)
    assert calls == [(case.case_id, case.narrative)]
    return result


@pytest.mark.parametrize(
    "case_id,observation",
    [
        ("TN_007", "historical conduct"),
        ("TN_005", "object-directed conduct"),
        ("TN_004", "self-directed conduct"),
        ("TN_008", "supported corrections"),
        ("TN_012", "contradictory accounts"),
        ("TN_014", "unresolved operational facts"),
    ],
)
def test_downstream_comparison_preserves_true_north_context_without_reclassification(case_id, observation):
    result = analyze(case_id)
    assert any(observation in item.lower() for item in result.comparison.semantic_enrichment_observations)
    assert result.policy_decision.outcome == CASES[case_id].ground_truth.deterministic_outcome
    assert result.validation_result.processing_status == CASES[case_id].ground_truth.processing_status
    assert result.validation_result.completeness_status == CASES[case_id].ground_truth.completeness_status


@pytest.mark.parametrize("case_id", ["TN_001", "TN_007", "TN_012", "TN_014", "TN_016"])
def test_presentation_and_preview_copy_validated_operational_authority(case_id):
    result = analyze(case_id)
    decision = result.policy_decision
    assert policy_outcome_label(decision) == decision.outcome.value
    assert semantic_summary(result.validation_result, decision)
    assert result.salesforce_preview is not None
    assert result.salesforce_preview["Illustrative_Deterministic_Outcome__c"] == decision.outcome.value
    assert result.salesforce_preview["Illustrative_Incident_Direction__c"] == result.validation_result.derived_semantics.incident_direction.value
    assert result.salesforce_preview["Illustrative_Evidence__c"] == list(validated_evidence_excerpts(result.validation_result))
    assert not any("proposition" in field.lower() for field in result.salesforce_preview)


@pytest.mark.parametrize("module", ["src/comparison.py", "src/presentation.py", "src/salesforce_preview.py"])
def test_downstream_modules_have_no_provider_request_or_external_connection(module):
    source = Path(module).read_text(encoding="utf-8").lower()
    assert not any(term in source for term in ("responses.parse", "openai(", "requests.", "simple_salesforce"))
