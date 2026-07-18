import sys
from unittest.mock import patch

from src.fixtures import SYNTHETIC_INCIDENTS

SOURCE_INSTRUCTION = "Select a fixture or enter a manual narrative, then press Run Analysis."
REMOVED_DISCLAIMER = (
    "Synthetic data only. The regex baseline is illustrative, lexical-only, "
    "and not Rochester Regional's actual implementation."
)


def fresh_app_test():
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("streamlit"):
            sys.modules.pop(module_name)
    from streamlit.testing.v1 import AppTest as FreshAppTest

    return FreshAppTest.from_file("app.py").run()


def header_values(app_test):
    return [item.value for item in app_test.header]


def assert_no_analysis_output(app_test):
    headers = header_values(app_test)

    assert "Regex Baseline" not in headers
    assert "Semantic Extraction" not in headers
    assert "Comparison" not in headers
    assert "Salesforce Preview" not in headers
    assert len(app_test.json) == 0


def assert_narrative_source_controls(app_test):
    assert app_test.radio[0].label == "Narrative source"
    assert app_test.radio[0].options == ["Synthetic fixture", "Manual narrative"]
    assert "Select a source" not in app_test.radio[0].options


def all_rendered_text(app_test):
    values = []
    for collection_name in ("title", "header", "subheader", "caption", "info", "warning", "error", "markdown", "text"):
        collection = getattr(app_test, collection_name, [])
        values.extend(getattr(item, "value", "") for item in collection)
    return "\n".join(values)


def test_empty_initial_state_has_no_active_source_workflow_or_analysis_output():
    app_test = fresh_app_test()

    assert header_values(app_test) == ["Narrative source", "Incident Narrative"]
    assert app_test.caption[0].value == SOURCE_INSTRUCTION
    assert_narrative_source_controls(app_test)
    assert app_test.radio[0].value is None
    assert len(app_test.selectbox) == 0
    assert len(app_test.button) == 0
    assert len(app_test.text_area) == 0
    assert "No active incident selected." in all_rendered_text(app_test)
    assert_no_analysis_output(app_test)
    assert REMOVED_DISCLAIMER not in all_rendered_text(app_test)


def test_initial_load_makes_no_provider_request():
    with patch("src.semantic_extractor.extract_violence_finding") as extractor:
        app_test = fresh_app_test()

    assert extractor.call_count == 0
    assert_no_analysis_output(app_test)


def test_fixture_selection_alone_shows_narrative_without_analysis_output():
    with patch("src.semantic_extractor.extract_violence_finding") as extractor:
        app_test = fresh_app_test()

        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(SYNTHETIC_INCIDENTS[-1]).run()

    assert extractor.call_count == 0
    assert [button.label for button in app_test.button] == ["Run Analysis"]
    assert app_test.text_area[0].label == "Original narrative used for analysis"
    assert app_test.text_area[0].value == "pt swung at rn missed. security called"
    assert_no_analysis_output(app_test)


def test_manual_typing_alone_shows_narrative_without_analysis_output():
    with patch("src.semantic_extractor.extract_violence_finding") as extractor:
        app_test = fresh_app_test()

        app_test.radio[0].set_value("Manual narrative").run()
        app_test.text_area[0].set_value("pt swung at rn missed").run()

    assert extractor.call_count == 0
    assert [button.label for button in app_test.button] == ["Run Analysis"]
    assert app_test.text_area[1].label == "Original narrative used for analysis"
    assert app_test.text_area[1].value == "pt swung at rn missed"
    assert_no_analysis_output(app_test)


def test_stale_result_clears_when_source_mode_changes():
    app_test = fresh_app_test()
    app_test.session_state["analysis_result"] = object()
    app_test.session_state["analysis_signature"] = "CASE_008:pt swung at rn missed. security called"

    app_test.radio[0].set_value("Manual narrative").run()
    app_test.text_area[0].set_value("pt swung at rn missed").run()

    assert "analysis_result" not in app_test.session_state
    assert "analysis_signature" not in app_test.session_state
    assert_no_analysis_output(app_test)


def test_newly_rejected_manual_input_shows_bounded_feedback_without_analysis():
    app_test = fresh_app_test()

    app_test.radio[0].set_value("Manual narrative").run()
    app_test.text_area[0].set_value("\ufeff").run()
    app_test.button[0].click().run()

    assert "Incident narrative must contain substantive text." in all_rendered_text(app_test)
    assert "AI Assessment" in header_values(app_test)
    assert "Unable to Determine" in all_rendered_text(app_test)
    assert "The incident input could not be validated." in all_rendered_text(app_test)
    assert "Application Write Disposition" not in all_rendered_text(app_test)
    assert [item.label for item in app_test.expander] == ["Technical Details"]
    assert "Internal outcome: WRITE_FAILED" in all_rendered_text(app_test)
    assert "Reason codes: ['input_validation_failed']" in all_rendered_text(app_test)
    assert "analysis_result" not in app_test.session_state
    assert "analysis_signature" not in app_test.session_state
    assert_no_analysis_output(app_test)
