# Evaluation Artifacts

This directory is the canonical artifact boundary for the independent Violence Checker evaluation capability. Evaluation contracts live in `src/evaluation/`; automated contract tests live in `tests/evaluation/`.

Artifact authority is separated by directory:

- `corpus/` contains the repository-authored synthetic corpus and authoritative ground truth.
- `runs/` is reserved for generated observed-output artifacts. Observations are evidence and never ground truth.
- `baselines/` is reserved for explicitly accepted baseline artifacts.
- `reports/` is reserved for generated engineering reports.

The authoritative corpus, deterministic loader, integrity validation, and coverage summary exist today. No live run, accepted baseline, regression executor, or engineering report is implemented.
