# Violence Checker

Violence Checker is a local Python and Streamlit executive demonstration of proposition-oriented violence semantics for workplace-safety incident review. It is non-production software: it performs no clinical, legal, safety, hospital-workflow, or Salesforce action.

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
  -> deterministic comparison and illustrative preview
  -> bounded executive communication and presentation
```

Raw narrative remains authoritative evidence. Provider SDK objects stop at the provider adapter. Invalid output fails closed; no stage repairs missing semantics or supplies silent defaults. The former document-level facts, compatibility finding, and operational finding are not current contracts and have no compatibility layer.

## Governing successor design

The following documents govern the planned true-north successor design; they do not claim that the current runtime has been migrated:

- [Workplace Violence Doctrine](docs/workplace_violence_doctrine.md)
- [True North Semantic Contract Specification](docs/true_north_semantic_contract_specification.md)
- [True North Migration Strategy](docs/true_north_migration_strategy.md)

The [Operator Communication Tone Guidelines](docs/operator_communication_tone_guidelines.md) are the governing authority for all operator-facing wording, including prompts, deterministic fallback communication, Streamlit presentation, operational facts, decision logic, Salesforce previews, and future communication evaluations. They establish presentation policy only and do not change runtime behavior or classification authority.

## Completed recovery baseline

The provider returns semantic propositions, exact supporting evidence, uncertainty, and temporary local references only. Repository code assigns incident identity, semantic and extraction contract identity, canonical identifiers and ordering, final reference remapping, and active/superseded resolution status before strict schema and domain validation. Provider metadata cannot override those deterministic values.

The current stakeholder workflow has been verified across all eight synthetic fixtures. CASE_003 completes as a historical disclosure with no active current interpersonal violence. Representative free-form manual narratives, including supported violence, non-violence, and bounded ambiguity, traverse the same one-request semantic pipeline; narrative wording remains user-authored and unrestricted except for deterministic input-boundary limits. Invalid input and non-analysis interactions make zero provider requests.

The deterministic policy distinguishes uncertainty that could change whether current interpersonal violence occurred from uncertainty that cannot negate an already explicit act. An affirmed, completed physical strike with contact is detected even if intentionality alone remains undetermined. Accidental contact, historical-only conduct, conflicting accounts, and materially unresolved conduct retain their separate outcomes.

The accepted executive information architecture presents the incident narrative first, Regex Keyword Detection and AI-Powered Semantic Analysis as the comparison, and the illustrative Salesforce record after both result cards. The AI card presents the final classification with Operator Communication fields for Incident Summary, Key Findings, and Why This Result. Each comparison card owns one collapsed Technical Details expander: regex details remain with keyword detection, while extracted entities, supporting evidence, and decision logic remain with AI analysis. At 390, 360, and 320 CSS pixels, the interface has no page-level horizontal overflow and stacks AI analysis before regex detail without duplicating either result. Deployment preparation supports Streamlit secrets, environment variables, and ignored local `.env` configuration.

After successful semantic validation and a non-failure policy result, the application constructs an immutable, narrative-free `OperatorCommunicationInput` from validated facts and deterministic downstream results. The Streamlit application may make one strict structured communication request and accepts only the bounded `OperatorCommunication` contract. A missing configuration, failed request, or invalid communication response leaves all authoritative results unchanged and uses deterministic repository-authored communication instead. Failed semantic analysis uses explicit deterministic failure communication and makes no communication request.

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

For local development, copy `.env.example` to the ignored `.env` file and set `OPENAI_API_KEY`. `OPENAI_MODEL` and `OPENAI_COMMUNICATION_MODEL` are optional and default to the repository demonstration models. Conventional environment variables are also supported and take precedence over values loaded from `.env`. Do not commit `.env` or `.streamlit/secrets.toml`.

The app starts and renders without credentials. Pressing **Run Analysis** with valid input and no provider credential produces a bounded configuration-failure result; it does not crash the application or issue a provider request.

Choose a synthetic fixture or enter a manual narrative, then press **Run Analysis**. Each valid analysis action makes exactly one semantic extraction request. A successfully validated non-failure result also attempts exactly one presentation-only communication request in the Streamlit application. The interface displays the original narrative, the executive regex and AI comparison, the deterministic policy classification, bounded Operator Communication, card-owned technical details, and the policy-gated illustrative Salesforce record.

The optional smoke test makes at most one provider request:

```sh
.venv/bin/python -m scripts.live_smoke_test
```

## Streamlit Community Cloud preparation

No hosted deployment or hosted URL is represented by this repository state. To configure a future Streamlit Community Cloud deployment:

1. Select repository `joelliptondesign/Violence_Checker`, branch `main`, and entrypoint `app.py`.
2. In **Advanced settings**, select Python 3.12. Community Cloud selects Python there; this repository therefore does not use `runtime.txt` as a deployment control.
3. In the Advanced settings **Secrets** field, enter `OPENAI_API_KEY` and optionally `OPENAI_MODEL` and `OPENAI_COMMUNICATION_MODEL` as top-level TOML keys. Enter values only in the Cloud secret manager, never in Git.
4. Deploy only after the intended operator has reviewed the synthetic-only and no-PHI boundary.

Configuration precedence is deterministic: Streamlit secrets, then conventional environment variables, then the ignored local `.env`, then the default model where applicable. Cold starts may take a few minutes while the hosted environment installs the pinned dependencies. Startup, source selection, fixture selection, and manual typing make zero provider requests. Each valid explicit analysis action makes exactly one semantic request with SDK retries disabled; a successfully validated non-failure result then makes at most one communication request, also with SDK retries disabled.

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
python3 -m tools.repo_governance route-sitrec
python3 -m tools.repo_governance validate-sitrec --path "docs/SITREC - 2026-07-20 Violence Checker Successor Semantic Baseline.md"
python3 -m tools.repo_governance validate-all
.venv/bin/python -m src.evaluation.corpus validate
.venv/bin/python -m src.evaluation.corpus coverage
```

SITREC lifecycle authority uses the `America/Los_Angeles` operational date. Only Markdown SITRECs directly under `docs/` are active candidates; historical records live under `docs/archive/sitrecs/`. The non-mutating router must run before generation. Lifecycle mutation leaves exactly one current-date active record, updates it on repeated same-day generation, archives stale active records before creating a later-date record, and rejects duplicate dates across active and archived records.

See `docs/architecture.md`, `docs/demo_runbook.md`, `docs/local_governance.md`, and `evaluation/README.md` for the detailed boundaries and commands.

## Repository map

- `src/contracts.py`: current semantic, validation, policy, and aggregate contracts
- `src/provider_adapter.py`: provider-object termination boundary
- `src/schema_validation.py`, `src/domain_validation.py`: independent admissibility gates
- `src/semantic_derivation.py`: deterministic active-set and policy-view derivation
- `src/policy.py`: total deterministic policy
- `src/operator_communication.py`: deterministic communication input projection and fallback
- `src/operator_communication_provider.py`: presentation-only structured communication boundary
- `src/operator_communication_prompt.py`: executive communication instructions
- `src/presentation.py`: executive comparison and Salesforce presentation projections
- `src/evaluation/`: current evaluation and strict legacy readers
- `evaluation/corpus/successor_corpus.json`: authoritative current synthetic ground truth
- `evaluation/runs/`, `evaluation/baselines/`, `evaluation/reports/`: evidence artifacts
- `tests/`: offline contract, pipeline, evaluation, policy, and governance tests
