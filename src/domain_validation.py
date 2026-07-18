"""Deterministic violence-domain consistency validation for schema-valid facts."""

from src.contracts import (
    DomainValidationResult,
    DomainValidationStatus,
    SemanticFacts,
    ValidationIssue,
    ValidationIssueCode,
)
from src.models import Intentionality, ViolenceEventType


def _issue(code: ValidationIssueCode, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def validate_semantic_domain(facts: SemanticFacts) -> DomainValidationResult:
    """Evaluate encoded field relationships without inference, repair, or defaults."""
    if not isinstance(facts, SemanticFacts):
        raise TypeError("domain validation requires schema-valid SemanticFacts")

    issues: list[ValidationIssue] = []

    if facts.violence_present and facts.event_type == ViolenceEventType.NONE:
        issues.append(
            _issue(
                ValidationIssueCode.VIOLENCE_WITH_EVENT_TYPE_NONE,
                "event_type",
                "event_type none cannot coexist with violence_present true.",
            )
        )
    if (
        not facts.violence_present
        and facts.event_type
        in {
            ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
            ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
        }
    ):
        issues.append(
            _issue(
                ValidationIssueCode.PHYSICAL_EVENT_WITHOUT_VIOLENCE,
                "violence_present",
                "Attempted or completed physical violence requires violence_present true.",
            )
        )
    if (
        facts.event_type == ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE
        and not facts.contact_occurred
    ):
        issues.append(
            _issue(
                ValidationIssueCode.COMPLETED_VIOLENCE_WITHOUT_CONTACT,
                "contact_occurred",
                "Completed physical violence requires contact_occurred true.",
            )
        )
    if facts.event_type == ViolenceEventType.NONE and facts.contact_occurred:
        issues.append(
            _issue(
                ValidationIssueCode.EVENT_TYPE_NONE_WITH_CONTACT,
                "contact_occurred",
                "event_type none cannot coexist with contact_occurred true.",
            )
        )
    if (
        not facts.violence_present
        and facts.contact_occurred
        and facts.intentionality != Intentionality.ACCIDENTAL
    ):
        issues.append(
            _issue(
                ValidationIssueCode.NONVIOLENT_NONACCIDENTAL_CONTACT,
                "intentionality",
                "Non-violent contact must be represented as accidental.",
            )
        )
    if (
        facts.negated
        and facts.violence_present
        and facts.current_event
        and not facts.correction_present
        and not facts.conflicting_information
    ):
        issues.append(
            _issue(
                ValidationIssueCode.NEGATED_CURRENT_AFFIRMATIVE_VIOLENCE,
                "negated",
                "Negated current violence cannot be an unqualified affirmative violence finding.",
            )
        )
    if (
        facts.conflicting_information
        and facts.event_type != ViolenceEventType.UNCLEAR
        and not facts.uncertainty_notes
    ):
        issues.append(
            _issue(
                ValidationIssueCode.CONFLICT_WITHOUT_UNCERTAINTY,
                "conflicting_information",
                "Conflicting information requires an unclear event type or uncertainty notes.",
            )
        )
    for index, evidence in enumerate(facts.evidence_text):
        if not evidence.strip():
            issues.append(
                _issue(
                    ValidationIssueCode.EMPTY_EVIDENCE_ITEM,
                    f"evidence_text.{index}",
                    "Evidence entries must be non-empty strings.",
                )
            )

    if issues:
        return DomainValidationResult(status=DomainValidationStatus.FAILED, issues=issues)
    return DomainValidationResult(status=DomainValidationStatus.PASSED)
