"""Strict contracts for the true-north incident-fact semantic boundary."""

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator, model_validator

from src.models import Incident


class SchemaValidationStatus(str, Enum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"


class DomainValidationStatus(str, Enum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"


class ValidationFailureStage(str, Enum):
    NOT_RUN = "not_run"
    NONE = "none"
    SCHEMA = "schema"
    DOMAIN = "domain"


class ValidationIssueCode(str, Enum):
    INVALID_CANDIDATE_TYPE = "invalid_candidate_type"
    PROVIDER_OBJECT_NOT_ALLOWED = "provider_object_not_allowed"
    UNSUPPORTED_SCHEMA_IDENTITY = "unsupported_schema_identity"
    UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"
    INCIDENT_ID_MISMATCH = "incident_id_mismatch"
    INVALID_IDENTIFIER = "invalid_identifier"
    DUPLICATE_IDENTIFIER = "duplicate_identifier"
    INVALID_COLLECTION_ORDER = "invalid_collection_order"
    DANGLING_REFERENCE = "dangling_reference"
    INVALID_EVIDENCE_IDENTITY = "invalid_evidence_identity"
    EVIDENCE_NOT_CONTAINED = "evidence_not_contained"
    INVALID_EVIDENCE_SUPPORT = "invalid_evidence_support"
    MISSING_EVIDENCE_SUPPORT = "missing_evidence_support"
    INVALID_FACT_COMBINATION = "invalid_fact_combination"
    INVALID_UNCERTAINTY = "invalid_uncertainty"
    INVALID_CORRECTION_REFERENCE = "invalid_correction_reference"
    CORRECTION_CYCLE = "correction_cycle"
    INVALID_CONTRADICTION_GROUP = "invalid_contradiction_group"


class PolicyOutcome(str, Enum):
    WRITE_DETECTED = "WRITE_DETECTED"
    WRITE_UNCERTAIN = "WRITE_UNCERTAIN"
    WRITE_NOT_DETECTED = "WRITE_NOT_DETECTED"
    WRITE_FAILED = "WRITE_FAILED"


class PolicyReasonCode(str, Enum):
    INPUT_VALIDATION_FAILED = "input_validation_failed"
    PROVIDER_CONFIGURATION_FAILED = "provider_configuration_failed"
    PROVIDER_REQUEST_FAILED = "provider_request_failed"
    PROVIDER_STRUCTURED_RESPONSE_FAILED = "provider_structured_response_failed"
    PROVIDER_VALIDATION_FAILED = "provider_validation_failed"
    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
    DOMAIN_VALIDATION_FAILED = "domain_validation_failed"
    UNSUPPORTED_POLICY_INPUT = "unsupported_policy_input"
    CONFLICTING_INFORMATION = "conflicting_information"
    SCOPED_SEMANTIC_UNCERTAINTY = "scoped_semantic_uncertainty"
    AFFIRMED_CURRENT_INTERPERSONAL_VIOLENCE = "affirmed_current_interpersonal_violence"
    NO_ACTIVE_CURRENT_INTERPERSONAL_VIOLENCE = "no_active_current_interpersonal_violence"


class PipelineFailureProvenance(str, Enum):
    INPUT_VALIDATION = "input_validation"
    PROVIDER_CONFIGURATION = "provider_configuration"
    PROVIDER_REQUEST = "provider_request"
    PROVIDER_STRUCTURED_RESPONSE = "provider_structured_response"
    PROVIDER_VALIDATION = "provider_validation"
    SCHEMA_VALIDATION = "schema_validation"
    DOMAIN_VALIDATION = "domain_validation"
    UNSUPPORTED_POLICY_INPUT = "unsupported_policy_input"


class PolicyDecision(BaseModel):
    """Unchanged downstream policy contract retained for later migration."""

    model_config = ConfigDict(strict=True, extra="forbid")

    policy_id: StrictStr
    policy_version: StrictStr
    outcome: PolicyOutcome
    reason_codes: list[PolicyReasonCode]
    explanation: StrictStr
    failure_provenance: Optional[PipelineFailureProvenance] = None

    @model_validator(mode="after")
    def require_consistent_decision(self) -> "PolicyDecision":
        if not self.reason_codes or not self.explanation:
            raise ValueError("policy decision requires reason codes and an explanation")
        if self.outcome == PolicyOutcome.WRITE_FAILED and self.failure_provenance is None:
            raise ValueError("WRITE_FAILED requires failure provenance")
        if self.outcome != PolicyOutcome.WRITE_FAILED and self.failure_provenance is not None:
            raise ValueError("non-failure policy outcomes cannot contain failure provenance")
        return self


class InputValidationStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class InputFailureCode(str, Enum):
    INVALID_ENVELOPE_TYPE = "invalid_envelope_type"
    UNSUPPORTED_FIELD = "unsupported_field"
    MISSING_INCIDENT_ID = "missing_incident_id"
    INVALID_INCIDENT_ID_TYPE = "invalid_incident_id_type"
    EMPTY_INCIDENT_ID = "empty_incident_id"
    MISSING_NARRATIVE = "missing_narrative"
    INVALID_NARRATIVE_TYPE = "invalid_narrative_type"
    EMPTY_NARRATIVE = "empty_narrative"
    WHITESPACE_ONLY_NARRATIVE = "whitespace_only_narrative"
    NO_SUBSTANTIVE_CONTENT = "no_substantive_content"
    NULL_CHARACTER = "null_character"
    SURROGATE_CODE_POINT = "surrogate_code_point"
    NARRATIVE_TOO_LONG = "narrative_too_long"


class InputValidationIssue(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: InputFailureCode
    field: StrictStr
    message: StrictStr


class InputValidationResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    status: InputValidationStatus
    incident: Optional[Incident] = None
    issues: list[InputValidationIssue] = Field(default_factory=list)
    policy_decision: Optional[PolicyDecision] = None

    @model_validator(mode="after")
    def require_consistent_outcome(self) -> "InputValidationResult":
        if self.status == InputValidationStatus.SUCCESS and (self.incident is None or self.issues):
            raise ValueError("successful input validation requires an incident and no issues")
        if self.status == InputValidationStatus.FAILURE and (self.incident is not None or not self.issues):
            raise ValueError("failed input validation requires issues and no incident")
        return self

    @property
    def succeeded(self) -> bool:
        return self.status == InputValidationStatus.SUCCESS

    @property
    def failure_code(self) -> Optional[InputFailureCode]:
        return self.issues[0].code if self.issues else None

    @property
    def failure_message(self) -> Optional[str]:
        return self.issues[0].message if self.issues else None


class NormalizationOperation(str, Enum):
    REMOVE_LEADING_BOM = "remove_leading_bom"
    UNICODE_NFC = "unicode_nfc"
    LINE_ENDINGS_LF = "line_endings_lf"
    NON_BREAKING_SPACES = "non_breaking_spaces"
    HORIZONTAL_WHITESPACE = "horizontal_whitespace"
    EXCESSIVE_BLANK_LINES = "excessive_blank_lines"
    TRIM_BOUNDARY_WHITESPACE = "trim_boundary_whitespace"


class NormalizedIncident(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    incident_id: StrictStr
    original_narrative: StrictStr
    normalized_narrative: StrictStr
    normalization_applied: StrictBool = False
    normalization_operations: list[NormalizationOperation] = Field(default_factory=list)

    @classmethod
    def from_incident(cls, incident: Incident) -> "NormalizedIncident":
        return cls(
            incident_id=incident.incident_id,
            original_narrative=incident.narrative,
            normalized_narrative=incident.narrative,
        )


class RegexResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    detected: StrictBool
    matched_terms: list[StrictStr]
    matched_patterns: list[StrictStr]

    @classmethod
    def from_legacy_dict(cls, value: Dict[str, object]) -> "RegexResult":
        return cls.model_validate(value)

    def to_legacy_dict(self) -> Dict[str, object]:
        return self.model_dump()


SEMANTIC_SCHEMA_IDENTITY = "violence-checker.true-north-incident-facts"
SEMANTIC_SCHEMA_VERSION = "1.0.0"
EXTRACTION_CONTRACT_IDENTITY = "violence-checker.true-north-fact-extraction@1.0.0"


class Conduct(str, Enum):
    VERBAL_THREAT = "verbal_threat"
    PHYSICAL_ATTEMPT = "physical_attempt"
    PHYSICAL_CONTACT = "physical_contact"
    SELF_HARM = "self_harm"
    PROPERTY_VIOLENCE = "property_violence"


class FactDirection(str, Enum):
    INTERPERSONAL = "interpersonal"
    SELF_DIRECTED = "self_directed"
    OBJECT_DIRECTED = "object_directed"
    UNKNOWN = "unknown"


class Intentionality(str, Enum):
    INTENTIONAL = "intentional"
    ACCIDENTAL = "accidental"
    UNRESOLVED = "unresolved"


class TemporalScope(str, Enum):
    CURRENT = "current"
    HISTORICAL = "historical"
    UNRESOLVED = "unresolved"


class AssertionStatus(str, Enum):
    AFFIRMED = "affirmed"
    DENIED = "denied"
    DISPUTED = "disputed"
    UNRESOLVED = "unresolved"


class ResolutionStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class MaterialAttribute(str, Enum):
    CONDUCT = "conduct"
    DIRECTION = "direction"
    INTENTIONALITY = "intentionality"
    TEMPORAL_SCOPE = "temporal_scope"
    ASSERTION_STATUS = "assertion_status"
    RESOLUTION_STATUS = "resolution_status"
    SUPERSESSION = "supersession"
    CONTRADICTION = "contradiction"


class UncertaintyDimension(str, Enum):
    CONDUCT = "conduct"
    DIRECTION = "direction"
    INTENTIONALITY = "intentionality"
    TEMPORAL_SCOPE = "temporal_scope"
    ASSERTION_STATUS = "assertion_status"


class FactEvidence(BaseModel):
    """Repository-identified exact evidence linked to one fact only."""

    model_config = ConfigDict(strict=True, extra="forbid")

    evidence_id: StrictStr
    excerpt: StrictStr
    supports: list[MaterialAttribute]
    start_offset: Optional[int] = Field(default=None, ge=0)
    end_offset: Optional[int] = Field(default=None, ge=0)

    @field_validator("excerpt")
    @classmethod
    def require_non_empty_excerpt(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence excerpt must not be empty")
        return value

    @field_validator("supports")
    @classmethod
    def require_unique_supports(cls, value: list[MaterialAttribute]) -> list[MaterialAttribute]:
        if not value:
            raise ValueError("evidence supports must not be empty")
        if len(value) != len(set(value)):
            raise ValueError("evidence supports must be unique")
        return value

    @model_validator(mode="after")
    def require_complete_offset_pair(self) -> "FactEvidence":
        if (self.start_offset is None) != (self.end_offset is None):
            raise ValueError("evidence offsets must be supplied together")
        if self.start_offset is not None and self.end_offset <= self.start_offset:
            raise ValueError("evidence end offset must follow start offset")
        return self


class IncidentFact(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    fact_id: StrictStr
    conduct: Optional[Conduct]
    direction: FactDirection
    intentionality: Intentionality
    temporal_scope: TemporalScope
    assertion_status: AssertionStatus
    resolution_status: ResolutionStatus
    evidence: list[FactEvidence]
    uncertainty: list[UncertaintyDimension]
    supersedes_fact_id: Optional[StrictStr] = None
    contradiction_group: Optional[StrictStr] = None

    @field_validator("evidence")
    @classmethod
    def require_evidence(cls, value: list[FactEvidence]) -> list[FactEvidence]:
        if not value:
            raise ValueError("every semantic fact requires evidence")
        return value

    @field_validator("uncertainty")
    @classmethod
    def require_unique_uncertainty(cls, value: list[UncertaintyDimension]) -> list[UncertaintyDimension]:
        if len(value) != len(set(value)):
            raise ValueError("uncertainty dimensions must be unique")
        return value


class TrueNorthSemanticEnvelope(BaseModel):
    """Provider-independent semantic truth; bookkeeping is repository-authored."""

    model_config = ConfigDict(strict=True, extra="forbid")

    schema_identity: StrictStr
    schema_version: StrictStr
    extraction_contract_identity: StrictStr
    incident_id: StrictStr
    facts: list[IncidentFact]


class ProviderFactEvidenceCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    excerpt: StrictStr
    supports: list[MaterialAttribute]
    start_offset: Optional[int] = Field(default=None, ge=0)
    end_offset: Optional[int] = Field(default=None, ge=0)

    @field_validator("excerpt")
    @classmethod
    def require_non_empty_excerpt(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence excerpt must not be empty")
        return value

    @field_validator("supports")
    @classmethod
    def require_unique_supports(cls, value: list[MaterialAttribute]) -> list[MaterialAttribute]:
        if not value or len(value) != len(set(value)):
            raise ValueError("evidence supports must be non-empty and unique")
        return value

    @model_validator(mode="after")
    def require_complete_offset_pair(self) -> "ProviderFactEvidenceCandidate":
        if (self.start_offset is None) != (self.end_offset is None):
            raise ValueError("evidence offsets must be supplied together")
        if self.start_offset is not None and self.end_offset <= self.start_offset:
            raise ValueError("evidence end offset must follow start offset")
        return self


class ProviderFactCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    local_ref: StrictStr
    conduct: Optional[Conduct]
    direction: FactDirection
    intentionality: Intentionality
    temporal_scope: TemporalScope
    assertion_status: AssertionStatus
    resolution_status: ResolutionStatus
    evidence: list[ProviderFactEvidenceCandidate]
    uncertainty: list[UncertaintyDimension]
    supersedes_local_ref: Optional[StrictStr] = None
    contradiction_group_local_ref: Optional[StrictStr] = None

    @field_validator("local_ref", "supersedes_local_ref", "contradiction_group_local_ref")
    @classmethod
    def require_present_local_refs(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("provider local references must not be empty")
        return value

    @field_validator("evidence")
    @classmethod
    def require_evidence(cls, value: list[ProviderFactEvidenceCandidate]) -> list[ProviderFactEvidenceCandidate]:
        if not value:
            raise ValueError("every provider fact requires evidence")
        return value

    @field_validator("uncertainty")
    @classmethod
    def require_unique_uncertainty(cls, value: list[UncertaintyDimension]) -> list[UncertaintyDimension]:
        if len(value) != len(set(value)):
            raise ValueError("uncertainty dimensions must be unique")
        return value


class ProviderStructuredResponse(BaseModel):
    """Provider-authored operational facts with temporary references only."""

    model_config = ConfigDict(strict=True, extra="forbid")

    facts: list[ProviderFactCandidate]

    @model_validator(mode="after")
    def require_unique_fact_references(self) -> "ProviderStructuredResponse":
        refs = [fact.local_ref for fact in self.facts]
        if len(refs) != len(set(refs)):
            raise ValueError("provider fact local references must be unique")
        return self


class ValidationIssue(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: ValidationIssueCode
    field: StrictStr
    message: StrictStr


class SchemaValidationResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    status: SchemaValidationStatus
    issues: list[ValidationIssue] = Field(default_factory=list)
    semantic_envelope: Optional[TrueNorthSemanticEnvelope] = None

    @model_validator(mode="after")
    def require_consistent_outcome(self) -> "SchemaValidationResult":
        if self.status == SchemaValidationStatus.PASSED and (self.semantic_envelope is None or self.issues):
            raise ValueError("passed schema validation requires an envelope and no issues")
        if self.status == SchemaValidationStatus.FAILED and (self.semantic_envelope is not None or not self.issues):
            raise ValueError("failed schema validation requires issues and no envelope")
        if self.status == SchemaValidationStatus.NOT_RUN and (self.semantic_envelope is not None or self.issues):
            raise ValueError("schema validation not-run state cannot contain results")
        return self

    @property
    def passed(self) -> bool:
        return self.status == SchemaValidationStatus.PASSED


class DomainValidationResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    status: DomainValidationStatus
    issues: list[ValidationIssue] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_consistent_outcome(self) -> "DomainValidationResult":
        if self.status == DomainValidationStatus.PASSED and self.issues:
            raise ValueError("passed domain validation cannot contain issues")
        if self.status == DomainValidationStatus.FAILED and not self.issues:
            raise ValueError("failed domain validation requires issues")
        if self.status == DomainValidationStatus.NOT_RUN and self.issues:
            raise ValueError("domain validation not-run state cannot contain issues")
        return self

    @property
    def passed(self) -> bool:
        return self.status == DomainValidationStatus.PASSED


class ValidationResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    schema_validation: SchemaValidationResult
    domain_validation: DomainValidationResult
    failure_stage: ValidationFailureStage
    validated_envelope: Optional[TrueNorthSemanticEnvelope] = None

    @model_validator(mode="after")
    def require_stage_consistency(self) -> "ValidationResult":
        if self.failure_stage == ValidationFailureStage.NOT_RUN:
            valid = (
                self.schema_validation.status == SchemaValidationStatus.NOT_RUN
                and self.domain_validation.status == DomainValidationStatus.NOT_RUN
                and self.validated_envelope is None
            )
        elif self.failure_stage == ValidationFailureStage.NONE:
            valid = self.schema_validation.passed and self.domain_validation.passed and self.validated_envelope is not None
        elif self.failure_stage == ValidationFailureStage.SCHEMA:
            valid = (
                self.schema_validation.status == SchemaValidationStatus.FAILED
                and self.domain_validation.status == DomainValidationStatus.NOT_RUN
                and self.validated_envelope is None
            )
        else:
            valid = (
                self.schema_validation.passed
                and self.domain_validation.status == DomainValidationStatus.FAILED
                and self.validated_envelope is None
            )
        if not valid:
            raise ValueError("validation stage and results are inconsistent")
        return self

    @property
    def passed(self) -> bool:
        return self.failure_stage == ValidationFailureStage.NONE
