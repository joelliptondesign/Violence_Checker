# Violence Checker

Violence Checker is a local Python and Streamlit demonstration of proposition-oriented violence semantics. It is non-production software: it performs no clinical, legal, safety, hospital-workflow, or Salesforce action.

## Current architecture

The only current semantic authority is `ViolenceSemanticEnvelope`, schema `violence-checker.proposition-semantics` version `1.0.0`. A validated envelope contains typed entities, proposition-scoped conduct and assertion state, directed relationships, bounded uncertainty, exact narrative evidence, and extraction metadata. Deterministic code derives the active proposition set and policy candidate view before policy runs.

The governed path is:

```text
raw Incident narrative
  -> formatting-only normalization
  -> exactly one provider structured-output request
  -> provider-independent ViolenceSemanticEnvelope
  -> schema validation
  -> violence-domain validation
  -> deterministic semantic derivation
  -> deterministic policy
  -> deterministic comparison, presentation, and illustrative preview
```

Raw narrative remains authoritative evidence. Provider SDK objects stop at the provider adapter. Invalid output fails closed; no stage repairs missing semantics or supplies silent defaults. The former document-level facts, compatibility finding, and operational finding are not current contracts and have no compatibility layer.

## Completed recovery baseline

The provider returns semantic candidate content with temporary local references only. Repository code assigns incident identity, semantic and extraction contract identity, canonical identifiers and ordering, and final reference remapping before strict schema and domain validation. Provider metadata cannot override those deterministic values.

The current stakeholder workflow has been verified across all eight synthetic fixtures. CASE_003 completes as a historical disclosure with no active current interpersonal violence. Representative free-form manual narratives, including supported violence, non-violence, and bounded ambiguity, traverse the same one-request pipeline; narrative wording remains user-authored and unrestricted except for deterministic input-boundary limits. Invalid input and non-analysis interactions make zero provider requests.

The deterministic policy distinguishes uncertainty that could change whether current interpersonal violence occurred from uncertainty that cannot negate an already explicit act. An affirmed, completed physical strike with contact is detected even if intentionality alone remains undetermined. Accidental contact, historical-only conduct, conflicting accounts, and materially unresolved conduct retain their separate outcomes.

At desktop widths, the Streamlit interface places Regex Baseline on the left and Semantic Analysis on the right. At 390, 360, and 320 CSS pixels, it has no page-level horizontal overflow, preserves technical-detail access, and stacks Semantic Analysis before Regex Baseline without duplicating either result. Deployment preparation supports Streamlit secrets, environment variables, and ignored local `.env` configuration.

## Demonstration-use boundary

This repository and its Streamlit interface are a synthetic demonstration only. Use the included synthetic fixtures or manually entered synthetic demonstration text. Do not submit real patient, hospital, protected health information (PHI), confidential, or production incident data. This is not a production hospital system. The Salesforce output is an illustrative preview and performs no external write.

## Local setup and use

Use Python 3.12 to match the hosted configuration documented below.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/streamlit run app.py
```

For local development, copy `.env.example` to the ignored `.env` file and set `OPENAI_API_KEY`. `OPENAI_MODEL` is optional and defaults to the repository demonstration model. Conventional environment variables are also supported and take precedence over values loaded from `.env`. Do not commit `.env` or `.streamlit/secrets.toml`.

The app starts and renders without credentials. Pressing **Run Analysis** with valid input and no provider credential produces a bounded configuration-failure result; it does not crash the application or issue a provider request.

Choose a synthetic fixture or enter a manual narrative, then press **Run Analysis**. One provider request occurs for each valid analysis action. The interface displays the original narrative, lexical baseline, proposition result, deterministic policy disposition, comparison, and policy-gated illustrative Salesforce preview.

The optional smoke test makes at most one provider request:

```sh
.venv/bin/python -m scripts.live_smoke_test
```

## Streamlit Community Cloud preparation

No hosted deployment or hosted URL is represented by this repository state. To configure a future Streamlit Community Cloud deployment:

1. Select repository `joelliptondesign/Violence_Checker`, branch `main`, and entrypoint `app.py`.
2. In **Advanced settings**, select Python 3.12. Community Cloud selects Python there; this repository therefore does not use `runtime.txt` as a deployment control.
3. In the Advanced settings **Secrets** field, enter `OPENAI_API_KEY` and optionally `OPENAI_MODEL` as top-level TOML keys. Enter values only in the Cloud secret manager, never in Git.
4. Deploy only after the intended operator has reviewed the synthetic-only and no-PHI boundary.

Configuration precedence is deterministic: Streamlit secrets, then conventional environment variables, then the ignored local `.env`, then the default model where applicable. Cold starts may take a few minutes while the hosted environment installs the pinned dependencies. Startup, source selection, fixture selection, and manual typing make zero provider requests. Each valid explicit analysis action makes exactly one request with SDK retries disabled.

## Evaluation

The authoritative current corpus is `evaluation/corpus/successor_corpus.json`: 48 manually authored synthetic cases using evaluation schema `2.0.0` and the successor semantic schema. Case IDs and raw narrative bytes are stable from the creation-time corpus, but successor ground truth is proposition-oriented and independent of provider output. Current observations, baselines, and comparisons are comparable only within the successor schema family.

Creation-time evaluation artifacts remain byte-immutable and readable through strict legacy schema `1.0.0` readers. They are never translated into successor truth, accepted as successor baselines, or compared across schema families. The creation-time corpus and artifacts are historical evidence, not current semantic authority.

```sh
.venv/bin/python -m src.evaluation.corpus validate
.venv/bin/python -m src.evaluation.corpus coverage
.venv/bin/python -m src.evaluation.runner validate --mode live_provider --run-id VALIDATE_ONLY --repository-commit "$(git rev-parse HEAD)" --output evaluation/runs/validate-only.json --case EVAL_001
```

Live evaluation remains explicit and performs exactly one governed analysis—and therefore one provider request—per selected valid case:

```sh
.venv/bin/python -m src.evaluation.runner run --mode live_provider --run-id LIVE_SUCCESSOR_001 --repository-commit "$(git rev-parse HEAD)" --model gpt-5-mini --config-identity semantic-prompt-successor-v1 --output evaluation/runs/live-successor-001.json
```

Generated runs are evidence, never ground truth. Existing outputs are not overwritten unless explicitly authorized by the runner.

## Validation

```sh
.venv/bin/python -m pytest
python3 -m tools.repo_governance validate-all
.venv/bin/python -m src.evaluation.corpus validate
.venv/bin/python -m src.evaluation.corpus coverage
```

See `docs/architecture.md`, `docs/demo_runbook.md`, `docs/local_governance.md`, and `evaluation/README.md` for the detailed boundaries and commands.

## Repository map

- `src/contracts.py`: current semantic, validation, policy, and aggregate contracts
- `src/provider_adapter.py`: provider-object termination boundary
- `src/schema_validation.py`, `src/domain_validation.py`: independent admissibility gates
- `src/semantic_derivation.py`: deterministic active-set and policy-view derivation
- `src/policy.py`: total deterministic policy
- `src/evaluation/`: current evaluation and strict legacy readers
- `evaluation/corpus/successor_corpus.json`: authoritative current synthetic ground truth
- `evaluation/runs/`, `evaluation/baselines/`, `evaluation/reports/`: evidence artifacts
- `tests/`: offline contract, pipeline, evaluation, policy, and governance tests
