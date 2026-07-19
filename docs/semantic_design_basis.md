# Semantic Design Basis

## 1. Purpose and Scope

This document establishes the bounded, repository-grounded basis for successor semantic contract design under OPORD 004. It records current authorities, demonstrated representational limitations, affected repository boundaries, and the semantic distinctions supported by the existing violence-detection corpus and preserved evaluation evidence.

This document does not define or implement the successor contract. It does not select final class names, a final JSON schema, migration mechanics, compatibility behavior, or policy rules. It does not authorize implementation, active-pipeline changes, corpus changes, or changes to preserved evaluation artifacts.

Statements labeled **Repository fact** report inspected repository content or deterministic output. Statements labeled **Analytical conclusion** state a bounded implication of those facts for later design review.

## 2. Authoritative Repository Baseline

### Repository identity

**Repository fact.** The inspected repository root was `/Users/joellipton/Desktop/Violence_Checker`, on branch `main`, at commit `367a5369dc43c2d451a8bf2b41776cff85d5c64d` (`docs: close OPORD 003 evaluation baseline`), with parent `c9e644b702db496551331b9f43e80df6a5080519`. The inspected commit exactly equaled the authorized OPORD 003 baseline, so it also satisfied the required ancestry check. The pre-change working tree contained no staged, modified, or untracked files.

### Validation state

**Repository fact.** The following pre-change deterministic checks completed without provider execution:

- `.venv/bin/python -m pytest` passed all 331 tests.
- `python3 -m tools.repo_governance validate-all` passed.
- `python3 -m tools.repo_governance validate-heartbeat` passed.
- `.venv/bin/python -m src.evaluation.corpus validate` passed with 48 cases.
- `.venv/bin/python -m src.evaluation.corpus coverage` reported the complete deterministic coverage summarized below.
- Strict repository loaders accepted the preserved operational run, accepted baseline, and regression comparison, each with 48 cases. The preserved Markdown report contained its ten required creation-time sections in order.

The first attempted Markdown structure assertion used headings from a different report format and failed because those headings were not present. Inspection of the preserved report's actual headings followed by an assertion against that creation-time structure passed. No repository file was changed by either read-only check.

### Corpus and preserved evidence

**Repository fact.** `evaluation/corpus/corpus.json` is the authoritative, repository-authored `violence-checker-synthetic-evaluation-corpus`, corpus version `1.0.0`, corpus-schema version `1.0.0`, and evaluation-schema version `1.0.0`. It contains 48 ordered synthetic cases, `EVAL_001` through `EVAL_048`, and manually authored ground truth. Coverage includes four cases in each of twelve primary categories, 21 compound cases, 44 current-event cases, four historical-only cases, and all documented quality tags. Expected policy outcomes are 15 detected, 18 uncertain, and 15 not detected. All 48 expectations are expected semantic successes.

**Repository fact.** The preserved evidence inspected was:

- `evaluation/runs/initial-operational-evaluation-001.json`
- `evaluation/baselines/initial-evaluation-baseline-001.json`
- `evaluation/reports/initial-operational-comparison-001.json`
- `evaluation/reports/initial-operational-evaluation-001.md`

The operational run records 48 provider requests, zero provider failures, 14 domain-validation rejections, zero matches, 34 partial mismatches, and 14 failures. The accepted baseline snapshots that run. The comparison is a baseline self-comparison with 48 unchanged cases. These artifacts are observed historical evidence, not current semantic authority or ground truth. Creation-time labels in those artifacts, including legacy compatibility and uncertainty classifications, are preserved evidence rather than current comparator conclusions (`README.md`, `docs/local_governance.md`, `src/evaluation/case_comparison.py`).

### Current contract authorities

**Repository fact.** The relevant current authorities are `ViolenceEventType`, `Intentionality`, and transitional `ViolenceFinding` in `src/models.py`; provider-facing `ProviderStructuredResponse`, provider-independent `SemanticFacts`, admissibility carrier `ValidatedSemanticFacts`, `PolicyDecision`, `SalesforcePayload`, and `PipelineResult` in `src/contracts.py`; staged validation in `src/schema_validation.py`, `src/domain_validation.py`, and `src/semantic_validation.py`; and ground-truth/evaluation artifact contracts in `src/evaluation/`.

## 3. Current Semantic Representation

### Provider-facing extraction

