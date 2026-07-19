# Demo Runbook

## Demonstration boundary

Use synthetic data only. This includes text entered through the manual narrative control. Do not submit real patient, hospital, PHI, confidential, or production incident data. The application is not a production hospital system, and its Salesforce preview is illustrative only.

## Local start

From the repository root:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Create the virtual environment with Python 3.12 and copy `.env.example` to the Git-ignored `.env` for local configuration. Configure `OPENAI_API_KEY` before a live analysis. `OPENAI_MODEL` is optional. Environment variables override `.env`; Streamlit secrets override both when the app runs under Streamlit.

The page renders without provider configuration. An explicit valid analysis without a credential returns a bounded configuration failure and makes no provider request.

## Streamlit Community Cloud configuration

No deployment is performed or claimed by this runbook.

1. Select `joelliptondesign/Violence_Checker`, branch `main`.
2. Use `app.py` as the sole entrypoint.
3. In **Advanced settings**, select Python 3.12.
4. In the **Secrets** field, configure top-level `OPENAI_API_KEY` and, optionally, `OPENAI_MODEL`. Do not add a populated `.streamlit/secrets.toml` or `.env` to Git.
5. Expect an initial cold start while pinned dependencies install. Missing configuration remains presentation-safe and does not crash startup.

Community Cloud chooses Python through Advanced settings, so this repository does not rely on `runtime.txt`. Do not record a hosted URL until a separately authorized deployment occurs.

## Verified stakeholder baseline

- CASE_001 through CASE_008 have completed the stakeholder workflow with one provider request per valid execution.
- CASE_003 is represented as an affirmed historical physical-conduct disclosure and produces `WRITE_NOT_DETECTED` because no active current interpersonal proposition exists.
- Representative free-form supported-violence, non-violence, and ambiguous manual narratives have been exercised; valid manual input uses the same one-request path.
- Empty, whitespace-only, malformed, and oversized input stops before provider execution.
- Mobile widths of 390, 360, and 320 CSS pixels were inspected with semantic results ordered before regex detail and no page-level horizontal overflow.
- Local and hosted configuration behavior is ready for operator use, but hosted deployment and hosted acceptance remain unperformed manual follow-on actions.

## Demonstration flow

1. Select a synthetic fixture or manual narrative.
2. Confirm that the original narrative is shown unchanged.
3. Press **Run Analysis** once.
4. Review the deterministic regex baseline.
5. Review proposition-oriented semantic analysis and the active proposition set.
6. Review schema/domain validation and the deterministic policy disposition.
7. Review comparison observations and the policy-gated illustrative Salesforce preview.

A valid analysis makes exactly one provider request. Changing the selected narrative clears stale output. Empty manual input fails before any provider request.
Import, startup, source selection, fixture selection, and manual typing make zero provider requests. SDK automatic retries are disabled.

## Expected boundaries

- The provider receives only the formatting-normalized narrative and required contract instructions.
- Provider SDK objects do not reach application, policy, presentation, or evaluation code.
- Invalid structured output produces a typed failure and no preview.
- Policy and all display/reporting transformations are deterministic.
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
