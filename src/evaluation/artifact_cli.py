"""Repository-native CLI for baselines, regression comparison, and reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import List, Optional

from src.evaluation.baseline import BaselineError, accept_baseline
from src.evaluation.regression import RegressionError, compare_run
from src.evaluation.reporting import generate_report


def _timestamp(value: Optional[str]) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage deterministic evaluation evidence artifacts.")
    commands = parser.add_subparsers(dest="command", required=True)

    accept = commands.add_parser("accept-baseline", help="explicitly accept one complete run")
    accept.add_argument("--baseline-id", required=True)
    accept.add_argument("--run", required=True)
    accept.add_argument("--output", required=True)
    accept.add_argument("--acceptance-repository-commit", required=True)
    accept.add_argument("--accepted-at")
    accept.add_argument("--replaces")

    compare = commands.add_parser("compare-run", help="compare a current run to an accepted baseline")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--run", required=True)
    compare.add_argument("--comparison-id", required=True)
    compare.add_argument("--timestamp")
    compare.add_argument("--output", required=True)

    report = commands.add_parser("generate-report", help="render an engineering report from regression evidence")
    report.add_argument("--regression", required=True)
    report.add_argument("--output", required=True)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "accept-baseline":
            artifact = accept_baseline(
                baseline_id=args.baseline_id,
                run_path=args.run,
                output_path=args.output,
                acceptance_repository_commit=args.acceptance_repository_commit,
                accepted_at=_timestamp(args.accepted_at),
                replaces_baseline_path=args.replaces,
            )
            result = {
                "accepted_run_id": artifact.accepted_run_id,
                "baseline_id": artifact.baseline_id,
                "case_count": len(artifact.case_evaluations),
                "status": "accepted",
            }
        elif args.command == "compare-run":
            artifact = compare_run(
                baseline_path=args.baseline,
                current_run_path=args.run,
                comparison_id=args.comparison_id,
                comparison_timestamp=_timestamp(args.timestamp),
                output_path=args.output,
            )
            result = {
                "comparison_id": artifact.comparison_id,
                "degraded": artifact.summary.degraded,
                "improved": artifact.summary.improved,
                "incomparable": artifact.summary.incomparable,
                "status": "compared",
                "unchanged": artifact.summary.unchanged,
            }
        else:
            report = generate_report(regression_path=args.regression, output_path=args.output)
            result = {
                "line_count": len(report.splitlines()),
                "status": "generated",
            }
        print(json.dumps(result, sort_keys=True))
        return 0
    except (BaselineError, RegressionError, ValueError, OSError) as error:
        code = getattr(getattr(error, "code", None), "value", "invalid_artifact_operation")
        print(json.dumps({"code": code, "message": str(error), "status": "failed"}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
