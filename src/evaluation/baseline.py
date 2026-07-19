"""Explicit acceptance and immutable storage of evaluation baselines."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from pydantic import ValidationError

from src.evaluation.corpus import REPOSITORY_ROOT
from src.evaluation.regression_contracts import (
    AcceptedBaselineArtifact,
    BaselineAcceptanceProvenance,
)
from src.evaluation.legacy_artifacts import LegacyArtifact, load_legacy_artifact
from src.evaluation.run_contracts import EvaluationRunArtifact, RunArtifactStatus
from src.evaluation.serialization import canonical_json


RUNS_ROOT = (REPOSITORY_ROOT / "evaluation" / "runs").resolve()
BASELINES_ROOT = (REPOSITORY_ROOT / "evaluation" / "baselines").resolve()


class BaselineIssueCode(str, Enum):
    SOURCE_OUTSIDE_RUNS = "source_outside_runs"
    OUTPUT_OUTSIDE_BASELINES = "output_outside_baselines"
    INVALID_ARTIFACT_EXTENSION = "invalid_artifact_extension"
    SOURCE_RUN_MISSING = "source_run_missing"
    SOURCE_RUN_INCOMPLETE = "source_run_incomplete"
    BASELINE_MISSING = "baseline_missing"
    BASELINE_EXISTS = "baseline_exists"
    REPLACEMENT_ID_REUSED = "replacement_id_reused"
    INVALID_ARTIFACT = "invalid_artifact"


class BaselineError(ValueError):
    def __init__(self, code: BaselineIssueCode, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code.value}: {message}")


def _resolve(path: str, root: Path, outside_code: BaselineIssueCode) -> Path:
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else REPOSITORY_ROOT / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise BaselineError(outside_code, f"artifact must be under {root.relative_to(REPOSITORY_ROOT)}") from error
    if resolved.suffix != ".json":
        raise BaselineError(
            BaselineIssueCode.INVALID_ARTIFACT_EXTENSION,
            "baseline and run artifacts must use .json extension",
        )
    return resolved


def resolve_run_path(path: str) -> Path:
    return _resolve(path, RUNS_ROOT, BaselineIssueCode.SOURCE_OUTSIDE_RUNS)


def resolve_baseline_path(path: str) -> Path:
    return _resolve(path, BASELINES_ROOT, BaselineIssueCode.OUTPUT_OUTSIDE_BASELINES)


def load_run_artifact(path: str) -> Union[EvaluationRunArtifact, LegacyArtifact]:
    source = resolve_run_path(path)
    if not source.is_file():
        raise BaselineError(BaselineIssueCode.SOURCE_RUN_MISSING, f"run artifact not found: {source.name}")
    try:
        raw = source.read_text(encoding="utf-8")
        header = json.loads(raw)
        if header.get("evaluation_schema_version") == "1.0.0":
            return load_legacy_artifact(source, "run")
        return EvaluationRunArtifact.model_validate_json(raw)
    except (OSError, ValidationError, ValueError) as error:
        raise BaselineError(BaselineIssueCode.INVALID_ARTIFACT, "run artifact is invalid") from error


def load_baseline_artifact(path: str) -> Union[AcceptedBaselineArtifact, LegacyArtifact]:
    source = resolve_baseline_path(path)
    if not source.is_file():
        raise BaselineError(BaselineIssueCode.BASELINE_MISSING, f"baseline not found: {source.name}")
    try:
        raw = source.read_text(encoding="utf-8")
        header = json.loads(raw)
        if header.get("evaluation_schema_version") == "1.0.0":
            return load_legacy_artifact(source, "baseline")
        return AcceptedBaselineArtifact.model_validate_json(raw)
    except (OSError, ValidationError, ValueError) as error:
        raise BaselineError(BaselineIssueCode.INVALID_ARTIFACT, "baseline artifact is invalid") from error


def accept_baseline(
    *,
    baseline_id: str,
    run_path: str,
    output_path: str,
    acceptance_repository_commit: str,
    accepted_at: datetime,
    replaces_baseline_path: Optional[str] = None,
) -> AcceptedBaselineArtifact:
    """Accept one complete run explicitly without modifying an existing baseline."""

    source_path = resolve_run_path(run_path)
    output = resolve_baseline_path(output_path)
    run = load_run_artifact(run_path)
    if isinstance(run, LegacyArtifact):
        raise BaselineError(BaselineIssueCode.INVALID_ARTIFACT, "legacy runs cannot become successor baselines")
    if run.status != RunArtifactStatus.COMPLETE:
        raise BaselineError(BaselineIssueCode.SOURCE_RUN_INCOMPLETE, "only complete runs can be accepted")
    if output.exists():
        raise BaselineError(BaselineIssueCode.BASELINE_EXISTS, f"baseline already exists: {output.name}")

    replaces_id = None
    if replaces_baseline_path is not None:
        replaced = load_baseline_artifact(replaces_baseline_path)
        if isinstance(replaced, LegacyArtifact):
            raise BaselineError(BaselineIssueCode.INVALID_ARTIFACT, "legacy baselines cannot be replaced by successor acceptance")
        if replaced.baseline_id == baseline_id:
            raise BaselineError(
                BaselineIssueCode.REPLACEMENT_ID_REUSED,
                "replacement requires a new baseline identifier",
            )
        replaces_id = replaced.baseline_id

    artifact = AcceptedBaselineArtifact(
        baseline_id=baseline_id,
        accepted_run_id=run.run_id,
        repository_commit=run.repository_commit,
        corpus_identity=run.corpus_identity,
        corpus_version=run.corpus_version,
        evaluation_schema_version=run.evaluation_schema_version,
        semantic_schema_identity=run.semantic_schema_identity,
        semantic_schema_version=run.semantic_schema_version,
        execution_mode=run.execution_mode,
        model_identifier=run.model_identifier,
        extraction_configuration_identity=run.extraction_configuration_identity,
        run_timestamp=run.run_timestamp,
        requested_case_ids=run.requested_case_ids,
        observed_cases=run.observed_cases,
        case_evaluations=run.case_evaluations,
        summary=run.summary,
        provenance=BaselineAcceptanceProvenance(
            source_run_path=str(source_path.relative_to(REPOSITORY_ROOT)),
            acceptance_repository_commit=acceptance_repository_commit,
            accepted_at=accepted_at,
            replaces_baseline_id=replaces_id,
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8") as handle:
            handle.write(canonical_json(artifact) + "\n")
    except FileExistsError as error:
        raise BaselineError(BaselineIssueCode.BASELINE_EXISTS, f"baseline already exists: {output.name}") from error
    return artifact
