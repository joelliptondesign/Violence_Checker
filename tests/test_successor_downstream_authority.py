from pathlib import Path

import pytest

from src.app_logic import run_analysis
from src.contracts import PolicyOutcome
from src.evaluation.corpus import load_corpus
from src.models import Incident
from src.presentation import policy_outcome_label, semantic_summary
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


CASES = {case.case_id: case for case in load_corpus().cases}


def analyze(case_id):
    case = CASES[case_id]
    calls = []

    def extractor(incident):
        calls.append((incident.incident_id, incident.narrative))
        return SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            case.ground_truth.semantic_envelope,
        )

    result = run_analysis(
        Incident(incident_id=case.case_id, narrative=case.narrative),
        extractor=extractor,
    )
    assert calls == [(case.case_id, case.narrative)]
    return result


@pytest.mark.parametrize(
    "case_id,observation",
    [
        ("EVAL_017", "historical conduct"),
        ("EVAL_033", "object-directed conduct"),
        ("EVAL_037", "self-directed conduct"),
        ("EVAL_020", "correction and supersession"),
        ("EVAL_029", "competing assertions"),
        ("EVAL_041", "bounded uncertainty"),
    ],
)
def test_comparison_preserves_each_successor_context_without_promotion(case_id, observation):
    result = analyze(case_id)
    assert any(
        observation in item.lower()
        for item in result.comparison.semantic_enrichment_observations
    )
    assert result.policy_decision == CASES[case_id].ground_truth.policy_decision


@pytest.mark.parametrize("case_id", ["EVAL_001", "EVAL_009", "EVAL_017", "EVAL_029", "EVAL_033", "EVAL_037", "EVAL_041"])
def test_presentation_and_preview_copy_authoritative_successor_results(case_id):
    result = analyze(case_id)
    decision = result.policy_decision
    assert policy_outcome_label(decision)
    assert semantic_summary(result.validation_result.validated_envelope, decision)
    if decision.outcome == PolicyOutcome.WRITE_FAILED:
        assert result.salesforce_preview is None
    else:
        assert result.salesforce_preview["Illustrative_Write_Disposition__c"] == decision.outcome.value
        assert result.salesforce_preview["Illustrative_Evidence__c"] == [
            item.text
            for item in result.validation_result.validated_envelope.envelope.evidence_excerpts
        ]


@pytest.mark.parametrize("module", ["src/comparison.py", "src/presentation.py", "src/salesforce_preview.py"])
def test_downstream_modules_have_no_provider_request_or_external_connection(module):
    source = Path(module).read_text(encoding="utf-8").lower()
    assert "responses.parse" not in source
    assert "openai(" not in source
    assert "requests." not in source
    assert "simple_salesforce" not in source
