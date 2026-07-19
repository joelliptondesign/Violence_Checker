# Evaluation Artifacts

This directory is the canonical artifact boundary for the independent Violence Checker evaluation capability. Evaluation contracts live in `src/evaluation/`; automated contract tests live in `tests/evaluation/`.

Artifact authority is separated by directory:

- `corpus/` contains the repository-authored synthetic corpus and authoritative ground truth.
- `runs/` is reserved for generated observed-output artifacts. Observations are evidence and never ground truth.
- `baselines/` is reserved for explicitly accepted baseline artifacts.
- `reports/` is reserved for generated engineering reports.

The authoritative corpus, deterministic loader, integrity validation, coverage summary, non-interactive runner, observed run artifacts, deterministic case comparison, and bounded failure-pattern classification exist today. The taxonomy covers `historical_current_confusion`, `correction_reversal_failure`, `conflict_resolution_failure`, `threat_classification_failure`, `accidental_intentional_confusion`, `negation_failure`, `object_directed_interpersonal_confusion`, `self_directed_interpersonal_confusion`, `unsupported_evidence`, `evidence_omission`, `excessive_uncertainty`, `insufficient_uncertainty`, `semantic_field_mismatch`, `validation_rejection`, `compatibility_failure`, `policy_mismatch`, `provider_failure`, and `pipeline_failure`. Live-provider mode is explicit and opt-in. No accepted baseline, baseline regression executor, or final engineering report is implemented.
