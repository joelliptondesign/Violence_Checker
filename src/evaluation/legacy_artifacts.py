"""Read-only creation-time routing for immutable evaluation artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional


LEGACY_EVALUATION_SCHEMA_VERSION = "1.0.0"
SUCCESSOR_EVALUATION_SCHEMA_VERSION = "2.0.0"
LEGACY_CORPUS_IDENTITY = "violence-checker-synthetic-evaluation-corpus"

_TOP_LEVEL_KEYS = {
    "run": {
        "case_evaluations", "corpus_identity", "corpus_version", "evaluation_schema_version",
        "execution_mode", "extraction_configuration_identity", "model_identifier", "observed_cases",
        "repository_commit", "requested_case_ids", "run_id", "run_timestamp", "status", "summary",
    },
    "baseline": {
        "accepted_run_id", "artifact_type", "baseline_id", "case_evaluations", "corpus_identity",
        "corpus_version", "evaluation_schema_version", "execution_mode", "extraction_configuration_identity",
        "model_identifier", "observed_cases", "provenance", "repository_commit", "requested_case_ids",
        "run_timestamp", "summary",
    },
    "comparison": {
        "artifact_type", "baseline_id", "baseline_repository_commit", "baseline_run_id", "case_regressions",
        "comparison_id", "comparison_timestamp", "corpus_identity", "corpus_version",
        "current_repository_commit", "current_run_id", "evaluation_schema_version", "requested_case_ids", "summary",
    },
}


@dataclass(frozen=True)
class LegacyArtifact:
    artifact_kind: str
    evaluation_schema_version: str
    corpus_identity: str
    data: Mapping[str, object]


@dataclass(frozen=True)
class ArtifactFamilyComparison:
    comparable: bool
    left_schema: str
    right_schema: str
    reason: Optional[str] = None


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_legacy_artifact(path: Path, artifact_kind: str) -> LegacyArtifact:
    if artifact_kind not in _TOP_LEVEL_KEYS:
        raise ValueError("unsupported legacy artifact kind")
    raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    if not isinstance(raw, dict) or set(raw) != _TOP_LEVEL_KEYS[artifact_kind]:
        raise ValueError("malformed creation-time artifact shape")
    if raw.get("evaluation_schema_version") != LEGACY_EVALUATION_SCHEMA_VERSION:
        raise ValueError("unsupported legacy evaluation schema version")
    if raw.get("corpus_identity") != LEGACY_CORPUS_IDENTITY:
        raise ValueError("unsupported legacy corpus identity")
    requested = raw.get("requested_case_ids")
    if not isinstance(requested, list) or requested != [f"EVAL_{index:03d}" for index in range(1, 49)]:
        raise ValueError("legacy artifact case identity/order is malformed")
    observed_key = "case_regressions" if artifact_kind == "comparison" else "observed_cases"
    observed = raw.get(observed_key)
    if not isinstance(observed, list) or len(observed) != 48:
        raise ValueError("legacy artifact requires 48 ordered case records")
    return LegacyArtifact(
        artifact_kind=artifact_kind,
        evaluation_schema_version=LEGACY_EVALUATION_SCHEMA_VERSION,
        corpus_identity=LEGACY_CORPUS_IDENTITY,
        data=MappingProxyType(raw),
    )


def compare_artifact_families(left_schema: str, right_schema: str) -> ArtifactFamilyComparison:
    if left_schema == right_schema == SUCCESSOR_EVALUATION_SCHEMA_VERSION:
        return ArtifactFamilyComparison(True, left_schema, right_schema)
    return ArtifactFamilyComparison(
        False,
        left_schema,
        right_schema,
        "schema_families_are_incomparable",
    )
