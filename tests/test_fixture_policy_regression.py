from src.contracts import CompletenessStatus, ProcessingStatus
from src.evaluation.corpus import load_corpus
from src.fixtures import SYNTHETIC_INCIDENTS


def test_all_eight_demonstration_fixtures_have_explicit_true_north_authority():
    expectations = load_corpus().fixture_expectations
    fixture_ids = [item["incident"].incident_id for item in SYNTHETIC_INCIDENTS]
    assert [item.fixture_id for item in expectations] == fixture_ids
    for expected in expectations:
        assert expected.expected_conduct
        assert expected.expected_direction
        assert expected.expected_uncertainty is not None
        assert expected.expected_processing_status == ProcessingStatus.SUCCESSFUL_ANALYSIS
        assert expected.expected_completeness_status in {
            CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS,
            CompletenessStatus.UNRESOLVED_SEMANTIC_CONTENT,
        }


def test_fixture_expectations_cover_detection_negative_and_directional_behavior():
    values = {item.fixture_id: item for item in load_corpus().fixture_expectations}
    assert values["CASE_001"].expected_outcome.value == "Violence Detected"
    assert values["CASE_003"].expected_outcome.value == "No Violence Detected"
    assert values["CASE_004"].expected_outcome.value == "No Violence Detected"
    assert values["CASE_006"].expected_conduct[0].value == "property_violence"
    assert values["CASE_006"].expected_direction.value == "object_directed"
    assert values["CASE_007"].expected_direction.value == "object_directed"
    assert values["CASE_008"].expected_conduct[0].value == "physical_attempt"
