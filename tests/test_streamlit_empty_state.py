import importlib
import inspect
import sys
from unittest.mock import patch

import pytest

from src.app_logic import (
    active_narrative_signature,
    is_stale_result,
    run_analysis as build_analysis_result,
    should_display_analysis_result,
)
from src.fixtures import SYNTHETIC_INCIDENTS
from src.contracts import (
    Completion,
    Contact,
    PipelineFailureProvenance,
    SemanticIntentionality,
    UncertaintyDimension,
)
from src.models import Incident
from src.policy import failed_policy_decision
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from tests.successor_helpers import envelope


SOURCE_INSTRUCTION = "Select a fixture or enter a manual narrative, then press Run Analysis."
APP_TITLE = "Workplace Safety Intelligence"
APP_SUBTITLE = (
    "AI reviews incident narratives to identify potential workplace violence, explain the reasoning, "
    "and support more consistent safety reporting."
)
PROHIBITED_VISIBLE_COPY = (
    "Synthetic demonstration data only",
    "Do not enter real patient data",
    "Do not enter hospital data",
    "Do not enter PHI",
    "Do not enter confidential data",
    "Do not enter production incident data",
    "Not a production hospital system",
    "Preview only",
    "No Salesforce connection",
    "No Salesforce write",
    "Rochester Regional",
    "Illustrative only",
    "Incident Narrative Review Demonstration",
    "Phase 0",
    "Pre-PoC",
)


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
        "title", "header", "subheader", "caption", "info", "success",
        "warning", "error", "markdown", "text",
    ):
        values.extend(
            getattr(item, "value", "")
            for item in getattr(app_test, collection_name, [])
        )
    return "\n".join(values)


def assert_no_analysis_output(app_test):
    headers = header_values(app_test)
    assert "Regex Keyword Detection" not in headers
    assert "AI-Powered Semantic Analysis" not in headers
    assert "What the Two Methods Show" not in headers
    assert "Illustrative Salesforce Record" not in headers
    assert len(app_test.json) == 0


def assert_no_prohibited_visible_copy(app_test):
    rendered = all_rendered_text(app_test).casefold()
    assert not any(candidate.casefold() in rendered for candidate in PROHIBITED_VISIBLE_COPY)


def test_app_import_does_not_execute_analysis_or_provider_request():
    module = importlib.import_module("app")
    assert hasattr(module, "main")


def test_empty_initial_state_has_no_active_workflow_or_analysis_output():
    app_test = fresh_app_test()
    assert app_test.title[0].value == APP_TITLE
    assert header_values(app_test) == ["Incident Narrative"]
    assert SOURCE_INSTRUCTION in [item.value for item in app_test.caption]
    assert app_test.radio[0].options == ["Synthetic fixture", "Manual narrative"]
    assert app_test.radio[0].value is None
    assert len(app_test.selectbox) == len(app_test.button) == len(app_test.text_area) == 0
    assert "No active incident selected." in all_rendered_text(app_test)
    rendered = all_rendered_text(app_test)
    assert APP_SUBTITLE in rendered
    assert rendered.count(APP_SUBTITLE) == 1
    assert_no_prohibited_visible_copy(app_test)
    assert len(app_test.info) == len(app_test.warning) == 0
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
    assert "Analysis Failed" in rendered
    assert "The analysis service is not configured." in rendered
    assert "No record generated for this result." in rendered
    assert "Incident Summary" not in rendered
    assert "Why This Result" not in rendered
    assert "Key Findings" not in rendered
    assert "deployment-secret" not in rendered
    assert not any("Illustrative_" in str(item.value) for item in app_test.json)
    assert len(app_test.table) == 0
    assert [item.label for item in app_test.expander] == ["Technical Details", "Technical Details"]
    assert_no_prohibited_visible_copy(app_test)
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
    message = "Incident narrative must contain substantive text."
    assert rendered.count(message) == 1
    assert "The incident narrative is not valid for analysis." not in rendered
    assert "analysis_result" not in app_test.session_state
    assert_no_analysis_output(app_test)


