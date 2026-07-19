# Demo Runbook

## Start

From the repository root:

```sh
.venv/bin/streamlit run app.py
```

Configure `OPENAI_API_KEY` before a live analysis. `OPENAI_MODEL` is optional.

## Demonstration flow

1. Select a synthetic fixture or manual narrative.
2. Confirm that the original narrative is shown unchanged.
3. Press **Run Analysis** once.
4. Review the deterministic regex baseline.
5. Review proposition-oriented semantic analysis and the active proposition set.
6. Review schema/domain validation and the deterministic policy disposition.
7. Review comparison observations and the policy-gated illustrative Salesforce preview.

A valid analysis makes exactly one provider request. Changing the selected narrative clears stale output. Empty manual input fails before any provider request.

## Expected boundaries

- The provider receives only the formatting-normalized narrative and required contract instructions.
- Provider SDK objects do not reach application, policy, presentation, or evaluation code.
- Invalid structured output produces a typed failure and no preview.
- Policy and all display/reporting transformations are deterministic.
- The preview is illustrative and performs no external write.

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
