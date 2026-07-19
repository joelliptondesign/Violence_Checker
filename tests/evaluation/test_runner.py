from __future__ import annotations

import ast
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.contracts import (
    PipelineFailureProvenance,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    SemanticFacts,
)
from src.evaluation.case_comparison import compare_case
from src.evaluation.contracts import (
    CaseEvaluationStatus,
    ExpectedField,
    FailurePattern,
)
from src.evaluation.corpus import REPOSITORY_ROOT, load_corpus
from src.evaluation.run_contracts import (
    EvaluationRunArtifact,
    EvaluationRunConfiguration,
    EvaluationRunnerMode,
)
from src.evaluation.runner import (
    RunnerError,
    RunnerIssueCode,
    main,
    run_evaluation,
    select_cases,
    validate_run_configuration,
    write_run_artifact,
)
from src.evaluation.serialization import canonical_json
from src.models import ViolenceEventType
from src.policy import failed_policy_decision
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


RUN_PATH = "evaluation/runs/test-runner-artifact.json"


def configuration(
    *,
    case_ids: tuple[str, ...] = ("EVAL_001",),
    mode: EvaluationRunnerMode = EvaluationRunnerMode.DETERMINISTIC_TEST,
    overwrite: bool = False,
) -> EvaluationRunConfiguration:
    return EvaluationRunConfiguration(
        run_id="TEST_RUN_003_3",
        execution_mode=mode,
        repository_commit="c02c113270988f7d1d25c9aae675be1dc237a393",
        model_identifier="deterministic-test-double" if mode == EvaluationRunnerMode.DETERMINISTIC_TEST else None,
        extraction_configuration_identity="corpus-ground-truth-double",
        run_timestamp=datetime(2026, 7, 18, 20, 0, tzinfo=timezone.utc),
        requested_case_ids=case_ids,
        output_path=RUN_PATH,
        overwrite=overwrite,
    )


class GroundTruthExecutor:
    def __init__(self) -> None:
        self.cases = {case.case_id: case for case in load_corpus().cases}
        self.calls = []

    def __call__(self, incident):
        self.calls.append(incident)
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=self.cases[incident.incident_id].ground_truth.semantic_facts,
        )


def _run_candidate(case_id: str, candidate: SemanticFacts):
    def executor(_incident):
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=candidate,
        )

    return run_evaluation(
        configuration(case_ids=(case_id,)),
        semantic_executor=executor,
        write_artifact=False,
    )


def test_one_case_executes_complete_governed_pipeline() -> None:
    executor = GroundTruthExecutor()

    artifact = run_evaluation(configuration(), semantic_executor=executor, write_artifact=False)
    observed = artifact.observed_cases[0]
    pipeline = observed.pipeline_result

    assert artifact.requested_case_ids == ("EVAL_001",)
    assert artifact.case_evaluations[0].status == CaseEvaluationStatus.MATCH
    assert pipeline.incident.incident_id == "EVAL_001"
    assert pipeline.normalized_incident.incident_id == "EVAL_001"
    assert pipeline.regex_result is not None
    assert observed.semantic_status == "success"
    assert pipeline.validation_result.passed is True
    assert pipeline.semantic_facts is not None
    assert pipeline.operational_finding is not None
    assert pipeline.policy_decision.outcome == PolicyOutcome.WRITE_DETECTED
    assert observed.pipeline_comparison.display_status
    assert pipeline.salesforce_payload is not None
    assert len(executor.calls) == 1


def test_full_48_case_deterministic_execution_is_stable_and_all_matches() -> None:
    executor = GroundTruthExecutor()
    config = configuration(case_ids=())

    first = run_evaluation(config, semantic_executor=executor, write_artifact=False)
    second_executor = GroundTruthExecutor()
    second = run_evaluation(config, semantic_executor=second_executor, write_artifact=False)

    assert len(first.observed_cases) == 48
    assert len(executor.calls) == 48
    assert first.summary.match_count == 48
    assert first.summary.partial_mismatch_count == 0
    assert first.summary.failure_count == 0
    assert first.summary.non_comparable_count == 0
    assert canonical_json(first) == canonical_json(second)


def test_selected_cases_return_canonical_order() -> None:
    executor = GroundTruthExecutor()

    artifact = run_evaluation(
        configuration(case_ids=("EVAL_012", "EVAL_002", "EVAL_008")),
        semantic_executor=executor,
        write_artifact=False,
    )

    assert artifact.requested_case_ids == ("EVAL_002", "EVAL_008", "EVAL_012")
    assert [call.incident_id for call in executor.calls] == list(artifact.requested_case_ids)


