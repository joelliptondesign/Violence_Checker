# Semantic Migration and Legacy Strategy

## 1. Purpose

This document defines the bounded implementation order and legacy strategy for replacing the active document-level semantic architecture with the approved proposition-oriented successor architecture. It is a migration plan only. It does not implement contracts, change behavior, migrate data, or authorize any later wave.

The plan is grounded in repository state at commit `367a5369dc43c2d451a8bf2b41776cff85d5c64d` and in the approved authorities `docs/semantic_design_basis.md` and `docs/successor_semantic_contract_specification.md`.

## 2. Scope and Non-Goals

The scope is the provider boundary, provider-independent contracts, structural and domain validation, deterministic derivation and policy, application orchestration, comparison, presentation, illustrative Salesforce preview, fixtures, evaluation ground truth and execution, serialization, historical readers, regression, reporting, tests, documentation, and governance.

This plan does not authorize source, prompt, policy, application, test, corpus, evaluation, presentation, preview, SITREC, or historical-artifact mutation. It does not define executable models or patches, run a provider, accept a baseline, connect to Salesforce, redefine policy outcomes, or expand beyond the demonstrated violence-detection domain. Injury scope, credibility, generalized temporal logic, clinical or legal conclusions, workflow, recommendations, and broader incident ontologies remain excluded.

## 3. Starting Repository State

The inspected root was `/Users/joellipton/Desktop/Violence_Checker`, branch `main`, at HEAD `367a5369dc43c2d451a8bf2b41776cff85d5c64d` with subject `docs: close OPORD 003 evaluation baseline`. HEAD exactly equaled the authorized baseline, and `git merge-base --is-ancestor` returned success. No files were staged.

The pre-change worktree contained only the expected OPORD 004 work: modified `docs/generated/repository_tree.txt`, `docs/generated/repository_knowledge_graph.md`, and `telemetry/executor_heartbeat.jsonl`; and untracked `docs/semantic_design_basis.md` and `docs/successor_semantic_contract_specification.md`. Those changes are preserved. No unexpected overlap was present.

The creation-time evaluation family is corpus, corpus-schema, and evaluation-schema version `1.0.0`, with run `INITIAL_OPERATIONAL_EVALUATION_001`, baseline `INITIAL_EVALUATION_BASELINE_001`, and comparison `INITIAL_OPERATIONAL_COMPARISON_001`. These identifiers and bytes are historical evidence, not successor authority.

## 4. Approved Successor Authority

The sole successor semantic authority is a validated `ViolenceSemanticEnvelope` with schema identity `violence-checker.proposition-semantics` and initial version `1.0.0`. Its authoritative content consists of envelope-local entities, propositions, relationships, uncertainties, evidence excerpts, evidence supports, and bounded extraction metadata. Raw narrative remains authoritative evidence; formatting-only normalization supplies the one inference input and retains provenance.

The provider proposes all semantic content in exactly one request. Provider-specific objects terminate at the provider adapter. Structural validation checks exact shape, identity, version, types, vocabularies, references, and collection rules. Domain validation checks violence-domain coherence, relationships, scoped evidence, and admissibility without inference or repair. Deterministic derivation alone produces direction, active assertion set, normalized relationships, evidence containment status, admissibility status, and a separately versioned typed policy-candidate view. Policy consumes only an explicit upstream failure or validated successor semantics plus that typed view.

Historical, object-directed, self-directed, negated, disputed, uncertain, accidental, and superseded content remains scoped context. Superseded propositions are inactive. Context never automatically becomes detected interpersonal violence. Provider confidence and free-form notes are not semantic equality or policy authority. The bounded vocabularies, identity rules, relationship direction, canonical ordering, evidence rules, uncertainty dimensions, and version rules in the successor specification are fixed design authority and are not reopened here.

## 5. Migration Principles

1. Current execution has exactly one semantic authority at every activation point. Coexistence in source before activation is not authority.
2. The current pipeline remains entirely legacy until the atomic Wave C cutover; successor code introduced earlier is unreachable from current application and evaluation entry points.
3. At cutover, all active semantic stages switch together. Any downstream surface not ready for successor input fails closed or is disabled; it may not route current content through legacy semantics.
4. No permanent dual write, shadow global semantic record, dual policy evaluation, dual corpus authority, dual current serialization, silent default, or reverse compatibility conversion is permitted.
5. Major stages exchange explicit typed contracts. Provider-independent semantic content never crosses a major stage as an ad hoc dictionary.
6. Exactly one provider request per valid analysis or evaluation case and no second semantic pass remain invariants.
7. Validation and derivation do not infer, repair, reconcile, or fill missing semantics. Policy and reporting remain deterministic.
8. Ground truth is manually repository-authored and independent of every observed or generated output.
9. Historical artifacts remain byte-unchanged and route only to creation-time readers.
10. Every wave is a separately reviewable change group and stops on its gate. A passed earlier gate does not authorize a later wave.

## 6. Complete Dependency Matrix

In the tables below, “adapter” means a temporary typed boundary, not a second authority. “Legacy” identifies creation-time reading needs. “Retire” gives the deletion or isolation condition. “Cutover” identifies the dependency that must be satisfied before Wave C activation or a later current capability can be enabled.

### Provider, contracts, validation, policy, and application

