from src.contracts import (
    AssertionStatus, CompletenessStatus, Conduct, FactDirection, Intentionality,
    PolicyOutcome, ProcessingStatus, ProviderFactCandidate,
    ProviderFactEvidenceCandidate, ProviderMaterialAttribute, ProviderStructuredResponse,
    TemporalScope,
)
from src.evaluation.corpus import load_corpus
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Incident
from src.policy import evaluate_policy
from src.provider_adapter import semantic_candidate_from_provider_response
from src.semantic_validation import validate_semantic_candidate


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


def test_case_001_closed_fist_assault_returns_detected_not_uncertain():
    incident = next(item["incident"] for item in SYNTHETIC_INCIDENTS if item["incident"].incident_id == "CASE_001")
    evidence = "rn tried to redirect him back to room and he hit her on left side of face with closed fist."
    candidate = semantic_candidate_from_provider_response(
        ProviderStructuredResponse(facts=[
            ProviderFactCandidate(
                local_ref="case-001-assault",
                conduct=Conduct.PHYSICAL_CONTACT,
                direction=FactDirection.INTERPERSONAL,
                intentionality=Intentionality.INTENTIONAL,
                temporal_scope=TemporalScope.CURRENT,
                assertion_status=AssertionStatus.AFFIRMED,
                evidence=[ProviderFactEvidenceCandidate(
                    excerpt=evidence,
                    supports=[
                        ProviderMaterialAttribute.CONDUCT,
                        ProviderMaterialAttribute.DIRECTION,
                        ProviderMaterialAttribute.INTENTIONALITY,
                        ProviderMaterialAttribute.TEMPORAL_SCOPE,
                        ProviderMaterialAttribute.ASSERTION_STATUS,
                    ],
                )],
                uncertainty=[],
            ),
        ]),
        incident=Incident(incident_id=incident.incident_id, narrative=incident.narrative),
    )
    validation = validate_semantic_candidate(
        candidate,
        incident_id=incident.incident_id,
        normalized_narrative=incident.narrative,
    )
    decision = evaluate_policy(
        validated=validation.validated_envelope,
        processing_status=validation.processing_status,
        completeness_status=validation.completeness_status,
        derived=validation.derived_semantics,
    )
    assert validation.passed
    assert validation.completeness_status == CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS
    assert decision.outcome == PolicyOutcome.VIOLENCE_DETECTED