def test_unknown_selection_is_rejected_before_semantic_execution() -> None:
    executor = GroundTruthExecutor()

    with pytest.raises(RunnerError) as exc_info:
        run_evaluation(
            configuration(case_ids=("EVAL_UNKNOWN",)),
            semantic_executor=executor,
            write_artifact=False,
        )

    assert exc_info.value.code == RunnerIssueCode.UNKNOWN_CASE_IDENTIFIER
    assert executor.calls == []


def test_duplicate_selection_is_rejected_before_semantic_execution() -> None:
    corpus = load_corpus()

    with pytest.raises(RunnerError) as exc_info:
        select_cases(corpus, ("EVAL_001", "EVAL_001"))

    assert exc_info.value.code == RunnerIssueCode.DUPLICATE_CASE_IDENTIFIER


def test_metadata_and_ground_truth_are_excluded_from_semantic_input() -> None:
    executor = GroundTruthExecutor()
    case = load_corpus().cases[0]

    artifact = run_evaluation(configuration(), semantic_executor=executor, write_artifact=False)

    assert executor.calls[0].model_dump() == {
        "incident_id": case.case_id,
        "narrative": case.narrative,
    }
    assert artifact.observed_cases[0].pipeline_result.incident.narrative == case.narrative
    assert case.metadata.engineering_notes not in executor.calls[0].narrative
    assert "ground_truth" not in executor.calls[0].narrative


def test_comparable_semantic_field_mismatch_has_stable_path_and_pattern() -> None:
    case = load_corpus().cases[0]
    changed = case.ground_truth.semantic_facts.model_copy(update={"actor": "visitor"})
    calls = []

    def executor(incident):
        calls.append(incident)
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=changed,
        )

    artifact = run_evaluation(configuration(), semantic_executor=executor, write_artifact=False)
    result = artifact.case_evaluations[0]

    assert result.status == CaseEvaluationStatus.PARTIAL_MISMATCH
    assert [difference.field for difference in result.field_differences] == [
        "semantic_facts.actor",
        "compatibility_finding",
    ]
    assert FailurePattern.SEMANTIC_FIELD_MISMATCH in result.failure_patterns
    assert FailurePattern.COMPATIBILITY_DIFFERENCE in result.failure_patterns
    assert FailurePattern.COMPATIBILITY_FAILURE not in result.failure_patterns


def test_genuine_compatibility_construction_failure_is_classified_as_failure() -> None:
    artifact = run_evaluation(
        configuration(),
        semantic_executor=GroundTruthExecutor(),
        write_artifact=False,
    )
    case = load_corpus().cases[0]
    observed = artifact.observed_cases[0]
    failed_policy = failed_policy_decision(
        PipelineFailureProvenance.COMPATIBILITY_CONSTRUCTION
    )
    failed_pipeline = observed.pipeline_result.model_copy(
        update={
            "operational_finding": None,
            "policy_decision": failed_policy,
            "salesforce_payload": None,
        }
    )
    failed_observed = observed.model_copy(
        update={
            "failure_provenance": PipelineFailureProvenance.COMPATIBILITY_CONSTRUCTION,
            "pipeline_result": failed_pipeline,
        }
    )

    result = compare_case(case, failed_observed)

    assert result.status == CaseEvaluationStatus.FAILURE
    assert FailurePattern.COMPATIBILITY_FAILURE in result.failure_patterns
    assert FailurePattern.COMPATIBILITY_DIFFERENCE not in result.failure_patterns
    assert "compatibility_finding" in {
        difference.field for difference in result.field_differences
    }


@pytest.mark.parametrize(
    ("case_id", "evidence"),
    [
        ("EVAL_001", ["struck a nurse on the shoulder"]),
        (
            "EVAL_001",
            [
                "Patient struck a nurse on the shoulder with a closed fist during medication administration."
            ],
        ),
        ("EVAL_023", ["no aggression", "no threats"]),
    ],
)
def test_evidence_equality_containment_and_segmentation_are_equivalent(
    case_id: str,
    evidence: list[str],
) -> None:
    case = next(case for case in load_corpus().cases if case.case_id == case_id)
    candidate = case.ground_truth.semantic_facts.model_copy(
        update={"evidence_text": evidence}
    )
    result = _run_candidate(case_id, candidate).case_evaluations[0]

    assert "semantic_facts.evidence_text" not in {
        difference.field for difference in result.field_differences
    }
    assert FailurePattern.UNSUPPORTED_EVIDENCE not in result.failure_patterns
    assert FailurePattern.EVIDENCE_OMISSION not in result.failure_patterns


def test_genuinely_unsupported_evidence_is_detected_without_false_omission() -> None:
    case = load_corpus().cases[0]
    candidate = case.ground_truth.semantic_facts.model_copy(
        update={
            "evidence_text": [
                *case.ground_truth.semantic_facts.evidence_text,
                "text absent from the supplied narrative",
            ]
        }
    )
    result = _run_candidate(case.case_id, candidate).case_evaluations[0]

    assert FailurePattern.UNSUPPORTED_EVIDENCE in result.failure_patterns
    assert FailurePattern.EVIDENCE_OMISSION not in result.failure_patterns


