from src.fixtures import SYNTHETIC_INCIDENTS


AUTHORIZED_NARRATIVES = {
    "CASE_001": "pt was getting upset about not being able to leave. rn tried to redirect him back to room and he hit her on left side of face with closed fist. security came up. rn has red area on cheek no loc",
    "CASE_002": "pt yelling about wait time at front desk. said if someone doesnt see me im gonna punch somebody. did not hit anyone. security was standing by",
    "CASE_003": "during admit questions pt said ex boyfriend assaulted her a few yrs ago. nothing happened today. pt calm and cooperative no threats or aggressive behavior",
    "CASE_004": "pt lost balance getting off commode and grabbed rn arm. both went into wall. rn wrist sore. pt was not combative this looked accidental",
    "CASE_005": "first report said pt punched tech. tech later said he didnt punch her. pt pulled arm away during blood draw and elbow hit her arm. she says it may have been accidental",
    "CASE_006": "pt mad about dc yelling thru cup at wall then came toward rn saying u better watch yourself. did not hit rn. secuirty came up and pt calmed after few mins",
    "CASE_007": "pt kicked nurse during med pass. correction pt did not kick nurse, kicked side rail and nurse was standing next to bed. no contact with nurse",
    "CASE_008": "pt swung at rn missed. security called",
}


def test_exactly_eight_fixtures_load():
    assert len(SYNTHETIC_INCIDENTS) == 8


def test_stable_identifiers_are_unique():
    identifiers = [item["incident"].incident_id for item in SYNTHETIC_INCIDENTS]

    assert identifiers == sorted(AUTHORIZED_NARRATIVES)
    assert len(set(identifiers)) == 8


def test_narratives_exactly_match_authorized_source_text():
    for item in SYNTHETIC_INCIDENTS:
        incident = item["incident"]
        assert incident.narrative == AUTHORIZED_NARRATIVES[incident.incident_id]
