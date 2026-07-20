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

`run_analysis()` validates the incident, normalizes narrative formatting, runs the deterministic regex baseline, and invokes semantic extraction once. `extract_semantic_envelope()` performs exactly one Responses API structured-output request with SDK retries disabled. The provider-facing contract contains semantic candidates and temporary local references only. It does not author incident identity, extraction metadata, schema identity/version, canonical identifiers, canonical ordering, or final references.

`provider_adapter.py` immediately terminates the provider object and deterministically assigns the validated incident identity, semantic schema identity/version, extraction contract identity, canonical entity/proposition/relationship/uncertainty/evidence/support identifiers, collection ordering, and final reference remapping. Obsolete provider-supplied extraction metadata is discarded and cannot override repository values.

Schema validation establishes exact contract shape, schema identity, bounded vocabularies, identifier form, uniqueness, canonical collection order, and reference integrity. Domain validation independently checks evidence containment, semantic combinations, relationship meaning, cycles, uncertainty scoping, attribution, and incident identity. Invalid candidates stop before derivation or policy; validators do not repair them.

`semantic_derivation.py` deterministically computes relationship indexes, superseded propositions, the active proposition set, and a typed policy candidate view. Derived values are not provider claims and do not become a second semantic authority.

Policy `violence_checker_write_disposition` version `2.0.0` is a total deterministic function over a validated derived view:

- active, current, interpersonal, affirmed physical violence or threats produce `WRITE_DETECTED`;
- intentionality uncertainty alone does not downgrade affirmed completed physical conduct with occurred contact; all uncertainty material to contact, completion, assertion, current scope, or interpersonal direction remains `WRITE_UNCERTAIN`;
- relevant conflict, scoped material uncertainty, or unresolved potentially violent propositions produce `WRITE_UNCERTAIN`;
- all other admissible states produce `WRITE_NOT_DETECTED`;
- failures before admissibility produce `WRITE_FAILED` through typed failure provenance.

Provider confidence and free-form prose never decide policy. Regex comparison, reporting, the illustrative Salesforce payload, and the facts supplied to executive communication consume typed results and remain deterministic.

After successful validation and a non-failure policy decision, `construct_communication_input()` creates an immutable, narrative-free `OperatorCommunicationInput`. It contains only bounded proposition facts plus narrow regex, comparison, policy, and Salesforce-eligibility projections. `generate_operator_communication()` may make one strict structured-output request with SDK retries disabled and accepts only `OperatorCommunication`: an incident summary, concise key findings, and a result explanation. Generated prose is presentation-only and cannot change validation, derivation, policy, comparison, Salesforce eligibility, or payload content. Missing configuration, request failure, malformed output, or an exception preserves deterministic repository-authored communication. Failed authoritative analysis uses explicit deterministic failure communication without making a communication request.

## Aggregate contract

`PipelineResult` carries the original incident, normalized narrative, regex result, validation statuses, the optional validated `semantic_envelope`, optional `derived_semantics`, policy decision, and typed failure provenance. `AnalysisResult` additionally carries deterministic comparison, policy-gated Salesforce preview, and bounded Operator Communication for presentation. Success requires all current successor stages. No ad hoc semantic dictionary connects major stages.

## Interaction and verification boundary

Narrative wording is user-authored free-form evidence. Deterministic input rules reject malformed, empty, whitespace-only, non-substantive, invalid-code-point, or over-20,000-character input before extraction; they do not constrain narrative semantics or vocabulary.

Import, startup, source selection, fixture selection, and manual typing issue zero provider requests. Invalid submission also issues zero. Each valid explicit **Run Analysis** action issues exactly one semantic extraction request. After successful validation and a non-failure policy decision, the Streamlit application attempts one separate presentation-only communication request. Extraction failure issues no communication request. Both provider clients disable SDK retries; there is no automatic analysis, semantic repair, critic, batch, or unattended inference path.

