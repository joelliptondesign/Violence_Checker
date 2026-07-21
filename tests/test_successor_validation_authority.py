from copy import deepcopy

from src.contracts import ValidationFailureStage, ValidationIssueCode
from src.evaluation.contracts import AdversarialCondition, ExpectedSemanticOutcome
from src.evaluation.corpus import load_corpus, semantic_candidate_for_case
from src.semantic_validation import validate_semantic_candidate


CASES = {case.case_id: case for case in load_corpus().cases}


def validate(case, candidate=None):
    return validate_semantic_candidate(
        candidate or semantic_candidate_for_case(case),
        incident_id=case.case_id,
        normalized_narrative=case.narrative,
    )


def test_all_corpus_candidates_match_repository_validation_authority():
    for case in CASES.values():
        result = validate(case)
        expected_pass = case.ground_truth.semantic_outcome == ExpectedSemanticOutcome.SUCCESS
        assert result.passed is expected_pass
        assert result.failure_stage == case.ground_truth.validation_failure_stage
        codes = {item.code for item in result.schema_validation.issues + result.domain_validation.issues}
        assert codes == set(case.ground_truth.validation_issue_codes)


def test_contradiction_adversaries_verify_repository_not_provider_behavior():
    by_condition = {case.adversarial_condition: validate(case) for case in CASES.values() if case.adversarial_condition}
    assert ValidationIssueCode.INVALID_EVIDENCE_SUPPORT in {
        issue.code for condition in (
            AdversarialCondition.DENIAL_AS_AFFIRMED,
            AdversarialCondition.ACCIDENTAL_AS_INTENTIONAL,
            AdversarialCondition.HISTORICAL_AS_CURRENT,
            AdversarialCondition.NO_CONTACT_AS_CONTACT,
        ) for issue in by_condition[condition].domain_validation.issues
    }
    assert ValidationIssueCode.INVALID_FACT_COMBINATION in {
        issue.code for issue in by_condition[AdversarialCondition.OBJECT_AS_INTERPERSONAL].domain_validation.issues
    }
    assert ValidationIssueCode.INVALID_CORRECTION_REFERENCE in {
        issue.code for issue in by_condition[AdversarialCondition.OMITTED_CORRECTION].domain_validation.issues
    }
    assert ValidationIssueCode.INVALID_CONTRADICTION_GROUP in {
        issue.code for issue in by_condition[AdversarialCondition.OMITTED_CONTRADICTION].domain_validation.issues
    }
    assert by_condition[AdversarialCondition.BROAD_EVIDENCE_REUSE].passed


def test_schema_failure_short_circuits_domain_and_issue_order_is_repeatable():
    case = CASES["TN_001"]
    candidate = semantic_candidate_for_case(case).model_copy(update={"schema_version": "9.0.0"})
    calls = []
    def domain(*_args, **_kwargs):
        calls.append(True)
    first = validate_semantic_candidate(candidate, incident_id=case.case_id, normalized_narrative=case.narrative, domain_validator=domain)
    second = validate_semantic_candidate(deepcopy(candidate), incident_id=case.case_id, normalized_narrative=case.narrative)
    assert first.failure_stage == ValidationFailureStage.SCHEMA
    assert calls == []
    assert first.schema_validation.issues == second.schema_validation.issues
