from itertools import product

from src.contracts import (
    AssertionStatus,
    EntityKind,
    PipelineFailureProvenance,
    PolicyOutcome,
    PolicyReasonCode,
    SemanticIntentionality,
    TargetKind,
    TemporalScope,
)
from src.policy import evaluate_policy
from src.semantic_validation import validate_semantic_candidate
from tests.successor_helpers import envelope


def decision(value, narrative="Patient struck the nurse."):
    validated = validate_semantic_candidate(value, incident_id=value.incident_id, normalized_narrative=narrative)
    assert validated.validated_envelope is not None
    return evaluate_policy(validated=validated.validated_envelope)


def test_affirmed_current_interpersonal_violence_is_detected():
    assert decision(envelope()).outcome == PolicyOutcome.WRITE_DETECTED


def test_historical_object_self_accidental_and_negated_states_are_not_detected():
    historical = envelope(temporal_scope=TemporalScope.HISTORICAL)
    object_directed = envelope(target_entity_kind=EntityKind.OBJECT)
    self_directed = envelope(target_kind=TargetKind.SELF)
    accidental = envelope(intentionality=SemanticIntentionality.ACCIDENTAL)
    negated = envelope(assertion_status=AssertionStatus.NEGATED)
    for value in (historical, object_directed, self_directed, accidental, negated):
        assert decision(value).outcome == PolicyOutcome.WRITE_NOT_DETECTED


def test_policy_failure_is_typed_and_total_for_missing_input():
    result = evaluate_policy(failure=PipelineFailureProvenance.SCHEMA_VALIDATION)
    assert result.outcome == PolicyOutcome.WRITE_FAILED
    assert result.failure_provenance == PipelineFailureProvenance.SCHEMA_VALIDATION
    unsupported = evaluate_policy()
    assert unsupported.outcome == PolicyOutcome.WRITE_FAILED
    assert unsupported.reason_codes == [PolicyReasonCode.UNSUPPORTED_POLICY_INPUT]


def test_provider_confidence_is_not_policy_input():
    low = envelope().model_copy(update={"extraction_metadata": envelope().extraction_metadata.model_copy(update={"provider_confidence": 0.01})})
    high = envelope().model_copy(update={"extraction_metadata": envelope().extraction_metadata.model_copy(update={"provider_confidence": 0.99})})
    assert decision(low).outcome == decision(high).outcome == PolicyOutcome.WRITE_DETECTED


def test_every_supported_policy_candidate_partition_has_a_nonfailure_outcome():
    base_result = validate_semantic_candidate(envelope(), incident_id="CASE_001", normalized_narrative="Patient struck the nurse.")
    base = base_result.validated_envelope
    list_fields = [
        "active_current_interpersonal_affirmed",
        "active_current_interpersonal_uncertain",
        "active_current_interpersonal_negated",
        "active_current_interpersonal_accidental",
        "active_current_interpersonal_violence",
        "active_potential_interpersonal_uncertain",
        "active_conflict_relationships",
        "active_uncertainties",
        "active_current_interpersonal_uncertainties",
    ]
    for flags in product((False, True), repeat=len(list_fields)):
        values = {field: (["SUBJECT-1"] if enabled else []) for field, enabled in zip(list_fields, flags)}
        candidate = base.policy_candidate.model_copy(update=values)
        validated = base.model_copy(update={"policy_candidate": candidate})
        assert evaluate_policy(validated=validated).outcome != PolicyOutcome.WRITE_FAILED
