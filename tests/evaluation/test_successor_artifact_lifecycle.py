from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.evaluation import baseline, regression, reporting, runner
from src.evaluation.baseline import BaselineError, BaselineIssueCode
from src.evaluation.corpus import load_corpus
from src.evaluation.regression import RegressionError, RegressionIssueCode
from src.evaluation.run_contracts import EvaluationRunConfiguration, EvaluationRunnerMode
from src.evaluation.runner import RunnerError, RunnerIssueCode
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


NOW = datetime(2026, 7, 19, tzinfo=timezone.utc)
COMMIT = "367a5369dc43c2d451a8bf2b41776cff85d5c64d"


def _executor():
    cases = {case.case_id: case for case in load_corpus().cases}

    def execute(incident):
        return SemanticExtractionResult(
            SemanticExtractionStatus.SUCCESS,
            cases[incident.incident_id].ground_truth.semantic_envelope,
        )

    return execute


def _roots(monkeypatch, tmp_path: Path) -> dict[str, Path]:
    roots = {
        "repository": tmp_path,
        "runs": tmp_path / "evaluation" / "runs",
        "baselines": tmp_path / "evaluation" / "baselines",
        "reports": tmp_path / "evaluation" / "reports",
    }
    for path in roots.values():
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(runner, "REPOSITORY_ROOT", roots["repository"])
    monkeypatch.setattr(runner, "RUNS_ROOT", roots["runs"])
    monkeypatch.setattr(baseline, "REPOSITORY_ROOT", roots["repository"])
    monkeypatch.setattr(baseline, "RUNS_ROOT", roots["runs"])
    monkeypatch.setattr(baseline, "BASELINES_ROOT", roots["baselines"])
    monkeypatch.setattr(regression, "REPOSITORY_ROOT", roots["repository"])
    monkeypatch.setattr(regression, "REPORTS_ROOT", roots["reports"])
    return roots


def _configuration(output: Path, *, overwrite: bool = False) -> EvaluationRunConfiguration:
    return EvaluationRunConfiguration(
        run_id="SUCCESSOR_ARTIFACT_TEST",
        execution_mode=EvaluationRunnerMode.DETERMINISTIC_TEST,
        repository_commit=COMMIT,
        run_timestamp=NOW,
        requested_case_ids=("EVAL_001",),
        output_path=str(output),
        overwrite=overwrite,
    )


def test_successor_run_write_is_canonical_loadable_and_overwrite_protected(monkeypatch, tmp_path):
    roots = _roots(monkeypatch, tmp_path)
    output = roots["runs"] / "successor.json"

    artifact = runner.run_evaluation(_configuration(output), semantic_executor=_executor())
    first_bytes = output.read_bytes()
    loaded = baseline.load_run_artifact(str(output))

    assert loaded == artifact
    assert first_bytes.endswith(b"\n")
    with pytest.raises(RunnerError) as error:
        runner.run_evaluation(_configuration(output), semantic_executor=_executor())
    assert error.value.code == RunnerIssueCode.ARTIFACT_EXISTS

    rewritten = runner.run_evaluation(
        _configuration(output, overwrite=True),
        semantic_executor=_executor(),
    )
    assert rewritten == artifact
    assert output.read_bytes() == first_bytes


def test_successor_baseline_acceptance_is_explicit_immutable_and_replaceable(monkeypatch, tmp_path):
    roots = _roots(monkeypatch, tmp_path)
    run_path = roots["runs"] / "successor.json"
    runner.run_evaluation(_configuration(run_path), semantic_executor=_executor())
    baseline_path = roots["baselines"] / "baseline-001.json"

    accepted = baseline.accept_baseline(
        baseline_id="SUCCESSOR_BASELINE_001",
        run_path=str(run_path),
        output_path=str(baseline_path),
        acceptance_repository_commit=COMMIT,
        accepted_at=NOW,
    )
    assert baseline.load_baseline_artifact(str(baseline_path)) == accepted
    with pytest.raises(BaselineError) as error:
        baseline.accept_baseline(
            baseline_id="SUCCESSOR_BASELINE_001",
            run_path=str(run_path),
            output_path=str(baseline_path),
            acceptance_repository_commit=COMMIT,
            accepted_at=NOW,
        )
    assert error.value.code == BaselineIssueCode.BASELINE_EXISTS

    replacement_path = roots["baselines"] / "baseline-002.json"
    replacement = baseline.accept_baseline(
        baseline_id="SUCCESSOR_BASELINE_002",
        run_path=str(run_path),
        output_path=str(replacement_path),
        acceptance_repository_commit=COMMIT,
        accepted_at=NOW,
        replaces_baseline_path=str(baseline_path),
    )
    assert replacement.provenance.replaces_baseline_id == accepted.baseline_id


def test_successor_regression_and_report_are_deterministic_and_overwrite_protected(monkeypatch, tmp_path):
    roots = _roots(monkeypatch, tmp_path)
    run_path = roots["runs"] / "successor.json"
    runner.run_evaluation(_configuration(run_path), semantic_executor=_executor())
    baseline_path = roots["baselines"] / "baseline.json"
    baseline.accept_baseline(
        baseline_id="SUCCESSOR_BASELINE",
        run_path=str(run_path),
        output_path=str(baseline_path),
        acceptance_repository_commit=COMMIT,
        accepted_at=NOW,
    )
    comparison_path = roots["reports"] / "comparison.json"
    comparison = regression.compare_run(
        baseline_path=str(baseline_path),
        current_run_path=str(run_path),
        comparison_id="SUCCESSOR_COMPARISON",
        comparison_timestamp=NOW,
        output_path=str(comparison_path),
    )
    assert comparison.summary.unchanged == 1
    assert regression.load_regression_artifact(str(comparison_path)) == comparison
    with pytest.raises(RegressionError) as error:
        regression.compare_run(
            baseline_path=str(baseline_path),
            current_run_path=str(run_path),
            comparison_id="DUPLICATE",
            comparison_timestamp=NOW,
            output_path=str(comparison_path),
        )
    assert error.value.code == RegressionIssueCode.ARTIFACT_EXISTS

    report_path = roots["reports"] / "comparison.md"
    report = reporting.generate_report(
        regression_path=str(comparison_path),
        output_path=str(report_path),
    )
    assert report == report_path.read_text(encoding="utf-8")
    assert "Evaluation schema: `2.0.0`" in report
    assert "Unchanged: 1" in report
    with pytest.raises(RegressionError) as error:
        reporting.generate_report(
            regression_path=str(comparison_path),
            output_path=str(report_path),
        )
    assert error.value.code == RegressionIssueCode.ARTIFACT_EXISTS


@pytest.mark.parametrize(
    "path,code",
    [
        ("outside.json", RunnerIssueCode.OUTPUT_OUTSIDE_RUNS),
        ("evaluation/runs/not-json.txt", RunnerIssueCode.INVALID_OUTPUT_EXTENSION),
    ],
)
def test_run_output_boundary_rejects_outside_and_non_json(monkeypatch, tmp_path, path, code):
    roots = _roots(monkeypatch, tmp_path)
    output = roots["repository"] / path
    with pytest.raises(RunnerError) as error:
        runner.validate_run_configuration(_configuration(output))
    assert error.value.code == code
