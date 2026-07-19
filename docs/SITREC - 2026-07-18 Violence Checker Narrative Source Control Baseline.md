# SITREC - 2026-07-18 Violence Checker Narrative Source Control Baseline

## A. SYSTEM IDENTITY

Repository: `Violence_Checker`.

System identity: local Phase 0 semantic violence detection pre-PoC.

Implementation layer: Python and Streamlit application for a local stakeholder demonstration using synthetic hospital incident narratives and optional manual demonstration narratives.

The repository demonstrates an illustrative lexical regex baseline, OpenAI Responses API semantic extraction, Pydantic validation, deterministic comparison status and observations, and an illustrative Salesforce write-back preview. It is local demonstration software and is not production software.

This SITREC is a current-state rehydration artifact for 2026-07-18. It does not supersede repository files, tests, source code, local configuration, or deterministic validation output. Historical campaigns shall remain preserved as provenance, while this artifact records current-state primacy for the repository baseline.

## B. CURRENT STATE

Current repository state for 2026-07-18:

- The app entry point is `app.py`.
- The initial page displays a `Narrative source` heading.
- Under `Narrative source`, the app displays: `Select a fixture or enter a manual narrative, then press Run Analysis.`
- The narrative-source radio control contains exactly `Synthetic fixture` and `Manual narrative`.
- The narrative-source radio control does not contain `Select a source`.
- The initial page has a true empty state with no active source workflow, no active fixture, no active manual narrative, no active incident narrative, and no analysis output.
- The app no longer displays the banner text: `Synthetic data only. The regex baseline is illustrative, lexical-only, and not Rochester Regional's actual implementation.`
- Required scope disclosure remains in documentation.
- Analysis occurs only after the explicit `Run Analysis` control.
- One semantic extraction request occurs per analysis action.
- No provider request occurs on module import, initial Streamlit load, source selection, fixture selection, or manual typing.
- Fixture selection alone displays the original selected fixture narrative and does not run analysis.
- Manual typing alone displays the entered non-empty manual narrative and does not run analysis.
- Empty or whitespace-only manual input cannot run analysis.
- Stale results are invalidated when the active source mode or active narrative changes.
- Eight approved synthetic fixtures exist in `src/fixtures.py` and remain unchanged.
- An independent evaluation capability exists in `src/evaluation/`, with canonical artifact boundaries under `evaluation/` and offline tests under `tests/evaluation/`.
- `evaluation/corpus/corpus.json` contains 48 ordered synthetic cases and manually authored deterministic ground truth under corpus identity `violence-checker-synthetic-evaluation-corpus` version `1.0.0`.
- Evaluation ground truth is repository-authored and authoritative; model, provider, regex, app, external-system, and observed output cannot author or repair expectations.
- `src/evaluation/corpus.py` implements deterministic atomic loading, bounded validation, and coverage calculation without provider execution.
- No integrated runner, provider corpus execution, accepted baseline, regression comparison, engineering report generation, or measured semantic performance is implemented.
- `Incident` and the transitional compatibility `ViolenceFinding` contract exist in `src/models.py`.
- OpenAI structured output parses into `ProviderStructuredResponse`; `src/provider_adapter.py` deterministically copies its fields into a provider-independent semantic candidate.
- Successful `SemanticExtractionResult` objects carry a semantic candidate and do not establish deterministic admissibility.
- `src/schema_validation.py` performs strict structural validation and constructs `SemanticFacts` only on schema success.
- `src/domain_validation.py` evaluates repository-grounded violence-domain consistency only after schema success.
- `src/semantic_validation.py` exposes `ValidatedSemanticFacts` only after both stages pass and preserves schema-versus-domain failure provenance.
- `src/compatibility_finding.py` accepts only `ValidatedSemanticFacts` and deterministically constructs the existing `ViolenceFinding` representation for comparison and preview compatibility.
- `src/policy.py` implements application write policy `violence_checker_write_disposition` version `1.0.1` with bounded `WRITE_DETECTED`, `WRITE_UNCERTAIN`, `WRITE_NOT_DETECTED`, and `WRITE_FAILED` outcomes.
- Structured facts determine uncertainty materiality. Free-form uncertainty notes remain visible but do not independently override decisive governing facts; `CASE_001` completed assault is detected for its affirmative validated state.
- `PolicyDecision` is the authoritative application write disposition and does not alter semantic facts, validation, compatibility findings, or comparison results.
- `src/presentation.py` maps every bounded policy outcome, policy reason code, and validation stage to deterministic stakeholder-readable text without altering execution contracts.
- Streamlit presents a primary two-column `Regex Baseline` and `Semantic Analysis` comparison. The semantic column includes deterministic summary text and a collapsed `Technical Details` section containing internal engineering artifacts.
- Semantic instructions in `src/semantic_prompt.py` request fact extraction and prohibit operational recommendations, hospital workflow decisions, Salesforce write decisions, and legal, clinical, or safety recommendations.
- Regex output is deterministic and lexical-only in `src/regex_baseline.py` and remains unchanged for this correction.
- Stakeholder-visible comparison behavior remains intact while consuming the deterministic compatibility finding.
- Salesforce preview requires both the deterministic compatibility finding and `PolicyDecision`, rejects `WRITE_FAILED`, and includes the illustrative write disposition without real connectivity.
- Local configuration is loaded from repository-root `.env` by `src/config.py`; `.env` remains ignored by Git.
- Automated tests exist under `tests/`.
- Executor operation telemetry exists at `telemetry/executor_heartbeat.jsonl`.
- Local deterministic repository governance tooling exists at `tools/repo_governance/`.
- Local governance usage and provenance are documented in `docs/local_governance.md`.
- Generated repository governance artifacts exist at `docs/generated/repository_tree.txt` and `docs/generated/repository_knowledge_graph.md`.
- Explicit internal pipeline boundary contracts exist at `src/contracts.py`.
- Compatibility adapters from existing analysis outputs to contract objects exist at `src/contract_adapters.py`.
- Deterministic incident-envelope validation exists at `src/input_validation.py` and returns typed failures before regex or semantic extraction.
- Deterministic conservative narrative normalization exists at `src/narrative_normalizer.py`; normalized inference text and ordered provenance are retained without mutating raw narrative text.

