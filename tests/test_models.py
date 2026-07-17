import pytest
from pydantic import ValidationError

from src.models import Incident, Intentionality, ViolenceEventType, ViolenceFinding


def valid_finding(**overrides):
    data = {
        "violence_present": True,
        "event_type": ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
        "actor": "patient",
        "target": "nurse",
        "contact_occurred": True,
        "injury_mentioned": True,
        "current_event": True,
        "intentionality": Intentionality.INTENTIONAL,
        "negated": False,
        "correction_present": False,
        "conflicting_information": False,
        "evidence_text": ["he hit her on left side of face"],
        "confidence": 0.9,
        "uncertainty_notes": [],
    }
    data.update(overrides)
    return ViolenceFinding(**data)


def test_valid_incident_accepted():
    incident = Incident(incident_id="CASE_X", narrative="exact narrative")

    assert incident.incident_id == "CASE_X"


def test_empty_incident_id_rejected():
    with pytest.raises(ValidationError):
        Incident(incident_id="", narrative="narrative")


def test_empty_narrative_rejected():
    with pytest.raises(ValidationError):
        Incident(incident_id="CASE_X", narrative="")


def test_narrative_preserved_exactly():
    text = "  pt hit rn. no normalization here  "

    incident = Incident(incident_id="CASE_X", narrative=text)

    assert incident.narrative == text


def test_valid_finding_accepted():
    finding = valid_finding()

    assert finding.event_type == ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE


def test_invalid_confidence_rejected():
    with pytest.raises(ValidationError):
        valid_finding(confidence=1.5)


def test_invalid_enum_rejected():
    with pytest.raises(ValidationError):
        valid_finding(event_type="physical")


def test_malformed_finding_rejected():
    with pytest.raises(ValidationError):
        ViolenceFinding(violence_present=True)


def test_internally_inconsistent_no_violence_finding_rejected():
    with pytest.raises(ValidationError):
        valid_finding(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            contact_occurred=True,
            injury_mentioned=False,
            intentionality=Intentionality.UNCLEAR,
            confidence=0.5,
        )


def test_accidental_contact_without_violence_is_accepted():
    finding = valid_finding(
        violence_present=False,
        event_type=ViolenceEventType.UNCLEAR,
        contact_occurred=True,
        intentionality=Intentionality.ACCIDENTAL,
        injury_mentioned=True,
        evidence_text=["this looked accidental"],
        confidence=0.8,
    )

    assert finding.contact_occurred is True
    assert finding.intentionality == Intentionality.ACCIDENTAL


def test_explicit_correction_can_result_in_no_person_directed_violence():
    finding = valid_finding(
        violence_present=False,
        event_type=ViolenceEventType.NONE,
        contact_occurred=False,
        injury_mentioned=False,
        intentionality=Intentionality.UNCLEAR,
        negated=True,
        correction_present=True,
        conflicting_information=True,
        evidence_text=["correction pt did not kick nurse", "no contact with nurse"],
        confidence=0.75,
    )

    assert finding.violence_present is False
    assert finding.correction_present is True


def test_object_directed_kicking_can_be_unclear_without_person_contact():
    finding = valid_finding(
        violence_present=False,
        event_type=ViolenceEventType.UNCLEAR,
        contact_occurred=False,
        injury_mentioned=False,
        intentionality=Intentionality.UNCLEAR,
        correction_present=True,
        evidence_text=["kicked side rail"],
        confidence=0.7,
    )

    assert finding.event_type == ViolenceEventType.UNCLEAR
    assert finding.contact_occurred is False


def test_corrected_object_directed_kicking_with_no_person_contact_is_valid():
    finding = valid_finding(
        violence_present=False,
        event_type=ViolenceEventType.UNCLEAR,
        actor="patient",
        target=None,
        contact_occurred=False,
        injury_mentioned=False,
        intentionality=Intentionality.UNCLEAR,
        negated=True,
        correction_present=True,
        conflicting_information=True,
        evidence_text=["did not kick nurse", "kicked side rail", "no contact with nurse"],
        confidence=0.7,
    )

    assert finding.contact_occurred is False
    assert finding.violence_present is False


def test_no_violence_corrected_finding_can_use_event_type_unclear():
    finding = valid_finding(
        violence_present=False,
        event_type=ViolenceEventType.UNCLEAR,
        contact_occurred=False,
        injury_mentioned=False,
        intentionality=Intentionality.UNCLEAR,
        negated=True,
        correction_present=True,
        conflicting_information=True,
        evidence_text=["correction said no contact"],
        confidence=0.65,
    )

    assert finding.event_type == ViolenceEventType.UNCLEAR


def test_completed_physical_violence_requires_violence_present_true():
    with pytest.raises(ValidationError):
        valid_finding(
            violence_present=False,
            event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
            contact_occurred=False,
            injury_mentioned=False,
            evidence_text=["completed violence"],
            confidence=0.7,
        )


def test_attempted_physical_violence_requires_violence_present_true():
    with pytest.raises(ValidationError):
        valid_finding(
            violence_present=False,
            event_type=ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
            contact_occurred=False,
            injury_mentioned=False,
            evidence_text=["attempted violence"],
            confidence=0.7,
        )


def test_current_threat_can_be_represented_as_current_without_contact():
    finding = valid_finding(
        event_type=ViolenceEventType.VERBAL_THREAT,
        contact_occurred=False,
        injury_mentioned=False,
        current_event=True,
        evidence_text=["u better watch yourself"],
        confidence=0.85,
    )

    assert finding.current_event is True
    assert finding.event_type == ViolenceEventType.VERBAL_THREAT


def test_historical_assault_can_remain_violence_present_with_current_event_false():
    finding = valid_finding(
        violence_present=True,
        event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
        contact_occurred=True,
        current_event=False,
        evidence_text=["assaulted her a few yrs ago"],
        confidence=0.8,
    )

    assert finding.violence_present is True
    assert finding.current_event is False
