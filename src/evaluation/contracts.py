"""Strict, provider-independent contracts for future evaluation artifacts.

These models describe evaluation data only. They do not execute the semantic
pipeline, infer expected values, compare cases, or call a provider.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, StrictStr, field_validator, model_validator

from src.contracts import (
    PipelineFailureProvenance,
    PolicyDecision,
    SemanticFacts,
    ValidationFailureStage,
)
from src.models import ViolenceFinding


class EvaluationContract(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


def _require_identifier(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty or whitespace")
    return value


def _require_unique(values: List[Enum], field_name: str) -> List[Enum]:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return values


class ExpectedSemanticOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class ObservedSemanticOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class ObservedValidationOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


class EvaluationExecutionMode(str, Enum):
    LIVE = "live"
    TEST = "test"


class ExpectedField(str, Enum):
    FAILURE_PROVENANCE = "failure_provenance"
    VALIDATION_STAGE = "validation_stage"
    COMPATIBILITY_FINDING = "compatibility_finding"
    POLICY_DECISION = "policy_decision"


class DifferenceClassification(str, Enum):
    MATCH = "match"
    VALUE_MISMATCH = "value_mismatch"
    EXPECTED_VALUE_MISSING = "expected_value_missing"
    OBSERVED_VALUE_MISSING = "observed_value_missing"
    NON_COMPARABLE = "non_comparable"


class DifferenceReasonCode(str, Enum):
    VALUES_EQUAL = "values_equal"
    VALUES_DIFFER = "values_differ"
    EXPECTATION_NOT_ASSERTED = "expectation_not_asserted"
    OBSERVATION_UNAVAILABLE = "observation_unavailable"
    PIPELINE_FAILURE = "pipeline_failure"
    VALIDATION_FAILURE = "validation_failure"
    MISSING_OBSERVED_VALUE = "missing_observed_value"
    UNEXPECTED_OBSERVED_VALUE = "unexpected_observed_value"
    SCALAR_MISMATCH = "scalar_mismatch"
    COLLECTION_MISMATCH = "collection_mismatch"
    VALIDATION_STAGE_MISMATCH = "validation_stage_mismatch"
    FAILURE_PROVENANCE_MISMATCH = "failure_provenance_mismatch"
    POLICY_OUTCOME_MISMATCH = "policy_outcome_mismatch"
    POLICY_REASON_MISMATCH = "policy_reason_mismatch"
    SEMANTIC_SUCCESS_MISMATCH = "semantic_success_mismatch"
    NON_COMPARABLE_PROVIDER_FAILURE = "non_comparable_provider_failure"


class CaseEvaluationStatus(str, Enum):
    MATCH = "match"
    PARTIAL_MISMATCH = "partial_mismatch"
    FAILURE = "failure"
    NON_COMPARABLE = "non_comparable"


class FailurePattern(str, Enum):
    PROVIDER_FAILURE = "provider_failure"
    VALIDATION_FAILURE = "validation_failure"
    COMPATIBILITY_FAILURE = "compatibility_failure"
    COMPATIBILITY_DIFFERENCE = "compatibility_difference"
    POLICY_FAILURE = "policy_failure"
    MISSING_OBSERVATION = "missing_observation"
    HISTORICAL_CURRENT_CONFUSION = "historical_current_confusion"
    CORRECTION_REVERSAL_FAILURE = "correction_reversal_failure"
    CONFLICT_RESOLUTION_FAILURE = "conflict_resolution_failure"
    THREAT_CLASSIFICATION_FAILURE = "threat_classification_failure"
    ACCIDENTAL_INTENTIONAL_CONFUSION = "accidental_intentional_confusion"
    NEGATION_FAILURE = "negation_failure"
    OBJECT_DIRECTED_INTERPERSONAL_CONFUSION = "object_directed_interpersonal_confusion"
    SELF_DIRECTED_INTERPERSONAL_CONFUSION = "self_directed_interpersonal_confusion"
    UNSUPPORTED_EVIDENCE = "unsupported_evidence"
    EVIDENCE_OMISSION = "evidence_omission"
    EVENT_TYPE_DISAGREEMENT = "event_type_disagreement"
    UNCERTAINTY_NOTE_DIFFERENCE = "uncertainty_note_difference"
    # Retained so previously generated artifacts remain readable. New comparisons
    # use the direction-neutral findings above instead.
    EXCESSIVE_UNCERTAINTY = "excessive_uncertainty"
    INSUFFICIENT_UNCERTAINTY = "insufficient_uncertainty"
    SEMANTIC_FIELD_MISMATCH = "semantic_field_mismatch"
    VALIDATION_REJECTION = "validation_rejection"
    POLICY_MISMATCH = "policy_mismatch"
    PIPELINE_FAILURE = "pipeline_failure"


class NonComparableReason(str, Enum):
    EXPECTATION_NOT_ASSERTED = "expectation_not_asserted"
    OBSERVATION_FAILED = "observation_failed"
    SCHEMA_VERSION_MISMATCH = "schema_version_mismatch"
    CORPUS_IDENTITY_MISMATCH = "corpus_identity_mismatch"


class BaselineClassification(str, Enum):
    IMPROVED = "improved"
    DEGRADED = "degraded"
    UNCHANGED = "unchanged"
    INCOMPARABLE = "incomparable"


class BaselineObservationCode(str, Enum):
    CASE_STATUS_IMPROVED = "case_status_improved"
    CASE_STATUS_DEGRADED = "case_status_degraded"
    CASE_STATUS_UNCHANGED = "case_status_unchanged"
    RESULT_SET_CHANGED = "result_set_changed"
    PROVENANCE_INCOMPATIBLE = "provenance_incompatible"


class EvaluationCategory(str, Enum):
    COMPLETED_PHYSICAL_ASSAULT = "completed_physical_assault"
    ATTEMPTED_PHYSICAL_ASSAULT = "attempted_physical_assault"
    VERBAL_THREAT = "verbal_threat"
    ACCIDENTAL_CONTACT = "accidental_contact"
    HISTORICAL_DISCLOSURE = "historical_disclosure"
    NEGATED_EVENT = "negated_event"
    CORRECTION = "correction"
    CONFLICTING_NARRATIVE = "conflicting_narrative"
    OBJECT_DIRECTED_AGGRESSION = "object_directed_aggression"
    SELF_DIRECTED_VIOLENCE = "self_directed_violence"
    AMBIGUOUS_ENCOUNTER = "ambiguous_encounter"
    INCOMPLETE_REPORT = "incomplete_report"


class DocumentationQualityTag(str, Enum):
    CLEAR = "clear"
    POOR_GRAMMAR = "poor_grammar"
    ABBREVIATION = "abbreviation"
    SHORTHAND = "shorthand"
    INCOMPLETE = "incomplete"
    CORRECTION_LANGUAGE = "correction_language"
    CONFLICTING_ACCOUNTS = "conflicting_accounts"
    HISTORICAL_REFERENCE = "historical_reference"
    NEGATION_LANGUAGE = "negation_language"
    AMBIGUOUS_PRONOUNS = "ambiguous_pronouns"
    TEMPORAL_AMBIGUITY = "temporal_ambiguity"


class EvaluationCaseMetadata(EvaluationContract):
    categories: List[StrictStr]
    documentation_quality_tags: List[StrictStr] = Field(default_factory=list)
    engineering_notes: Optional[StrictStr] = None
    primary_category: Optional[EvaluationCategory] = None
    compound: StrictBool = False

    @field_validator("categories", "documentation_quality_tags")
    @classmethod
    def require_non_empty_items(cls, values: List[str]) -> List[str]:
        if any(not value.strip() for value in values):
            raise ValueError("metadata list items must not be empty or whitespace")
        if len(values) != len(set(values)):
            raise ValueError("metadata lists must not contain duplicates")
        return values

    @model_validator(mode="after")
    def require_category(self) -> "EvaluationCaseMetadata":
        if not self.categories:
            raise ValueError("evaluation metadata requires at least one category")
        if self.engineering_notes is not None and not self.engineering_notes.strip():
            raise ValueError("engineering_notes must be omitted or non-empty")
        if self.primary_category is not None:
            allowed_categories = {item.value for item in EvaluationCategory}
            allowed_tags = {item.value for item in DocumentationQualityTag}
            if self.categories[0] != self.primary_category.value:
                raise ValueError("primary_category must be the first ordered category")
            if any(value not in allowed_categories for value in self.categories):
                raise ValueError("authoritative categories must use bounded vocabulary")
            if any(value not in allowed_tags for value in self.documentation_quality_tags):
                raise ValueError("authoritative documentation tags must use bounded vocabulary")
        return self


class ExpectedEvaluationOutcome(EvaluationContract):
    semantic_outcome: ExpectedSemanticOutcome
    semantic_facts: Optional[SemanticFacts] = None
    validation_failure_stage: Optional[ValidationFailureStage] = None
    failure_provenance: Optional[PipelineFailureProvenance] = None
    compatibility_finding: Optional[ViolenceFinding] = None
    policy_decision: Optional[PolicyDecision] = None
    intentionally_not_asserted: List[ExpectedField] = Field(default_factory=list)

    @field_validator("intentionally_not_asserted")
    @classmethod
    def require_unique_unasserted_fields(cls, values: List[ExpectedField]) -> List[ExpectedField]:
        return _require_unique(values, "intentionally_not_asserted")

    @model_validator(mode="after")
    def require_consistent_expectation(self) -> "ExpectedEvaluationOutcome":
        if self.semantic_outcome == ExpectedSemanticOutcome.SUCCESS:
            if self.semantic_facts is None:
                raise ValueError("expected success requires semantic_facts")
            if self.validation_failure_stage is not None or self.failure_provenance is not None:
                raise ValueError("expected success cannot contain failure provenance")
        else:
            if self.semantic_facts is not None or self.compatibility_finding is not None:
                raise ValueError("expected failure cannot contain successful semantic payloads")
            if self.policy_decision is not None and self.policy_decision.failure_provenance is None:
                raise ValueError("expected failure cannot contain a non-failure policy decision")
            if self.validation_failure_stage is None and self.failure_provenance is None:
                raise ValueError("expected failure requires validation stage or failure provenance")
            if self.validation_failure_stage in {
                ValidationFailureStage.NONE,
                ValidationFailureStage.NOT_RUN,
            }:
                raise ValueError("expected failure requires an actual validation failure stage")

        asserted_values = {
            ExpectedField.FAILURE_PROVENANCE: self.failure_provenance,
            ExpectedField.VALIDATION_STAGE: self.validation_failure_stage,
            ExpectedField.COMPATIBILITY_FINDING: self.compatibility_finding,
            ExpectedField.POLICY_DECISION: self.policy_decision,
        }
        contradictory = [field.value for field in self.intentionally_not_asserted if asserted_values[field] is not None]
        if contradictory:
            raise ValueError(f"fields cannot be both asserted and intentionally unasserted: {contradictory}")
        return self


class EvaluationCase(EvaluationContract):
    case_id: StrictStr
    schema_version: StrictStr
    synthetic: StrictBool
    narrative: StrictStr
    metadata: EvaluationCaseMetadata
    ground_truth: ExpectedEvaluationOutcome

    @field_validator("case_id", "schema_version")
    @classmethod
    def require_identifiers(cls, value: str, info: Any) -> str:
        return _require_identifier(value, info.field_name)

    @field_validator("narrative")
    @classmethod
    def require_narrative(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("narrative must not be empty or whitespace")
        return value

    @model_validator(mode="after")
    def require_synthetic_designation(self) -> "EvaluationCase":
        if self.synthetic is not True:
            raise ValueError("evaluation cases must be explicitly synthetic")
        return self


class EvaluationArtifactProvenance(EvaluationContract):
    evaluation_schema_version: StrictStr
    corpus_identity: StrictStr
    repository_commit: StrictStr
    model_identifier: Optional[StrictStr] = None
    extraction_configuration_identity: Optional[StrictStr] = None
    run_timestamp: datetime
    execution_mode: EvaluationExecutionMode

    @field_validator(
        "evaluation_schema_version",
        "corpus_identity",
        "repository_commit",
        "model_identifier",
        "extraction_configuration_identity",
    )
    @classmethod
    def require_provenance_identifiers(cls, value: Optional[str], info: Any) -> Optional[str]:
        if value is not None:
            return _require_identifier(value, info.field_name)
        return value


class ObservedEvaluationResult(EvaluationContract):
    case_id: StrictStr
    run_id: StrictStr
    provenance: EvaluationArtifactProvenance
    semantic_outcome: ObservedSemanticOutcome
    validation_outcome: ObservedValidationOutcome
    validation_failure_stage: Optional[ValidationFailureStage] = None
    semantic_facts: Optional[SemanticFacts] = None
    compatibility_finding: Optional[ViolenceFinding] = None
    policy_decision: Optional[PolicyDecision] = None
    failure_provenance: Optional[PipelineFailureProvenance] = None

    @field_validator("case_id", "run_id")
    @classmethod
    def require_identifiers(cls, value: str, info: Any) -> str:
        return _require_identifier(value, info.field_name)

    @model_validator(mode="after")
    def require_consistent_observation(self) -> "ObservedEvaluationResult":
        if self.semantic_outcome == ObservedSemanticOutcome.SUCCESS:
            if self.validation_outcome != ObservedValidationOutcome.PASSED or self.semantic_facts is None:
                raise ValueError("observed success requires passed validation and semantic_facts")
            if self.validation_failure_stage is not None or self.failure_provenance is not None:
                raise ValueError("observed success cannot contain failure provenance")
        else:
            if self.semantic_facts is not None or self.compatibility_finding is not None:
                raise ValueError("observed failure cannot expose admissible facts or compatibility findings")
            if self.validation_outcome == ObservedValidationOutcome.PASSED:
                raise ValueError("observed failure cannot report passed validation")
            if self.validation_outcome == ObservedValidationOutcome.FAILED:
                if self.validation_failure_stage not in {
                    ValidationFailureStage.SCHEMA,
                    ValidationFailureStage.DOMAIN,
                }:
                    raise ValueError("failed validation requires schema or domain failure stage")
            elif self.validation_failure_stage is not None:
                raise ValueError("validation stage is allowed only when validation failed")
            if self.failure_provenance is None and self.validation_failure_stage is None:
                raise ValueError("observed failure requires explicit failure provenance")
            if self.policy_decision is not None and self.policy_decision.failure_provenance is None:
                raise ValueError("observed failure cannot contain a non-failure policy decision")
        return self


class FieldDifference(EvaluationContract):
    field: StrictStr
    expected_value: JsonValue = None
    observed_value: JsonValue = None
    classification: DifferenceClassification
    reason_code: DifferenceReasonCode
    explanation: Optional[StrictStr] = None

    @field_validator("field")
    @classmethod
    def require_field(cls, value: str) -> str:
        return _require_identifier(value, "field")

    @model_validator(mode="after")
    def require_reason_alignment(self) -> "FieldDifference":
        if self.classification == DifferenceClassification.MATCH and self.reason_code != DifferenceReasonCode.VALUES_EQUAL:
            raise ValueError("matching differences require values_equal reason")
        if self.classification != DifferenceClassification.MATCH and self.reason_code == DifferenceReasonCode.VALUES_EQUAL:
            raise ValueError("material differences cannot use values_equal reason")
        if self.explanation is not None and not self.explanation.strip():
            raise ValueError("difference explanation must be omitted or non-empty")
        return self

    @property
    def material(self) -> bool:
        return self.classification != DifferenceClassification.MATCH


class CaseEvaluationResult(EvaluationContract):
    result_id: StrictStr
    case_id: StrictStr
    observed_run_id: StrictStr
    status: CaseEvaluationStatus
    field_differences: List[FieldDifference] = Field(default_factory=list)
    failure_patterns: List[FailurePattern] = Field(default_factory=list)
    non_comparable_reason: Optional[NonComparableReason] = None

    @field_validator("result_id", "case_id", "observed_run_id")
    @classmethod
    def require_identifiers(cls, value: str, info: Any) -> str:
        return _require_identifier(value, info.field_name)

    @field_validator("failure_patterns")
    @classmethod
    def require_unique_failure_patterns(cls, values: List[FailurePattern]) -> List[FailurePattern]:
        return _require_unique(values, "failure_patterns")

    @model_validator(mode="after")
    def require_status_invariants(self) -> "CaseEvaluationResult":
        material_differences = [difference for difference in self.field_differences if difference.material]
        if self.status == CaseEvaluationStatus.MATCH:
            if material_differences or self.failure_patterns or self.non_comparable_reason is not None:
                raise ValueError("match cannot contain material differences or failure provenance")
        elif self.status == CaseEvaluationStatus.PARTIAL_MISMATCH:
            if not material_differences:
                raise ValueError("partial mismatch requires at least one material difference")
            if self.non_comparable_reason is not None:
                raise ValueError("partial mismatch cannot contain non-comparable provenance")
        elif self.status == CaseEvaluationStatus.FAILURE:
            if not self.failure_patterns:
                raise ValueError("failure requires at least one ordered failure pattern")
            if self.non_comparable_reason is not None:
                raise ValueError("failure cannot contain non-comparable provenance")
        elif self.non_comparable_reason is None:
            raise ValueError("non-comparable result requires explicit provenance")
        return self


class BaselineComparisonObservation(EvaluationContract):
    code: BaselineObservationCode
    detail: StrictStr

    @field_validator("detail")
    @classmethod
    def require_detail(cls, value: str) -> str:
        return _require_identifier(value, "detail")


class BaselineComparison(EvaluationContract):
    comparison_id: StrictStr
    prior_result_id: StrictStr
    current_result_id: StrictStr
    classification: BaselineClassification
    observations: List[BaselineComparisonObservation] = Field(default_factory=list)

    @field_validator("comparison_id", "prior_result_id", "current_result_id")
    @classmethod
    def require_identifiers(cls, value: str, info: Any) -> str:
        return _require_identifier(value, info.field_name)

    @model_validator(mode="after")
    def require_comparison_observations(self) -> "BaselineComparison":
        if not self.observations:
            raise ValueError("baseline classification requires ordered comparison observations")
        return self
