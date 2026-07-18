from unittest.mock import Mock

import pytest

from src.app_logic import AnalysisResult, run_analysis
from src.contracts import (
    InputFailureCode,
    InputValidationResult,
    InputValidationStatus,
    NormalizationOperation,
    SemanticFacts,
    PolicyOutcome,
)
from src.fixtures import SYNTHETIC_INCIDENTS
from src.input_validation import MAX_NARRATIVE_CHARACTERS, validate_incident
from src.models import Incident, Intentionality, ViolenceEventType
from src.narrative_normalizer import normalize_incident
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


def semantic_success() -> SemanticExtractionResult:
    return SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        semantic_candidate=SemanticFacts(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            actor=None,
            target=None,
            contact_occurred=False,
            injury_mentioned=False,
            current_event=True,
            intentionality=Intentionality.UNCLEAR,
            negated=True,
            correction_present=False,
            conflicting_information=False,
            evidence_text=["did not hit anyone"],
            confidence=0.9,
            uncertainty_notes=[],
        ),
    )


@pytest.mark.parametrize(
    ("candidate", "code"),
    [
        (object(), InputFailureCode.INVALID_ENVELOPE_TYPE),
        ({"incident_id": "CASE_X", "narrative": "text", "extra": True}, InputFailureCode.UNSUPPORTED_FIELD),
        ({"narrative": "text"}, InputFailureCode.MISSING_INCIDENT_ID),
        ({"incident_id": 1, "narrative": "text"}, InputFailureCode.INVALID_INCIDENT_ID_TYPE),
        ({"incident_id": "", "narrative": "text"}, InputFailureCode.EMPTY_INCIDENT_ID),
        ({"incident_id": "   ", "narrative": "text"}, InputFailureCode.EMPTY_INCIDENT_ID),
        ({"incident_id": "CASE_X"}, InputFailureCode.MISSING_NARRATIVE),
        ({"incident_id": "CASE_X", "narrative": None}, InputFailureCode.INVALID_NARRATIVE_TYPE),
        ({"incident_id": "CASE_X", "narrative": ""}, InputFailureCode.EMPTY_NARRATIVE),
        ({"incident_id": "CASE_X", "narrative": " \t\n"}, InputFailureCode.WHITESPACE_ONLY_NARRATIVE),
        ({"incident_id": "CASE_X", "narrative": "\ufeff \n"}, InputFailureCode.NO_SUBSTANTIVE_CONTENT),
        ({"incident_id": "CASE_X", "narrative": "text\x00"}, InputFailureCode.NULL_CHARACTER),
        ({"incident_id": "CASE_X", "narrative": "text\ud800"}, InputFailureCode.SURROGATE_CODE_POINT),
        (
            {"incident_id": "CASE_X", "narrative": "x" * (MAX_NARRATIVE_CHARACTERS + 1)},
            InputFailureCode.NARRATIVE_TOO_LONG,
        ),
    ],
)
def test_invalid_incident_candidates_return_typed_failures(candidate: object, code: InputFailureCode) -> None:
    result = validate_incident(candidate)

    assert isinstance(result, InputValidationResult)
    assert result.status == InputValidationStatus.FAILURE
    assert result.incident is None
    assert result.failure_code == code
    assert result.failure_message


def test_valid_fixture_short_unicode_and_maximum_size_inputs_pass() -> None:
    fixture = SYNTHETIC_INCIDENTS[0]["incident"]
    candidates = [
        fixture,
        {"incident_id": "SHORT", "narrative": "No."},
        {"incident_id": "UNICODE", "narrative": "Patient said cafe\u0301."},
        {"incident_id": "MAX", "narrative": "x" * MAX_NARRATIVE_CHARACTERS},
    ]

    results = [validate_incident(candidate) for candidate in candidates]

    assert all(result.status == InputValidationStatus.SUCCESS for result in results)
    assert results[0].incident == fixture
    assert results[1].incident.narrative == "No."
    assert results[2].incident.narrative == "Patient said cafe\u0301."
    assert len(results[3].incident.narrative) == MAX_NARRATIVE_CHARACTERS


def test_invalid_input_cannot_reach_regex_or_semantic_extraction(monkeypatch) -> None:
    regex = Mock()
    extractor = Mock()
    monkeypatch.setattr("src.app_logic.detect_violence_terms", regex)

    result = run_analysis(
        {"incident_id": "CASE_X", "narrative": "bad\x00input"},
        extractor=extractor,
    )

    assert isinstance(result, InputValidationResult)
    regex.assert_not_called()
    extractor.assert_not_called()


def test_noop_normalization_preserves_raw_narrative() -> None:
    incident = Incident(incident_id="CASE_X", narrative="Do not hit anyone.")

    result = normalize_incident(incident)

    assert result.original_narrative == incident.narrative
    assert result.normalized_narrative == incident.narrative
    assert result.normalization_applied is False
    assert result.normalization_operations == []