**Repository fact.** `ProviderStructuredResponse` in `src/contracts.py` is the provider structured-output authority. `src/semantic_extractor.py` makes exactly one Responses API parse request for a valid analysis and returns a provider-independent dictionary produced by `src/provider_adapter.py`. The provider-facing object does not cross into schema validation. `src/semantic_prompt.py` requests the current global field set and exact narrative excerpts while prohibiting operational recommendations.

### Provider-independent and validated facts

**Repository fact.** `SemanticFacts` in `src/contracts.py` is the current provider-independent semantic record. It has one value per document for `violence_present`, `event_type`, `actor`, `target`, `contact_occurred`, `injury_mentioned`, `current_event`, `intentionality`, `negated`, `correction_present`, `conflicting_information`, `evidence_text`, `confidence`, and `uncertainty_notes`.

`src/schema_validation.py` is the structural authority and constructs `SemanticFacts` only after strict field, type, enum, and range validation. `src/domain_validation.py` is the current deterministic violence-domain consistency authority. It evaluates relationships among the global fields without inference or repair. `src/semantic_validation.py` sequences the stages and exposes `ValidatedSemanticFacts` only when both pass.

### Compatibility representation

**Repository fact.** `src/compatibility_finding.py` exactly copies all validated semantic fields into the transitional `ViolenceFinding` in `src/models.py`. `CompatibilityFindingResult` carries success or construction-failure provenance. `ViolenceFinding` remains the operational representation consumed by comparison and preview; it is not provider-authored.

### Policy and aggregate pipeline

**Repository fact.** `src/policy.py` consumes both `ValidatedSemanticFacts` and the exactly matching `ViolenceFinding`. `PolicyDecision` is authoritative only for the demonstration write disposition. Failure, bounded structured uncertainty, detected, and not-detected precedence is deterministic. Provider confidence and free-form uncertainty notes do not independently determine the outcome.

`src/app_logic.py` orchestrates input validation, normalization, regex, one semantic extraction, validation, compatibility construction, policy, comparison, and preview. `src/contract_adapters.py` constructs `PipelineResult`, whose `semantic_facts`, `operational_finding`, `policy_decision`, `salesforce_payload`, and presentation payload preserve the current boundary separation.

### Downstream representations

**Repository fact.** `src/comparison.py` reads the compatibility finding and produces deterministic regex alignment and semantic-enrichment messages. `src/presentation.py` reads validated facts and policy decisions to produce display-only labels and summaries. `src/salesforce_preview.py` serializes the global compatibility fields and policy outcome into illustrative fields. `app.py` renders these outputs but is not semantic authority.

### Evaluation representations

**Repository fact.** `evaluation/corpus/corpus.json` and `src/evaluation/contracts.py` define current evaluation ground truth as one expected `SemanticFacts`, one optional matching `ViolenceFinding`, and one `PolicyDecision` per case. `src/evaluation/case_comparison.py` compares the same global semantic field paths, excluding provider confidence from semantic equality. `src/evaluation/run_contracts.py`, `baseline.py`, `regression_contracts.py`, `regression.py`, `reporting.py`, and `serialization.py` define observed-run, immutable-baseline, comparison, report, and canonical-serialization boundaries. Historical artifacts are evidence only.

## 4. Demonstrated Representational Limitations

The classifications below distinguish direct corpus demonstrations from structural implications of the current contracts. “Deferred” means current repository evidence does not justify making the concept part of successor design.

