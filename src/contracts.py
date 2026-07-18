from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictStr, field_validator, model_validator

from src.models import Incident, Intentionality, ViolenceEventType, ViolenceFinding


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
    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNSUPPORTED_FIELD = "unsupported_field"
    INVALID_EVENT_TYPE = "invalid_event_type"
    INVALID_INTENTIONALITY = "invalid_intentionality"
    INVALID_BOOLEAN = "invalid_boolean"
    INVALID_ACTOR = "invalid_actor"
    INVALID_TARGET = "invalid_target"
    INVALID_EVIDENCE_COLLECTION = "invalid_evidence_collection"
    INVALID_EVIDENCE_ITEM = "invalid_evidence_item"
    INVALID_CONFIDENCE_TYPE = "invalid_confidence_type"
    CONFIDENCE_OUT_OF_RANGE = "confidence_out_of_range"
    INVALID_UNCERTAINTY_COLLECTION = "invalid_uncertainty_collection"
    INVALID_UNCERTAINTY_ITEM = "invalid_uncertainty_item"
    VIOLENCE_WITH_EVENT_TYPE_NONE = "violence_with_event_type_none"
    PHYSICAL_EVENT_WITHOUT_VIOLENCE = "physical_event_without_violence"
    COMPLETED_VIOLENCE_WITHOUT_CONTACT = "completed_violence_without_contact"
    EVENT_TYPE_NONE_WITH_CONTACT = "event_type_none_with_contact"
    NONVIOLENT_NONACCIDENTAL_CONTACT = "nonviolent_nonaccidental_contact"
    NEGATED_CURRENT_AFFIRMATIVE_VIOLENCE = "negated_current_affirmative_violence"
    CONFLICT_WITHOUT_UNCERTAINTY = "conflict_without_uncertainty"
    EMPTY_EVIDENCE_ITEM = "empty_evidence_item"


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
    COMPATIBILITY_CONSTRUCTION_FAILED = "compatibility_construction_failed"
    UNSUPPORTED_POLICY_INPUT = "unsupported_policy_input"
    CONFLICTING_INFORMATION = "conflicting_information"
    THREAT_WITHOUT_VIOLENCE_INDICATION = "threat_without_violence_indication"
    UNCLEAR_EVENT_TYPE = "unclear_event_type"
    UNCLEAR_MATERIAL_INTENTIONALITY = "unclear_material_intentionality"
    MATERIAL_UNCERTAINTY_NOTES = "material_uncertainty_notes"
    NEGATED_AFFIRMATIVE_FINDING = "negated_affirmative_finding"
    AFFIRMATIVE_VIOLENCE_OR_THREAT = "affirmative_violence_or_threat"
    NO_VIOLENCE = "no_violence"
    NEGATED_NON_EVENT = "negated_non_event"
    CORRECTED_NON_EVENT = "corrected_non_event"


class PipelineFailureProvenance(str, Enum):
    INPUT_VALIDATION = "input_validation"
    PROVIDER_CONFIGURATION = "provider_configuration"
    PROVIDER_REQUEST = "provider_request"
    PROVIDER_STRUCTURED_RESPONSE = "provider_structured_response"
    PROVIDER_VALIDATION = "provider_validation"
    SCHEMA_VALIDATION = "schema_validation"
    DOMAIN_VALIDATION = "domain_validation"
    COMPATIBILITY_CONSTRUCTION = "compatibility_construction"
    UNSUPPORTED_POLICY_INPUT = "unsupported_policy_input"


class PolicyDecision(BaseModel):
    """Provider-independent application write disposition."""

    model_config = ConfigDict(strict=True, extra="forbid")

    policy_id: StrictStr
    policy_version: StrictStr
    outcome: PolicyOutcome
    reason_codes: List[PolicyReasonCode]
    explanation: StrictStr
    failure_provenance: Optional[PipelineFailureProvenance] = None

    @model_validator(mode="after")
    def require_consistent_decision(self) -> "PolicyDecision":
        if not self.reason_codes:
            raise ValueError("policy decision requires at least one reason code")
        if not self.explanation:
            raise ValueError("policy decision requires an explanation")
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
    model_config = ConfigDict(strict=True)

    code: InputFailureCode
    field: StrictStr
    message: StrictStr


class InputValidationResult(BaseModel):
    model_config = ConfigDict(strict=True)

    status: InputValidationStatus
    incident: Optional[Incident] = None
    issues: List[InputValidationIssue] = Field(default_factory=list)
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
    model_config = ConfigDict(strict=True)

    incident_id: StrictStr
    original_narrative: StrictStr
    normalized_narrative: StrictStr
    normalization_applied: StrictBool = False
    normalization_operations: List[NormalizationOperation] = Field(default_factory=list)

    @classmethod
    def from_incident(cls, incident: Incident) -> "NormalizedIncident":
        return cls(
            incident_id=incident.incident_id,
            original_narrative=incident.narrative,
            normalized_narrative=incident.narrative,
            normalization_applied=False,
            normalization_operations=[],
        )


