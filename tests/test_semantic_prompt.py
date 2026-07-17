from src.semantic_prompt import SEMANTIC_EXTRACTION_PROMPT
from pathlib import Path


def test_prompt_defines_current_event_timing_generally():
    assert "current_event" in SEMANTIC_EXTRACTION_PROMPT
    assert "during the incident being\n  reported" in SEMANTIC_EXTRACTION_PROMPT
    assert "Historical disclosures unrelated" in SEMANTIC_EXTRACTION_PROMPT


def test_prompt_addresses_corrections_and_object_directed_contact():
    assert "later explicit and\n  credible correction" in SEMANTIC_EXTRACTION_PROMPT
    assert "do not preserve the earlier person-directed violence claim" in SEMANTIC_EXTRACTION_PROMPT
    assert "Kicking, striking, or contacting an object" in SEMANTIC_EXTRACTION_PROMPT
    assert "person-directed attempt or contact" in SEMANTIC_EXTRACTION_PROMPT
    assert "Object-directed aggression may be event_type=unclear" in SEMANTIC_EXTRACTION_PROMPT


def test_prompt_addresses_accidental_contact_and_threats():
    assert "Accidental contact\n  may have contact_occurred=true while violence_present=false" in SEMANTIC_EXTRACTION_PROMPT
    assert "use event_type=unclear rather\n  than event_type=none" in SEMANTIC_EXTRACTION_PROMPT
    assert "Threatening movement or language" in SEMANTIC_EXTRACTION_PROMPT
    assert "without evidence of a person-directed physical attempt" in SEMANTIC_EXTRACTION_PROMPT


def test_prompt_contains_no_fixture_identifiers_or_case_specific_labels():
    forbidden_terms = [
        "CASE_001",
        "CASE_002",
        "CASE_003",
        "CASE_004",
        "CASE_005",
        "CASE_006",
        "CASE_007",
        "CASE_008",
        "completed assault",
        "historical disclosure",
        "conflicting correction",
        "ambiguous intimidation",
        "corrected non-contact",
        "attempted strike",
    ]

    for term in forbidden_terms:
        assert term not in SEMANTIC_EXTRACTION_PROMPT


def test_model_validators_contain_no_fixture_identifiers_or_case_specific_labels():
    source = Path("src/models.py").read_text(encoding="utf-8")
    forbidden_terms = [
        "CASE_001",
        "CASE_002",
        "CASE_003",
        "CASE_004",
        "CASE_005",
        "CASE_006",
        "CASE_007",
        "CASE_008",
        "completed assault",
        "historical disclosure",
        "conflicting correction",
        "ambiguous intimidation",
        "corrected non-contact",
        "attempted strike",
    ]

    for term in forbidden_terms:
        assert term not in source