| ID | Current field or structure | Repository evidence | Operational distinction not faithfully represented | Affected boundaries | Classification |
|---|---|---|---|---|---|
| L-01 | One document-level `violence_present` | The corpus has 21 compound cases. `EVAL_007` contains a historical punch, a current denial, and a current lunge; `EVAL_011` contains accidental contact and a later intentional threat; `EVAL_025` contains a corrected person-directed punch claim and an object strike. Each ground truth has one boolean (`evaluation/corpus/corpus.json`). | Separate affirmative, negative, historical, corrected, object-directed, and uncertain propositions cannot retain independent violence state. | Provider boundary, semantic facts, validation, compatibility, policy, pipeline, presentation, preview, evaluation | Directly demonstrated |
| L-02 | One document-level `event_type` | Four cases each cover attempted assault and completed assault. Compound `EVAL_011` has accidental completed contact plus a verbal threat; `EVAL_025` has an initial completed-assault assertion superseded by object-directed conduct. | Different conduct propositions cannot retain separate type or completion state; a single enum selects or conflates them. | Same active and evaluation boundaries as L-01 | Directly demonstrated |
| L-03 | One `actor` and one `target`, without proposition identity | `EVAL_017`–`EVAL_020` encode violence toward the patient; `EVAL_037`–`EVAL_040` encode self-directed conduct; `EVAL_033`–`EVAL_036` encode object-directed conduct; `EVAL_029`–`EVAL_032` contain competing accounts. | Actor-action-target direction cannot be attached to each claimed act or account. The record cannot distinguish participants in multiple propositions. | Extraction, semantic facts, compatibility, presentation, preview, corpus truth, comparison | Directly demonstrated |
| L-04 | Global `contact_occurred` | `EVAL_005`–`EVAL_008` distinguish attempt from completion. `EVAL_011` assigns accidental contact to a bump while the selected event type describes a later threat. `EVAL_025`–`EVAL_027` distinguish corrected person contact from object or accidental contact. | Contact cannot be scoped to the conduct, target, or assertion to which it belongs. | Domain validation, policy, comparison, presentation, preview, evaluation | Directly demonstrated |
| L-05 | Global `negated` | `EVAL_007` has a current denial plus a current affirmative attempt and historical violence. `EVAL_022` has a historical assault plus denial of current acts. `EVAL_029` and `EVAL_030` contain one account negating another account's assertion. | Negation cannot identify the proposition it negates; the global value can appear to negate an unrelated affirmative claim. | Domain validation, policy, presentation, evaluation comparison and findings | Directly demonstrated |
| L-06 | Global `correction_present` | `EVAL_020` corrects current timing to childhood. `EVAL_025`–`EVAL_028` correct person-directed assault, contact, or threat claims to different propositions. | The record marks that some correction exists but cannot identify the superseded assertion, the replacing assertion, or the corrected dimension. | Extraction, validation, policy, evaluation ground truth and comparison | Directly demonstrated |
| L-07 | Global `conflicting_information` | `EVAL_029`–`EVAL_032` contain competing accounts about contact, attempt, or intent. Ground truth marks one document-level conflict while retaining one actor/target/event selection. | The conflicting assertions, their sources, and the exact disputed dimensions cannot be represented separately. | Extraction, validation, policy uncertainty, presentation, evaluation | Directly demonstrated |
| L-08 | Global `current_event` | `EVAL_007` and `EVAL_022` contain both historical and current propositions; `EVAL_020` corrects apparent current timing to childhood. | Temporal scope cannot be attached independently to each proposition. A single value necessarily describes a selected interpretation rather than all documented conduct. | Prompt, comparison enrichment, corpus coverage, evaluation findings | Directly demonstrated |
| L-09 | Free-form `uncertainty_notes` | `EVAL_012` is uncertain about speaker, target, and whether words are a threat; `EVAL_031` is uncertain about attempted kicking versus transfer movement; `EVAL_032` is uncertain about intent despite confirmed contact. The corpus stores ordered free-form notes without claim identifiers. | Uncertainty cannot identify its subject, disputed dimension, or supported proposition in a bounded deterministic form. | Policy inspection, presentation, preview, case comparison, reports | Directly demonstrated for scope; final bounded uncertainty vocabulary is not demonstrated and is deferred |
| L-10 | Unscoped `evidence_text` | Every ground-truth record has a global excerpt list. Compound cases contain multiple propositions, but excerpt entries have no assertion link. The operational run recorded evidence differences in 33 cases under creation-time comparison behavior. Current comparison uses exact containment and ordered exact-span segmentation (`src/evaluation/case_comparison.py`). | Evidence cannot be linked to an individual assertion, negation, correction, conflict side, temporal claim, or uncertainty. | Prompt, validation, preview, evaluation comparison, artifact serialization, reports | Directly demonstrated for scope; offset or locator mechanics are not demonstrated and are deferred |
| L-11 | One global `intentionality` | `EVAL_011` combines accidental contact with an intentional threat; `EVAL_032` confirms contact while leaving intent disputed; `EVAL_025` describes intentional object conduct after correction of interpersonal conduct. | Intent cannot be scoped independently to each action or contact. | Domain validation, policy, presentation, preview, evaluation | Directly demonstrated |
| L-12 | Global `injury_mentioned` and provider `confidence` | Current contracts contain one value for each. The corpus demonstrates injury associated with completed assaults (`EVAL_003`, `EVAL_004`) but does not provide a compound case requiring two independently scoped injury findings. Confidence is provider-reported and excluded from case semantic equality. | Proposition-scoped injury and calibrated deterministic confidence are not established by repository evidence. | Current schemas and serialization | Structurally inferred; not demonstrated and therefore deferred as successor requirements |

