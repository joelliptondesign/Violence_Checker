# Stakeholder Demo Runbook

## Prerequisites

- Repository available at `/Users/joellipton/Desktop/Violence_Checker`
- Repository-local virtual environment present at `.venv`
- Local `.env` configured for semantic extraction
- All incident reports used in the demo are synthetic

## Start

From the repository root:

```sh
source .venv/bin/activate
.venv/bin/streamlit run app.py
```

The initial page should show no selected incident and no analysis output. It should display the project title, synthetic-data notice, regex baseline disclaimer, and instruction to select a fixture or enter a narrative.

## Five-Minute Demo Sequence

Use this sequence:

1. `CASE_008` — attempted violence without contact
2. `CASE_007` — correction handling
3. `CASE_003` — historical context
4. `CASE_004` — accidental contact

For each case:

1. Select `Synthetic fixture`.
2. Choose the case.
3. Confirm the narrative appears.
4. Press `Run Analysis`.
5. Compare `Regex Baseline` on the left with `Semantic Analysis` on the right, including the deterministic summary, explanation, and reasons.
6. Expand `Technical Details` inside the semantic column only when engineering inspection of semantic facts, validation stages, compatibility status, policy metadata, internal outcome, or reason codes is useful.

## Talking Points

- The regex baseline is illustrative and lexical-only.
- Regex can flag terms without understanding historical context, corrections, or negation.
- Semantic extraction returns structured output validated by Pydantic.
- Comparison observations are deterministic and do not make another model call.
- Policy `violence_checker_write_disposition` version `1.0.1` deterministically represents admissible results as `WRITE_DETECTED`, `WRITE_UNCERTAIN`, `WRITE_NOT_DETECTED`, or `WRITE_FAILED`.
- Structured facts determine material uncertainty. Free-form uncertainty notes remain visible but cannot independently change a decisive disposition.
- `CASE_001` is the completed-assault demonstration and is expected to display `Violence Detected` when its affirmative structured facts validate without conflict, negation, or correction override.
- The primary assessment labels are deterministic display mappings: `Violence Detected`, `Uncertain`, `No Violence Detected`, and `Unable to Determine`.
- Stakeholder summaries, explanations, and reasons are deterministic mappings from validated facts and `PolicyDecision`; they are not model-generated and make no additional provider request.
- Internal enums and policy metadata remain available under `Technical Details` and remain authoritative for engineering inspection.
- The policy is an application write disposition only; it is not a clinical, legal, safety, hospital workflow, or real Salesforce decision.
- One semantic request occurs per `Run Analysis` click.
- Explicit analysis input is validated before regex or semantic extraction. Narratives require substantive text, exclude null characters and Unicode surrogates, and are limited to 20,000 Python characters for the local demonstration.
- Rejected input displays a bounded message and makes no regex or semantic request.
- The Salesforce preview is illustrative only and performs no integration.

## Expected Contrasts

- `CASE_008`: semantic extraction should distinguish attempted violence from completed violence and show no contact.
- `CASE_007`: semantic extraction should surface correction language and no contact with the nurse.
- `CASE_003`: semantic extraction should preserve the historical versus current-event distinction.
- `CASE_004`: semantic extraction should represent accidental contact.

## Failure Fallback

If input, provider, schema, domain, or compatibility processing returns a typed failure, do not retry during the demo. The primary assessment shows `Unable to Determine`; `Technical Details` retains internal `WRITE_FAILED` and failure provenance. Explain that failed output cannot produce a Salesforce preview and continue with deterministic comparison behavior where available.

## Shutdown

Stop Streamlit with `Ctrl-C` in the terminal running the server.