## C. CORE INVARIANTS

- The original incident narrative remains unchanged as the authoritative raw evidence source and display value.
- Only a separate deterministic normalized narrative copy is supplied to regex and semantic extraction.
- Invalid incident input reaches neither regex nor semantic extraction.
- Fixture metadata is not submitted to semantic extraction.
- Evaluation case metadata, engineering notes, and expected outcomes remain structurally separate from narrative input and must never be submitted to semantic extraction.
- Evaluation contracts make no provider calls, perform no semantic inference, and cannot automatically modify the semantic pipeline.
- Semantic output cannot propagate as an application result without Pydantic validation.
- Provider-specific response and SDK objects do not reach app logic, comparison, or Salesforce preview.
- The provider extracts semantic facts and does not author the authoritative downstream `ViolenceFinding`, policy outcome, Salesforce write outcome, or workflow action.
- Provider success alone is insufficient for propagation; schema and domain validation must both pass.
- Schema failure prevents domain validation and exposes no admissible facts.
- Domain failure exposes no admissible facts.
- Every typed input, provider, schema, domain, or compatibility failure maps to `WRITE_FAILED` and produces no Salesforce preview.
- Policy precedence is failure, uncertainty, detected, then not detected.
- Provider-reported confidence alone does not determine policy outcome.
- Semantic failures cannot silently become default `ViolenceFinding` objects.
- Compatibility-construction failures cannot silently become default `ViolenceFinding` objects.
- Exactly one OpenAI Responses API request is made per explicit analysis action.
- No provider request occurs on module import, initial Streamlit load, source selection, fixture selection, or manual typing.
- Regex behavior remains illustrative, lexical, deterministic, and not Rochester Regional logic.
- Comparison and preview layers make no provider requests.
- Salesforce preview requires a non-failed `PolicyDecision` and successful deterministic compatibility construction.
- Failed semantic extraction results do not produce Salesforce previews.
- `.env` remains untracked and ignored.
- Data in the approved fixture library is synthetic.
- The repository does not assert protected health information handling capability.
- Repository truth supersedes SITREC text.

## D. SYSTEM MODEL

Initial page path:

Streamlit startup -> title and purpose text -> `Narrative source` heading -> supporting instruction -> unselected two-option radio -> no source workflow active -> `Incident Narrative` empty state -> no run button -> no analysis result -> no provider request.

Fixture path:

`Synthetic fixture` radio selection -> fixture selectbox -> approved fixture record from `src/fixtures.py` -> `Incident` object -> original narrative display -> explicit `Run Analysis` -> deterministic input validation -> deterministic normalization -> regex baseline using normalized narrative -> OpenAI structured parse to `ProviderStructuredResponse` using normalized narrative -> deterministic provider-independent candidate -> typed semantic result -> schema validation -> domain validation -> `ValidatedSemanticFacts` -> deterministic compatibility construction to `ViolenceFinding` -> deterministic policy evaluation -> deterministic comparison status with classification divergence and semantic enrichment observations -> policy-gated illustrative Salesforce preview -> stakeholder-readable validation and assessment mapping -> collapsed technical detail rendering.

Manual input path:

`Manual narrative` radio selection -> manual text area -> whitespace-only rejection -> session-local illustrative incident identifier -> `Incident` object -> original narrative display -> explicit `Run Analysis` -> deterministic input validation -> deterministic normalization -> regex baseline using normalized narrative -> OpenAI structured parse to `ProviderStructuredResponse` using normalized narrative -> deterministic provider-independent candidate -> typed semantic result -> schema validation -> domain validation -> `ValidatedSemanticFacts` -> deterministic compatibility construction to `ViolenceFinding` -> deterministic policy evaluation -> deterministic comparison status with classification divergence and semantic enrichment observations -> policy-gated illustrative Salesforce preview -> stakeholder-readable validation and assessment mapping -> collapsed technical detail rendering.

Failure path:

semantic configuration failure, OpenAI request failure, structured response failure, or provider parse validation failure -> typed `SemanticExtractionResult` with no candidate -> deterministic validation not run -> no compatibility construction -> provenance-specific `WRITE_FAILED` -> semantic comparison unavailable status and deterministic failure observation -> no Salesforce preview -> bounded Streamlit error and policy display.

Schema failure path:

provider-independent semantic candidate -> typed schema failure with bounded ordered issues -> domain validation not run -> no `ValidatedSemanticFacts` -> no compatibility finding -> schema-specific `WRITE_FAILED` and comparison-unavailable status -> no Salesforce preview -> bounded Streamlit error and policy display.

Domain failure path:

schema-valid `SemanticFacts` -> typed domain failure with bounded ordered issues -> no `ValidatedSemanticFacts` -> no compatibility finding -> domain-specific `WRITE_FAILED` and comparison-unavailable status -> no Salesforce preview -> bounded Streamlit error and policy display.

Compatibility failure path:

successful `ValidatedSemanticFacts` -> defensive compatibility construction failure -> typed compatibility failure -> compatibility-specific `WRITE_FAILED` -> no default finding -> semantic comparison unavailable status -> no Salesforce preview.

Input failure path:

invalid envelope, identifier, narrative type or content, disallowed Unicode content, or over-limit narrative -> typed `InputValidationResult` with bounded issue code, message, and input-specific `WRITE_FAILED` -> no regex call -> no semantic request -> no analysis result or Salesforce preview -> bounded Streamlit error and policy display.

## E. AUTHORITY MODEL

| Component | Authority Level |
| --- | --- |
| Streamlit interface | `app.py` |
| App presentation support logic | `src/app_logic.py` |
| Approved fixture source text | `src/fixtures.py` |
| Incident schema | `src/models.py` `Incident` |
| Input validation contracts | `src/contracts.py` `InputValidationStatus`, `InputFailureCode`, `InputValidationIssue`, and `InputValidationResult` |
| Input-boundary authority | `src/input_validation.py` |
| Narrative-normalization authority | `src/narrative_normalizer.py` and `src/contracts.py` `NormalizedIncident` |
| Provider parsing schema | `src/contracts.py` `ProviderStructuredResponse` |
| Provider-independent candidate | `src/provider_adapter.py` |
| Provider-independent facts | `src/contracts.py` `SemanticFacts` and `src/schema_validation.py` |
| Schema-validation authority | `src/schema_validation.py` |
| Domain-validation authority | `src/domain_validation.py` |
| Combined validation authority | `src/semantic_validation.py` |
| Admissibility carrier | `src/contracts.py` `ValidatedSemanticFacts` |
| Compatibility finding schema | `src/models.py` `ViolenceFinding` and `src/compatibility_finding.py` |
| Application write policy | `src/policy.py` and `src/contracts.py` policy contracts |
| Semantic prompt | `src/semantic_prompt.py` |
| Semantic extraction behavior | `src/semantic_extractor.py` |
| Regex baseline | `src/regex_baseline.py` |
| Comparison layer | `src/comparison.py` |
| Salesforce preview layer | `src/salesforce_preview.py` |
| Internal contract definitions | `src/contracts.py` |
| Contract compatibility adapters | `src/contract_adapters.py` |
| Environment configuration | `src/config.py`, `.env.example`, ignored local `.env` |
| Automated regression behavior | `tests/` |
| Architecture documentation | `docs/architecture.md` |
| Demonstration runbook | `docs/demo_runbook.md` |
| Local governance documentation | `docs/local_governance.md` |
| Evaluation contract authority | `src/evaluation/contracts.py`, `src/evaluation/serialization.py`, and `src/evaluation/corpus.py` |
| Evaluation ground-truth authority | `evaluation/corpus/corpus.json` version `1.0.0` |
| Generated evaluation observations | Future derived artifacts under `evaluation/runs/`; evidence only, never ground truth |
| Evaluation baseline and report locations | `evaluation/baselines/` and `evaluation/reports/` |
| Repository tree artifact | `docs/generated/repository_tree.txt` |
| Repository knowledge graph artifact | `docs/generated/repository_knowledge_graph.md` |
| SITREC | Current-state rehydration artifact only |
| Deterministic validators | Test suite and local `tools/repo_governance/` validation commands |