class RegexResult(BaseModel):
    model_config = ConfigDict(strict=True)

    detected: StrictBool
    matched_terms: List[StrictStr]
    matched_patterns: List[StrictStr]

    @classmethod
    def from_legacy_dict(cls, value: Dict[str, object]) -> "RegexResult":
        return cls.model_validate(value)

    def to_legacy_dict(self) -> Dict[str, object]:
        return self.model_dump()


class SemanticFacts(BaseModel):
    """Provider-independent extracted facts; confidence remains provider-reported."""

    model_config = ConfigDict(strict=True, extra="forbid")

    violence_present: StrictBool
    event_type: ViolenceEventType
    actor: Optional[StrictStr]
    target: Optional[StrictStr]
    contact_occurred: StrictBool
    injury_mentioned: StrictBool
    current_event: StrictBool
    intentionality: Intentionality
    negated: StrictBool
    correction_present: StrictBool
    conflicting_information: StrictBool
    evidence_text: List[StrictStr]
    confidence: StrictFloat = Field(ge=0.0, le=1.0)
    uncertainty_notes: List[StrictStr]



class ProviderStructuredResponse(BaseModel):
    """OpenAI structured-output schema contained inside semantic extraction."""

    model_config = ConfigDict(strict=True, extra="forbid")

    violence_present: StrictBool
    event_type: ViolenceEventType
    actor: Optional[StrictStr]
    target: Optional[StrictStr]
    contact_occurred: StrictBool
    injury_mentioned: StrictBool
    current_event: StrictBool
    intentionality: Intentionality
    negated: StrictBool
    correction_present: StrictBool
    conflicting_information: StrictBool
    evidence_text: List[StrictStr]
    confidence: StrictFloat = Field(ge=0.0, le=1.0)
    uncertainty_notes: List[StrictStr]


class ValidationIssue(BaseModel):
    model_config = ConfigDict(strict=True)

    code: ValidationIssueCode
    field: StrictStr
    message: StrictStr


class SchemaValidationResult(BaseModel):
    model_config = ConfigDict(strict=True)

    status: SchemaValidationStatus
    issues: List[ValidationIssue] = Field(default_factory=list)
    semantic_facts: Optional[SemanticFacts] = None

    @model_validator(mode="after")
    def require_consistent_outcome(self) -> "SchemaValidationResult":
        if self.status == SchemaValidationStatus.PASSED and (self.semantic_facts is None or self.issues):
            raise ValueError("passed schema validation requires facts and no issues")
        if self.status == SchemaValidationStatus.FAILED and (self.semantic_facts is not None or not self.issues):
            raise ValueError("failed schema validation requires issues and no facts")
        if self.status == SchemaValidationStatus.NOT_RUN and (self.semantic_facts is not None or self.issues):
            raise ValueError("schema validation not-run state cannot contain facts or issues")
        return self

    @property
    def passed(self) -> bool:
        return self.status == SchemaValidationStatus.PASSED


class DomainValidationResult(BaseModel):
    model_config = ConfigDict(strict=True)

    status: DomainValidationStatus
    issues: List[ValidationIssue] = Field(default_factory=list)

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


class ValidatedSemanticFacts(BaseModel):
    """Admissibility carrier available only after both validation stages pass."""

    model_config = ConfigDict(strict=True)

    facts: SemanticFacts


class ValidationResult(BaseModel):
    model_config = ConfigDict(strict=True)

    schema_validation: SchemaValidationResult
    domain_validation: DomainValidationResult
    failure_stage: ValidationFailureStage
    validated_facts: Optional[ValidatedSemanticFacts] = None

    @model_validator(mode="after")
    def require_stage_consistency(self) -> "ValidationResult":
        if self.failure_stage == ValidationFailureStage.NOT_RUN:
            if (
                self.schema_validation.status != SchemaValidationStatus.NOT_RUN
                or self.domain_validation.status != DomainValidationStatus.NOT_RUN
                or self.validated_facts is not None
            ):
                raise ValueError("not-run validation cannot contain stage results or facts")
        elif self.failure_stage == ValidationFailureStage.NONE:
            if not self.schema_validation.passed or not self.domain_validation.passed or self.validated_facts is None:
                raise ValueError("successful validation requires both stages and validated facts")
        elif self.failure_stage == ValidationFailureStage.SCHEMA:
            if self.schema_validation.status != SchemaValidationStatus.FAILED:
                raise ValueError("schema failure stage requires failed schema validation")
            if self.domain_validation.status != DomainValidationStatus.NOT_RUN or self.validated_facts is not None:
                raise ValueError("schema failure cannot run domain validation or expose facts")
        elif self.failure_stage == ValidationFailureStage.DOMAIN:
            if not self.schema_validation.passed or self.domain_validation.status != DomainValidationStatus.FAILED:
                raise ValueError("domain failure requires passed schema and failed domain validation")
            if self.validated_facts is not None:
                raise ValueError("domain failure cannot expose validated facts")
        return self

    @property
    def passed(self) -> bool:
        return self.failure_stage == ValidationFailureStage.NONE


