# Violence Checker Architecture

## Purpose And Scope

Violence Checker is a local Phase 0 Semantic Violence Detection Pre-PoC. It demonstrates how a synthetic incident narrative can move through lexical detection, semantic fact extraction, deterministic compatibility construction, comparison, and an illustrative write-back preview.

The repository is not a production system. It does not implement real Salesforce connectivity, persistence, authentication, deployment, workflow routing, analytics, a completed evaluation corpus or runner, CI/CD, containerization, FoxCommand integration, or background processing.

## Incident Input Model

`src/models.py` defines the `Incident` input model. Each incident has:

- `incident_id`
- `narrative`

Both fields must be non-empty strings. The narrative is preserved exactly as supplied.

## Deterministic Input Boundary

`src/input_validation.py` is the sole input-boundary authority for an explicit analysis run. It accepts an existing `Incident` or a strict dictionary envelope containing only `incident_id` and `narrative`, then returns a typed `InputValidationResult`. Expected invalid input produces bounded `InputFailureCode` values and user-safe issue messages; it does not raise an application exception or reach regex or semantic extraction.

The boundary verifies required fields, strict string types, non-empty and non-whitespace identifiers, narrative presence and type, null-character exclusion, Unicode-surrogate exclusion, and a local demonstration maximum of 20,000 Python characters. Its conservative minimum-information rule requires at least one non-whitespace character after disregarding one optional leading byte-order mark. This rule does not assess violence relevance, clinical sufficiency, semantic quality, or operational usefulness.

Input validation does not validate provider output, interpret narrative meaning, evaluate policy, construct findings, or make network requests.

## Deterministic Narrative Normalization

`src/narrative_normalizer.py` owns normalization of a successfully validated incident. It creates a `NormalizedIncident` with the identifier, exact raw narrative, normalized inference narrative, a changed flag, and ordered provenance for each transformation that changed the inference copy.

The fixed operation order is: remove one leading Unicode byte-order mark, Unicode NFC normalization, convert CRLF and CR line endings to LF, replace non-breaking spaces with ordinary spaces, collapse runs of spaces and tabs, reduce runs of more than one blank line to one blank line, and trim leading or trailing spaces, tabs, and line feeds from the inference copy. No operation is recorded when no transformation changes the copy. Repeated normalization of the same validated incident is deterministic and idempotent.

Normalization does not summarize, paraphrase, translate, classify, infer, redact, reorder sentences, lowercase, remove punctuation, remove repeated words, correct spelling, expand abbreviations, map synonyms, replace profanity, alter quoted speech, remove negation or temporal language, or alter numbers and incident terminology.

## Synthetic Fixture Library

`src/fixtures.py` contains the eight approved synthetic narratives, `CASE_001` through `CASE_008`. Fixture metadata is qualitative demonstration context only and is not submitted to semantic extraction.

## Lexical Detection

`src/regex_baseline.py` implements the illustrative regex baseline. It is deterministic, case-insensitive, lexical-only, and reusable outside Streamlit. It returns:

- `detected`
- `matched_terms`
- `matched_patterns`

This baseline intentionally does not resolve negation, corrections, historical context, accidental contact, or conflicting information.

## Semantic Extraction

### Semantic Authority Inventory Before This Boundary Refactor

Before the current boundary, the provider parsed all violence, event type, actor, target, contact, injury, current-event, intentionality, negation, correction, conflict, evidence, confidence, and uncertainty fields directly into `ViolenceFinding`. The prompt asked for a final structured finding and embedded interpretation for corrections, object contact, accidental contact, threats, and event-type selection. `SemanticExtractionResult.finding`, comparison, Salesforce preview, Streamlit presentation, and the pipeline adapter all treated that provider-created `ViolenceFinding` as the final application finding. `ViolenceFinding` Pydantic validators enforced violence/event-type consistency, no-violence/contact/intentionality consistency, and no-contact for event type `none`. The OpenAI SDK response itself was read only for `output_parsed`, but the previous `ProviderStructuredResponse` contract was a generic wrapper rather than the provider parsing schema.

