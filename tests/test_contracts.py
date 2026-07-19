import pytest
from pydantic import ValidationError

from src.contracts import (
    EntityKind,
    PipelineResult,
    ProviderStructuredResponse,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    ViolenceSemanticEnvelope,
)
from src.provider_adapter import semantic_candidate_from_provider_response
from tests.successor_helpers import envelope


def test_successor_schema_identity_and_version_are_explicit():
    value = envelope()
    assert value.schema_identity == SEMANTIC_SCHEMA_IDENTITY
    assert value.schema_version == SEMANTIC_SCHEMA_VERSION


def test_provider_adapter_terminates_provider_object_with_typed_envelope():
    provider = envelope(provider=True)
    adapted = semantic_candidate_from_provider_response(provider)
    assert type(adapted) is ViolenceSemanticEnvelope
    assert adapted.model_dump(mode="json") == provider.model_dump(mode="json")


def test_contracts_forbid_unknown_fields_and_silent_defaults():
    values = envelope().model_dump()
    values["unexpected"] = True
    with pytest.raises(ValidationError):
        ViolenceSemanticEnvelope.model_validate(values)
    values = envelope().model_dump()
    del values["propositions"]
    with pytest.raises(ValidationError):
        ViolenceSemanticEnvelope.model_validate(values)


def test_pipeline_contract_has_one_successor_authority_and_no_global_finding():
    assert "semantic_envelope" in PipelineResult.model_fields
    assert "derived_semantics" in PipelineResult.model_fields
    assert "semantic_facts" not in PipelineResult.model_fields
    assert "operational_finding" not in PipelineResult.model_fields


def test_bounded_entity_vocabulary_is_exact():
    assert {item.value for item in EntityKind} == {"person", "people_collective", "object", "unspecified"}
