# OPORD 004 Verification Authority

## Purpose

This matrix identifies the permanent deterministic test and governance authorities for the implemented successor semantic architecture. It supplements the approved migration strategy without changing its contracts, concepts, waves, or gates.

## Gate-to-test matrix

| Gate | Permanent authority | Primary tests |
| --- | --- | --- |
| A — contracts and provider boundary | Exact semantic identity/version, bounded vocabularies, strict fields, no silent required defaults, provider-object termination, one request, typed extraction failures, metadata exclusion | `tests/test_contracts.py`, `tests/test_semantic_extractor.py`, `tests/test_semantic_prompt.py`, `tests/test_semantic_authority_boundary.py` |
| B — validation and derivation | Identifier/reference integrity, ordering, relationship duplicates/direction/cycles, uncertainty applicability, support roles and coverage, contradiction rejection, schema short-circuit, deterministic issue order, active set and 48-case expected derivations | `tests/test_semantic_validation.py`, `tests/test_successor_validation_authority.py` |
| C — application and policy cutover | Input rejection before provider, raw/normalized narrative, typed failures, policy precedence, all failure mappings, unsupported input failure, 512 policy-view partitions, aggregate sole authority, exactly one request | `tests/test_input_boundary.py`, `tests/test_app_logic.py`, `tests/test_policy.py`, `tests/test_successor_policy_authority.py` |
| D — evaluation authority | 48 IDs and narrative bytes, metadata isolation, selection validation, exact one request per case, stable identifier paths, evidence omission/unsupported distinction, canonical run writing, overwrite refusal, explicit baseline acceptance and replacement | `tests/evaluation/test_corpus.py`, `tests/evaluation/test_contracts.py`, `tests/evaluation/test_runner.py`, `tests/evaluation/test_successor_artifact_lifecycle.py` |
| E — downstream workflow | Historical/object/self/correction/conflict/uncertainty context, deterministic presentation and preview, no external/provider call, empty/select/manual/run/stale Streamlit states, raw narrative display, semantic-first mobile ordering, synthetic/no-PHI notice, bounded missing configuration | `tests/test_comparison.py`, `tests/test_presentation.py`, `tests/test_salesforce_preview.py`, `tests/test_successor_downstream_authority.py`, `tests/test_streamlit_empty_state.py`, `tests/test_fixture_policy_regression.py`, `tests/test_config_and_app.py` |
| F — legacy isolation and reporting | Strict creation-time routing, malformed/unsupported rejection, read-only carrier, no legacy promotion, cross-family rejection, historical byte hashes, successor regression and stable report generation | `tests/evaluation/test_regression.py`, `tests/evaluation/test_successor_artifact_lifecycle.py` |
| G — baseline readiness | Current SITREC selection/hygiene, tree/graph determinism and freshness, nested evaluation test graphing, protected hashes, retired-authority scan, ancestry/staging/whitespace, corpus validation/coverage and complete suite | `tests/test_repo_governance.py`, `python3 -m tools.repo_governance baseline-readiness` |

## Consolidation rule

Collected-test count is evidence but not authority by itself. Parameterized cases and 48-case loops may consolidate implementation while every row above remains explicitly asserted. A future rewrite may remove an obsolete test only when its permanent behavior is retained elsewhere and the gate-to-test matrix is updated in the same reviewed change.

## Baseline rule

Baseline readiness requires all authorities above, unchanged approved design and creation-time artifact hashes, fresh generated governance artifacts, one current SITREC, no staged files, valid authorized-baseline ancestry, and a passing composed readiness command. It does not itself authorize a commit or baseline acceptance.