The current boundary retains the same semantic fields because existing comparison, display, and preview behavior consumes them. Provider-reported confidence is retained to preserve those outputs, but it remains an extraction attribute and is not used to create new policy behavior.

`src/semantic_extractor.py` sends the normalized inference narrative supplied by app orchestration to the OpenAI Responses API. It makes one provider request per extraction call and requests structured output using the provider-facing `ProviderStructuredResponse` schema. The SDK response object terminates inside the extractor. `src/provider_adapter.py` copies only the parsed fact fields into a provider-independent mapping candidate. Provider success reports extraction success and a candidate; it does not establish deterministic admissibility.

`src/semantic_prompt.py` centralizes the prompt. The prompt instructs the model to extract facts only from the supplied narrative, preserve current versus historical distinctions, identify negation, corrections, and conflicting statements, distinguish threats, attempts, completed violence, no violence, and unclear events, distinguish person-directed violence from object-directed contact, represent accidental contact without intentional violence, preserve exact evidence excerpts, and represent uncertainty. It explicitly prohibits operational recommendations, hospital workflow decisions, Salesforce write decisions, and legal, clinical, or safety recommendations.

## Validation Boundary

### Existing Validation Responsibility Inventory

Before independent validation was active, `ProviderStructuredResponse` performed strict provider parse validation, `SemanticFacts` performed strict provider-independent contract construction, and `ViolenceFinding` combined compatibility construction with four domain relationships: violence could not use event type `none`; attempted or completed physical violence required violence presence; non-violent non-accidental contact was rejected; and event type `none` could not claim contact. App orchestration defensively required extraction success, comparison treated absent compatibility output as semantic failure, and preview required a `ViolenceFinding`. The previous `SchemaValidationResult`, `DomainValidationResult`, and `ValidationResult` were adapter placeholders: schema status mirrored provider success and domain validation was always not run.

Responsibility classification:

- Provider parse and strict field shape are schema responsibilities.
- Required fields, forbidden extras, types, bounded enums, collection shapes, and confidence range are schema responsibilities.
- Relationships among violence presence, event type, contact, intentionality, negation, conflict, and non-empty evidence entries are domain responsibilities.
- Exact `ValidatedSemanticFacts` to `ViolenceFinding` mapping is compatibility-only.
- Comparison labels, bounded failure observations, Streamlit messages, and preview formatting are presentation-only.
- Injury mention, actor, target, correction, and current-event fields have no additional repository-grounded cross-field rule beyond the encoded invariants; they are preserved without inference.

### Schema Validation Authority

`src/schema_validation.py` accepts only an existing `SemanticFacts` object or a supported deterministic mapping. It rejects provider objects, SDK-like objects, missing fields, unsupported fields, invalid strict types, invalid enum membership, invalid evidence or uncertainty collection shapes, and confidence values outside the existing zero-through-one range. It constructs `SemanticFacts` only after these structural checks pass. Schema validation does not evaluate relationships between fields.

`SchemaValidationStatus`, `ValidationIssueCode`, `ValidationIssue`, and `SchemaValidationResult` provide bounded, stable results. Missing fields follow contract field order; unsupported fields are sorted; Pydantic structural errors preserve deterministic contract order.

### Domain Validation Authority

`src/domain_validation.py` accepts only schema-valid `SemanticFacts`. It evaluates deterministic consistency without calling a provider, interpreting narrative text, repairing evidence, supplying defaults, or deriving policy. It enforces:

- violence presence cannot use event type `none`;
- attempted or completed physical violence requires violence presence;
- completed physical violence requires contact;
- event type `none` cannot coexist with contact;
- non-violent contact must use the already documented accidental-contact representation;
- negated current violence cannot remain an unqualified affirmative finding unless correction or conflict is explicitly represented;
- conflicting information requires event type `unclear` or explicit uncertainty notes;
- every supplied evidence entry must contain non-whitespace text.

