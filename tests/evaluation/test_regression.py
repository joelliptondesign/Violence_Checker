from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.evaluation.artifact_cli import main
from src.evaluation.baseline import BaselineError, BaselineIssueCode, accept_baseline
from src.evaluation.contracts import BaselineClassification, FailurePattern
from src.evaluation.corpus import REPOSITORY_ROOT, load_corpus
from src.evaluation.regression import (
    RegressionError,
    RegressionIssueCode,
    compare_artifacts,
    compare_run,
)
from src.evaluation.reporting import generate_report, render_engineering_report
from src.evaluation.run_contracts import (
    EvaluationRunConfiguration,
    EvaluationRunnerMode,
)
from src.evaluation.runner import run_evaluation, write_run_artifact
from src.evaluation.serialization import canonical_json
from src.models import ViolenceEventType
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


TIMESTAMP = datetime(2026, 7, 19, 2, 0, tzinfo=timezone.utc)
CASE_IDS = ("EVAL_001", "EVAL_002", "EVAL_003", "EVAL_004")
BASE_RUN = "evaluation/runs/test-regression-baseline-run.json"
CURRENT_RUN = "evaluation/runs/test-regression-current-run.json"
BASELINE_ONE = "evaluation/baselines/test-accepted-baseline-v1.json"
BASELINE_TWO = "evaluation/baselines/test-accepted-baseline-v2.json"
REGRESSION_PATH = "evaluation/reports/test-regression-comparison.json"
REPORT_PATH = "evaluation/reports/test-engineering-report.md"


ALL_TEST_ARTIFACTS = (
    BASE_RUN,
    CURRENT_RUN,
    BASELINE_ONE,
    BASELINE_TWO,
    REGRESSION_PATH,
    REPORT_PATH,
)


@pytest.fixture(autouse=True)
def clean_test_artifacts():
    for path in ALL_TEST_ARTIFACTS:
        (REPOSITORY_ROOT / path).unlink(missing_ok=True)
    yield
    for path in ALL_TEST_ARTIFACTS:
        (REPOSITORY_ROOT / path).unlink(missing_ok=True)


def _configuration(run_id: str, output_path: str) -> EvaluationRunConfiguration:
    return EvaluationRunConfiguration(
        run_id=run_id,
        execution_mode=EvaluationRunnerMode.DETERMINISTIC_TEST,
        repository_commit="01af87cf338e4b81f8e1cee30016e8f34d88bee4",
        model_identifier="offline-regression-double",
        extraction_configuration_identity="regression-test-evidence",
        run_timestamp=TIMESTAMP,
        requested_case_ids=CASE_IDS,
        output_path=output_path,
    )


def _artifacts():
    cases = {case.case_id: case for case in load_corpus().cases}
    baseline_candidates = {
        case_id: cases[case_id].ground_truth.semantic_facts for case_id in CASE_IDS
    }
    baseline_candidates["EVAL_001"] = baseline_candidates["EVAL_001"].model_copy(
        update={"actor": "baseline actor one"}
    )
    baseline_candidates["EVAL_002"] = baseline_candidates["EVAL_002"].model_copy(
        update={"actor": "baseline actor two"}
    )

    def baseline_executor(incident):
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=baseline_candidates[incident.incident_id],
        )

    invalid = cases["EVAL_003"].ground_truth.semantic_facts.model_construct(
        **{
            **cases["EVAL_003"].ground_truth.semantic_facts.model_dump(),
            "event_type": ViolenceEventType.NONE,
        }
    )

    def current_executor(incident):
        if incident.incident_id == "EVAL_002":
            candidate = cases[incident.incident_id].ground_truth.semantic_facts.model_copy(
                update={"actor": "current different mismatch"}
            )
            return SemanticExtractionResult(
                status=SemanticExtractionStatus.SUCCESS,
                semantic_candidate=candidate,
            )
        if incident.incident_id == "EVAL_003":
            return SemanticExtractionResult(
                status=SemanticExtractionStatus.SUCCESS,
                semantic_candidate=invalid,
            )
        if incident.incident_id == "EVAL_004":
            return SemanticExtractionResult(
                status=SemanticExtractionStatus.REQUEST_FAILURE,
                failure_message="OfflineProviderFailure",
            )
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=cases[incident.incident_id].ground_truth.semantic_facts,
        )

    baseline_run = run_evaluation(
        _configuration("REGRESSION_BASELINE_RUN", BASE_RUN),
        semantic_executor=baseline_executor,
        write_artifact=False,
    )
    current_run = run_evaluation(
        _configuration("REGRESSION_CURRENT_RUN", CURRENT_RUN),
        semantic_executor=current_executor,
        write_artifact=False,
    )
    return baseline_run, current_run