class SalesforcePayload(BaseModel):
    model_config = ConfigDict(strict=True)

    illustrative_incident_identifier: StrictStr
    illustrative_violence_detected: StrictBool
    illustrative_violence_event_type: StrictStr
    illustrative_actor: Optional[StrictStr]
    illustrative_target: Optional[StrictStr]
    illustrative_contact_occurred: StrictBool
    illustrative_injury_mentioned: StrictBool
    illustrative_current_event: StrictBool
    illustrative_intentionality: StrictStr
    illustrative_negation_present: StrictBool
    illustrative_correction_present: StrictBool
    illustrative_conflicting_information: StrictBool
    illustrative_confidence: StrictFloat = Field(ge=0.0, le=1.0)
    illustrative_evidence: List[StrictStr]
    illustrative_uncertainty_notes: List[StrictStr]
    illustrative_validation_status: StrictStr
    illustrative_write_disposition: StrictStr

    @classmethod
    def from_preview_dict(cls, value: Dict[str, object]) -> "SalesforcePayload":
        return cls(
            illustrative_incident_identifier=value["Illustrative_Incident_Identifier__c"],
            illustrative_violence_detected=value["Illustrative_Violence_Detected__c"],
            illustrative_violence_event_type=value["Illustrative_Violence_Event_Type__c"],
            illustrative_actor=value["Illustrative_Actor__c"],
            illustrative_target=value["Illustrative_Target__c"],
            illustrative_contact_occurred=value["Illustrative_Contact_Occurred__c"],
            illustrative_injury_mentioned=value["Illustrative_Injury_Mentioned__c"],
            illustrative_current_event=value["Illustrative_Current_Event__c"],
            illustrative_intentionality=value["Illustrative_Intentionality__c"],
            illustrative_negation_present=value["Illustrative_Negation_Present__c"],
            illustrative_correction_present=value["Illustrative_Correction_Present__c"],
            illustrative_conflicting_information=value["Illustrative_Conflicting_Information__c"],
            illustrative_confidence=value["Illustrative_Confidence__c"],
            illustrative_evidence=value["Illustrative_Evidence__c"],
            illustrative_uncertainty_notes=value["Illustrative_Uncertainty_Notes__c"],
            illustrative_validation_status=value["Illustrative_Validation_Status__c"],
            illustrative_write_disposition=value["Illustrative_Write_Disposition__c"],
        )

    def to_preview_dict(self) -> Dict[str, object]:
        return {
            "Illustrative_Incident_Identifier__c": self.illustrative_incident_identifier,
            "Illustrative_Violence_Detected__c": self.illustrative_violence_detected,
            "Illustrative_Violence_Event_Type__c": self.illustrative_violence_event_type,
            "Illustrative_Actor__c": self.illustrative_actor,
            "Illustrative_Target__c": self.illustrative_target,
            "Illustrative_Contact_Occurred__c": self.illustrative_contact_occurred,
            "Illustrative_Injury_Mentioned__c": self.illustrative_injury_mentioned,
            "Illustrative_Current_Event__c": self.illustrative_current_event,
            "Illustrative_Intentionality__c": self.illustrative_intentionality,
            "Illustrative_Negation_Present__c": self.illustrative_negation_present,
            "Illustrative_Correction_Present__c": self.illustrative_correction_present,
            "Illustrative_Conflicting_Information__c": self.illustrative_conflicting_information,
            "Illustrative_Confidence__c": self.illustrative_confidence,
            "Illustrative_Evidence__c": list(self.illustrative_evidence),
            "Illustrative_Uncertainty_Notes__c": list(self.illustrative_uncertainty_notes),
            "Illustrative_Validation_Status__c": self.illustrative_validation_status,
            "Illustrative_Write_Disposition__c": self.illustrative_write_disposition,
        }


class PipelineResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    incident: Incident
    normalized_incident: NormalizedIncident
    regex_result: RegexResult
    semantic_facts: Optional[SemanticFacts]
    validation_result: ValidationResult
    operational_finding: Optional[ViolenceFinding]
    policy_decision: PolicyDecision
    salesforce_payload: Optional[SalesforcePayload]
    presentation_payload: Dict[str, Any]
    signature: StrictStr

    @field_validator("presentation_payload")
    @classmethod
    def require_presentation_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value:
            raise ValueError("presentation_payload must not be empty")
        return value