Injury mention does not independently force violence presence. Correction, historical/current status, actor, and target remain preserved facts; no unsupported relationship is inferred for them.

### Combined Admissibility Boundary

`src/semantic_validation.py` always runs schema validation before domain validation. Domain validation is not called after schema failure. `ValidationResult.failure_stage` distinguishes not run, schema failure, domain failure, and success. `ValidatedSemanticFacts` is exposed only when both stages pass. Expected invalid candidates return bounded issues and no admissible facts; repeated execution preserves issue ordering.

`ProviderStructuredResponse` remains the Pydantic parsing boundary for OpenAI structured output. Expected extractor outcomes remain represented separately by `SemanticExtractionResult`:

- `success`
- `configuration_failure`
- `openai_request_failure`
- `structured_response_failure`
- `pydantic_validation_failure`

Missing or malformed provider output does not produce a semantic candidate. Provider failure leaves deterministic validation not run. Provider extraction success alone cannot reach compatibility construction, comparison enrichment, preview, or semantic-fact presentation.

`src/compatibility_finding.py` accepts only `ValidatedSemanticFacts` and maps its facts field-for-field into the existing `ViolenceFinding` contract. It performs no schema validation, domain inference, repair, defaults, or provider call. Passing raw or unvalidated facts is rejected defensively. The compatibility object is a transitional representation for current comparison and preview consumers, not policy evaluation.

Within the compatibility `ViolenceFinding`, `contact_occurred` means person-directed physical contact relevant to the represented facts. It does not mean any contact with any object mentioned in the narrative.

## Contract Model

`src/contracts.py` defines explicit typed contracts for major pipeline boundaries while preserving existing runtime interfaces. Existing operational modules may continue returning their current dataclasses and dictionaries; `src/contract_adapters.py` converts those outputs into the contract model for deterministic validation and later migration work.

| Contract | Owner | Producer | Consumer |
| --- | --- | --- | --- |
| `Incident` | `src/models.py` | fixtures, manual input helpers, strict input-envelope adapter | input validator; raw evidence, comparison, signature, display, preview identifier |
| `InputValidationResult` | `src/contracts.py` | `src/input_validation.py` | app orchestration and bounded invalid-input presentation |
| `NormalizedIncident` | `src/contracts.py` | `src/narrative_normalizer.py` | regex baseline, semantic inference adapter, pipeline contract adapter |
| `RegexResult` | `src/contracts.py` | adapter from `src/regex_baseline.py` dictionary output | contract tests and later typed pipeline migration |
| `ProviderStructuredResponse` | `src/contracts.py` | OpenAI Responses API structured parse | `src/provider_adapter.py` only; provider schema terminates at extraction |
| semantic candidate mapping | `src/provider_adapter.py` | deterministic provider adapter | schema validator only |
| `SemanticFacts` | `src/contracts.py` | schema validator | domain validator and schema-stage result |
| `SchemaValidationResult` | `src/contracts.py` | `src/schema_validation.py` | combined validation orchestrator |
| `DomainValidationResult` | `src/contracts.py` | `src/domain_validation.py` | combined validation orchestrator |
| `ValidatedSemanticFacts` | `src/contracts.py` | combined validation orchestrator after both stages pass | compatibility constructor |
| `ValidationResult` | `src/contracts.py` | `src/semantic_validation.py` | app orchestration, comparison, presentation, and pipeline adapter |
| `ViolenceFinding` | `src/models.py` | deterministic compatibility constructor | comparison and preview generation as a transitional representation |
| `PolicyDecision` | `src/contracts.py` | `src/policy.py` | app orchestration, Salesforce preview, presentation, and pipeline adapter |
| `SalesforcePayload` | `src/contracts.py` | adapter from illustrative preview dictionary | contract tests and later typed presentation migration |
| `PipelineResult` | `src/contracts.py` | `pipeline_result_from_analysis` adapter | deterministic contract validation and later migration work |

Current provider-isolation and application flow:

