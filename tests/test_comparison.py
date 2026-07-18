from src.comparison import build_comparison_result as _build_comparison_result
from src.compatibility_finding import construct_compatibility_finding
from src.contracts import SemanticFacts
from src.models import Incident, Intentionality, ViolenceEventType
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from src.semantic_validation import validate_semantic_candidate, validation_not_run


def facts(**overrides):
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
    return SemanticFacts(**data)


def semantic_success(**overrides):
    return SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        semantic_candidate=facts(**overrides),
    )


def build_comparison_result(incident, regex, semantic_result):
    validation = validation_not_run()
    compatibility = None
    if semantic_result.succeeded:
        validation = validate_semantic_candidate(semantic_result.semantic_candidate)
        if validation.validated_facts is not None:
            compatibility = construct_compatibility_finding(validation.validated_facts)
    return _build_comparison_result(incident, regex, semantic_result, validation, compatibility)


def test_successful_outputs_produce_comparison_result():
    incident = Incident(incident_id="CASE_008", narrative="pt swung at rn missed. security called")
    regex = {"detected": True, "matched_terms": ["swing"], "matched_patterns": [r"\bsw(?:ing|ung)\b"]}

    result = build_comparison_result(incident, regex, semantic_success())

    assert result.incident is incident
    assert result.regex_result == regex
    assert result.semantic_validation_status == "success"
    assert result.observations
    assert result.classification_alignment == "aligned_positive"
    assert result.material_difference_detected is True
    assert result.display_status == "Classification Aligned, Semantic Context Added"


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

    assert result.material_difference_detected is True
    assert result.classification_alignment == "regex_positive_semantic_negative"
    assert result.display_status == "Material Difference Detected"
    assert "historical or non-current" in " ".join(result.semantic_enrichment_observations)


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

    observations = " ".join(result.semantic_enrichment_observations)
    assert result.material_difference_detected is True
    assert "negated violence language" in observations
    assert "correction" in observations


def test_attempted_violence_distinguished_from_completed():
    result = build_comparison_result(
        Incident(incident_id="CASE_008", narrative="pt swung at rn missed"),
        {"detected": True, "matched_terms": ["swing"], "matched_patterns": []},
        semantic_success(),
    )

    assert result.material_difference_detected is True
    assert "attempted physical violence" in " ".join(result.semantic_enrichment_observations)


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

    assert result.material_difference_detected is True
    assert "accidental contact" in " ".join(result.semantic_enrichment_observations)


def test_semantic_failure_represented_without_default_finding():
    result = build_comparison_result(
        Incident(incident_id="CASE_X", narrative="text"),
        {"detected": False, "matched_terms": [], "matched_patterns": []},
        SemanticExtractionResult(status=SemanticExtractionStatus.REQUEST_FAILURE, failure_message="RequestError"),
    )

    assert result.semantic_result.semantic_candidate is None
    assert result.classification_alignment == "semantic_failure"
    assert result.material_difference_detected is True
    assert result.display_status == "Semantic Comparison Unavailable"
    assert result.divergence_observations == [
        "Semantic extraction failed and no validated semantic comparison is available."
    ]


def test_regex_positive_semantic_negative_produces_material_difference():
    result = build_comparison_result(
        Incident(incident_id="CASE_NEG", narrative="did not punch anyone"),
        {"detected": True, "matched_terms": ["punch"], "matched_patterns": []},
        semantic_success(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            contact_occurred=False,
            negated=True,
            evidence_text=["did not punch anyone"],
        ),
    )

    assert result.classification_alignment == "regex_positive_semantic_negative"
    assert result.material_difference_detected is True
    assert result.divergence_observations == [
        "Regex detected violence-related language, but semantic extraction determined no violence."
    ]


def test_regex_negative_semantic_positive_produces_material_difference():
    result = build_comparison_result(
        Incident(incident_id="CASE_POS", narrative="patient shoved the nurse"),
        {"detected": False, "matched_terms": [], "matched_patterns": []},
        semantic_success(
            violence_present=True,
            event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
            contact_occurred=True,
            evidence_text=["patient shoved the nurse"],
        ),
    )

    assert result.classification_alignment == "regex_negative_semantic_positive"
    assert result.material_difference_detected is True
    assert result.display_status == "Material Difference Detected"
    assert result.divergence_observations == [
        "Regex did not detect violence-related language, but semantic extraction determined violence was present."
    ]


def test_verbal_threat_produces_semantic_enrichment():
    result = build_comparison_result(
        Incident(incident_id="CASE_002", narrative="im gonna punch somebody"),
        {"detected": True, "matched_terms": ["gonna punch"], "matched_patterns": []},
        semantic_success(
            event_type=ViolenceEventType.VERBAL_THREAT,
            contact_occurred=False,
            evidence_text=["im gonna punch somebody"],
        ),
    )

    assert result.classification_alignment == "aligned_positive"
    assert result.material_difference_detected is True
    assert result.display_status == "Classification Aligned, Semantic Context Added"
    assert "verbal threat" in " ".join(result.semantic_enrichment_observations)


