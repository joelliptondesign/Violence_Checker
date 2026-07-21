import pytest
from pydantic import ValidationError

from src.evaluation.contracts import EvaluationCase, ExpectedEvaluationOutcome
from src.evaluation.corpus import EVALUATION_SCHEMA_VERSION, load_corpus
from src.evaluation.serialization import canonical_json


def test_true_north_case_contract_contains_only_operational_expectations():
    case = load_corpus().cases[0]
    assert EVALUATION_SCHEMA_VERSION == "3.0.0"
    assert set(ExpectedEvaluationOutcome.model_fields) == {
        "semantic_outcome", "deterministic_outcome", "qualifying_conduct",
        "incident_direction", "operational_facts", "processing_status",
        "completeness_status", "validation_failure_stage",
        "validation_issue_codes", "doctrine_compliance",
    }
    rendered = str(case.ground_truth.model_dump(mode="json")).lower()
    assert not any(term in rendered for term in ("proposition", "entity", "relationship", "policycandidate"))


def test_evaluation_contracts_are_strict_and_serialization_is_deterministic():
    case = load_corpus().cases[0]
    values = case.model_dump()
    values["unknown"] = True
    with pytest.raises(ValidationError):
        EvaluationCase.model_validate(values)
    assert canonical_json(case) == canonical_json(case)