Incident candidate -> deterministic input validation -> deterministic normalization -> existing regex baseline -> OpenAI structured parse to `ProviderStructuredResponse` -> deterministic provider-independent candidate -> typed `SemanticExtractionResult` -> schema validation -> domain validation -> `ValidatedSemanticFacts` -> deterministic compatibility constructor to `ViolenceFinding` -> deterministic policy evaluation -> existing comparison -> policy-gated Salesforce preview -> presentation.

Invalid input terminates before regex and semantic extraction. Valid input is normalized once and causes exactly one semantic extraction call per explicit `Run Analysis` action. Import, initial load, source selection, fixture selection, and manual typing do not call the provider.

Authority separation:

- Evidence is the original incident narrative and semantic evidence excerpts.
- The raw accepted narrative remains unchanged in `AnalysisResult.incident`, the active signature, and the original narrative display. The extractor receives a separate `Incident` containing only the same identifier and normalized inference narrative; fixture metadata remains excluded.
- Semantic evidence text is not rewritten or repaired after extraction. Conservative whitespace or NFC changes can prevent direct string matching against the raw narrative, so the application makes no raw-span offset claim and performs no fuzzy alignment.
- Semantic facts represent extracted fact fields without provider response metadata, policy outcomes, Salesforce outcomes, workflow actions, or display status.
- Only `ValidationResult.validated_facts` is admissible for compatibility construction and presentation.
- `ViolenceFinding` remains only the downstream compatibility representation and is not authored authoritatively by the provider.
- `PolicyDecision` is the authoritative application write disposition; it does not alter semantic or validation facts.
- Presentation payloads are represented by Salesforce and pipeline payload contracts.

Provider-specific OpenAI response objects do not propagate into app logic, comparison, or preview. Only copied parsed fields reach schema validation, and validated `SemanticFacts` exposes no OpenAI response identifiers or SDK objects. No retries, secondary model calls, voting, or review calls are present.

## Deterministic Application Write Policy

### Implicit Policy Inventory Before Activation

Before `src/policy.py` was active, detected and not-detected states were read from `ViolenceFinding.violence_present` by comparison and preview formatting. Uncertainty was presented through comparison enrichment for unclear event type, conflict, uncertainty notes, and confidence below one, but did not have a write disposition. Provider, schema, domain, and compatibility failures blocked preview creation through app gating. Successful compatibility construction automatically allowed a preview, so preview presence acted as the implicit write disposition. Comparison status did not gate preview and therefore remained comparison-only rather than policy. No confidence threshold determined preview eligibility or classification.

Responsibility classification:

- Violence presence, event type, intentionality, conflict, negation, and uncertainty notes are semantic facts.
- Their admissibility relationships remain domain invariants.
- `ViolenceFinding` construction remains compatibility-only.
- Regex alignment and enrichment observations remain comparison-only.
- Dictionary construction and field mapping remain preview-only.
- Streamlit labels and messages remain presentation-only.
- Automatic preview creation after compatibility success was implicit policy and is replaced by `PolicyDecision`.

### Policy Contract And Authority

`src/policy.py` implements policy `violence_checker_write_disposition` version `1.0.1`. It accepts only `ValidatedSemanticFacts`, the exactly matching compatibility `ViolenceFinding`, or explicit typed pipeline failure provenance. It returns provider-independent `PolicyDecision` with a bounded `PolicyOutcome`, ordered bounded `PolicyReasonCode` values, policy identifier, version, deterministic explanation, and optional failure provenance.

The four outcomes are:

- `WRITE_FAILED`: an explicit input, provider, schema, domain, compatibility, or unsupported-input failure prevents an admissible representation.
- `WRITE_UNCERTAIN`: admissible structured facts contain conflict, a verbal-threat event without an affirmative violence indication, unclear event type, materially unclear intentionality, or a negated affirmative finding.
- `WRITE_DETECTED`: admissible non-negated facts affirm violence or a verbal threat, attempted physical violence, or completed physical violence.
- `WRITE_NOT_DETECTED`: admissible facts represent violence absent with event type `none` and no unresolved conflict; negated and corrected non-events receive additional bounded reasons.

