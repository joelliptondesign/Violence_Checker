# Violence Checker Architecture

## Authority model

Raw `Incident.narrative` is the evidence authority. Normalization may change formatting only; it cannot summarize, correct, classify, or add facts.

`ViolenceSemanticEnvelope` is the sole current semantic authority. Its identity is `violence-checker.proposition-semantics` and its version is `1.0.0`. It represents:

- stable typed entities;
- proposition-scoped conduct, direction, completion, contact, temporal scope, assertion status, negation, and optional attribution;
- typed proposition relationships such as correction, supersession, support, contradiction, and negation;
- bounded proposition- or relationship-scoped uncertainties;
- exact excerpts from the normalized narrative with typed many-to-many support links; and
- extraction provenance for the structured-output contract and optional provider/model/request observations.

Document-level `SemanticFacts`, compatibility findings, and `operational_finding` are retired. They are neither generated nor accepted by current execution.

## Execution sequence

`run_analysis()` validates the incident, normalizes narrative formatting, runs the deterministic regex baseline, and invokes semantic extraction once. `extract_semantic_envelope()` performs exactly one Responses API structured-output request. `provider_adapter.py` immediately converts the structured provider response into the provider-independent envelope; no provider object crosses that boundary.

Schema validation establishes exact contract shape, schema identity, bounded vocabularies, identifier form, uniqueness, canonical collection order, and reference integrity. Domain validation independently checks evidence containment, semantic combinations, relationship meaning, cycles, uncertainty scoping, attribution, and incident identity. Invalid candidates stop before derivation or policy; validators do not repair them.

`semantic_derivation.py` deterministically computes relationship indexes, superseded propositions, the active proposition set, and a typed policy candidate view. Derived values are not provider claims and do not become a second semantic authority.

Policy `violence_checker_write_disposition` version `2.0.0` is a total deterministic function over a validated derived view:

- active, current, interpersonal, affirmed, intentional physical violence or threats produce `WRITE_DETECTED`;
- relevant conflict, scoped material uncertainty, or unresolved potentially violent propositions produce `WRITE_UNCERTAIN`;
- all other admissible states produce `WRITE_NOT_DETECTED`;
- failures before admissibility produce `WRITE_FAILED` through typed failure provenance.

Provider confidence and free-form prose never decide policy. Presentation, regex comparison, reporting, and the illustrative Salesforce payload consume typed results and remain deterministic.

## Aggregate contract

`PipelineResult` carries the original incident, normalized narrative, regex result, validation statuses, the optional validated `semantic_envelope`, optional `derived_semantics`, policy decision, and typed failure provenance. Success requires all current successor stages. No ad hoc semantic dictionary connects major stages.

## Evaluation boundary

Current evaluation uses corpus/evaluation schema `2.0.0`, successor semantic identity/version provenance, typed expected envelopes and derived views, proposition-addressed deterministic difference paths, and separately asserted validation and policy expectations. The current authoritative corpus is `evaluation/corpus/successor_corpus.json`.

The deterministic executor used by tests takes repository-authored ground truth as a fixture and makes no provider request. Live evaluation calls the same application orchestration exactly once per case. Corpus metadata and expectations never enter the extraction narrative.

Creation-time corpus, runs, accepted baseline, comparison, and engineering report remain unchanged. Strict top-level schema routing loads legacy JSON as immutable read-only artifacts. Legacy and successor artifact families are explicitly incomparable; no translation, upgrade, fallback guessing, or baseline promotion is permitted.

## Operational boundaries

The application is a local demonstration. Salesforce output is an illustrative dictionary only. There are no credentials, Salesforce identifiers, connections, writes, automated interventions, or claims that the policy constitutes clinical, legal, or safety judgment.

The approved design basis, successor specification, and migration strategy remain under `docs/`. They describe why this architecture is bounded and how creation-time evidence is isolated.