| File | Current role; consumes → produces | Successor dependency | Wave | Adapter / legacy | Retire, test authority, immutability, cutover dependency |
| --- | --- | --- | --- | --- | --- |
| `src/models.py` | `Incident`; defines `ViolenceEventType`, `Intentionality`, `ViolenceFinding` | Keep incident input; move successor semantic types to explicit contract authority | A/G | No active adapter; legacy types may be imported only by legacy readers | Retire current semantic uses at C; remove or isolate legacy definitions at G after reader imports are bounded; `tests/test_models.py`; no artifact rewrite; contract graph must be ready |
| `src/contracts.py` | Defines provider/global facts, validation, policy, preview, and `PipelineResult`; global contracts → aggregate | Successor provider schema, envelope, admissibility carrier, derivation and policy-input views, successor aggregate, schema identity/version | A/C | Temporary coexistence only; legacy contracts retained for legacy reader modules | Global contracts lose current authority at C; isolate/delete at G; contract and aggregate tests; serialized historical aggregates require legacy models; all active consumers must compile against successor aggregate |
| `src/semantic_prompt.py` | Narrative instructions → global provider fields | One-response proposition envelope and exact linked evidence instructions | A | None; no legacy runtime use | Old prompt retires at C; `tests/test_semantic_prompt.py`; extraction contract identity must be explicit |
| `src/semantic_extractor.py` | Normalized narrative + provider client → `SemanticExtractionResult` candidate | Exact successor provider schema, typed provider-independent extraction result, one request | A | No semantic adapter; legacy extraction only for historical fixtures if a reader never calls provider | Old result retires from current path at C; extractor tests protect one request and failures; cutover requires provider-boundary tests without live execution |
| `src/provider_adapter.py` | `ProviderStructuredResponse` → dictionary | Provider object → typed provider-independent candidate/envelope input | A | One-way provider termination only | Global dictionary adapter retires at C; authority-boundary tests; no legacy artifact dependency; successor validator must receive typed content |
| `src/config.py` | Loads provider key/model | Record successor extraction-contract identity without changing provider count | A | None | Configuration remains; config tests; no cutover unless model/config provenance is explicit |
| `src/schema_validation.py` | Mapping/global facts → `SemanticFacts` or issues | Identity/version, exact successor structure, enums, references, ordering, no defaults | B | No legacy validation in current path | Global validator becomes legacy-only or is removed at C/G; validation tests; historical validation results are read, never rerun; all successor malformed states fail closed |
| `src/domain_validation.py` | `SemanticFacts` → domain issues | Proposition/reference/relationship/evidence/uncertainty coherence and atomic envelope failure | B | None | Global rules retire from current path at C; validation tests; creation-time rejections immutable; complete rule enumeration required |
| `src/semantic_validation.py` | Candidate → staged `ValidationResult` and `ValidatedSemanticFacts` | Ordered successor schema/domain gates and typed validated envelope | B | No fallback to global facts | Old orchestrator retires from current path at C; validation tests; cutover requires no invalid envelope reaches derivation/policy |
| successor deterministic derivation boundary (placement decided in implementation without changing concepts) | No dedicated current module; limited logic is distributed | Direction, active set, relationship normalization, containment, admissibility, versioned policy candidate | B | None | New authority; derivation tests; must exist before policy migration and must not use legacy fields |
| `src/compatibility_finding.py` | `ValidatedSemanticFacts` → `CompatibilityFindingResult` / `ViolenceFinding` | No successor active equivalent | C/F/G | May remain only behind creation-time legacy reader/rendering boundary; never successor → finding | Remove from active orchestration at C; isolate at F; delete if no legacy loader requires construction at G; authority and validation tests; historical serialized findings remain unchanged |
| `src/policy.py` | validated global facts + exactly matching finding or failure → decision | Validated envelope + versioned candidate view or failure | C | No dual evaluation, no finding adapter | Old input branch retires at C; policy tests replace global state enumeration with successor state enumeration; preserved outcomes are observations only; all admissible states must be enumerated |
| `src/app_logic.py` | Input/normalization/regex/extraction/validation/compatibility/policy/comparison/preview → `AnalysisResult` | Successor stages and aggregate; one call; fail-closed optional downstream surfaces | C | May call typed downstream views; cannot construct `ViolenceFinding` | Existing orchestration switches atomically at C; app/input/fixture tests; raw narrative and stale-result behavior unchanged; every active consumer must accept successor or be disabled |
| `src/contract_adapters.py` | `AnalysisResult` → `PipelineResult` | Successor aggregate only | C/G | Only file temporarily allowed to recognize old and new aggregate types during pre-cutover tests; no semantic conversion | Old branch deleted at C or immediately after cutover gate; contract tests; historical aggregates load elsewhere; cutover requires successor serialization consumers |
| `app.py` | Streamlit state and aggregate → stakeholder and technical display | Successor aggregate and typed presentation details | C/E | Temporary display boundary may know both only before cutover; after C it must reject legacy current results | Old current rendering retires at C/E; Streamlit tests; no historical artifact role; stale invalidation and no-call-on-render required |
| `src/input_validation.py` | candidate → validated incident | No semantic change; preserve incident identity and raw bytes | C | None | Retained; input tests; cutover requires incident/envelope identity binding |
| `src/narrative_normalizer.py` | validated incident → normalization provenance | No semantic change; preserve single formatting-only input | C | None | Retained; input tests; raw/normalized invariant gate |
| `src/regex_baseline.py` | narrative → lexical result | Remains non-authoritative comparison input | C/E | None | Retained; regex tests; cannot author successor semantics |

### Downstream representation and fixtures

| File | Current role; consumes → produces | Successor dependency | Wave | Adapter / legacy | Retire, test authority, immutability, cutover dependency |
| --- | --- | --- | --- | --- | --- |
| `src/comparison.py` | regex + compatibility finding → alignment/enrichment | Regex + typed policy/derived successor view → deterministic operational comparison | C/E | A typed successor comparison view is allowed; no successor → `ViolenceFinding` | Legacy semantic path leaves current execution at C and is deleted/isolation-tested at E/G; `tests/test_comparison.py`; preserve operational meaning; minimum cutover implementation required before activation |
| `src/presentation.py` | validated globals + decision → labels/summary | Validated active propositions + derived/policy views → display-only output | E | Typed lossy display summary allowed only as non-authoritative output | Global summary path retires at E; presentation tests; no semantic inference or second call; C may expose only safe minimal status until E gate |
| `src/salesforce_preview.py` | finding + decision → illustrative global dictionary | Policy-approved typed successor preview view → illustrative payload | E | No semantic compatibility object; legacy payload only in historical rendering | Global current fields retire at E; preview tests; no real connection; C must disable preview until successor mapper passes |
| `src/fixtures.py` | Eight stable narratives and metadata | Narratives remain input fixtures; successor expected behavior lives only in tests | E | None | Retain narratives byte-for-byte; fixture tests/regression; no fixture metadata reaches provider |
| `src/contracts.py` `SalesforcePayload` portion | Global preview fields → typed aggregate payload | New typed illustrative successor preview without global authority | E | Historical payload belongs to legacy run model | Old current payload isolated at F/G; preview/contract tests; historical bytes unchanged |
| `app.py` technical details and workflow | Global facts/finding display | Proposition, relationship, uncertainty, evidence, validation, policy, and preview display | E | No inference; no hidden flattening | Global technical detail path deleted at E; Streamlit tests; raw narrative unchanged and preview absent on failure |

### Evaluation, artifacts, and serialization

