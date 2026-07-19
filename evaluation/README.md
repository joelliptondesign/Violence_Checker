# Evaluation Artifacts

This directory separates evaluation authority from observed evidence.

- `corpus/` contains repository-authored synthetic ground truth.
- `runs/` contains generated ordered observations.
- `baselines/` contains explicitly accepted immutable snapshots.
- `reports/` contains deterministic regression comparisons and engineering reports.

Current evaluation schema `2.0.0` is proposition-oriented and records semantic schema identity/version on every run, baseline, and comparison. Expected envelopes, deterministic derived views, validation outcomes, and policy decisions are independent authorities; observed provider and pipeline output cannot author or repair them. Difference paths address stable entity, proposition, relationship, uncertainty, evidence, and support identifiers.

Creation-time schema `1.0.0` artifacts are loaded by strict immutable legacy readers. They remain readable under their creation-time vocabulary but cannot be translated, promoted into current baselines, or compared with current artifacts.

```sh
.venv/bin/python -m src.evaluation.corpus validate
.venv/bin/python -m src.evaluation.corpus coverage
.venv/bin/python -m pytest tests/evaluation
```

These checks are offline. Live-provider execution is explicit and performs one governed provider request per valid selected case.