def test_correction_produces_semantic_enrichment():
    result = build_comparison_result(
        Incident(incident_id="CASE_007", narrative="correction pt kicked rail"),
        {"detected": True, "matched_terms": ["kicked"], "matched_patterns": []},
        semantic_success(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            contact_occurred=False,
            correction_present=True,
            evidence_text=["correction pt kicked rail"],
        ),
    )

    assert result.material_difference_detected is True
    assert "correction" in " ".join(result.semantic_enrichment_observations)


def test_conflicting_information_produces_semantic_enrichment():
    result = build_comparison_result(
        Incident(incident_id="CASE_005", narrative="first report said punched later denied"),
        {"detected": True, "matched_terms": ["punched"], "matched_patterns": []},
        semantic_success(
            event_type=ViolenceEventType.UNCLEAR,
            conflicting_information=True,
            evidence_text=["first report said punched later denied"],
            uncertainty_notes=["Later statement conflicts with first report."],
        ),
    )

    assert result.material_difference_detected is True
    assert "conflicting statements" in " ".join(result.semantic_enrichment_observations)


def test_no_contact_distinction_produces_semantic_enrichment():
    result = build_comparison_result(
        Incident(incident_id="CASE_008", narrative="pt swung and missed"),
        {"detected": True, "matched_terms": ["swung"], "matched_patterns": []},
        semantic_success(
            event_type=ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
            contact_occurred=False,
            evidence_text=["pt swung and missed"],
        ),
    )

    assert result.material_difference_detected is True
    assert "no person-directed physical contact" in " ".join(result.semantic_enrichment_observations)


def test_evidence_and_uncertainty_are_represented_without_provider_call():
    result = build_comparison_result(
        Incident(incident_id="CASE_EVIDENCE", narrative="pt hit rn maybe"),
        {"detected": True, "matched_terms": ["hit"], "matched_patterns": []},
        semantic_success(
            event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
            contact_occurred=True,
            evidence_text=["pt hit rn"],
            confidence=0.55,
            uncertainty_notes=["Unclear target role."],
        ),
    )

    observations = " ".join(result.semantic_enrichment_observations)
    assert result.material_difference_detected is True
    assert "supporting evidence excerpts" in observations
    assert "confidence or uncertainty" in observations


def test_no_material_difference_only_for_minimal_aligned_finding():
    result = build_comparison_result(
        Incident(incident_id="CASE_MIN", narrative="quiet shift"),
        {"detected": False, "matched_terms": [], "matched_patterns": []},
        semantic_success(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            actor=None,
            target=None,
            contact_occurred=False,
            injury_mentioned=False,
            current_event=True,
            intentionality=Intentionality.UNCLEAR,
            evidence_text=[],
            confidence=1.0,
            uncertainty_notes=[],
        ),
    )

    assert result.classification_alignment == "aligned_negative"
    assert result.material_difference_detected is False
    assert result.display_status == "No Material Difference Identified"
    assert result.observations == ["No material difference identified."]


def test_case_003_like_historical_output_no_longer_returns_no_difference():
    result = build_comparison_result(
        Incident(incident_id="CASE_003", narrative="ex boyfriend assaulted her a few yrs ago"),
        {"detected": True, "matched_terms": ["assaulted"], "matched_patterns": []},
        semantic_success(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            contact_occurred=False,
            current_event=False,
            evidence_text=["assaulted her a few yrs ago"],
        ),
    )

    assert result.display_status != "No Material Difference Identified"


def test_case_004_like_accidental_output_no_longer_returns_no_difference():
    result = build_comparison_result(
        Incident(incident_id="CASE_004", narrative="grabbed rn arm accidental"),
        {"detected": True, "matched_terms": ["grabbed"], "matched_patterns": []},
        semantic_success(
            event_type=ViolenceEventType.UNCLEAR,
            intentionality=Intentionality.ACCIDENTAL,
            contact_occurred=True,
            evidence_text=["looked accidental"],
        ),
    )

    assert result.display_status != "No Material Difference Identified"


def test_case_007_like_corrected_output_no_longer_returns_no_difference():
    result = build_comparison_result(
        Incident(incident_id="CASE_007", narrative="did not kick nurse kicked rail"),
        {"detected": True, "matched_terms": ["kick"], "matched_patterns": []},
        semantic_success(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            contact_occurred=False,
            correction_present=True,
            evidence_text=["did not kick nurse"],
        ),
    )

    assert result.display_status != "No Material Difference Identified"


def test_case_008_like_attempted_output_no_longer_returns_no_difference():
    result = build_comparison_result(
        Incident(incident_id="CASE_008", narrative="pt swung at rn missed"),
        {"detected": True, "matched_terms": ["swung"], "matched_patterns": []},
        semantic_success(),
    )

    assert result.display_status != "No Material Difference Identified"
