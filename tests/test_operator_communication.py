from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

import src.app_logic as app_logic
from src.app_logic import AnalysisResult, run_analysis
from src.contracts import (
    OperatorCommunication,
    OperatorCommunicationInput,
    PipelineFailureProvenance,
    PolicyOutcome,
)
from src.evaluation.corpus import load_corpus
from src.models import Incident
from src.operator_communication import (
    build_deterministic_communication,
    construct_communication_input,
)
from src.policy import failed_policy_decision
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


CASES = {case.case_id: case for case in load_corpus().cases}


def analyze(case_id: str, *, communicator=None) -> AnalysisResult:
    case = CASES[case_id]
    calls = []

    def extractor(incident):
        calls.append(incident)
        return SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            case.ground_truth.semantic_envelope,
        )

    result = run_analysis(
        Incident(incident_id=case.case_id, narrative=case.narrative),
        extractor=extractor,
        communicator=communicator,
    )
    assert isinstance(result, AnalysisResult)
    assert len(calls) == 1
    return result


def communication_input(result: AnalysisResult) -> OperatorCommunicationInput:
    return construct_communication_input(
        result.validation_result,
        result.policy_decision,
        result.regex_result,
        result.comparison,
        salesforce_preview_eligible=result.salesforce_preview is not None,
    )


def test_contracts_are_bounded_and_expose_only_authorized_fields():
    result = analyze("EVAL_001")
    facts = communication_input(result)
    payload = build_deterministic_communication(facts)

    assert set(OperatorCommunication.model_fields) == {
        "incident_summary",
        "key_findings",
        "why_this_result",
    }
    assert 0 < len(payload.incident_summary) <= 500
    assert 0 < len(payload.why_this_result) <= 500
    assert 1 <= len(payload.key_findings) <= 8
    prohibited = {
        "incident",
        "narrative",
        "original_narrative",
        "normalized_narrative",
        "provider_response",
        "recommendation",
        "outcome_override",
        "classification_override",
    }
    assert prohibited.isdisjoint(OperatorCommunicationInput.model_fields)
    assert prohibited.isdisjoint(OperatorCommunication.model_fields)
    assert "incident" not in type(facts.comparison).model_fields


def test_contracts_reject_extra_empty_and_mutated_authority():
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="", key_findings=("Patient identified",), why_this_result="reason")
    with pytest.raises(ValidationError):
        OperatorCommunication(
            incident_summary="summary",
            key_findings=("Patient identified",),
            why_this_result="reason",
            recommendation="act now",
        )
    facts = communication_input(analyze("EVAL_001"))
    with pytest.raises(ValidationError):
        facts.policy_outcome = PolicyOutcome.WRITE_NOT_DETECTED


def test_incomplete_construction_fails_without_repairing_semantics():
    result = analyze("EVAL_001")
    with pytest.raises(ValueError):
        construct_communication_input(
            result.validation_result.model_copy(update={"validated_envelope": None}),
            result.policy_decision,
            result.regex_result,
            result.comparison,
            salesforce_preview_eligible=True,
        )
    with pytest.raises(ValueError):
        construct_communication_input(
            result.validation_result,
            failed_policy_decision(PipelineFailureProvenance.DOMAIN_VALIDATION),
            result.regex_result,
            result.comparison,
            salesforce_preview_eligible=False,
        )


def test_construction_does_not_mutate_any_authoritative_input_or_preview():
    result = analyze("EVAL_029")
    validation_before = result.validation_result.model_copy(deep=True)
    validated_before = result.validation_result.validated_envelope.model_copy(deep=True)
    policy_before = result.policy_decision.model_copy(deep=True)
    comparison_before = deepcopy(result.comparison)
    preview_before = deepcopy(result.salesforce_preview)

    facts = communication_input(result)
    build_deterministic_communication(facts)

    assert result.validation_result == validation_before
    assert result.validation_result.validated_envelope == validated_before
    assert result.policy_decision == policy_before
    assert result.comparison == comparison_before
    assert result.salesforce_preview == preview_before


