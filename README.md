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

## Setup and use

Python 3.10 or newer is required.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/streamlit run app.py
```

Set `OPENAI_API_KEY` for live extraction. `OPENAI_MODEL` is optional and defaults to the repository demonstration model. The app starts without credentials, but an analysis request requires them.

Choose a synthetic fixture or enter a manual narrative, then press **Run Analysis**. One provider request occurs for each valid analysis action. The interface displays the original narrative, lexical baseline, proposition result, deterministic policy disposition, comparison, and policy-gated illustrative Salesforce preview.

The optional smoke test makes at most one provider request:

```sh
.venv/bin/python -m scripts.live_smoke_test
```

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
