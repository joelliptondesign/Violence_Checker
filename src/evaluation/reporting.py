"""Deterministic engineering report generation from regression artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable, List

from src.evaluation.contracts import BaselineClassification, CaseEvaluationStatus
from src.evaluation.regression import (
    RegressionError,
    RegressionIssueCode,
    load_regression_artifact,
    resolve_report_path,
)
from src.evaluation.regression_contracts import CaseRegressionResult, RegressionArtifact


def _lines_for_counts(counts: Counter[str]) -> List[str]:
    if not counts:
        return ["- None observed."]
    return [f"- `{key}`: {counts[key]}" for key in sorted(counts)]


def _current_pattern_counts(cases: Iterable[CaseRegressionResult]) -> Counter[str]:
    return Counter(pattern.value for case in cases for pattern in case.current_failure_patterns)


def _difficult_cases(artifact: RegressionArtifact) -> List[CaseRegressionResult]:
    priorities = (
        BaselineClassification.DEGRADED,
        BaselineClassification.INCOMPARABLE,
        BaselineClassification.UNCHANGED,
    )
    selected: List[CaseRegressionResult] = []
    for classification in priorities:
        for case in artifact.case_regressions:
            if case.classification != classification:
                continue
            if (
                case.current_outcome == CaseEvaluationStatus.MATCH
                and classification == BaselineClassification.UNCHANGED
            ):
                continue
            selected.append(case)
            if len(selected) == 5:
                return selected
    return selected


def _opportunities(artifact: RegressionArtifact) -> List[str]:
    pattern_counts = _current_pattern_counts(artifact.case_regressions)
    introduced_fields = Counter(
        difference.field
        for case in artifact.case_regressions
        for difference in case.field_differences_introduced
    )
    lines: List[str] = []
    for pattern, count in sorted(pattern_counts.items(), key=lambda item: (-item[1], item[0]))[:3]:
        case_ids = [
            case.case_id
            for case in artifact.case_regressions
            if any(item.value == pattern for item in case.current_failure_patterns)
        ]
        lines.append(
            f"- Review the observed `{pattern}` evidence recurring in {count} case(s): "
            f"{', '.join(case_ids)}."
        )
    for field, count in sorted(introduced_fields.items(), key=lambda item: (-item[1], item[0]))[:2]:
        case_ids = [
            case.case_id
            for case in artifact.case_regressions
            if any(item.field == field for item in case.field_differences_introduced)
        ]
        lines.append(
            f"- Investigate the introduced `{field}` difference observed in {count} case(s): "
            f"{', '.join(case_ids)}."
        )
    if not lines:
        return ["- No evidence-supported engineering opportunity was identified in this comparison."]
    return lines


def render_engineering_report(artifact: RegressionArtifact) -> str:
    """Render stable Markdown from machine-readable observed evidence only."""

    category_counts = Counter(case.primary_category for case in artifact.case_regressions)
    pattern_counts = _current_pattern_counts(artifact.case_regressions)
    validation_counts = Counter(case.current_validation_stage for case in artifact.case_regressions)
    policy_counts = Counter(case.current_policy_outcome for case in artifact.case_regressions)
    difficult = _difficult_cases(artifact)
    summary = artifact.summary

    lines = [
        "# Evaluation Engineering Report",
        "",
        "## 1. Run provenance",
        "",
        f"- Comparison: `{artifact.comparison_id}`",
        f"- Accepted baseline: `{artifact.baseline_id}` from run `{artifact.baseline_run_id}`",
        f"- Current run: `{artifact.current_run_id}`",
        f"- Baseline repository commit: `{artifact.baseline_repository_commit}`",
        f"- Current repository commit: `{artifact.current_repository_commit}`",
        f"- Comparison timestamp: `{artifact.comparison_timestamp.isoformat()}`",
        "",
        "## 2. Corpus identity",
        "",
        f"- Corpus: `{artifact.corpus_identity}` version `{artifact.corpus_version}`",
        f"- Evaluation schema: `{artifact.evaluation_schema_version}`",
        "",
        "## 3. Evaluation coverage",
        "",
        f"- Total compared cases: {summary.total_cases}",
        *_lines_for_counts(category_counts),
        "",
        "## 4. Overall summary",
        "",
        f"- Improved: {summary.improved}",
        f"- Degraded: {summary.degraded}",
        f"- Unchanged: {summary.unchanged}",
        f"- Incomparable: {summary.incomparable}",
        f"- Current provider failures: {summary.provider_failures}",
        "",
        "## 5. Regression summary",
        "",
    ]
    for category in sorted(summary.regression_counts_by_category):
        values = summary.regression_counts_by_category[category]
        detail = ", ".join(f"{key}={values[key]}" for key in sorted(values))
        lines.append(f"- `{category}`: {detail}")

    lines.extend(["", "## 6. Most frequent failure patterns", ""])
    if pattern_counts:
        for pattern, count in sorted(pattern_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{pattern}`: {count}")
    else:
        lines.append("- No current failure patterns were observed.")

    lines.extend(["", "## 7. Validation observations", ""])
    lines.extend(_lines_for_counts(validation_counts))
    if summary.validation_stage_changes:
        lines.append("- Stage changes:")
        lines.extend(
            f"  - `{key}`: {summary.validation_stage_changes[key]}"
            for key in sorted(summary.validation_stage_changes)
        )
    else:
        lines.append("- No validation-stage changes were observed.")

    lines.extend(["", "## 8. Policy observations", ""])
    lines.extend(_lines_for_counts(policy_counts))
    if summary.policy_outcome_changes:
        lines.append("- Outcome changes:")
        lines.extend(
            f"  - `{key}`: {summary.policy_outcome_changes[key]}"
            for key in sorted(summary.policy_outcome_changes)
        )
    else:
        lines.append("- No policy-outcome changes were observed.")

    lines.extend(["", "## 9. Representative difficult cases", ""])
    if difficult:
        for case in difficult:
            patterns = ", ".join(pattern.value for pattern in case.current_failure_patterns) or "none"
            fields = ", ".join(item.field for item in case.field_differences_introduced) or "none"
            lines.append(
                f"- `{case.case_id}` ({case.primary_category}): {case.classification.value}; "
                f"current outcome={case.current_outcome.value}; patterns={patterns}; "
                f"introduced fields={fields}."
            )
    else:
        lines.append("- No degraded, incomparable, or persistently mismatched case was observed.")

    lines.extend(["", "## 10. Engineering opportunities", ""])
    lines.extend(_opportunities(artifact))
    lines.append("")
    return "\n".join(lines)


def generate_report(*, regression_path: str, output_path: str) -> str:
    artifact = load_regression_artifact(regression_path)
    report = render_engineering_report(artifact)
    output = resolve_report_path(output_path, ".md")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8") as handle:
            handle.write(report)
    except FileExistsError as error:
        raise RegressionError(RegressionIssueCode.ARTIFACT_EXISTS, f"report already exists: {output.name}") from error
    return report