| File or artifact | Current role; consumes → produces | Successor dependency | Wave | Adapter / legacy | Retire, test authority, immutability, cutover dependency |
| --- | --- | --- | --- | --- | --- |
| `src/evaluation/contracts.py` | Global expected/observed facts, finding, policy, differences | Successor expected/observed entities, propositions, relationships, uncertainty, support, active set, validation and separate policy | D/F | Separate legacy and successor contract families; never one permissive union | Global family becomes legacy-only at D/F; `tests/evaluation/test_contracts.py`; historical payloads require exact models; successor corpus must compile |
| `src/evaluation/run_contracts.py` | Full `PipelineResult` observations → run artifact | Successor aggregate observations, semantic schema identity, artifact schema identity/version | D/F | Strict family-specific models | Old models route only legacy artifacts after D; runner/contract tests; existing run immutable; new identity required |
| `src/evaluation/corpus.py` | Strict corpus loader/validator; current corpus → ground truth | Family router plus strict successor corpus validator, canonical ordering, asserted/unasserted rules | D/F | Legacy corpus loader and successor loader are separate | Legacy corpus prohibited from new runs at C; successor becomes sole new-run authority at D; corpus tests; current corpus preserved as historical artifact |
| `src/evaluation/case_comparison.py` | Global field/evidence/policy comparison → differences/findings | Identifier-addressed proposition/entity/relationship/uncertainty/evidence differences; validation and policy separate | D/F | Family-specific comparator; cross-family returns typed incomparable | Global comparator legacy-only at D/F; runner tests; old labels preserved; no lossy cross-schema mapping |
| `src/evaluation/runner.py` | Corpus + complete app pipeline → run and evaluations | Successor corpus + successor aggregate → successor run; exactly one request | D | At C legacy new-run mode is disabled; no fallback | Current capability re-enabled only at D; runner tests; existing run protected; deterministic executor precedes any separately authorized live run |
| `src/evaluation/baseline.py` | Loads run/baseline and accepts immutable baseline | Schema-routed loads; successor baseline new ID and explicit acceptance | D/F | Separate legacy/successor loaders | Legacy acceptance prohibited for successor runs; baseline tests; existing baseline immutable; no successor baseline implicitly accepted |
| `src/evaluation/regression_contracts.py` | Baseline/regression schemas | Family-tagged successor contracts and typed incomparable result | D/F | Legacy contracts isolated | Old family historical-only; regression tests; preserved comparison bytes; both inputs must share supported family for comparable result |
| `src/evaluation/regression.py` | Baseline + current run → comparison | Route by identity/version; successor proposition paths; typed incomparable across families | D/F | No compatibility translation | Old comparator legacy-only; regression tests; no historical rewrite; successor IDs required |
| `src/evaluation/reporting.py` | Regression artifact → Markdown | Family-specific current successor report and bounded legacy renderer | F | Strict historical renderer terminates at display | Legacy renderer retained permanently only if needed for readability; reporting tests; never re-render existing report in place |
| `src/evaluation/serialization.py` | Canonical model dump → JSON | Strict family identity, UTF-8 deterministic lossless encoding, canonical collection order, no defaults | D/F | Family chosen before deserialization | Current generic entry must not guess; serialization tests; existing artifacts never reserialized; required before successor run writing |
| `src/evaluation/artifact_cli.py` | Accept/compare/report commands | Identity-routed successor operations and explicit legacy read-only commands | D/F | Command must select supported family from declared identity | Legacy mutation commands prohibited; regression tests; output overwrite protection remains; current operation requires successor family |
| `evaluation/corpus/corpus.json` | 48-case manual global ground truth | Preserved legacy corpus; successor corpus receives new identity/version in separately authorized mutation | D | Legacy loader only | Never rewritten or used for new successor runs after C; corpus tests; byte immutable; successor corpus must preserve IDs/narratives |
| `evaluation/runs/initial-operational-evaluation-001.json` | Creation-time observed run | Legacy run reader only | F | Legacy route by evaluation schema `1.0.0` plus artifact shape/identity | Permanent historical evidence; loader tests; byte immutable; never policy/evaluation input |
| `evaluation/baselines/initial-evaluation-baseline-001.json` | Accepted creation-time snapshot | Legacy baseline reader only | F | Legacy route by artifact type and schema | Permanent historical evidence; baseline tests; byte immutable; not ground truth or successor acceptance |
| `evaluation/reports/initial-operational-comparison-001.json` | Creation-time self-comparison | Legacy regression reader only | F | Legacy route by artifact type and schema | Permanent historical evidence; regression tests; byte immutable; never compared directly to successor family |
| `evaluation/reports/initial-operational-evaluation-001.md` | Creation-time engineering report | Historical display/file serving only | F | No semantic loader required beyond structure if displayed | Permanent historical evidence; report structure test; byte immutable; never regenerated |
| `evaluation/README.md`; `evaluation/corpus/README.md`; `evaluation/runs/README.md`; `evaluation/baselines/README.md`; `evaluation/reports/README.md` | Current authority and artifact rules | Document successor/legacy family separation, IDs, routing, and prohibitions | G | Historical statements retained where identified | Update current instructions only; documentation review; no artifact mutation; after all behaviors pass |

### Documentation, governance, and tests

| File/group | Current role | Successor dependency and wave | Temporary / legacy rule | Retirement, test authority, immutability, cutover dependency |
| --- | --- | --- | --- | --- |
| `README.md` | Current usage and authority | G: successor current state and legacy commands | No legacy authority | Current global description retires after implementation; documentation gate |
| `docs/architecture.md` | Detailed current architecture | G: successor flow, cutover, readers | Preserve creation-time history only when labeled | Update after code truth; documentation gate |
| `docs/demo_runbook.md` | Stakeholder workflow | G after E: proposition-aware workflow without inference | No historical reader | Update only after downstream tests; one-call and failure behavior remain |
| `docs/local_governance.md` | Deterministic validation commands | G: successor validations and immutability checks | Historical load checks remain | Governance gate; no live-provider command in closeout |
| active `docs/SITREC - 2026-07-18 Violence Checker Narrative Source Control Baseline.md` | Current rehydration authority | G: supersede/update only under separate authorization | Historical SITREC remains immutable when superseded | Cannot change in this brief; later SITREC gate follows code and docs |
| `docs/generated/repository_tree.txt`; `docs/generated/repository_knowledge_graph.md` | Deterministic repository inventory | Each approved change group if generation differs; final at G | No semantic authority | Regenerate only with governance tool; `tests/test_repo_governance.py`; cutover scan uses graph |
| `tools/repo_governance/` | Tree, graph, heartbeat, SITREC validation | G only if new deterministic checks are authorized | No schema fallback | Governance tests; tool must not infer semantic authority |
| `telemetry/executor_heartbeat.jsonl` | Operations audit | Append per authorized brief | Historical lines immutable | Governance validation; not semantic authority |
| `tests/test_models.py` | Incident and `ViolenceFinding` rules | A contracts; F permanent legacy construction only if reader needs it; G remove active expectations | Legacy cases explicitly named | Delete current-execution finding tests when no active import; preserve historical-reader tests |
| `tests/test_contracts.py` | Provider/global/aggregate/preview contracts | A/C/E successor replacements; F legacy round trips | Temporary coexistence through C | Old current aggregate tests deleted at C; permanent historical serialization tests remain |
| `tests/test_semantic_extractor.py`; `tests/test_semantic_prompt.py`; `tests/test_semantic_authority_boundary.py` | Provider shape, prompt, one request, isolation | A successor provider boundary | No legacy current path | Replace global expectations at A/C; preserve no-call and provider termination tests |
| `tests/test_semantic_validation.py` | Structural/domain/admissibility/global compatibility | B successor validation and derivation | Legacy validation tests move to reader suite only if artifacts require reconstruction, normally not | Delete global current-execution cases at C; add references, relationships, uncertainty, evidence, active-set rejection tests |
| `tests/test_policy.py` | Global admissible-state policy enumeration and failure gating | C successor policy candidate enumeration | No dual evaluation | Replace old state space at C; preserve failure precedence and no-call assertions |
| `tests/test_app_logic.py`; `tests/test_input_boundary.py` | Orchestration, normalization, one call, failure/stale boundaries | C successor aggregate | No legacy current orchestration | Replace global expected payloads at C; preserve input/raw/normalization/one-call tests |
| `tests/test_comparison.py` | Regex/global finding comparison | C minimum safe successor mapping; E full downstream behavior | No finding conversion | Retire global comparison cases at E; add contextual-proposition non-promotion tests |
| `tests/test_presentation.py`; `tests/test_salesforce_preview.py`; `tests/test_streamlit_empty_state.py` | Display, preview, workflow | E successor representation | Legacy historical rendering tested separately | Replace global current assertions at E; preserve failed-policy preview block, stale clearing, and no calls |
| `tests/test_fixtures.py`; `tests/test_fixture_policy_regression.py`; `tests/test_regex_baseline.py` | Fixture bytes, expected policy, lexical behavior | E successor policy expectations; regex retained | No corpus authority | Preserve narrative bytes and fixture IDs; replace only semantic/policy expected shape |
| `tests/evaluation/test_contracts.py`; `tests/evaluation/test_corpus.py` | Evaluation schemas, manual authority, coverage | D successor asserted/unasserted contracts and corpus validation | Add permanent legacy routing tests in F | Old current schema tests become legacy-specific; corpus ID/narrative preservation and synthetic-only tests required |
| `tests/evaluation/test_runner.py` | Full 48 deterministic execution, comparison paths, one call, artifacts | D successor deterministic executor and run | Legacy runner cannot create new runs | Replace global comparison paths; retain stable ordering, provider failure, immutable output, one-call tests |
| `tests/evaluation/test_regression.py` | Baseline, regression, reporting, CLI | D successor artifacts; F identity routing and legacy isolation | Both families read separately, never coerced | Permanent historical loader/hash tests; successor baseline requires explicit acceptance |
| `tests/test_config_and_app.py`; `tests/test_fixtures.py`; `tests/test_repo_governance.py` | Non-semantic import/config/fixture/governance guards | A/E/G as applicable | None | Retain unless successor provenance changes exact config expectations |

