from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

from tools.repo_governance import governance


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_SITREC = REPO_ROOT / "docs" / "SITREC - 2026-07-18 Violence Checker Narrative Source Control Baseline.md"


def test_governance_tooling_imports_without_foxcommand_runtime_path() -> None:
    module = importlib.import_module("tools.repo_governance.governance")

    assert module.DEFAULT_REPOSITORY_TREE_PATH.as_posix() == "docs/generated/repository_tree.txt"
    assert all("foxcommand-runtime" not in value for value in sys.path)


def test_repository_tree_generation_is_stable_and_excludes_secrets() -> None:
    output = REPO_ROOT / governance.DEFAULT_REPOSITORY_TREE_PATH

    first = governance.write_repository_tree(REPO_ROOT, output)
    first_text = output.read_text(encoding="utf-8")
    second = governance.write_repository_tree(REPO_ROOT, output)
    second_text = output.read_text(encoding="utf-8")

    assert first["entries"] == second["entries"]
    assert first_text == second_text
    assert ".git/" not in first_text
    assert ".env\n" not in first_text
    assert ".streamlit/secrets.toml" not in first_text


def test_knowledge_graph_generation_is_stable_and_marks_boundaries() -> None:
    output = REPO_ROOT / governance.DEFAULT_KNOWLEDGE_GRAPH_PATH

    governance.write_knowledge_graph(REPO_ROOT, output)
    first_text = output.read_text(encoding="utf-8")
    governance.write_knowledge_graph(REPO_ROOT, output)
    second_text = output.read_text(encoding="utf-8")

    assert first_text == second_text
    assert "`src/app_logic.py`" in first_text
    assert "`src/semantic_extractor.py`" in first_text
    assert "Provider-facing components" in first_text
    assert "Unresolved Relationships" in first_text


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

    assert findings == []


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
