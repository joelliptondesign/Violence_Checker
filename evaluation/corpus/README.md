# Synthetic Corpus And Ground Truth

`corpus.json` is the authoritative repository-authored OPORD 003 synthetic corpus and deterministic ground-truth dataset. It contains no real hospital data or identifying information.

## Authority Rules

- Ground truth is authored directly from the repository semantic, validation, compatibility, and policy contracts.
- Provider output, regex output, interactive app results, and external classification systems cannot author, repair, or approve ground truth.
- Narrative input is isolated from metadata and expected outcomes. Only `case_id` and `narrative` constitute the future semantic input envelope.
- Observed results belong under `evaluation/runs/` and remain evidence, never authority.
- Cases use stable identifiers `EVAL_001` through `EVAL_048`. Identifiers do not depend on metadata or file position and must not be reused.
- Corpus, corpus-schema, and evaluation-schema versions are `1.0.0`. A version change requires deliberate repository review.
- Cases remain lexicographically ordered by identifier. Primary category appears first in the ordered category list; categories and documentation tags use bounded vocabularies from `src/evaluation/contracts.py`.
- Every expected success includes manually authored admissible `SemanticFacts`, the exact compatibility `ViolenceFinding`, and the current deterministic `PolicyDecision`.

The corpus covers all twelve required primary semantic categories and all required documentation-quality conditions, including compound interactions. It does not establish measured model performance.

Validate and inspect coverage from the repository root:

```sh
.venv/bin/python -m src.evaluation.corpus validate
.venv/bin/python -m src.evaluation.corpus coverage
.venv/bin/python -m pytest tests/evaluation
```

These commands make no provider request. No live runner, baseline, regression executor, or engineering report generator is implemented.