Precedence is fixed: `WRITE_FAILED`, then `WRITE_UNCERTAIN`, then `WRITE_DETECTED`, then `WRITE_NOT_DETECTED`. Failure reason codes preserve input-validation, provider-configuration, provider-request, provider-structured-response, provider-validation, schema-validation, domain-validation, and compatibility-construction provenance. Unsupported combinations fail explicitly and never default to not detected. Provider-reported confidence is not read by the policy evaluator.

Free-form uncertainty notes are preserved in validated facts, comparison observations, technical presentation, and the illustrative preview, but their presence alone is not policy authority. The evaluator performs no text interpretation over notes. Materiality comes only from the bounded structured conditions above. A completed physical violence state with affirmative violence, contact, current-event status, intentionality, no negation, and no conflicting information therefore remains detected even when incidental terminology or abbreviation caveats are present.

The `UNSUPPORTED_POLICY_INPUT` terminal guard is reserved for missing or incorrectly typed policy inputs, a mismatch between validated facts and the compatibility finding, programmer error, or future contract evolution not yet supported by this policy version. Exhaustive canonical enumeration confirms that no currently domain-admissible fact state reaches this guard.

The policy performs no semantic inference, validation, repair, provider call, SDK inspection, persistence, remote loading, simulation, replay, real Salesforce operation, human review routing, hospital workflow decision, or clinical, legal, or safety disposition. Its authority is limited to representation inside this demonstration.

## Deterministic Comparison

`src/comparison.py` builds `ComparisonResult` from an incident, a regex result, deterministic `ValidationResult`, and the compatibility finding. Provider failures retain provider status; schema and domain failures expose distinct validation status and bounded unavailable observations while retaining the existing `semantic_failure` classification and stakeholder-facing unavailable display. Comparison neither receives nor overrides `PolicyDecision`, does not determine preview eligibility, makes no provider calls, and does not use model-generated comparison prose.

The comparison result explicitly separates classification divergence from semantic enrichment. Classification alignment records whether regex and semantic extraction are both positive, both negative, regex-positive/semantic-negative, regex-negative/semantic-positive, or unavailable because semantic extraction failed. Semantic enrichment records material distinctions represented by validated semantic output but not by the lexical regex boolean, including historical context, threats, attempts, completed violence, accidental contact, no person-directed contact, negation, corrections, conflicting statements, injury mentions, actor or target information, supporting evidence, and confidence or uncertainty notes.

`material_difference_detected` is true when classification diverges or semantic enrichment exists. A true no-material-difference state is limited to aligned classifications with no material semantic distinction. Comparison remains deterministic and does not make an additional provider request.

## Salesforce Preview

`src/salesforce_preview.py` creates a deterministic illustrative dictionary only from the compatibility `ViolenceFinding` and authoritative `PolicyDecision`. It rejects `WRITE_FAILED`, performs no independent policy evaluation, and copies the policy outcome into the minimal `Illustrative_Write_Disposition__c` field. `WRITE_DETECTED`, `WRITE_UNCERTAIN`, and `WRITE_NOT_DETECTED` use the existing fact fields to represent their admissible findings. The field names are deliberately illustrative and contain no real Salesforce object names, credentials, identifiers, connection logic, or API calls.

Input, provider, schema, domain, or compatibility failure produces `WRITE_FAILED` and no preview.

## Streamlit Interface

`app.py` is the Streamlit interface. It provides:

- true empty-state behavior on initial load
- source selection for synthetic fixtures or manual narrative entry
- original narrative display before analysis
- explicit `Run Analysis` control
- stakeholder-readable deterministic validation summary
- primary two-column `Regex Baseline` and `Semantic Analysis` comparison
- stakeholder-readable semantic classification, deterministic validated-fact summary, explanation, and reasons
- comparison status, classification divergence, and semantic enrichment observations
- illustrative Salesforce preview
- collapsed `Technical Details` inside the semantic column containing semantic facts, validation stages, compatibility status, policy identifier and version, internal outcome, internal explanation, reason codes, and failure provenance when present

