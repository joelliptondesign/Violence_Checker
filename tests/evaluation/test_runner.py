from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.evaluation.corpus import load_corpus
from src.evaluation.contracts import FailurePattern
from src.evaluation.runner import RunnerError, RunnerIssueCode, run_evaluation, select_cases
from src.evaluation.run_contracts import EvaluationRunConfiguration, EvaluationRunnerMode
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


def configuration(case_ids=()):
    return EvaluationRunConfiguration(
        run_id="SUCCESSOR_DETERMINISTIC_TEST",
        execution_mode=EvaluationRunnerMode.DETERMINISTIC_TEST,
        repository_commit="367a5369dc43c2d451a8bf2b41776cff85d5c64d",
        run_timestamp=datetime(2026, 7, 19, tzinfo=timezone.utc),
        requested_case_ids=tuple(case_ids),
        output_path="evaluation/runs/successor-deterministic-test.json",
    )


def executor():
    cases = {case.case_id: case for case in load_corpus().cases}
    calls = []
    def execute(incident):
        calls.append(incident.incident_id)
        return SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, cases[incident.incident_id].ground_truth.semantic_envelope)
    return execute, calls


def test_full_48_case_successor_execution_is_stable_and_all_matches():
    execute, calls = executor()
    artifact = run_evaluation(configuration(), semantic_executor=execute, write_artifact=False)
    assert artifact.evaluation_schema_version == "2.0.0"
    assert artifact.semantic_schema_identity == "violence-checker.proposition-semantics"
    assert artifact.summary.match_count == 48
    assert artifact.summary.failure_count == artifact.summary.partial_mismatch_count == 0
    assert calls == [f"EVAL_{index:03d}" for index in range(1, 49)]


def test_one_selected_case_makes_one_semantic_request():
    execute, calls = executor()
    artifact = run_evaluation(configuration(("EVAL_001",)), semantic_executor=execute, write_artifact=False)
    assert artifact.summary.match_count == 1
    assert calls == ["EVAL_001"]


def test_deterministic_mode_requires_explicit_executor():
    with pytest.raises(RunnerError) as error:
        run_evaluation(configuration(), write_artifact=False)
    assert error.value.code == RunnerIssueCode.DETERMINISTIC_EXECUTOR_REQUIRED


def test_live_mode_rejects_injected_executor_before_execution():
    execute, calls = executor()
    config = configuration().model_copy(update={"execution_mode": EvaluationRunnerMode.LIVE_PROVIDER})
    with pytest.raises(RunnerError) as error:
        run_evaluation(config, semantic_executor=execute, write_artifact=False)
    assert error.value.code == RunnerIssueCode.EXECUTOR_NOT_ALLOWED
    assert not calls


def test_proposition_difference_paths_are_identifier_addressed():
    cases = {case.case_id: case for case in load_corpus().cases}
    def changed(incident):
        value = cases[incident.incident_id].ground_truth.semantic_envelope
        proposition = value.propositions[0].model_copy(update={"intentionality": value.propositions[0].intentionality.__class__.UNDETERMINED})
        return SemanticExtractionResult(SemanticExtractionStatus.SUCCESS, value.model_copy(update={"propositions": [proposition]}))
    artifact = run_evaluation(configuration(("EVAL_001",)), semantic_executor=changed, write_artifact=False)
    paths = [item.field for item in artifact.case_evaluations[0].field_differences]
    assert any(path.startswith("propositions[PROP-0001].") for path in paths)


def test_selected_cases_are_returned_in_canonical_corpus_order():
    selected = select_cases(load_corpus(), ("EVAL_010", "EVAL_002"))
    assert [case.case_id for case in selected] == ["EVAL_002", "EVAL_010"]


@pytest.mark.parametrize(
    "case_ids,code",
    [
        (("EVAL_999",), RunnerIssueCode.UNKNOWN_CASE_IDENTIFIER),
        (("EVAL_001", "EVAL_001"), RunnerIssueCode.DUPLICATE_CASE_IDENTIFIER),
    ],
)
def test_invalid_case_selection_stops_before_semantic_execution(case_ids, code):
    execute, calls = executor()
    if code == RunnerIssueCode.DUPLICATE_CASE_IDENTIFIER:
        with pytest.raises(ValidationError):
            configuration(case_ids)
    else:
        with pytest.raises(RunnerError) as error:
            run_evaluation(configuration(case_ids), semantic_executor=execute, write_artifact=False)
        assert error.value.code == code
    assert calls == []


def test_evaluation_metadata_and_ground_truth_never_enter_semantic_input():
    case = load_corpus().cases[0]
    observed = []

    def execute(incident):
        observed.append((incident.incident_id, incident.narrative))
        return SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            case.ground_truth.semantic_envelope,
        )

    run_evaluation(configuration((case.case_id,)), semantic_executor=execute, write_artifact=False)
    assert observed == [(case.case_id, case.narrative)]
    if case.metadata.engineering_notes is not None:
        assert case.metadata.engineering_notes not in case.narrative


def test_expected_evidence_without_observed_exact_coverage_is_an_omission():
    case = load_corpus().cases[0]
    shortened = "Patient struck a nurse on the shoulder"

    def execute(_incident):
        value = case.ground_truth.semantic_envelope
        evidence = value.evidence_excerpts[0].model_copy(update={"text": shortened})
        return SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            value.model_copy(update={"evidence_excerpts": [evidence]}),
        )

    artifact = run_evaluation(
        configuration((case.case_id,)),
        semantic_executor=execute,
        write_artifact=False,
    )
    assert FailurePattern.EVIDENCE_OMISSION in artifact.case_evaluations[0].failure_patterns


def test_fabricated_evidence_is_classified_as_unsupported_validation_failure():
    case = load_corpus().cases[0]

    def execute(_incident):
        value = case.ground_truth.semantic_envelope
        evidence = value.evidence_excerpts[0].model_copy(update={"text": "fabricated evidence"})
        return SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            value.model_copy(update={"evidence_excerpts": [evidence]}),
        )

    artifact = run_evaluation(
        configuration((case.case_id,)),
        semantic_executor=execute,
        write_artifact=False,
    )
    patterns = artifact.case_evaluations[0].failure_patterns
    assert FailurePattern.VALIDATION_FAILURE in patterns
    assert FailurePattern.UNSUPPORTED_EVIDENCE in patterns
