from src.fixtures import SYNTHETIC_INCIDENTS
from src.regex_baseline import detect_violence_terms


def narrative(case_id):
    for item in SYNTHETIC_INCIDENTS:
        incident = item["incident"]
        if incident.incident_id == case_id:
            return incident.narrative
    raise AssertionError(f"missing fixture {case_id}")


def test_regex_output_is_deterministic():
    text = narrative("CASE_001")

    assert detect_violence_terms(text) == detect_violence_terms(text)


def test_direct_assault_terms_detected():
    result = detect_violence_terms(narrative("CASE_001"))

    assert result["detected"] is True
    assert "hit" in result["matched_terms"]


def test_threat_language_detected():
    result = detect_violence_terms(narrative("CASE_002"))

    assert result["detected"] is True
    assert "gonna punch" in result["matched_terms"]


def test_attempted_strike_detected():
    result = detect_violence_terms(narrative("CASE_008"))

    assert result["detected"] is True
    assert "swing" in result["matched_terms"]


def test_historical_assault_term_still_triggers_lexically():
    result = detect_violence_terms(narrative("CASE_003"))

    assert result["detected"] is True
    assert "assault" in result["matched_terms"]


def test_negated_assault_term_still_triggers_lexically():
    result = detect_violence_terms(narrative("CASE_002"))

    assert result["detected"] is True
    assert "hit" in result["matched_terms"]


def test_corrected_non_contact_report_still_triggers_lexically():
    result = detect_violence_terms(narrative("CASE_007"))

    assert result["detected"] is True
    assert "kick" in result["matched_terms"]


def test_accidental_contact_may_trigger_based_on_lexical_content():
    result = detect_violence_terms(narrative("CASE_004"))

    assert result["detected"] is True
    assert "grab" in result["matched_terms"]