**Analytical conclusion.** The directly demonstrated limitation is loss of proposition identity and scope across multiple documented claims. This conclusion does not establish that every global field must be replaced, nor does it select a successor representation. It establishes that later design cannot faithfully cover the demonstrated cases by treating additional unscoped fields as independent document attributes.

## 5. Field Conflation Analysis

| Transitional field | Concepts currently compressed or left unscoped | Evidence basis |
|---|---|---|
| `violence_present` | Document disposition, existence of any in-scope interpersonal conduct, selected proposition truth, and handling of historical/corrected/competing claims | `EVAL_007`, `EVAL_011`, `EVAL_017`–`EVAL_020`, `EVAL_025`–`EVAL_032`, `EVAL_033`–`EVAL_040` |
| `event_type` | Conduct kind, attempted/completed state, and a document-level selection among multiple actions | `EVAL_005`–`EVAL_012`, `EVAL_025`–`EVAL_028` |
| `actor` | Actor for the selected document interpretation, without attachment to a particular action, assertion, or account | `EVAL_017`–`EVAL_020`, `EVAL_029`–`EVAL_032`, `EVAL_037`–`EVAL_043` |
| `target` | Person, staff collective, self, null object direction, and unknown participant, without action identity | `EVAL_008`, `EVAL_010`, `EVAL_017`–`EVAL_020`, `EVAL_033`–`EVAL_043` |
| `contact_occurred` | Any physical contact, person-directed contact, accidental contact, object contact excluded from the current boolean, and completed-versus-attempted conduct | `EVAL_005`–`EVAL_008`, `EVAL_011`, `EVAL_013`–`EVAL_016`, `EVAL_025`–`EVAL_027` |
| `current_event` | Timing of a selected violence interpretation despite narratives containing current and historical propositions | `EVAL_007`, `EVAL_017`–`EVAL_022` |
| `negated` | Presence of negation and implied disposition of a selected proposition, without a negation target | `EVAL_007`, `EVAL_021`–`EVAL_024`, `EVAL_029`, `EVAL_030` |
| `correction_present` | Presence of correction, supersession, timing correction, target correction, contact correction, and quoted-language correction | `EVAL_020`, `EVAL_025`–`EVAL_028` |
| `conflicting_information` | Presence of conflict, competing sources, disputed contact, disputed action, and disputed intent | `EVAL_029`–`EVAL_032` |
| `evidence_text` | Exact excerpts supporting any selected fact, without linkage to claim, field, attribution, negation, or correction | All 48 corpus cases; exact comparison in `src/evaluation/case_comparison.py` |
| `uncertainty_notes` | Free-form caveat, ambiguity subject, disputed field, missing information, and extraction commentary | `EVAL_012`, `EVAL_029`–`EVAL_032`, `EVAL_041`–`EVAL_048` |

`intentionality` has the same scope problem: it may describe contact, threatened action, object-directed action, or an unresolved account globally. `injury_mentioned` is global, but the current corpus does not directly demonstrate a need for multiple independently scoped injury assertions. `confidence` is a provider report about its output, not deterministic truth, policy authority, or ground truth.

## 6. Required Violence-Domain Distinctions

### Required for successor design

The following distinctions are directly supported by current violence-detection cases. This list states requirements, not fields or schema shape.

