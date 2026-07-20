# Violence Checker Architecture

## Current implementation state

The true-north semantic boundary is implemented. It replaces the former proposition-oriented semantic representation with `TrueNorthSemanticEnvelope`, schema identity `violence-checker.true-north-incident-facts`, version `1.0.0`.

This execution intentionally stops at the semantic boundary. Deterministic policy, communication, presentation, evaluation, corpus, application orchestration, and Streamlit acceptance still reference the retired proposition runtime and are not currently compatible with the new contract. A fully working application is not claimed. No compatibility wrapper or dual semantic authority is present.

## Semantic authority

Raw `Incident.narrative` remains the evidence authority. Normalization may change formatting only; it cannot summarize, correct, classify, or add facts.

`TrueNorthSemanticEnvelope` is the provider-independent semantic contract. It contains one ordered `facts` collection. Each `IncidentFact` contains only:

- conduct;
- direction;
- intentionality;
- temporal scope;
- assertion status;
- resolution status;
- exact fact-local evidence and supported attributes;
- explicit material uncertainty;
- an optional narrow supersession reference; and
- an optional narrow contradiction-group identifier.

The semantic contract does not contain entities, propositions, general relationships, graph structures, policy outcomes or reasons, processing or completeness status, communication prose, or presentation fields. Atomic fact direction excludes `multiple`; that value belongs to later deterministic incident-level derivation.

## Provider boundary

The provider response contains only candidate facts, exact evidence excerpts, attribute support links, uncertainty, and temporary fact/correction/contradiction references. The provider cannot author:

- incident, schema, extraction-contract, fact, evidence, or contradiction-group identity;
- canonical ordering;
- processing or completeness status;
- policy results or reasons;
- recommendations, inferred outcomes, or negative conclusions; or
- compatibility, communication, presentation, entity, proposition, relationship, or graph payloads.

`provider_adapter.py` terminates the provider object. It rejects extra provider-authored bookkeeping, validates temporary reference resolution, assigns repository incident/schema/extraction identity, creates deterministic `FACT-`, `EVID-`, and `CGRP-` identifiers, canonicalizes collections and narrow references, and records exact offsets only when an excerpt occurrence is unambiguous or provider offsets identify it exactly.

## Evidence integrity

Evidence is fact-oriented. Every evidence record belongs to one fact, preserves an exact non-empty narrative excerpt, has repository-owned identity, may carry exact offsets, and names the material attributes it supports. There is no subject-oriented evidence graph.

Schema validation enforces strict shape, exact identities and versions, bounded enumerations, canonical identifiers and ordering, and reference integrity. Domain validation enforces exact containment and offsets, material-attribute coverage, uncertainty correspondence, doctrinal combinations, denial/accident/historical/no-contact safeguards, correction order and acyclicity, and contradiction-group integrity.

Validation is deterministic and fail-closed. It does not repair candidates, apply silent semantic defaults, or attempt unrestricted natural-language entailment.

## Current execution sequence

The implemented boundary is:

`normalized incident narrative` → one structured provider fact response → deterministic repository adapter → strict schema validation → deterministic domain/evidence validation → validated true-north envelope

Successful validation exposes the envelope directly. It does not call semantic derivation or create a policy-candidate aggregate. Repository-owned processing/completeness bookkeeping, active-set derivation, incident direction, material uncertainty, policy, communication, presentation, and evaluation remain later migration work.

## Preserved boundaries

Input validation, narrative normalization, regex result, and existing downstream policy-result contracts remain available. This semantic execution made no provider request, live evaluation run, corpus or baseline regeneration, deployment, push, external write, or Streamlit change.

Historical evaluation artifacts retain their creation-time schema families and were not rewritten or promoted. The proposition contract is no longer a current runtime semantic authority; legacy downstream consumers fail until separately authorized migration packages replace them.

## Operational limitations

The repository remains a synthetic demonstration. It does not provide clinical, legal, disciplinary, emergency-response, or safety decision support; PHI handling; a real Salesforce write; external persistence; authentication; hosted acceptance; or production suitability. Real patient, hospital, confidential, or production incident data must not be submitted.

## Governing authority

The approved [Workplace Violence Doctrine](workplace_violence_doctrine.md), [True North Semantic Contract Specification](true_north_semantic_contract_specification.md), and [True North Migration Strategy](true_north_migration_strategy.md) govern this boundary. Later packages must migrate deterministic derivation and policy, communication and presentation, evaluation and corpus authority, application orchestration, local and live-provider acceptance, baseline acceptance, deployment, and hosted acceptance without restoring dual semantic authority.
