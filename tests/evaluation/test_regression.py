import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.evaluation import baseline, regression
from src.evaluation.baseline import BaselineError, BaselineIssueCode, accept_baseline, load_baseline_artifact, load_run_artifact
from src.evaluation.legacy_artifacts import LegacyArtifact, compare_artifact_families
from src.evaluation.regression import RegressionError, RegressionIssueCode, compare_run, load_regression_artifact


HISTORICAL = [
    "evaluation/runs/initial-operational-evaluation-001.json",
    "evaluation/baselines/initial-evaluation-baseline-001.json",
    "evaluation/reports/initial-operational-comparison-001.json",
    "evaluation/reports/initial-operational-evaluation-001.md",
]


def test_creation_time_json_artifacts_route_to_strict_legacy_readers():
    run = load_run_artifact(HISTORICAL[0])
    baseline = load_baseline_artifact(HISTORICAL[1])
    comparison = load_regression_artifact(HISTORICAL[2])
    assert all(isinstance(item, LegacyArtifact) for item in (run, baseline, comparison))
    assert [item.artifact_kind for item in (run, baseline, comparison)] == ["run", "baseline", "comparison"]
    assert all(item.evaluation_schema_version == "1.0.0" for item in (run, baseline, comparison))


def test_cross_schema_families_are_explicitly_incomparable():
    result = compare_artifact_families("1.0.0", "3.0.0")
    assert result.comparable is False
    assert result.reason == "schema_families_are_incomparable"


def test_historical_artifact_loading_does_not_change_bytes():
    before = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in HISTORICAL}
    load_run_artifact(HISTORICAL[0])
    load_baseline_artifact(HISTORICAL[1])
    load_regression_artifact(HISTORICAL[2])
    after = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in HISTORICAL}
    assert before == after


def test_historical_markdown_report_remains_creation_time_document():
    text = Path(HISTORICAL[3]).read_text()
    assert text.startswith("# Evaluation Engineering Report")
    assert "INITIAL_OPERATIONAL_EVALUATION_001" in text


def test_legacy_reader_exposes_read_only_top_level_creation_time_data():
    artifact = load_run_artifact(HISTORICAL[0])
    with pytest.raises(TypeError):
        artifact.data["run_id"] = "changed"


def test_malformed_and_unsupported_run_schemas_fail_without_fallback(monkeypatch, tmp_path):
    runs = tmp_path / "evaluation" / "runs"
    runs.mkdir(parents=True)
    monkeypatch.setattr(baseline, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(baseline, "RUNS_ROOT", runs)

    malformed = runs / "malformed.json"
    malformed.write_text(json.dumps({"evaluation_schema_version": "1.0.0"}), encoding="utf-8")
    unsupported = runs / "unsupported.json"
    unsupported.write_text(json.dumps({"evaluation_schema_version": "9.0.0"}), encoding="utf-8")

    for path in (malformed, unsupported):
        with pytest.raises(BaselineError) as error:
            load_run_artifact(str(path))
        assert error.value.code == BaselineIssueCode.INVALID_ARTIFACT


def test_legacy_run_cannot_be_promoted_to_successor_baseline():
    output = "evaluation/baselines/legacy-promotion-must-not-exist.json"
    assert not Path(output).exists()
    with pytest.raises(BaselineError) as error:
        accept_baseline(
            baseline_id="INVALID_LEGACY_PROMOTION",
            run_path=HISTORICAL[0],
            output_path=output,
            acceptance_repository_commit="test",
            accepted_at=datetime.now(timezone.utc),
        )
    assert error.value.code == BaselineIssueCode.INVALID_ARTIFACT
    assert not Path(output).exists()


def test_legacy_baseline_and_run_are_rejected_by_current_regression():
    output = "evaluation/reports/legacy-cross-family-must-not-exist.json"
    assert not Path(output).exists()
    with pytest.raises(RegressionError) as error:
        compare_run(
            baseline_path=HISTORICAL[1],
            current_run_path=HISTORICAL[0],
            comparison_id="INVALID_LEGACY_COMPARISON",
            comparison_timestamp=datetime.now(timezone.utc),
            output_path=output,
        )
    assert error.value.code == RegressionIssueCode.INCOMPATIBLE_SCHEMA
    assert not Path(output).exists()
