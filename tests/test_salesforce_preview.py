import pytest

from src.contracts import PipelineFailureProvenance
from src.policy import evaluate_policy, failed_policy_decision
from src.salesforce_preview import build_salesforce_preview, preview_field_names
from src.semantic_validation import validate_semantic_candidate
from tests.successor_helpers import envelope


def validated():
    return validate_semantic_candidate(envelope(), incident_id="CASE_001", normalized_narrative="Patient struck the nurse.").validated_envelope


def test_preview_is_deterministic_successor_representation():
    value = validated()
    decision = evaluate_policy(validated=value)
    first = build_salesforce_preview(value, decision)
    assert first == build_salesforce_preview(value, decision)
    assert list(first) == preview_field_names()
    assert first["Illustrative_Semantic_Schema__c"] == "violence-checker.proposition-semantics@1.0.0"


def test_failed_policy_cannot_produce_preview():
    with pytest.raises(ValueError):
        build_salesforce_preview(validated(), failed_policy_decision(PipelineFailureProvenance.DOMAIN_VALIDATION))


def test_preview_has_no_connection_or_policy_inference_fields():
    names = set(preview_field_names())
    assert not any("credential" in name.lower() or "connection" in name.lower() for name in names)
