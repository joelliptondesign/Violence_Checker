import pytest

from src.app_logic import run_analysis
from src.contracts import CompletenessStatus, PolicyOutcome, ProcessingStatus
from src.models import Incident
from src.policy import evaluate_policy
from src.salesforce_preview import build_salesforce_preview, preview_field_names
from tests.test_app_logic import candidate_for, extraction_for


def validated_result():
    narrative = "Patient intentionally struck the nurse today."
    return run_analysis(Incident(incident_id="CASE_001", narrative=narrative), extractor=extraction_for(candidate_for(narrative)))


def test_preview_is_deterministic_true_north_representation():
    result = validated_result()
    first = build_salesforce_preview(result.validation_result, result.policy_decision)
    assert first == build_salesforce_preview(result.validation_result, result.policy_decision)
    assert list(first) == preview_field_names()
    assert first["Illustrative_Deterministic_Outcome__c"] == "Violence Detected"
    assert first["Illustrative_Qualifying_Conduct__c"] == ["physical_contact"]
    assert first["Illustrative_Incident_Direction__c"] == "interpersonal"
    assert not any("proposition" in name.lower() for name in first)


def test_unable_policy_and_failed_validation_cannot_produce_preview():
    result = validated_result()
    unable = evaluate_policy(
        validated=None, processing_status=ProcessingStatus.PROVIDER_FAILURE,
        completeness_status=CompletenessStatus.INCOMPLETE_ANALYSIS, derived=None,
    )
    assert unable.outcome == PolicyOutcome.UNABLE_TO_DETERMINE
    with pytest.raises(ValueError):
        build_salesforce_preview(result.validation_result, unable)
    with pytest.raises(TypeError):
        build_salesforce_preview(result.validation_result.model_copy(update={"failure_stage": "not_run"}), result.policy_decision)
