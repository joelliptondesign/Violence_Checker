# Violence Checker Architecture

## Purpose And Scope

Violence Checker is a local Phase 0 Semantic Violence Detection Pre-PoC. It demonstrates how a synthetic incident narrative can move through lexical detection, semantic extraction, deterministic validation, comparison, and an illustrative write-back preview.

The repository is not a production system. It does not implement real Salesforce connectivity, persistence, authentication, deployment, workflow routing, analytics, model evaluation infrastructure, CI/CD, containerization, FoxCommand integration, or background processing.

## Incident Input Model

`src/models.py` defines the `Incident` input model. Each incident has:

- `incident_id`
- `narrative`

Both fields must be non-empty strings. The narrative is preserved exactly as supplied.

## Synthetic Fixture Library

`src/fixtures.py` contains the eight approved synthetic narratives, `CASE_001` through `CASE_008`. Fixture metadata is qualitative demonstration context only and is not submitted to semantic extraction.

## Lexical Detection

`src/regex_baseline.py` implements the illustrative regex baseline. It is deterministic, case-insensitive, lexical-only, and reusable outside Streamlit. It returns:

- `detected`
- `matched_terms`
- `matched_patterns`

This baseline intentionally does not resolve negation, corrections, historical context, accidental contact, or conflicting information.

## Semantic Extraction

`src/semantic_extractor.py` sends the unmodified incident narrative to the OpenAI Responses API. It makes one provider request per extraction call and requests structured output compatible with `ViolenceFinding`.

`src/semantic_prompt.py` centralizes the prompt. The prompt instructs the model to analyze only the supplied narrative, preserve current versus historical distinctions, identify negation, corrections, and conflicting statements, distinguish threats, attempts, completed violence, no violence, and unclear events, distinguish person-directed violence from object-directed contact, represent accidental contact without intentional violence, preserve exact evidence excerpts, and represent uncertainty.

## Validation Boundary

`ViolenceFinding` is the Pydantic validation boundary for semantic output. It validates bounded event type and intentionality values, confidence range, evidence list structure, and basic internal consistency. Expected extractor outcomes are represented by `SemanticExtractionResult`:

- `success`
- `configuration_failure`
- `openai_request_failure`
- `structured_response_failure`
- `pydantic_validation_failure`

Unvalidated provider output does not propagate as an application result.

Within `ViolenceFinding`, `contact_occurred` means person-directed physical contact relevant to the violence finding. It does not mean any contact with any object mentioned in the narrative.

## Deterministic Comparison

`src/comparison.py` builds `ComparisonResult` from an incident, a regex result, and a semantic extraction result. It makes no provider calls and does not use model-generated comparison prose. Observations are deterministic presentation logic derived from existing outputs.

The comparison result explicitly separates classification divergence from semantic enrichment. Classification alignment records whether regex and semantic extraction are both positive, both negative, regex-positive/semantic-negative, regex-negative/semantic-positive, or unavailable because semantic extraction failed. Semantic enrichment records material distinctions represented by validated semantic output but not by the lexical regex boolean, including historical context, threats, attempts, completed violence, accidental contact, no person-directed contact, negation, corrections, conflicting statements, injury mentions, actor or target information, supporting evidence, and confidence or uncertainty notes.

`material_difference_detected` is true when classification diverges or semantic enrichment exists. A true no-material-difference state is limited to aligned classifications with no material semantic distinction. Comparison remains deterministic and does not make an additional provider request.

## Salesforce Preview

`src/salesforce_preview.py` creates a deterministic illustrative dictionary from a successful validated semantic result. The field names are deliberately illustrative and contain no real Salesforce object names, credentials, identifiers, connection logic, or API calls.

Failed semantic results do not produce a preview.

## Streamlit Interface

`app.py` is the Streamlit interface. It provides:

- true empty-state behavior on initial load
- source selection for synthetic fixtures or manual narrative entry
- original narrative display before analysis
- explicit `Run Analysis` control
- side-by-side regex and semantic output
- semantic validation status
- comparison status, classification divergence, and semantic enrichment observations
- illustrative Salesforce preview

Semantic extraction is not run on page load, fixture selection, or manual typing. One semantic request occurs per `Run Analysis` action.

## Session Behavior

`src/app_logic.py` contains testable presentation support logic. It builds analysis results, validates manual narratives, assigns a session-local manual identifier, and invalidates stale results when the active narrative changes.

## Architecture Boundaries

The system separates:

- lexical detection in `regex_baseline.py`
- semantic extraction in `semantic_extractor.py`
- deterministic validation in `models.py`
- deterministic presentation and comparison logic in `app_logic.py`, `comparison.py`, and `salesforce_preview.py`

These boundaries keep OpenAI logic isolated from Streamlit and keep deterministic display behavior testable without network access.