## F. DATA / CONTRACT MODEL

- `Incident`: Pydantic model with non-empty `incident_id` and non-empty `narrative`. The narrative is preserved exactly.
- `ViolenceFinding`: transitional downstream Pydantic representation with `violence_present`, `event_type`, `actor`, `target`, `contact_occurred`, `injury_mentioned`, `current_event`, `intentionality`, `negated`, `correction_present`, `conflicting_information`, `evidence_text`, `confidence`, and `uncertainty_notes`.
- `ViolenceEventType`: bounded values `none`, `verbal_threat`, `attempted_physical_violence`, `completed_physical_violence`, and `unclear`.
- `Intentionality`: bounded values `intentional`, `accidental`, and `unclear`.
- `SemanticExtractionResult`: typed provider result with `success`, `configuration_failure`, `openai_request_failure`, `structured_response_failure`, and `pydantic_validation_failure`; success carries a semantic candidate, not admissible facts.
- `InputValidationResult`: typed input-boundary result containing success or failure status, a validated `Incident` only on success, and bounded field-level issues only on failure.
- `InputFailureCode`: bounded values for envelope type, unsupported field, missing/type/empty identifier, missing/type/empty/whitespace/non-substantive narrative, null character, surrogate code point, and narrative size failures.
- Regex result: dictionary containing `detected`, `matched_terms`, and `matched_patterns`.
- `ComparisonResult`: typed comparison container with incident, regex result, semantic result, semantic validation status, classification alignment, material difference flag, display status, deterministic classification divergence observations, deterministic semantic enrichment observations, and aggregate observations.
- Salesforce preview dictionary: illustrative fields derived from a compatibility `ViolenceFinding` and non-failed `PolicyDecision`, including `Illustrative_Write_Disposition__c`.
- `NormalizedIncident`: typed contract preserving the exact original narrative plus a normalized inference narrative, changed flag, and ordered `NormalizationOperation` provenance.
- `RegexResult`: typed adapter contract for the existing regex result dictionary.
- `ProviderStructuredResponse`: provider-facing structured parse schema containing only authorized extracted fact fields.
- `SemanticFacts`: provider-independent typed semantic fact contract produced by deterministic adaptation from `ProviderStructuredResponse`; provider-reported confidence is retained as an extraction attribute and is not deterministic truth.
- `ValidationIssueCode` and `ValidationIssue`: bounded deterministic schema and domain issue representation.
- `SchemaValidationResult`, `DomainValidationResult`, and `ValidationResult`: typed stage results with deterministic ordering and explicit not-run, schema-failure, domain-failure, or successful provenance.
- `ValidatedSemanticFacts`: admissibility carrier exposed only after schema and domain validation pass.
- `CompatibilityFindingResult`: typed deterministic success or defensive failure result for exact `ValidatedSemanticFacts` to `ViolenceFinding` mapping.
- `PolicyOutcome`: bounded `WRITE_DETECTED`, `WRITE_UNCERTAIN`, `WRITE_NOT_DETECTED`, and `WRITE_FAILED` values.
- `PolicyReasonCode`: bounded failure, uncertainty, detected, and not-detected reason values with deterministic ordering.
- `PolicyDecision`: provider-independent application write disposition with stable policy identifier, version, outcome, ordered reasons, deterministic explanation, and optional typed failure provenance.
- `SalesforcePayload`: typed adapter contract for the existing illustrative Salesforce preview dictionary.
- `PipelineResult`: typed aggregate contract representing incident, normalized incident, regex result, semantic facts, validation result, operational finding, policy decision, Salesforce payload, presentation payload, and signature.
- Fixture records: dictionaries containing an `Incident` and qualitative metadata. Metadata is display context only and is not semantic extraction input.
- Narrative source UI state: unselected initial radio state, `Synthetic fixture`, or `Manual narrative`; the UI state is not a third source value.
- `EvaluationCase` and `EvaluationCaseMetadata`: strict synthetic case identity, schema version, narrative, categories, documentation-quality tags, and optional engineering notes, with metadata and ground truth structurally separate from narrative input.
- `ExpectedEvaluationOutcome` and `ObservedEvaluationResult`: independent expected and observed states that reject contradictory success and failure payloads and never infer expectations from observations.
- `FieldDifference` and `CaseEvaluationResult`: ordered deterministic difference and failure-pattern representation with bounded match, partial mismatch, failure, and non-comparable status.
- `BaselineComparison`: prior and current result identities, ordered observations, and bounded improved, degraded, unchanged, or incomparable classification vocabulary.
- `EvaluationArtifactProvenance`: evaluation schema, corpus identity, repository commit, optional model and extraction configuration identity, timestamp, and explicit live or test mode.
- `EvaluationCategory` and `DocumentationQualityTag`: bounded corpus vocabularies for twelve primary semantic categories and eleven documentation-quality conditions.
- `CorpusDocument`, `CorpusValidationIssue`, and `CorpusCoverageSummary`: strict corpus envelope, bounded deterministic validation issues, and ordered machine-readable coverage counts.

