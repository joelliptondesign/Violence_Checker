from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.evaluation.contracts import EvaluationCase, ExpectedEvaluationOutcome, ExpectedSemanticOutcome
from src.evaluation.corpus import load_corpus
from src.evaluation.serialization import canonical_json


def test_successor_case_contract_contains_complete_proposition_expectations():
    case = load_corpus().cases[0]
    assert case.ground_truth.semantic_envelope is not None
    assert case.ground_truth.expected_derived is not None
    assert case.ground_truth.policy_decision is not None
    assert case.ground_truth.semantic_envelope.incident_id == case.case_id


def test_success_expectation_rejects_missing_authoritative_subjects():
    with pytest.raises(ValidationError):
        ExpectedEvaluationOutcome(semantic_outcome=ExpectedSemanticOutcome.SUCCESS)


def test_evaluation_contracts_forbid_unknown_fields():
    values = load_corpus().cases[0].model_dump()
    values["unknown"] = True
    with pytest.raises(ValidationError):
        EvaluationCase.model_validate(values)


def test_canonical_serialization_is_deterministic():
    case = load_corpus().cases[0]
    assert canonical_json(case) == canonical_json(case)
