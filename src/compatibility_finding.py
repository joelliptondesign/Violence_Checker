"""Deterministic transitional construction of downstream ViolenceFinding objects.

This module performs exact field mapping only after independent schema and domain
validation. Policy evaluation remains outside the active application flow.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pydantic import ValidationError

from src.contracts import ValidatedSemanticFacts
from src.models import ViolenceFinding


class CompatibilityFindingStatus(str, Enum):
    SUCCESS = "success"
    VALIDATION_FAILURE = "validation_failure"


@dataclass(frozen=True)
class CompatibilityFindingResult:
    status: CompatibilityFindingStatus
    finding: Optional[ViolenceFinding] = None
    failure_message: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.status == CompatibilityFindingStatus.SUCCESS


def construct_compatibility_finding(validated: ValidatedSemanticFacts) -> CompatibilityFindingResult:
    """Map already-admissible facts exactly into the downstream representation."""
    if not isinstance(validated, ValidatedSemanticFacts):
        return CompatibilityFindingResult(
            status=CompatibilityFindingStatus.VALIDATION_FAILURE,
            failure_message="TypeError",
        )
    facts = validated.facts
    try:
        finding = ViolenceFinding(
            violence_present=facts.violence_present,
            event_type=facts.event_type,
            actor=facts.actor,
            target=facts.target,
            contact_occurred=facts.contact_occurred,
            injury_mentioned=facts.injury_mentioned,
            current_event=facts.current_event,
            intentionality=facts.intentionality,
            negated=facts.negated,
            correction_present=facts.correction_present,
            conflicting_information=facts.conflicting_information,
            evidence_text=list(facts.evidence_text),
            confidence=facts.confidence,
            uncertainty_notes=list(facts.uncertainty_notes),
        )
    except ValidationError as exc:
        return CompatibilityFindingResult(
            status=CompatibilityFindingStatus.VALIDATION_FAILURE,
            failure_message=exc.__class__.__name__,
        )

    return CompatibilityFindingResult(
        status=CompatibilityFindingStatus.SUCCESS,
        finding=finding,
    )