## G. SYSTEM BOUNDARIES

- No production deployment.
- No real Salesforce connectivity.
- No Salesforce credentials, real object identifiers, API calls, or authentication.
- No user authentication.
- No database persistence.
- No protected health information handling capability.
- No FoxCommand integration.
- No workflow redesign.
- No human review queue.
- Policy outcomes are application representation only and do not determine hospital, clinical, legal, or safety action.
- No batch processing.
- No analytics dashboard.
- Evaluation includes contracts, canonical serialization, an authoritative synthetic corpus, deterministic loading, validation, coverage, documentation, and offline tests; there is no runner, provider corpus execution, comparison executor, accepted baseline, or report generator.
- No model retry infrastructure.
- No guarantee of clinical, legal, operational, or safety correctness.
- No Rochester Regional implementation claim for the regex baseline.

## H. CURRENT CAPABILITIES

- Streamlit local interface can launch from `app.py`.
- Initial empty state is implemented without a placeholder source option.
- Fixture source selection supports the eight approved synthetic narratives.
- Manual narrative entry is supported for local demonstration.
- Empty or whitespace-only manual input is rejected before analysis.
- Strict incident envelopes are validated deterministically before regex and semantic extraction.
- Narratives must contain a non-whitespace character after one optional leading byte-order mark is disregarded, must exclude null characters and Unicode surrogates, and must not exceed 20,000 Python characters.
- Valid narratives are normalized through a fixed formatting-only operation order before inference while raw narratives remain unchanged.
- Invalid explicit analysis input returns bounded presentation-safe feedback without regex or provider calls.
- Regex baseline can run locally without network access.
- Semantic extraction can run through OpenAI Responses API when local credentials and network availability exist.
- Provider candidates pass independent deterministic schema and domain validation before use.
- Typed semantic failure categories are displayed without stack traces.
- Regex and semantic outputs are displayed side by side after analysis.
- Comparison status and observations are deterministic and require no provider call.
- Deterministic policy `violence_checker_write_disposition` version `1.0.1` represents validated results as detected, uncertain, not detected, or failed.
- Deterministic semantic summaries are created locally from validated structured facts and policy decisions without a second provider request.
- Salesforce preview is deterministic, illustrative, requires `PolicyDecision`, and is never generated for `WRITE_FAILED`.
- Stale analysis results are hidden when active input changes.
- Automated tests validate core behavior.
- Strict evaluation contracts compose existing semantic, compatibility, validation, and policy types without changing them.
- Evaluation artifacts have canonical, authority-separated corpus, generated-run, accepted-baseline, and generated-report locations.
- Canonical evaluation serialization is deterministic and preserves explicit collection ordering.
- The authoritative corpus contains 48 synthetic cases, represents every required category and documentation tag, and includes compound cases.
- Corpus validation rejects malformed documents atomically, duplicate keys and identifiers, unsupported versions, unknown fields, non-synthetic cases, incomplete ground truth, authority mismatches, and non-placeholder generated artifacts.
- Corpus coverage deterministically reports category, documentation tag, success/failure, current/historical, policy-outcome, and compound-case counts without benchmark scoring.

## I. KNOWN LIMITATIONS

- Semantic output remains probabilistic.
- Fixture set is small and synthetic.
- Regex baseline is illustrative and not Rochester Regional's actual implementation.
- No production security controls are implemented.
- No production reliability controls are implemented.
- No persistent audit record exists beyond local executor heartbeat telemetry.
- No real hospital taxonomy integration exists.
- No measured benchmark or accepted regression baseline exists.
- The corpus has not been executed against a provider and establishes no semantic performance measurement.
- No integrated evaluation runner, live batch evaluation, accepted baseline, regression comparison, regression executor, or engineering report generator exists.
- Local API availability and valid credentials are required for semantic analysis.
- Provider or network failures produce typed failures.
- Salesforce preview uses illustrative fields only.
- Local `.venv` and `.env` setup are required for a fresh local live semantic run.

## J. INTERACTION MODEL

