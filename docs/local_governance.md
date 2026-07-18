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

Generated artifact locations:

- `docs/generated/repository_tree.txt`
- `docs/generated/repository_knowledge_graph.md`

The local tooling must operate on an explicitly supplied repository root or the current working repository, write generated artifacts only inside Violence_Checker, avoid network access, avoid importing application code for validation, and avoid importing FoxCommand runtime application modules.

Limitations:

- The knowledge graph is static and repository-derived; unresolved relationships remain marked unresolved.
- The SITREC validator checks required structure and repository primacy language; it does not determine application truth.
- The heartbeat validator checks JSONL structure for executor operation events; it does not audit operational correctness.
- Divergence from foxcommand-runtime reference tooling is intentional where FoxCommand manifest lifecycle, runtime boundary, deployment, closeout, and documentation synchronization behavior is outside Violence_Checker scope.
