"""Ordered true-north schema and domain validation boundary."""

from collections.abc import Callable

from src.contracts import (
    CompletenessStatus,
    DomainValidationResult,
    DomainValidationStatus,
    ProcessingStatus,
    SchemaValidationResult,
    SchemaValidationStatus,
    ValidationFailureStage,
    ValidationResult,
)
from src.domain_validation import validate_semantic_domain
from src.schema_validation import validate_semantic_schema
from src.semantic_derivation import derive_semantic_views, has_unresolved_semantic_content


def validation_not_run() -> ValidationResult:
    return ValidationResult(
        schema_validation=SchemaValidationResult(status=SchemaValidationStatus.NOT_RUN),
        domain_validation=DomainValidationResult(status=DomainValidationStatus.NOT_RUN),
        failure_stage=ValidationFailureStage.NOT_RUN,
        processing_status=ProcessingStatus.PIPELINE_FAILURE,
        completeness_status=CompletenessStatus.INCOMPLETE_ANALYSIS,
    )


def validate_semantic_candidate(
    candidate: object,
    *,
    incident_id: str,
    normalized_narrative: str,
    domain_validator: Callable = validate_semantic_domain,
) -> ValidationResult:
    schema_result = validate_semantic_schema(candidate, expected_incident_id=incident_id)
    if not schema_result.passed:
        return ValidationResult(
            schema_validation=schema_result,
            domain_validation=DomainValidationResult(status=DomainValidationStatus.NOT_RUN),
            failure_stage=ValidationFailureStage.SCHEMA,
            processing_status=ProcessingStatus.SCHEMA_FAILURE,
            completeness_status=CompletenessStatus.INCOMPLETE_ANALYSIS,
        )

    envelope = schema_result.semantic_envelope
    if envelope is None:
        raise RuntimeError("passed schema validation did not expose an envelope")
    domain_result = domain_validator(envelope, normalized_narrative=normalized_narrative)
    if not domain_result.passed:
        return ValidationResult(
            schema_validation=schema_result,
            domain_validation=domain_result,
            failure_stage=ValidationFailureStage.DOMAIN,
            processing_status=ProcessingStatus.VALIDATION_FAILURE,
            completeness_status=CompletenessStatus.INCOMPLETE_ANALYSIS,
        )

    derived = derive_semantic_views(envelope)
    completeness = (
        CompletenessStatus.UNRESOLVED_SEMANTIC_CONTENT
        if has_unresolved_semantic_content(envelope, derived)
        else CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS
    )
    return ValidationResult(
        schema_validation=schema_result,
        domain_validation=domain_result,
        failure_stage=ValidationFailureStage.NONE,
        processing_status=ProcessingStatus.SUCCESSFUL_ANALYSIS,
        completeness_status=completeness,
        validated_envelope=envelope,
        derived_semantics=derived,
    )