- User interacts with Streamlit locally.
- User sees `Narrative source`, the supporting instruction, and exactly two radio options on initial load.
- User selects synthetic fixture input or manual narrative input.
- Streamlit displays the active narrative before analysis only after a fixture is selected or a non-empty manual narrative is entered.
- User presses `Run Analysis`.
- Streamlit calls app logic.
- App logic validates the incident candidate and terminates typed failures before analysis work.
- App logic creates one deterministic normalized inference copy with ordered provenance.
- App logic calls the regex baseline locally with normalized narrative text.
- App logic calls semantic extraction once with normalized narrative text.
- Semantic extractor reads local configuration, constructs an OpenAI client when credentials are present, and calls `responses.parse`.
- Pydantic parses the provider structured response and validates provider-independent semantic facts.
- A deterministic constructor maps facts exactly into the transitional compatibility finding.
- Deterministic policy evaluation applies failure, uncertainty, detected, then not-detected precedence without reading provider confidence; an admissible verbal-threat event without an affirmative violence indication is represented explicitly as uncertain.
- App logic builds deterministic comparison observations.
- App logic builds an illustrative Salesforce preview only after compatibility construction and a non-failed policy decision.
- Streamlit renders results or typed failure information.
- Presentation maps internal outcomes to `Violence Detected`, `Uncertain`, `No Violence Detected`, or `Unable to Determine`, displays deterministic explanations and human-readable reasons first, and retains internal artifacts under `Technical Details`.

## K. GUARANTEES

- Repository tests enforce the current deterministic behavior within their encoded scope.
- `Incident` rejects empty `incident_id` and empty `narrative`.
- Input validation returns deterministic typed failures for expected invalid envelopes and prevents those failures from reaching regex or semantic extraction.
- The minimum-information rule is independent of violence terminology or semantic interpretation, and the local demonstration maximum is exactly 20,000 Python characters.
- Raw accepted narrative text remains unchanged in the application result, active signature, and original narrative display.
- Normalization is deterministic and formatting-only; approved fixture narratives are normalization no-ops.
- Schema validation enforces candidate type, complete strict field shape, forbidden extras, bounded event type and intentionality, strict booleans and strings, collection shapes, and confidence range without domain judgments.
- Domain validation enforces repository-grounded violence, event-type, contact, intentionality, negation, conflict, and evidence consistency without inference or repair.
- Compatibility construction accepts only `ValidatedSemanticFacts` and adds no policy threshold.
- Policy accepts only typed validated inputs or explicit typed failure provenance and makes no provider call or semantic inference.
- Presentation mappings consume authoritative validation and policy contracts without changing their fields, values, precedence, or outcomes.
- Stakeholder-facing explanations are deterministic local mappings and make no provider request.
- Every typed input, provider, schema, domain, or compatibility failure produces `WRITE_FAILED` and no Salesforce preview.
- Comparison cannot determine or override policy outcome.
- Malformed semantic results return typed failure instead of default findings.
- The app import path does not make a provider request.
- Initial Streamlit state has no active incident or analysis output.
- Initial Streamlit state does not activate a fixture workflow or manual workflow.
- Fixture selection alone does not display analysis output.
- Manual typing alone does not display analysis output.
- One analysis action invokes one semantic extractor call in test-covered app logic.
- Stale-result invalidation clears stale stored results when source mode or active narrative changes.
- Fixture narratives remain exact in the fixture tests.
- Salesforce preview rejects objects that are not validated compatibility `ViolenceFinding` and `PolicyDecision` instances and rejects `WRITE_FAILED`.

## L. NON-GUARANTEES

- The system does not guarantee clinical correctness.
- The system does not guarantee legal correctness.
- The system does not guarantee production readiness.
- The system does not guarantee model determinism.
- The system does not guarantee provider availability.
- The system does not guarantee that confidence values are stable.
- The system does not guarantee Salesforce compatibility.
- The system does not guarantee data retention, auditability, authentication, authorization, backup, recovery, monitoring, or deployment behavior.
- The SITREC does not guarantee truth when repository files differ from this text.

## M. GROUNDING ANCHORS

`README.md`
<Identifies the project as a local Python and Streamlit pre-PoC, documents local setup, explicit Run Analysis flow, semantic extraction, comparison, and illustrative Salesforce preview.>

`app.py`
<Defines the Streamlit empty state, two-option narrative source selection, supporting instruction, original narrative display, explicit Run Analysis control, two-column regex and semantic result presentation, deterministic stakeholder summary, semantic-column technical details, and stale-result hiding.>

`src/presentation.py`
<Maps every bounded policy outcome, policy reason code, and validation stage into deterministic stakeholder-readable labels and creates concise summaries from validated facts without an additional provider request.>

`src/app_logic.py`
<Validates and normalizes explicit analysis input, preserves raw active signatures, maps typed failures to policy, evaluates admissible findings, gates preview generation by policy, and supports stale-result invalidation.>