def test_successful_run_renders_two_owned_cards_without_shared_sections():
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
    assert "Regex Keyword Detection" in headers
    assert "AI-Powered Semantic Analysis" in headers
    assert "What the Two Methods Show" not in headers
    assert "Illustrative Salesforce Record" in header_values(app_test)
    assert rendered.count("Incident Summary") == 1
    assert rendered.count("Why This Result") == 1
    assert rendered.count("Key Findings") == 1
    assert "Why This Matters" not in rendered
    assert "The narrative describes violence involving another person." not in rendered
    assert "The result is based on the reported event details shown above." not in rendered
    assert "What the Keyword Detector Noticed" not in rendered
    assert "What the AI Analysis Understood" not in rendered
    assert "Why the Views Agree or Differ" not in rendered
    assert "Why the Comparison Matters" not in rendered
    assert not any(
        term in rendered
        for term in (
            "Semantic schema:",
            "Propositions:",
            "Active propositions:",
            "Policy version:",
            "Reason codes:",
            "Classification alignment:",
            "Material difference detected:",
            "ENT-",
            "PROP-",
            "EVIDENCE-",
        )
    )
    assert headers == [
        "Incident Narrative",
        "Regex Keyword Detection",
        "AI-Powered Semantic Analysis",
        "Illustrative Salesforce Record",
    ]
    source = __import__("pathlib").Path("app.py").read_text(encoding="utf-8")
    assert "@media (max-width: 640px)" in source
    assert "semantic-result-marker) { order: 1; }" in source
    assert "regex-result-marker) { order: 2; }" in source
    assert source.count('st.header("AI-Powered Semantic Analysis")') == 1
    assert source.count('st.header("Regex Keyword Detection")') == 1
    assert source.count('st.markdown("### Incident Summary")') == 1
    assert source.count('st.markdown("### Why This Result")') == 1
    assert source.count('st.markdown("### Key Findings")') == 1
    assert len(app_test.expander) == 3
    assert [item.label for item in app_test.expander] == [
        "Technical Details",
        "Technical Details",
        "Salesforce Payload Details",
    ]
    assert source.count('st.expander("Technical Details", expanded=False)') == 2
    assert source.count('st.expander("Salesforce Payload Details", expanded=False)') == 1
    assert source.count("regex-technical-details-marker") == 1
    assert source.count("ai-technical-details-marker") == 1
    assert len(app_test.get("column")) == 4
    assert len(app_test.json) == 0
    assert len(app_test.code) == 1
    assert app_test.code[0].language == "yaml"
    assert app_test.code[0].value == (
        "incident_facts:\n"
        "  participants_identified: true\n"
        "  occurred_during_current_incident: true\n"
        "  involved_another_person: true\n"
        "  conduct_was_intentional: true\n"
        "  physical_contact_occurred: true\n"
        "  reported_conduct_supported: true\n"
        "  conflicting_accounts: false\n"
        "result:\n"
        "  workplace_violence_assessment: Violence Detected"
    )
    assert not any(
        term in app_test.code[0].value.casefold()
        for term in (
            "proposition",
            "schema",
            "validation metadata",
            "policy identifier",
            "reason code",
            "entity id",
            "relationship id",
            "uncertainty object",
            "serialized contract",
        )
    )
    assert source.count("salesforce-payload-details-marker") == 1
    assert len(app_test.table) == 3
    assert list(app_test.table[0].value.columns) == ["Role", "Category"]
    assert app_test.table[0].value.to_dict("records") == [
        {"Role": "Patient", "Category": "Patient"},
        {"Role": "Nurse", "Category": "Clinical Staff"},
    ]
    assert app_test.table[1].value.to_dict("records") == [
        {"Field": "Incident Identifier", "Value": result.salesforce_preview["Illustrative_Incident_Identifier__c"]},
        {"Field": "Write Disposition", "Value": result.salesforce_preview["Illustrative_Write_Disposition__c"]},
        {"Field": "Evidence", "Value": result.salesforce_preview["Illustrative_Evidence__c"][0]},
    ]
    payload_rows = app_test.table[2].value.to_dict("records")
    assert [row["Field"] for row in payload_rows] == list(result.salesforce_preview)
    assert "Preview" not in rendered
    assert "connection" not in rendered.casefold()
    assert not any(
        term in rendered.casefold()
        for term in (
            "semantic analysis pipeline",
            "repository validation",
            "deterministic application rules",
            "assertion_confirmed",
            "validated_facts",
        )
    )
    assert_no_prohibited_visible_copy(app_test)
    assert analyzer.call_count == 1


