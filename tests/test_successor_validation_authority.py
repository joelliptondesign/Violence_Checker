from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.contracts import (
    AssertionStatus,
    EvidenceSupportRole,
    ExtractionMetadata,
    RelationshipKind,
    SemanticRelationship,
    UncertaintyDimension,
    ValidationFailureStage,
    ValidationIssueCode,
)
from src.evaluation.corpus import load_corpus
from src.semantic_validation import validate_semantic_candidate


CASES = {case.case_id: case for case in load_corpus().cases}


def validate(case_id, candidate=None):
    case = CASES[case_id]
    return validate_semantic_candidate(
        candidate or case.ground_truth.semantic_envelope,
        incident_id=case.case_id,
        normalized_narrative=case.narrative,
    )


def domain_codes(result):
    return [issue.code for issue in result.domain_validation.issues]


def schema_codes(result):
    return [issue.code for issue in result.schema_validation.issues]


def test_all_48_ground_truth_envelopes_pass_and_derivations_match_authority():
    for case in CASES.values():
        result = validate(case.case_id)
        assert result.passed
        assert result.validated_envelope.derived == case.ground_truth.expected_derived


@pytest.mark.parametrize("identifier", ["PROP-0002", "PROP-9999", "P-0001"])
def test_noncanonical_or_invalid_proposition_identifiers_fail_schema(identifier):
    case = CASES["EVAL_001"]
    proposition = case.ground_truth.semantic_envelope.propositions[0].model_copy(
        update={"proposition_id": identifier}
    )
    result = validate(
        case.case_id,
        case.ground_truth.semantic_envelope.model_copy(update={"propositions": [proposition]}),
    )
    assert result.failure_stage == ValidationFailureStage.SCHEMA
    assert set(schema_codes(result)) & {
        ValidationIssueCode.INVALID_IDENTIFIER,
        ValidationIssueCode.INVALID_COLLECTION_ORDER,
        ValidationIssueCode.DANGLING_REFERENCE,
    }


def test_duplicate_semantic_relationship_is_rejected():
    case = CASES["EVAL_020"]
    value = case.ground_truth.semantic_envelope
    duplicate = value.relationships[0].model_copy(update={"relationship_id": "REL-0002"})
    result = validate(case.case_id, value.model_copy(update={"relationships": [*value.relationships, duplicate]}))
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_RELATIONSHIP in domain_codes(result)


def test_supersession_cycle_and_reverse_direction_are_rejected():
    case = CASES["EVAL_020"]
    value = case.ground_truth.semantic_envelope
    reverse = SemanticRelationship(
        relationship_id="REL-0002",
        relationship_kind=RelationshipKind.SUPERSEDES,
        source_proposition_ref="PROP-0001",
        target_proposition_ref="PROP-0002",
        disputed_dimensions=[],
    )
    result = validate(case.case_id, value.model_copy(update={"relationships": [*value.relationships, reverse]}))
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.RELATIONSHIP_CYCLE in domain_codes(result)
    assert ValidationIssueCode.INVALID_RELATIONSHIP in domain_codes(result)


def test_conflict_between_semantically_identical_propositions_is_rejected():
    case = CASES["EVAL_029"]
    value = case.ground_truth.semantic_envelope
    first, second = value.propositions[:2]
    identical = first.model_copy(update={"proposition_id": second.proposition_id})
    candidate = value.model_copy(update={"propositions": [first, identical, *value.propositions[2:]]})
    result = validate(case.case_id, candidate)
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_RELATIONSHIP in domain_codes(result)


def test_uncertainty_requires_an_unresolved_or_disputed_dimension():
    case = next(
        case
        for case in CASES.values()
        if case.ground_truth.semantic_envelope.uncertainties
        and case.ground_truth.semantic_envelope.propositions[0].contact.value != "undetermined"
    )
    value = case.ground_truth.semantic_envelope
    uncertainty = value.uncertainties[0].model_copy(update={"dimension": UncertaintyDimension.CONTACT})
    result = validate(case.case_id, value.model_copy(update={"uncertainties": [uncertainty, *value.uncertainties[1:]]}))
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_UNCERTAINTY in domain_codes(result)


def test_evidence_support_role_must_match_subject_semantics():
    case = CASES["EVAL_001"]
    value = case.ground_truth.semantic_envelope
    support = value.evidence_supports[0].model_copy(update={"role": EvidenceSupportRole.SUPPORTS_UNCERTAINTY})
    result = validate(case.case_id, value.model_copy(update={"evidence_supports": [support]}))
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_EVIDENCE_SUPPORT in domain_codes(result)


def test_every_relationship_requires_evidence_support():
    case = CASES["EVAL_020"]
    value = case.ground_truth.semantic_envelope
    supports = [item for item in value.evidence_supports if item.subject_ref != "REL-0001"]
    result = validate(case.case_id, value.model_copy(update={"evidence_supports": supports}))
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.MISSING_EVIDENCE_SUPPORT in domain_codes(result)


def test_negated_proposition_requires_negation_support_role():
    case = CASES["EVAL_001"]
    value = case.ground_truth.semantic_envelope
    proposition = value.propositions[0].model_copy(update={"assertion_status": AssertionStatus.NEGATED})
    result = validate(case.case_id, value.model_copy(update={"propositions": [proposition, *value.propositions[1:]]}))
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_EVIDENCE_SUPPORT in domain_codes(result)


def test_schema_failure_short_circuits_domain_validator():
    case = CASES["EVAL_001"]
    calls = []

    def domain_validator(*_args, **_kwargs):
        calls.append(True)
        raise AssertionError("domain validator must not run")

    candidate = case.ground_truth.semantic_envelope.model_copy(update={"schema_version": "9.0.0"})
    result = validate_semantic_candidate(
        candidate,
        incident_id=case.case_id,
        normalized_narrative=case.narrative,
        domain_validator=domain_validator,
    )
    assert result.failure_stage == ValidationFailureStage.SCHEMA
    assert calls == []


def test_validation_issue_order_is_repeatable_for_compound_invalid_state():
    case = CASES["EVAL_001"]
    value = case.ground_truth.semantic_envelope
    proposition = value.propositions[0].model_copy(
        update={"actor_ref": "ENT-9999", "proposition_id": "WRONG"}
    )
    candidate = value.model_copy(update={"schema_identity": "wrong", "propositions": [proposition]})
    first = validate(case.case_id, candidate)
    second = validate(case.case_id, deepcopy(candidate))
    assert first.schema_validation.issues == second.schema_validation.issues


@pytest.mark.parametrize(
    "field,value",
    [
        ("extraction_contract_identity", ""),
        ("provider_name", "   "),
        ("model_identifier", ""),
        ("request_id", "\t"),
    ],
)
def test_extraction_metadata_rejects_present_but_empty_identifiers(field, value):
    values = {"extraction_contract_identity": "violence-checker.proposition-extraction@1.0.0"}
    values[field] = value
    with pytest.raises(ValidationError):
        ExtractionMetadata(**values)
