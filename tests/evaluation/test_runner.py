from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.evaluation.corpus import load_corpus, semantic_candidate_for_case
from src.evaluation.contracts import FailurePattern
from src.evaluation.runner import RunnerError, RunnerIssueCode, run_evaluation, select_cases
from src.evaluation.run_contracts import EvaluationRunConfiguration, EvaluationRunnerMode
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


def configuration(case_ids=()):
    return EvaluationRunConfiguration(
        run_id="TRUE_NORTH_TEST", execution_mode=EvaluationRunnerMode.DETERMINISTIC_TEST,
        repository_commit="289b06c936a0c0db1074a43853413b8337d0e680",
        run_timestamp=datetime(2026, 7, 20, tzinfo=timezone.utc),
        requested_case_ids=tuple(case_ids), output_path="evaluation/runs/true-north-test.json",
    )


def executor():
    cases = {case.case_id: case for case in load_corpus().cases}
    calls = []
    def execute(incident):
        calls.append(incident.incident_id)
        return SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, semantic_candidate_for_case(cases[incident.incident_id]))
    return execute, calls


def test_full_true_north_execution_is_stable_and_all_matches():
    execute, calls = executor()
    artifact = run_evaluation(configuration(), semantic_executor=execute, write_artifact=False)
    assert artifact.evaluation_schema_version == "3.0.0"
    assert artifact.semantic_schema_identity == "violence-checker.true-north-incident-facts"
    assert artifact.summary.match_count == 24
    assert artifact.summary.partial_mismatch_count == artifact.summary.failure_count == 0
    assert calls == [f"TN_{index:03d}" for index in range(1, 25)]


def test_one_selected_case_makes_one_semantic_request():
    execute, calls = executor()
    artifact = run_evaluation(configuration(("TN_001",)), semantic_executor=execute, write_artifact=False)
    assert artifact.summary.match_count == 1 and calls == ["TN_001"]


def test_operational_fact_difference_paths_never_use_retired_graph_terms():
    cases = {case.case_id: case for case in load_corpus().cases}
    def changed(incident):
        candidate = semantic_candidate_for_case(cases[incident.incident_id])
        fact = candidate.facts[0].model_copy(update={"intentionality": candidate.facts[0].intentionality.__class__.ACCIDENTAL})
        return SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, candidate.model_copy(update={"facts": [fact]}))
    artifact = run_evaluation(configuration(("TN_001",)), semantic_executor=changed, write_artifact=False)
    paths = [item.field for item in artifact.case_evaluations[0].field_differences]
    assert paths
    assert not any(term in " ".join(paths) for term in ("proposition", "entity", "relationship"))


def test_selection_and_execution_boundaries_fail_before_requests():
    execute, calls = executor()
    with pytest.raises(RunnerError) as error:
        run_evaluation(configuration(("TN_999",)), semantic_executor=execute, write_artifact=False)
    assert error.value.code == RunnerIssueCode.UNKNOWN_CASE_IDENTIFIER and calls == []
    with pytest.raises(ValidationError):
        configuration(("TN_001", "TN_001"))
    with pytest.raises(RunnerError) as error:
        run_evaluation(configuration(), write_artifact=False)
    assert error.value.code == RunnerIssueCode.DETERMINISTIC_EXECUTOR_REQUIRED


def test_selected_cases_return_in_canonical_order():
    assert [case.case_id for case in select_cases(load_corpus(), ("TN_010", "TN_002"))] == ["TN_002", "TN_010"]
