from copy import deepcopy

import pytest

from src.contracts import (
    Completion,
    ConductKind,
    Contact,
    Direction,
    EntityKind,
    EvidenceExcerpt,
    ProviderStructuredResponse,
    SchemaValidationStatus,
    ValidationFailureStage,
    ValidationIssueCode,
)
from src.domain_validation import validate_semantic_domain
from src.schema_validation import validate_semantic_schema
from src.semantic_validation import validate_semantic_candidate
from tests.successor_helpers import envelope


def validate(value, narrative="Patient struck the nurse.", incident_id="CASE_001"):
    return validate_semantic_candidate(value, incident_id=incident_id, normalized_narrative=narrative)


def test_valid_envelope_passes_both_stages_and_derives_interpersonal_active_set():
    result = validate(envelope())
    assert result.passed
    assert result.validated_envelope.derived.active_proposition_ids == ["PROP-0001"]
    assert result.validated_envelope.derived.propositions[0].direction == Direction.INTERPERSONAL


def test_provider_object_is_rejected_before_domain_validation():
    result = validate(envelope(provider=True))
    assert result.failure_stage == ValidationFailureStage.SCHEMA
    assert result.schema_validation.issues[0].code == ValidationIssueCode.PROVIDER_OBJECT_NOT_ALLOWED


@pytest.mark.parametrize("field,value,code", [
    ("schema_identity", "wrong", ValidationIssueCode.UNSUPPORTED_SCHEMA_IDENTITY),
    ("schema_version", "9.0.0", ValidationIssueCode.UNSUPPORTED_SCHEMA_VERSION),
    ("incident_id", "OTHER", ValidationIssueCode.INCIDENT_ID_MISMATCH),
])
def test_identity_failures_are_typed(field, value, code):
    candidate = envelope().model_copy(update={field: value})
    result = validate(candidate)
    assert result.failure_stage == ValidationFailureStage.SCHEMA
    assert code in {issue.code for issue in result.schema_validation.issues}


def test_dangling_references_and_noncanonical_ids_fail_schema():
    proposition = envelope().propositions[0].model_copy(update={"actor_ref": "ENT-9999", "proposition_id": "P1"})
    result = validate(envelope().model_copy(update={"propositions": [proposition]}))
    codes = {item.code for item in result.schema_validation.issues}
    assert ValidationIssueCode.DANGLING_REFERENCE in codes
    assert ValidationIssueCode.INVALID_IDENTIFIER in codes


@pytest.mark.parametrize("conduct,completion,contact", [
    (ConductKind.THREAT_EXPRESSION, Completion.COMPLETED, Contact.OCCURRED),
    (ConductKind.PHYSICAL_CONDUCT, Completion.ATTEMPTED, Contact.OCCURRED),
    (ConductKind.CONTACT_ONLY, Completion.ATTEMPTED, Contact.DID_NOT_OCCUR),
])
def test_invalid_conduct_combinations_fail_domain(conduct, completion, contact):
    proposition = envelope().propositions[0].model_copy(update={"conduct_kind": conduct, "completion": completion, "contact": contact})
    result = validate(envelope().model_copy(update={"propositions": [proposition]}))
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_CONDUCT_COMBINATION in {item.code for item in result.domain_validation.issues}


def test_evidence_must_be_exact_narrative_substring():
    result = validate(envelope(), narrative="Different narrative")
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.EVIDENCE_NOT_CONTAINED in {item.code for item in result.domain_validation.issues}


def test_evidence_excerpt_order_is_validated_against_narrative_occurrence():
    candidate = envelope(narrative="First statement. Second statement.")
    candidate = candidate.model_copy(
        update={
            "evidence_excerpts": [
                EvidenceExcerpt(evidence_id="EVID-0001", text="Second statement."),
                EvidenceExcerpt(evidence_id="EVID-0002", text="First statement."),
            ]
        }
    )
    result = validate(candidate, narrative="First statement. Second statement.")
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_COLLECTION_ORDER in {
        item.code for item in result.domain_validation.issues
    }


def test_supersession_must_point_from_later_to_earlier_proposition():
    from src.evaluation.corpus import load_corpus

    case = next(item for item in load_corpus().cases if item.case_id == "EVAL_020")
    candidate = case.ground_truth.semantic_envelope
    relationship = candidate.relationships[0]
    reversed_relationship = relationship.model_copy(
        update={
            "source_proposition_ref": relationship.target_proposition_ref,
            "target_proposition_ref": relationship.source_proposition_ref,
        }
    )
    result = validate_semantic_candidate(
        candidate.model_copy(update={"relationships": [reversed_relationship]}),
        incident_id=case.case_id,
        normalized_narrative=case.narrative,
    )
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_RELATIONSHIP in {
        item.code for item in result.domain_validation.issues
    }


def test_domain_validation_is_deterministic():
    first = validate(envelope(), narrative="Different narrative")
    second = validate(envelope(), narrative="Different narrative")
    assert first == second
