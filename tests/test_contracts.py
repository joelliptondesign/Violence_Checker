import pytest
from pydantic import ValidationError

from src.contracts import (
    AssertionStatus,
    Completion,
    ConductKind,
    Contact,
    EntityKind,
    EvidenceSubjectKind,
    EvidenceSupportRole,
    EXTRACTION_CONTRACT_IDENTITY,
    PipelineResult,
    ProviderEntityCandidate,
    ProviderEvidenceCandidate,
    ProviderEvidenceSupportCandidate,
    ProviderPropositionCandidate,
    ProviderStructuredResponse,
    ProviderTargetCandidate,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    SemanticIntentionality,
    TargetKind,
    TemporalScope,
    UncertaintyDimension,
    ViolenceSemanticEnvelope,
)
from src.provider_adapter import semantic_candidate_from_provider_response
from src.models import Incident
from tests.successor_helpers import envelope


def test_successor_schema_identity_and_version_are_explicit():
    value = envelope()
    assert value.schema_identity == SEMANTIC_SCHEMA_IDENTITY
    assert value.schema_version == SEMANTIC_SCHEMA_VERSION


def test_provider_adapter_terminates_provider_object_with_typed_envelope():
    provider = envelope(provider=True)
    adapted = semantic_candidate_from_provider_response(
        provider,
        incident=Incident(incident_id="CASE_001", narrative="Patient struck the nurse."),
    )
    assert type(adapted) is ViolenceSemanticEnvelope
    assert adapted.incident_id == "CASE_001"
    assert "incident_id" not in ProviderStructuredResponse.model_fields
    assert "schema_identity" not in ProviderStructuredResponse.model_fields
    assert "extraction_metadata" not in ProviderStructuredResponse.model_fields
    assert adapted.extraction_metadata.extraction_contract_identity == EXTRACTION_CONTRACT_IDENTITY
    assert adapted.extraction_metadata.provider_name is None
    assert adapted.extraction_metadata.model_identifier is None
    assert adapted.extraction_metadata.request_id is None
    assert adapted.extraction_metadata.provider_confidence is None


def test_provider_cannot_override_repository_extraction_metadata():
    values = envelope(provider=True).model_dump()
    values["extraction_metadata"] = {
        "extraction_contract_identity": "provider-authored@999",
        "provider_name": "provider-authored",
    }
    provider = ProviderStructuredResponse.model_validate(values)
    adapted = semantic_candidate_from_provider_response(
        provider,
        incident=Incident(incident_id="CASE_001", narrative="Patient struck the nurse."),
    )
    assert "extraction_metadata" not in provider.model_dump()
    assert adapted.extraction_metadata.extraction_contract_identity == EXTRACTION_CONTRACT_IDENTITY
    assert adapted.extraction_metadata.provider_name is None


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


def historical_assault_provider_values():
    return {
        "entities": [
            ProviderEntityCandidate(local_ref="former-partner", entity_kind=EntityKind.PERSON),
            ProviderEntityCandidate(local_ref="patient", entity_kind=EntityKind.PERSON),
        ],
        "propositions": [
            ProviderPropositionCandidate(
                local_ref="historical-assault",
                actor_ref="former-partner",
                conduct_kind=ConductKind.PHYSICAL_CONDUCT,
                target=ProviderTargetCandidate(target_kind=TargetKind.ENTITY, target_ref="patient"),
                completion=Completion.COMPLETED,
                contact=Contact.OCCURRED,
                temporal_scope=TemporalScope.HISTORICAL,
                intentionality=SemanticIntentionality.INTENTIONAL,
                assertion_status=AssertionStatus.AFFIRMED,
            )
        ],
        "relationships": [],
        "uncertainties": [],
        "evidence_excerpts": [ProviderEvidenceCandidate(local_ref="disclosure", text="assaulted her a few yrs ago")],
        "evidence_supports": [
            ProviderEvidenceSupportCandidate(
                evidence_ref="disclosure",
                subject_kind=EvidenceSubjectKind.PROPOSITION,
                subject_ref="historical-assault",
                role=EvidenceSupportRole.SUPPORTS_ASSERTION,
            )
        ],
    }


def test_provider_candidate_rejects_invalid_conduct_combinations():
    with pytest.raises(ValidationError, match="completed physical conduct requires occurred contact"):
        ProviderPropositionCandidate(
            local_ref="historical-assault",
            actor_ref="former-partner",
            conduct_kind=ConductKind.PHYSICAL_CONDUCT,
            target=ProviderTargetCandidate(target_kind=TargetKind.ENTITY, target_ref="patient"),
            completion=Completion.COMPLETED,
            contact=Contact.DID_NOT_OCCUR,
            temporal_scope=TemporalScope.HISTORICAL,
            intentionality=SemanticIntentionality.INTENTIONAL,
            assertion_status=AssertionStatus.AFFIRMED,
        )


def test_provider_target_candidate_rejects_incoherent_reference_shapes():
    with pytest.raises(ValidationError, match="entity target requires target_ref"):
        ProviderTargetCandidate(target_kind=TargetKind.ENTITY)
    with pytest.raises(ValidationError, match="only entity target"):
        ProviderTargetCandidate(target_kind=TargetKind.UNDETERMINED, target_ref="patient")


def test_case_003_historical_assault_provider_shape_is_admissible():
    candidate = ProviderStructuredResponse.model_validate(historical_assault_provider_values())
    assert candidate.propositions[0].temporal_scope == TemporalScope.HISTORICAL


def test_provider_candidate_rejects_resolved_uncertainty_and_incoherent_support():
    values = historical_assault_provider_values()
    values["uncertainties"] = [
        {"local_ref": "timing", "proposition_ref": "historical-assault", "dimension": UncertaintyDimension.TEMPORAL_SCOPE}
    ]
    with pytest.raises(ValidationError, match="unresolved or disputed"):
        ProviderStructuredResponse.model_validate(values)

    values = historical_assault_provider_values()
    values["evidence_supports"][0] = ProviderEvidenceSupportCandidate(
        evidence_ref="disclosure",
        subject_kind=EvidenceSubjectKind.PROPOSITION,
        subject_ref="historical-assault",
        role=EvidenceSupportRole.SUPPORTS_NEGATION,
    )
    with pytest.raises(ValidationError, match="incoherent"):
        ProviderStructuredResponse.model_validate(values)


def test_provider_candidate_rejects_semantic_subject_without_evidence_support():
    values = historical_assault_provider_values()
    values["evidence_supports"] = []
    with pytest.raises(ValidationError, match="every provider proposition"):
        ProviderStructuredResponse.model_validate(values)


def test_provider_support_subject_kind_rejects_impossible_role():
    with pytest.raises(ValidationError, match="not allowed"):
        ProviderEvidenceSupportCandidate(
            evidence_ref="disclosure",
            subject_kind=EvidenceSubjectKind.UNCERTAINTY,
            subject_ref="timing",
            role=EvidenceSupportRole.SUPPORTS_ASSERTION,
        )
