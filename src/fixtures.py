from src.models import Incident


SYNTHETIC_INCIDENTS = [
    {
        "incident": Incident(
            incident_id="CASE_001",
            narrative="pt was getting upset about not being able to leave. rn tried to redirect him back to room and he hit her on left side of face with closed fist. security came up. rn has red area on cheek no loc",
        ),
        "metadata": {"scenario_type": "completed assault"},
    },
    {
        "incident": Incident(
            incident_id="CASE_002",
            narrative="pt yelling about wait time at front desk. said if someone doesnt see me im gonna punch somebody. did not hit anyone. security was standing by",
        ),
        "metadata": {"scenario_type": "verbal threat"},
    },
    {
        "incident": Incident(
            incident_id="CASE_003",
            narrative="during admit questions pt said ex boyfriend assaulted her a few yrs ago. nothing happened today. pt calm and cooperative no threats or aggressive behavior",
        ),
        "metadata": {"scenario_type": "historical disclosure"},
    },
    {
        "incident": Incident(
            incident_id="CASE_004",
            narrative="pt lost balance getting off commode and grabbed rn arm. both went into wall. rn wrist sore. pt was not combative this looked accidental",
        ),
        "metadata": {"scenario_type": "accidental contact"},
    },
    {
        "incident": Incident(
            incident_id="CASE_005",
            narrative="first report said pt punched tech. tech later said he didnt punch her. pt pulled arm away during blood draw and elbow hit her arm. she says it may have been accidental",
        ),
        "metadata": {"scenario_type": "conflicting correction"},
    },
    {
        "incident": Incident(
            incident_id="CASE_006",
            narrative="pt mad about dc yelling thru cup at wall then came toward rn saying u better watch yourself. did not hit rn. secuirty came up and pt calmed after few mins",
        ),
        "metadata": {"scenario_type": "ambiguous intimidation"},
    },
    {
        "incident": Incident(
            incident_id="CASE_007",
            narrative="pt kicked nurse during med pass. correction pt did not kick nurse, kicked side rail and nurse was standing next to bed. no contact with nurse",
        ),
        "metadata": {"scenario_type": "corrected non-contact"},
    },
    {
        "incident": Incident(
            incident_id="CASE_008",
            narrative="pt swung at rn missed. security called",
        ),
        "metadata": {"scenario_type": "attempted strike"},
    },
]