1. **Distinct documented propositions.** Multiple claims in one narrative must remain distinguishable (`EVAL_007`, `EVAL_011`, `EVAL_022`, `EVAL_025`–`EVAL_032`).
2. **Actor-action-target direction per proposition.** Interpersonal direction, self direction, object direction, collective or unknown participants, and reversed actor/target direction must not collapse into one document pair (`EVAL_017`–`EVAL_020`, `EVAL_033`–`EVAL_043`).
3. **Interpersonal, object-directed, and self-directed scope.** The existing corpus explicitly distinguishes these categories. The requirement is to preserve the distinction needed for interpersonal violence detection, not to design broader object- or self-harm taxonomies.
4. **Attempted versus completed conduct.** Attempt and completion, including whether person-directed contact occurred, are separate operational distinctions (`EVAL_001`–`EVAL_008`).
5. **Contact scoped to conduct and target.** Accidental, person-directed, absent, and object-mediated contact must not be assigned to an unrelated proposition (`EVAL_011`, `EVAL_013`–`EVAL_016`, `EVAL_025`–`EVAL_027`).
6. **Current versus historical scope per proposition.** Mixed-time narratives must preserve which conduct is current and which is historical (`EVAL_007`, `EVAL_017`–`EVAL_022`).
7. **Proposition-scoped negation.** A denial must identify the conduct it negates and must not globally negate unrelated historical or current affirmative conduct (`EVAL_007`, `EVAL_022`, `EVAL_029`, `EVAL_030`).
8. **Correction and supersession relationships.** Later corrected content and the earlier assertion must remain distinguishable without treating both as equally current truth (`EVAL_020`, `EVAL_025`–`EVAL_028`).
9. **Conflict between assertions.** Competing accounts and the disputed dimension must remain representable without resolving credibility (`EVAL_029`–`EVAL_032`).
10. **Claim-scoped uncertainty.** The subject of uncertainty—participant, action kind, intent, contact, timing, or threat meaning—must be distinguishable where the corpus demonstrates it (`EVAL_012`, `EVAL_031`, `EVAL_032`, `EVAL_041`–`EVAL_048`).
11. **Claim-scoped evidence support.** Exact narrative support must be connectable to the assertion it supports, negates, corrects, or places in conflict. The narrative remains authority.

### Potentially reusable but bounded to violence

- Stable proposition identity, participant roles, temporal scope, assertion relationship, and evidence linkage are potentially reusable primitives, but this basis justifies them only for the demonstrated violence-detection distinctions above.
- A bounded distinction between stated, denied, corrected/superseded, and disputed claims may be reusable within violence cases. Repository evidence does not justify a general-purpose information-extraction ontology.
- Conduct completion and contact scope may be reusable within person-directed violence analysis. They do not establish a general event model.

### Deferred

- A complete taxonomy of self-harm, property damage, falls, medication events, devices, security investigations, clinical state, legal state, safety actions, workflow queues, or broader hospital incidents.
- Credibility scoring, source ranking, truth adjudication, causal inference, motive, legal intent, clinical intent, or recommended action.
- Provider confidence calibration or use of provider confidence as deterministic truth.
- Proposition-scoped injury modeling, exact character-offset requirements, generalized temporal logic, coreference resolution, and a universal participant ontology. Current contracts make some of these structurally imaginable, but the corpus does not demonstrate them as required successor distinctions.

## 7. Evidence and Provenance Limitations

### Current evidence representation

**Repository fact.** `evidence_text` is an ordered list of strings in `ProviderStructuredResponse`, `SemanticFacts`, `ViolenceFinding`, Salesforce preview, corpus expectations, observed runs, and baselines. `src/semantic_prompt.py` requires exact excerpts. `src/domain_validation.py` rejects empty excerpts but does not verify narrative containment. `src/evaluation/case_comparison.py` performs deterministic evidence comparison against the normalized narrative.

### Evidence comparison behavior

**Repository fact.** Expected evidence is covered when an expected excerpt is contained in one observed excerpt or in an ordered space-joined sequence of observed excerpts. An observed excerpt is unsupported when it is absent from the normalized narrative and is not itself an expected excerpt. Comparison is exact and ordered; it does not use fuzzy or model-assisted matching. Provider confidence is deliberately omitted from `_SEMANTIC_FIELDS` and therefore from semantic equality.

### Scope and provenance

**Analytical conclusion.** Because evidence entries have no proposition or field identity, exact text can be known while its semantic support relationship remains ambiguous in compound cases. Normalization provenance is preserved separately in `NormalizedIncident` as the original narrative, normalized narrative, applied flag, and ordered normalization operations (`src/contracts.py`, `src/narrative_normalizer.py`). The original narrative remains the authoritative raw evidence and display source; normalized text is the deterministic inference and comparison input.

### Authority separation