The matrix includes every repository boundary named in the execution package. `src/input_validation.py`, `src/narrative_normalizer.py`, and `src/regex_baseline.py` are included because application cutover depends on their invariants even though their authorities do not change. `scripts/live_smoke_test.py` is outside normal tests but is a provider-capable entry point: it must remain disabled during deterministic gates and migrate to successor validation only under separate live-smoke authorization in G or later.

## 7. Migration Waves

### 7.1 Wave A — Successor Contract Foundation

Prerequisites are approved design documents, clean wave scope, baseline ancestry, and no overlapping changes. Create the successor provider-facing schema, provider-independent envelope and component contracts, extraction-result carrier, schema identity/version constants, and contract-only tests. Modify no current entry point. Provider objects must still terminate at the adapter, and current execution must remain byte-for-byte behaviorally legacy.

Intermediate state: successor contract code is present but unreachable from `run_analysis`, the Streamlit app, and evaluation runner. Current and successor types coexist in source only. Stop if a required concept or vocabulary is absent from the specification, typed stage boundaries require dictionaries, or one-response construction cannot be expressed.

### 7.2 Wave B — Validation and Derivation

Prerequisite is Gate A. Implement successor structural validation, domain admissibility, combined validation, deterministic direction, active set, relationship normalization, evidence containment, admissibility carrier, and versioned policy candidate view. Tests must enumerate identity, references, ordering, relationship integrity, uncertainty applicability, exact evidence support, contradictions, and atomic failure. No current execution path changes.

Intermediate state: an offline successor envelope can be deterministically validated and derived, while current execution remains legacy. Stop on inference/repair pressure, silent defaults, unsupported admissible states, or any derivation that needs regex, presentation, provider confidence, free-form notes, legacy globals, or a second provider call.

### 7.3 Wave C — Core Application and Policy Cutover

Prerequisite is Gate B plus complete policy-state enumeration and minimum safe successor mappings for comparison/status display. Migrate policy input, policy evaluation, extraction orchestration, aggregate pipeline contracts, and application orchestration in one wave-bounded activation change. Remove compatibility construction from active execution. Preserve raw narrative, normalization, regex, one request, failure provenance, stale invalidation, and preview gating.

This wave contains the authority switch. Current evaluation execution, baseline acceptance, regression generation, reporting generation, preview, or rich presentation that is not yet successor-capable must fail closed or be explicitly unavailable; none may fall back to global contracts. Existing historical artifact reading remains available only where already read-only and isolated.

Intermediate state after Gate C: successor semantics is the sole current semantic authority. Some current optional capabilities may be disabled pending D/E. Legacy current execution cannot be restored without rolling back the entire C change group.

### 7.4 Wave D — Evaluation Authority Migration

Prerequisites are Gate C and a separately reviewed manual 48-case successor corpus change. Introduce successor evaluation contracts, a new corpus identity/version family, manually authored proposition ground truth, strict validation, deterministic-test execution, identifier-addressed comparison, successor run serialization, and new run identity. Re-enable current evaluation only for the successor family.

Observed outputs, old global expectations, accepted baselines, regex, policy outcomes, and preserved artifacts cannot seed ground truth. The deterministic executor is authorized before any live-provider run. No baseline is accepted implicitly. Intermediate state: current successor evaluation works; old corpus and artifacts are historical read-only inputs awaiting fully explicit routing in F.

### 7.5 Wave E — Downstream Migration

Prerequisites are Gate C and successful successor aggregate/policy tests; Gate D may run in parallel only as a separate unactivated change group, but both must pass before broad release. Migrate regex-versus-semantic comparison, stakeholder presentation, technical details, illustrative Salesforce preview, fixture regression, and Streamlit workflow to typed successor views.

Operational meaning remains primary. Display may summarize but cannot become semantic or policy authority. Preview performs no policy inference, cannot exist for failed policy, and makes no external connection. Contextual propositions cannot automatically become detected interpersonal violence. Intermediate state: all current user-facing surfaces consume successor contracts; no global current representation remains.

### 7.6 Wave F — Legacy Readers and Reporting

Prerequisites are Gates D and E. Add explicit artifact-family routing and strictly separated legacy run, baseline, regression, and report readers. Add successor current reporting. Unsupported or malformed identities fail closed; cross-family regression is a typed incomparable result, not a field comparison. Legacy readers terminate at historical display or creation-time comparison and cannot produce current policy input, current evaluation observations, or successor evidence.

Intermediate state: current successor operations and historical legacy reading coexist as separate authorities with distinct entry points. Coexistence here is not mixed current authority.

### 7.7 Wave G — Cleanup and Closeout

Prerequisite is Gate F. Remove dead transitional adapters, active imports of `ViolenceFinding`, `ViolenceEventType`, global `SemanticFacts`, `ValidatedSemanticFacts`, `CompatibilityFindingResult`, `operational_finding`, legacy comparison fields, legacy preview globals, and legacy expected/observed fields. Retain legacy types only inside named reader modules when required to parse historical bytes. Update current documentation and authorized SITREC, regenerate governance artifacts, run the full deterministic suite and final scans, and form a wave-bounded baseline commit only after Kilgore approval.

No live-provider execution is part of closeout. Any live smoke test is separately authorized and produces a new non-accepted successor run identity.

## 8. Mixed-State Strategy

