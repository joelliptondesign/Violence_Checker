# Violence Checker Architecture

## Current implementation state

The true-north semantic, deterministic-policy, and downstream application runtime are implemented. They use `TrueNorthSemanticEnvelope`, schema identity `violence-checker.true-north-incident-facts`, version `1.0.0`, repository-owned analysis status, deterministic semantic views, and direct policy evaluation over validated facts.

Application orchestration, regex comparison, illustrative Salesforce projection, bounded operator communication, presentation, and Streamlit now consume the true-north fact contract. Evaluation, corpus reconstruction, baseline acceptance, live-provider validation, deployment, and hosted acceptance remain pending. No compatibility wrapper, proposition policy candidate, or dual semantic authority is present.

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

The semantic contract does not contain entities, propositions, general relationships, graph structures, policy outcomes or reasons, processing or completeness status, communication prose, or presentation fields. Atomic fact direction excludes `multiple`; repository derivation computes it only as an incident-level direction.

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

## Repository interpretation and policy

Repository processing status is outside semantic facts and has exactly five states: successful analysis, provider failure, schema failure, validation failure, and pipeline failure. Completeness status is also outside facts and distinguishes complete admissible analysis, incomplete analysis, and unresolved semantic content. Neither status concludes that violence is absent.

After successful validation, `semantic_derivation.py` deterministically projects only active fact IDs, superseded fact IDs, narrow contradiction-group membership, and incident direction. Incident direction is `interpersonal`, `self_directed`, `object_directed`, `multiple`, or `unknown`. Derivation does not create facts or a generalized graph.

`policy.py` evaluates validated operational facts directly with repository processing/completeness status and the reproducible deterministic view. It does not consume a policy-candidate aggregate, provider confidence, provider outcomes, recommendations, communication, or presentation fields. The policy returns:

- `Violence Detected` for at least one active, affirmed, intentional, current qualifying fact;
- `Uncertain` for admissible active semantic uncertainty capable of changing classification;
- `No Violence Detected` only for complete admissible analysis without qualifying current violence or material classification uncertainty; and
- `Unable to Determine` for failed, incomplete, malformed, or inadmissible processing.

All five conduct values qualify when the other doctrinal conditions hold. Self-directed violence and intentional object-directed property violence qualify. Accidental, historical, denied, and superseded facts do not qualify. Direction describes the incident and never independently suppresses violence; unknown direction alone is non-material.

## Current execution sequence

The implemented runtime is:

`input validation` → `normalization` → one structured provider fact response → deterministic repository adapter → strict schema validation → deterministic domain/evidence validation → validated true-north envelope → repository status and deterministic semantic views → direct deterministic policy → regex comparison → illustrative Salesforce projection → bounded operator communication → presentation

Successful validation exposes the envelope, repository processing/completeness status, and deterministic views. Policy reads the facts directly and verifies that the supplied view and completeness state match them. Downstream components project this authority without reinterpreting it. Evaluation reconstruction and acceptance remain later migration work.

## Preserved boundaries

Input validation, narrative normalization, and regex result contracts remain available. The application makes one semantic request for a valid explicit analysis, disables provider retries, and makes no request for invalid input. This integration made no live evaluation run, corpus or baseline regeneration, deployment, push, or external write.

Historical evaluation artifacts retain their creation-time schema families and were not rewritten or promoted. The proposition contract is no longer a current runtime semantic authority; evaluation and corpus consumers remain for a separately authorized migration package.

## Operational limitations

The repository remains a synthetic demonstration. It does not provide clinical, legal, disciplinary, emergency-response, or safety decision support; PHI handling; a real Salesforce write; external persistence; authentication; hosted acceptance; or production suitability. Real patient, hospital, confidential, or production incident data must not be submitted.

## Governing authority

The approved [Workplace Violence Doctrine](workplace_violence_doctrine.md), [True North Semantic Contract Specification](true_north_semantic_contract_specification.md), and [True North Migration Strategy](true_north_migration_strategy.md) govern this boundary. Later packages must migrate evaluation and corpus authority and complete local and live-provider acceptance, baseline acceptance, deployment, and hosted acceptance without restoring dual semantic authority.
