# Evaluation Artifacts

This directory is the canonical artifact boundary for the independent Violence Checker evaluation capability. Evaluation contracts live in `src/evaluation/`; automated contract tests live in `tests/evaluation/`.

Artifact authority is separated by directory:

- `corpus/` is reserved for repository-authored synthetic cases and authoritative ground truth.
- `runs/` is reserved for generated observed-output artifacts. Observations are evidence and never ground truth.
- `baselines/` is reserved for explicitly accepted baseline artifacts.
- `reports/` is reserved for generated engineering reports.

Only this structure and its contracts exist today. No production corpus, live run, accepted baseline, regression executor, or engineering report is implemented by the evaluation foundation.
