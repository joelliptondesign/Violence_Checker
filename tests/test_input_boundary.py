import pytest

from src.app_logic import AnalysisResult, run_analysis
from src.contracts import InputFailureCode, InputValidationResult, NormalizationOperation
from src.fixtures import SYNTHETIC_INCIDENTS
from src.input_validation import MAX_NARRATIVE_CHARACTERS, validate_incident
from src.models import Incident
from src.narrative_normalizer import normalize_incident
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from tests.successor_helpers import envelope


@pytest.mark.parametrize("candidate,code", [
    (None, InputFailureCode.INVALID_ENVELOPE_TYPE),
    ({}, InputFailureCode.MISSING_INCIDENT_ID),
    ({"incident_id": "X"}, InputFailureCode.MISSING_NARRATIVE),
    ({"incident_id": 1, "narrative": "text"}, InputFailureCode.INVALID_INCIDENT_ID_TYPE),
    ({"incident_id": " ", "narrative": "text"}, InputFailureCode.EMPTY_INCIDENT_ID),
    ({"incident_id": "X", "narrative": 1}, InputFailureCode.INVALID_NARRATIVE_TYPE),
    ({"incident_id": "X", "narrative": ""}, InputFailureCode.EMPTY_NARRATIVE),
    ({"incident_id": "X", "narrative": "   "}, InputFailureCode.WHITESPACE_ONLY_NARRATIVE),
    ({"incident_id": "X", "narrative": "\ufeff"}, InputFailureCode.NO_SUBSTANTIVE_CONTENT),
    ({"incident_id": "X", "narrative": "a\x00b"}, InputFailureCode.NULL_CHARACTER),
    ({"incident_id": "X", "narrative": "a\ud800b"}, InputFailureCode.SURROGATE_CODE_POINT),
    ({"incident_id": "X", "narrative": "x" * (MAX_NARRATIVE_CHARACTERS + 1)}, InputFailureCode.NARRATIVE_TOO_LONG),
    ({"incident_id": "X", "narrative": "text", "extra": True}, InputFailureCode.UNSUPPORTED_FIELD),
])
def test_invalid_incidents_fail_with_bounded_codes(candidate, code):
    assert validate_incident(candidate).failure_code == code


def test_normalization_preserves_raw_and_applies_only_formatting():
    result = normalize_incident(Incident(incident_id="X", narrative="\ufeff  a\u00a0 b\r\n"))
    assert result.original_narrative == "\ufeff  a\u00a0 b\r\n"
    assert result.normalized_narrative == "a b"
    assert set(result.normalization_operations).issubset(set(NormalizationOperation))


def test_all_fixture_narratives_retain_bytes_at_input_boundary():
    for item in SYNTHETIC_INCIDENTS:
        incident = item["incident"]
        assert validate_incident(incident).incident.narrative == incident.narrative


def test_invalid_input_cannot_reach_successor_extraction():
    calls = []
    result = run_analysis({"incident_id": "X", "narrative": " "}, extractor=lambda value: calls.append(value))
    assert isinstance(result, InputValidationResult)
    assert not calls


def test_valid_input_binds_normalized_narrative_and_incident_id_to_envelope():
    raw = "  Patient struck the nurse.  "
    def executor(incident):
        return SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, envelope(narrative=incident.narrative, incident_id=incident.incident_id))
    result = run_analysis(Incident(incident_id="CASE_001", narrative=raw), extractor=executor)
    assert isinstance(result, AnalysisResult)
    assert result.validation_result.validated_envelope.envelope.incident_id == "CASE_001"
    assert result.validation_result.validated_envelope.envelope.evidence_excerpts[0].text == "Patient struck the nurse."