@pytest.mark.parametrize(
    "case_id,expected",
    [
        ("EVAL_001", "intentionally made physical contact"),
        ("EVAL_005", "attempted physical contact"),
        ("EVAL_009", "made a current threat"),
        ("EVAL_013", "accidental contact"),
        ("EVAL_017", "historical context"),
        ("EVAL_025", "correction or denial"),
        ("EVAL_029", "conflicting information"),
        ("EVAL_033", "directing conduct at the wall"),
        ("EVAL_037", "self-directed conduct"),
        ("EVAL_041", "material detail remains unclear"),
    ],
)
def test_deterministic_fallback_distinguishes_repository_supported_states(case_id, expected):
    payload = analyze(case_id).communication
    assert isinstance(payload, OperatorCommunication)
    assert expected in payload.incident_summary


def test_no_current_interpersonal_violence_has_bounded_default():
    result = analyze("EVAL_021")
    assert result.communication is not None
    assert "does not establish current interpersonal violence" in result.communication.incident_summary


def test_key_findings_are_ordered_concise_and_operational():
    payload = analyze("EVAL_001").communication
    assert payload is not None
    assert payload.key_findings == (
        "Patient identified",
        "Nurse identified",
        "Intentional assault identified",
        "Physical contact confirmed",
    )
    assert all(2 <= len(finding.split()) <= 5 for finding in payload.key_findings)


def test_every_fallback_uses_human_language_without_implementation_terms():
    forbidden = {
        "proposition",
        "policy",
        "schema",
        "validation",
        "reason code",
        "repository",
        "metadata",
        "entity id",
    }
    for case_id in CASES:
        payload = analyze(case_id).communication
        assert payload is not None
        rendered = " ".join((payload.incident_summary, *payload.key_findings, payload.why_this_result)).casefold()
        assert forbidden.isdisjoint({term for term in forbidden if term in rendered})
        assert 1 <= len(payload.key_findings) <= 8
        assert all(2 <= len(item.split()) <= 5 for item in payload.key_findings)


def test_contract_rejects_invalid_finding_count_length_and_implementation_language():
    with pytest.raises(ValidationError):
        OperatorCommunication(incident_summary="Summary", key_findings=(), why_this_result="Reason")
    with pytest.raises(ValidationError):
        OperatorCommunication(
            incident_summary="Summary",
            key_findings=("This finding contains far too many words for review",),
            why_this_result="Reason",
        )
    with pytest.raises(ValidationError):
        OperatorCommunication(
            incident_summary="Schema validated the result.",
            key_findings=("Patient identified",),
            why_this_result="Reason",
        )


def test_failed_analysis_carries_failure_communication_without_preview():
    calls = []

    def extractor(incident):
        calls.append(incident)
        return SemanticExtractionResult(
            SemanticExtractionStatus.REQUEST_FAILURE,
            failure_message="bounded failure",
        )

    result = run_analysis(Incident(incident_id="CASE_FAIL", narrative="Patient struck a nurse."), extractor=extractor)
    assert isinstance(result, AnalysisResult)
    assert len(calls) == 1
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED
    assert result.salesforce_preview is None
    assert result.communication is not None
    assert "could not be assessed" in result.communication.incident_summary


def test_communication_failure_leaves_authoritative_result_unchanged():
    expected = analyze("EVAL_001")

    def fail_communication(*_args, **_kwargs):
        raise ValueError("presentation unavailable")

    actual = analyze("EVAL_001", communicator=fail_communication)
    assert actual.communication == expected.communication
    assert actual.validation_result == expected.validation_result
    assert actual.policy_decision == expected.policy_decision
    assert actual.comparison == expected.comparison
    assert actual.salesforce_preview == expected.salesforce_preview


def test_invalid_input_still_issues_zero_requests_and_has_no_communication():
    calls = []
    result = run_analysis({"incident_id": "CASE", "narrative": "   "}, extractor=lambda item: calls.append(item))
    assert calls == []
    assert not hasattr(result, "communication")


def test_communication_module_has_no_provider_semantic_or_network_imports():
    source = Path("src/operator_communication.py").read_text(encoding="utf-8").lower()
    prohibited = (
        "semantic_extractor",
        "openai",
        "requests",
        "urllib",
        "httpx",
        "socket",
        "responses.parse",
    )
    assert not any(term in source for term in prohibited)
    assert "evaluate_policy" not in source
    assert "build_salesforce_preview" not in source