def test_genuinely_missing_expected_evidence_is_detected_without_unsupported_label() -> None:
    case = load_corpus().cases[0]
    candidate = case.ground_truth.semantic_facts.model_copy(
        update={"evidence_text": []}
    )
    result = _run_candidate(case.case_id, candidate).case_evaluations[0]

    assert FailurePattern.EVIDENCE_OMISSION in result.failure_patterns
    assert FailurePattern.UNSUPPORTED_EVIDENCE not in result.failure_patterns


def test_event_type_and_uncertainty_note_disagreements_have_distinct_labels() -> None:
    case = load_corpus().cases[0]
    event_candidate = case.ground_truth.semantic_facts.model_copy(
        update={"event_type": ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE}
    )
    event_result = _run_candidate(case.case_id, event_candidate).case_evaluations[0]

    assert FailurePattern.EVENT_TYPE_DISAGREEMENT in event_result.failure_patterns
    assert FailurePattern.UNCERTAINTY_NOTE_DIFFERENCE not in event_result.failure_patterns
    assert FailurePattern.EXCESSIVE_UNCERTAINTY not in event_result.failure_patterns
    assert FailurePattern.INSUFFICIENT_UNCERTAINTY not in event_result.failure_patterns

    note_candidate = case.ground_truth.semantic_facts.model_copy(
        update={"uncertainty_notes": ["Exact deterministic note disagreement."]}
    )
    note_result = _run_candidate(case.case_id, note_candidate).case_evaluations[0]

    assert FailurePattern.UNCERTAINTY_NOTE_DIFFERENCE in note_result.failure_patterns
    assert FailurePattern.EVENT_TYPE_DISAGREEMENT not in note_result.failure_patterns
    assert FailurePattern.EXCESSIVE_UNCERTAINTY not in note_result.failure_patterns
    assert FailurePattern.INSUFFICIENT_UNCERTAINTY not in note_result.failure_patterns


def test_expected_success_with_domain_rejection_is_failure_not_provider_failure() -> None:
    invalid = SemanticFacts.model_construct(
        **{
            **load_corpus().cases[0].ground_truth.semantic_facts.model_dump(),
            "event_type": ViolenceEventType.NONE,
        }
    )

    def executor(_incident):
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=invalid,
        )

    artifact = run_evaluation(configuration(), semantic_executor=executor, write_artifact=False)
    result = artifact.case_evaluations[0]

    assert result.status == CaseEvaluationStatus.FAILURE
    assert FailurePattern.VALIDATION_REJECTION in result.failure_patterns
    assert FailurePattern.PROVIDER_FAILURE not in result.failure_patterns
    assert FailurePattern.COMPATIBILITY_FAILURE not in result.failure_patterns
    assert FailurePattern.COMPATIBILITY_DIFFERENCE not in result.failure_patterns
    assert "compatibility_finding" not in {
        difference.field for difference in result.field_differences
    }
    assert artifact.summary.validation_rejection_count == 1
    assert artifact.summary.provider_failure_count == 0


def test_provider_failure_is_non_comparable_without_semantic_differences() -> None:
    def executor(_incident):
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.REQUEST_FAILURE,
            failure_message="TestProviderFailure",
        )

    artifact = run_evaluation(configuration(), semantic_executor=executor, write_artifact=False)
    result = artifact.case_evaluations[0]

    assert result.status == CaseEvaluationStatus.NON_COMPARABLE
    assert result.field_differences == []
    assert result.failure_patterns == [FailurePattern.PROVIDER_FAILURE]
    assert artifact.summary.provider_failure_count == 1


def test_policy_only_mismatch_and_non_asserted_policy_behavior() -> None:
    executor = GroundTruthExecutor()
    artifact = run_evaluation(configuration(), semantic_executor=executor, write_artifact=False)
    case = load_corpus().cases[0]
    observed = artifact.observed_cases[0]
    changed_policy = PolicyDecision(
        policy_id="violence_checker_write_disposition",
        policy_version="1.0.1",
        outcome=PolicyOutcome.WRITE_UNCERTAIN,
        reason_codes=[PolicyReasonCode.UNCLEAR_EVENT_TYPE],
        explanation="Validated facts contain explicit unresolved uncertainty for application representation.",
    )
    changed_pipeline = observed.pipeline_result.model_copy(update={"policy_decision": changed_policy})
    changed_observed = observed.model_copy(update={"pipeline_result": changed_pipeline})

    compared = compare_case(case, changed_observed)
    assert compared.status == CaseEvaluationStatus.PARTIAL_MISMATCH
    assert [item.field for item in compared.field_differences] == [
        "policy_decision.outcome",
        "policy_decision.reason_codes",
    ]
    assert compared.failure_patterns == [FailurePattern.POLICY_MISMATCH]

    unasserted_truth = case.ground_truth.model_copy(
        update={
            "intentionally_not_asserted": [
                *case.ground_truth.intentionally_not_asserted,
                ExpectedField.POLICY_DECISION,
            ]
        }
    )
    unasserted_case = case.model_copy(update={"ground_truth": unasserted_truth})
    assert compare_case(unasserted_case, changed_observed).status == CaseEvaluationStatus.MATCH


