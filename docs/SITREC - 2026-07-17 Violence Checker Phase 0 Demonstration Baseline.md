# SITREC - 2026-07-17 Violence Checker Phase 0 Demonstration Baseline

## A. SYSTEM IDENTITY

Repository: `Violence_Checker`.

System identity: local Phase 0 semantic violence detection pre-PoC.

Implementation layer: Python and Streamlit application for a local stakeholder demonstration using synthetic hospital incident narratives only.

The repository demonstrates an illustrative lexical regex baseline, OpenAI Responses API semantic extraction, Pydantic validation, deterministic comparison observations, and an illustrative Salesforce write-back preview. It is local demonstration software and is not production software.

This SITREC is a current-state rehydration artifact for 2026-07-17. It does not supersede repository files, tests, source code, local configuration, or deterministic validation output.

## B. CURRENT STATE

Repo truth for 2026-07-17:

- The app entry point is `app.py`.
- The application has a true initial empty state with no active incident and no analysis output.
- The Streamlit interface requires a fixture selection or non-empty manual narrative before analysis.
- Analysis occurs only after the explicit `Run Analysis` control.
- One semantic extraction request occurs per analysis action.
- Fixture selection alone does not run regex analysis, semantic extraction, comparison generation, or Salesforce preview generation.
- Manual typing alone does not run regex analysis, semantic extraction, comparison generation, or Salesforce preview generation.
- Eight approved synthetic fixtures exist in `src/fixtures.py`.
- `Incident` and `ViolenceFinding` contracts exist in `src/models.py`.
- Semantic extraction uses the OpenAI Responses API through `src/semantic_extractor.py`.
- Semantic instructions are centralized in `src/semantic_prompt.py`.
- Semantic extraction returns typed success and failure categories through `SemanticExtractionResult`.
- Successful semantic output must validate as a real `ViolenceFinding`.
- Failed semantic output does not silently become a default finding.
- Regex output is deterministic and lexical-only in `src/regex_baseline.py`.
- Comparison observations are deterministic in `src/comparison.py`.
- Salesforce preview generation is deterministic and illustrative in `src/salesforce_preview.py`.
- Salesforce preview is generated only from successful validated semantic output.
- Stale results are invalidated when the active narrative changes.
- Local configuration is loaded from repository-root `.env` by `src/config.py`.
- `.env` is ignored by Git through `.gitignore`.
- `.env.example` contains placeholder configuration names.
- Repository-local virtual environment `.venv` exists for local execution and is ignored by Git.
- Automated tests exist under `tests/`.
- Architecture documentation exists at `docs/architecture.md`.
- Stakeholder demonstration runbook exists at `docs/demo_runbook.md`.
- Executor operation telemetry exists at `telemetry/executor_heartbeat.jsonl`.

## C. CORE INVARIANTS

- The original incident narrative is not rewritten before analysis.
- Fixture metadata is not submitted to semantic extraction.
- Semantic output cannot propagate as an application result without Pydantic validation.
- Semantic failures cannot silently become default `ViolenceFinding` objects.
- Exactly one OpenAI Responses API request is made per explicit analysis action.
- No provider request occurs on module import, initial Streamlit load, fixture selection, or manual typing.
- Regex behavior remains illustrative, lexical, deterministic, and not Rochester Regional logic.
- Comparison and preview layers make no provider requests.
- Salesforce preview requires validated semantic success.
- Failed semantic extraction results do not produce Salesforce previews.
- `.env` remains untracked and ignored.
- Data in the approved fixture library is synthetic.
- The repository does not assert protected health information handling capability.
- Repository truth supersedes SITREC text.

## D. SYSTEM MODEL

Fixture path:

`src/fixtures.py` approved fixture record -> `Incident` object -> original narrative display -> explicit `Run Analysis` -> regex baseline -> semantic extractor -> Pydantic validation -> typed semantic result -> deterministic comparison -> illustrative Salesforce preview when semantic validation succeeds -> Streamlit rendering.

Manual input path:

manual text area -> whitespace-only rejection -> session-local illustrative incident identifier -> `Incident` object -> original narrative display -> explicit `Run Analysis` -> regex baseline -> semantic extractor -> Pydantic validation -> typed semantic result -> deterministic comparison -> illustrative Salesforce preview when semantic validation succeeds -> Streamlit rendering.

Failure path:

semantic configuration failure, OpenAI request failure, structured response failure, or Pydantic validation failure -> typed `SemanticExtractionResult` -> no default finding -> deterministic comparison observation for failure -> no Salesforce preview -> bounded Streamlit error display.

## E. AUTHORITY MODEL

