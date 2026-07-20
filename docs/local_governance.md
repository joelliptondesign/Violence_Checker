# Local Governance Tooling

Repository-local deterministic governance lives in `tools/repo_governance/`. It adapts only repository-appropriate concepts from FoxCommand Runtime: the Universal SITREC Standard's truth-preservation, invariant-lock, boundary-clarity, rehydration, daily-uniqueness, and generation/validation separation; deterministic inventories; current-SITREC selection and hygiene; artifact freshness; protected-authority hashes; authority scans; and composed baseline readiness.

FoxCommand Runtime was inspected through its `tools/sitrec_router.py`, `tools/repo_governance.py`, `tools/validate_sitrec.py`, `tools/validate_sitrec_hygiene.py`, and `docs/standards/UNIVERSAL_SITREC_STANDARD.md`. Violence_Checker does not import FoxCommand deployment, infrastructure, API, authentication, customer-authority, manifest lifecycle, documentation publication, or runtime-boundary capabilities.

## Commands

```sh
python3 -m tools.repo_governance repo-tree
python3 -m tools.repo_governance knowledge-graph
python3 -m tools.repo_governance route-sitrec
python3 -m tools.repo_governance sitrec
python3 -m tools.repo_governance validate-heartbeat
python3 -m tools.repo_governance validate-sitrec --path "docs/SITREC - 2026-07-20 Violence Checker Successor Semantic Baseline.md"
python3 -m tools.repo_governance validate-all
python3 -m tools.repo_governance baseline-readiness
```

## Deterministic SITREC routing and generation

`route-sitrec` is the required non-mutating preflight. `tools/repo_governance/sitrec_router.py` resolves the operational date with the `America/Los_Angeles` IANA timezone, inventories only top-level Markdown SITRECs directly under `docs/`, extracts dashed `YYYY-MM-DD` and compact `YYYYMMDD` filename dates, and reports one canonical decision: `UPDATE_CURRENT`, `CREATE_TODAY`, `ARCHIVE_AND_CREATE_TODAY`, or `NORMALIZE_ACTIVE_SET`. Its structured output explicitly confirms that the router did not mutate the filesystem.

`sitrec` is the repository-appropriate lifecycle mutation and generation stage. It is implemented in `tools/repo_governance/sitrec.py`, separate from routing and from the generic validators in `tools/repo_governance/governance.py`. It resolves the Pacific date once, routes before writing, and then:

- verifies every declared grounding anchor exists;
- reads corpus identity, schema versions, and case count from `evaluation/corpus/successor_corpus.json` without importing application code;
- updates the existing current-date active record rather than creating a duplicate;
- creates a current-date record when no active record exists;
- archives every stale active record under `docs/archive/sitrecs/` before creating the current-date record;
- normalizes multiple active records deterministically while preserving at most one current-date record;
- refuses duplicate operational dates, archive overwrites, malformed dates, and filename/document Operational Date disagreement before mutation;
- inventories archived prior SITRECs as historical provenance;
- renders all A–S sections with repository identity, current state, invariants, end-to-end model, an explicit authority table, contracts, negative boundaries, capabilities, limitations, guarantees, non-guarantees, grounding descriptions, ordered rehydration steps, lifecycle, validation, and responsibility boundaries;
- uses no network, provider, Git mutation, or generated timestamp, so the same repository state, resolved operational date, and title produce byte-identical content.

Exactly one top-level active SITREC is permitted after mutation, and its date must equal the Pacific operational date. No operational date may appear more than once across active and archived lifecycle-managed records. Archived files retain their original filenames and substantive bytes and are readable historical provenance, not active authority. The default active output is `docs/SITREC - <date> Violence Checker Successor Semantic Baseline.md`. `validate-all` independently reconstructs the current SITREC in memory and rejects drift from generator output. This generation-freshness check complements structural and lifecycle validation; it does not make the validator a source of application truth.

`validate-all` performs offline local governance checks:

- validates active and archived lifecycle-managed SITRECs structurally;
- requires exactly one active top-level SITREC whose date equals the resolved Pacific date;
- rejects stale, malformed, duplicate-date, and filename/document-date-mismatched lifecycle states;
- excludes `docs/archive/sitrecs/` from active selection;
- applies current-SITREC identity, semantic-authority, and historical-provenance hygiene;
- rejects a current SITREC that differs from deterministic repository generation;
- validates heartbeat JSONL structure; and
- regenerates the expected repository tree and knowledge graph in memory and rejects missing or stale governed files.

`baseline-readiness` composes `validate-all` authorities with:

- approved OPORD 004 design-document SHA-256 checks;
- creation-time corpus, run, baseline, comparison, and report SHA-256 checks;
- active-source scans for retired semantic authorities;
- authorized-baseline ancestry, staged-file, and Git whitespace checks;
- successor corpus validation and deterministic coverage; and
- the complete automated test suite.

Use `baseline-readiness --skip-tests` only when the complete suite was already run against the same unchanged working state. Before commit it accepts an unstaged candidate but rejects staged paths; after commit it should run against a clean worktree. The command does not stage, commit, call a provider, accept a baseline, or mutate historical evidence.

## Generated artifacts

- `docs/generated/repository_tree.txt`
- `docs/generated/repository_knowledge_graph.md`

Generation is deterministic and repository-scoped. Freshness validation compares these files byte-for-byte with an in-memory reconstruction. The knowledge graph includes the router, lifecycle tests, active SITREC, archived historical SITRECs, and both top-level and `tests/evaluation/` test modules.

## Evaluation and historical authority

The current authoritative synthetic corpus is `evaluation/corpus/successor_corpus.json`. Validation enforces its identity and versions, 48 stable ordered case IDs, synthetic designation, bounded vocabularies, proposition admissibility, expected derivation, deterministic policy agreement, primary-category coverage, and documentation-quality coverage without invoking a provider.

Creation-time evaluation artifacts use schema `1.0.0`; current artifacts use schema `2.0.0` and identify successor semantic schema `violence-checker.proposition-semantics` version `1.0.0`. Strict readers route recognized creation-time schemas only. Cross-family regression and legacy-to-successor baseline promotion are prohibited.

Protected hash constants deliberately bind the three approved OPORD 004 design documents and the creation-time corpus and four operational artifacts. Updating those hashes is not routine regeneration; it requires separate authority for the protected artifact change.
