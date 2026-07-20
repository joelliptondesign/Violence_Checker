from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tools.repo_governance import governance, sitrec
from tools.repo_governance.sitrec_router import (
    DECISION_ARCHIVE_AND_CREATE_TODAY,
    DECISION_CREATE_TODAY,
    DECISION_NORMALIZE_ACTIVE_SET,
    DECISION_UPDATE_CURRENT,
    active_sitrecs,
    extract_date,
    pacific_today,
    route_sitrec,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-07-20"


def write_record(root: Path, name: str, operational_date: str, body: str = "historical body") -> Path:
    path = root / "docs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# SITREC - {operational_date} Test\n\nOperational Date: `{operational_date}`\n\n"
        "## A. SYSTEM IDENTITY\n\nViolence_Checker is a non-production repository.\n\n"
        "## B. CURRENT STATE\n\nThe current semantic authority is repository-governed.\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return path


def fake_render(_root: Path, operational_date: str, title: str = sitrec.DEFAULT_TITLE) -> str:
    return (
        f"# SITREC - {operational_date} {title}\n\n"
        f"Operational Date: `{operational_date}`\n\ncurrent generated body\n"
    )


@pytest.fixture
def isolated_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sitrec, "collect_sitrec_facts", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(sitrec, "render_sitrec", fake_render)


def test_no_active_sitrec_routes_create_today(tmp_path: Path) -> None:
    assert route_sitrec(tmp_path, TODAY).decision == DECISION_CREATE_TODAY


def test_one_current_sitrec_routes_update_current(tmp_path: Path) -> None:
    write_record(tmp_path, "SITREC - 2026-07-20 Current.md", TODAY)
    assert route_sitrec(tmp_path, TODAY).decision == DECISION_UPDATE_CURRENT


def test_one_stale_sitrec_routes_archive_and_create(tmp_path: Path) -> None:
    write_record(tmp_path, "SITREC - 2026-07-19 Stale.md", "2026-07-19")
    assert route_sitrec(tmp_path, TODAY).decision == DECISION_ARCHIVE_AND_CREATE_TODAY


def test_multiple_active_sitrecs_route_normalization(tmp_path: Path) -> None:
    write_record(tmp_path, "SITREC - 2026-07-18 Older.md", "2026-07-18")
    write_record(tmp_path, "SITREC - 2026-07-19 Stale.md", "2026-07-19")
    assert route_sitrec(tmp_path, TODAY).decision == DECISION_NORMALIZE_ACTIVE_SET


def test_archive_files_are_excluded_from_active_detection(tmp_path: Path) -> None:
    archived = tmp_path / "docs/archive/sitrecs/SITREC - 2026-07-19 Archived.md"
    archived.parent.mkdir(parents=True)
    archived.write_text("archive\n", encoding="utf-8")
    assert active_sitrecs(tmp_path) == ()


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("SITREC - 2026-07-20 Dashed.md", TODAY),
        ("SITREC_20260720_Compact.md", TODAY),
    ],
)
def test_supported_filename_date_extraction(filename: str, expected: str) -> None:
    assert extract_date(Path(filename)) == expected


def test_undated_active_candidate_is_reported_and_mutation_fails(tmp_path: Path, isolated_generator: None) -> None:
    write_record(tmp_path, "SITREC Current.md", TODAY)
    route = route_sitrec(tmp_path, TODAY)
    assert route.active_sitrecs[0].operational_date is None
    with pytest.raises(ValueError, match="filename has no valid operational date"):
        sitrec.write_sitrec(tmp_path, TODAY)


def test_pacific_date_resolution_uses_injected_instant() -> None:
    instant = datetime(2026, 7, 20, 6, 30, tzinfo=timezone.utc)
    assert pacific_today(instant) == "2026-07-19"


