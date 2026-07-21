from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

from tools.repo_governance import governance


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_SITREC = REPO_ROOT / "docs" / "SITREC - 2026-07-20 Violence Checker Successor Semantic Baseline.md"
COMMUNICATION_AUTHORITY = REPO_ROOT / "docs" / "operator_communication_tone_guidelines.md"


def test_governance_tooling_imports_without_foxcommand_runtime_path() -> None:
    module = importlib.import_module("tools.repo_governance.governance")

    assert module.DEFAULT_REPOSITORY_TREE_PATH.as_posix() == "docs/generated/repository_tree.txt"
    assert all("foxcommand-runtime" not in value for value in sys.path)


def test_repository_tree_generation_is_stable_and_excludes_secrets() -> None:
    first = governance.build_repository_tree(REPO_ROOT)
    second = governance.build_repository_tree(REPO_ROOT)

    assert first == second
    assert ".git/" not in first
    assert ".env\n" not in first
    assert ".streamlit/secrets.toml" not in first


def test_knowledge_graph_generation_is_stable_and_marks_boundaries() -> None:
    first_text = governance.build_knowledge_graph(REPO_ROOT)
    second_text = governance.build_knowledge_graph(REPO_ROOT)

    assert first_text == second_text
    assert "`src/app_logic.py`" in first_text
    assert "`src/semantic_extractor.py`" in first_text
    assert "Provider-facing components" in first_text
    assert "Unresolved Relationships" in first_text
    assert "`tests/evaluation/test_runner.py`" in first_text
    assert "`src/evaluation/runner.py`" in first_text


def test_generated_artifact_outputs_must_remain_inside_repository() -> None:
    outside = REPO_ROOT.parent / "outside-tree.txt"

    try:
        governance.write_repository_tree(REPO_ROOT, outside)
    except ValueError as error:
        assert "escapes repository root" in str(error)
    else:
        raise AssertionError("expected outside output to fail")


def test_heartbeat_jsonl_validation_accepts_local_telemetry() -> None:
    findings = governance.validate_heartbeat_jsonl(REPO_ROOT / governance.HEARTBEAT_PATH)

    assert findings == []


def test_sitrec_validation_accepts_current_active_sitrec() -> None:
    findings = governance.validate_sitrec_file(ACTIVE_SITREC)
    text = ACTIVE_SITREC.read_text(encoding="utf-8")

    assert findings == []
    assert "Provider authority is limited to semantic candidates" in text
    assert "all eight demonstration fixtures" in text
    assert "24 synthetic operational cases" in text
    assert "Streamlit Community Cloud deployment remains a manual operator follow-on" in text
    assert "no hosted deployment, hosted URL, or hosted acceptance is claimed" in text
    assert "`TrueNorthSemanticEnvelope` is the sole current semantic authority" in text
    assert "True North runtime is active" in text
    assert "Historical evaluation artifacts remain immutable" in text
    assert "docs/workplace_violence_doctrine.md" in text
    assert "docs/true_north_semantic_contract_specification.md" in text
    assert "docs/true_north_migration_strategy.md" in text
    assert "docs/operator_communication_tone_guidelines.md" in text
    assert "Governing presentation policy for every operator-facing communication surface" in text
    assert "Live-provider evaluation, baseline acceptance, deployment, and hosted acceptance remain pending" in text


def test_operator_communication_authority_covers_required_surfaces_and_examples() -> None:
    text = COMMUNICATION_AUTHORITY.read_text(encoding="utf-8")

    assert "The purpose of operator communication is to help a hospital operator understand what happened." in text
    assert "The purpose is not to explain how the software reached its conclusion." in text
    assert "The UI does not expose repository fields one-for-one." in text
    assert "The UI answers operator questions." in text
    assert "## Incident-first principle" in text
    assert "## Classification separation" in text
    assert "If the Incident Summary is not noticeably easier to understand than the original narrative" in text
    assert "## Acceptance checklist" in text
    for surface in (
        "Outcome subtitle",
        "Incident Summary",
        "Key Findings",
        "Why This Result",
        "Operational Facts",
        "Decision Logic",
        "Salesforce Preview",
        "deterministic fallback communication",
        "provider-generated communication",
    ):
        assert surface in text
    for example in (
        "Intentional interpersonal assault",
        "Explicit physical threat",
        "Self-harm",
        "Intentional property violence",
        "Accidental contact",
        "Historical-only conduct",
        "Corrected allegation",
        "Unresolved contradiction",
        "Insufficient information",
    ):
        assert f"### {example}" in text


def test_sitrec_lifecycle_selects_one_active_current_record() -> None:
    assert governance.active_sitrec_paths(REPO_ROOT) == [
        "docs/SITREC - 2026-07-20 Violence Checker Successor Semantic Baseline.md"
    ]
    assert governance.validate_sitrec_lifecycle(REPO_ROOT, "2026-07-20") == []


def test_generated_governance_artifacts_are_fresh() -> None:
    assert governance.validate_generated_freshness(REPO_ROOT) == []


def test_generated_freshness_detects_drift_without_mutating_repository(tmp_path: Path) -> None:
    (tmp_path / "docs" / "generated").mkdir(parents=True)
    (tmp_path / "docs" / "generated" / "repository_tree.txt").write_text("stale\n")
    (tmp_path / "docs" / "generated" / "repository_knowledge_graph.md").write_text("stale\n")

    findings = governance.validate_generated_freshness(tmp_path)

    assert {finding.message for finding in findings} == {"generated artifact is stale"}


def test_baseline_static_authorities_are_ready() -> None:
    assert governance.validate_protected_hashes(REPO_ROOT) == []
    assert governance.validate_current_authority(REPO_ROOT) == []
    assert governance.validate_repository_state(REPO_ROOT) == []


def test_cli_executes_without_foxcommand_runtime_python_path() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.repo_governance",
            "--repo-root",
            str(REPO_ROOT),
            "validate-heartbeat",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "passed" in result.stdout
    assert "foxcommand-runtime" not in result.stdout
    assert "foxcommand-runtime" not in result.stderr


def test_heartbeat_validation_rejects_invalid_jsonl(tmp_path: Path) -> None:
    heartbeat = tmp_path / "executor_heartbeat.jsonl"
    heartbeat.write_text(
        json.dumps(
            {
                "timestamp": "2026-07-18T00:00:00Z",
                "event_type": "executor_ops",
                "actor": "codex",
                "payload": {"description": "test", "operations": []},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    findings = governance.validate_heartbeat_jsonl(heartbeat)

    assert findings
    assert "operations" in findings[0].message
