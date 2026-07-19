from pathlib import Path

import pytest

from src.app_logic import run_analysis
from src.contracts import (
    PipelineFailureProvenance,
    PolicyOutcome,
    PolicyReasonCode,
)
from src.models import Incident
from src.policy import POLICY_ID, POLICY_VERSION, evaluate_policy
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from src.semantic_validation import validate_semantic_candidate
from tests.successor_helpers import envelope


FAILURE_REASON = {
    PipelineFailureProvenance.INPUT_VALIDATION: PolicyReasonCode.INPUT_VALIDATION_FAILED,
    PipelineFailureProvenance.PROVIDER_CONFIGURATION: PolicyReasonCode.PROVIDER_CONFIGURATION_FAILED,
    PipelineFailureProvenance.PROVIDER_REQUEST: PolicyReasonCode.PROVIDER_REQUEST_FAILED,
    PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE: PolicyReasonCode.PROVIDER_STRUCTURED_RESPONSE_FAILED,
    PipelineFailureProvenance.PROVIDER_VALIDATION: PolicyReasonCode.PROVIDER_VALIDATION_FAILED,
    PipelineFailureProvenance.SCHEMA_VALIDATION: PolicyReasonCode.SCHEMA_VALIDATION_FAILED,
    PipelineFailureProvenance.DOMAIN_VALIDATION: PolicyReasonCode.DOMAIN_VALIDATION_FAILED,
    PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT: PolicyReasonCode.UNSUPPORTED_POLICY_INPUT,
}


def validated():
    result = validate_semantic_candidate(
        envelope(),
        incident_id="CASE_001",
        normalized_narrative="Patient struck the nurse.",
    )
    assert result.validated_envelope is not None
    return result.validated_envelope


@pytest.mark.parametrize("failure", tuple(PipelineFailureProvenance))
def test_every_typed_pipeline_failure_maps_to_explicit_failed_policy(failure):
    decision = evaluate_policy(failure=failure)
    assert decision.policy_id == POLICY_ID
    assert decision.policy_version == POLICY_VERSION
    assert decision.outcome == PolicyOutcome.WRITE_FAILED
    assert decision.failure_provenance == failure
    assert decision.reason_codes == [FAILURE_REASON[failure]]


def test_explicit_failure_precedes_otherwise_detected_validated_input():
    decision = evaluate_policy(
        validated=validated(),
        failure=PipelineFailureProvenance.PROVIDER_REQUEST,
    )
    assert decision.outcome == PolicyOutcome.WRITE_FAILED
    assert decision.failure_provenance == PipelineFailureProvenance.PROVIDER_REQUEST


@pytest.mark.parametrize(
    "status,provenance",
    [
        (SemanticExtractionStatus.CONFIGURATION_FAILURE, PipelineFailureProvenance.PROVIDER_CONFIGURATION),
        (SemanticExtractionStatus.REQUEST_FAILURE, PipelineFailureProvenance.PROVIDER_REQUEST),
        (SemanticExtractionStatus.STRUCTURED_RESPONSE_FAILURE, PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE),
        (SemanticExtractionStatus.VALIDATION_FAILURE, PipelineFailureProvenance.PROVIDER_VALIDATION),
    ],
)
def test_provider_failures_map_to_failed_policy_and_no_preview(status, provenance):
    calls = []

    def extractor(incident):
        calls.append(incident.incident_id)
        return SemanticExtractionResult(status=status, failure_message="bounded")

    result = run_analysis(Incident(incident_id="CASE_X", narrative="Patient struck a nurse."), extractor=extractor)
    assert calls == ["CASE_X"]
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED
    assert result.policy_decision.failure_provenance == provenance
    assert result.salesforce_preview is None


def test_mismatched_policy_candidate_identity_fails_without_negative_default():
    value = validated()
    candidate = value.policy_candidate.model_copy(update={"schema_version": "9.0.0"})
    decision = evaluate_policy(validated=value.model_copy(update={"policy_candidate": candidate}))
    assert decision.outcome == PolicyOutcome.WRITE_FAILED
    assert decision.reason_codes == [PolicyReasonCode.UNSUPPORTED_POLICY_INPUT]


def test_policy_module_has_no_provider_or_external_side_effect_imports():
    source = Path("src/policy.py").read_text(encoding="utf-8")
    assert "openai" not in source.lower()
    assert "salesforce" not in source.lower()
    assert "requests" not in source.lower()
