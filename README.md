# Violence Checker

Violence Checker is a local Python and Streamlit pre-PoC for exploring semantic violence detection contracts and fixture behavior.

## Current Status

This repository is a local, non-production demonstration project. It contains a runnable Streamlit demonstration interface, canonical Pydantic data contracts, eight approved synthetic incident fixtures, a deterministic illustrative regex baseline, validated semantic extraction, a comparison layer, an illustrative Salesforce write-back preview, and the contract foundation for an independent evaluation capability.

Semantic extraction is implemented as an isolated Python module that calls the OpenAI Responses API and validates structured output with Pydantic. The Streamlit app lets a user run one analysis at a time and view regex, semantic, comparison, and preview outputs side by side. It performs no real Salesforce integration.

## Prerequisites

- Python 3.10 or newer
- Local shell access from the repository root

## Local Setup

Create and activate a repository-local virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```sh
.venv/bin/python -m pip install -r requirements.txt
```

Create a local environment file from the example:

```sh
cp .env.example .env
```

Place the future OpenAI API key in `.env`:

```sh
OPENAI_API_KEY=
OPENAI_MODEL=
```

The current scaffold does not require `OPENAI_API_KEY` to start or test.
Semantic extraction requires `OPENAI_API_KEY` only when extraction is invoked. `OPENAI_MODEL` is optional and defaults to `gpt-5-mini` for this demonstration.

Start the Streamlit application:

```sh
.venv/bin/streamlit run app.py
```

Complete the local demonstration flow:

1. Choose a narrative source. The initial page does not select an incident or show analysis output.
2. Select `Synthetic fixture` and choose `CASE_001` through `CASE_008`, or select `Manual narrative`.
3. For manual input, enter a non-empty narrative. The text is analyzed as typed and is not persisted.
4. Review the original narrative displayed by the app.
5. Press `Run Analysis`.
6. View the illustrative regex baseline, validated semantic extraction result, deterministic application write disposition, comparison status, separated classification divergence and semantic enrichment observations, and policy-gated illustrative Salesforce write-back preview.

Semantic extraction occurs only after pressing `Run Analysis`. One semantic request occurs per analysis action.

Run the automated tests:

```sh
.venv/bin/python -m pytest
```

Run the optional live semantic extraction smoke test:

```sh
.venv/bin/python -m scripts.live_smoke_test
```

The live smoke test uses `CASE_008`, makes at most one OpenAI request, and fails clearly if `OPENAI_API_KEY` is unavailable. It prints only extraction status and non-secret result data.

## Evaluation Foundation

`src/evaluation/` defines strict, provider-independent evaluation contracts, canonical JSON serialization, and a deterministic corpus loader, validator, and coverage calculator. Evaluation is an independent repository capability: it describes expected and observed results without changing or executing the semantic pipeline.

The 48-case `violence-checker-synthetic-evaluation-corpus` version `1.0.0` and its manually authored deterministic ground truth live under `evaluation/corpus/` and are authoritative. Stable case identifiers use `EVAL_001` through `EVAL_048`; cases are ordered by identifier and use bounded primary-category and documentation-quality vocabularies. Generated observations belong under `evaluation/runs/` and are evidence, not ground truth. Accepted baselines and generated engineering reports have separate locations under `evaluation/baselines/` and `evaluation/reports/`. Evaluation metadata, engineering notes, and expected outcomes are structurally separate from the synthetic narrative and must never be submitted to semantic extraction.

The corpus covers completed and attempted assault, threats, accidental contact, historical disclosures, negation, corrections, conflicts, object-directed aggression, self-directed violence, ambiguous encounters, incomplete reports, required documentation-quality conditions, and compound cases. Ground truth cannot be authored or repaired from provider, regex, app, or external-system output. The framework contracts and stored artifact serialization are deterministic even though future live provider output will be probabilistic. OPORD 003 does not authorize automatic pipeline modification, and corpus loading, validation, and coverage make no provider calls or semantic inferences.

Validate the corpus, inspect deterministic coverage, and run evaluation tests:

```sh
.venv/bin/python -m src.evaluation.corpus validate
.venv/bin/python -m src.evaluation.corpus coverage
.venv/bin/python -m pytest tests/evaluation
```

## Domain Models

`src/models.py` defines:

- `Incident`, with non-empty `incident_id` and `narrative` fields. The narrative is preserved exactly as supplied.
- `ViolenceFinding`, a strict Pydantic model for later structured output. It captures event type, actor, target, contact, injury, current-event status, intentionality, negation, correction and conflict flags, evidence text, confidence, and uncertainty notes.

The finding contract uses bounded event and intentionality enums, requires confidence from `0` through `1`, rejects malformed objects, and blocks basic internal inconsistencies such as a no-violence finding that claims physical contact.

## Fixture Library

`src/fixtures.py` contains exactly eight approved synthetic incidents with stable identifiers `CASE_001` through `CASE_008`. Optional qualitative metadata labels the scenario type for tests and documentation only; it is not runtime classification output.

## Regex Baseline

`src/regex_baseline.py` implements a deterministic, case-insensitive lexical baseline. It returns:

- `detected`
- `matched_terms`
- `matched_patterns`

The baseline is intentionally transparent and limited to bounded keyword and phrase matching, including terms such as `hit`, `punch`, `punched`, `kick`, `kicked`, `assault`, `assaulted`, `swing`, `swung`, and threat phrases such as `gonna punch`.

Regex limitations are intentional and visible. The baseline does not resolve negation, historical context, accidental versus intentional contact, corrections, or conflicting statements.

## Comparison Layer

`src/comparison.py` builds deterministic comparison status and observations from the existing regex result and semantic extraction result. It does not make a second model call and does not use model-generated prose for comparison.

