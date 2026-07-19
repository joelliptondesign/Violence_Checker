from src.contracts import (
    AssertionStatus,
    Completion,
    ConductKind,
    Contact,
    EntityKind,
    EntityReference,
    EvidenceExcerpt,
    EvidenceSubjectKind,
    EvidenceSupport,
    EvidenceSupportRole,
    ExtractionMetadata,
    PropositionTarget,
    ProviderStructuredResponse,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    SemanticIntentionality,
    TargetKind,
    TemporalScope,
    ViolenceProposition,
    ViolenceSemanticEnvelope,
)


def envelope(
    narrative="Patient struck the nurse.",
    incident_id="CASE_001",
    *,
    provider=False,
    conduct=ConductKind.PHYSICAL_CONDUCT,
    completion=Completion.COMPLETED,
    contact=Contact.OCCURRED,
    temporal_scope=TemporalScope.CURRENT_INCIDENT,
    intentionality=SemanticIntentionality.INTENTIONAL,
    assertion_status=AssertionStatus.AFFIRMED,
    target_kind=TargetKind.ENTITY,
    target_entity_kind=EntityKind.PERSON,
):
    entities = [EntityReference(entity_id="ENT-0001", entity_kind=EntityKind.PERSON, label="patient")]
    target_ref = None
    if target_kind == TargetKind.ENTITY:
        target_ref = "ENT-0002"
        entities.append(EntityReference(entity_id=target_ref, entity_kind=target_entity_kind, label="nurse"))
    model = ProviderStructuredResponse if provider else ViolenceSemanticEnvelope
    return model(
        schema_identity=SEMANTIC_SCHEMA_IDENTITY,
        schema_version=SEMANTIC_SCHEMA_VERSION,
        incident_id=incident_id,
        entities=entities,
        propositions=[
            ViolenceProposition(
                proposition_id="PROP-0001",
                actor_ref="ENT-0001",
                conduct_kind=conduct,
                target=PropositionTarget(target_kind=target_kind, target_ref=target_ref),
                completion=completion,
                contact=contact,
                temporal_scope=temporal_scope,
                intentionality=intentionality,
                assertion_status=assertion_status,
            )
        ],
        relationships=[],
        uncertainties=[],
        evidence_excerpts=[EvidenceExcerpt(evidence_id="EVID-0001", text=narrative)],
        evidence_supports=[
            EvidenceSupport(
                support_id="SUP-0001",
                evidence_ref="EVID-0001",
                subject_kind=EvidenceSubjectKind.PROPOSITION,
                subject_ref="PROP-0001",
                role=(EvidenceSupportRole.SUPPORTS_NEGATION if assertion_status == AssertionStatus.NEGATED else EvidenceSupportRole.SUPPORTS_ASSERTION),
            )
        ],
        extraction_metadata=ExtractionMetadata(extraction_contract_identity="violence-checker.proposition-extraction@1.0.0"),
    )
