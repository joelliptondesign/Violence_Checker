import re
import unicodedata

from src.contracts import NormalizationOperation, NormalizedIncident
from src.models import Incident


_EXCESSIVE_BLANK_LINES = re.compile(r"\n(?:[ \t]*\n){2,}")
_HORIZONTAL_WHITESPACE = re.compile(r"[ \t]+")


def normalize_incident(incident: Incident) -> NormalizedIncident:
    """Create a deterministic inference copy while retaining the raw narrative."""
    normalized = incident.narrative
    operations: list[NormalizationOperation] = []

    if normalized.startswith("\ufeff"):
        normalized = normalized.removeprefix("\ufeff")
        operations.append(NormalizationOperation.REMOVE_LEADING_BOM)

    transformed = unicodedata.normalize("NFC", normalized)
    if transformed != normalized:
        normalized = transformed
        operations.append(NormalizationOperation.UNICODE_NFC)

    transformed = normalized.replace("\r\n", "\n").replace("\r", "\n")
    if transformed != normalized:
        normalized = transformed
        operations.append(NormalizationOperation.LINE_ENDINGS_LF)

    transformed = normalized.replace("\u00a0", " ")
    if transformed != normalized:
        normalized = transformed
        operations.append(NormalizationOperation.NON_BREAKING_SPACES)

    transformed = _HORIZONTAL_WHITESPACE.sub(" ", normalized)
    if transformed != normalized:
        normalized = transformed
        operations.append(NormalizationOperation.HORIZONTAL_WHITESPACE)

    transformed = _EXCESSIVE_BLANK_LINES.sub("\n\n", normalized)
    if transformed != normalized:
        normalized = transformed
        operations.append(NormalizationOperation.EXCESSIVE_BLANK_LINES)

    transformed = normalized.strip(" \t\n")
    if transformed != normalized:
        normalized = transformed
        operations.append(NormalizationOperation.TRIM_BOUNDARY_WHITESPACE)

    return NormalizedIncident(
        incident_id=incident.incident_id,
        original_narrative=incident.narrative,
        normalized_narrative=normalized,
        normalization_applied=bool(operations),
        normalization_operations=operations,
    )
