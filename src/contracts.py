from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictStr, field_validator, model_validator

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
    UNSUPPORTED_SCHEMA_IDENTITY = "unsupported_schema_identity"
    UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"
    INCIDENT_ID_MISMATCH = "incident_id_mismatch"
    INVALID_IDENTIFIER = "invalid_identifier"
    DUPLICATE_IDENTIFIER = "duplicate_identifier"
    INVALID_COLLECTION_ORDER = "invalid_collection_order"
    DANGLING_REFERENCE = "dangling_reference"
    INVALID_TARGET_REFERENCE = "invalid_target_reference"
    INVALID_RELATIONSHIP = "invalid_relationship"
    RELATIONSHIP_CYCLE = "relationship_cycle"
    INVALID_UNCERTAINTY = "invalid_uncertainty"
    INVALID_EVIDENCE_SUPPORT = "invalid_evidence_support"
    EVIDENCE_NOT_CONTAINED = "evidence_not_contained"
    MISSING_EVIDENCE_SUPPORT = "missing_evidence_support"
    INVALID_CONDUCT_COMBINATION = "invalid_conduct_combination"


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
    model_config = ConfigDict(strict=True, extra="forbid")

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
    model_config = ConfigDict(strict=True, extra="forbid")

    detected: StrictBool
    matched_terms: List[StrictStr]
    matched_patterns: List[StrictStr]

    @classmethod
    def from_legacy_dict(cls, value: Dict[str, object]) -> "RegexResult":
        return cls.model_validate(value)

    def to_legacy_dict(self) -> Dict[str, object]:
        return self.model_dump()


SEMANTIC_SCHEMA_IDENTITY = "violence-checker.proposition-semantics"
SEMANTIC_SCHEMA_VERSION = "1.0.0"
EXTRACTION_CONTRACT_IDENTITY = "violence-checker.proposition-extraction@1.0.0"
POLICY_CANDIDATE_SCHEMA_IDENTITY = "violence-checker.policy-candidate"
POLICY_CANDIDATE_SCHEMA_VERSION = "1.0.0"


class EntityKind(str, Enum):
    PERSON = "person"
    PEOPLE_COLLECTIVE = "people_collective"
    OBJECT = "object"
    UNSPECIFIED = "unspecified"


class ConductKind(str, Enum):
    PHYSICAL_CONDUCT = "physical_conduct"
    THREAT_EXPRESSION = "threat_expression"
    THREATENING_MOVEMENT = "threatening_movement"
    CONTACT_ONLY = "contact_only"
    UNDETERMINED = "undetermined"


class TargetKind(str, Enum):
    ENTITY = "entity"
    SELF = "self"
    NONE = "none"
    UNDETERMINED = "undetermined"


class Direction(str, Enum):
    INTERPERSONAL = "interpersonal"
    OBJECT_DIRECTED = "object-directed"
    SELF_DIRECTED = "self-directed"
    UNDETERMINED = "undetermined"


class Completion(str, Enum):
    THREATENED = "threatened"
    ATTEMPTED = "attempted"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"
    UNDETERMINED = "undetermined"


class Contact(str, Enum):
    OCCURRED = "occurred"
    DID_NOT_OCCUR = "did_not_occur"
    UNDETERMINED = "undetermined"
    NOT_APPLICABLE = "not_applicable"


class TemporalScope(str, Enum):
    CURRENT_INCIDENT = "current_incident"
    HISTORICAL = "historical"
    UNDETERMINED = "undetermined"


class AssertionStatus(str, Enum):
    AFFIRMED = "affirmed"
    NEGATED = "negated"
    UNCERTAIN = "uncertain"


class SemanticIntentionality(str, Enum):
    INTENTIONAL = "intentional"
    ACCIDENTAL = "accidental"
    UNDETERMINED = "undetermined"
    NOT_APPLICABLE = "not_applicable"


class RelationshipKind(str, Enum):
    NEGATES = "negates"
    SUPERSEDES = "supersedes"
    CONFLICTS_WITH = "conflicts_with"