The comparison distinguishes classification divergence from semantic enrichment. It can highlight regex-positive/semantic-negative results, regex-negative/semantic-positive results, semantic comparison failure, and semantic context that the lexical baseline does not encode, including historical language, threats, attempts, completed violence, accidental contact, no contact, negation, corrections, conflicting information, injury mentions, actor or target information, evidence excerpts, and confidence or uncertainty notes.

## Semantic Extraction

`src/semantic_prompt.py` centralizes the semantic extraction instructions. The prompt tells the model to analyze only the supplied incident narrative, distinguish current and historical events, identify negation, corrections, and conflicting statements, classify threats, attempts, completed violence, no violence, and unclear cases, distinguish intentional from accidental contact, avoid unsupported assumptions, preserve exact evidence excerpts, and represent uncertainty.

`src/semantic_extractor.py` exposes:

```python
extract_violence_finding(incident: Incident) -> SemanticExtractionResult
```

The extractor keeps OpenAI logic out of Streamlit. App orchestration supplies a separate incident containing the deterministically normalized narrative. The extractor makes one OpenAI Responses API call, parses `ProviderStructuredResponse`, and deterministically copies its fields into a provider-independent candidate. Dedicated schema validation constructs `SemanticFacts`; dedicated domain validation evaluates encoded field consistency; and only the resulting `ValidatedSemanticFacts` may enter the local compatibility constructor that maps facts into `ViolenceFinding` for current comparison and preview behavior.

Malformed or missing structured output cannot propagate as an application result. Expected failure states are typed:

- `configuration_failure`
- `openai_request_failure`
- `structured_response_failure`
- `pydantic_validation_failure`

Offline tests use fakes and do not require credentials or network access.

## Application Write Policy

`src/policy.py` implements local policy `violence_checker_write_disposition` version `1.0.1`. After schema validation, domain validation, and compatibility construction, it deterministically produces `WRITE_DETECTED`, `WRITE_UNCERTAIN`, `WRITE_NOT_DETECTED`, or `WRITE_FAILED`. Failure takes precedence over uncertainty, uncertainty over detected, and detected over not detected. Provider-reported confidence alone does not affect the outcome.

Material uncertainty is determined only from bounded structured facts: conflicting information, unclear event type, materially unclear intentionality, an inconsistent threat representation, or a negated affirmative finding. Free-form uncertainty notes remain visible evidence but cannot independently override decisive structured facts. Accordingly, the approved `CASE_001` completed-assault state is `WRITE_DETECTED` when violence, completed physical violence, contact, injury, current-event status, and intentionality are affirmative and no conflict, negation, or correction override is present.

The policy controls only representation inside this demonstration. It does not make clinical, legal, safety, hospital workflow, human-review, or real Salesforce decisions.

## Presentation Layer

`src/presentation.py` deterministically translates internal policy outcomes, reason codes, validation stages, and validated semantic facts into stakeholder-readable labels, explanations, and a concise summary. The primary Streamlit result is a two-column comparison: `Regex Baseline` on the left and `Semantic Analysis` on the right. The semantic column contains a collapsed `Technical Details` expander with validation, semantic facts, compatibility status, policy metadata, internal outcome, reason codes, and internal explanation.

Presentation mappings do not evaluate policy, reinterpret semantic facts, alter validation, change comparison or preview behavior, or make an additional provider request. Summary text reuses only validated bounded fields and makes no inference request. The deterministic execution contracts remain authoritative; presentation labels are display-only.

## Salesforce Preview

`src/salesforce_preview.py` creates a deterministic illustrative dictionary from the locally constructed compatibility `ViolenceFinding` and required `PolicyDecision`. `WRITE_FAILED` cannot produce a preview; the other outcomes are copied into the illustrative write-disposition field. Field names are intentionally illustrative and contain no real Salesforce identifiers, credentials, connection logic, or API calls.

Preview generation is declined for configuration failures, provider request failures, structured response failures, provider parse failures, schema failures, domain failures, and compatibility failures. Invalid or inadmissible semantic output cannot produce a write-back payload.

## Repository Structure

```text
.
├── app.py
├── README.md
├── evaluation
│   ├── corpus
│   ├── runs
│   ├── baselines
│   └── reports
├── requirements.txt
├── src
│   ├── evaluation
│   │   ├── corpus.py
│   │   ├── contracts.py
│   │   └── serialization.py
│   ├── config.py
│   ├── app_logic.py
│   ├── comparison.py
│   ├── fixtures.py
│   ├── models.py
│   ├── regex_baseline.py
│   ├── salesforce_preview.py
│   ├── semantic_extractor.py
│   └── semantic_prompt.py
├── scripts
│   └── live_smoke_test.py
├── telemetry
│   └── executor_heartbeat.jsonl
└── tests
    ├── evaluation
    │   ├── test_corpus.py
    │   └── test_contracts.py
    ├── test_config_and_app.py
    ├── test_app_logic.py
    ├── test_comparison.py
    ├── test_fixtures.py
    ├── test_models.py
    ├── test_regex_baseline.py
    ├── test_salesforce_preview.py
    └── test_semantic_extractor.py
```

## Documentation

- [Architecture](docs/architecture.md)
- [Stakeholder Demo Runbook](docs/demo_runbook.md)

## Not Yet Implemented

- LLM orchestration
- Real Salesforce connectivity
- Database persistence
- Authentication
- Production deployment
- Deployment configuration
- FoxCommand integration
- Background processing
- Batch processing
- Agent orchestration
- Workflow routing
- Human review queues
- Analytics dashboards
- Integrated evaluation runner and live batch execution
- Accepted evaluation baselines and regression execution
- Generated engineering evaluation reports
- CI/CD
- Containerization