**Repository fact.** The corpus's manually authored ground truth is authoritative for expected outcomes. Provider output, observed run output, regex output, policy output, compatibility output, and preserved artifacts cannot author or repair it (`README.md`, `evaluation/corpus/README.md`, `src/evaluation/corpus.py`). Preserved operational evidence records what one execution produced; it is not narrative truth. Provider confidence is provider-reported evidence only and is neither policy authority nor semantic ground truth.

## 8. Downstream Dependency Map

| Repository boundary | Files | Current semantic dependency | Authority role | Migration impact | Historical immutability concern |
|---|---|---|---|---|---|
| Provider structured response | `src/contracts.py`, `src/semantic_prompt.py`, `src/semantic_extractor.py` | Full global field vocabulary and bounded enums | Provider boundary | Provider boundary | None for code; exactly-one-request invariant remains authoritative |
| Provider adaptation | `src/provider_adapter.py` | Exact dump/copy of `ProviderStructuredResponse` | Terminates provider-specific object | Provider boundary | None |
| Extraction result | `src/semantic_extractor.py` | Provider-independent candidate with the same fields | Extraction success/failure carrier | Provider boundary | Run artifacts preserve observed extraction status |
| Provider-independent facts | `src/contracts.py` | `SemanticFacts` global record | Current semantic authority after schema construction | Current semantic authority | Serialized historical facts must remain readable and unchanged |
| Schema validation | `src/schema_validation.py` | Exact required field list, types, enums, confidence range | Deterministic structural authority | Deterministic validation | Historical validation results use current serialized paths |
| Domain validation | `src/domain_validation.py` | Cross-field rules for global violence, type, contact, negation, conflict, evidence | Deterministic violence-domain authority | Deterministic validation | Creation-time rejections remain evidence |
| Combined validation | `src/semantic_validation.py`, `src/contracts.py` | `SemanticFacts` to `ValidatedSemanticFacts` gating | Admissibility authority | Deterministic validation | Preserved validation stage values are immutable |
| Compatibility construction | `src/compatibility_finding.py`, `src/models.py` | Exact global-field copy to `ViolenceFinding` | Transitional downstream construction | Downstream representation | Legacy artifacts contain compatibility findings and creation-time classifications |
| Deterministic policy | `src/policy.py`, `src/contracts.py` | Global conflict, type, violence, contact, intent, negation, correction; exact fact/finding equality | Application write-disposition authority | Deterministic policy | Preserved policy outcomes/reasons are immutable observations |
| Aggregate pipeline and adapters | `src/app_logic.py`, `src/contract_adapters.py`, `src/contracts.py` | Validation, facts, finding, decision, preview in `AnalysisResult`/`PipelineResult` | Orchestration and aggregate contract | Current semantic authority / downstream representation | Observed runs serialize `PipelineResult` |
| Regex comparison | `src/comparison.py` | `ViolenceFinding` classification and enrichment fields | Deterministic comparison only | Downstream representation | Preserved comparison messages remain historical evidence |
| Stakeholder presentation | `src/presentation.py`, `app.py` | Event type, actor, target, contact, injury, policy and validation | Display-only mapping | Downstream representation | Historical reports are not presentation authority |
| Salesforce preview | `src/salesforce_preview.py`, `src/contracts.py` | One illustrative field per global semantic value plus policy outcome | Illustrative serializer only | Downstream representation | Preserved run payloads are immutable |
| Fixture regression | `src/fixtures.py`, `tests/test_fixture_policy_regression.py` | Eight approved expected global findings and decisions | Fixture test authority | Test authority | Fixture expectations are separate from evaluation corpus truth |
| Evaluation ground truth | `evaluation/corpus/corpus.json`, `src/evaluation/contracts.py`, `src/evaluation/corpus.py` | One expected global fact/finding/decision set per case | Current evaluation authority | Current evaluation authority | Ground truth cannot be derived from observed artifacts |
| Case comparison | `src/evaluation/case_comparison.py` | Fixed global semantic paths; exact evidence behavior; bounded findings | Deterministic evaluation comparator | Current evaluation authority | Reads creation-time and current values; legacy labels remain readable |
| Run execution and observation | `src/evaluation/runner.py`, `src/evaluation/run_contracts.py` | Complete `PipelineResult`, comparison, failure provenance | Observed evidence producer | Current evaluation authority | Existing run paths protected from overwrite |
| Baseline acceptance/loading | `src/evaluation/baseline.py`, `src/evaluation/regression_contracts.py` | Snapshots ordered observed cases and evaluations | Explicit immutable baseline authority | Legacy artifact reader | Existing baseline immutable; replacement requires new identity |
| Regression comparison | `src/evaluation/regression.py`, `src/evaluation/regression_contracts.py` | Field differences, failure patterns, policy/validation changes | Deterministic comparison authority | Legacy artifact reader / current evaluation authority | Preserved comparison remains byte-immutable |
| Engineering reporting | `src/evaluation/reporting.py`, `src/evaluation/artifact_cli.py` | Regression classifications and semantic field paths | Evidence-only rendering | Legacy artifact reader / documentation | Preserved Markdown must not be regenerated in place |
| Canonical serialization | `src/evaluation/serialization.py` | Strict model dumps and stable JSON | Artifact serialization authority | Legacy artifact reader | Re-serialization would change immutable evidence |
| Tests | `tests/test_models.py`, `tests/test_contracts.py`, `tests/test_semantic_extractor.py`, `tests/test_semantic_validation.py`, `tests/test_semantic_authority_boundary.py`, `tests/test_policy.py`, `tests/test_comparison.py`, `tests/test_presentation.py`, `tests/test_salesforce_preview.py`, `tests/test_app_logic.py`, `tests/test_fixture_policy_regression.py`, `tests/test_streamlit_empty_state.py`, `tests/evaluation/` | Constructors, exact fields, rules, orchestration, serialization, 48-case evaluation behavior | Test authority | Test authority | Tests also protect historical loader behavior and corpus separation |
| Architecture documentation | `README.md`, `docs/architecture.md`, active `docs/SITREC - 2026-07-18 Violence Checker Narrative Source Control Baseline.md`, `docs/generated/repository_knowledge_graph.md` | Current global contracts and authority boundaries | Documentation | Documentation | Active SITREC was inspection-only under this brief |
| Demonstration documentation | `docs/demo_runbook.md` | Policy labels, fixture contrasts, exactly-one-request behavior | Documentation | Documentation | No historical authority |
| Historical documentation | `docs/SITREC - 2026-07-17 Violence Checker Phase 0 Demonstration Baseline.md`, preserved evaluation Markdown | Earlier vocabulary and creation-time observations | Historical documentation only | Legacy artifact reader / documentation | Must remain unchanged and must not become current authority |

