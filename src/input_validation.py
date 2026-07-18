from typing import List

from src.contracts import (
    InputFailureCode,
    InputValidationIssue,
    InputValidationResult,
    InputValidationStatus,
)
from src.models import Incident


MAX_NARRATIVE_CHARACTERS = 20_000
SUPPORTED_ENVELOPE_FIELDS = frozenset({"incident_id", "narrative"})
_MISSING = object()

_MESSAGES = {
    InputFailureCode.INVALID_ENVELOPE_TYPE: "Incident input must be an Incident or a supported incident envelope.",
    InputFailureCode.UNSUPPORTED_FIELD: "Incident input contains an unsupported field.",
    InputFailureCode.MISSING_INCIDENT_ID: "Incident identifier is required.",
    InputFailureCode.INVALID_INCIDENT_ID_TYPE: "Incident identifier must be a string.",
    InputFailureCode.EMPTY_INCIDENT_ID: "Incident identifier must not be empty or whitespace-only.",
    InputFailureCode.MISSING_NARRATIVE: "Incident narrative is required.",
    InputFailureCode.INVALID_NARRATIVE_TYPE: "Incident narrative must be a string.",
    InputFailureCode.EMPTY_NARRATIVE: "Incident narrative must not be empty.",
    InputFailureCode.WHITESPACE_ONLY_NARRATIVE: "Incident narrative must contain a non-whitespace character.",
    InputFailureCode.NO_SUBSTANTIVE_CONTENT: "Incident narrative must contain substantive text.",
    InputFailureCode.NULL_CHARACTER: "Incident narrative contains a disallowed null character.",
    InputFailureCode.SURROGATE_CODE_POINT: "Incident narrative contains a disallowed Unicode surrogate.",
    InputFailureCode.NARRATIVE_TOO_LONG: (
        f"Incident narrative must not exceed {MAX_NARRATIVE_CHARACTERS} characters for this local demonstration."
    ),
}


def _issue(code: InputFailureCode, field: str) -> InputValidationIssue:
    return InputValidationIssue(code=code, field=field, message=_MESSAGES[code])


def _failure(issues: List[InputValidationIssue]) -> InputValidationResult:
    return InputValidationResult(status=InputValidationStatus.FAILURE, issues=issues)


def _adapt_envelope(candidate: object) -> tuple[object, object, List[InputValidationIssue]]:
    if isinstance(candidate, Incident):
        return candidate.incident_id, candidate.narrative, []

    if not isinstance(candidate, dict):
        return None, None, [_issue(InputFailureCode.INVALID_ENVELOPE_TYPE, "envelope")]

    issues: List[InputValidationIssue] = []
    unsupported = sorted(
        (field for field in candidate if field not in SUPPORTED_ENVELOPE_FIELDS),
        key=str,
    )
    issues.extend(_issue(InputFailureCode.UNSUPPORTED_FIELD, str(field)) for field in unsupported)

    incident_id = candidate.get("incident_id", _MISSING)
    narrative = candidate.get("narrative", _MISSING)
    if "incident_id" not in candidate:
        issues.append(_issue(InputFailureCode.MISSING_INCIDENT_ID, "incident_id"))
    if "narrative" not in candidate:
        issues.append(_issue(InputFailureCode.MISSING_NARRATIVE, "narrative"))
    return incident_id, narrative, issues


def validate_incident(candidate: object) -> InputValidationResult:
    """Validate an incident candidate without semantic or domain interpretation."""
    incident_id, narrative, issues = _adapt_envelope(candidate)
    if issues and not isinstance(candidate, dict):
        return _failure(issues)

    if incident_id is not _MISSING and not isinstance(incident_id, str):
        issues.append(_issue(InputFailureCode.INVALID_INCIDENT_ID_TYPE, "incident_id"))
    elif isinstance(incident_id, str) and not incident_id.strip():
        issues.append(_issue(InputFailureCode.EMPTY_INCIDENT_ID, "incident_id"))

    if narrative is not _MISSING and not isinstance(narrative, str):
        issues.append(_issue(InputFailureCode.INVALID_NARRATIVE_TYPE, "narrative"))
    elif isinstance(narrative, str):
        if narrative == "":
            issues.append(_issue(InputFailureCode.EMPTY_NARRATIVE, "narrative"))
        elif not any(not character.isspace() for character in narrative):
            issues.append(_issue(InputFailureCode.WHITESPACE_ONLY_NARRATIVE, "narrative"))
        elif not any(not character.isspace() for character in narrative.removeprefix("\ufeff")):
            issues.append(_issue(InputFailureCode.NO_SUBSTANTIVE_CONTENT, "narrative"))

        if "\x00" in narrative:
            issues.append(_issue(InputFailureCode.NULL_CHARACTER, "narrative"))
        if any(0xD800 <= ord(character) <= 0xDFFF for character in narrative):
            issues.append(_issue(InputFailureCode.SURROGATE_CODE_POINT, "narrative"))
        if len(narrative) > MAX_NARRATIVE_CHARACTERS:
            issues.append(_issue(InputFailureCode.NARRATIVE_TOO_LONG, "narrative"))

    if issues:
        return _failure(issues)

    return InputValidationResult(
        status=InputValidationStatus.SUCCESS,
        incident=Incident(incident_id=incident_id, narrative=narrative),
    )