`src/input_validation.py`
<Owns strict deterministic incident-envelope validation, the 20,000-character local limit, conservative minimum-information rule, Unicode exclusions, and typed failure production before analysis work.>

`src/narrative_normalizer.py`
<Creates a deterministic normalized inference copy through bounded formatting-only operations while preserving exact raw narrative text and ordered provenance.>

`tests/test_streamlit_empty_state.py`
<Covers the two-option narrative source radio, removed placeholder option, supporting instruction, removed banner text, initial empty state, source-selection no-call behavior, selection-only no-analysis behavior, stakeholder-facing failed-assessment rendering, and stale-result clearing on source change.>

`tests/test_presentation.py`
<Covers complete deterministic outcome, reason, explanation, and validation-stage mappings while confirming presentation does not mutate authoritative policy contracts.>

`tests/test_app_logic.py`
<Covers app import behavior, manual input validation, metadata exclusion, stale-result helpers, and one semantic extraction call per analysis action.>

`src/fixtures.py`
<Defines exactly eight approved synthetic fixture records with stable identifiers and qualitative metadata.>

`src/semantic_extractor.py`
<Calls OpenAI Responses API structured parsing with `ProviderStructuredResponse`, adapts parsed output into a provider-independent semantic candidate, and returns typed provider success or bounded provider failure without deciding deterministic admissibility.>

`src/provider_adapter.py`
<Terminates the provider-facing schema through deterministic field copying to a provider-independent candidate mapping.>

`src/schema_validation.py`
<Owns structural candidate validation, strict `SemanticFacts` construction, bounded schema issues, and deterministic issue ordering without domain judgments.>

`src/domain_validation.py`
<Owns repository-grounded violence-domain consistency rules for schema-valid facts without inference, repair, defaults, provider calls, or policy outcomes.>

`src/semantic_validation.py`
<Runs schema before domain validation, short-circuits domain execution after schema failure, and exposes `ValidatedSemanticFacts` only after both stages pass.>

`src/compatibility_finding.py`
<Accepts only `ValidatedSemanticFacts` and maps its facts exactly into the transitional `ViolenceFinding` representation with typed defensive failure and no provider calls, semantic inference, defaults, policy, or workflow action.>

`src/policy.py`
<Implements provider-independent application write policy `violence_checker_write_disposition` version `1.0.1`, structured-fact uncertainty materiality, bounded outcomes and reasons, explicit precedence, and typed failure mapping without inference or operational action.>

`src/comparison.py`
<Builds deterministic comparison status, classification divergence observations, and semantic enrichment observations from regex output and the compatibility finding without provider calls.>

`src/salesforce_preview.py`
<Requires compatibility `ViolenceFinding` and `PolicyDecision`, rejects `WRITE_FAILED`, copies the authoritative disposition, and performs no independent policy evaluation or external API call.>

`src/contracts.py`
<Defines explicit internal contracts for normalized incidents, regex results, provider boundary responses, semantic facts, validation results, bounded policy outcomes and reasons, policy decisions, Salesforce payloads, and aggregate pipeline results while reusing existing `Incident` and `ViolenceFinding` contracts.>

`src/evaluation/contracts.py`
<Defines strict provider-independent evaluation case, expectation, observation, difference, case result, baseline comparison, and provenance contracts by composing authoritative repository semantic types.>

`src/evaluation/serialization.py`
<Defines canonical deterministic JSON serialization for typed evaluation artifacts.>

`src/evaluation/corpus.py`
<Loads only the canonical corpus, rejects invalid data atomically with bounded issues, validates required coverage and ground-truth consistency, and calculates deterministic coverage without provider execution.>

`evaluation/corpus/corpus.json`
<Stores the ordered 48-case synthetic corpus and manually authored authoritative ground truth separately from generated observations.>

`evaluation/`
<Separates authoritative corpus truth from placeholder-only generated observed runs, accepted baselines, and generated engineering report locations.>

`tests/evaluation/test_contracts.py`
<Covers evaluation construction, deterministic serialization, malformed and contradictory state rejection, ordered collections, provider-call suppression, and compatibility with authoritative semantic, compatibility, validation, and policy contracts.>

`tests/evaluation/test_corpus.py`
<Covers corpus loading, versions, bounded coverage, ordering, uniqueness, malformed-record rejection, ground-truth completeness, provider-call suppression, placeholder-only generated locations, and byte-for-byte fixture preservation.>

`src/contract_adapters.py`
<Provides compatibility adapters from existing `AnalysisResult`, regex dictionaries, semantic results, and Salesforce preview dictionaries into the explicit contract model without changing operational pipeline behavior.>

`tests/test_contracts.py`
<Covers contract construction, serialization, legacy dictionary compatibility, provider response boundary adaptation, validation adapter behavior, and aggregate pipeline adapter behavior.>

