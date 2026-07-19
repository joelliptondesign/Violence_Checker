import importlib
import sys
from unittest.mock import patch

from src.app_logic import (
    active_narrative_signature,
    is_stale_result,
    run_analysis as build_analysis_result,
    should_display_analysis_result,
)
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Incident
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from tests.successor_helpers import envelope


SOURCE_INSTRUCTION = "Select a fixture or enter a manual narrative, then press Run Analysis."
DEMONSTRATION_NOTICE = "Synthetic demonstration only, including manual narratives."


def fresh_app_test():
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("streamlit"):
            sys.modules.pop(module_name)
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file("app.py").run()


def header_values(app_test):
    return [item.value for item in app_test.header]


def all_rendered_text(app_test):
    values = []
    for collection_name in (
        "title", "header", "subheader", "caption", "info", "warning",
        "error", "markdown", "text",
    ):
        values.extend(
            getattr(item, "value", "")
            for item in getattr(app_test, collection_name, [])
        )
    return "\n".join(values)


def assert_no_analysis_output(app_test):
    headers = header_values(app_test)
    assert "Regex Baseline" not in headers
    assert "Semantic Analysis" not in headers
    assert "Comparison" not in headers
    assert "Salesforce Preview" not in headers
    assert len(app_test.json) == 0


def test_app_import_does_not_execute_analysis_or_provider_request():
    module = importlib.import_module("app")
    assert hasattr(module, "main")


def test_empty_initial_state_has_no_active_workflow_or_analysis_output():
    app_test = fresh_app_test()
    assert header_values(app_test) == ["Narrative source", "Incident Narrative"]
    assert app_test.caption[0].value == SOURCE_INSTRUCTION
    assert app_test.radio[0].options == ["Synthetic fixture", "Manual narrative"]
    assert app_test.radio[0].value is None
    assert len(app_test.selectbox) == len(app_test.button) == len(app_test.text_area) == 0
    assert "No active incident selected." in all_rendered_text(app_test)
    rendered = all_rendered_text(app_test)
    assert DEMONSTRATION_NOTICE in rendered
    assert "Do not submit real patient, hospital, PHI" in rendered
    assert "not a production hospital system" in rendered
    assert_no_analysis_output(app_test)


def test_missing_provider_configuration_renders_bounded_failure_without_secret_value():
    fixture = SYNTHETIC_INCIDENTS[0]
    incident = fixture["incident"]
    result = build_analysis_result(
        incident,
        extractor=lambda value: SemanticExtractionResult(
            SemanticExtractionStatus.CONFIGURATION_FAILURE,
            failure_message="OPENAI_API_KEY is required for semantic extraction.",
        ),
    )
    with patch("src.app_logic.run_analysis", return_value=result) as analyzer:
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)

    rendered = all_rendered_text(app_test)
    assert "Unable to Determine" in rendered
    assert "Semantic analysis is unavailable because the provider is not configured." in rendered
    assert "Preview is available only after successful validated semantic extraction." in rendered
    assert "deployment-secret" not in rendered
    assert not any("Illustrative_" in str(item.value) for item in app_test.json)
    assert analyzer.call_count == 1


def test_fixture_selection_alone_shows_raw_narrative_without_analysis():
    app_test = fresh_app_test()
    app_test.radio[0].set_value("Synthetic fixture").run()
    app_test.selectbox[0].set_value(SYNTHETIC_INCIDENTS[-1]).run()
    assert [button.label for button in app_test.button] == ["Run Analysis"]
    assert app_test.text_area[0].value == SYNTHETIC_INCIDENTS[-1]["incident"].narrative
    assert_no_analysis_output(app_test)


def test_manual_typing_alone_shows_raw_narrative_without_analysis():
    app_test = fresh_app_test()
    app_test.radio[0].set_value("Manual narrative").run()
    app_test.text_area[0].set_value("pt swung at rn missed").run()
    assert [button.label for button in app_test.button] == ["Run Analysis"]
    assert app_test.text_area[1].value == "pt swung at rn missed"
    assert_no_analysis_output(app_test)


def test_stale_result_invalidation_remains_deterministic():
    first = active_narrative_signature(Incident(incident_id="X", narrative="one"))
    second = active_narrative_signature(Incident(incident_id="X", narrative="two"))
    assert is_stale_result(first, second)
    assert not should_display_analysis_result(first, second)
    assert should_display_analysis_result(first, first)


def test_stale_result_is_cleared_when_active_source_changes():
    app_test = fresh_app_test()
    app_test.session_state["analysis_result"] = object()
    app_test.session_state["analysis_signature"] = "CASE_008:stale"
    app_test.radio[0].set_value("Manual narrative").run()
    app_test.text_area[0].set_value("pt swung at rn missed").run()
    assert "analysis_result" not in app_test.session_state
    assert "analysis_signature" not in app_test.session_state
    assert_no_analysis_output(app_test)


def test_rejected_manual_input_shows_bounded_failure_without_analysis_result():
    app_test = fresh_app_test()
    app_test.radio[0].set_value("Manual narrative").run()
    app_test.text_area[0].set_value("\ufeff").run()
    app_test.button[0].click().run()
    rendered = all_rendered_text(app_test)
    assert "Incident narrative must contain substantive text." in rendered
    assert "Unable to Determine" in rendered
    assert "The incident input could not be validated." in rendered
    assert "analysis_result" not in app_test.session_state
    assert_no_analysis_output(app_test)


def test_successful_run_renders_primary_result_before_baseline_details_and_preview_once():
    fixture = SYNTHETIC_INCIDENTS[0]
    incident = fixture["incident"]
    result = build_analysis_result(
        incident,
        extractor=lambda value: SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            envelope(narrative=value.narrative, incident_id=value.incident_id),
        ),
    )
    with patch("src.app_logic.run_analysis", return_value=result) as analyzer:
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)

    rendered = all_rendered_text(app_test)
    headers = header_values(app_test)
    assert "Regex Baseline" in header_values(app_test)
    assert "Semantic Analysis" in header_values(app_test)
    assert "Comparison" in header_values(app_test)
    assert "Salesforce Preview" in header_values(app_test)
    assert "Semantic schema:" in rendered
    assert "Propositions:" in rendered
    assert "Active propositions:" in rendered
    assert "Policy version: 2.0.0" in rendered
    assert headers.index("Semantic Analysis") < headers.index("Regex Baseline")
    assert len(app_test.get("column")) == 4
    assert any(
        "Illustrative_Write_Disposition__c" in str(item.value)
        for item in app_test.json
    )
    assert analyzer.call_count == 1
