from src.contracts import (
    AssertionStatus,
    Completion,
    Contact,
    PipelineFailureProvenance,
    PolicyOutcome,
    SemanticIntentionality,
    TemporalScope,
    UncertaintyDimension,
)
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
    assert semantic_summary(value, decision) == "The narrative describes completed physical violence involving contact."


def test_failed_summary_and_reason_are_safe():
    decision = failed_policy_decision(PipelineFailureProvenance.PROVIDER_REQUEST)
    assert policy_outcome_label(decision) == "Analysis Failed"
    assert policy_reason_explanations(decision)
    assert "could not" in semantic_summary(None, decision).lower()


def test_stakeholder_language_is_plain_for_every_outcome():
    prohibited = {
        "proposition", "semantic envelope", "bounded uncertainty", "scoped semantic",
        "deterministic policy", "active-set", "schema-admissible", "provider validation",
    }
    detected_value = validated()
    uncertain_result = validate_semantic_candidate(
        envelope(
            completion=Completion.UNDETERMINED,
            contact=Contact.UNDETERMINED,
            uncertainty_dimension=UncertaintyDimension.CONTACT,
        ),
        incident_id="CASE_001",
        normalized_narrative="Patient may have struck the nurse.",
    ).validated_envelope
    values = [
        (detected_value, evaluate_policy(validated=detected_value)),
        (uncertain_result, evaluate_policy(validated=uncertain_result)),
        (None, failed_policy_decision(PipelineFailureProvenance.PROVIDER_REQUEST)),
    ]
    for value, decision in values:
        rendered = " ".join([
            policy_outcome_label(decision),
            semantic_summary(value, decision),
            *policy_reason_explanations(decision),
        ]).lower()
        assert not any(term in rendered for term in prohibited)


def test_accidental_and_historical_summaries_remain_distinct():
    accidental_narrative = "Patient bumped the nurse by accident."
    accidental = validate_semantic_candidate(
        envelope(narrative=accidental_narrative, intentionality=SemanticIntentionality.ACCIDENTAL),
        incident_id="CASE_001",
        normalized_narrative=accidental_narrative,
    ).validated_envelope
    historical_narrative = "Patient struck a nurse years ago."
    historical = validate_semantic_candidate(
        envelope(narrative=historical_narrative, temporal_scope=TemporalScope.HISTORICAL),
        incident_id="CASE_001",
        normalized_narrative=historical_narrative,
    ).validated_envelope
    assert "accidental contact" in semantic_summary(accidental, evaluate_policy(validated=accidental))
    assert "past event" in semantic_summary(historical, evaluate_policy(validated=historical))