Successor contracts first enter the repository in Wave A. The only mixed-current-contract interval is the unactivated implementation interval from the first Wave A change through the Wave C activation. It is bounded to three wave change groups—A, B, and C—and must not span a release or accepted baseline. Current entry points remain entirely legacy before C; successor contracts are exercised only by contract/validation tests. After C, current entry points are entirely successor and incapable consumers fail closed.

Files temporarily allowed to know both families are `src/contracts.py` while definitions are separated, `src/contract_adapters.py` during aggregate test transition, and specifically named evaluation routing/legacy-reader modules in D/F. Test files may import both solely to prove isolation. `app.py`, policy, provider adapter, active validation, active comparison, active preview, and the active evaluation runner must not select contracts implicitly.

Legacy schema families may remain after C only as creation-time reader types. That permanent read capability is not a mixed-state current architecture: legacy objects terminate before current orchestration. Tests enforce that no current import graph from `app.py`, `src/app_logic.py`, `src/policy.py`, or `src/evaluation/runner.py` reaches a legacy semantic reader.

The cutover trigger is complete Gates A and B plus all C preconditions in Section 9. The adapter deletion trigger is Gate E for active downstream bridges and Gate F for generic routing bridges; final dead code is removed at G. The final authority scan in Section 22 is mandatory.

## 9. Authority Cutover Definition

The exact cutover point is the Wave C activation commit/change group that simultaneously makes the successor extraction result, validated envelope, derived policy candidate, successor policy path, and successor application aggregate the only contracts reachable from `run_analysis` and `app.py`, and removes `construct_compatibility_finding` from that call graph. This is an atomic repository boundary, not a gradual runtime flag.

At that point:

- provider output is the approved successor structured schema and terminates in a typed provider-independent contract;
- validation accepts only the supported successor identity/version for current execution;
- policy accepts only upstream failure or validated successor envelope plus typed policy view;
- the application aggregate carries no `operational_finding` or global semantic authority;
- comparison and minimal presentation consume typed successor/policy views or are unavailable;
- Salesforce preview is successor-capable or unavailable, and remains absent for failed policy;
- the legacy evaluation runner is prohibited from new execution until D enables the successor runner;
- the legacy corpus becomes historical-only and cannot be current ground truth for new execution;
- no new run, baseline, comparison, or report can serialize the legacy family; and
- current reporting is unavailable until successor reporting is enabled, while historical display remains read-only.

Preconditions are passing successor contracts and validation tests; complete enumeration of deterministic policy input states; no unsupported admissible state; passing application, normalization, failure, stale-state, and one-request tests; a validating successor corpus change ready for D without derived ground truth; a complete deterministic 48-case successor test execution plan; no current path requiring `ViolenceFinding`; and proven isolation of legacy readers. If any condition fails, C does not activate.

## 10. Transitional Adapter Rules

No semantic adapter from the successor envelope to `ViolenceFinding`, `SemanticFacts`, or legacy expected/observed fields is allowed in current execution. Such a conversion is necessarily lossy because global fields cannot preserve proposition identity, relationships, uncertainty subjects, or evidence supports.

Allowed adapters are limited to:

- provider-specific successor response to the identically expressive typed provider-independent candidate, one way, before validation;
- validated successor envelope to separately typed deterministic policy, comparison, presentation, and preview views, one way, with explicit version and provenance;
- current internal result to successor aggregate, one way;
- serialized artifact bytes to the exact creation-time legacy model or exact successor model after explicit schema-family routing; and
- legacy model to historical rendering data within the reader boundary only.

Reverse adaptation, implicit field defaults, fallback guessing, automatic identity coercion, dropped propositions, collapsed evidence, and reuse of display summaries as semantic input are prohibited. Every adapter must be deterministic, typed, tested for losslessness over its declared authoritative inputs, and deleted when all declared consumers accept the upstream contract directly.

## 11. Compatibility Retirement Plan

| Transitional authority | Temporary need | Retirement / isolation | Prohibited after C |
| --- | --- | --- | --- |
| `ViolenceFinding` | Pre-C current execution; post-C exact legacy deserialization only if required | Remove active construction/imports in C; confine remaining definition/imports to legacy readers by F; delete at G if no reader needs class construction | Policy, application, comparison, preview, current evaluation, current reporting |
| `ViolenceEventType` and current `Intentionality` | Pre-C global contracts and legacy artifact parsing | Remove current semantic use in C/E; retain only legacy model namespace if necessary | Mapping successor conduct/completion/contact into old event type; current policy |
| global `SemanticFacts` | Pre-C schema/domain/policy/evaluation; historical parsing | Replace current validation/policy/aggregate in A-C; isolate legacy model in F/G | Current semantic authority, derivation, policy, evaluation truth |
| `ValidatedSemanticFacts` | Pre-C admissibility carrier | Replace with validated successor carrier in B/C | Current policy or presentation |
| `CompatibilityFindingResult` | Pre-C typed compatibility failure | Remove from `AnalysisResult` and active comparison in C; legacy-only or delete in F/G | Current failure or success representation |
| `compatibility_finding.py` | Pre-C constructor; no need to reconstruct stored artifacts unless exact reader proves it | Remove active imports C; isolate or delete G | Successor-to-global conversion |
| `PipelineResult.operational_finding` | Pre-C aggregate and historical run bytes | Omit from successor aggregate at C; retain only legacy run model F | Any new artifact or current renderer |
| legacy semantic comparison paths | Historical family comparison/rendering only | Successor identifier paths in D; legacy comparator namespaced in F | Cross-family equality or successor comparison |
| legacy Salesforce global fields | Historical payload reading only | New typed preview E; old payload in legacy run reader F | Current preview, policy, or semantic summary |
| legacy expected/observed semantic fields | Historical corpus/run/baseline/comparison reading | New evaluation models D; old models legacy-only F | New successor ground truth, runs, baselines, or reports |

Equivalent renamed global records are subject to the same rules. The final scan checks semantics and call graphs, not only class names.

## 12. Legacy Artifact Routing

Routing reads a minimal artifact header before constructing a semantic model. The routing key is an explicit artifact type or corpus identity together with evaluation/corpus schema identity and version present in the artifact. For creation-time files lacking a distinct named schema identity, the exact documented combination of top-level shape, artifact type where present, corpus identity, and `evaluation_schema_version=1.0.0` is the registered legacy route. The route is explicit code, not heuristic guessing.

The router dispatches to family-specific strict loaders. Legacy models live in a bounded legacy namespace; successor models live in a successor namespace. Neither imports current policy or application orchestration. Unknown identity/version returns a typed unsupported-schema failure. A recognized identity with malformed, missing, duplicate, or inconsistent fields returns a typed malformed-artifact failure. No fallback to another family occurs.

The initial run routes to the creation-time run loader, the accepted baseline to the creation-time baseline loader, and the initial comparison to the creation-time regression loader. The Markdown engineering report remains a byte-preserved historical document and may be served or structurally checked without semantic reinterpretation. Legacy rendering may display only creation-time values and labels with their provenance. It cannot invoke policy, create successor observed evidence, seed ground truth, or regenerate an artifact.