`tests/test_input_boundary.py`
<Covers strict input validation, bounded failure codes, size limits, call suppression, formatting-only normalization, provenance order, idempotence, raw preservation, fixture no-ops, normalized inference integration, and unchanged semantic failure and preview gating behavior.>

`tests/test_semantic_authority_boundary.py`
<Covers provider-to-facts isolation, bounded semantic fields, absence of operational fields, semantic result consistency, deterministic compatibility mapping, no provider call, rejection without defaults, and semantic-only prompt constraints.>

`tests/test_semantic_validation.py`
<Covers schema structure, bounded issues, provider and operational-field rejection, domain invariants, deterministic issue ordering, stage short-circuiting, admissibility, compatibility gating, and integration failure propagation.>

`tests/test_policy.py`
<Covers policy contract serialization, bounded outcomes and reasons, stable identity and version, all failure mappings, incidental-note materiality correction, exhaustive admissible-state partitions, validation-rejected states, compatibility equality, terminal guards, negation, correction, conflict, uncertainty, detected and not-detected rules, precedence, confidence independence, preview gating, provider independence, and active-flow integration.>

`tests/test_fixture_policy_regression.py`
<Covers all eight approved fixtures through deterministic semantic doubles, including detected `CASE_001`, validation, policy reasons, preview gating, raw narrative input, and zero live provider requests.>

`telemetry/executor_heartbeat.jsonl`
<Stores local executor operation telemetry as JSONL.>

`tools/repo_governance/`
<Contains local deterministic governance tooling for repository tree generation, repository knowledge graph generation, SITREC structural validation, and heartbeat JSONL validation without executing foxcommand-runtime tooling.>

`docs/local_governance.md`
<Documents copied governance tooling provenance, authorized local commands, generated artifact paths, limitations, and the prohibition on routine foxcommand-runtime execution for Violence Checker governance operations.>

`docs/generated/repository_tree.txt`
<Generated deterministic repository tree excluding local configuration, caches, transient environments, and Git internals.>

`docs/generated/repository_knowledge_graph.md`
<Generated deterministic repository knowledge graph derived from repository files, imports, tests, documentation, entry points, contracts, and unresolved relationships.>

`docs/SITREC - 2026-07-17 Violence Checker Phase 0 Demonstration Baseline.md`
<Preserved prior-date active SITREC provenance and was not modified by the 2026-07-18 correction.>

## N. SOURCE OF TRUTH RULE

If the SITREC and repository conflict, the repository wins. The SITREC must be updated immediately. The SITREC never supersedes repository truth.

## O. REHYDRATION INSTRUCTIONS

1. Begin with repository inspection.
2. Confirm Git status before changes.
3. Read `README.md`, `docs/architecture.md`, `docs/demo_runbook.md`, `docs/local_governance.md`, `app.py`, `src/`, `tests/`, `tools/repo_governance/`, and `telemetry/executor_heartbeat.jsonl`.
4. Run deterministic validation before relying on behavior.
5. Preserve OPORD-completed boundaries and do not assume production readiness.
6. Use the minimum context required.
7. If repository truth changes on 2026-07-18, update this same-date SITREC.
8. On a later date, create a new dated SITREC rather than duplicating this date.
9. Planner defines operational meaning and continuation boundaries.
10. Executor maintains artifacts, runs validators, and performs deterministic repair loops without redefining meaning.

## P. SITREC LIFECYCLE

This active SITREC represents current repository truth for 2026-07-18. It is not an execution diary and must not be treated as historical narrative. It may be updated if repository truth changes on the same date. Historical provenance remains supporting context only and must not redefine the current system identity.

## Q. DAILY UNIQUENESS

Exactly one active SITREC shall exist for 2026-07-18. If another 2026-07-18 SITREC appears, consolidation is required. The active canonical location is the top-level `docs/` directory, with archived historical SITRECs reserved for `docs/archive/sitrecs/` if needed by later lifecycle operations.

## R. VALIDATION

Validation is deterministic support, not source of truth. Required validation for this SITREC includes:

- active SITREC routing check
- same-date uniqueness check
- required section check
- grounding anchor check
- source-of-truth rule check
- continuation safety check
- target repository test suite
- local governance validation with `python3 -m tools.repo_governance validate-all`
- heartbeat JSONL validation
- target and reference repository Git status checks

## S. PLANNER / EXECUTOR RESPONSIBILITY MODEL

| Role | Responsibility |
| --- | --- |
| Planner | Defines operational meaning, invariants, system boundaries, and interpretation of repository truth. |
| Executor | Performs repository inspection, deterministic validation, authorized file mutations, deterministic repair, and telemetry append. |
| Deterministic validators | Identify structural, uniqueness, grounding, and continuation-safety findings without superseding repository truth. |
