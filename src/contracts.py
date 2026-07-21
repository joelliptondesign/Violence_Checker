"""Strict contracts for the true-north incident-fact semantic boundary."""

from enum import Enum
from typing import Any, Dict, Optional

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
    VIOLENCE_DETECTED = "Violence Detected"
    NO_VIOLENCE_DETECTED = "No Violence Detected"
    UNCERTAIN = "Uncertain"
    UNABLE_TO_DETERMINE = "Unable to Determine"


class PolicyReasonCode(str, Enum):
    QUALIFYING_CURRENT_VIOLENCE = "qualifying_current_violence"
    NO_QUALIFYING_CURRENT_VIOLENCE = "no_qualifying_current_violence"
    MATERIAL_SEMANTIC_UNCERTAINTY = "material_semantic_uncertainty"
    UNRESOLVED_CONTRADICTION = "unresolved_contradiction"
    INCOMPLETE_ANALYSIS = "incomplete_analysis"
    PROVIDER_FAILURE = "provider_failure"
    SCHEMA_FAILURE = "schema_failure"
    VALIDATION_FAILURE = "validation_failure"
    PIPELINE_FAILURE = "pipeline_failure"
    MALFORMED_SEMANTIC_INPUT = "malformed_semantic_input"


class ProcessingStatus(str, Enum):
    SUCCESSFUL_ANALYSIS = "successful_analysis"
    PROVIDER_FAILURE = "provider_failure"
    SCHEMA_FAILURE = "schema_failure"
    VALIDATION_FAILURE = "validation_failure"
    PIPELINE_FAILURE = "pipeline_failure"


class CompletenessStatus(str, Enum):
    COMPLETE_ADMISSIBLE_ANALYSIS = "complete_admissible_analysis"
    INCOMPLETE_ANALYSIS = "incomplete_analysis"
    UNRESOLVED_SEMANTIC_CONTENT = "unresolved_semantic_content"


class PolicyDecision(BaseModel):
    """Repository-authored doctrinal outcome over validated incident facts."""

    model_config = ConfigDict(strict=True, extra="forbid")

    policy_id: StrictStr
    policy_version: StrictStr
    outcome: PolicyOutcome
    reason_codes: list[PolicyReasonCode]
    explanation: StrictStr

    @model_validator(mode="after")
    def require_consistent_decision(self) -> "PolicyDecision":
        if not self.reason_codes or not self.explanation.strip():
            raise ValueError("policy decision requires reason codes and an explanation")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("policy decision reason codes must be unique")
        allowed = {
            PolicyOutcome.VIOLENCE_DETECTED: {PolicyReasonCode.QUALIFYING_CURRENT_VIOLENCE},
            PolicyOutcome.NO_VIOLENCE_DETECTED: {PolicyReasonCode.NO_QUALIFYING_CURRENT_VIOLENCE},
            PolicyOutcome.UNCERTAIN: {
                PolicyReasonCode.MATERIAL_SEMANTIC_UNCERTAINTY,
                PolicyReasonCode.UNRESOLVED_CONTRADICTION,
            },
            PolicyOutcome.UNABLE_TO_DETERMINE: {
                PolicyReasonCode.INCOMPLETE_ANALYSIS,
                PolicyReasonCode.PROVIDER_FAILURE,
                PolicyReasonCode.SCHEMA_FAILURE,
                PolicyReasonCode.VALIDATION_FAILURE,
                PolicyReasonCode.PIPELINE_FAILURE,
                PolicyReasonCode.MALFORMED_SEMANTIC_INPUT,
            },
        }[self.outcome]
        if not set(self.reason_codes).issubset(allowed):
            raise ValueError("policy decision reason codes are incoherent with its outcome")
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


class IncidentDirection(str, Enum):
    INTERPERSONAL = "interpersonal"
    SELF_DIRECTED = "self_directed"
    OBJECT_DIRECTED = "object_directed"
    MULTIPLE = "multiple"
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


