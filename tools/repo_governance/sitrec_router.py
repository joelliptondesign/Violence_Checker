"""Deterministic, non-mutating router for lifecycle-managed SITRECs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PACIFIC_TIMEZONE = ZoneInfo("America/Los_Angeles")
ARCHIVE_PATH = Path("docs/archive/sitrecs")

DECISION_UPDATE_CURRENT = "UPDATE_CURRENT"
DECISION_CREATE_TODAY = "CREATE_TODAY"
DECISION_ARCHIVE_AND_CREATE_TODAY = "ARCHIVE_AND_CREATE_TODAY"
DECISION_NORMALIZE_ACTIVE_SET = "NORMALIZE_ACTIVE_SET"

DATE_PATTERNS = (
    re.compile(r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)"),
    re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)"),
)
DOCUMENT_DATE_PATTERN = re.compile(
    r"^Operational Date:\s*`?(20\d{2}-\d{2}-\d{2})`?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
HEADING_DATE_PATTERN = re.compile(
    r"^#\s+SITREC\s*-\s*(20\d{2}-\d{2}-\d{2})(?:\s|$)",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class SitrecCandidate:
    path: Path
    operational_date: str | None


@dataclass(frozen=True)
class SitrecRoute:
    pacific_operational_date: str
    active_sitrecs: tuple[SitrecCandidate, ...]
    decision: str

    def to_dict(self, root: Path) -> dict[str, object]:
        return {
            "pacific_operational_date": self.pacific_operational_date,
            "active_sitrecs": [
                {
                    "path": candidate.path.relative_to(root).as_posix(),
                    "operational_date": candidate.operational_date,
                }
                for candidate in self.active_sitrecs
            ],
            "decision": self.decision,
            "router_mutated_filesystem": False,
        }


def repo_root() -> Path:
    """Resolve this package's repository root."""
    return Path(__file__).resolve().parents[2]


def pacific_today(now: datetime | None = None) -> str:
    """Return the operational date under the Pacific IANA timezone authority."""
    if now is not None and now.tzinfo is None:
        raise ValueError("injected time must be timezone-aware")
    pacific_now = datetime.now(PACIFIC_TIMEZONE) if now is None else now.astimezone(PACIFIC_TIMEZONE)
    return pacific_now.date().isoformat()


def extract_date(path: Path) -> str | None:
    """Extract a valid dashed or compact operational date from a filename."""
    for pattern in DATE_PATTERNS:
        match = pattern.search(path.name)
        if not match:
            continue
        value = match.group(1) if len(match.groups()) == 1 else "-".join(match.groups())
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return None
    return None


def extract_document_date(text: str) -> str | None:
    """Extract a valid operational date from metadata or a historical title."""
    for pattern in (DOCUMENT_DATE_PATTERN, HEADING_DATE_PATTERN):
        match = pattern.search(text)
        if match:
            try:
                return date.fromisoformat(match.group(1)).isoformat()
            except ValueError:
                return None
    return None


def is_active_sitrec(path: Path, root: Path) -> bool:
    """Return whether path is a top-level Markdown SITREC directly under docs/."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    return (
        len(relative.parts) == 2
        and relative.parts[0].lower() == "docs"
        and path.suffix.lower() == ".md"
        and "sitrec" in path.name.lower()
        and path.is_file()
    )


def active_sitrecs(root: Path) -> tuple[SitrecCandidate, ...]:
    docs = root / "docs"
    if not docs.is_dir():
        return ()
    return tuple(
        SitrecCandidate(path=path, operational_date=extract_date(path))
        for path in sorted(docs.glob("*.md"), key=lambda item: item.name)
        if is_active_sitrec(path, root)
    )


def determine_decision(active: tuple[SitrecCandidate, ...], today: str) -> str:
    if len(active) > 1:
        return DECISION_NORMALIZE_ACTIVE_SET
    if not active:
        return DECISION_CREATE_TODAY
    if active[0].operational_date == today:
        return DECISION_UPDATE_CURRENT
    return DECISION_ARCHIVE_AND_CREATE_TODAY


def route_sitrec(root: Path | None = None, operational_date: str | None = None) -> SitrecRoute:
    """Report the required lifecycle action without mutating the filesystem."""
    resolved_root = (root or repo_root()).resolve()
    today = operational_date or pacific_today()
    today = date.fromisoformat(today).isoformat()
    active = active_sitrecs(resolved_root)
    return SitrecRoute(
        pacific_operational_date=today,
        active_sitrecs=active,
        decision=determine_decision(active, today),
    )
