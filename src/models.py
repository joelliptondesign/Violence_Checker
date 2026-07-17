from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictStr, field_validator, model_validator


class ViolenceEventType(str, Enum):
    NONE = "none"
    VERBAL_THREAT = "verbal_threat"
    ATTEMPTED_PHYSICAL_VIOLENCE = "attempted_physical_violence"
    COMPLETED_PHYSICAL_VIOLENCE = "completed_physical_violence"
    UNCLEAR = "unclear"


class Intentionality(str, Enum):
    INTENTIONAL = "intentional"
    ACCIDENTAL = "accidental"
    UNCLEAR = "unclear"


class Incident(BaseModel):
    model_config = ConfigDict(strict=True)

    incident_id: StrictStr
    narrative: StrictStr

    @field_validator("incident_id", "narrative")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("value must be non-empty")
        return value


class ViolenceFinding(BaseModel):
    model_config = ConfigDict(strict=True)

    violence_present: StrictBool
    event_type: ViolenceEventType
    actor: Optional[StrictStr]
    target: Optional[StrictStr]
    contact_occurred: StrictBool
    injury_mentioned: StrictBool
    current_event: StrictBool
    intentionality: Intentionality
    negated: StrictBool
    correction_present: StrictBool
    conflicting_information: StrictBool
    evidence_text: List[StrictStr]
    confidence: StrictFloat = Field(ge=0.0, le=1.0)
    uncertainty_notes: List[StrictStr]

    @model_validator(mode="after")
    def prevent_internal_inconsistency(self) -> "ViolenceFinding":
        if self.violence_present and self.event_type == ViolenceEventType.NONE:
            raise ValueError("violence_present cannot use event_type none")

        if (
            not self.violence_present
            and self.event_type
            in (
                ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
                ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
            )
        ):
            raise ValueError("attempted or completed physical violence requires violence_present true")

        if (
            not self.violence_present
            and self.contact_occurred
            and self.intentionality != Intentionality.ACCIDENTAL
        ):
            raise ValueError("no-violence findings cannot claim non-accidental physical contact")

        if self.event_type == ViolenceEventType.NONE and self.contact_occurred:
            raise ValueError("event_type none cannot claim completed physical contact")

        return self