class DerivedContradictionGroup(BaseModel):
    """Deterministic membership view for one narrow contradiction group."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    contradiction_group: StrictStr
    fact_ids: tuple[StrictStr, ...]

    @field_validator("fact_ids")
    @classmethod
    def require_canonical_members(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) < 2 or len(value) != len(set(value)) or value != tuple(sorted(value)):
            raise ValueError("contradiction-group fact identifiers must be unique and canonical")
        return value


class DerivedSemanticView(BaseModel):
    """Repository-owned views derived without creating or rewriting semantic facts."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    incident_id: StrictStr
    active_fact_ids: tuple[StrictStr, ...]
    superseded_fact_ids: tuple[StrictStr, ...]
    contradiction_groups: tuple[DerivedContradictionGroup, ...]
    incident_direction: IncidentDirection


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
    processing_status: ProcessingStatus
    completeness_status: CompletenessStatus
    validated_envelope: Optional[TrueNorthSemanticEnvelope] = None
    derived_semantics: Optional[DerivedSemanticView] = None

    @model_validator(mode="after")
    def require_stage_consistency(self) -> "ValidationResult":
        if self.failure_stage == ValidationFailureStage.NOT_RUN:
            valid = (
                self.schema_validation.status == SchemaValidationStatus.NOT_RUN
                and self.domain_validation.status == DomainValidationStatus.NOT_RUN
                and self.validated_envelope is None
                and self.derived_semantics is None
                and self.processing_status == ProcessingStatus.PIPELINE_FAILURE
                and self.completeness_status == CompletenessStatus.INCOMPLETE_ANALYSIS
            )
        elif self.failure_stage == ValidationFailureStage.NONE:
            valid = (
                self.schema_validation.passed
                and self.domain_validation.passed
                and self.validated_envelope is not None
                and self.derived_semantics is not None
                and self.processing_status == ProcessingStatus.SUCCESSFUL_ANALYSIS
                and self.completeness_status in {
                    CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS,
                    CompletenessStatus.UNRESOLVED_SEMANTIC_CONTENT,
                }
            )
        elif self.failure_stage == ValidationFailureStage.SCHEMA:
            valid = (
                self.schema_validation.status == SchemaValidationStatus.FAILED
                and self.domain_validation.status == DomainValidationStatus.NOT_RUN
                and self.validated_envelope is None
                and self.derived_semantics is None
                and self.processing_status == ProcessingStatus.SCHEMA_FAILURE
                and self.completeness_status == CompletenessStatus.INCOMPLETE_ANALYSIS
            )
        else:
            valid = (
                self.schema_validation.passed
                and self.domain_validation.status == DomainValidationStatus.FAILED
                and self.validated_envelope is None
                and self.derived_semantics is None
                and self.processing_status == ProcessingStatus.VALIDATION_FAILURE
                and self.completeness_status == CompletenessStatus.INCOMPLETE_ANALYSIS
            )
        if valid and self.failure_stage == ValidationFailureStage.NONE:
            fact_ids = tuple(fact.fact_id for fact in self.validated_envelope.facts)
            derived_ids = self.derived_semantics.active_fact_ids + self.derived_semantics.superseded_fact_ids
            valid = (
                self.derived_semantics.incident_id == self.validated_envelope.incident_id
                and len(derived_ids) == len(set(derived_ids))
                and set(derived_ids) == set(fact_ids)
            )
        if not valid:
            raise ValueError("validation stage and results are inconsistent")
        return self

    @property
    def passed(self) -> bool:
        return self.failure_stage == ValidationFailureStage.NONE


class CommunicationFact(BaseModel):
    """Identifier-free operational fact projected from validated repository truth."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    conduct: Optional[Conduct]
    direction: FactDirection
    intentionality: Intentionality
    temporal_scope: TemporalScope
    assertion_status: AssertionStatus
    resolution_status: ResolutionStatus
    uncertainty: tuple[UncertaintyDimension, ...]
    evidence_excerpts: tuple[StrictStr, ...] = Field(min_length=1)


class OperatorCommunicationInput(BaseModel):
    """Minimal presentation-only projection with no provider or bookkeeping fields."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    outcome: PolicyOutcome
    incident_direction: IncidentDirection
    active_facts: tuple[CommunicationFact, ...]
    superseded_facts: tuple[CommunicationFact, ...]
    has_unresolved_contradiction: StrictBool


class OperatorCommunication(BaseModel):
    """Complete presentation-only communication surface."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    incident_summary: StrictStr = Field(min_length=1, max_length=500)
    key_findings: tuple[StrictStr, ...] = Field(min_length=1, max_length=8)
    why_this_result: StrictStr = Field(min_length=1, max_length=500)

    @field_validator("key_findings")
    @classmethod
    def require_concise_findings(cls, findings: tuple[str, ...]) -> tuple[str, ...]:
        if len({finding.casefold() for finding in findings}) != len(findings):
            raise ValueError("key findings must not contain duplicates")
        if any(not 2 <= len(finding.split()) <= 5 for finding in findings):
            raise ValueError("each key finding must contain 2 to 5 words")
        return findings

    @model_validator(mode="after")
    def prohibit_implementation_language(self) -> "OperatorCommunication":
        rendered = " ".join((self.incident_summary, *self.key_findings, self.why_this_result)).casefold()
        forbidden = (
            "assertion affirmed",
            "canonical id",
            "classifier concluded",
            "completeness status",
            "contradiction group",
            "deterministic processing",
            "model determined",
            "policy candidate",
            "processing status",
            "provider output",
            "reason code",
            "repository",
            "repository bookkeeping",
            "resolution active",
            "schema version",
            "semantic analysis",
            "semantic graph",
            "system determined",
            "temporal scope",
            "validated facts",
            "validation stage",
        )
        if any(term in rendered for term in forbidden):
            raise ValueError("operator communication cannot expose implementation language")
        return self


class PipelineResult(BaseModel):
    """True North application pipeline authority before presentation-only communication."""

    model_config = ConfigDict(strict=True, extra="forbid", arbitrary_types_allowed=True)

    incident: Incident
    normalized_incident: NormalizedIncident
    regex_result: Dict[str, Any]
    validation_result: ValidationResult
    policy_decision: PolicyDecision
    salesforce_payload: Optional[Dict[str, Any]] = None
    signature: StrictStr

    @model_validator(mode="after")
    def require_pipeline_consistency(self) -> "PipelineResult":
        if self.incident.incident_id != self.normalized_incident.incident_id:
            raise ValueError("pipeline incident identities must match")
        if self.validation_result.passed:
            envelope = self.validation_result.validated_envelope
            if envelope is None or envelope.incident_id != self.incident.incident_id:
                raise ValueError("validated semantic identity must match the pipeline incident")
        if self.policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE and self.salesforce_payload is not None:
            raise ValueError("unable-to-determine analysis cannot produce a Salesforce payload")
        return self
