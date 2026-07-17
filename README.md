# Violence Checker

Violence Checker is a local Python and Streamlit pre-PoC for exploring semantic violence detection contracts and fixture behavior.

## Current Status

This repository is a local, non-production demonstration project. It contains a runnable Streamlit demonstration interface, canonical Pydantic data contracts, eight approved synthetic incident fixtures, a deterministic illustrative regex baseline, validated semantic extraction, a comparison layer, and an illustrative Salesforce write-back preview.

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
6. View the illustrative regex baseline, validated semantic extraction result, deterministic comparison status, separated classification divergence and semantic enrichment observations, and illustrative Salesforce write-back preview.

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

The extractor keeps OpenAI logic out of Streamlit. It submits the unmodified `Incident.narrative` to the OpenAI Responses API using one model call, requests structured output tied to `ViolenceFinding`, and validates the result through Pydantic before returning success.

Malformed or missing structured output cannot propagate as an application result. Expected failure states are typed:

- `configuration_failure`
- `openai_request_failure`
- `structured_response_failure`
- `pydantic_validation_failure`

Offline tests use fakes and do not require credentials or network access.

## Salesforce Preview

`src/salesforce_preview.py` creates a deterministic illustrative dictionary from a successful validated semantic result. Field names are intentionally illustrative and contain no real Salesforce identifiers, credentials, connection logic, or API calls.

Preview generation is declined for configuration failures, provider request failures, structured response failures, and Pydantic validation failures. Invalid or failed semantic output cannot produce a write-back payload.

## Repository Structure

```text
.
├── app.py
├── README.md
├── requirements.txt
├── src
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
- Model evaluation infrastructure
- CI/CD
- Containerization
