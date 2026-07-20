import pytest
from pydantic import ValidationError

from src.contracts import (
    AssertionStatus,
    Conduct,
    FactDirection,
    Intentionality,
    MaterialAttribute,
    ProviderFactCandidate,
    ProviderFactEvidenceCandidate,
    ProviderStructuredResponse,
    ResolutionStatus,
    TemporalScope,
    TrueNorthSemanticEnvelope,
    UncertaintyDimension,
)


def provider_fact(**updates):
    values = {
        "local_ref": "contact",
        "conduct": Conduct.PHYSICAL_CONTACT,
        "direction": FactDirection.INTERPERSONAL,
        "intentionality": Intentionality.INTENTIONAL,
        "temporal_scope": TemporalScope.CURRENT,
        "assertion_status": AssertionStatus.AFFIRMED,
        "resolution_status": ResolutionStatus.ACTIVE,
        "evidence": [ProviderFactEvidenceCandidate(
            excerpt="He intentionally punched a coworker today.",
            supports=[
                MaterialAttribute.CONDUCT,
                MaterialAttribute.DIRECTION,
                MaterialAttribute.INTENTIONALITY,
                MaterialAttribute.TEMPORAL_SCOPE,
                MaterialAttribute.ASSERTION_STATUS,
            ],
        )],
        "uncertainty": [],
    }
    values.update(updates)
    return ProviderFactCandidate(**values)


def test_true_north_vocabularies_are_exact_and_atomic_direction_excludes_multiple():
    assert {item.value for item in Conduct} == {
        "verbal_threat", "physical_attempt", "physical_contact", "self_harm", "property_violence",
    }
    assert {item.value for item in FactDirection} == {
        "interpersonal", "self_directed", "object_directed", "unknown",
    }
    assert {item.value for item in Intentionality} == {"intentional", "accidental", "unresolved"}
    assert {item.value for item in AssertionStatus} == {"affirmed", "denied", "disputed", "unresolved"}


def test_provider_contract_contains_only_operational_fact_candidates():
    assert set(ProviderStructuredResponse.model_fields) == {"facts"}
    fields = set(ProviderFactCandidate.model_fields)
    assert fields == {
        "local_ref", "conduct", "direction", "intentionality", "temporal_scope",
        "assertion_status", "resolution_status", "evidence", "uncertainty",
        "supersedes_local_ref", "contradiction_group_local_ref",
    }
    forbidden = {
        "incident_id", "schema_identity", "schema_version", "fact_id", "evidence_id",
        "policy_outcome", "policy_reason", "processing_status", "completeness_status",
        "entities", "propositions", "relationships",
    }
    assert fields.isdisjoint(forbidden)


def test_contracts_reject_extra_fields_missing_fields_and_duplicate_local_refs():
    with pytest.raises(ValidationError):
        ProviderStructuredResponse(facts=[provider_fact()], schema_identity="provider-authored")
    values = provider_fact().model_dump()
    del values["direction"]
    with pytest.raises(ValidationError):
        ProviderFactCandidate.model_validate(values)
    with pytest.raises(ValidationError, match="must be unique"):
        ProviderStructuredResponse(facts=[provider_fact(), provider_fact()])


def test_fact_evidence_is_fact_local_exact_text_with_attribute_supports():
    evidence_fields = set(ProviderFactEvidenceCandidate.model_fields)
    assert evidence_fields == {"excerpt", "supports", "start_offset", "end_offset"}
    with pytest.raises(ValidationError, match="must not be empty"):
        ProviderFactEvidenceCandidate(excerpt="  ", supports=[MaterialAttribute.CONDUCT])
    with pytest.raises(ValidationError, match="non-empty and unique"):
        ProviderFactEvidenceCandidate(excerpt="text", supports=[])
    with pytest.raises(ValidationError, match="supplied together"):
        ProviderFactEvidenceCandidate(
            excerpt="text", supports=[MaterialAttribute.CONDUCT], start_offset=0,
        )


def test_repository_envelope_has_one_fact_collection_and_no_legacy_graph():
    assert set(TrueNorthSemanticEnvelope.model_fields) == {
        "schema_identity", "schema_version", "extraction_contract_identity", "incident_id", "facts",
    }
    assert "entities" not in TrueNorthSemanticEnvelope.model_fields
    assert "propositions" not in TrueNorthSemanticEnvelope.model_fields
    assert "relationships" not in TrueNorthSemanticEnvelope.model_fields
    assert "multiple" not in {item.value for item in FactDirection}
    assert UncertaintyDimension.CONDUCT.value == "conduct"
