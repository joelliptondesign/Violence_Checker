from pydantic import BaseModel, ConfigDict, StrictStr, field_validator


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
