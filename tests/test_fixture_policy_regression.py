from unittest.mock import Mock

from src.app_logic import AnalysisResult, run_analysis
from src.contracts import PolicyOutcome, PolicyReasonCode, SemanticFacts
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Intentionality, ViolenceEventType
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


FIXTURE_FACTS = {
    "CASE_001": dict(violence_present=True, event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE, actor="pt", target="rn", contact_occurred=True, injury_mentioned=True, current_event=True, intentionality=Intentionality.INTENTIONAL, negated=False, correction_present=False, conflicting_information=False, evidence_text=["he hit her on left side of face with closed fist", "rn has red area on cheek"], confidence=0.9, uncertainty_notes=["The secondary shorthand no loc is ambiguous.", "Actor and target abbreviations pt and rn are preserved."]),
    "CASE_002": dict(violence_present=True, event_type=ViolenceEventType.VERBAL_THREAT, actor="pt", target="somebody", contact_occurred=False, injury_mentioned=False, current_event=True, intentionality=Intentionality.INTENTIONAL, negated=False, correction_present=False, conflicting_information=False, evidence_text=["im gonna punch somebody"], confidence=0.9, uncertainty_notes=[]),
    "CASE_003": dict(violence_present=False, event_type=ViolenceEventType.NONE, actor=None, target=None, contact_occurred=False, injury_mentioned=False, current_event=False, intentionality=Intentionality.UNCLEAR, negated=False, correction_present=False, conflicting_information=False, evidence_text=["nothing happened today"], confidence=0.9, uncertainty_notes=[]),
    "CASE_004": dict(violence_present=False, event_type=ViolenceEventType.UNCLEAR, actor="pt", target="rn", contact_occurred=True, injury_mentioned=True, current_event=True, intentionality=Intentionality.ACCIDENTAL, negated=False, correction_present=False, conflicting_information=False, evidence_text=["pt lost balance", "this looked accidental"], confidence=0.8, uncertainty_notes=[]),
    "CASE_005": dict(violence_present=False, event_type=ViolenceEventType.UNCLEAR, actor="pt", target="tech", contact_occurred=True, injury_mentioned=False, current_event=True, intentionality=Intentionality.ACCIDENTAL, negated=False, correction_present=True, conflicting_information=True, evidence_text=["tech later said he didnt punch her", "elbow hit her arm"], confidence=0.7, uncertainty_notes=["The reports conflict."]),
    "CASE_006": dict(violence_present=True, event_type=ViolenceEventType.UNCLEAR, actor="pt", target="rn", contact_occurred=False, injury_mentioned=False, current_event=True, intentionality=Intentionality.UNCLEAR, negated=False, correction_present=False, conflicting_information=False, evidence_text=["u better watch yourself"], confidence=0.6, uncertainty_notes=["The statement's event type is unclear."]),
    "CASE_007": dict(violence_present=False, event_type=ViolenceEventType.NONE, actor="pt", target="nurse", contact_occurred=False, injury_mentioned=False, current_event=True, intentionality=Intentionality.UNCLEAR, negated=True, correction_present=True, conflicting_information=False, evidence_text=["correction pt did not kick nurse"], confidence=0.95, uncertainty_notes=[]),
    "CASE_008": dict(violence_present=True, event_type=ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE, actor="pt", target="rn", contact_occurred=False, injury_mentioned=False, current_event=True, intentionality=Intentionality.INTENTIONAL, negated=False, correction_present=False, conflicting_information=False, evidence_text=["pt swung at rn missed"], confidence=0.9, uncertainty_notes=[]),
}

EXPECTED = {
    "CASE_001": ("completed assault", PolicyOutcome.WRITE_DETECTED, [PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT]),
    "CASE_002": ("verbal threat", PolicyOutcome.WRITE_DETECTED, [PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT]),
    "CASE_003": ("historical disclosure", PolicyOutcome.WRITE_NOT_DETECTED, [PolicyReasonCode.NO_VIOLENCE]),
    "CASE_004": ("accidental contact", PolicyOutcome.WRITE_UNCERTAIN, [PolicyReasonCode.UNCLEAR_EVENT_TYPE]),
    "CASE_005": ("conflicting correction", PolicyOutcome.WRITE_UNCERTAIN, [PolicyReasonCode.CONFLICTING_INFORMATION, PolicyReasonCode.UNCLEAR_EVENT_TYPE]),
    "CASE_006": ("ambiguous intimidation", PolicyOutcome.WRITE_UNCERTAIN, [PolicyReasonCode.UNCLEAR_EVENT_TYPE, PolicyReasonCode.UNCLEAR_MATERIAL_INTENTIONALITY]),
    "CASE_007": ("corrected non-contact", PolicyOutcome.WRITE_NOT_DETECTED, [PolicyReasonCode.NO_VIOLENCE, PolicyReasonCode.NEGATED_NON_EVENT, PolicyReasonCode.CORRECTED_NON_EVENT]),
    "CASE_008": ("attempted strike", PolicyOutcome.WRITE_DETECTED, [PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT]),
}


def test_all_approved_fixtures_have_deterministic_policy_regression(monkeypatch):
    provider = Mock(side_effect=AssertionError("fixture regression must not call a provider"))
    monkeypatch.setattr("openai.OpenAI", provider)
    calls = []

    for fixture in SYNTHETIC_INCIDENTS:
        incident = fixture["incident"]

        def extractor(inference_incident, *, case_id=incident.incident_id):
            calls.append((inference_incident.incident_id, inference_incident.narrative))
            return SemanticExtractionResult(
                status=SemanticExtractionStatus.SUCCESS,
                semantic_candidate=SemanticFacts(**FIXTURE_FACTS[case_id]),
            )

        result = run_analysis(incident, extractor=extractor)
        assert isinstance(result, AnalysisResult)
        category, outcome, reasons = EXPECTED[incident.incident_id]
        assert fixture["metadata"]["scenario_type"] == category
        assert result.validation_result.passed
        assert result.policy_decision.outcome == outcome
        assert result.policy_decision.reason_codes == reasons
        assert result.salesforce_preview is not None
        assert result.salesforce_preview["Illustrative_Write_Disposition__c"] == outcome.value

    assert [case_id for case_id, _ in calls] == list(EXPECTED)
    assert [narrative for _, narrative in calls] == [
        fixture["incident"].narrative for fixture in SYNTHETIC_INCIDENTS
    ]
    provider.assert_not_called()


def test_fixture_001_completed_assault_is_detected_with_incidental_notes():
    fixture = SYNTHETIC_INCIDENTS[0]
    result = run_analysis(
        fixture["incident"],
        extractor=lambda _incident: SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=SemanticFacts(**FIXTURE_FACTS["CASE_001"]),
        ),
    )

    assert isinstance(result, AnalysisResult)
    facts = result.validation_result.validated_facts.facts
    assert facts.violence_present is True
    assert facts.event_type == ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE
    assert facts.contact_occurred is True
    assert facts.injury_mentioned is True
    assert facts.conflicting_information is False
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_DETECTED
    assert result.salesforce_preview is not None
