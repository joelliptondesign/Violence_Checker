"""Immutable contracts for True North baselines and operational regression evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Tuple

from pydantic import StrictInt, StrictStr, field_validator, model_validator

from src.evaluation.contracts import (
    BaselineClassification,
    CaseEvaluationResult,
    CaseEvaluationStatus,
    FailurePattern,
    FieldDifference,
)
from src.evaluation.run_contracts import (
    EvaluationExecutionSummary,
    EvaluationRunnerMode,
    ImmutableEvaluationContract,
    ObservedCaseResult,
)
from src.contracts import SEMANTIC_SCHEMA_IDENTITY, SEMANTIC_SCHEMA_VERSION
from src.evaluation.corpus import EVALUATION_SCHEMA_VERSION


class BaselineAcceptanceProvenance(ImmutableEvaluationContract):
    source_run_path: StrictStr
    acceptance_repository_commit: StrictStr
    accepted_at: datetime
    accepted_by: StrictStr = "explicit_command"
    replaces_baseline_id: Optional[StrictStr] = None

    @field_validator(
        "source_run_path",
        "acceptance_repository_commit",
        "accepted_by",
        "replaces_baseline_id",
    )
    @classmethod
    def require_non_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("baseline provenance identifiers must not be empty")
        return value

    @model_validator(mode="after")
    def require_aware_timestamp(self) -> "BaselineAcceptanceProvenance":
        if self.accepted_at.tzinfo is None or self.accepted_at.utcoffset() is None:
            raise ValueError("accepted_at must be timezone-aware")
        return self


class AcceptedBaselineArtifact(ImmutableEvaluationContract):
    artifact_type: StrictStr = "accepted_evaluation_baseline"
    baseline_id: StrictStr
    accepted_run_id: StrictStr
    repository_commit: StrictStr
    corpus_identity: StrictStr
    corpus_version: StrictStr
    evaluation_schema_version: StrictStr
    semantic_schema_identity: StrictStr
    semantic_schema_version: StrictStr
    execution_mode: EvaluationRunnerMode
    model_identifier: Optional[StrictStr] = None
    extraction_configuration_identity: Optional[StrictStr] = None
    run_timestamp: datetime
    requested_case_ids: Tuple[StrictStr, ...]
    observed_cases: Tuple[ObservedCaseResult, ...]
    case_evaluations: Tuple[CaseEvaluationResult, ...]
    summary: EvaluationExecutionSummary
    provenance: BaselineAcceptanceProvenance

    @field_validator(
        "artifact_type",
        "baseline_id",
        "accepted_run_id",
        "repository_commit",
        "corpus_identity",
        "corpus_version",
        "evaluation_schema_version",
        "semantic_schema_identity",
        "semantic_schema_version",
        "model_identifier",
        "extraction_configuration_identity",
    )
    @classmethod
    def require_identifiers(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("baseline identifiers must not be empty")
        return value

    @model_validator(mode="after")
    def require_snapshot_consistency(self) -> "AcceptedBaselineArtifact":
        if self.artifact_type != "accepted_evaluation_baseline":
            raise ValueError("unsupported baseline artifact type")
        if self.evaluation_schema_version != EVALUATION_SCHEMA_VERSION:
            raise ValueError("unsupported evaluation schema version")
        if (self.semantic_schema_identity, self.semantic_schema_version) != (
            SEMANTIC_SCHEMA_IDENTITY,
            SEMANTIC_SCHEMA_VERSION,
        ):
            raise ValueError("unsupported semantic schema identity or version")
        observed_ids = tuple(item.case_id for item in self.observed_cases)
        evaluation_ids = tuple(item.case_id for item in self.case_evaluations)
        if observed_ids != self.requested_case_ids or evaluation_ids != self.requested_case_ids:
            raise ValueError("baseline case ordering must match requested case ordering")
        if any(item.run_id != self.accepted_run_id for item in self.observed_cases):
            raise ValueError("observed baseline cases must reference the accepted run")
        if any(item.observed_run_id != self.accepted_run_id for item in self.case_evaluations):
            raise ValueError("baseline evaluations must reference the accepted run")
        if self.summary.requested_cases != len(self.requested_case_ids):
            raise ValueError("baseline summary must match requested cases")
        return self


class RegressionValueChange(ImmutableEvaluationContract):
    baseline_value: Optional[StrictStr] = None
    current_value: Optional[StrictStr] = None

    @model_validator(mode="after")
    def require_change(self) -> "RegressionValueChange":
        if self.baseline_value == self.current_value:
            raise ValueError("regression value change requires different values")
        return self


class CaseRegressionResult(ImmutableEvaluationContract):
    case_id: StrictStr
    primary_category: StrictStr
    baseline_outcome: CaseEvaluationStatus
    current_outcome: CaseEvaluationStatus
    classification: BaselineClassification
    field_differences_introduced: Tuple[FieldDifference, ...]
    field_differences_resolved: Tuple[FieldDifference, ...]
    baseline_failure_patterns: Tuple[FailurePattern, ...]
    current_failure_patterns: Tuple[FailurePattern, ...]
    failure_patterns_introduced: Tuple[FailurePattern, ...]
    failure_patterns_resolved: Tuple[FailurePattern, ...]
    baseline_policy_outcome: StrictStr
    current_policy_outcome: StrictStr
    baseline_validation_stage: StrictStr
    current_validation_stage: StrictStr
    policy_outcome_change: Optional[RegressionValueChange] = None
    validation_stage_change: Optional[RegressionValueChange] = None
    explanation: StrictStr

    @field_validator(
        "case_id",
        "primary_category",
        "baseline_policy_outcome",
        "current_policy_outcome",
        "baseline_validation_stage",
        "current_validation_stage",
        "explanation",
    )
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("case regression text must not be empty")
        return value


class RegressionExecutionSummary(ImmutableEvaluationContract):
    total_cases: StrictInt
    improved: StrictInt
    degraded: StrictInt
    unchanged: StrictInt
    incomparable: StrictInt
    regression_counts_by_category: Dict[StrictStr, Dict[StrictStr, StrictInt]]
    regression_counts_by_failure_pattern: Dict[StrictStr, Dict[StrictStr, StrictInt]]
    policy_outcome_changes: Dict[StrictStr, StrictInt]
    validation_stage_changes: Dict[StrictStr, StrictInt]
    provider_failures: StrictInt


class RegressionArtifact(ImmutableEvaluationContract):
    artifact_type: StrictStr = "evaluation_regression_comparison"
    comparison_id: StrictStr
    baseline_id: StrictStr
    baseline_run_id: StrictStr
    current_run_id: StrictStr
    baseline_repository_commit: StrictStr
    current_repository_commit: StrictStr
    corpus_identity: StrictStr
    corpus_version: StrictStr
    evaluation_schema_version: StrictStr
    semantic_schema_identity: StrictStr
    semantic_schema_version: StrictStr
    comparison_timestamp: datetime
    requested_case_ids: Tuple[StrictStr, ...]
    case_regressions: Tuple[CaseRegressionResult, ...]
    summary: RegressionExecutionSummary

    @field_validator(
        "artifact_type",
        "comparison_id",
        "baseline_id",
        "baseline_run_id",
        "current_run_id",
        "baseline_repository_commit",
        "current_repository_commit",
        "corpus_identity",
        "corpus_version",
        "evaluation_schema_version",
        "semantic_schema_identity",
        "semantic_schema_version",
    )
    @classmethod
    def require_identifiers(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("regression identifiers must not be empty")
        return value

    @model_validator(mode="after")
    def require_comparison_consistency(self) -> "RegressionArtifact":
        if self.artifact_type != "evaluation_regression_comparison":
            raise ValueError("unsupported regression artifact type")
        if self.evaluation_schema_version != EVALUATION_SCHEMA_VERSION:
            raise ValueError("unsupported evaluation schema version")
        if (self.semantic_schema_identity, self.semantic_schema_version) != (
            SEMANTIC_SCHEMA_IDENTITY,
            SEMANTIC_SCHEMA_VERSION,
        ):
            raise ValueError("unsupported semantic schema identity or version")
        if self.comparison_timestamp.tzinfo is None or self.comparison_timestamp.utcoffset() is None:
            raise ValueError("comparison_timestamp must be timezone-aware")
        if tuple(item.case_id for item in self.case_regressions) != self.requested_case_ids:
            raise ValueError("regression case ordering must match requested cases")
        counts = {
            BaselineClassification.IMPROVED: self.summary.improved,
            BaselineClassification.DEGRADED: self.summary.degraded,
            BaselineClassification.UNCHANGED: self.summary.unchanged,
            BaselineClassification.INCOMPARABLE: self.summary.incomparable,
        }
        if self.summary.total_cases != len(self.case_regressions):
            raise ValueError("regression total must match case count")
        if sum(counts.values()) != self.summary.total_cases:
            raise ValueError("regression classification counts must match total")
        return self