Semantic extraction is not run on page load, fixture selection, or manual typing. One semantic request occurs per `Run Analysis` action.

`src/presentation.py` is a display-only translation boundary. It maps every bounded `PolicyOutcome`, `PolicyReasonCode`, and `ValidationFailureStage` to deterministic stakeholder text and creates a concise summary only from `ValidatedSemanticFacts` and `PolicyDecision`. `app.py` renders these human-readable summaries before technical details. Summary generation makes no provider request. The deterministic execution layer remains authoritative: extraction, schema validation, domain validation, compatibility construction, policy evaluation, comparison, and Salesforce preview logic do not consume presentation labels and are unchanged by them.

## Session Behavior

`src/app_logic.py` contains testable presentation support logic. It validates and normalizes explicit analysis input, builds analysis results, validates manual narratives, assigns a session-local manual identifier, returns typed input failures before analysis work, and invalidates stale results when the active raw narrative changes.

## Independent Evaluation Foundation

Evaluation is a repository capability independent from the operational semantic pipeline. `src/evaluation/contracts.py` defines strict typed envelopes for synthetic cases, repository-authored expectations, observed results, field differences, case outcomes, baseline classifications, and artifact provenance. `src/evaluation/serialization.py` provides canonical JSON with sorted object keys while preserving explicitly ordered collections. These modules make no provider calls, import no OpenAI SDK, perform no semantic inference, and do not mutate application contracts.

Authority is deliberately separated:

- `evaluation/corpus/` is the future authoritative source for repository-authored synthetic cases and ground truth.
- `evaluation/runs/` is the future generated store for observed output. Observed output is evidence, never ground truth.
- `evaluation/baselines/` is reserved for explicitly accepted baselines.
- `evaluation/reports/` is reserved for generated engineering reports.
- `tests/evaluation/` verifies the contract boundary without network access.

An evaluation case keeps its synthetic narrative, metadata, and ground-truth expectation in distinct fields. Metadata, engineering notes, and expected outcomes must never be submitted to semantic extraction. Expected success requires an independently authored semantic payload; expected failure cannot contain success payloads. Observed failure cannot fabricate admissible semantic facts. Case status vocabulary is bounded to match, partial mismatch, failure, and non-comparable; baseline vocabulary is bounded to improved, degraded, unchanged, and incomparable. This execution defines vocabulary and invariants only, not comparison or baseline algorithms.

The framework is deterministic even though future live provider output will be probabilistic. Canonically stored observations enable later deterministic comparison against independently authored expectations. No production corpus, integrated runner, live or batch evaluation, accepted baseline, regression execution, or engineering report generation exists. OPORD 003 does not authorize automatic modification of the semantic pipeline from evaluation results.

## Architecture Boundaries

The system separates:

- lexical detection in `regex_baseline.py`
- deterministic input validation in `input_validation.py`
- deterministic narrative normalization in `narrative_normalizer.py`
- semantic extraction in `semantic_extractor.py`
- provider schema adaptation in `provider_adapter.py`
- structural semantic validation in `schema_validation.py`
- violence-domain consistency validation in `domain_validation.py`
- ordered validation orchestration in `semantic_validation.py`
- deterministic compatibility construction in `compatibility_finding.py`
- deterministic application write policy in `policy.py`
- deterministic stakeholder-facing label and explanation mapping in `presentation.py`
- independent deterministic evaluation contracts in `evaluation/contracts.py` and canonical serialization in `evaluation/serialization.py`
- transitional compatibility enforcement in `models.py`
- deterministic presentation and comparison logic in `app_logic.py`, `comparison.py`, and `salesforce_preview.py`

These boundaries keep OpenAI logic isolated from Streamlit and keep deterministic display behavior testable without network access.
