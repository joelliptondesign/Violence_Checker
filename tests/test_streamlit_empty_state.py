import sys

from src.fixtures import SYNTHETIC_INCIDENTS


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


def test_empty_initial_state_has_no_active_incident_or_analysis_output():
    app_test = fresh_app_test()

    assert header_values(app_test) == ["Incident Narrative"]
    assert len(app_test.selectbox) == 0
    assert len(app_test.button) == 0
    assert len(app_test.text_area) == 0
    assert_no_analysis_output(app_test)


def test_fixture_selection_alone_shows_narrative_without_analysis_output():
    app_test = fresh_app_test()

    app_test.radio[0].set_value("Synthetic fixture").run()
    app_test.selectbox[0].set_value(SYNTHETIC_INCIDENTS[-1]).run()

    assert [button.label for button in app_test.button] == ["Run Analysis"]
    assert app_test.text_area[0].label == "Original narrative used for analysis"
    assert app_test.text_area[0].value == "pt swung at rn missed. security called"
    assert_no_analysis_output(app_test)


def test_manual_typing_alone_shows_narrative_without_analysis_output():
    app_test = fresh_app_test()

    app_test.radio[0].set_value("Manual narrative").run()
    app_test.text_area[0].set_value("pt swung at rn missed").run()

    assert [button.label for button in app_test.button] == ["Run Analysis"]
    assert app_test.text_area[1].label == "Original narrative used for analysis"
    assert app_test.text_area[1].value == "pt swung at rn missed"
    assert_no_analysis_output(app_test)