Current regression requires both operands to declare the same supported successor family and compatible versions. Different families produce an explicitly typed incomparable result with both identities; field differences are not attempted. No legacy observed evidence is translated into successor observed evidence, no successor proposition is inferred from global fields, and no historical artifact is rewritten.

## 13. Corpus Ground-Truth Migration Procedure

Corpus mutation is a separately authorized Wave D change, performed manually for all 48 cases.

1. Freeze and hash the legacy corpus. Preserve it in place as a historical version-routed corpus artifact and prohibit it from successor runs.
2. Create a new corpus identity/version and new corpus/evaluation schema identity/version that explicitly reference semantic schema `violence-checker.proposition-semantics` `1.0.0`. Do not overwrite `corpus.json` destructively; the final path and identity must be reviewed before mutation.
3. Copy only stable case ID, exact raw narrative bytes, synthetic designation, category metadata, documentation-quality tags, and other non-semantic authored metadata. A byte comparison must prove all 48 narratives are unchanged and IDs remain `EVAL_001` through `EVAL_048` in canonical order.
4. For each narrative, manually author the complete expected entity set; proposition set and scoped conduct, target, completion, contact, temporal scope, intentionality, assertion status, and attribution where explicit; negation, supersession, and conflict relationships; uncertainty records; exact excerpts and many-to-many evidence supports; derived directions and active set; expected structural/domain validation result; and a separate policy outcome/reasons expectation where applicable.
5. Mark every intentionally unasserted field explicitly. Asserted and intentionally unasserted sets are mutually exclusive; omission is never interpreted as unasserted.
6. Perform an independent per-case review. Ground truth cannot be copied, transformed, repaired, or suggested from provider output, preserved runs, accepted baselines, regex output, policy output, current observed results, or compatibility findings.
7. Conduct dedicated review of all compound cases and the historical, correction, conflict, object-directed, self-directed, ambiguous, incomplete-documentation, attempted/completed, threat, accidental-contact, negation, and direction-reversal categories.
8. Run strict deterministic validation, canonical ordering checks, unique-reference and evidence-containment checks, synthetic-only checks, category/tag coverage comparison, policy-balance review, stable-ID check, and narrative byte check.
9. Kilgore reviews each case or recorded case-level review evidence. No successor deterministic execution starts until all corpus issues are zero.

The legacy corpus remains readable only through its creation-time loader and is never coequal authority for a new successor run.

## 14. Evaluation Framework Migration

Successor expected and observed contracts carry explicit semantic and evaluation schema identities. Expected semantic success contains complete ordered asserted subjects; expected failure contains explicit validation stage and bounded issue paths/codes. Observed results preserve extraction, validation, policy, infrastructure, and provider failure provenance without fabricating semantic payloads.

Comparison uses stable identifier-addressed paths for entities, propositions, relationships, uncertainties, evidence excerpts/supports, and active-set membership. It distinguishes missing expected subject, unexpected observed subject, scalar/collection mismatch, relationship mismatch, evidence omission, unsupported evidence, validation mismatch, and policy mismatch. Evidence support, relationship, and active-set comparisons are explicit. Validation and policy comparisons remain separate from semantic comparison. Provider/infrastructure failures remain non-comparable with typed provenance, not semantic differences. Provider confidence and free-form notes remain excluded from equality.

Case order remains stable ID order; envelope collections use successor canonical order. The deterministic-test executor must exercise the complete governed successor pipeline without provider calls and prove all 48 manually authored cases. Live-provider execution remains separately authorized and still makes one request per selected case.

Successor runs, baselines, regression artifacts, and reports receive new family and artifact identities. Run serialization is strict, canonical, and lossless; overwrite remains refused. Baseline acceptance is explicit, points to one successor run, cannot overwrite an existing ID, and is never implied by a passing run. Historical baselines remain accepted only within their creation-time family. Cross-family regression is typed incomparable.

## 15. Downstream Representation Migration

Regex comparison receives the non-authoritative regex result and a typed successor policy/comparison view. It reports operational alignment and proposition-scoped context without reducing the semantic envelope to a global truth record. Contextual historical, object-directed, self-directed, negated, corrected, disputed, uncertain, or accidental propositions do not automatically produce detected interpersonal violence.

Presentation consumes validated successor views and `PolicyDecision`; it maps them to stakeholder labels, summaries, proposition details, relationships, uncertainty, and exact evidence without inference. Technical details expose schema identity/version, validation issues, derived active set, policy provenance, and provider/infrastructure failure state. Raw narrative display remains unchanged.

The illustrative Salesforce preview consumes an explicit policy-approved successor preview view. It does not evaluate policy, infer semantics, connect to Salesforce, contain real identifiers or credentials, or exist when policy failed. Any intentionally summarized fields are labeled display/write representations and never flow back upstream.

Streamlit preserves explicit Run Analysis behavior, one provider request, source and manual input behavior, stale-result invalidation, two-column primary comparison where applicable, safe empty state, and failure feedback. Fixture regression preserves all eight source narratives and tests successor policy behavior separately from the 48-case evaluation authority.

## 16. Test Migration Strategy

Wave A replaces provider/global contract expectations in `test_contracts`, `test_semantic_extractor`, `test_semantic_prompt`, and `test_semantic_authority_boundary` with exact schema identity/version, bounded vocabulary, proposition/entity/reference/evidence support identity, provider termination, and one-request tests. Legacy serialization tests are explicitly separated.

Wave B replaces global admissibility tests in `test_semantic_validation` and extends contract tests for referential integrity, duplicate/cycle/order rejection, uncertainty dimensions, evidence containment/support, negation/supersession/conflict rules, derived direction, active set, and atomic rejection. No unsupported admissible envelope may exist.

Wave C replaces global policy and aggregate tests in `test_policy`, `test_app_logic`, `test_input_boundary`, and `test_contracts`. It enumerates every admissible policy candidate state, proves failure precedence and no silent negative default, proves exactly one provider request and no second pass, and scans current imports/fields for active legacy authority.

Wave D replaces `tests/evaluation/test_contracts.py`, `test_corpus.py`, and `test_runner.py` current-authority cases with asserted/unasserted successor ground truth, 48-case deterministic execution, stable paths and ordering, narrative-byte preservation, proposition/evidence/relationship/active-set comparisons, explicit validation/policy differences, successor serialization, immutable run output, and explicit baseline acceptance.

Wave E replaces global comparison, presentation, preview, fixture regression, and Streamlit tests. Required behavior includes operational meaning, contextual non-promotion, no semantic inference, no provider/external calls, no preview on failure, exact evidence display, raw narrative preservation, and stale-result invalidation.

Wave F adds permanent tests that load the four named historical artifacts without byte changes; reject unsupported/malformed/ambiguous routes; prevent legacy-to-current imports; produce typed incomparable cross-family results; and keep legacy rendering outside current policy/evaluation execution. `test_regression` covers both strict families without translating them.