def _write_runs():
    baseline_run, current_run = _artifacts()
    write_run_artifact(baseline_run, BASE_RUN)
    write_run_artifact(current_run, CURRENT_RUN)
    return baseline_run, current_run


def _accept():
    baseline_run, current_run = _write_runs()
    accepted = accept_baseline(
        baseline_id="TEST_BASELINE_V1",
        run_path=BASE_RUN,
        output_path=BASELINE_ONE,
        acceptance_repository_commit="01af87cf338e4b81f8e1cee30016e8f34d88bee4",
        accepted_at=TIMESTAMP,
    )
    return accepted, current_run


def test_baseline_creation_is_explicit_strict_immutable_and_canonical() -> None:
    accepted, _ = _accept()
    stored = (REPOSITORY_ROOT / BASELINE_ONE).read_text(encoding="utf-8")

    assert accepted.baseline_id == "TEST_BASELINE_V1"
    assert accepted.accepted_run_id == "REGRESSION_BASELINE_RUN"
    assert accepted.requested_case_ids == CASE_IDS
    assert stored == canonical_json(accepted) + "\n"
    with pytest.raises(ValidationError):
        accepted.baseline_id = "changed"
    payload = accepted.model_dump(mode="json")
    payload["unknown"] = True
    with pytest.raises(ValidationError):
        type(accepted).model_validate(payload)


def test_baseline_overwrite_refusal_and_explicit_new_id_replacement() -> None:
    accepted, _ = _accept()
    original = (REPOSITORY_ROOT / BASELINE_ONE).read_bytes()

    with pytest.raises(BaselineError) as exc_info:
        accept_baseline(
            baseline_id="TEST_BASELINE_V1",
            run_path=BASE_RUN,
            output_path=BASELINE_ONE,
            acceptance_repository_commit="01af87cf338e4b81f8e1cee30016e8f34d88bee4",
            accepted_at=TIMESTAMP,
        )
    assert exc_info.value.code == BaselineIssueCode.BASELINE_EXISTS

    replacement = accept_baseline(
        baseline_id="TEST_BASELINE_V2",
        run_path=CURRENT_RUN,
        output_path=BASELINE_TWO,
        acceptance_repository_commit="01af87cf338e4b81f8e1cee30016e8f34d88bee4",
        accepted_at=TIMESTAMP,
        replaces_baseline_path=BASELINE_ONE,
    )
    assert replacement.provenance.replaces_baseline_id == accepted.baseline_id
    assert (REPOSITORY_ROOT / BASELINE_ONE).read_bytes() == original


def test_regression_classifications_and_deltas_are_deterministic() -> None:
    accepted, current = _accept()
    first = compare_artifacts(
        baseline=accepted,
        current=current,
        comparison_id="TEST_COMPARISON",
        comparison_timestamp=TIMESTAMP,
    )
    second = compare_artifacts(
        baseline=accepted,
        current=current,
        comparison_id="TEST_COMPARISON",
        comparison_timestamp=TIMESTAMP,
    )

    assert [item.classification for item in first.case_regressions] == [
        BaselineClassification.IMPROVED,
        BaselineClassification.UNCHANGED,
        BaselineClassification.DEGRADED,
        BaselineClassification.INCOMPARABLE,
    ]
    changed_mismatch = first.case_regressions[1]
    assert changed_mismatch.field_differences_introduced
    assert changed_mismatch.field_differences_resolved
    assert "without classifying it as improvement" in changed_mismatch.explanation
    assert first.case_regressions[2].validation_stage_change is not None
    assert first.case_regressions[2].policy_outcome_change is not None
    assert first.case_regressions[3].current_failure_patterns == (FailurePattern.PROVIDER_FAILURE,)
    assert first.summary.improved == 1
    assert first.summary.degraded == 1
    assert first.summary.unchanged == 1
    assert first.summary.incomparable == 1
    assert first.summary.provider_failures == 1
    assert canonical_json(first) == canonical_json(second)