def test_router_is_deterministic_and_non_mutating(tmp_path: Path) -> None:
    write_record(tmp_path, "SITREC - 2026-07-19 Stale.md", "2026-07-19")
    before = sorted(
        (path.relative_to(tmp_path).as_posix(), path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    first = route_sitrec(tmp_path, TODAY).to_dict(tmp_path)
    second = route_sitrec(tmp_path, TODAY).to_dict(tmp_path)
    after = sorted(
        (path.relative_to(tmp_path).as_posix(), path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    assert first == second
    assert first["router_mutated_filesystem"] is False
    assert before == after


def test_stale_records_are_archived_and_current_record_created_once(
    tmp_path: Path, isolated_generator: None
) -> None:
    stale = write_record(tmp_path, "SITREC - 2026-07-19 Stale.md", "2026-07-19")
    historical = stale.read_bytes()
    first = sitrec.write_sitrec(tmp_path, TODAY)
    second = sitrec.write_sitrec(tmp_path, TODAY)
    archived = tmp_path / "docs/archive/sitrecs" / stale.name
    active = list((tmp_path / "docs").glob("*SITREC*.md"))
    assert first["router_decision"] == DECISION_ARCHIVE_AND_CREATE_TODAY
    assert first["archived"] == [f"docs/archive/sitrecs/{stale.name}"]
    assert second["router_decision"] == DECISION_UPDATE_CURRENT
    assert archived.read_bytes() == historical
    assert len(active) == 1
    assert TODAY in active[0].name


def test_multiple_stale_records_are_normalized_deterministically(
    tmp_path: Path, isolated_generator: None
) -> None:
    older = write_record(tmp_path, "SITREC - 2026-07-18 Older.md", "2026-07-18")
    stale = write_record(tmp_path, "SITREC - 2026-07-19 Stale.md", "2026-07-19")
    result = sitrec.write_sitrec(tmp_path, TODAY)
    assert result["router_decision"] == DECISION_NORMALIZE_ACTIVE_SET
    assert result["archived"] == [
        f"docs/archive/sitrecs/{older.name}",
        f"docs/archive/sitrecs/{stale.name}",
    ]


def test_duplicate_same_date_records_fail_without_mutation(tmp_path: Path, isolated_generator: None) -> None:
    first = write_record(tmp_path, "SITREC - 2026-07-19 One.md", "2026-07-19")
    second = write_record(tmp_path, "SITREC_20260719_Two.md", "2026-07-19")
    before = {first: first.read_bytes(), second: second.read_bytes()}
    with pytest.raises(ValueError, match="duplicate SITREC operational date 2026-07-19"):
        sitrec.write_sitrec(tmp_path, TODAY)
    assert {path: path.read_bytes() for path in before} == before


def test_filename_and_document_date_mismatch_fails(tmp_path: Path, isolated_generator: None) -> None:
    write_record(tmp_path, "SITREC - 2026-07-19 Mismatch.md", "2026-07-18")
    with pytest.raises(ValueError, match="disagrees with document Operational Date"):
        sitrec.write_sitrec(tmp_path, TODAY)


def test_lifecycle_validation_rejects_stale_active_and_accepts_corrected_set(tmp_path: Path) -> None:
    stale = write_record(tmp_path, "SITREC - 2026-07-19 Stale.md", "2026-07-19")
    findings = governance.validate_sitrec_lifecycle(tmp_path, TODAY)
    assert any("does not equal Pacific operational date" in finding.message for finding in findings)
    archive = tmp_path / "docs/archive/sitrecs"
    archive.mkdir(parents=True)
    stale.replace(archive / stale.name)
    write_record(
        tmp_path,
        "SITREC - 2026-07-20 Current.md",
        TODAY,
        "Archived historical SITREC records remain provenance.",
    )
    assert governance.validate_sitrec_lifecycle(tmp_path, TODAY) == []


def test_route_sitrec_cli_reports_non_mutating_decision() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tools.repo_governance", "route-sitrec"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["router_mutated_filesystem"] is False
    assert payload["decision"] in {
        DECISION_UPDATE_CURRENT,
        DECISION_CREATE_TODAY,
        DECISION_ARCHIVE_AND_CREATE_TODAY,
        DECISION_NORMALIZE_ACTIVE_SET,
    }
