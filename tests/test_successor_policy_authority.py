from pathlib import Path

from src.contracts import PolicyOutcome, ProcessingStatus
from src.evaluation.corpus import load_corpus, semantic_candidate_for_case
from src.policy import POLICY_ID, POLICY_VERSION, evaluate_policy
from src.semantic_validation import validate_semantic_candidate


def decision_for(case):
    validation = validate_semantic_candidate(
        semantic_candidate_for_case(case), incident_id=case.case_id,
        normalized_narrative=case.narrative,
    )
    return validation, evaluate_policy(
        validated=validation.validated_envelope,
        processing_status=validation.processing_status,
        completeness_status=validation.completeness_status,
        derived=validation.derived_semantics,
    )


def test_every_corpus_case_matches_direct_four_outcome_policy_authority():
    outcomes = set()
    for case in load_corpus().cases:
        validation, decision = decision_for(case)
        outcomes.add(decision.outcome)
        assert decision.policy_id == POLICY_ID and decision.policy_version == POLICY_VERSION
        assert decision.outcome == case.ground_truth.deterministic_outcome
        assert validation.processing_status == case.ground_truth.processing_status
    assert outcomes == set(PolicyOutcome)


def test_invalid_adversarial_candidates_never_default_to_no_violence():
    for case in load_corpus().cases:
        if case.ground_truth.processing_status == ProcessingStatus.VALIDATION_FAILURE:
            _, decision = decision_for(case)
            assert decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE


def test_policy_module_has_no_provider_or_external_side_effect_imports():
    source = Path("src/policy.py").read_text(encoding="utf-8").lower()
    assert not any(term in source for term in ("openai", "salesforce", "requests"))
