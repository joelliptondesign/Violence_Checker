"""Deterministic structural validation for provider-independent semantic candidates."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from src.contracts import (
    ProviderStructuredResponse,
    SchemaValidationResult,
    SchemaValidationStatus,
    SemanticFacts,
    ValidationIssue,
    ValidationIssueCode,
)


_BOOLEAN_FIELDS = {
    "violence_present",
    "contact_occurred",
    "injury_mentioned",
    "current_event",
    "negated",
    "correction_present",
    "conflicting_information",
}


def _issue(code: ValidationIssueCode, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def _pydantic_issue(error: dict[str, Any]) -> ValidationIssue:
    location = error.get("loc", ())
    field = str(location[0]) if location else "candidate"
    error_type = str(error.get("type", ""))

    if field == "event_type":
        return _issue(ValidationIssueCode.INVALID_EVENT_TYPE, field, "event_type must be a supported value.")
    if field == "intentionality":
        return _issue(
            ValidationIssueCode.INVALID_INTENTIONALITY,
            field,
            "intentionality must be a supported value.",
        )
    if field in _BOOLEAN_FIELDS:
        return _issue(ValidationIssueCode.INVALID_BOOLEAN, field, f"{field} must be a boolean.")
    if field == "actor":
        return _issue(ValidationIssueCode.INVALID_ACTOR, field, "actor must be a string or null.")
    if field == "target":
        return _issue(ValidationIssueCode.INVALID_TARGET, field, "target must be a string or null.")
    if field == "evidence_text":
        if len(location) > 1:
            return _issue(
                ValidationIssueCode.INVALID_EVIDENCE_ITEM,
                f"evidence_text.{location[1]}",
                "Each evidence_text item must be a string.",
            )
        return _issue(
            ValidationIssueCode.INVALID_EVIDENCE_COLLECTION,
            field,
            "evidence_text must be a list of strings.",
        )
    if field == "confidence":
        if error_type in {"greater_than_equal", "less_than_equal"}:
            return _issue(
                ValidationIssueCode.CONFIDENCE_OUT_OF_RANGE,
                field,
                "confidence must be between 0 and 1.",
            )
        return _issue(
            ValidationIssueCode.INVALID_CONFIDENCE_TYPE,
            field,
            "confidence must be a floating-point number.",
        )
    if field == "uncertainty_notes":
        if len(location) > 1:
            return _issue(
                ValidationIssueCode.INVALID_UNCERTAINTY_ITEM,
                f"uncertainty_notes.{location[1]}",
                "Each uncertainty_notes item must be a string.",
            )
        return _issue(
            ValidationIssueCode.INVALID_UNCERTAINTY_COLLECTION,
            field,
            "uncertainty_notes must be a list of strings.",
        )
    return _issue(ValidationIssueCode.INVALID_CANDIDATE_TYPE, field, "Semantic candidate is malformed.")


def validate_semantic_schema(candidate: object) -> SchemaValidationResult:
    """Validate structure only; no relationships between semantic fields are evaluated."""
    if isinstance(candidate, ProviderStructuredResponse):
        return SchemaValidationResult(
            status=SchemaValidationStatus.FAILED,
            issues=[
                _issue(
                    ValidationIssueCode.PROVIDER_OBJECT_NOT_ALLOWED,
                    "candidate",
                    "Provider response objects are not accepted by semantic schema validation.",
                )
            ],
        )

    if isinstance(candidate, SemanticFacts):
        values: object = candidate.model_dump()
    elif isinstance(candidate, Mapping) and not isinstance(candidate, BaseModel):
        values = dict(candidate)
    else:
        return SchemaValidationResult(
            status=SchemaValidationStatus.FAILED,
            issues=[
                _issue(
                    ValidationIssueCode.INVALID_CANDIDATE_TYPE,
                    "candidate",
                    "Semantic candidate must be SemanticFacts or a supported mapping.",
                )
            ],
        )

    expected_fields = list(SemanticFacts.model_fields)
    supplied_fields = set(values)
    boundary_issues = [
        _issue(
            ValidationIssueCode.MISSING_REQUIRED_FIELD,
            field,
            f"Required semantic field {field} is missing.",
        )
        for field in expected_fields
        if field not in supplied_fields
    ]
    boundary_issues.extend(
        _issue(
            ValidationIssueCode.UNSUPPORTED_FIELD,
            field,
            f"Unsupported semantic field {field} is not allowed.",
        )
        for field in sorted(supplied_fields - set(expected_fields))
    )
    if boundary_issues:
        return SchemaValidationResult(status=SchemaValidationStatus.FAILED, issues=boundary_issues)

    try:
        facts = SemanticFacts.model_validate(values)
    except ValidationError as exc:
        issues = [_pydantic_issue(error) for error in exc.errors()]
        return SchemaValidationResult(status=SchemaValidationStatus.FAILED, issues=issues)

    return SchemaValidationResult(
        status=SchemaValidationStatus.PASSED,
        semantic_facts=facts,
    )