## 9. Required Authority Separation

**Repository fact.** Current authority is already divided among provider extraction, deterministic provider adaptation, schema validation, domain validation, compatibility construction, policy, presentation, evaluation ground truth, and observed evaluation evidence.

**Analytical conclusion.** Later successor specification must preserve or strengthen these separations without assigning final successor fields here:

- Provider extraction may propose narrative-grounded semantic content but cannot author policy, workflow, ground truth, deterministic validation, or Salesforce disposition.
- Deterministic derivation may construct bounded relationships only from admissible extracted content and narrative provenance defined by the later specification; it cannot silently infer, repair, or default unsupported facts.
- Schema validation determines structure and vocabulary, not semantic truth.
- Domain validation determines encoded violence-domain consistency, not clinical, legal, safety, or credibility conclusions.
- Policy consumes admissible semantic content under explicit deterministic rules and must remain separate from provider confidence and free-form prose.
- Presentation translates authoritative results without reinterpreting them.
- Repository-authored evaluation ground truth remains independent from all model, provider, app, regex, policy, and observed outputs.
- Observed runs, accepted baselines, comparisons, and reports remain evidence of executions. They cannot become ground truth or current semantic authority merely because they are preserved or accepted.
- Transitional compatibility cannot become a second long-term semantic authority. If retained for a bounded reader or display boundary in later work, its authority and termination point must be explicit.

## 10. Boundedness Assessment

### Justified design scope

Repository evidence justifies design review of proposition identity; actor-action-target direction; interpersonal versus object/self direction; attempted versus completed conduct; scoped contact; current versus historical scope; proposition-scoped negation; correction/supersession; conflict between assertions; and claim-scoped uncertainty and evidence. These distinctions are justified only to represent the demonstrated violence-detection cases.

### Scope not justified by current evidence

