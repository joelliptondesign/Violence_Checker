"""Strict structural validation for proposition-oriented semantic envelopes."""

import re
from typing import Iterable, Optional

from src.contracts import (
    EvidenceSubjectKind,
    ProviderStructuredResponse,
    RelationshipKind,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    SchemaValidationResult,
    SchemaValidationStatus,
    ValidationIssue,
    ValidationIssueCode,
    ViolenceSemanticEnvelope,
)


_ID_PATTERNS = {
    "entities": re.compile(r"ENT-\d{4}"),
    "propositions": re.compile(r"PROP-\d{4}"),
    "relationships": re.compile(r"REL-\d{4}"),
    "uncertainties": re.compile(r"UNC-\d{4}"),
    "evidence_excerpts": re.compile(r"EVID-\d{4}"),
    "evidence_supports": re.compile(r"SUP-\d{4}"),
}


def _issue(code: ValidationIssueCode, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def _check_ids(
    issues: list[ValidationIssue],
    collection_name: str,
    identifiers: Iterable[str],
) -> None:
    pattern = _ID_PATTERNS[collection_name]
    seen: set[str] = set()
    for index, identifier in enumerate(identifiers, start=1):
        field = f"{collection_name}.{index - 1}"
        expected = {
            "entities": "ENT",
            "propositions": "PROP",
            "relationships": "REL",
            "uncertainties": "UNC",
            "evidence_excerpts": "EVID",
            "evidence_supports": "SUP",
        }[collection_name] + f"-{index:04d}"
        if pattern.fullmatch(identifier) is None:
            issues.append(_issue(ValidationIssueCode.INVALID_IDENTIFIER, field, "Identifier has an invalid form."))
        elif identifier != expected:
            issues.append(
                _issue(
                    ValidationIssueCode.INVALID_COLLECTION_ORDER,
                    field,
                    f"Expected canonical identifier {expected} at this position.",
                )
            )
        if identifier in seen:
            issues.append(_issue(ValidationIssueCode.DUPLICATE_IDENTIFIER, field, "Identifier is duplicated."))
        seen.add(identifier)


def validate_semantic_schema(
    candidate: object,
    *,
    expected_incident_id: Optional[str] = None,
) -> SchemaValidationResult:
    """Validate exact structure, identities, references, and canonical IDs only."""
    if isinstance(candidate, ProviderStructuredResponse):
        return SchemaValidationResult(
            status=SchemaValidationStatus.FAILED,
            issues=[
                _issue(
                    ValidationIssueCode.PROVIDER_OBJECT_NOT_ALLOWED,
                    "candidate",
                    "Provider response objects must terminate at the provider adapter.",
                )
            ],
        )
    if not isinstance(candidate, ViolenceSemanticEnvelope):
        return SchemaValidationResult(
            status=SchemaValidationStatus.FAILED,
            issues=[
                _issue(
                    ValidationIssueCode.INVALID_CANDIDATE_TYPE,
                    "candidate",
                    "Semantic validation requires a typed provider-independent envelope.",
                )
            ],
        )

    issues: list[ValidationIssue] = []
    if candidate.schema_identity != SEMANTIC_SCHEMA_IDENTITY:
        issues.append(
            _issue(
                ValidationIssueCode.UNSUPPORTED_SCHEMA_IDENTITY,
                "schema_identity",
                "Semantic schema identity is unsupported.",
            )
        )
    if candidate.schema_version != SEMANTIC_SCHEMA_VERSION:
        issues.append(
            _issue(
                ValidationIssueCode.UNSUPPORTED_SCHEMA_VERSION,
                "schema_version",
                "Semantic schema version is unsupported.",
            )
        )
    if expected_incident_id is not None and candidate.incident_id != expected_incident_id:
        issues.append(
            _issue(
                ValidationIssueCode.INCIDENT_ID_MISMATCH,
                "incident_id",
                "Semantic envelope incident identity does not match the validated incident.",
            )
        )
    if not candidate.entities:
        issues.append(_issue(ValidationIssueCode.MISSING_REQUIRED_FIELD, "entities", "At least one entity is required."))
    if not candidate.propositions:
        issues.append(_issue(ValidationIssueCode.MISSING_REQUIRED_FIELD, "propositions", "At least one proposition is required."))
    if not candidate.evidence_excerpts:
        issues.append(_issue(ValidationIssueCode.MISSING_REQUIRED_FIELD, "evidence_excerpts", "At least one evidence excerpt is required."))
    if not candidate.evidence_supports:
        issues.append(_issue(ValidationIssueCode.MISSING_REQUIRED_FIELD, "evidence_supports", "At least one evidence support is required."))

    _check_ids(issues, "entities", (item.entity_id for item in candidate.entities))
    _check_ids(issues, "propositions", (item.proposition_id for item in candidate.propositions))
    _check_ids(issues, "relationships", (item.relationship_id for item in candidate.relationships))
    _check_ids(issues, "uncertainties", (item.uncertainty_id for item in candidate.uncertainties))
    _check_ids(issues, "evidence_excerpts", (item.evidence_id for item in candidate.evidence_excerpts))
    _check_ids(issues, "evidence_supports", (item.support_id for item in candidate.evidence_supports))

    entity_ids = {item.entity_id for item in candidate.entities}
    proposition_ids = {item.proposition_id for item in candidate.propositions}
    relationship_ids = {item.relationship_id for item in candidate.relationships}
    uncertainty_ids = {item.uncertainty_id for item in candidate.uncertainties}
    evidence_ids = {item.evidence_id for item in candidate.evidence_excerpts}

    for index, proposition in enumerate(candidate.propositions):
        if proposition.actor_ref not in entity_ids:
            issues.append(_issue(ValidationIssueCode.DANGLING_REFERENCE, f"propositions.{index}.actor_ref", "Actor reference does not resolve."))
        if proposition.target.target_ref is not None and proposition.target.target_ref not in entity_ids:
            issues.append(_issue(ValidationIssueCode.DANGLING_REFERENCE, f"propositions.{index}.target.target_ref", "Target reference does not resolve."))
        if proposition.attribution and proposition.attribution.source_ref is not None and proposition.attribution.source_ref not in entity_ids:
            issues.append(_issue(ValidationIssueCode.DANGLING_REFERENCE, f"propositions.{index}.attribution.source_ref", "Attribution source reference does not resolve."))

    for index, relationship in enumerate(candidate.relationships):
        field = f"relationships.{index}"
        if relationship.source_proposition_ref not in proposition_ids or relationship.target_proposition_ref not in proposition_ids:
            issues.append(_issue(ValidationIssueCode.DANGLING_REFERENCE, field, "Relationship endpoint does not resolve."))
        if relationship.source_proposition_ref == relationship.target_proposition_ref:
            issues.append(_issue(ValidationIssueCode.INVALID_RELATIONSHIP, field, "Relationship endpoints must be distinct."))
        if relationship.relationship_kind == RelationshipKind.CONFLICTS_WITH:
            if relationship.source_proposition_ref >= relationship.target_proposition_ref:
                issues.append(_issue(ValidationIssueCode.INVALID_RELATIONSHIP, field, "Conflict endpoints are not canonical."))
            if not relationship.disputed_dimensions:
                issues.append(_issue(ValidationIssueCode.INVALID_RELATIONSHIP, field, "Conflict requires disputed dimensions."))
        elif relationship.disputed_dimensions:
            issues.append(_issue(ValidationIssueCode.INVALID_RELATIONSHIP, field, "Only conflict relationships carry disputed dimensions."))

    for index, uncertainty in enumerate(candidate.uncertainties):
        if uncertainty.proposition_ref not in proposition_ids:
            issues.append(_issue(ValidationIssueCode.DANGLING_REFERENCE, f"uncertainties.{index}.proposition_ref", "Uncertainty proposition does not resolve."))

    subject_ids = {
        EvidenceSubjectKind.PROPOSITION: proposition_ids,
        EvidenceSubjectKind.RELATIONSHIP: relationship_ids,
        EvidenceSubjectKind.UNCERTAINTY: uncertainty_ids,
    }
    for index, support in enumerate(candidate.evidence_supports):
        field = f"evidence_supports.{index}"
        if support.evidence_ref not in evidence_ids:
            issues.append(_issue(ValidationIssueCode.DANGLING_REFERENCE, f"{field}.evidence_ref", "Evidence reference does not resolve."))
        if support.subject_ref not in subject_ids[support.subject_kind]:
            issues.append(_issue(ValidationIssueCode.DANGLING_REFERENCE, f"{field}.subject_ref", "Evidence subject does not resolve for its declared kind."))

    duplicate_texts = len({item.text for item in candidate.evidence_excerpts}) != len(candidate.evidence_excerpts)
    if duplicate_texts:
        issues.append(_issue(ValidationIssueCode.DUPLICATE_IDENTIFIER, "evidence_excerpts", "Duplicate exact evidence excerpts are not allowed."))

    if issues:
        return SchemaValidationResult(status=SchemaValidationStatus.FAILED, issues=issues)
    return SchemaValidationResult(
        status=SchemaValidationStatus.PASSED,
        semantic_envelope=candidate,
    )
