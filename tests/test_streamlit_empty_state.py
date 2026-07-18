import sys
from unittest.mock import patch

from src.app_logic import run_analysis as build_analysis_result
from src.contracts import SemanticFacts
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Intentionality, ViolenceEventType
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus

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


def test_successful_result_restores_two_column_primary_comparison_and_details():
    fixture = SYNTHETIC_INCIDENTS[0]
    result = build_analysis_result(
        fixture["incident"],
        extractor=lambda _incident: SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=SemanticFacts(
                violence_present=True,
                event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
                actor="pt",
                target="rn",
                contact_occurred=True,
                injury_mentioned=True,
                current_event=True,
                intentionality=Intentionality.INTENTIONAL,
                negated=False,
                correction_present=False,
                conflicting_information=False,
                evidence_text=["he hit her on left side of face with closed fist"],
                confidence=0.9,
                uncertainty_notes=["Actor and target abbreviations are preserved."],
            ),
        ),
    )

    with patch("src.app_logic.run_analysis", return_value=result) as analyzer:
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)

    rendered = all_rendered_text(app_test)
    assert "Regex Baseline" in header_values(app_test)
    assert "Semantic Analysis" in header_values(app_test)
    assert "Semantic Extraction" not in header_values(app_test)
    assert "pt is described as responsible for completed physical violence involving rn." in rendered
    assert "Physical contact occurred. An injury was documented." in rendered
    assert "Illustrative lexical baseline based only on matching terms and patterns." in rendered
    assert [item.label for item in app_test.expander] == ["Technical Details"]
    for label in (
        "Result category:",
        "Validation stage:",
        "Schema validation status:",
        "Domain validation status:",
        "Violence present:",
        "Event type:",
        "Actor:",
        "Target:",
        "Contact occurred:",
        "Injury mentioned:",
        "Current event:",
        "Intentionality:",
        "Negation:",
        "Correction:",
        "Conflicting information:",
        "Confidence:",
        "Evidence excerpts",
        "Uncertainty notes",
        "Compatibility construction:",
        "Policy identifier:",
        "Policy version:",
        "Internal outcome:",
        "Reason codes:",
        "Internal explanation:",
    ):
        assert label in rendered
    assert analyzer.call_count == 1
