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
- `Incident` and `ViolenceFinding` contracts exist in `src/models.py` and remain unchanged for this correction.
- Semantic extraction uses `src/semantic_extractor.py` and remains unchanged for this correction.
- Semantic instructions in `src/semantic_prompt.py` remain unchanged for this correction.
- Regex output is deterministic and lexical-only in `src/regex_baseline.py` and remains unchanged for this correction.
- Comparison behavior in `src/comparison.py` remains unchanged for this correction.
- Salesforce preview behavior in `src/salesforce_preview.py` remains unchanged for this correction.
- Local configuration is loaded from repository-root `.env` by `src/config.py`; `.env` remains ignored by Git.
- Automated tests exist under `tests/`.
- Executor operation telemetry exists at `telemetry/executor_heartbeat.jsonl`.

## C. CORE INVARIANTS

- The original incident narrative is not rewritten before analysis.
- Fixture metadata is not submitted to semantic extraction.
- Semantic output cannot propagate as an application result without Pydantic validation.
- Semantic failures cannot silently become default `ViolenceFinding` objects.
- Exactly one OpenAI Responses API request is made per explicit analysis action.
- No provider request occurs on module import, initial Streamlit load, source selection, fixture selection, or manual typing.
- Regex behavior remains illustrative, lexical, deterministic, and not Rochester Regional logic.
- Comparison and preview layers make no provider requests.
- Salesforce preview requires validated semantic success.
- Failed semantic extraction results do not produce Salesforce previews.
- `.env` remains untracked and ignored.
- Data in the approved fixture library is synthetic.
- The repository does not assert protected health information handling capability.
- Repository truth supersedes SITREC text.

## D. SYSTEM MODEL

Initial page path:

Streamlit startup -> title and purpose text -> `Narrative source` heading -> supporting instruction -> unselected two-option radio -> no source workflow active -> `Incident Narrative` empty state -> no run button -> no analysis result -> no provider request.

Fixture path:

`Synthetic fixture` radio selection -> fixture selectbox -> approved fixture record from `src/fixtures.py` -> `Incident` object -> original narrative display -> explicit `Run Analysis` -> regex baseline -> semantic extractor -> Pydantic validation -> typed semantic result -> deterministic comparison status with classification divergence and semantic enrichment observations -> illustrative Salesforce preview when semantic validation succeeds -> Streamlit rendering.

Manual input path:

`Manual narrative` radio selection -> manual text area -> whitespace-only rejection -> session-local illustrative incident identifier -> `Incident` object -> original narrative display -> explicit `Run Analysis` -> regex baseline -> semantic extractor -> Pydantic validation -> typed semantic result -> deterministic comparison status with classification divergence and semantic enrichment observations -> illustrative Salesforce preview when semantic validation succeeds -> Streamlit rendering.

Failure path:

semantic configuration failure, OpenAI request failure, structured response failure, or Pydantic validation failure -> typed `SemanticExtractionResult` -> no default finding -> semantic comparison unavailable status and deterministic failure observation -> no Salesforce preview -> bounded Streamlit error display.

## E. AUTHORITY MODEL

| Component | Authority Level |
| --- | --- |
| Streamlit interface | `app.py` |
| App presentation support logic | `src/app_logic.py` |
| Approved fixture source text | `src/fixtures.py` |
| Incident schema | `src/models.py` `Incident` |
| Violence finding schema | `src/models.py` `ViolenceFinding` and validators |
| Semantic prompt | `src/semantic_prompt.py` |
| Semantic extraction behavior | `src/semantic_extractor.py` |
| Regex baseline | `src/regex_baseline.py` |
| Comparison layer | `src/comparison.py` |
| Salesforce preview layer | `src/salesforce_preview.py` |
| Environment configuration | `src/config.py`, `.env.example`, ignored local `.env` |
| Automated regression behavior | `tests/` |
| Architecture documentation | `docs/architecture.md` |
| Demonstration runbook | `docs/demo_runbook.md` |
| SITREC | Current-state rehydration artifact only |
| Deterministic validators | Test suite and imported reference SITREC validator functions |

## F. DATA / CONTRACT MODEL

- `Incident`: Pydantic model with non-empty `incident_id` and non-empty `narrative`. The narrative is preserved exactly.
- `ViolenceFinding`: Pydantic model with `violence_present`, `event_type`, `actor`, `target`, `contact_occurred`, `injury_mentioned`, `current_event`, `intentionality`, `negated`, `correction_present`, `conflicting_information`, `evidence_text`, `confidence`, and `uncertainty_notes`.
- `ViolenceEventType`: bounded values `none`, `verbal_threat`, `attempted_physical_violence`, `completed_physical_violence`, and `unclear`.
- `Intentionality`: bounded values `intentional`, `accidental`, and `unclear`.
- `SemanticExtractionResult`: typed result with `success`, `configuration_failure`, `openai_request_failure`, `structured_response_failure`, and `pydantic_validation_failure`.
- Regex result: dictionary containing `detected`, `matched_terms`, and `matched_patterns`.
- `ComparisonResult`: typed comparison container with incident, regex result, semantic result, semantic validation status, classification alignment, material difference flag, display status, deterministic classification divergence observations, deterministic semantic enrichment observations, and aggregate observations.
- Salesforce preview dictionary: illustrative fields derived from a successful validated `ViolenceFinding`.
- Fixture records: dictionaries containing an `Incident` and qualitative metadata. Metadata is display context only and is not semantic extraction input.
- Narrative source UI state: unselected initial radio state, `Synthetic fixture`, or `Manual narrative`; the UI state is not a third source value.

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
- No batch processing.
- No analytics dashboard.
- No evaluation platform or formal benchmark infrastructure.
- No model retry infrastructure.
- No guarantee of clinical, legal, operational, or safety correctness.
- No Rochester Regional implementation claim for the regex baseline.

