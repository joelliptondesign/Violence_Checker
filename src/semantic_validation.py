"""Ordered deterministic schema and domain validation orchestration."""

from collections.abc import Callable

from src.contracts import (
    DomainValidationResult,
    DomainValidationStatus,
    SchemaValidationResult,
    SchemaValidationStatus,
    ValidatedSemanticFacts,
    ValidationFailureStage,
    ValidationResult,
)
from src.domain_validation import validate_semantic_domain
from src.schema_validation import validate_semantic_schema


def validation_not_run() -> ValidationResult:
    """Represent a provider failure that never produced a semantic candidate."""
    return ValidationResult(
        schema_validation=SchemaValidationResult(status=SchemaValidationStatus.NOT_RUN),
        domain_validation=DomainValidationResult(status=DomainValidationStatus.NOT_RUN),
        failure_stage=ValidationFailureStage.NOT_RUN,
    )


def validate_semantic_candidate(
    candidate: object,
    *,
    domain_validator: Callable = validate_semantic_domain,
) -> ValidationResult:
    schema_result = validate_semantic_schema(candidate)
    if not schema_result.passed:
        return ValidationResult(
            schema_validation=schema_result,
            domain_validation=DomainValidationResult(status=DomainValidationStatus.NOT_RUN),
            failure_stage=ValidationFailureStage.SCHEMA,
        )

    facts = schema_result.semantic_facts
    if facts is None:  # Contract consistency makes this unreachable.
        raise RuntimeError("passed schema validation did not expose SemanticFacts")

    domain_result = domain_validator(facts)
    if not domain_result.passed:
        return ValidationResult(
            schema_validation=schema_result,
            domain_validation=domain_result,
            failure_stage=ValidationFailureStage.DOMAIN,
        )

    return ValidationResult(
        schema_validation=schema_result,
        domain_validation=domain_result,
        failure_stage=ValidationFailureStage.NONE,
        validated_facts=ValidatedSemanticFacts(facts=facts),
    )
