import ast
from pathlib import Path

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
    ExtractionMetadata,
    PipelineResult,
    ProviderEntityCandidate,
    ProviderEvidenceCandidate,
    ProviderEvidenceSupportCandidate,
    ProviderPropositionCandidate,
    ProviderRelationshipCandidate,
    ProviderStructuredResponse,
    ProviderTargetCandidate,
    ProviderUncertaintyCandidate,
    RelationshipKind,
    SemanticIntentionality,
    TargetKind,
    TemporalScope,
    UncertaintyDimension,
    ViolenceSemanticEnvelope,
)
from src.provider_adapter import semantic_candidate_from_provider_response
from src.models import Incident
from src.semantic_validation import validate_semantic_candidate
from tests.successor_helpers import envelope


ACTIVE_FILES = [
    "app.py", "src/app_logic.py", "src/policy.py", "src/comparison.py",
    "src/salesforce_preview.py", "src/contract_adapters.py", "src/evaluation/runner.py",
]


def test_provider_shape_terminates_at_adapter():
    provider = envelope(provider=True)
    adapted = semantic_candidate_from_provider_response(
        provider,
        incident=Incident(incident_id="CASE_001", narrative="Patient struck the nurse."),
    )
    assert isinstance(provider, ProviderStructuredResponse)
    assert type(adapted) is ViolenceSemanticEnvelope


def test_repository_owns_incident_identity_and_all_final_identifiers():
    provider = envelope(provider=True)
    assert "incident_id" not in ProviderStructuredResponse.model_fields
    assert all("_id" not in field for field in ProviderStructuredResponse.model_fields)
    adapted = semantic_candidate_from_provider_response(
        provider,
        incident=Incident(incident_id="REPOSITORY_CASE", narrative="Patient struck the nurse."),
    )
    assert adapted.incident_id == "REPOSITORY_CASE"
    assert [item.entity_id for item in adapted.entities] == ["ENT-0001", "ENT-0002"]
    assert [item.proposition_id for item in adapted.propositions] == ["PROP-0001"]
    assert [item.evidence_id for item in adapted.evidence_excerpts] == ["EVID-0001"]
    assert [item.support_id for item in adapted.evidence_supports] == ["SUP-0001"]


def test_equivalent_provider_content_has_equivalent_repository_bookkeeping():
    original = envelope(provider=True).model_dump()
    renamed = envelope(provider=True).model_dump()
    renamed["entities"].reverse()
    replacements = {"actor": "local-person-a", "target": "local-person-b", "conduct": "local-claim", "evidence": "local-quote"}
    for entity in renamed["entities"]:
        entity["local_ref"] = replacements[entity["local_ref"]]
    proposition = renamed["propositions"][0]
    proposition["local_ref"] = replacements[proposition["local_ref"]]
    proposition["actor_ref"] = replacements[proposition["actor_ref"]]
    proposition["target"]["target_ref"] = replacements[proposition["target"]["target_ref"]]
    renamed["evidence_excerpts"][0]["local_ref"] = "local-quote"
    renamed["evidence_supports"][0].update(
        evidence_ref="local-quote",
        subject_ref="local-claim",
    )
    incident = Incident(incident_id="CASE_001", narrative="Patient struck the nurse.")
    first = semantic_candidate_from_provider_response(original, incident=incident)
    second = semantic_candidate_from_provider_response(renamed, incident=incident)
    assert first == second


def test_unresolved_and_duplicate_provider_local_references_fail_closed():
    incident = Incident(incident_id="CASE_001", narrative="Patient struck the nurse.")
    unresolved = envelope(provider=True).model_dump()
    unresolved["propositions"][0]["actor_ref"] = "missing"
    with pytest.raises(ValueError, match="unresolved provider reference"):
        semantic_candidate_from_provider_response(unresolved, incident=incident)

    duplicate = envelope(provider=True).model_dump()
    duplicate["entities"][1]["local_ref"] = duplicate["entities"][0]["local_ref"]
    with pytest.raises(ValidationError, match="must be unique"):
        semantic_candidate_from_provider_response(duplicate, incident=incident)