def test_compare_run_writes_canonical_artifact_and_refuses_missing_baseline() -> None:
    _accept()
    artifact = compare_run(
        baseline_path=BASELINE_ONE,
        current_run_path=CURRENT_RUN,
        comparison_id="TEST_COMPARISON",
        comparison_timestamp=TIMESTAMP,
        output_path=REGRESSION_PATH,
    )
    assert (REPOSITORY_ROOT / REGRESSION_PATH).read_text(encoding="utf-8") == canonical_json(artifact) + "\n"

    with pytest.raises(BaselineError) as exc_info:
        compare_run(
            baseline_path="evaluation/baselines/missing.json",
            current_run_path=CURRENT_RUN,
            comparison_id="MISSING_BASELINE",
            comparison_timestamp=TIMESTAMP,
            output_path="evaluation/reports/missing-baseline.json",
        )
    assert exc_info.value.code == BaselineIssueCode.BASELINE_MISSING


def test_engineering_report_has_required_stable_order_and_observed_evidence() -> None:
    accepted, current = _accept()
    regression = compare_artifacts(
        baseline=accepted,
        current=current,
        comparison_id="TEST_COMPARISON",
        comparison_timestamp=TIMESTAMP,
    )
    first = render_engineering_report(regression)
    second = render_engineering_report(regression)
    headings = [
        "## 1. Run provenance",
        "## 2. Corpus identity",
        "## 3. Evaluation coverage",
        "## 4. Overall summary",
        "## 5. Regression summary",
        "## 6. Most frequent failure patterns",
        "## 7. Validation observations",
        "## 8. Policy observations",
        "## 9. Representative difficult cases",
        "## 10. Engineering opportunities",
    ]

    assert first == second
    assert [first.index(heading) for heading in headings] == sorted(first.index(heading) for heading in headings)
    assert "`provider_failure`: 1" in first
    assert "EVAL_003" in first
    assert "prompt" not in first.lower()


def test_command_interface_accepts_compares_and_generates_without_provider(capsys) -> None:
    _write_runs()
    accepted_at = "2026-07-19T02:00:00Z"
    assert main([
        "accept-baseline",
        "--baseline-id", "TEST_BASELINE_V1",
        "--run", BASE_RUN,
        "--output", BASELINE_ONE,
        "--acceptance-repository-commit", "01af87cf338e4b81f8e1cee30016e8f34d88bee4",
        "--accepted-at", accepted_at,
    ]) == 0
    assert '"status": "accepted"' in capsys.readouterr().out

    assert main([
        "compare-run",
        "--baseline", BASELINE_ONE,
        "--run", CURRENT_RUN,
        "--comparison-id", "TEST_COMPARISON",
        "--timestamp", accepted_at,
        "--output", REGRESSION_PATH,
    ]) == 0
    assert '"status": "compared"' in capsys.readouterr().out

    assert main([
        "generate-report",
        "--regression", REGRESSION_PATH,
        "--output", REPORT_PATH,
    ]) == 0
    assert '"status": "generated"' in capsys.readouterr().out
    assert (REPOSITORY_ROOT / REPORT_PATH).is_file()


def test_regression_and_reporting_sources_do_not_import_provider() -> None:
    for relative in (
        "src/evaluation/baseline.py",
        "src/evaluation/regression.py",
        "src/evaluation/reporting.py",
        "src/evaluation/artifact_cli.py",
    ):
        source = (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")
        imports = {
            node.module
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imports.update(
            alias.name
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert "openai" not in imports
        assert "src.semantic_extractor" not in imports
        assert "responses.parse" not in source
