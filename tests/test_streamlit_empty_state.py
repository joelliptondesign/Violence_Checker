import importlib
import sys
from pathlib import Path
from unittest.mock import patch

from src.app_logic import run_analysis
from src.fixtures import SYNTHETIC_INCIDENTS
from src.contracts import ProviderFactEvidenceCandidate
from src.models import Incident
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from tests.test_app_logic import ALL_SUPPORTS, candidate_for, extraction_for


def fresh_app_test():
    for name in list(sys.modules):
        if name == "app" or name.startswith("streamlit"):
            sys.modules.pop(name)
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file("app.py").run()


def rendered(app_test):
    collections = ("title", "header", "subheader", "caption", "error", "markdown", "text")
    return "\n".join(getattr(item, "value", "") for name in collections for item in getattr(app_test, name, []))


def test_app_import_and_empty_state_do_not_execute_analysis():
    assert hasattr(importlib.import_module("app"), "main")
    app_test = fresh_app_test()
    assert app_test.title[0].value == "Workplace Safety Intelligence"
    assert [item.value for item in app_test.header] == ["Incident Narrative"]
    assert app_test.radio[0].value is None
    assert "No active incident selected." in rendered(app_test)


def test_successful_run_preserves_two_cards_mobile_order_and_true_north_details():
    fixture = SYNTHETIC_INCIDENTS[0]
    narrative = fixture["incident"].narrative
    evidence = "he hit her on left side of face with closed fist"
    result = run_analysis(
        fixture["incident"],
        extractor=extraction_for(candidate_for(
            narrative,
            incident_id=fixture["incident"].incident_id,
            evidence=[ProviderFactEvidenceCandidate(excerpt=evidence, supports=ALL_SUPPORTS)],
        )),
    )
    with patch("src.app_logic.run_analysis", return_value=result):
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)

    text = rendered(app_test)
    assert [item.value for item in app_test.header] == [
        "Incident Narrative", "Regex Keyword Detection", "AI-Powered Semantic Analysis",
        "Illustrative Salesforce Record",
    ]
    assert all(value in text for value in ("Incident Summary", "Key Findings", "Why This Result", "Violence Detected"))
    assert [item.label for item in app_test.expander] == ["Technical Details", "Technical Details", "Salesforce Payload Details"]
    assert list(app_test.table[0].value.columns) == ["Conduct", "Direction", "Intent", "Timing", "Assertion", "Resolution"]
    assert "incident_direction:" in app_test.code[0].value
    assert not any(term in app_test.code[0].value.lower() for term in ("proposition", "entity", "relationship"))
    source = Path("app.py").read_text(encoding="utf-8")
    assert "@media (max-width: 640px)" in source
    assert "semantic-result-marker) { order: 1; }" in source
    assert "regex-result-marker) { order: 2; }" in source


def test_unable_result_renders_bounded_communication_and_no_record():
    fixture = SYNTHETIC_INCIDENTS[0]
    incident = fixture["incident"]
    result = run_analysis(
        incident,
        extractor=lambda _: SemanticExtractionResult(SemanticExtractionStatus.REQUEST_FAILURE, failure_message="secret-value"),
    )
    with patch("src.app_logic.run_analysis", return_value=result):
        app_test = fresh_app_test()
        app_test.radio[0].set_value("Synthetic fixture").run()
        app_test.selectbox[0].set_value(fixture).run()
        app_test.button[0].click().run(timeout=10)
    text = rendered(app_test)
    assert "Unable to Determine" in text
    assert "Incident Summary" in text
    assert "No record generated for this result." in text
    assert "secret-value" not in text