def test_normalization_applies_only_ordered_formatting_operations() -> None:
    raw = "\ufeff  Cafe\u0301\u00a0said:\t\"Do  NOT hit #42!\"\r\n\r\n\r\n  damn.  "
    incident = Incident(incident_id="CASE_X", narrative=raw)

    result = normalize_incident(incident)

    assert result.original_narrative == raw
    assert result.normalized_narrative == 'Caf\u00e9 said: "Do NOT hit #42!"\n\n damn.'
    assert result.normalization_operations == [
        NormalizationOperation.REMOVE_LEADING_BOM,
        NormalizationOperation.UNICODE_NFC,
        NormalizationOperation.LINE_ENDINGS_LF,
        NormalizationOperation.NON_BREAKING_SPACES,
        NormalizationOperation.HORIZONTAL_WHITESPACE,
        NormalizationOperation.EXCESSIVE_BLANK_LINES,
        NormalizationOperation.TRIM_BOUNDARY_WHITESPACE,
    ]
    assert "NOT" in result.normalized_narrative
    assert '"Do NOT hit #42!"' in result.normalized_narrative
    assert "damn" in result.normalized_narrative


@pytest.mark.parametrize(
    ("raw", "expected", "operation"),
    [
        ("a\r\nb\rc", "a\nb\nc", NormalizationOperation.LINE_ENDINGS_LF),
        ("a\u00a0b", "a b", NormalizationOperation.NON_BREAKING_SPACES),
        ("\ufefftext", "text", NormalizationOperation.REMOVE_LEADING_BOM),
        ("a\t  b", "a b", NormalizationOperation.HORIZONTAL_WHITESPACE),
        ("a\n\n\n\nb", "a\n\nb", NormalizationOperation.EXCESSIVE_BLANK_LINES),
        (" \ntext\t ", "text", NormalizationOperation.TRIM_BOUNDARY_WHITESPACE),
    ],
)
def test_each_formatting_normalization_is_deterministic(raw: str, expected: str, operation: NormalizationOperation) -> None:
    incident = Incident(incident_id="CASE_X", narrative=raw)

    first = normalize_incident(incident)
    second = normalize_incident(incident)

    assert first == second
    assert first.normalized_narrative == expected
    assert operation in first.normalization_operations


def test_fixture_narratives_are_normalization_noops() -> None:
    normalized = [normalize_incident(item["incident"]) for item in SYNTHETIC_INCIDENTS]

    assert all(item.normalized_narrative == item.original_narrative for item in normalized)
    assert all(item.normalization_operations == [] for item in normalized)


def test_valid_analysis_uses_normalized_inference_copy_and_retains_raw_incident() -> None:
    raw = "  pt\u00a0did  not hit anyone.  "
    incident = Incident(incident_id="CASE_X", narrative=raw)
    calls = []

    def extractor(inference_incident: Incident) -> SemanticExtractionResult:
        calls.append(inference_incident)
        return semantic_success()

    result = run_analysis(incident, extractor=extractor)

    assert isinstance(result, AnalysisResult)
    assert len(calls) == 1
    assert calls[0].incident_id == incident.incident_id
    assert calls[0].narrative == "pt did not hit anyone."
    assert result.incident.narrative == raw
    assert result.normalized_incident.original_narrative == raw
    assert result.normalized_incident.normalized_narrative == calls[0].narrative
    assert result.semantic_result.status == SemanticExtractionStatus.SUCCESS
    assert result.salesforce_preview is not None


def test_semantic_failure_behavior_and_preview_gating_remain_typed() -> None:
    failure = SemanticExtractionResult(
        status=SemanticExtractionStatus.REQUEST_FAILURE,
        failure_message="RuntimeError",
    )

    result = run_analysis(Incident(incident_id="CASE_X", narrative="text"), extractor=lambda _incident: failure)

    assert isinstance(result, AnalysisResult)
    assert result.semantic_result is failure
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED
    assert result.salesforce_preview is None
    assert result.comparison.classification_alignment == "semantic_failure"


def test_compatibility_failure_cannot_produce_default_finding_or_preview() -> None:
    inconsistent_facts = SemanticFacts(
        violence_present=True,
        event_type=ViolenceEventType.NONE,
        actor="patient",
        target="nurse",
        contact_occurred=False,
        injury_mentioned=False,
        current_event=True,
        intentionality=Intentionality.INTENTIONAL,
        negated=False,
        correction_present=False,
        conflicting_information=False,
        evidence_text=["patient threatened the nurse"],
        confidence=0.7,
        uncertainty_notes=[],
    )
    semantic_result = SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        semantic_candidate=inconsistent_facts,
    )

    result = run_analysis(
        Incident(incident_id="CASE_X", narrative="patient threatened the nurse"),
        extractor=lambda _incident: semantic_result,
    )

    assert isinstance(result, AnalysisResult)
    assert result.validation_result.failure_stage.value == "domain"
    assert result.validation_result.validated_facts is None
    assert result.compatibility_result is None
    assert result.salesforce_preview is None
    assert result.comparison.classification_alignment == "semantic_failure"
