from src.contracts import PipelineFailureProvenance, PolicyOutcome
from src.policy import evaluate_policy, failed_policy_decision
from src.presentation import policy_outcome_label, policy_reason_explanations, semantic_summary
from src.semantic_validation import validate_semantic_candidate
from tests.successor_helpers import envelope


def validated():
    result = validate_semantic_candidate(envelope(), incident_id="CASE_001", normalized_narrative="Patient struck the nurse.")
    return result.validated_envelope


def test_presentation_maps_every_policy_outcome_without_inference():
    assert {outcome for outcome in PolicyOutcome} == set(__import__("src.presentation", fromlist=["POLICY_OUTCOME_LABELS"]).POLICY_OUTCOME_LABELS)


def test_successor_summary_uses_typed_derived_counts():
    value = validated()
    decision = evaluate_policy(validated=value)
    assert "1 active current interpersonal proposition" in semantic_summary(value, decision)


def test_failed_summary_and_reason_are_safe():
    decision = failed_policy_decision(PipelineFailureProvenance.PROVIDER_REQUEST)
    assert policy_outcome_label(decision) == "Unable to Determine"
    assert policy_reason_explanations(decision)
    assert "unable" in semantic_summary(None, decision).lower()
