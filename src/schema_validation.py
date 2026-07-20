"""Strict structural validation for the true-north incident-fact envelope."""

import re
from typing import Optional

from pydantic import ValidationError

from src.contracts import (
    EXTRACTION_CONTRACT_IDENTITY,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    ProviderStructuredResponse,
    SchemaValidationResult,
    SchemaValidationStatus,
    TrueNorthSemanticEnvelope,
    ValidationIssue,
    ValidationIssueCode,
)


_FACT_ID = re.compile(r"FACT-\d{4}")
_EVIDENCE_ID = re.compile(r"EVID-\d{4}")
_GROUP_ID = re.compile(r"CGRP-\d{4}")


def _issue(code: ValidationIssueCode, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def validate_semantic_schema(
    candidate: object,
    *,
    expected_incident_id: Optional[str] = None,
) -> SchemaValidationResult:
    """Validate exact shape, identities, canonical IDs, ordering, and references."""
    if isinstance(candidate, ProviderStructuredResponse):
        return SchemaValidationResult(
            status=SchemaValidationStatus.FAILED,
            issues=[_issue(
                ValidationIssueCode.PROVIDER_OBJECT_NOT_ALLOWED,
                "candidate",
                "Provider objects must terminate at the repository adapter.",
            )],
        )
    try:
        envelope = (
            candidate
            if isinstance(candidate, TrueNorthSemanticEnvelope)
            else TrueNorthSemanticEnvelope.model_validate(candidate)
        )
    except (ValidationError, TypeError, ValueError) as exc:
        return SchemaValidationResult(
            status=SchemaValidationStatus.FAILED,
            issues=[_issue(
                ValidationIssueCode.INVALID_CANDIDATE_TYPE,
                "candidate",
                f"Candidate does not satisfy the strict true-north schema: {exc.__class__.__name__}.",
            )],
        )

    issues: list[ValidationIssue] = []
    if envelope.schema_identity != SEMANTIC_SCHEMA_IDENTITY:
        issues.append(_issue(
            ValidationIssueCode.UNSUPPORTED_SCHEMA_IDENTITY,
            "schema_identity",
            "Semantic schema identity is unsupported.",
        ))
    if envelope.schema_version != SEMANTIC_SCHEMA_VERSION:
        issues.append(_issue(
            ValidationIssueCode.UNSUPPORTED_SCHEMA_VERSION,
            "schema_version",
            "Semantic schema version is unsupported.",
        ))
    if envelope.extraction_contract_identity != EXTRACTION_CONTRACT_IDENTITY:
        issues.append(_issue(
            ValidationIssueCode.UNSUPPORTED_SCHEMA_IDENTITY,
            "extraction_contract_identity",
            "Extraction contract identity is unsupported.",
        ))
    if expected_incident_id is not None and envelope.incident_id != expected_incident_id:
        issues.append(_issue(
            ValidationIssueCode.INCIDENT_ID_MISMATCH,
            "incident_id",
            "Semantic incident identity does not match the validated incident.",
        ))

    fact_ids = [fact.fact_id for fact in envelope.facts]
    if len(fact_ids) != len(set(fact_ids)):
        issues.append(_issue(ValidationIssueCode.DUPLICATE_IDENTIFIER, "facts", "Fact identifiers must be unique."))
    for index, fact_id in enumerate(fact_ids, 1):
        if _FACT_ID.fullmatch(fact_id) is None:
            issues.append(_issue(ValidationIssueCode.INVALID_IDENTIFIER, f"facts.{index - 1}.fact_id", "Fact identifier has an invalid form."))
        elif fact_id != f"FACT-{index:04d}":
            issues.append(_issue(ValidationIssueCode.INVALID_COLLECTION_ORDER, f"facts.{index - 1}.fact_id", "Fact identifiers must encode canonical collection order."))

    fact_id_set = set(fact_ids)
    evidence_ids: list[str] = []
    group_first_seen: list[str] = []
    for fact_index, fact in enumerate(envelope.facts):
        if fact.supersedes_fact_id is not None and fact.supersedes_fact_id not in fact_id_set:
            issues.append(_issue(
                ValidationIssueCode.DANGLING_REFERENCE,
                f"facts.{fact_index}.supersedes_fact_id",
                "Correction reference does not resolve to a fact.",
            ))
        if fact.contradiction_group is not None:
            if _GROUP_ID.fullmatch(fact.contradiction_group) is None:
                issues.append(_issue(
                    ValidationIssueCode.INVALID_IDENTIFIER,
                    f"facts.{fact_index}.contradiction_group",
                    "Contradiction-group identifier has an invalid form.",
                ))
            if fact.contradiction_group not in group_first_seen:
                group_first_seen.append(fact.contradiction_group)
        if fact.uncertainty != sorted(fact.uncertainty, key=lambda value: list(type(value)).index(value)):
            issues.append(_issue(
                ValidationIssueCode.INVALID_COLLECTION_ORDER,
                f"facts.{fact_index}.uncertainty",
                "Uncertainty dimensions are not in canonical order.",
            ))
        for evidence_index, evidence in enumerate(fact.evidence):
            evidence_ids.append(evidence.evidence_id)
            if evidence.supports != sorted(evidence.supports, key=lambda value: list(type(value)).index(value)):
                issues.append(_issue(
                    ValidationIssueCode.INVALID_COLLECTION_ORDER,
                    f"facts.{fact_index}.evidence.{evidence_index}.supports",
                    "Evidence supports are not in canonical order.",
                ))

    if group_first_seen != [f"CGRP-{index:04d}" for index in range(1, len(group_first_seen) + 1)]:
        issues.append(_issue(
            ValidationIssueCode.INVALID_COLLECTION_ORDER,
            "facts.contradiction_group",
            "Contradiction groups are not canonically identified by first appearance.",
        ))
    if len(evidence_ids) != len(set(evidence_ids)):
        issues.append(_issue(ValidationIssueCode.DUPLICATE_IDENTIFIER, "facts.evidence", "Evidence identifiers must be globally unique."))
    for index, evidence_id in enumerate(evidence_ids, 1):
        if _EVIDENCE_ID.fullmatch(evidence_id) is None:
            issues.append(_issue(ValidationIssueCode.INVALID_IDENTIFIER, "facts.evidence", "Evidence identifier has an invalid form."))
        elif evidence_id != f"EVID-{index:04d}":
            issues.append(_issue(ValidationIssueCode.INVALID_COLLECTION_ORDER, "facts.evidence", "Evidence identifiers must encode canonical order."))

    if issues:
        return SchemaValidationResult(status=SchemaValidationStatus.FAILED, issues=issues)
    return SchemaValidationResult(
        status=SchemaValidationStatus.PASSED,
        semantic_envelope=envelope,
    )
