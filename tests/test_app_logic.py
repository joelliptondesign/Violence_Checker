import importlib

import pytest

from src.app_logic import (
    active_narrative_signature,
    create_manual_incident,
    is_stale_result,
    run_analysis,
    should_display_analysis_result,
    validate_manual_narrative,
)
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Intentionality, ViolenceEventType, ViolenceFinding
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


def valid_semantic_result():
    return SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        finding=ViolenceFinding(
            violence_present=True,
            event_type=ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
            actor="pt",
            target="rn",
            contact_occurred=False,
            injury_mentioned=False,
            current_event=True,
            intentionality=Intentionality.INTENTIONAL,
            negated=False,
            correction_present=False,
            conflicting_information=False,
            evidence_text=["pt swung at rn missed"],
            confidence=0.9,
            uncertainty_notes=[],
        ),
    )


def test_app_imports_without_making_provider_request():
    app = importlib.import_module("app")

    assert hasattr(app, "main")


def test_analysis_is_not_invoked_on_import():
    app = importlib.reload(importlib.import_module("app"))

    assert hasattr(app, "run_analysis")


def test_empty_manual_input_is_rejected():
    with pytest.raises(ValueError):
        validate_manual_narrative("   ")


def test_manual_input_preserves_text():
    text = "  freeform narrative stays as typed  "

    incident = create_manual_incident(text)

    assert incident.narrative == text


def test_fixture_metadata_is_not_passed_to_semantic_extraction():
    fixture = next(item for item in SYNTHETIC_INCIDENTS if item["incident"].incident_id == "CASE_008")
    calls = []

    def extractor(incident):
        calls.append(incident)
        return valid_semantic_result()

    run_analysis(fixture["incident"], extractor=extractor)

    assert calls == [fixture["incident"]]
    assert fixture["metadata"]["scenario_type"] not in calls[0].narrative


def test_stale_result_protection_is_deterministic():
    first = create_manual_incident("first narrative")
    second = create_manual_incident("second narrative")

    assert is_stale_result(active_narrative_signature(first), active_narrative_signature(second)) is True
    assert is_stale_result(active_narrative_signature(first), active_narrative_signature(first)) is False
    assert should_display_analysis_result(active_narrative_signature(first), active_narrative_signature(second)) is False
    assert should_display_analysis_result(active_narrative_signature(first), active_narrative_signature(first)) is True


def test_one_analysis_action_results_in_one_semantic_extraction_call():
    fixture = next(item for item in SYNTHETIC_INCIDENTS if item["incident"].incident_id == "CASE_008")
    calls = []

    def extractor(incident):
        calls.append(incident.incident_id)
        return valid_semantic_result()

    result = run_analysis(fixture["incident"], extractor=extractor)

    assert calls == ["CASE_008"]
    assert result.salesforce_preview is not None
