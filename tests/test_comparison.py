from src.comparison import build_comparison_result
from src.models import Incident, Intentionality, ViolenceEventType, ViolenceFinding
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


def finding(**overrides):
    data = {
        "violence_present": True,
        "event_type": ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
        "actor": "pt",
        "target": "rn",
        "contact_occurred": False,
        "injury_mentioned": False,
        "current_event": True,
        "intentionality": Intentionality.INTENTIONAL,
        "negated": False,
        "correction_present": False,
        "conflicting_information": False,
        "evidence_text": ["pt swung at rn missed"],
        "confidence": 0.9,
        "uncertainty_notes": [],
    }
    data.update(overrides)
    return ViolenceFinding(**data)


def semantic_success(**overrides):
    return SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        finding=finding(**overrides),
    )


def test_successful_outputs_produce_comparison_result():
    incident = Incident(incident_id="CASE_008", narrative="pt swung at rn missed. security called")
    regex = {"detected": True, "matched_terms": ["swing"], "matched_patterns": [r"\bsw(?:ing|ung)\b"]}

    result = build_comparison_result(incident, regex, semantic_success())

    assert result.incident is incident
    assert result.regex_result == regex
    assert result.semantic_validation_status == "success"
    assert result.observations


def test_comparison_layer_makes_no_provider_request():
    incident = Incident(incident_id="CASE_008", narrative="pt swung at rn missed. security called")

    build_comparison_result(
        incident,
        {"detected": True, "matched_terms": ["swing"], "matched_patterns": []},
        semantic_success(),
    )


def test_historical_semantic_result_produces_observation():
    result = build_comparison_result(
        Incident(incident_id="CASE_003", narrative="historical assault"),
        {"detected": True, "matched_terms": ["assault"], "matched_patterns": []},
        semantic_success(
            event_type=ViolenceEventType.NONE,
            violence_present=False,
            current_event=False,
            contact_occurred=False,
            evidence_text=["assaulted her a few yrs ago"],
        ),
    )

    assert "historical or non-current context" in " ".join(result.observations)


def test_negated_or_corrected_semantic_result_produces_observation():
    result = build_comparison_result(
        Incident(incident_id="CASE_007", narrative="correction pt did not kick nurse"),
        {"detected": True, "matched_terms": ["kick"], "matched_patterns": []},
        semantic_success(
            event_type=ViolenceEventType.NONE,
            violence_present=False,
            contact_occurred=False,
            negated=True,
            correction_present=True,
            evidence_text=["did not kick nurse"],
        ),
    )

    assert "corrected or negated" in " ".join(result.observations)


def test_attempted_violence_distinguished_from_completed():
    result = build_comparison_result(
        Incident(incident_id="CASE_008", narrative="pt swung at rn missed"),
        {"detected": True, "matched_terms": ["swing"], "matched_patterns": []},
        semantic_success(),
    )

    assert "attempted violence from completed violence" in " ".join(result.observations)


def test_accidental_contact_is_represented():
    result = build_comparison_result(
        Incident(incident_id="CASE_004", narrative="grabbed rn arm accidental"),
        {"detected": True, "matched_terms": ["grab"], "matched_patterns": []},
        semantic_success(
            event_type=ViolenceEventType.UNCLEAR,
            intentionality=Intentionality.ACCIDENTAL,
            contact_occurred=True,
            evidence_text=["looked accidental"],
        ),
    )

    assert "accidental contact" in " ".join(result.observations)


def test_semantic_failure_represented_without_default_finding():
    result = build_comparison_result(
        Incident(incident_id="CASE_X", narrative="text"),
        {"detected": False, "matched_terms": [], "matched_patterns": []},
        SemanticExtractionResult(status=SemanticExtractionStatus.REQUEST_FAILURE, failure_message="RequestError"),
    )

    assert result.semantic_result.finding is None
    assert result.observations == ["Semantic extraction returned failure; no validated finding is available."]
