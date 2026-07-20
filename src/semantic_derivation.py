"""Deterministic views derived only from validated true-north incident facts."""

from collections import defaultdict

from src.contracts import (
    DerivedContradictionGroup,
    DerivedSemanticView,
    FactDirection,
    IncidentDirection,
    ResolutionStatus,
    TrueNorthSemanticEnvelope,
    UncertaintyDimension,
)


_MATERIAL_UNCERTAINTY = {
    UncertaintyDimension.CONDUCT,
    UncertaintyDimension.INTENTIONALITY,
    UncertaintyDimension.TEMPORAL_SCOPE,
    UncertaintyDimension.ASSERTION_STATUS,
}


def derive_semantic_views(envelope: TrueNorthSemanticEnvelope) -> DerivedSemanticView:
    """Project fact state and incident direction without creating semantic facts."""
    if not isinstance(envelope, TrueNorthSemanticEnvelope):
        raise TypeError("semantic derivation requires a validated TrueNorthSemanticEnvelope")

    active_fact_ids = tuple(
        fact.fact_id
        for fact in envelope.facts
        if fact.resolution_status == ResolutionStatus.ACTIVE
    )
    superseded_fact_ids = tuple(
        fact.fact_id
        for fact in envelope.facts
        if fact.resolution_status == ResolutionStatus.SUPERSEDED
    )
    active_id_set = set(active_fact_ids)

    group_members: dict[str, list[str]] = defaultdict(list)
    for fact in envelope.facts:
        if fact.fact_id in active_id_set and fact.contradiction_group is not None:
            group_members[fact.contradiction_group].append(fact.fact_id)
    contradiction_groups = tuple(
        DerivedContradictionGroup(
            contradiction_group=group_id,
            fact_ids=tuple(sorted(group_members[group_id])),
        )
        for group_id in sorted(group_members)
    )

    known_directions = {
        fact.direction
        for fact in envelope.facts
        if fact.fact_id in active_id_set
        and fact.conduct is not None
        and fact.direction != FactDirection.UNKNOWN
    }
    if not known_directions:
        incident_direction = IncidentDirection.UNKNOWN
    elif len(known_directions) > 1:
        incident_direction = IncidentDirection.MULTIPLE
    else:
        incident_direction = IncidentDirection(next(iter(known_directions)).value)

    return DerivedSemanticView(
        incident_id=envelope.incident_id,
        active_fact_ids=active_fact_ids,
        superseded_fact_ids=superseded_fact_ids,
        contradiction_groups=contradiction_groups,
        incident_direction=incident_direction,
    )


def has_unresolved_semantic_content(
    envelope: TrueNorthSemanticEnvelope,
    derived: DerivedSemanticView,
) -> bool:
    """Return whether active facts preserve unresolved material semantic content."""
    active_ids = set(derived.active_fact_ids)
    if derived.contradiction_groups:
        return True
    return any(
        fact.fact_id in active_ids
        and bool(_MATERIAL_UNCERTAINTY.intersection(fact.uncertainty))
        for fact in envelope.facts
    )
