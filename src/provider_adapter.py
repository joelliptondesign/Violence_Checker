"""Deterministic adapter that terminates provider-facing structured output."""

from collections import defaultdict
from typing import Callable, TypeVar

from src.contracts import (
    Attribution,
    EvidenceExcerpt,
    EvidenceSubjectKind,
    EvidenceSupport,
    EntityReference,
    EXTRACTION_CONTRACT_IDENTITY,
    ExtractionMetadata,
    PropositionTarget,
    ProviderStructuredResponse,
    RelationshipKind,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    SemanticRelationship,
    SemanticUncertainty,
    ViolenceProposition,
    ViolenceSemanticEnvelope,
)
from src.models import Incident


T = TypeVar("T")


def _enum_rank(value: object) -> int:
    return list(type(value)).index(value)


def _local_map(items: list[object], collection: str) -> dict[str, object]:
    result = {item.local_ref: item for item in items}
    if len(result) != len(items):
        raise ValueError(f"duplicate {collection} local reference")
    return result


def _require_ref(reference: str, references: dict[str, object], field: str) -> None:
    if reference not in references:
        raise ValueError(f"unresolved provider reference at {field}")


def _topological_order(
    items: list[T],
    *,
    local_ref: Callable[[T], str],
    sort_key: Callable[[T], tuple],
    edges: list[tuple[str, str]],
) -> list[T]:
    """Return deterministic target-before-source order for directed semantic edges."""
    by_ref = {local_ref(item): item for item in items}
    outgoing: dict[str, set[str]] = defaultdict(set)
    indegree = {reference: 0 for reference in by_ref}
    for earlier, later in edges:
        if later not in outgoing[earlier]:
            outgoing[earlier].add(later)
            indegree[later] += 1
    ready = sorted((by_ref[ref] for ref, degree in indegree.items() if degree == 0), key=sort_key)
    ordered: list[T] = []
    while ready:
        item = ready.pop(0)
        reference = local_ref(item)
        ordered.append(item)
        for successor in sorted(outgoing[reference]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(by_ref[successor])
                ready.sort(key=sort_key)
    if len(ordered) != len(items):
        raise ValueError("provider proposition relationships contain a directed cycle")
    return ordered


def semantic_candidate_from_provider_response(
    response: object,
    *,
    incident: Incident,
) -> ViolenceSemanticEnvelope:
    """Validate candidates, canonicalize bookkeeping, and attach repository identity."""
    if not isinstance(incident, Incident):
        raise TypeError("provider adapter requires a validated repository Incident")
    provider = ProviderStructuredResponse.model_validate(response)

    entities_by_ref = _local_map(provider.entities, "entity")
    propositions_by_ref = _local_map(provider.propositions, "proposition")
    relationships_by_ref = _local_map(provider.relationships, "relationship")
    uncertainties_by_ref = _local_map(provider.uncertainties, "uncertainty")
    evidence_by_ref = _local_map(provider.evidence_excerpts, "evidence")

    for index, proposition in enumerate(provider.propositions):
        _require_ref(proposition.actor_ref, entities_by_ref, f"propositions.{index}.actor_ref")
        if proposition.target.target_ref is not None:
            _require_ref(proposition.target.target_ref, entities_by_ref, f"propositions.{index}.target.target_ref")
        if proposition.attribution and proposition.attribution.source_ref is not None:
            _require_ref(proposition.attribution.source_ref, entities_by_ref, f"propositions.{index}.attribution.source_ref")
    for index, relationship in enumerate(provider.relationships):
        _require_ref(relationship.source_proposition_ref, propositions_by_ref, f"relationships.{index}.source_proposition_ref")
        _require_ref(relationship.target_proposition_ref, propositions_by_ref, f"relationships.{index}.target_proposition_ref")
    for index, uncertainty in enumerate(provider.uncertainties):
        _require_ref(uncertainty.proposition_ref, propositions_by_ref, f"uncertainties.{index}.proposition_ref")
    subject_maps = {
        EvidenceSubjectKind.PROPOSITION: propositions_by_ref,
        EvidenceSubjectKind.RELATIONSHIP: relationships_by_ref,
        EvidenceSubjectKind.UNCERTAINTY: uncertainties_by_ref,
    }
    for index, support in enumerate(provider.evidence_supports):
        _require_ref(support.evidence_ref, evidence_by_ref, f"evidence_supports.{index}.evidence_ref")
        _require_ref(support.subject_ref, subject_maps[support.subject_kind], f"evidence_supports.{index}.subject_ref")

    evidence_position = {
        item.local_ref: incident.narrative.find(item.text) for item in provider.evidence_excerpts
    }
    ordered_evidence = sorted(
        provider.evidence_excerpts,
        key=lambda item: (
            evidence_position[item.local_ref] if evidence_position[item.local_ref] >= 0 else len(incident.narrative),
            -len(item.text),
            item.text,
            item.local_ref,
        ),
    )
    evidence_ids = {item.local_ref: f"EVID-{index:04d}" for index, item in enumerate(ordered_evidence, 1)}

    support_positions: dict[str, list[int]] = defaultdict(list)
    for support in provider.evidence_supports:
        if support.subject_kind == EvidenceSubjectKind.PROPOSITION:
            position = evidence_position[support.evidence_ref]
            support_positions[support.subject_ref].append(position if position >= 0 else len(incident.narrative))

    def entity_fingerprint(reference: str) -> tuple:
        entity = entities_by_ref[reference]
        return (entity.entity_kind.value, entity.label or "")

    def proposition_key(item) -> tuple:
        target_fingerprint = entity_fingerprint(item.target.target_ref) if item.target.target_ref else ()
        attribution = item.attribution
        attribution_key = (
            attribution.source_kind.value,
            entity_fingerprint(attribution.source_ref) if attribution and attribution.source_ref else (),
        ) if attribution else ()
        return (
            min(support_positions.get(item.local_ref, [len(incident.narrative)])),
            item.temporal_scope.value,
            item.assertion_status.value,
            item.conduct_kind.value,
            entity_fingerprint(item.actor_ref),
            item.target.target_kind.value,
            target_fingerprint,
            item.completion.value,
            item.contact.value,
            item.intentionality.value,
            attribution_key,
            item.local_ref,
        )

    supersession_edges = [
        (item.target_proposition_ref, item.source_proposition_ref)
        for item in provider.relationships
        if item.relationship_kind == RelationshipKind.SUPERSEDES
    ]
    ordered_propositions = _topological_order(
        provider.propositions,
        local_ref=lambda item: item.local_ref,
        sort_key=proposition_key,
        edges=supersession_edges,
    )
    proposition_ids = {item.local_ref: f"PROP-{index:04d}" for index, item in enumerate(ordered_propositions, 1)}
    proposition_index = {item.local_ref: index for index, item in enumerate(ordered_propositions)}

    entity_usage: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for index, proposition in enumerate(ordered_propositions):
        entity_usage[proposition.actor_ref].append((index, 0))
        if proposition.target.target_ref is not None:
            entity_usage[proposition.target.target_ref].append((index, 1))
        if proposition.attribution and proposition.attribution.source_ref is not None:
            entity_usage[proposition.attribution.source_ref].append((index, 2))
    ordered_entities = sorted(
        provider.entities,
        key=lambda item: (
            min(entity_usage.get(item.local_ref, [(len(ordered_propositions), 3)])),
            item.entity_kind.value,
            item.label or "",
            item.local_ref,
        ),
    )
    entity_ids = {item.local_ref: f"ENT-{index:04d}" for index, item in enumerate(ordered_entities, 1)}

    ordered_relationships = sorted(
        provider.relationships,
        key=lambda item: (
            min(proposition_index[item.source_proposition_ref], proposition_index[item.target_proposition_ref])
            if item.relationship_kind == RelationshipKind.CONFLICTS_WITH
            else proposition_index[item.source_proposition_ref],
            _enum_rank(item.relationship_kind),
            max(proposition_index[item.source_proposition_ref], proposition_index[item.target_proposition_ref])
            if item.relationship_kind == RelationshipKind.CONFLICTS_WITH
            else proposition_index[item.target_proposition_ref],
            tuple(_enum_rank(value) for value in item.disputed_dimensions),
            item.local_ref,
        ),
    )
    relationship_ids = {item.local_ref: f"REL-{index:04d}" for index, item in enumerate(ordered_relationships, 1)}

    ordered_uncertainties = sorted(
        provider.uncertainties,
        key=lambda item: (
            proposition_index[item.proposition_ref],
            _enum_rank(item.dimension),
            item.note or "",
            item.local_ref,
        ),
    )
    uncertainty_ids = {item.local_ref: f"UNC-{index:04d}" for index, item in enumerate(ordered_uncertainties, 1)}
    subject_ids = {
        EvidenceSubjectKind.PROPOSITION: proposition_ids,
        EvidenceSubjectKind.RELATIONSHIP: relationship_ids,
        EvidenceSubjectKind.UNCERTAINTY: uncertainty_ids,
    }
    ordered_supports = sorted(
        provider.evidence_supports,
        key=lambda item: (
            evidence_ids[item.evidence_ref],
            _enum_rank(item.subject_kind),
            subject_ids[item.subject_kind][item.subject_ref],
            _enum_rank(item.role),
        ),
    )

    relationships = []
    for index, item in enumerate(ordered_relationships, 1):
        source_ref = proposition_ids[item.source_proposition_ref]
        target_ref = proposition_ids[item.target_proposition_ref]
        if item.relationship_kind == RelationshipKind.CONFLICTS_WITH and source_ref > target_ref:
            source_ref, target_ref = target_ref, source_ref
        relationships.append(
            SemanticRelationship(
                relationship_id=f"REL-{index:04d}",
                relationship_kind=item.relationship_kind,
                source_proposition_ref=source_ref,
                target_proposition_ref=target_ref,
                disputed_dimensions=item.disputed_dimensions,
            )
        )

    return ViolenceSemanticEnvelope(
        schema_identity=SEMANTIC_SCHEMA_IDENTITY,
        schema_version=SEMANTIC_SCHEMA_VERSION,
        incident_id=incident.incident_id,
        entities=[
            EntityReference(entity_id=entity_ids[item.local_ref], entity_kind=item.entity_kind, label=item.label)
            for item in ordered_entities
        ],
        propositions=[
            ViolenceProposition(
                proposition_id=proposition_ids[item.local_ref],
                actor_ref=entity_ids[item.actor_ref],
                conduct_kind=item.conduct_kind,
                target=PropositionTarget(
                    target_kind=item.target.target_kind,
                    target_ref=entity_ids[item.target.target_ref] if item.target.target_ref else None,
                ),
                completion=item.completion,
                contact=item.contact,
                temporal_scope=item.temporal_scope,
                intentionality=item.intentionality,
                assertion_status=item.assertion_status,
                attribution=Attribution(
                    source_kind=item.attribution.source_kind,
                    source_ref=entity_ids[item.attribution.source_ref] if item.attribution.source_ref else None,
                ) if item.attribution else None,
            )
            for item in ordered_propositions
        ],
        relationships=relationships,
        uncertainties=[
            SemanticUncertainty(
                uncertainty_id=uncertainty_ids[item.local_ref],
                proposition_ref=proposition_ids[item.proposition_ref],
                dimension=item.dimension,
                note=item.note,
            )
            for item in ordered_uncertainties
        ],
        evidence_excerpts=[
            EvidenceExcerpt(evidence_id=evidence_ids[item.local_ref], text=item.text)
            for item in ordered_evidence
        ],
        evidence_supports=[
            EvidenceSupport(
                support_id=f"SUP-{index:04d}",
                evidence_ref=evidence_ids[item.evidence_ref],
                subject_kind=item.subject_kind,
                subject_ref=subject_ids[item.subject_kind][item.subject_ref],
                role=item.role,
            )
            for index, item in enumerate(ordered_supports, 1)
        ],
        extraction_metadata=ExtractionMetadata(
            extraction_contract_identity=EXTRACTION_CONTRACT_IDENTITY,
        ),
    )