def test_historical_failure_pattern_is_deterministic() -> None:
    case = next(case for case in load_corpus().cases if case.case_id == "EVAL_017")
    changed = case.ground_truth.semantic_facts.model_copy(update={"current_event": True})

    def executor(_incident):
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=changed,
        )

    artifact = run_evaluation(
        configuration(case_ids=("EVAL_017",)),
        semantic_executor=executor,
        write_artifact=False,
    )

    assert FailurePattern.HISTORICAL_CURRENT_CONFUSION in artifact.case_evaluations[0].failure_patterns


def test_artifact_is_strict_immutable_and_canonical() -> None:
    artifact = run_evaluation(
        configuration(),
        semantic_executor=GroundTruthExecutor(),
        write_artifact=False,
    )
    serialized = canonical_json(artifact)

    assert serialized == canonical_json(artifact)
    with pytest.raises(ValidationError):
        artifact.run_id = "changed"
    payload = artifact.model_dump(mode="json")
    payload["provider_sdk_object"] = "forbidden"
    with pytest.raises(ValidationError):
        EvaluationRunArtifact.model_validate(payload)


def test_artifact_overwrite_is_refused_by_default_and_explicit_when_enabled() -> None:
    target = REPOSITORY_ROOT / RUN_PATH
    target.unlink(missing_ok=True)
    artifact = run_evaluation(
        configuration(),
        semantic_executor=GroundTruthExecutor(),
        write_artifact=False,
    )
    try:
        write_run_artifact(artifact, RUN_PATH)
        first = target.read_text(encoding="utf-8")
        with pytest.raises(RunnerError) as exc_info:
            write_run_artifact(artifact, RUN_PATH)
        assert exc_info.value.code == RunnerIssueCode.ARTIFACT_EXISTS
        write_run_artifact(artifact, RUN_PATH, overwrite=True)
        assert target.read_text(encoding="utf-8") == first
    finally:
        target.unlink(missing_ok=True)


def test_mode_separation_requires_or_forbids_explicit_executor() -> None:
    with pytest.raises(RunnerError) as deterministic_error:
        run_evaluation(configuration(), write_artifact=False)
    assert deterministic_error.value.code == RunnerIssueCode.DETERMINISTIC_EXECUTOR_REQUIRED

    with pytest.raises(RunnerError) as live_error:
        run_evaluation(
            configuration(mode=EvaluationRunnerMode.LIVE_PROVIDER),
            semantic_executor=GroundTruthExecutor(),
            write_artifact=False,
        )
    assert live_error.value.code == RunnerIssueCode.EXECUTOR_NOT_ALLOWED


def test_configuration_validation_and_import_make_no_provider_call(monkeypatch: pytest.MonkeyPatch) -> None:
    import openai

    def fail_provider(*args: object, **kwargs: object) -> None:
        raise AssertionError("configuration validation must not construct provider client")

    monkeypatch.setattr(openai, "OpenAI", fail_provider)

    assert len(validate_run_configuration(configuration())) == 1
    assert main(
        [
            "validate",
            "--mode",
            "live_provider",
            "--run-id",
            "VALIDATE_ONLY",
            "--repository-commit",
            "c02c113270988f7d1d25c9aae675be1dc237a393",
            "--output",
            "evaluation/runs/validate-only.json",
            "--case",
            "EVAL_001",
            "--timestamp",
            "2026-07-18T20:00:00Z",
        ]
    ) == 0


def test_runner_source_has_no_openai_import_or_provider_request() -> None:
    path = REPOSITORY_ROOT / "src" / "evaluation" / "runner.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imports.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert "openai" not in imports
    assert "responses.parse" not in source


def test_corpus_and_fixture_authorities_remain_byte_for_byte_unchanged() -> None:
    corpus = (REPOSITORY_ROOT / "evaluation" / "corpus" / "corpus.json").read_bytes()
    fixtures = (REPOSITORY_ROOT / "src" / "fixtures.py").read_bytes()

    assert hashlib.sha256(corpus).hexdigest() == (
        "5e981e374d5c767a42e50e3447c192368cd9f8b578bd428c13649d97e8768dcb"
    )
    assert hashlib.sha256(fixtures).hexdigest() == (
        "8b99c65481d9f9642bbed5e2b194c4727d78ad6c3c2f32d78a9935e2c258d271"
    )