def test_relationship_uncertainty_and_support_references_are_canonically_remapped():
    narrative = "Patient may have hit nurse. Patient denied hitting nurse."
    provider = ProviderStructuredResponse(
        entities=[
            ProviderEntityCandidate(local_ref="nurse", entity_kind=EntityKind.PERSON, label="nurse"),
            ProviderEntityCandidate(local_ref="patient", entity_kind=EntityKind.PERSON, label="patient"),
        ],
        propositions=[
            ProviderPropositionCandidate(
                local_ref="denial", actor_ref="patient", conduct_kind=ConductKind.PHYSICAL_CONDUCT,
                target=ProviderTargetCandidate(target_kind=TargetKind.ENTITY, target_ref="nurse"),
                completion=Completion.COMPLETED, contact=Contact.OCCURRED,
                temporal_scope=TemporalScope.CURRENT_INCIDENT,
                intentionality=SemanticIntentionality.INTENTIONAL,
                assertion_status=AssertionStatus.NEGATED,
            ),
            ProviderPropositionCandidate(
                local_ref="possible", actor_ref="patient", conduct_kind=ConductKind.PHYSICAL_CONDUCT,
                target=ProviderTargetCandidate(target_kind=TargetKind.ENTITY, target_ref="nurse"),
                completion=Completion.COMPLETED, contact=Contact.OCCURRED,
                temporal_scope=TemporalScope.CURRENT_INCIDENT,
                intentionality=SemanticIntentionality.INTENTIONAL,
                assertion_status=AssertionStatus.UNCERTAIN,
            ),
        ],
        relationships=[
            ProviderRelationshipCandidate(
                local_ref="denies", relationship_kind=RelationshipKind.NEGATES,
                source_proposition_ref="denial", target_proposition_ref="possible", disputed_dimensions=[],
            )
        ],
        uncertainties=[
            ProviderUncertaintyCandidate(
                local_ref="status", proposition_ref="possible",
                dimension=UncertaintyDimension.ASSERTION_STATUS, note="Narrative says may have.",
            )
        ],
        evidence_excerpts=[
            ProviderEvidenceCandidate(local_ref="denial-evidence", text="Patient denied hitting nurse."),
            ProviderEvidenceCandidate(local_ref="possible-evidence", text="Patient may have hit nurse."),
        ],
        evidence_supports=[
            ProviderEvidenceSupportCandidate(evidence_ref="denial-evidence", subject_kind=EvidenceSubjectKind.PROPOSITION, subject_ref="denial", role=EvidenceSupportRole.SUPPORTS_NEGATION),
            ProviderEvidenceSupportCandidate(evidence_ref="possible-evidence", subject_kind=EvidenceSubjectKind.PROPOSITION, subject_ref="possible", role=EvidenceSupportRole.SUPPORTS_ASSERTION),
            ProviderEvidenceSupportCandidate(evidence_ref="denial-evidence", subject_kind=EvidenceSubjectKind.RELATIONSHIP, subject_ref="denies", role=EvidenceSupportRole.SUPPORTS_NEGATION),
            ProviderEvidenceSupportCandidate(evidence_ref="possible-evidence", subject_kind=EvidenceSubjectKind.UNCERTAINTY, subject_ref="status", role=EvidenceSupportRole.SUPPORTS_UNCERTAINTY),
        ],
        extraction_metadata=ExtractionMetadata(extraction_contract_identity="violence-checker.proposition-extraction@1.0.0"),
    )
    adapted = semantic_candidate_from_provider_response(
        provider,
        incident=Incident(incident_id="CASE_REFS", narrative=narrative),
    )
    assert [item.proposition_id for item in adapted.propositions] == ["PROP-0001", "PROP-0002"]
    assert adapted.relationships[0].source_proposition_ref == "PROP-0002"
    assert adapted.relationships[0].target_proposition_ref == "PROP-0001"
    assert adapted.uncertainties[0].proposition_ref == "PROP-0001"
    assert {item.subject_ref for item in adapted.evidence_supports} == {"PROP-0001", "PROP-0002", "REL-0001", "UNC-0001"}
    assert validate_semantic_candidate(
        adapted,
        incident_id="CASE_REFS",
        normalized_narrative=narrative,
    ).passed


def test_current_pipeline_contains_no_transitional_global_authority():
    forbidden = {"ViolenceFinding", "SemanticFacts", "ValidatedSemanticFacts", "operational_finding", "compatibility_result"}
    for path in ACTIVE_FILES:
        source = Path(path).read_text()
        assert not forbidden.intersection({node.id for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Name)})
        assert "operational_finding" not in source
        assert "compatibility_result" not in source
    assert "operational_finding" not in PipelineResult.model_fields


def test_compatibility_module_is_removed():
    assert not Path("src/compatibility_finding.py").exists()