def test_regex_card_has_exact_operator_copy_and_separate_bounded_inspection():
    import app

    operator_source = inspect.getsource(app._display_regex_operator_view)
    details_source = inspect.getsource(app._display_regex_technical_details)
    assert "Traditional regular expression (regex) matching scans the incident narrative for predefined words and phrases." in operator_source
    assert '"Potential Match" if detected else "No Match"' in operator_source
    assert "Searches for matching words rather than the overall meaning." in operator_source
    assert "May miss important context or flag words used in a different way." in operator_source
    assert "matched_patterns" not in operator_source
    assert all(term in details_source for term in ("Keyword Matching", "Detected", "Matched Terms", "Matched Patterns"))
    assert not any(term in details_source for term in ("communication", "comparison", "salesforce", "semantic"))


def test_no_match_card_uses_concise_empty_evidence_state():
    fixture = SYNTHETIC_INCIDENTS[0]
    result = build_analysis_result(
        fixture["incident"],
        extractor=lambda value: SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            envelope(narrative=value.narrative, incident_id=value.incident_id),
        ),
    )
    result = result.__class__(
        **{**result.__dict__, "regex_result": {"detected": False, "matched_terms": [], "matched_patterns": []}}
    )
    with patch("src.app_logic.run_analysis", return_value=result):
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)
    rendered = all_rendered_text(app_test)
    assert "No Match" in rendered
    assert "No configured keyword or phrase was detected." in rendered


def test_ai_card_has_exact_operator_copy_and_incident_only_inspection():
    import app

    operator_source = inspect.getsource(app._display_ai_operator_view)
    details_source = inspect.getsource(app._display_ai_technical_details)
    assert "Reviews the incident as a whole, including who was involved, what occurred, and whether the reported conduct meets the workplace violence criteria." in operator_source
    assert all(term in details_source for term in ("Extracted Entities", "Supporting Evidence", "Decision Logic"))
    assert "Generated Operator Communication" not in details_source
    assert "_display_operator_communication" not in details_source
    assert not any(
        term in details_source
        for term in (
            "schema_identity",
            "schema_version",
            "policy_id",
            "reason_codes",
            "classification_alignment",
            "salesforce_preview",
            "model_dump",
            "st.json",
        )
    )


def test_salesforce_payload_details_are_owned_only_by_salesforce_section():
    import app

    salesforce_source = inspect.getsource(app._display_salesforce_record)
    regex_source = inspect.getsource(app._display_regex_technical_details)
    ai_source = inspect.getsource(app._display_ai_technical_details)
    results_source = inspect.getsource(app._display_results)
    assert 'st.expander("Salesforce Payload Details", expanded=False)' in salesforce_source
    assert "salesforce_payload_rows(payload)" in salesforce_source
    assert not any(
        term in salesforce_source
        for term in ("communication", "validation_result", "policy_decision", "comparison")
    )
    assert "Salesforce" not in regex_source
    assert "salesforce" not in regex_source
    assert "Salesforce" not in ai_source
    assert "salesforce" not in ai_source
    assert results_source.index("st.columns(2)") < results_source.index("_display_salesforce_record")


@pytest.mark.parametrize("viewport_width", [390, 360, 320])
def test_mobile_layout_contract_keeps_ai_first_without_page_overflow(viewport_width):
    source = __import__("pathlib").Path("app.py").read_text(encoding="utf-8")
    assert viewport_width <= 640
    assert ".stApp { overflow-x: hidden; }" in source
    assert "@media (max-width: 640px)" in source
    assert "semantic-result-marker) { order: 1; }" in source
    assert "regex-result-marker) { order: 2; }" in source
    assert source.count("semantic-result-marker") == 2
    assert source.count("regex-result-marker") == 2
    assert source.count('st.header("Illustrative Salesforce Record")') == 2


def test_regex_and_ai_inspection_preserve_exact_readable_evidence():
    fixture = SYNTHETIC_INCIDENTS[0]
    incident = fixture["incident"]
    result = build_analysis_result(
        incident,
        extractor=lambda value: SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            envelope(narrative=value.narrative, incident_id=value.incident_id),
        ),
    )
    with patch("src.app_logic.run_analysis", return_value=result):
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)
    rendered = all_rendered_text(app_test)
    assert "- “hit”" in rendered
    assert "- `\\bhit\\b`" in rendered
    assert f"- “{incident.narrative}”" in rendered


