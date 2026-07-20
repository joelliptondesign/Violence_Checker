# Demo Runbook

## Demonstration boundary

Use synthetic data only. This includes text entered through the manual narrative control. Do not submit real patient, hospital, PHI, confidential, or production incident data. The application is not a production hospital system, and its Salesforce preview is illustrative only.

## Local start

From the repository root:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Create the virtual environment with Python 3.12 and copy `.env.example` to the Git-ignored `.env` for local configuration. Configure `OPENAI_API_KEY` before a live analysis. `OPENAI_MODEL` and `OPENAI_COMMUNICATION_MODEL` are optional. Environment variables override `.env`; Streamlit secrets override both when the app runs under Streamlit.

The page renders without provider configuration. An explicit valid analysis without a credential returns a bounded configuration failure and makes no provider request.

## Streamlit Community Cloud configuration

No deployment is performed or claimed by this runbook.

1. Select `joelliptondesign/Violence_Checker`, branch `main`.
2. Use `app.py` as the sole entrypoint.
3. In **Advanced settings**, select Python 3.12.
4. In the **Secrets** field, configure top-level `OPENAI_API_KEY` and, optionally, `OPENAI_MODEL` and `OPENAI_COMMUNICATION_MODEL`. Do not add a populated `.streamlit/secrets.toml` or `.env` to Git.
5. Expect an initial cold start while pinned dependencies install. Missing configuration remains presentation-safe and does not crash startup.

Community Cloud chooses Python through Advanced settings, so this repository does not rely on `runtime.txt`. Do not record a hosted URL until a separately authorized deployment occurs.

## Verified stakeholder baseline

- CASE_001 through CASE_008 have completed the stakeholder workflow with one semantic extraction request per valid execution.
- CASE_003 is represented as an affirmed historical physical-conduct disclosure and produces `WRITE_NOT_DETECTED` because no active current interpersonal proposition exists.
- Representative free-form supported-violence, non-violence, and ambiguous manual narratives have been exercised; valid manual input uses the same one-request semantic path.
- Empty, whitespace-only, malformed, and oversized input stops before provider execution.
- Executive UX acceptance covers the incident-first information architecture, the side-by-side regex and AI comparison, single-instance Operator Communication, dual card-owned Technical Details, downstream Salesforce presentation, and deterministic failure and communication-fallback states.
- Mobile widths of 390, 360, and 320 CSS pixels were inspected with AI results ordered before regex detail and no page-level horizontal overflow.
- Local and hosted configuration behavior is ready for operator use, but hosted deployment and hosted acceptance remain unperformed manual follow-on actions.

## Demonstration flow

1. Select a synthetic fixture or manual narrative.
2. Confirm that the original narrative is shown unchanged.
3. Press **Run Analysis** once.
4. Review Regex Keyword Detection in the left comparison card.
5. Review the classification, Incident Summary, Key Findings, and Why This Result in the AI-Powered Semantic Analysis card.
6. Open the regex Technical Details expander for matched terms and patterns when needed.
7. Open the AI Technical Details expander for extracted entities, supporting evidence, and decision logic when needed.
8. Review the policy-gated illustrative Salesforce record and its separate payload-details expander.

A valid analysis makes exactly one semantic extraction request. After successful semantic validation and a non-failure policy result, the Streamlit application attempts exactly one presentation-only Operator Communication request. Communication failure preserves the authoritative result and displays deterministic fallback communication. Semantic extraction failure makes no communication request. Changing the selected narrative clears stale output. Empty manual input fails before any provider request.
Import, startup, source selection, fixture selection, and manual typing make zero provider requests. SDK automatic retries are disabled for both provider boundaries.

## Expected boundaries

- The provider receives only the formatting-normalized narrative and required contract instructions.
- Provider SDK objects do not reach application, policy, presentation, or evaluation code.
- Invalid structured output produces a typed failure and no preview.
- Policy, comparison, Salesforce eligibility, and Salesforce payload generation are deterministic.
- Operator Communication receives only a narrative-free bounded projection after successful validation and policy, and its output cannot change authoritative results.
- The deterministic Operator Communication fallback occupies the same AI-card surface as accepted provider communication.
- The preview is illustrative and performs no external write.
- Narrative length remains bounded at 20,000 characters; invalid input stops before extraction.
- No batch or unattended analysis path exists in the Streamlit application.

## Offline verification

```sh
.venv/bin/python -m pytest
.venv/bin/python -m src.evaluation.corpus validate
.venv/bin/python -m src.evaluation.corpus coverage
python3 -m tools.repo_governance validate-all
```

The live smoke test is optional and makes at most one request:

```sh
.venv/bin/python -m scripts.live_smoke_test
```
