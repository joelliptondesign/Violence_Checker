"""Ordered successor schema, domain, and deterministic derivation boundary."""

from collections.abc import Callable

from src.contracts import (
    DomainValidationResult,
    DomainValidationStatus,
    SchemaValidationResult,
    SchemaValidationStatus,
    ValidatedSemanticEnvelope,
    ValidationFailureStage,
    ValidationResult,
)
from src.domain_validation import validate_semantic_domain
from src.schema_validation import validate_semantic_schema
from src.semantic_derivation import derive_semantic_views


def validation_not_run() -> ValidationResult:
    return ValidationResult(
        schema_validation=SchemaValidationResult(status=SchemaValidationStatus.NOT_RUN),
        domain_validation=DomainValidationResult(status=DomainValidationStatus.NOT_RUN),
        failure_stage=ValidationFailureStage.NOT_RUN,
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
        )

    derived, policy_candidate = derive_semantic_views(envelope)
    return ValidationResult(
        schema_validation=schema_result,
        domain_validation=domain_result,
        failure_stage=ValidationFailureStage.NONE,
        validated_envelope=ValidatedSemanticEnvelope(
            envelope=envelope,
            derived=derived,
            policy_candidate=policy_candidate,
        ),
    )