@pytest.mark.parametrize(
    "candidate_options,expected_label,expected_yaml_fact",
    [
        (
            {"intentionality": SemanticIntentionality.ACCIDENTAL},
            "No Violence Detected",
            "conduct_was_intentional: false",
        ),
        (
            {
                "completion": Completion.UNDETERMINED,
                "contact": Contact.UNDETERMINED,
                "uncertainty_dimension": UncertaintyDimension.CONTACT,
            },
            "Unable to Determine",
            "physical_contact_occurred: uncertain",
        ),
    ],
)
def test_ai_card_renders_existing_negative_and_uncertain_result_labels(
    candidate_options, expected_label, expected_yaml_fact
):
    fixture = SYNTHETIC_INCIDENTS[0]
    incident = fixture["incident"]
    candidate = envelope(
        narrative=incident.narrative,
        incident_id=incident.incident_id,
        **candidate_options,
    )
    result = build_analysis_result(
        incident,
        extractor=lambda _value: SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, candidate),
    )
    with patch("src.app_logic.run_analysis", return_value=result):
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)
    assert expected_label in all_rendered_text(app_test)
    assert app_test.code[0].language == "yaml"
    assert expected_yaml_fact in app_test.code[0].value
    assert f"workplace_violence_assessment: {expected_label}" in app_test.code[0].value
    assert len(app_test.json) == 0


def test_provider_and_fallback_communication_share_the_same_surface():
    fixture = SYNTHETIC_INCIDENTS[0]
    incident = fixture["incident"]
    fallback = build_analysis_result(
        incident,
        extractor=lambda value: SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            envelope(narrative=value.narrative, incident_id=value.incident_id),
        ),
    )
    provider_copy = fallback.communication.model_copy(
        update={
            "incident_summary": "Provider summary.",
            "key_findings": ("Provider finding",),
            "why_this_result": "Provider reason.",
        }
    )
    provider_result = fallback.__class__(
        **{**fallback.__dict__, "communication": provider_copy}
    )

    for result, expected in ((fallback, fallback.communication.incident_summary), (provider_result, "Provider summary.")):
        with patch("src.app_logic.run_analysis", return_value=result):
            app_test = fresh_app_test()
            app_test.radio[0].set_value("Synthetic fixture").run()
            app_test.selectbox[0].set_value(fixture).run()
            app_test.button[0].click().run(timeout=10)
        rendered = all_rendered_text(app_test)
        assert expected in rendered
        assert rendered.count("Incident Summary") == 1
        assert rendered.count("Why This Result") == 1
        assert rendered.count("Key Findings") == 1


def test_validation_failure_does_not_render_successful_communication_sections():
    fixture = SYNTHETIC_INCIDENTS[0]
    incident = fixture["incident"]
    invalid = envelope(
        narrative=incident.narrative,
        incident_id=incident.incident_id,
    ).model_copy(update={"schema_version": "unsupported"})
    result = build_analysis_result(
        incident,
        extractor=lambda _value: SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            invalid,
        ),
    )
    with patch("src.app_logic.run_analysis", return_value=result):
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)

    rendered = all_rendered_text(app_test)
    assert "Analysis Failed" in rendered
    assert "The result was missing required information." in rendered
    assert "Incident Summary" not in rendered
    assert "Why This Result" not in rendered
    assert "Key Findings" not in rendered
    assert "No validated entities are available." in rendered
    assert "No validated supporting evidence is available." in rendered
    assert "Decision Logic" in rendered
    assert app_test.code[0].language == "yaml"
    assert "confirmed_details_available: false" in app_test.code[0].value
    assert "workplace_violence_assessment: Analysis Failed" in app_test.code[0].value


def test_policy_failure_does_not_render_successful_communication_sections():
    fixture = SYNTHETIC_INCIDENTS[0]
    incident = fixture["incident"]
    with patch(
        "src.app_logic.evaluate_policy",
        return_value=failed_policy_decision(PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT),
    ):
        result = build_analysis_result(
            incident,
            extractor=lambda value: SemanticExtractionResult(
                SemanticExtractionStatus.SUCCESS,
                envelope(narrative=value.narrative, incident_id=value.incident_id),
            ),
        )
    with patch("src.app_logic.run_analysis", return_value=result):
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)

    rendered = all_rendered_text(app_test)
    assert "Analysis Failed" in rendered
    assert "could not be classified" in rendered
    assert "Incident Summary" not in rendered
    assert "Why This Result" not in rendered
    assert "Key Findings" not in rendered
    assert "Decision Logic" in rendered
    assert app_test.code[0].language == "yaml"
    assert "participants_identified: true" in app_test.code[0].value
    assert "physical_contact_occurred: true" in app_test.code[0].value
    assert "workplace_violence_assessment: Analysis Failed" in app_test.code[0].value
