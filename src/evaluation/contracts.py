"""Strict operational contracts for the True North evaluation family."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, StrictStr, field_validator, model_validator

from src.contracts import (
    AssertionStatus, CompletenessStatus, Conduct, FactDirection, IncidentDirection,
    Intentionality, MaterialAttribute, PolicyOutcome, ProcessingStatus,
    ResolutionStatus, TemporalScope, UncertaintyDimension, ValidationFailureStage,
    ValidationIssueCode,
)


class EvaluationContract(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


def _identifier(value: str, field: str) -> str:
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    return value


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
    OPERATIONAL_FACTS = "operational_facts"
    DETERMINISTIC_OUTCOME = "deterministic_outcome"
    PROCESSING_STATUS = "processing_status"
    COMPLETENESS_STATUS = "completeness_status"


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
    POLICY_OUTCOME_MISMATCH = "policy_outcome_mismatch"
    PROCESSING_STATUS_MISMATCH = "processing_status_mismatch"
    COMPLETENESS_STATUS_MISMATCH = "completeness_status_mismatch"
    DOCTRINE_COMPLIANCE_MISMATCH = "doctrine_compliance_mismatch"


class CaseEvaluationStatus(str, Enum):
    MATCH = "match"
    PARTIAL_MISMATCH = "partial_mismatch"
    FAILURE = "failure"
    NON_COMPARABLE = "non_comparable"


class FailurePattern(str, Enum):
    PROVIDER_FAILURE = "provider_failure"
    VALIDATION_FAILURE = "validation_failure"
    POLICY_FAILURE = "policy_failure"
    MISSING_OBSERVATION = "missing_observation"
    UNSUPPORTED_EVIDENCE = "unsupported_evidence"
    EVIDENCE_OMISSION = "evidence_omission"
    OPERATIONAL_FACT_MISMATCH = "operational_fact_mismatch"
    PROCESSING_STATUS_MISMATCH = "processing_status_mismatch"
    COMPLETENESS_STATUS_MISMATCH = "completeness_status_mismatch"
    DOCTRINE_MISMATCH = "doctrine_mismatch"
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
    EXPLICIT_THREAT = "explicit_threat"
    PHYSICAL_ATTEMPT = "physical_attempt"
    COMPLETED_PHYSICAL_CONTACT = "completed_physical_contact"
    SELF_HARM = "self_harm"
    INTENTIONAL_PROPERTY_VIOLENCE = "intentional_property_violence"
    ACCIDENTAL_CONTACT = "accidental_contact"
    HISTORICAL_ONLY_CONDUCT = "historical_only_conduct"
    CORRECTED_ALLEGATION = "corrected_allegation"
    DENIAL = "denial"
    DENIAL_FOLLOWED_BY_CORRECTION = "denial_followed_by_correction"
    COPIED_FORWARD_CORRECTION = "copied_forward_correction"
    UNRESOLVED_CONTRADICTORY_WITNESSES = "unresolved_contradictory_witnesses"
    PROFANITY_WITHOUT_PHYSICAL_THREAT = "profanity_without_physical_threat"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    QUALIFYING_VIOLENCE_UNKNOWN_DIRECTION = "qualifying_violence_unknown_direction"
    MIXED_DIRECTION_INCIDENT = "mixed_direction_incident"
    ADVERSARIAL_DENIAL_AS_AFFIRMED = "adversarial_denial_as_affirmed"
    ADVERSARIAL_ACCIDENTAL_AS_INTENTIONAL = "adversarial_accidental_as_intentional"
    ADVERSARIAL_HISTORICAL_AS_CURRENT = "adversarial_historical_as_current"
    ADVERSARIAL_NO_CONTACT_AS_CONTACT = "adversarial_no_contact_as_contact"
    ADVERSARIAL_OBJECT_AS_INTERPERSONAL = "adversarial_object_as_interpersonal"
    ADVERSARIAL_OMITTED_CORRECTION = "adversarial_omitted_correction"
    ADVERSARIAL_OMITTED_CONTRADICTION = "adversarial_omitted_contradiction"
    ADVERSARIAL_BROAD_EVIDENCE_REUSE = "adversarial_broad_evidence_reuse"


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


class DoctrineCompliance(str, Enum):
    COMPLIANT = "compliant"
    REJECTED_VIOLATION = "rejected_violation"
    BOUNDED_NOT_PROVABLE = "bounded_not_provable"


class AdversarialCondition(str, Enum):
    DENIAL_AS_AFFIRMED = "denial_as_affirmed"
    ACCIDENTAL_AS_INTENTIONAL = "accidental_as_intentional"
    HISTORICAL_AS_CURRENT = "historical_as_current"
    NO_CONTACT_AS_CONTACT = "no_contact_as_contact"
    OBJECT_AS_INTERPERSONAL = "object_as_interpersonal"
    OMITTED_CORRECTION = "omitted_correction"
    OMITTED_CONTRADICTION = "omitted_contradiction"
    BROAD_EVIDENCE_REUSE = "broad_evidence_reuse"


class ExpectedEvidence(EvaluationContract):
    excerpt: StrictStr
    supports: Tuple[MaterialAttribute, ...] = (
        MaterialAttribute.CONDUCT,
        MaterialAttribute.DIRECTION,
        MaterialAttribute.INTENTIONALITY,
        MaterialAttribute.TEMPORAL_SCOPE,
        MaterialAttribute.ASSERTION_STATUS,
    )

    @field_validator("excerpt")
    @classmethod
    def non_empty(cls, value: str) -> str:
        return _identifier(value, "excerpt")


class ExpectedOperationalFact(EvaluationContract):
    conduct: Optional[Conduct]
    direction: FactDirection = FactDirection.INTERPERSONAL
    intentionality: Intentionality = Intentionality.INTENTIONAL
    temporal_scope: TemporalScope = TemporalScope.CURRENT
    assertion_status: AssertionStatus = AssertionStatus.AFFIRMED
    resolution_status: ResolutionStatus = ResolutionStatus.ACTIVE
    uncertainty: Tuple[UncertaintyDimension, ...] = ()
    evidence: Tuple[ExpectedEvidence, ...]
    correction_of_fact: Optional[int] = Field(default=None, ge=0)
    contradiction_group: Optional[StrictStr] = None


class ExpectedEvaluationOutcome(EvaluationContract):
    semantic_outcome: ExpectedSemanticOutcome = ExpectedSemanticOutcome.SUCCESS
    deterministic_outcome: PolicyOutcome
    qualifying_conduct: Tuple[Conduct, ...] = ()
    incident_direction: IncidentDirection
    operational_facts: Tuple[ExpectedOperationalFact, ...]
    processing_status: ProcessingStatus = ProcessingStatus.SUCCESSFUL_ANALYSIS
    completeness_status: CompletenessStatus = CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS
    validation_failure_stage: ValidationFailureStage = ValidationFailureStage.NONE
    validation_issue_codes: Tuple[ValidationIssueCode, ...] = ()
    doctrine_compliance: DoctrineCompliance = DoctrineCompliance.COMPLIANT

    @model_validator(mode="after")
    def consistent(self) -> "ExpectedEvaluationOutcome":
        failed = self.processing_status != ProcessingStatus.SUCCESSFUL_ANALYSIS
        if failed != (self.semantic_outcome == ExpectedSemanticOutcome.FAILURE):
            raise ValueError("semantic outcome must match repository processing status")
        if failed and self.deterministic_outcome != PolicyOutcome.UNABLE_TO_DETERMINE:
            raise ValueError("failed processing requires Unable to Determine")
        if not failed and self.validation_failure_stage != ValidationFailureStage.NONE:
            raise ValueError("successful processing cannot have a validation failure stage")
        return self


class EvaluationCaseMetadata(EvaluationContract):
    primary_category: EvaluationCategory
    categories: Tuple[EvaluationCategory, ...] = ()
    documentation_quality_tags: Tuple[DocumentationQualityTag, ...] = ()
    engineering_notes: Optional[StrictStr] = None
    compound: StrictBool = False

    @model_validator(mode="after")
    def category_order(self) -> "EvaluationCaseMetadata":
        if self.categories and self.categories[0] != self.primary_category:
            raise ValueError("primary category must be first")
        return self


class EvaluationCase(EvaluationContract):
    case_id: StrictStr
    schema_version: StrictStr = "3.0.0"
    synthetic: StrictBool = True
    narrative: StrictStr
    metadata: EvaluationCaseMetadata
    adversarial_condition: Optional[AdversarialCondition] = None
    ground_truth: ExpectedEvaluationOutcome

    @field_validator("case_id", "schema_version", "narrative")
    @classmethod
    def identifiers(cls, value: str, info: Any) -> str:
        return _identifier(value, info.field_name)

    @model_validator(mode="after")
    def synthetic_only(self) -> "EvaluationCase":
        if self.synthetic is not True:
            raise ValueError("evaluation cases must be explicitly synthetic")
        return self


class FixtureExpectation(EvaluationContract):
    fixture_id: StrictStr
    expected_outcome: PolicyOutcome
    expected_conduct: Tuple[Conduct, ...]
    expected_direction: IncidentDirection
    expected_uncertainty: Tuple[UncertaintyDimension, ...]
    expected_processing_status: ProcessingStatus
    expected_completeness_status: CompletenessStatus


class EvaluationArtifactProvenance(EvaluationContract):
    evaluation_schema_version: StrictStr
    corpus_identity: StrictStr
    repository_commit: StrictStr
    model_identifier: Optional[StrictStr] = None
    extraction_configuration_identity: Optional[StrictStr] = None
    run_timestamp: datetime
    execution_mode: EvaluationExecutionMode


class ObservedEvaluationResult(EvaluationContract):
    case_id: StrictStr
    run_id: StrictStr
    provenance: EvaluationArtifactProvenance
    semantic_outcome: ObservedSemanticOutcome
    validation_outcome: ObservedValidationOutcome
    processing_status: ProcessingStatus
    completeness_status: CompletenessStatus
    deterministic_outcome: PolicyOutcome
    operational_facts: Tuple[ExpectedOperationalFact, ...] = ()


class FieldDifference(EvaluationContract):
    field: StrictStr
    expected_value: JsonValue = None
    observed_value: JsonValue = None
    classification: DifferenceClassification
    reason_code: DifferenceReasonCode
    explanation: Optional[StrictStr] = None

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

    @model_validator(mode="after")
    def status_invariants(self) -> "CaseEvaluationResult":
        differences = [item for item in self.field_differences if item.material]
        if self.status == CaseEvaluationStatus.MATCH and (differences or self.failure_patterns or self.non_comparable_reason):
            raise ValueError("match cannot carry mismatch evidence")
        if self.status == CaseEvaluationStatus.PARTIAL_MISMATCH and not differences:
            raise ValueError("partial mismatch requires differences")
        if self.status == CaseEvaluationStatus.FAILURE and not self.failure_patterns:
            raise ValueError("failure requires failure patterns")
        if self.status == CaseEvaluationStatus.NON_COMPARABLE and self.non_comparable_reason is None:
            raise ValueError("non-comparable requires a reason")
        return self


class BaselineComparisonObservation(EvaluationContract):
    code: BaselineObservationCode
    detail: StrictStr


class BaselineComparison(EvaluationContract):
    comparison_id: StrictStr
    prior_result_id: StrictStr
    current_result_id: StrictStr
    classification: BaselineClassification
    observations: List[BaselineComparisonObservation]
