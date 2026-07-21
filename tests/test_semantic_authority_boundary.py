from pathlib import Path

import pytest
from pydantic import ValidationError

from src.contracts import (
    AssertionStatus,
    Conduct,
    EXTRACTION_CONTRACT_IDENTITY,
    FactDirection,
    Intentionality,
    MaterialAttribute,
    ProviderFactCandidate,
    ProviderFactEvidenceCandidate,
    ProviderStructuredResponse,
    ResolutionStatus,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    TemporalScope,
    TrueNorthSemanticEnvelope,
    UncertaintyDimension,
)
from src.models import Incident
from src.provider_adapter import semantic_candidate_from_provider_response


SUPPORTS = [
    MaterialAttribute.CONDUCT,
    MaterialAttribute.DIRECTION,
    MaterialAttribute.INTENTIONALITY,
    MaterialAttribute.TEMPORAL_SCOPE,
    MaterialAttribute.ASSERTION_STATUS,
]


def candidate(local_ref, excerpt, **updates):
    values = dict(
        local_ref=local_ref,
        conduct=Conduct.PHYSICAL_CONTACT,
        direction=FactDirection.INTERPERSONAL,
        intentionality=Intentionality.INTENTIONAL,
        temporal_scope=TemporalScope.CURRENT,
        assertion_status=AssertionStatus.AFFIRMED,
        resolution_status=ResolutionStatus.ACTIVE,
        evidence=[ProviderFactEvidenceCandidate(excerpt=excerpt, supports=SUPPORTS)],
        uncertainty=[],
    )
    values.update(updates)
    return ProviderFactCandidate(**values)


def test_adapter_terminates_provider_object_and_assigns_all_repository_bookkeeping():
    narrative = "He intentionally punched a coworker today."
    adapted = semantic_candidate_from_provider_response(
        ProviderStructuredResponse(facts=[candidate("provider-ref", narrative)]),
        incident=Incident(incident_id="REPOSITORY_CASE", narrative=narrative),
    )
    assert type(adapted) is TrueNorthSemanticEnvelope
    assert adapted.schema_identity == SEMANTIC_SCHEMA_IDENTITY
    assert adapted.schema_version == SEMANTIC_SCHEMA_VERSION
    assert adapted.extraction_contract_identity == EXTRACTION_CONTRACT_IDENTITY
    assert adapted.incident_id == "REPOSITORY_CASE"
    assert [fact.fact_id for fact in adapted.facts] == ["FACT-0001"]
    assert [item.evidence_id for item in adapted.facts[0].evidence] == ["EVID-0001"]
    assert adapted.facts[0].evidence[0].start_offset == 0
    assert adapted.facts[0].evidence[0].end_offset == len(narrative)


def test_provider_authored_repository_bookkeeping_is_rejected_not_discarded():
    raw = ProviderStructuredResponse(facts=[]).model_dump()
    for field in (
        "incident_id", "schema_identity", "schema_version", "extraction_contract_identity",
        "processing_status", "completeness_status", "policy_outcome",
    ):
        values = dict(raw)
        values[field] = "provider-authored"
        with pytest.raises(ValidationError):
            semantic_candidate_from_provider_response(
                values,
                incident=Incident(incident_id="CASE", narrative="text"),
            )


def test_equivalent_provider_order_and_local_names_produce_equivalent_bookkeeping():
    first_text = "First, he intentionally punched a coworker today."
    second_text = "Then he intentionally shoved another coworker today."
    narrative = f"{first_text} {second_text}"
    first = ProviderStructuredResponse(facts=[
        candidate("z", second_text),
        candidate("a", first_text),
    ])
    second = ProviderStructuredResponse(facts=[
        candidate("renamed-first", first_text),
        candidate("renamed-second", second_text),
    ])
    incident = Incident(incident_id="CASE", narrative=narrative)
    assert semantic_candidate_from_provider_response(first, incident=incident) == semantic_candidate_from_provider_response(second, incident=incident)


def test_correction_and_contradiction_local_references_are_canonically_remapped():
    first_text = "Witness A reported an intentional punch today."
    second_text = "Witness B disputed the intentional punch today."
    narrative = f"{first_text} {second_text}"
    contradiction_supports = SUPPORTS + [MaterialAttribute.CONTRADICTION]
    provider = ProviderStructuredResponse(facts=[
        candidate(
            "b", second_text,
            assertion_status=AssertionStatus.DISPUTED,
            contradiction_group_local_ref="provider-group",
            uncertainty=[UncertaintyDimension.ASSERTION_STATUS],
            evidence=[ProviderFactEvidenceCandidate(excerpt=second_text, supports=contradiction_supports)],
        ),
        candidate(
            "a", first_text,
            assertion_status=AssertionStatus.DISPUTED,
            contradiction_group_local_ref="provider-group",
            uncertainty=[UncertaintyDimension.ASSERTION_STATUS],
            evidence=[ProviderFactEvidenceCandidate(excerpt=first_text, supports=contradiction_supports)],
        ),
    ])
    adapted = semantic_candidate_from_provider_response(
        provider,
        incident=Incident(incident_id="CASE", narrative=narrative),
    )
    assert [fact.fact_id for fact in adapted.facts] == ["FACT-0001", "FACT-0002"]
    assert {fact.contradiction_group for fact in adapted.facts} == {"CGRP-0001"}
    assert [evidence.evidence_id for fact in adapted.facts for evidence in fact.evidence] == ["EVID-0001", "EVID-0002"]


def test_unresolved_provider_correction_reference_fails_closed():
    narrative = "Later corrected account."
    provider = ProviderStructuredResponse(facts=[
        candidate("later", narrative, supersedes_local_ref="missing"),
    ])
    with pytest.raises(ValueError, match="unresolved provider reference"):
        semantic_candidate_from_provider_response(
            provider,
            incident=Incident(incident_id="CASE", narrative=narrative),
        )


def test_provider_correction_cycle_and_false_offsets_fail_closed():
    narrative = "First account. Second account."
    cyclic = ProviderStructuredResponse(facts=[
        candidate("first", "First account.", supersedes_local_ref="second"),
        candidate("second", "Second account.", supersedes_local_ref="first"),
    ])
    with pytest.raises(ValueError, match="cycle"):
        semantic_candidate_from_provider_response(
            cyclic,
            incident=Incident(incident_id="CASE", narrative=narrative),
        )

    wrong_offsets = ProviderStructuredResponse(facts=[candidate(
        "first",
        "First account.",
        evidence=[ProviderFactEvidenceCandidate(
            excerpt="First account.", supports=SUPPORTS, start_offset=1, end_offset=15,
        )],
    )])
    with pytest.raises(ValueError, match="offsets"):
        semantic_candidate_from_provider_response(
            wrong_offsets,
            incident=Incident(incident_id="CASE", narrative=narrative),
        )


def test_successor_boundary_contains_no_legacy_semantic_contract_classes():
    contracts = Path("src/contracts.py").read_text()
    for obsolete in (
        "ViolenceProposition", "EntityReference", "SemanticRelationship",
        "EvidenceSupport", "PolicyCandidateView",
        "ViolenceSemanticEnvelope",
    ):
        assert f"class {obsolete}" not in contracts
    assert "violence-checker.proposition-semantics" not in contracts
