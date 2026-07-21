"""Immutable run contracts for the True North evaluation family."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Tuple

from pydantic import ConfigDict, StrictBool, StrictInt, StrictStr, field_validator, model_validator

from src.contracts import PipelineResult, PolicyOutcome, SEMANTIC_SCHEMA_IDENTITY, SEMANTIC_SCHEMA_VERSION
from src.evaluation.contracts import CaseEvaluationResult, EvaluationContract
from src.evaluation.corpus import EVALUATION_SCHEMA_VERSION


class ImmutableEvaluationContract(EvaluationContract):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class EvaluationRunnerMode(str, Enum):
    DETERMINISTIC_TEST = "deterministic_test"
    LIVE_PROVIDER = "live_provider"


class RunArtifactStatus(str, Enum):
    COMPLETE = "complete"
    FAILED = "failed"


class ObservedPipelineComparison(ImmutableEvaluationContract):
    regex_detected: StrictBool
    true_north_outcome: PolicyOutcome
    classification_alignment: StrictStr


class ObservedCaseResult(ImmutableEvaluationContract):
    case_id: StrictStr
    run_id: StrictStr
    semantic_status: StrictStr
    semantic_failure_message: Optional[StrictStr] = None
    pipeline_result: PipelineResult
    pipeline_comparison: ObservedPipelineComparison

    @field_validator("case_id", "run_id", "semantic_status")
    @classmethod
    def non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("observed identifiers and status must not be empty")
        return value


class EvaluationRunConfiguration(ImmutableEvaluationContract):
    run_id: StrictStr
    execution_mode: EvaluationRunnerMode
    repository_commit: StrictStr
    model_identifier: Optional[StrictStr] = None
    extraction_configuration_identity: Optional[StrictStr] = None
    run_timestamp: datetime
    requested_case_ids: Tuple[StrictStr, ...] = ()
    output_path: StrictStr
    overwrite: StrictBool = False

    @field_validator("run_id", "repository_commit", "model_identifier", "extraction_configuration_identity", "output_path")
    @classmethod
    def identifiers(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("runner identifiers must not be empty")
        return value

    @model_validator(mode="after")
    def valid_selection(self) -> "EvaluationRunConfiguration":
        if self.run_timestamp.tzinfo is None or self.run_timestamp.utcoffset() is None:
            raise ValueError("run timestamp must be timezone-aware")
        if len(self.requested_case_ids) != len(set(self.requested_case_ids)):
            raise ValueError("requested case identifiers must be unique")
        return self


class EvaluationExecutionSummary(ImmutableEvaluationContract):
    requested_cases: StrictInt
    executed_cases: StrictInt
    match_count: StrictInt
    partial_mismatch_count: StrictInt
    failure_count: StrictInt
    non_comparable_count: StrictInt
    provider_failure_count: StrictInt
    validation_rejection_count: StrictInt
    policy_mismatch_count: StrictInt
    failure_pattern_counts: Dict[StrictStr, StrictInt]
    cases_by_primary_category: Dict[StrictStr, StrictInt]
    outcomes_by_primary_category: Dict[StrictStr, Dict[StrictStr, StrictInt]]


class EvaluationRunArtifact(ImmutableEvaluationContract):
    evaluation_schema_version: StrictStr
    semantic_schema_identity: StrictStr
    semantic_schema_version: StrictStr
    corpus_identity: StrictStr
    corpus_version: StrictStr
    run_id: StrictStr
    execution_mode: EvaluationRunnerMode
    repository_commit: StrictStr
    model_identifier: Optional[StrictStr] = None
    extraction_configuration_identity: Optional[StrictStr] = None
    run_timestamp: datetime
    requested_case_ids: Tuple[StrictStr, ...]
    observed_cases: Tuple[ObservedCaseResult, ...]
    case_evaluations: Tuple[CaseEvaluationResult, ...]
    summary: EvaluationExecutionSummary
    status: RunArtifactStatus

    @model_validator(mode="after")
    def consistent(self) -> "EvaluationRunArtifact":
        if self.evaluation_schema_version != EVALUATION_SCHEMA_VERSION:
            raise ValueError("unsupported evaluation schema version")
        if (self.semantic_schema_identity, self.semantic_schema_version) != (SEMANTIC_SCHEMA_IDENTITY, SEMANTIC_SCHEMA_VERSION):
            raise ValueError("unsupported semantic schema")
        ids = tuple(item.case_id for item in self.observed_cases)
        evaluated = tuple(item.case_id for item in self.case_evaluations)
        if ids != self.requested_case_ids or evaluated != self.requested_case_ids:
            raise ValueError("artifact case ordering is inconsistent")
        if self.summary.requested_cases != len(self.requested_case_ids) or self.summary.executed_cases != len(self.observed_cases):
            raise ValueError("artifact summary counts are inconsistent")
        return self