## H. CURRENT CAPABILITIES

- Streamlit local interface can launch from `app.py`.
- Initial empty state is implemented without a placeholder source option.
- Fixture source selection supports the eight approved synthetic narratives.
- Manual narrative entry is supported for local demonstration.
- Empty or whitespace-only manual input is rejected before analysis.
- Regex baseline can run locally without network access.
- Semantic extraction can run through OpenAI Responses API when local credentials and network availability exist.
- Semantic outputs are validated through Pydantic before use.
- Typed semantic failure categories are displayed without stack traces.
- Regex and semantic outputs are displayed side by side after analysis.
- Comparison status and observations are deterministic and require no provider call.
- Salesforce preview is deterministic, illustrative, and only generated from validated semantic success.
- Stale analysis results are hidden when active input changes.
- Automated tests validate core behavior.

## I. KNOWN LIMITATIONS

- Semantic output remains probabilistic.
- Fixture set is small and synthetic.
- Regex baseline is illustrative and not Rochester Regional's actual implementation.
- No production security controls are implemented.
- No production reliability controls are implemented.
- No persistent audit record exists beyond local executor heartbeat telemetry.
- No real hospital taxonomy integration exists.
- No formal benchmark or gold dataset exists.
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
- App logic calls the regex baseline locally.
- App logic calls semantic extraction once.
- Semantic extractor reads local configuration, constructs an OpenAI client when credentials are present, and calls `responses.parse`.
- Pydantic validates the structured semantic result.
- App logic builds deterministic comparison observations.
- App logic builds an illustrative Salesforce preview only after semantic success.
- Streamlit renders results or typed failure information.

## K. GUARANTEES

- Repository tests enforce the current deterministic behavior within their encoded scope.
- `Incident` rejects empty `incident_id` and empty `narrative`.
- `ViolenceFinding` enforces bounded event type, bounded intentionality, confidence range, list evidence, and encoded consistency rules.
- Malformed semantic results return typed failure instead of default findings.
- The app import path does not make a provider request.
- Initial Streamlit state has no active incident or analysis output.
- Initial Streamlit state does not activate a fixture workflow or manual workflow.
- Fixture selection alone does not display analysis output.
- Manual typing alone does not display analysis output.
- One analysis action invokes one semantic extractor call in test-covered app logic.
- Stale-result invalidation clears stale stored results when source mode or active narrative changes.
- Fixture narratives remain exact in the fixture tests.
- Salesforce preview rejects non-success semantic results.

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
<Defines the Streamlit empty state, two-option narrative source selection, supporting instruction, original narrative display, explicit Run Analysis control, result rendering, and stale-result hiding.>

`src/app_logic.py`
<Builds analysis results, validates manual narratives, preserves active signatures, gates preview generation, and supports stale-result invalidation.>

`tests/test_streamlit_empty_state.py`
<Covers the two-option narrative source radio, removed placeholder option, supporting instruction, removed banner text, initial empty state, source-selection no-call behavior, selection-only no-analysis behavior, and stale-result clearing on source change.>

`tests/test_app_logic.py`
<Covers app import behavior, manual input validation, metadata exclusion, stale-result helpers, and one semantic extraction call per analysis action.>

`src/fixtures.py`
<Defines exactly eight approved synthetic fixture records with stable identifiers and qualitative metadata.>

`src/semantic_extractor.py`
<Calls OpenAI Responses API structured parsing, validates output through `ViolenceFinding`, and returns typed success or failure.>

`src/comparison.py`
<Builds deterministic comparison status, classification divergence observations, and semantic enrichment observations from existing regex and semantic results without provider calls.>

`src/salesforce_preview.py`
<Builds deterministic illustrative preview dictionaries only from successful validated semantic results.>

`telemetry/executor_heartbeat.jsonl`
<Stores local executor operation telemetry as JSONL.>

`docs/SITREC - 2026-07-17 Violence Checker Phase 0 Demonstration Baseline.md`
<Preserved prior-date active SITREC provenance and was not modified by the 2026-07-18 correction.>

## N. SOURCE OF TRUTH RULE

If the SITREC and repository conflict, the repository wins. The SITREC must be updated immediately. The SITREC never supersedes repository truth.

## O. REHYDRATION INSTRUCTIONS

1. Begin with repository inspection.
2. Confirm Git status before changes.
3. Read `README.md`, `docs/architecture.md`, `docs/demo_runbook.md`, `app.py`, `src/`, `tests/`, and `telemetry/executor_heartbeat.jsonl`.
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
- heartbeat JSONL validation
- target and reference repository Git status checks

## S. PLANNER / EXECUTOR RESPONSIBILITY MODEL

| Role | Responsibility |
| --- | --- |
| Planner | Defines operational meaning, invariants, system boundaries, and interpretation of repository truth. |
| Executor | Performs repository inspection, deterministic validation, authorized file mutations, deterministic repair, and telemetry append. |
| Deterministic validators | Identify structural, uniqueness, grounding, and continuation-safety findings without superseding repository truth. |