class UncertaintyDimension(str, Enum):
    ACTOR_IDENTITY = "actor_identity"
    TARGET_IDENTITY = "target_identity"
    CONDUCT_TYPE = "conduct_type"
    DIRECTION = "direction"
    CONTACT = "contact"
    COMPLETION = "completion"
    INTENTIONALITY = "intentionality"
    TEMPORAL_SCOPE = "temporal_scope"
    THREAT_MEANING = "threat_meaning"
    ASSERTION_STATUS = "assertion_status"


class EvidenceSubjectKind(str, Enum):
    PROPOSITION = "proposition"
    RELATIONSHIP = "relationship"
    UNCERTAINTY = "uncertainty"


class EvidenceSupportRole(str, Enum):
    SUPPORTS_ASSERTION = "supports_assertion"
    SUPPORTS_NEGATION = "supports_negation"
    SUPPORTS_SUPERSESSION = "supports_supersession"
    SUPPORTS_CONFLICT = "supports_conflict"
    SUPPORTS_UNCERTAINTY = "supports_uncertainty"


class AttributionSourceKind(str, Enum):
    PATIENT = "patient"
    STAFF = "staff"
    WITNESS = "witness"
    UNSPECIFIED = "unspecified"


class EntityReference(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    entity_id: StrictStr
    entity_kind: EntityKind
    label: Optional[StrictStr] = None


class PropositionTarget(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    target_kind: TargetKind
    target_ref: Optional[StrictStr] = None

    @model_validator(mode="after")
    def require_reference_shape(self) -> "PropositionTarget":
        if self.target_kind == TargetKind.ENTITY and self.target_ref is None:
            raise ValueError("entity target requires target_ref")
        if self.target_kind != TargetKind.ENTITY and self.target_ref is not None:
            raise ValueError("only entity target may contain target_ref")
        return self


class Attribution(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    source_kind: AttributionSourceKind
    source_ref: Optional[StrictStr] = None


class ViolenceProposition(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    proposition_id: StrictStr
    actor_ref: StrictStr
    conduct_kind: ConductKind
    target: PropositionTarget
    completion: Completion
    contact: Contact
    temporal_scope: TemporalScope
    intentionality: SemanticIntentionality
    assertion_status: AssertionStatus
    attribution: Optional[Attribution] = None


class SemanticRelationship(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    relationship_id: StrictStr
    relationship_kind: RelationshipKind
    source_proposition_ref: StrictStr
    target_proposition_ref: StrictStr
    disputed_dimensions: List[UncertaintyDimension]


class SemanticUncertainty(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    uncertainty_id: StrictStr
    proposition_ref: StrictStr
    dimension: UncertaintyDimension
    note: Optional[StrictStr] = None


class EvidenceExcerpt(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    evidence_id: StrictStr
    text: StrictStr


class EvidenceSupport(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    support_id: StrictStr
    evidence_ref: StrictStr
    subject_kind: EvidenceSubjectKind
    subject_ref: StrictStr
    role: EvidenceSupportRole


class ExtractionMetadata(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    extraction_contract_identity: StrictStr = Field(
        description="Required non-empty extraction contract identity; use violence-checker.proposition-extraction@1.0.0."
    )
    provider_name: Optional[StrictStr] = None
    model_identifier: Optional[StrictStr] = None
    request_id: Optional[StrictStr] = None
    provider_confidence: Optional[StrictFloat] = Field(default=None, ge=0.0, le=1.0)

    @field_validator(
        "extraction_contract_identity",
        "provider_name",
        "model_identifier",
        "request_id",
    )
    @classmethod
    def require_present_identifiers_to_be_non_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("extraction provenance identifiers must not be empty")
        return value


class ViolenceSemanticEnvelope(BaseModel):
    """Sole provider-independent current semantic authority."""

    model_config = ConfigDict(strict=True, extra="forbid")

    schema_identity: StrictStr
    schema_version: StrictStr
    incident_id: StrictStr
    entities: List[EntityReference]
    propositions: List[ViolenceProposition]
    relationships: List[SemanticRelationship]
    uncertainties: List[SemanticUncertainty]
    evidence_excerpts: List[EvidenceExcerpt]
    evidence_supports: List[EvidenceSupport]
    extraction_metadata: ExtractionMetadata


class ProviderEntityCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    local_ref: StrictStr
    entity_kind: EntityKind
    label: Optional[StrictStr] = None


class ProviderTargetCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    target_kind: TargetKind = Field(
        description="Use entity exactly when target_ref names a provider entity; use self or undetermined only with a null target_ref."
    )
    target_ref: Optional[StrictStr] = Field(
        default=None,
        description="Provider-local entity reference required for entity targets and forbidden for self or undetermined targets.",
    )

    @model_validator(mode="after")
    def require_reference_shape(self) -> "ProviderTargetCandidate":
        if self.target_kind == TargetKind.ENTITY and self.target_ref is None:
            raise ValueError("entity target requires target_ref")
        if self.target_kind != TargetKind.ENTITY and self.target_ref is not None:
            raise ValueError("only entity target may contain target_ref")
        return self


class ProviderAttributionCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    source_kind: AttributionSourceKind
    source_ref: Optional[StrictStr] = None


class ProviderPropositionCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    local_ref: StrictStr
    actor_ref: StrictStr
    conduct_kind: ConductKind = Field(
        description="Semantic conduct category; it must use the completion and contact tuple required by the extraction instructions."
    )
    target: ProviderTargetCandidate
    completion: Completion = Field(
        description="Physical conduct: attempted, completed, or undetermined; contact-only: completed; threat expression: threatened or undetermined; threatening movement: not_applicable or undetermined."
    )
    contact: Contact = Field(
        description="Attempted physical conduct: did_not_occur; completed physical conduct or contact-only: occurred; threat expression: not_applicable."
    )
    temporal_scope: TemporalScope
    intentionality: SemanticIntentionality
    assertion_status: AssertionStatus
    attribution: Optional[ProviderAttributionCandidate] = None

    @model_validator(mode="after")
    def require_admissible_conduct_shape(self) -> "ProviderPropositionCandidate":
        if self.conduct_kind == ConductKind.THREAT_EXPRESSION:
            if self.completion not in {Completion.THREATENED, Completion.UNDETERMINED} or self.contact != Contact.NOT_APPLICABLE:
                raise ValueError("threat expression requires threatened or undetermined completion and not-applicable contact")
        elif self.conduct_kind == ConductKind.PHYSICAL_CONDUCT:
            if self.completion not in {Completion.ATTEMPTED, Completion.COMPLETED, Completion.UNDETERMINED}:
                raise ValueError("physical conduct has invalid completion")
            if self.completion == Completion.ATTEMPTED and self.contact != Contact.DID_NOT_OCCUR:
                raise ValueError("attempted physical conduct requires did-not-occur contact")
            if self.completion == Completion.COMPLETED and self.contact != Contact.OCCURRED:
                raise ValueError("completed physical conduct requires occurred contact")
        elif self.conduct_kind == ConductKind.CONTACT_ONLY:
            if self.completion != Completion.COMPLETED or self.contact != Contact.OCCURRED:
                raise ValueError("contact-only conduct requires completed and occurred")
        elif self.conduct_kind == ConductKind.THREATENING_MOVEMENT:
            if self.completion not in {Completion.NOT_APPLICABLE, Completion.UNDETERMINED}:
                raise ValueError("threatening movement cannot be attempted or completed conduct")
        if self.intentionality == SemanticIntentionality.ACCIDENTAL and self.conduct_kind not in {ConductKind.CONTACT_ONLY, ConductKind.PHYSICAL_CONDUCT}:
            raise ValueError("accidental intentionality is limited to contact or physical conduct")
        return self


class ProviderRelationshipCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    local_ref: StrictStr
    relationship_kind: RelationshipKind
    source_proposition_ref: StrictStr
    target_proposition_ref: StrictStr
    disputed_dimensions: List[UncertaintyDimension]


class ProviderUncertaintyCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    local_ref: StrictStr
    proposition_ref: StrictStr
    dimension: UncertaintyDimension
    note: Optional[StrictStr] = None


class ProviderEvidenceCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    local_ref: StrictStr
    text: StrictStr


class ProviderEvidenceSupportCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    evidence_ref: StrictStr
    subject_kind: EvidenceSubjectKind
    subject_ref: StrictStr
    role: EvidenceSupportRole

    @model_validator(mode="after")
    def require_role_allowed_for_subject_kind(self) -> "ProviderEvidenceSupportCandidate":
        allowed = {
            EvidenceSubjectKind.PROPOSITION: {EvidenceSupportRole.SUPPORTS_ASSERTION, EvidenceSupportRole.SUPPORTS_NEGATION},
            EvidenceSubjectKind.RELATIONSHIP: {EvidenceSupportRole.SUPPORTS_NEGATION, EvidenceSupportRole.SUPPORTS_SUPERSESSION, EvidenceSupportRole.SUPPORTS_CONFLICT},
            EvidenceSubjectKind.UNCERTAINTY: {EvidenceSupportRole.SUPPORTS_UNCERTAINTY},
        }[self.subject_kind]
        if self.role not in allowed:
            raise ValueError("evidence role is not allowed for provider subject kind")
        return self


class ProviderStructuredResponse(BaseModel):
    """Strict provider-only semantic candidates; all local references terminate at the adapter."""

    model_config = ConfigDict(strict=True, extra="forbid")

    entities: List[ProviderEntityCandidate]
    propositions: List[ProviderPropositionCandidate]
    relationships: List[ProviderRelationshipCandidate]
    uncertainties: List[ProviderUncertaintyCandidate]
    evidence_excerpts: List[ProviderEvidenceCandidate]
    evidence_supports: List[ProviderEvidenceSupportCandidate] = Field(
        description="Must contain at least one coherent evidence support for every proposition, relationship, and uncertainty."
    )

    @model_validator(mode="before")
    @classmethod
    def discard_obsolete_repository_metadata(cls, value: object) -> object:
        """Accept legacy callers without restoring provider metadata authority."""
        if isinstance(value, dict) and "extraction_metadata" in value:
            value = {key: item for key, item in value.items() if key != "extraction_metadata"}
        return value

    @field_validator(
        "entities",
        "propositions",
        "relationships",
        "uncertainties",
        "evidence_excerpts",
    )
    @classmethod
    def require_unique_local_references(cls, value: List[BaseModel]) -> List[BaseModel]:
        references = [item.local_ref for item in value]
        if any(not reference.strip() for reference in references):
            raise ValueError("provider local references must not be empty")
        if len(references) != len(set(references)):
            raise ValueError("provider local references must be unique within each collection")
        return value

    @model_validator(mode="after")
    def require_admissible_uncertainty_and_support(self) -> "ProviderStructuredResponse":
        entities = {item.local_ref: item for item in self.entities}
        propositions = {item.local_ref: item for item in self.propositions}
        relationships = {item.local_ref: item for item in self.relationships}
        uncertainties = {item.local_ref: item for item in self.uncertainties}
        conflict_dimensions: Dict[str, set[UncertaintyDimension]] = {}
        for relationship in self.relationships:
            if relationship.relationship_kind == RelationshipKind.CONFLICTS_WITH:
                for reference in (relationship.source_proposition_ref, relationship.target_proposition_ref):
                    conflict_dimensions.setdefault(reference, set()).update(relationship.disputed_dimensions)

        for uncertainty in self.uncertainties:
            proposition = propositions.get(uncertainty.proposition_ref)
            if proposition is None or proposition.actor_ref not in entities:
                continue
            target_entity = entities.get(proposition.target.target_ref) if proposition.target.target_ref else None
            if proposition.target.target_kind == TargetKind.SELF:
                direction = Direction.SELF_DIRECTED
            elif proposition.target.target_kind != TargetKind.ENTITY or target_entity is None:
                direction = Direction.UNDETERMINED
            elif target_entity.entity_kind == EntityKind.OBJECT:
                direction = Direction.OBJECT_DIRECTED
            elif target_entity.entity_kind in {EntityKind.PERSON, EntityKind.PEOPLE_COLLECTIVE} and proposition.actor_ref != proposition.target.target_ref and entities[proposition.actor_ref].entity_kind != EntityKind.UNSPECIFIED:
                direction = Direction.INTERPERSONAL
            else:
                direction = Direction.UNDETERMINED
            unresolved = {
                UncertaintyDimension.ACTOR_IDENTITY: entities[proposition.actor_ref].entity_kind == EntityKind.UNSPECIFIED,
                UncertaintyDimension.TARGET_IDENTITY: proposition.target.target_kind == TargetKind.UNDETERMINED or (target_entity is not None and target_entity.entity_kind == EntityKind.UNSPECIFIED),
                UncertaintyDimension.CONDUCT_TYPE: proposition.conduct_kind == ConductKind.UNDETERMINED,
                UncertaintyDimension.DIRECTION: direction == Direction.UNDETERMINED,
                UncertaintyDimension.CONTACT: proposition.contact == Contact.UNDETERMINED,
                UncertaintyDimension.COMPLETION: proposition.completion == Completion.UNDETERMINED,
                UncertaintyDimension.INTENTIONALITY: proposition.intentionality == SemanticIntentionality.UNDETERMINED,
                UncertaintyDimension.TEMPORAL_SCOPE: proposition.temporal_scope == TemporalScope.UNDETERMINED,
                UncertaintyDimension.THREAT_MEANING: proposition.conduct_kind in {ConductKind.THREAT_EXPRESSION, ConductKind.THREATENING_MOVEMENT, ConductKind.UNDETERMINED},
                UncertaintyDimension.ASSERTION_STATUS: proposition.assertion_status == AssertionStatus.UNCERTAIN,
            }[uncertainty.dimension]
            disputed = uncertainty.dimension in conflict_dimensions.get(proposition.local_ref, set())
            if not unresolved and not disputed:
                raise ValueError("provider uncertainty must identify an unresolved or disputed dimension")

        for support in self.evidence_supports:
            if support.subject_kind == EvidenceSubjectKind.PROPOSITION:
                subject = propositions.get(support.subject_ref)
                if subject is None:
                    continue
                expected = EvidenceSupportRole.SUPPORTS_NEGATION if subject.assertion_status == AssertionStatus.NEGATED else EvidenceSupportRole.SUPPORTS_ASSERTION
            elif support.subject_kind == EvidenceSubjectKind.RELATIONSHIP:
                subject = relationships.get(support.subject_ref)
                if subject is None:
                    continue
                expected = {
                    RelationshipKind.NEGATES: EvidenceSupportRole.SUPPORTS_NEGATION,
                    RelationshipKind.SUPERSEDES: EvidenceSupportRole.SUPPORTS_SUPERSESSION,
                    RelationshipKind.CONFLICTS_WITH: EvidenceSupportRole.SUPPORTS_CONFLICT,
                }[subject.relationship_kind]
            else:
                if support.subject_ref not in uncertainties:
                    continue
                expected = EvidenceSupportRole.SUPPORTS_UNCERTAINTY
            if support.role != expected:
                raise ValueError("provider evidence role is incoherent with its referenced subject")

        supported = {(item.subject_kind, item.subject_ref) for item in self.evidence_supports}
        required = (
            {(EvidenceSubjectKind.PROPOSITION, item.local_ref) for item in self.propositions}
            | {(EvidenceSubjectKind.RELATIONSHIP, item.local_ref) for item in self.relationships}
            | {(EvidenceSubjectKind.UNCERTAINTY, item.local_ref) for item in self.uncertainties}
        )
        if required - supported:
            raise ValueError("every provider proposition, relationship, and uncertainty requires evidence support")
        return self


class DerivedProposition(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    proposition_id: StrictStr
    direction: Direction
    active: StrictBool


class DerivedSemanticView(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    schema_identity: StrictStr
    schema_version: StrictStr
    incident_id: StrictStr
    propositions: List[DerivedProposition]
    active_proposition_ids: List[StrictStr]


class PolicyCandidateView(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    schema_identity: StrictStr
    schema_version: StrictStr
    incident_id: StrictStr
    active_current_interpersonal_affirmed: List[StrictStr]
    active_current_interpersonal_uncertain: List[StrictStr]
    active_current_interpersonal_negated: List[StrictStr]
    active_current_interpersonal_accidental: List[StrictStr]
    active_current_interpersonal_violence: List[StrictStr]
    active_potential_interpersonal_uncertain: List[StrictStr]
    active_conflict_relationships: List[StrictStr]
    active_uncertainties: List[StrictStr]
    active_current_interpersonal_uncertainties: List[StrictStr]


class ValidationIssue(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: ValidationIssueCode
    field: StrictStr
    message: StrictStr


class SchemaValidationResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    status: SchemaValidationStatus
    issues: List[ValidationIssue] = Field(default_factory=list)
    semantic_envelope: Optional[ViolenceSemanticEnvelope] = None

    @model_validator(mode="after")
    def require_consistent_outcome(self) -> "SchemaValidationResult":
        if self.status == SchemaValidationStatus.PASSED and (self.semantic_envelope is None or self.issues):
            raise ValueError("passed schema validation requires an envelope and no issues")
        if self.status == SchemaValidationStatus.FAILED and (self.semantic_envelope is not None or not self.issues):
            raise ValueError("failed schema validation requires issues and no envelope")
        if self.status == SchemaValidationStatus.NOT_RUN and (self.semantic_envelope is not None or self.issues):
            raise ValueError("schema validation not-run state cannot contain an envelope or issues")
        return self

    @property
    def passed(self) -> bool:
        return self.status == SchemaValidationStatus.PASSED


class DomainValidationResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

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


class ValidatedSemanticEnvelope(BaseModel):
    """Admissibility carrier available only after both validation stages pass."""

    model_config = ConfigDict(strict=True, extra="forbid")

    envelope: ViolenceSemanticEnvelope
    derived: DerivedSemanticView
    policy_candidate: PolicyCandidateView


class ValidationResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    schema_validation: SchemaValidationResult
    domain_validation: DomainValidationResult
    failure_stage: ValidationFailureStage
    validated_envelope: Optional[ValidatedSemanticEnvelope] = None

    @model_validator(mode="after")
    def require_stage_consistency(self) -> "ValidationResult":
        if self.failure_stage == ValidationFailureStage.NOT_RUN:
            if (
                self.schema_validation.status != SchemaValidationStatus.NOT_RUN
                or self.domain_validation.status != DomainValidationStatus.NOT_RUN
                or self.validated_envelope is not None
            ):
                raise ValueError("not-run validation cannot contain stage results or facts")
        elif self.failure_stage == ValidationFailureStage.NONE:
            if not self.schema_validation.passed or not self.domain_validation.passed or self.validated_envelope is None:
                raise ValueError("successful validation requires both stages and a validated envelope")
        elif self.failure_stage == ValidationFailureStage.SCHEMA:
            if self.schema_validation.status != SchemaValidationStatus.FAILED:
                raise ValueError("schema failure stage requires failed schema validation")
            if self.domain_validation.status != DomainValidationStatus.NOT_RUN or self.validated_envelope is not None:
                raise ValueError("schema failure cannot run domain validation or expose an envelope")
        elif self.failure_stage == ValidationFailureStage.DOMAIN:
            if not self.schema_validation.passed or self.domain_validation.status != DomainValidationStatus.FAILED:
                raise ValueError("domain failure requires passed schema and failed domain validation")
            if self.validated_envelope is not None:
                raise ValueError("domain failure cannot expose a validated envelope")
        return self

    @property
    def passed(self) -> bool:
        return self.failure_stage == ValidationFailureStage.NONE


class CommunicationPropositionFact(BaseModel):
    """Narrative-free projection of one validated proposition."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    actor_label: Optional[StrictStr] = Field(default=None, min_length=1, max_length=80)
    target_label: Optional[StrictStr] = Field(default=None, min_length=1, max_length=80)
    conduct_kind: ConductKind
    direction: Direction
    completion: Completion
    contact: Contact
    temporal_scope: TemporalScope
    intentionality: SemanticIntentionality
    assertion_status: AssertionStatus
    active: StrictBool


class CommunicationRegexProjection(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    detected: StrictBool
    match_count: int = Field(ge=0)


class CommunicationComparisonProjection(BaseModel):
    """Narrow comparison facts that cannot retain an Incident."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    semantic_validation_status: StrictStr = Field(min_length=1, max_length=80)
    classification_alignment: StrictStr = Field(min_length=1, max_length=80)
    material_difference_detected: StrictBool
    display_status: StrictStr = Field(min_length=1, max_length=120)
    observations: tuple[StrictStr, ...]


class OperatorCommunicationInput(BaseModel):
    """Immutable, presentation-only facts created after validation and policy."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    policy_outcome: PolicyOutcome
    policy_reason_codes: tuple[PolicyReasonCode, ...]
    validation_status: ValidationFailureStage
    failure_provenance: Optional[PipelineFailureProvenance] = None
    proposition_facts: tuple[CommunicationPropositionFact, ...]
    uncertainty_dimensions: tuple[UncertaintyDimension, ...]
    relationship_kinds: tuple[RelationshipKind, ...]
    regex: CommunicationRegexProjection
    comparison: CommunicationComparisonProjection
    salesforce_preview_eligible: StrictBool

    @model_validator(mode="after")
    def require_validated_nonfailure_authority(self) -> "OperatorCommunicationInput":
        if self.validation_status != ValidationFailureStage.NONE:
            raise ValueError("communication input requires successful deterministic validation")
        if self.policy_outcome == PolicyOutcome.WRITE_FAILED or self.failure_provenance is not None:
            raise ValueError("communication input requires a completed non-failure policy decision")
        if not self.policy_reason_codes:
            raise ValueError("communication input requires policy reason codes")
        return self


class OperatorCommunication(BaseModel):
    """The complete presentation-only communication payload."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, str_strip_whitespace=True)

    incident_summary: StrictStr = Field(min_length=1, max_length=500)
    key_findings: tuple[StrictStr, ...] = Field(min_length=1, max_length=8)
    why_this_result: StrictStr = Field(min_length=1, max_length=500)

    @field_validator("key_findings")
    @classmethod
    def require_concise_findings(cls, findings: tuple[str, ...]) -> tuple[str, ...]:
        for finding in findings:
            word_count = len(finding.split())
            if not 2 <= word_count <= 5:
                raise ValueError("each key finding must contain 2 to 5 words")
        if len({finding.casefold() for finding in findings}) != len(findings):
            raise ValueError("key findings must not contain duplicates")
        return findings

    @model_validator(mode="after")
    def prohibit_implementation_language(self) -> "OperatorCommunication":
        text = " ".join((self.incident_summary, *self.key_findings, self.why_this_result)).casefold()
        forbidden = (
            "active proposition",
            "classification metadata",
            "deterministic policy",
            "entity ent-",
            "entity id",
            "implementation detail",
            "policy identifier",
            "policy matched",
            "proposition",
            "proposition id",
            "reason code",
            "repository",
            "schema",
            "schema validated",
            "semantic contract",
            "semantic graph",
            "validation",
            "validation passed",
            "validation stage",
        )
        if any(term in text for term in forbidden):
            raise ValueError("operator communication cannot expose implementation language")
        return self


class SalesforcePayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    illustrative_incident_identifier: StrictStr
    illustrative_semantic_schema: StrictStr
    illustrative_active_propositions: List[StrictStr]
    illustrative_interpersonal_propositions: List[StrictStr]
    illustrative_evidence: List[StrictStr]
    illustrative_validation_status: StrictStr
    illustrative_write_disposition: StrictStr

    @classmethod
    def from_preview_dict(cls, value: Dict[str, object]) -> "SalesforcePayload":
        return cls(
            illustrative_incident_identifier=value["Illustrative_Incident_Identifier__c"],
            illustrative_semantic_schema=value["Illustrative_Semantic_Schema__c"],
            illustrative_active_propositions=value["Illustrative_Active_Propositions__c"],
            illustrative_interpersonal_propositions=value["Illustrative_Interpersonal_Propositions__c"],
            illustrative_evidence=value["Illustrative_Evidence__c"],
            illustrative_validation_status=value["Illustrative_Validation_Status__c"],
            illustrative_write_disposition=value["Illustrative_Write_Disposition__c"],
        )

    def to_preview_dict(self) -> Dict[str, object]:
        return {
            "Illustrative_Incident_Identifier__c": self.illustrative_incident_identifier,
            "Illustrative_Semantic_Schema__c": self.illustrative_semantic_schema,
            "Illustrative_Active_Propositions__c": list(self.illustrative_active_propositions),
            "Illustrative_Interpersonal_Propositions__c": list(self.illustrative_interpersonal_propositions),
            "Illustrative_Evidence__c": list(self.illustrative_evidence),
            "Illustrative_Validation_Status__c": self.illustrative_validation_status,
            "Illustrative_Write_Disposition__c": self.illustrative_write_disposition,
        }


class PipelineResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", arbitrary_types_allowed=True)

    incident: Incident
    normalized_incident: NormalizedIncident
    regex_result: RegexResult
    semantic_envelope: Optional[ViolenceSemanticEnvelope]
    derived_semantics: Optional[DerivedSemanticView]
    validation_result: ValidationResult
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