Repository verification covers all eight stakeholder fixtures, CASE_003 historical-disclosure behavior, explicit completed strikes with unresolved intentionality, accidental contact, and representative free-form manual narratives. The accepted executive information architecture presents the incident narrative, then a two-card comparison with Regex Keyword Detection on the left and AI-Powered Semantic Analysis on the right, followed by the illustrative Salesforce record. Incident Summary, Key Findings, and Why This Result appear once in the AI card. Regex and AI each own one collapsed Technical Details expander; Salesforce payload details remain owned by the Salesforce section. Mobile inspection at 390, 360, and 320 CSS pixels confirms responsive AI-first stacking without duplicate content or page-level overflow.

## Evaluation boundary

Current evaluation uses corpus/evaluation schema `2.0.0`, successor semantic identity/version provenance, typed expected envelopes and derived views, proposition-addressed deterministic difference paths, and separately asserted validation and policy expectations. The current authoritative corpus is `evaluation/corpus/successor_corpus.json`.

The deterministic executor used by tests takes repository-authored ground truth as a fixture and makes no provider request. Live evaluation calls the same application orchestration exactly once per case. Corpus metadata and expectations never enter the extraction narrative.

Creation-time corpus, runs, accepted baseline, comparison, and engineering report remain unchanged. Strict top-level schema routing loads legacy JSON as immutable read-only artifacts. Legacy and successor artifact families are explicitly incomparable; no translation, upgrade, fallback guessing, or baseline promotion is permitted.

## Operational boundaries

The application is a synthetic demonstration. Salesforce output is an illustrative dictionary only. Real patient, hospital, PHI, confidential, and production incident data must not be submitted. There are no committed credentials, Salesforce identifiers, connections, writes, automated interventions, or claims that the policy constitutes clinical, legal, or safety judgment.

Configuration precedence is Streamlit secrets, conventional environment variables, ignored local `.env`, and then the default model where applicable. Semantic extraction and Operator Communication have independently selectable model settings and share the configured provider credential. `app.py` is prepared as the sole Streamlit Community Cloud entrypoint with pinned dependencies and bounded missing-configuration behavior. Hosted deployment and hosted acceptance have not occurred; deployment remains a manual operator action.

The approved design basis, successor specification, and migration strategy remain under `docs/`. They describe why this architecture is bounded and how creation-time evidence is isolated.

## Planned true-north target state

The current runtime architecture described above remains the repository's active implementation. The approved [Workplace Violence Doctrine](workplace_violence_doctrine.md) is authoritative for a planned successor implementation, and the [True North Semantic Contract Specification](true_north_semantic_contract_specification.md) defines its target incident-fact design. Neither document is implemented runtime truth. The [True North Migration Strategy](true_north_migration_strategy.md) defines the replacement boundary and verification gates without authorizing implementation.

The planned target replaces the proposition-oriented envelope with minimal fact-level conduct, direction, intentionality, temporal scope, assertion, resolution, evidence, and uncertainty semantics. It deterministically derives active facts, incident direction, material uncertainty, and the four doctrinal outcomes. It also broadens qualifying doctrine to include self-directed and intentional property-directed violence and requires affirmed intentionality for qualifying completed contact. Those statements describe successor requirements, not current policy behavior.

No dual current semantic authority is permitted. A future implementation must replace or retire superseded provider contracts, semantic contracts, derived views, policy inputs, communication projections, and evaluation contracts before declaring the target contract active. Historical artifacts remain in their creation-time schema families, and temporary adapters must terminate before the sole current semantic boundary and be removed at cutover.

## SITREC governance boundary

SITREC governance is repository support and does not participate in application execution. `tools/repo_governance/sitrec_router.py` resolves the operational date with `America/Los_Angeles` and reports a deterministic route without filesystem mutation. Only top-level `docs/*.md` SITRECs are active candidates. Every mutating generation routes first, leaves one current-date active record, moves stale records to `docs/archive/sitrecs/`, updates rather than duplicates the same date, and rejects duplicate dates or filename/document Operational Date disagreement. Archived SITRECs remain historical provenance and are excluded from current authority selection.
