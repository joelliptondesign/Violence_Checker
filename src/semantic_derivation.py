"""Deterministic views derived only from an admissible semantic envelope."""

from src.contracts import (
    AssertionStatus,
    ConductKind,
    Direction,
    DerivedProposition,
    DerivedSemanticView,
    EntityKind,
    POLICY_CANDIDATE_SCHEMA_IDENTITY,
    POLICY_CANDIDATE_SCHEMA_VERSION,
    PolicyCandidateView,
    RelationshipKind,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    SemanticIntentionality,
    TargetKind,
    TemporalScope,
    ViolenceSemanticEnvelope,
)


def derive_direction(proposition, entities) -> Direction:
    if proposition.target.target_kind == TargetKind.SELF:
        return Direction.SELF_DIRECTED
    if proposition.target.target_kind != TargetKind.ENTITY or proposition.target.target_ref is None:
        return Direction.UNDETERMINED
    actor = entities[proposition.actor_ref]
    target = entities[proposition.target.target_ref]
    if target.entity_kind == EntityKind.OBJECT:
        return Direction.OBJECT_DIRECTED
    if target.entity_kind in {EntityKind.PERSON, EntityKind.PEOPLE_COLLECTIVE}:
        if actor.entity_kind == EntityKind.UNSPECIFIED or proposition.actor_ref == proposition.target.target_ref:
            return Direction.UNDETERMINED
        return Direction.INTERPERSONAL
    return Direction.UNDETERMINED


def derive_semantic_views(envelope: ViolenceSemanticEnvelope) -> tuple[DerivedSemanticView, PolicyCandidateView]:
    entities = {item.entity_id: item for item in envelope.entities}
    superseded = {
        relationship.target_proposition_ref
        for relationship in envelope.relationships
        if relationship.relationship_kind == RelationshipKind.SUPERSEDES
    }
    derived_propositions = [
        DerivedProposition(
            proposition_id=proposition.proposition_id,
            direction=derive_direction(proposition, entities),
            active=proposition.proposition_id not in superseded,
        )
        for proposition in envelope.propositions
    ]
    active_ids = [item.proposition_id for item in derived_propositions if item.active]
    derived = DerivedSemanticView(
        schema_identity=SEMANTIC_SCHEMA_IDENTITY,
        schema_version=SEMANTIC_SCHEMA_VERSION,
        incident_id=envelope.incident_id,
        propositions=derived_propositions,
        active_proposition_ids=active_ids,
    )

    direction_by_id = {item.proposition_id: item.direction for item in derived_propositions}
    active = [item for item in envelope.propositions if item.proposition_id in active_ids]
    current_interpersonal = [
        item
        for item in active
        if item.temporal_scope == TemporalScope.CURRENT_INCIDENT
        and direction_by_id[item.proposition_id] == Direction.INTERPERSONAL
    ]
    current_interpersonal_ids = {item.proposition_id for item in current_interpersonal}
    active_set = set(active_ids)
    policy_candidate = PolicyCandidateView(
        schema_identity=POLICY_CANDIDATE_SCHEMA_IDENTITY,
        schema_version=POLICY_CANDIDATE_SCHEMA_VERSION,
        incident_id=envelope.incident_id,
        active_current_interpersonal_affirmed=[item.proposition_id for item in current_interpersonal if item.assertion_status == AssertionStatus.AFFIRMED],
        active_current_interpersonal_uncertain=[item.proposition_id for item in current_interpersonal if item.assertion_status == AssertionStatus.UNCERTAIN],
        active_current_interpersonal_negated=[item.proposition_id for item in current_interpersonal if item.assertion_status == AssertionStatus.NEGATED],
        active_current_interpersonal_accidental=[item.proposition_id for item in current_interpersonal if item.intentionality == SemanticIntentionality.ACCIDENTAL],
        active_current_interpersonal_violence=[
            item.proposition_id
            for item in current_interpersonal
            if item.assertion_status == AssertionStatus.AFFIRMED
            and item.intentionality != SemanticIntentionality.ACCIDENTAL
            and item.conduct_kind in {ConductKind.PHYSICAL_CONDUCT, ConductKind.THREAT_EXPRESSION}
        ],
        active_potential_interpersonal_uncertain=[
            item.proposition_id
            for item in active
            if item.assertion_status != AssertionStatus.NEGATED
            and item.temporal_scope in {TemporalScope.CURRENT_INCIDENT, TemporalScope.UNDETERMINED}
            and direction_by_id[item.proposition_id] == Direction.UNDETERMINED
        ],
        active_conflict_relationships=[
            item.relationship_id
            for item in envelope.relationships
            if item.relationship_kind == RelationshipKind.CONFLICTS_WITH
            and item.source_proposition_ref in current_interpersonal_ids
            and item.target_proposition_ref in current_interpersonal_ids
        ],
        active_uncertainties=[item.uncertainty_id for item in envelope.uncertainties if item.proposition_ref in active_set],
        active_current_interpersonal_uncertainties=[
            item.uncertainty_id
            for item in envelope.uncertainties
            if item.proposition_ref in current_interpersonal_ids
        ],
    )
    return derived, policy_candidate