Wave G removes tests that protect obsolete current execution only after replacement coverage exists. Permanent tests retain incident/raw narrative, regex non-authority, provider isolation, one request, historical immutability/readability, explicit baseline acceptance, and governance behavior. A final source/AST scan proves no active `ViolenceFinding`, global facts, `operational_finding`, legacy comparison, or legacy preview dependency.

## 17. Verification Gates

Every gate records the exact commit/change group, changed-file list, test commands and outputs, scans, artifact hashes, Git status, and Kilgore review disposition. No gate runs a live provider.

### Gate A — Contract foundation accepted

- Tests: successor contract, provider boundary, exact identity/version, vocabulary, identifier/reference, strict serialization, extraction failure, and one-request construction tests.
- Deterministic commands: targeted Wave A tests, then the full automated suite.
- Scans/artifacts: provider SDK objects terminate at adapter; no current entry point imports successor types; no ad hoc dictionary crosses a major successor stage; historical hashes unchanged.
- Git: authorized Wave A files only, no staged surprises, diff check clean, baseline ancestry valid.
- Stop: design vocabulary gap, provider boundary leak, implicit default, second request, or current behavior change.
- Review evidence: contract inventory mapped line-by-line to specification Sections 5–9 and 16.

### Gate B — Validation accepted

- Tests: schema identity/version, strict types, collection order, references, relationship integrity/cycles, uncertainty applicability, evidence support/containment, contradiction rejection, deterministic derivations, active set, and atomic failure.
- Deterministic commands: targeted validation/derivation tests and full suite.
- Scans/artifacts: validation imports no provider/policy/presentation/regex/legacy compatibility; repeated issue ordering stable; historical hashes unchanged.
- Git: Wave B-only scope and clean whitespace.
- Stop: repair/inference, defaulting, unsupported admissible state, proposition loss, or policy logic in validation.
- Review evidence: admissibility rule checklist and derivation input/output table approved by Kilgore.

### Gate C — Core authority cutover accepted

- Tests: complete policy-state enumeration, no unsupported admissible states, application success/failure, aggregate contract, one request, no second pass, raw/normalized narrative, stale state, regex non-authority, and disabled-not-fallback downstream behavior.
- Deterministic commands: core targeted tests, full suite, current-authority source/AST scan.
- Scans/artifacts: `app.py`, `app_logic`, policy, active validation, active comparison, preview, runner call graph contain no `ViolenceFinding`, global facts, `CompatibilityFindingResult`, or `operational_finding`; historical hashes unchanged.
- Git: atomic C change group only; no partial activation; diff check clean.
- Stop: any current legacy fallback, dual policy, second provider call, unsupported state, or incapable consumer that does not fail closed.
- Review evidence: Kilgore signs the cutover checklist and exact call graph.

### Gate D — Evaluation authority accepted

- Tests: successor corpus strict validation; all 48 IDs/order; raw narrative byte equality; synthetic-only authority; category/tag coverage; manually authored asserted/unasserted expectations; deterministic 48-case execution; stable proposition paths; semantic/evidence/relationship/active-set, validation, and policy comparisons; run serialization and explicit baseline acceptance.
- Deterministic commands: corpus validate/coverage for both routed families as applicable, evaluation tests, full suite; no live mode.
- Scans/artifacts: no ground truth source imports observed outputs/provider/regex/policy/baseline; legacy corpus rejected for new runs; new artifact paths/IDs do not overwrite historical files.
- Git: corpus review manifest and Wave D scope; historical hashes unchanged.
- Stop: automatic conversion, changed ID/narrative byte, omitted category/tag, implicit baseline, or provider execution.
- Review evidence: 48 case-level author/reviewer records and Kilgore corpus acceptance.

### Gate E — Downstream workflow accepted

- Tests: comparison operational meaning, contextual non-promotion, presentation/technical details, preview gating, no Salesforce connection, fixtures, Streamlit empty/run/stale flows, raw narrative display, and no extra call.
- Deterministic commands: downstream targeted tests and full suite.
- Scans/artifacts: presentation/preview do not import provider or evaluate policy; no global current fields; fixture and corpus narrative hashes unchanged.
- Git: Wave E scope and clean diff.
- Stop: proposition loss that changes operational meaning, semantic/policy inference downstream, preview on failed policy, stale result, or second request.
- Review evidence: Kilgore mapping of each successor state to display/preview behavior.

### Gate F — Legacy isolation accepted

- Tests: strict loading of initial run, baseline, comparison, and report; unsupported/malformed/ambiguous schema failures; typed cross-family incomparable; successor reports; no legacy-to-current flow; byte immutability.
- Deterministic commands: historical loader tests, regression/reporting tests, full suite, recorded SHA-256 comparison.
- Scans/artifacts: legacy namespaces import neither current policy nor app/evaluation execution; no historical write path; all four bytes equal pre-migration hashes.
- Git: readers/reporting only; no artifact mutation.
- Stop: routing guess, fallback, rewrite requirement, legacy policy execution, or semantic translation.
- Review evidence: Kilgore routing table and import-boundary approval.

### Gate G — Final repository baseline accepted

- Tests: full automated suite and governance suite; all permanent authorities above.
- Deterministic commands: full tests, `python3 -m tools.repo_governance validate-all`, corpus validation/coverage, generated tree and graph regeneration/consistency, heartbeat validation, and Git whitespace validation.
- Scans/artifacts: final authority scan in Section 22; historical and corpus hashes; current docs match code; no live execution or unaccepted generated evidence.
- Git: expected files only, no staged surprises before review, clean diff checks, valid ancestry; commit only after explicit Kilgore authorization.
- Stop: any prior gate regression, dead adapter, current legacy import, docs/code contradiction, historical change, or live-provider evidence.
- Review evidence: complete Gate A–G record and Kilgore baseline acceptance.

## 18. Rollback Boundaries

Rollback is repository-only and wave-bounded. Historical artifacts and the legacy corpus are never mutated, so they require no data rollback. Each wave is a separate commit or explicitly recorded change group with its own gate.

Before Wave C activation, A or B may be reverted as whole change groups while the legacy current pipeline remains authoritative. Partial reversion that leaves reachable successor types is prohibited. Wave C rollback must revert the entire cutover group to the last single legacy authority; it cannot enable both pipelines or retain dual writes.

After C, rollback of D, E, or F retains successor current authority and disables the affected capability. It must not reactivate legacy evaluation, preview, reporting, or policy as current behavior. If C itself must be rolled back, successor-generated runs remain clearly identified, non-accepted evidence and are never relabeled as legacy. Failed-wave artifacts remain non-accepted and use unique identities or are removed only under their artifact rules. No rollback changes ground truth based on observed output, rewrites history, or converts evidence between families.

## 19. Stop Conditions

Stop before mutation or activation on any of the following:

- baseline lineage mismatch, unexpected staged work, or overlapping worktree changes;
- material contradiction between repository truth and the approved design authorities;
- any requirement to mutate or reserialize a historical run, baseline, comparison, report, or legacy corpus;
- inability to preserve exactly one provider request or pressure for a second semantic inference pass;
- inability to enumerate policy inputs or existence of an unsupported admissible state;
- requirement for permanent dual authority, dual write, dual corpus authority, or dual current serialization;
- inability to preserve all 48 stable IDs, raw narrative bytes, synthetic metadata, category coverage, or documentation-tag coverage;
- pressure to generate ground truth automatically or from observed/provider/baseline/regex/policy output;
- legacy reader or legacy object leaking into current application, policy, evaluation execution, or current reporting;
- missing, ambiguous, guessed, or fallback schema routing;
- proposition, relationship, uncertainty, attribution, evidence-support, or active-set loss in an authoritative downstream mapping;
- silent defaults, semantic repair, unsupported identity/version acceptance, or ad hoc dictionaries between major stages;
- expansion into excluded domains or policy redesign outside separate authority;
- presentation or preview performing semantic/policy inference, preview on failed policy, or a real Salesforce connection; or
- any live-provider execution without separate explicit authorization.

## 20. Commit and Review Boundaries

This Phase I package remains uncommitted and unstaged for Kilgore and Eagle Actual review. Later implementation uses one reviewable commit/change group per Wave A–G; Wave C is atomic and cannot be split across an authority switch. Corpus authoring may be subdivided for review, but no partial corpus becomes current and the final D activation is one reviewed authority change.

Each boundary records prerequisites, files, tests, deterministic output, scans, hashes, stop-condition assessment, and reviewer decision. Generated governance artifacts and telemetry belong to the wave that necessitates them. Historical artifacts never enter a mutation commit. A baseline commit is a Gate G outcome requiring explicit approval, not an automatic executor action.

## 21. Historical Immutability Controls

Before each wave, record SHA-256 hashes for the legacy corpus and four preserved artifacts. After each wave and rollback, compare those exact paths and fail on any difference. File permissions or protected-path tests should reject writes through runner, baseline, regression, reporting, and CLI entry points. Existing artifact paths retain overwrite refusal.

Legacy loading reads bytes without canonical reserialization. Tests compare bytes before and after loading/rendering. Historical IDs, timestamps, repository commits, provider observations, policy results, validation labels, compatibility findings, comparison classifications, and report wording remain creation-time evidence. No successor field, schema label, or inferred proposition is inserted. Accepted baselines remain observed snapshots, never ground truth.

## 22. Final Authority Scan

Gate G performs deterministic text and AST/import scans across active source, tests, corpus, documentation, and generated governance artifacts. It must prove:

- current provider, validation, derivation, policy, application, evaluation, comparison, presentation, and preview paths use the successor identity/version;
- active source has no dependency on `ViolenceFinding`, legacy `ViolenceEventType`, global `SemanticFacts`, `ValidatedSemanticFacts`, `CompatibilityFindingResult`, `compatibility_finding.py`, `operational_finding`, global expected/observed fields, or legacy Salesforce globals;
- any remaining symbol is confined to a named legacy reader, legacy contract, historical test, or explicitly historical documentation path;
- current entry points cannot import or call legacy readers;
- there is one current corpus family and one current run serializer;
- no successor-to-global adapter, dual policy, hidden default, second semantic pass, or provider object beyond the provider boundary exists;
- historical hashes match; and
- generated tree and graph reflect the final boundaries.

Any unexplained match fails the scan. Renamed equivalent global or shadow authorities also fail.

## 23. Phase II Entry Criteria

Broad mutation may begin only after Kilgore and Eagle Actual accept this strategy and boundedness review; repository HEAD still equals or descends from the authorized baseline; all expected Phase I changes are preserved and unexpected overlaps are absent; the design basis and successor specification remain unchanged or are re-approved; historical hashes are recorded; Wave A file scope and contracts are explicitly authorized; the mixed-state and cutover change groups are scheduled; every affected owner/file and test has a matrix entry; Gate A commands and evidence format are ready; corpus migration has a separate manual authority/review plan; legacy routing identities are registered; and live-provider execution remains separately gated.

Failure of any entry criterion stops Phase II. Entry does not authorize Waves B–G.

## 24. Boundedness Assessment

| Question | Result | Repository-grounded basis |
| --- | --- | --- |
| Every affected boundary mapped? | Pass | All named app, source, evaluation, artifact, documentation, governance, and test files are in Section 6; unchanged input/normalization/regex dependencies and provider smoke entry are also identified. |
| Mixed-current interval temporary? | Pass | It is limited to unactivated A–C change groups and cannot span a release/baseline. |
| Cutover unambiguous? | Pass | The atomic C activation removes compatibility construction from the current call graph and disables incapable consumers. |
| Permanent dual authority prohibited? | Pass | Post-C legacy schemas terminate in creation-time readers only. |
| Legacy readers isolated and artifacts immutable? | Pass | F uses strict family routes; Sections 12 and 21 prohibit writes and upstream flow. |
| Corpus migration manual and authority-separated? | Pass | All 48 cases require manual authoring, independent review, stable IDs, and narrative byte proof. |
| Every wave gated? | Pass | Gates A–G define tests, commands, scans, artifacts, Git checks, stops, and Kilgore evidence. |
| Compatibility retirement explicit? | Pass | Section 11 names every required authority and its C/F/G condition. |
| Implementation order complete? | Pass | A–G prerequisites, intermediate states, activation, deletion, and rollback boundaries are explicit. |
| Remaining questions blocking? | Pass; none | Approved design fixes semantics; implementation placement may not change authority and is reviewed within wave scope. |
| Violence-domain boundary preserved? | Pass | Excluded domains remain excluded; contextual self/object content exists only to preserve interpersonal scope. |
| Live-provider execution separately gated? | Pass | No gate authorizes it; deterministic execution precedes separate authorization. |

The migration is bounded. Implementation can proceed wave by wave without inventing migration order or authority boundaries, but cannot begin until Section 23 is satisfied.

## 25. Acceptance Criteria

This strategy is acceptable when review confirms all 27 required sections and seven named waves/gates; complete file-level dependency inventory; one successor current authority; bounded A–C mixed-current interval; atomic C cutover; one-way typed adapters and deletion triggers; complete compatibility retirement; strict creation-time schema routing; byte-immutable history; manual 48-case ground-truth migration with stable IDs and narrative bytes; proposition-level evaluation and new artifact identities; deterministic downstream behavior; wave-mapped tests; rollback and stop conditions; final authority scan; explicit Phase II entry criteria; no executable implementation; no migration or behavior change; no permanent dual authority; no excluded-domain expansion; and no live-provider authorization.

## 26. Unresolved Questions

None. The approved successor specification resolves the semantic questions required for sequencing. Later module placement and artifact path names are implementation details that must conform to the wave boundaries and cannot alter schema, authority, vocabularies, routing, or immutability rules.

## 27. Conclusion

The safe path adds unreachable successor contracts and validation first, performs one atomic current-authority cutover, restores evaluation and downstream capabilities only on typed successor contracts, then isolates creation-time readers and deletes transitional authority. The mixed-current interval is limited to Waves A–C; post-cutover legacy coexistence is read-only and cannot enter current execution. Historical bytes, manual ground truth, raw narrative authority, deterministic behavior, and exactly one provider request remain protected throughout.
