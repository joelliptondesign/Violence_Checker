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
5. Review the regex result, semantic extraction result, comparison observations, and Salesforce preview.

## Talking Points

- The regex baseline is illustrative and lexical-only.
- Regex can flag terms without understanding historical context, corrections, or negation.
- Semantic extraction returns structured output validated by Pydantic.
- Comparison observations are deterministic and do not make another model call.
- One semantic request occurs per `Run Analysis` click.
- The Salesforce preview is illustrative only and performs no integration.

## Expected Contrasts

- `CASE_008`: semantic extraction should distinguish attempted violence from completed violence and show no contact.
- `CASE_007`: semantic extraction should surface correction language and no contact with the nurse.
- `CASE_003`: semantic extraction should preserve the historical versus current-event distinction.
- `CASE_004`: semantic extraction should represent accidental contact.

## Failure Fallback

If a semantic request returns a typed failure, do not retry during the demo. Show the result category, explain that failed semantic output cannot produce a Salesforce preview, and continue with deterministic regex and comparison behavior where available.

## Shutdown

Stop Streamlit with `Ctrl-C` in the terminal running the server.
