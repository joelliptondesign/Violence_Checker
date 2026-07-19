# Local Governance Tooling

Violence_Checker contains repository-local deterministic governance tooling at `tools/repo_governance/`.

The tooling was adapted from read-only reference files in `/Users/joellipton/Desktop/foxcommand-runtime/tools/`, specifically the repository tree, knowledge graph, SITREC structural validation, and heartbeat JSONL validation concepts from `repo_governance.py`, `validate_knowledge_graph.py`, and `validate_sitrec.py`.

The local copy exists so routine Violence Checker governance operations do not require executing tooling from the foxcommand-runtime repository. foxcommand-runtime remains a provenance source only for this copied governance boundary.

Authorized local functions:

- Generate deterministic repository tree: `python3 -m tools.repo_governance repo-tree`
- Generate deterministic repository knowledge graph: `python3 -m tools.repo_governance knowledge-graph`
- Validate executor heartbeat JSONL: `python3 -m tools.repo_governance validate-heartbeat`
- Validate the active SITREC: `python3 -m tools.repo_governance validate-sitrec --path "docs/SITREC - 2026-07-18 Violence Checker Narrative Source Control Baseline.md"`
- Run local governance validation: `python3 -m tools.repo_governance validate-all`
- Validate the authoritative synthetic evaluation corpus: `.venv/bin/python -m src.evaluation.corpus validate`
- Inspect deterministic corpus coverage: `.venv/bin/python -m src.evaluation.corpus coverage`
- Validate evaluation runner configuration without provider execution: `.venv/bin/python -m src.evaluation.runner validate --mode live_provider --run-id VALIDATE_ONLY --repository-commit "$(git rev-parse HEAD)" --output evaluation/runs/validate-only.json --case EVAL_001`
- Explicitly accept a run as an immutable baseline: `.venv/bin/python -m src.evaluation.artifact_cli accept-baseline --baseline-id BASELINE_001 --run evaluation/runs/accepted-run.json --output evaluation/baselines/baseline-001.json --acceptance-repository-commit "$(git rev-parse HEAD)"`
- Compare a current run to an accepted baseline: `.venv/bin/python -m src.evaluation.artifact_cli compare-run --baseline evaluation/baselines/baseline-001.json --run evaluation/runs/current-run.json --comparison-id COMPARISON_001 --output evaluation/reports/comparison-001.json`
- Generate an evidence-only engineering report: `.venv/bin/python -m src.evaluation.artifact_cli generate-report --regression evaluation/reports/comparison-001.json --output evaluation/reports/comparison-001.md`

Evaluation classification is deterministic and repository-local. Compatibility construction failures require explicit compatibility failure provenance and remain distinct from compatibility differences. Evidence coverage uses exact substring containment and ordered exact-span segmentation without fuzzy or model-assisted matching. Reports separate runtime failures from comparison differences, semantic weakness indicators, and legacy classification artifacts.

Generated artifact locations:

- `docs/generated/repository_tree.txt`
- `docs/generated/repository_knowledge_graph.md`

The local tooling must operate on an explicitly supplied repository root or the current working repository, write generated artifacts only inside Violence_Checker, avoid network access, avoid importing application code for validation, and avoid importing FoxCommand runtime application modules.

Limitations:

- The knowledge graph is static and repository-derived; unresolved relationships remain marked unresolved.
- The SITREC validator checks required structure and repository primacy language; it does not determine application truth.
- The heartbeat validator checks JSONL structure for executor operation events; it does not audit operational correctness.
- Corpus validation checks strict schema, bounded vocabulary, deterministic ordering, coverage, and manually authored ground-truth consistency without executing a provider. Generated evidence locations remain outside corpus authority.
- Divergence from foxcommand-runtime reference tooling is intentional where FoxCommand manifest lifecycle, runtime boundary, deployment, closeout, and documentation synchronization behavior is outside Violence_Checker scope.