| Component | Authority Level |
| --- | --- |
| Approved fixture source text | `src/fixtures.py` |
| Incident schema | `src/models.py` `Incident` |
| Violence finding schema | `src/models.py` `ViolenceFinding` and validators |
| Semantic prompt | `src/semantic_prompt.py` |
| Semantic extraction behavior | `src/semantic_extractor.py` |
| Pydantic validation boundary | `src/models.py` plus Pydantic runtime validation |
| Regex baseline | `src/regex_baseline.py` |
| Comparison layer | `src/comparison.py` |
| Salesforce preview layer | `src/salesforce_preview.py` |
| Streamlit interface | `app.py` |
| App presentation support logic | `src/app_logic.py` |
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
- `ComparisonResult`: typed comparison container with incident, regex result, semantic result, semantic validation status, and deterministic observations.
- Salesforce preview dictionary: illustrative fields derived from a successful validated `ViolenceFinding`.
- Fixture records: dictionaries containing an `Incident` and qualitative metadata. Metadata is display context only and is not semantic extraction input.

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
- Initial empty state is implemented.
- Fixture source selection supports the eight approved synthetic narratives.
- Manual narrative entry is supported for local demonstration.
- Empty or whitespace-only manual input is rejected before analysis.
- Regex baseline can run locally without network access.
- Semantic extraction can run through OpenAI Responses API when local credentials and network availability exist.
- Semantic outputs are validated through Pydantic before use.
- Typed semantic failure categories are displayed without stack traces.
- Regex and semantic outputs are displayed side by side after analysis.
- Comparison observations are deterministic and require no provider call.
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
- User selects synthetic fixture input or manual narrative input.
- Streamlit displays the active narrative before analysis.
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
- Fixture selection alone does not display analysis output.
- Manual typing alone does not display analysis output.
- One analysis action invokes one semantic extractor call in test-covered app logic.
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
<Defines the Streamlit empty state, fixture/manual source selection, original narrative display, explicit Run Analysis control, result rendering, and stale-result hiding.>

`src/config.py`
<Loads repository-root `.env`, keeps `OPENAI_API_KEY` optional for import/offline tests, and defaults `OPENAI_MODEL` to `gpt-5-mini`.>

`src/models.py`
<Defines `Incident`, `ViolenceFinding`, event type enum, intentionality enum, and Pydantic consistency validators.>

`src/fixtures.py`
<Defines exactly eight approved synthetic fixture records with stable identifiers and qualitative metadata.>

`src/regex_baseline.py`
<Defines deterministic case-insensitive lexical matching and returns `detected`, `matched_terms`, and `matched_patterns`.>

`src/semantic_prompt.py`
<Centralizes semantic extraction instructions and contains no fixture identifiers or case-specific expected outputs.>

`src/semantic_extractor.py`
<Calls OpenAI Responses API structured parsing, validates output through `ViolenceFinding`, and returns typed success or failure.>

`src/comparison.py`
<Builds deterministic comparison observations from existing regex and semantic results without provider calls.>

`src/salesforce_preview.py`
<Builds deterministic illustrative preview dictionaries only from successful validated semantic results.>

`src/app_logic.py`
<Builds analysis results, validates manual narratives, preserves active signatures, gates preview generation, and supports stale-result invalidation.>

`docs/architecture.md`
<Documents purpose, scope, data flow, validation boundary, comparison, preview, Streamlit behavior, and exclusions.>

`docs/demo_runbook.md`
<Documents the stakeholder demonstration flow, expected empty state, recommended fixtures, talking points, failure fallback, and shutdown.>

`requirements.txt`
<Declares Streamlit, OpenAI, Pydantic, python-dotenv, and pytest dependencies.>

`tests/`
<Contains automated tests for config, app logic, empty state, fixtures, models, regex, semantic extractor, prompt, comparison, and preview behavior.>

`telemetry/executor_heartbeat.jsonl`
<Stores local executor operation telemetry as JSONL.>

`.gitignore`
<Excludes `.env`, `.venv`, Python caches, Streamlit secrets, test caches, and OS metadata.>

## N. SOURCE OF TRUTH RULE

If the SITREC and repository conflict, the repository wins. The SITREC must be updated immediately. The SITREC never supersedes repository truth.

## O. REHYDRATION INSTRUCTIONS

1. Begin with repository inspection.
2. Confirm Git status before changes.
3. Read `README.md`, `docs/architecture.md`, `docs/demo_runbook.md`, `app.py`, `src/`, `tests/`, and `telemetry/executor_heartbeat.jsonl`.
4. Run deterministic validation before relying on behavior.
5. Preserve OPORD-completed boundaries and do not assume production readiness.
6. Use the minimum context required.
7. If repository truth changes on 2026-07-17, update this same-date SITREC.
8. On a later date, create a new dated SITREC rather than duplicating this date.
9. Planner defines operational meaning and continuation boundaries.
10. Executor maintains artifacts, runs validators, and performs deterministic repair loops without redefining meaning.

## P. SITREC LIFECYCLE

This active SITREC represents current repository truth for 2026-07-17. It is not an execution diary and must not be treated as historical narrative. It may be updated if repository truth changes on the same date. Historical provenance remains supporting context only and must not redefine the current system identity.

## Q. DAILY UNIQUENESS

Exactly one active SITREC shall exist for 2026-07-17. If another 2026-07-17 SITREC appears, consolidation is required. The active canonical location is the top-level `docs/` directory, with archived historical SITRECs reserved for `docs/archive/sitrecs/` if needed by later lifecycle operations.

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

Validator output may identify structural defects. Validator output does not determine operational truth.

## S. PLANNER / EXECUTOR RESPONSIBILITY MODEL

| Role | Responsibility |
| --- | --- |
| Planner | Defines operational meaning, invariants, system boundaries, and interpretation of repository truth. |
| Executor | Performs repository inspection, deterministic validation, authorized file mutations, deterministic repair, and telemetry append. |
| Deterministic validators | Identify structural, uniqueness, grounding, and continuation-safety findings without superseding repository truth. |

The executor must not override planner-defined meaning, introduce future capability claims, or treat this SITREC as stronger than repository truth.
