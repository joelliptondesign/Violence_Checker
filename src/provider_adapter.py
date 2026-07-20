"""Deterministic termination of true-north provider fact candidates."""

from __future__ import annotations

from collections import defaultdict

from src.contracts import (
    EXTRACTION_CONTRACT_IDENTITY,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    FactEvidence,
    IncidentFact,
    ProviderFactCandidate,
    ProviderStructuredResponse,
    TrueNorthSemanticEnvelope,
)
from src.models import Incident


def _enum_rank(value: object) -> int:
    return list(type(value)).index(value)


def _fact_key(fact: ProviderFactCandidate, narrative: str) -> tuple:
    positions = [narrative.find(item.excerpt) for item in fact.evidence]
    first_position = min((value for value in positions if value >= 0), default=len(narrative))
    return (
        first_position,
        fact.temporal_scope.value,
        fact.assertion_status.value,
        fact.conduct.value if fact.conduct is not None else "",
        fact.direction.value,
        fact.intentionality.value,
        fact.resolution_status.value,
        tuple(sorted(item.excerpt for item in fact.evidence)),
        tuple(item.value for item in sorted(fact.uncertainty, key=_enum_rank)),
        fact.local_ref,
    )


def _canonical_facts(provider: ProviderStructuredResponse, narrative: str) -> list[ProviderFactCandidate]:
    by_ref = {fact.local_ref: fact for fact in provider.facts}
    outgoing: dict[str, set[str]] = defaultdict(set)
    indegree = {reference: 0 for reference in by_ref}
    for fact in provider.facts:
        if fact.supersedes_local_ref is None:
            continue
        if fact.supersedes_local_ref not in by_ref:
            raise ValueError("unresolved provider reference at facts.supersedes_local_ref")
        if fact.supersedes_local_ref == fact.local_ref:
            raise ValueError("provider fact cannot supersede itself")
        earlier, later = fact.supersedes_local_ref, fact.local_ref
        if later not in outgoing[earlier]:
            outgoing[earlier].add(later)
            indegree[later] += 1

    ready = sorted(
        (by_ref[reference] for reference, degree in indegree.items() if degree == 0),
        key=lambda fact: _fact_key(fact, narrative),
    )
    ordered: list[ProviderFactCandidate] = []
    while ready:
        fact = ready.pop(0)
        ordered.append(fact)
        for successor in sorted(outgoing[fact.local_ref]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(by_ref[successor])
                ready.sort(key=lambda item: _fact_key(item, narrative))
    if len(ordered) != len(provider.facts):
        raise ValueError("provider correction references contain a cycle")
    return ordered


def _resolved_offsets(excerpt: str, narrative: str, start: int | None, end: int | None) -> tuple[int | None, int | None]:
    if start is not None:
        if end is None or narrative[start:end] != excerpt:
            raise ValueError("provider evidence offsets do not identify the exact excerpt")
        return start, end
    first = narrative.find(excerpt)
    if first >= 0 and narrative.find(excerpt, first + 1) < 0:
        return first, first + len(excerpt)
    return None, None


def semantic_candidate_from_provider_response(
    response: object,
    *,
    incident: Incident,
) -> TrueNorthSemanticEnvelope:
    """Reject provider bookkeeping and assign all repository identity deterministically."""
    if not isinstance(incident, Incident):
        raise TypeError("provider adapter requires a validated repository Incident")
    provider = ProviderStructuredResponse.model_validate(response)
    ordered = _canonical_facts(provider, incident.narrative)
    fact_ids = {fact.local_ref: f"FACT-{index:04d}" for index, fact in enumerate(ordered, 1)}

    group_members: dict[str, list[int]] = defaultdict(list)
    for index, fact in enumerate(ordered):
        if fact.contradiction_group_local_ref is not None:
            group_members[fact.contradiction_group_local_ref].append(index)
    ordered_groups = sorted(group_members, key=lambda group: (tuple(group_members[group]), group))
    group_ids = {group: f"CGRP-{index:04d}" for index, group in enumerate(ordered_groups, 1)}

    evidence_counter = 1
    repository_facts: list[IncidentFact] = []
    for fact in ordered:
        ordered_evidence = sorted(
            enumerate(fact.evidence),
            key=lambda pair: (
                incident.narrative.find(pair[1].excerpt)
                if incident.narrative.find(pair[1].excerpt) >= 0
                else len(incident.narrative),
                -len(pair[1].excerpt),
                pair[1].excerpt,
                tuple(_enum_rank(value) for value in pair[1].supports),
                pair[0],
            ),
        )
        evidence: list[FactEvidence] = []
        for _, item in ordered_evidence:
            start, end = _resolved_offsets(
                item.excerpt,
                incident.narrative,
                item.start_offset,
                item.end_offset,
            )
            evidence.append(
                FactEvidence(
                    evidence_id=f"EVID-{evidence_counter:04d}",
                    excerpt=item.excerpt,
                    supports=sorted(item.supports, key=_enum_rank),
                    start_offset=start,
                    end_offset=end,
                )
            )
            evidence_counter += 1
        repository_facts.append(
            IncidentFact(
                fact_id=fact_ids[fact.local_ref],
                conduct=fact.conduct,
                direction=fact.direction,
                intentionality=fact.intentionality,
                temporal_scope=fact.temporal_scope,
                assertion_status=fact.assertion_status,
                resolution_status=fact.resolution_status,
                supersedes_fact_id=(
                    fact_ids[fact.supersedes_local_ref]
                    if fact.supersedes_local_ref is not None
                    else None
                ),
                contradiction_group=(
                    group_ids[fact.contradiction_group_local_ref]
                    if fact.contradiction_group_local_ref is not None
                    else None
                ),
                evidence=evidence,
                uncertainty=sorted(fact.uncertainty, key=_enum_rank),
            )
        )

    return TrueNorthSemanticEnvelope(
        schema_identity=SEMANTIC_SCHEMA_IDENTITY,
        schema_version=SEMANTIC_SCHEMA_VERSION,
        extraction_contract_identity=EXTRACTION_CONTRACT_IDENTITY,
        incident_id=incident.incident_id,
        facts=repository_facts,
    )