The repository does not justify a complete event ontology, generalized temporal reasoning, credibility scoring, clinical or legal classifications, action recommendations, provider-confidence calibration, a universal evidence-location scheme, or detailed taxonomies for self-directed and object-directed conduct. It also does not directly demonstrate that injury must be proposition-scoped.

### Explicitly excluded domains

Falls, medications, devices, security investigations, broader hospital taxonomies, workflow queues, clinical decision support, legal or safety disposition, and real Salesforce integration are outside this basis and OPORD 004 scope as supplied. Self-directed and object-directed narratives appear only to preserve the boundary between them and in-scope interpersonal violence detection; they do not authorize broader domain design.

### Design risks

- Premature ontology expansion would add unsupported concepts, widen validation and evaluation authority, and obscure the narrow violence-detection distinctions actually demonstrated.
- Merely adding more global fields would retain the proposition-scope failure and permit values from different claims to be combined into a semantically invalid document record.
- Preserving `ViolenceFinding` or another compatibility form as an equal semantic authority would create two sources of truth and could allow policy, presentation, preview, and evaluation to diverge.
- Treating free-form notes, provider confidence, or provider-selected document summaries as deterministic truth would violate current authority separation.
- Rewriting legacy artifacts into a successor shape would destroy their creation-time provenance and is not justified.

## 11. Design Inputs for the Successor Specification

The later successor contract specification must resolve the following repository-grounded requirements without assuming an implementation in this document:

1. Preserve multiple violence-relevant propositions from one narrative without collapsing their independent state.
2. Attach actor, action/conduct, target/direction, attempt/completion, contact, intentionality, and temporal scope to the proposition they describe where those distinctions are asserted.
3. Represent interpersonal, object-directed, and self-directed direction sufficiently to prevent out-of-scope conduct from becoming person-directed violence.
4. Represent negation against the proposition it negates.
5. Preserve correction and supersession relationships between earlier and later assertions.
6. Preserve competing assertions and their disputed dimensions without provider credibility adjudication.
7. Attach uncertainty and exact narrative evidence to the claims they qualify or support.
8. Preserve raw-narrative authority and deterministic normalization provenance.
9. Define structural validation, violence-domain validation, and policy as separate authorities over the successor representation.
10. Define a single current semantic authority and bound any legacy-artifact reading so compatibility does not become a second authority.
11. Keep provider confidence non-authoritative and excluded from repository-authored semantic equality unless a later, separately authorized requirement changes that rule.
12. Account for every active dependency and immutable historical reader identified in Section 8 without rewriting preserved evidence.
13. Retain the exactly-one-provider-request invariant and prohibit a second semantic inference pass.
14. Establish evaluation expectations independently from provider or observed output and preserve the current distinction between corpus truth and run evidence.

These are inputs to later specification and boundedness review. They are not an implementation authorization or a final contract.

## 12. Open Repository Questions

The following questions materially affect later successor design but cannot be answered from current repository truth:

1. What minimum bounded representation of assertion attribution is required for the competing witness/staff/patient accounts in `EVAL_029`–`EVAL_032`? The corpus demonstrates competing sources but does not author expected source identities, credibility, or attribution structure.
2. What deterministic evidence locator, if any, is required in addition to exact excerpt text? The repository requires exact excerpts and preserves normalized narrative provenance, but it does not establish offsets, line/segment identifiers, or behavior when normalization changes positions.
3. What is the authoritative semantic treatment of propositions that are relevant only as context—such as historical, object-directed, or self-directed conduct—once they are preserved separately from the in-scope interpersonal classification? Current ground truth establishes document outcomes and boundary distinctions, but it does not define successor proposition inclusion rules.
4. Which uncertainty dimensions require bounded representation beyond those directly demonstrated (participant, action kind, contact, intent, timing, and threat meaning)? Current free-form expectations show the scope problem but do not establish a final uncertainty vocabulary.

These are specification questions, not recommendations. No repository mutation or implementation is authorized by recording them.

## 13. Conclusion

Repository evidence is sufficient to proceed to successor contract specification and boundedness review. The current contracts, all 48 manually authored cases, compound-case distinctions, strict evaluation authorities, and preserved operational evidence establish a factual need for proposition-scoped violence semantics and identify every active and historical boundary affected by that need.

This conclusion does not authorize implementation. The successor specification must remain bounded to the demonstrated violence-detection distinctions, retain authority separation, and preserve historical artifacts unchanged.
