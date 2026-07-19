# Successor Semantic Contract Specification

## 1. Purpose

This specification defines the implementation-neutral successor semantic contract for the repository's violence-detection domain. It replaces the current document-level semantic model conceptually with one proposition-oriented authority capable of retaining multiple independently scoped assertions from one incident narrative.

The specification is complete enough to govern a later implementation without inventing additional semantic concepts. It does not implement the contract, change current behavior, migrate data, or define a new policy outcome vocabulary.

## 2. Scope and Non-Goals

The scope is limited to distinctions demonstrated by the current repository: interpersonal, object-directed, and self-directed conduct; threatened, attempted, and completed conduct; contact; current and historical scope; negation; correction and supersession; competing assertions; bounded uncertainty; attribution; and exact narrative evidence.

The successor contract does not define complete taxonomies for self-harm, property damage, falls, medications, devices, security investigations, clinical findings, legal findings, safety findings, workflow queues, motive, causation, source credibility, or a general hospital-event ontology. It does not define generalized temporal logic, a universal entity ontology, proposition-scoped injury, provider-confidence calibration, clinical or legal intent, or recommendations of any kind.

The specification does not authorize source, test, prompt, policy, corpus, presentation, compatibility, preview, or migration changes. It contains no executable model, JSON Schema, migration procedure, or implementation patch.

## 3. Design Basis

The approved design basis is `docs/semantic_design_basis.md`, checked against current repository contracts and behavior. The current `SemanticFacts` and transitional `ViolenceFinding` each compress a complete narrative into one event type, actor, target, contact state, time state, negation flag, correction flag, conflict flag, evidence list, and uncertainty list. Compound corpus cases demonstrate that these values can belong to different assertions and therefore cannot remain authoritative document-level semantics.

The governing repository facts are:

- normalization is formatting-only; the raw narrative remains authoritative evidence and the normalized narrative is the single provider inference input;
- one provider request is made for each valid single analysis or evaluation case;
- provider-specific objects terminate at the provider adapter;
- structural validation, violence-domain validation, deterministic policy, presentation, and evaluation have separate authority;
- provider confidence is excluded from current semantic equality and is not deterministic truth;
- evaluation corpus truth is repository-authored and independent of provider, regex, application, policy, and observed outputs; and
- preserved runs, baselines, comparisons, and reports are immutable creation-time evidence.

No inspected repository authority contradicts the design basis.

## 4. Architectural Principles

1. **One current semantic authority.** A `ViolenceSemanticEnvelope` is the sole authoritative current semantic representation. No document-level `ViolenceFinding`, compatibility record, aggregate shadow fields, or parallel write model is coequal.
2. **Proposition scope.** Every violence-relevant semantic value belongs to an identified proposition or an identified relationship between propositions.
3. **Narrative authority.** The raw narrative is authoritative evidence. Deterministic normalization may change formatting only and produces the sole inference input without changing meaning.
4. **One semantic pass.** A valid single analysis or evaluation case makes exactly one provider request. All propositions, relationships, uncertainties, and evidence supports are returned in that request; no second semantic pass is allowed.
5. **Strict stage boundaries.** Provider extraction proposes narrative-grounded content. Deterministic schema validation establishes shape. Deterministic domain validation establishes encoded coherence. Neither validation stage infers, repairs, or silently defaults semantics.
6. **Deterministic policy.** Policy consumes only a validated envelope and explicitly versioned deterministic views. It never consumes provider SDK objects, provider confidence, or free-form notes.
7. **Context without promotion.** Historical, object-directed, self-directed, negated, corrected, disputed, and uncertain propositions remain semantic context but do not automatically become active current interpersonal violence.
8. **Bounded vocabularies.** Semantic decisions use closed vocabularies. Free-form labels and notes are non-authoritative display or provenance content.
9. **No lossy primary representation.** A global summary may be derived for presentation, but it cannot govern current semantics, policy, or evaluation truth.
10. **Historical immutability.** Legacy artifacts remain readable through their creation-time schema and remain byte-unchanged. They are not translated into successor evidence.

## 5. Authoritative Semantic Envelope

The conceptual `ViolenceSemanticEnvelope` is incident-scoped and contains exactly these authoritative collections and identities:

- `schema_identity`, required and equal to `violence-checker.proposition-semantics`;
- `schema_version`, required and initially equal to `1.0.0`;
- `incident_id`, required, non-empty, and equal to the validated incident identity;
- ordered `entities`, required and non-empty because every proposition has an actor reference, including an `unspecified` entity for an unresolved actor;
- ordered `propositions`, required and non-empty for a successful extraction, including explicit negative or uncertain propositions when no affirmative conduct is asserted;
- ordered `relationships`, required and permitted to be empty;
- ordered `uncertainties`, required and permitted to be empty;
- ordered `evidence_excerpts`, required and non-empty for a successful extraction;
- ordered `evidence_supports`, required and non-empty for a successful extraction; and
- `extraction_metadata`, required only for the bounded provenance described in Section 6.15.

Raw and normalized narratives remain in the validated incident and normalization provenance contracts rather than being duplicated as alternate truth inside the semantic envelope. The envelope is bound to those inputs by `incident_id`. A consumer must receive the envelope together with the matching validated incident provenance.

Successful structural and domain validation create a typed admissibility carrier for this exact envelope. Validation status, issue records, policy outcomes, comparisons, presentation summaries, and workflow fields are outside the envelope.

## 6. Core Concepts

### 6.1 Proposition

A proposition is one narrative-grounded assertion about one bounded conduct involving one actor and one target scope at one temporal scope. It is the smallest unit on which conduct, completion, contact, intentionality, assertion status, uncertainty, evidence, and attribution may differ.

Required content is `proposition_id`, `actor_ref`, `conduct_kind`, `target`, `completion`, `contact`, `temporal_scope`, `intentionality`, and `assertion_status`. `attribution` is optional only for unattributed narrative prose. Relationships, uncertainty, and evidence are separate referenced records.

The provider extracts proposition content in the single response. Schema validation establishes its exact shape and vocabulary; domain validation establishes coherence. Deterministic derivation may classify direction and active-set membership but may not change extracted content. Policy may consume only validated propositions through the boundary in Section 14.

A proposition may not contain a document outcome, policy decision, workflow action, recommendation, source-credibility judgment, provider confidence, or global incident summary.

### 6.2 Participant Reference

An `EntityReference` provides envelope-local identity for an actor, target, or attribution source. The bounded `entity_kind` vocabulary is `person`, `people_collective`, `object`, and `unspecified`. An optional exact or normalized narrative label may distinguish entities such as patient, nurse, staff, witness one, witness two, wall, or cart; the label is referential, not an ontology or credibility claim.

An explicit but unidentified person uses an entity of kind `unspecified`; null is not used to mean unknown. Objects are represented only to distinguish object-directed from interpersonal conduct. Roles such as patient, staff, or witness may appear as bounded attribution kinds or non-authoritative narrative labels; they do not imply truth or rank.

Entity references are provider-extracted, structurally validated, and consumed by domain validation, deterministic direction derivation, presentation, and evaluation. Policy may consume only the resulting validated direction and any specifically versioned participant-role view required by policy; it may not infer identity from labels.

### 6.3 Conduct

`conduct_kind` captures what kind of conduct is asserted without encoding completion. Its bounded values are:

- `physical_conduct`: a physical act or movement, including person-, self-, or object-directed conduct;
- `threat_expression`: words or communicative conduct presented as potentially threatening;
- `threatening_movement`: movement presented as potentially threatening but not established as a physical attempt;
- `contact_only`: physical contact described without an established violent act, such as an accidental bump; and
- `undetermined`: the narrative is violence-relevant but does not establish a conduct kind.

The provider extracts conduct. Validation does not upgrade threatening movement to physical attempt, contact to violence, or general aggression to a more specific kind. Free-form descriptions may be displayed as exact evidence but are not additional conduct vocabulary.

### 6.4 Direction and Target

Each proposition contains a required target structure with one `target_kind`: `entity`, `self`, `none`, or `undetermined`. `target_ref` is required exactly when `target_kind` is `entity`; `self` means the actor is the target and carries no second reference; `none` means the conduct has no target for this bounded representation; and `undetermined` means a target is semantically applicable but unresolved.

Direction is not provider-authored. It is derived deterministically as:

- `self-directed` when `target_kind` is `self`;
- `object-directed` when the target reference has `entity_kind=object`;
- `interpersonal` when the target reference has `entity_kind=person` or `people_collective` and does not resolve to the actor;
- `undetermined` when target kind or referenced entity kind is `undetermined` or `unspecified`, when actor/target identity prevents distinguishing self from other, or when no bounded rule establishes direction.

`target_kind=none` yields `undetermined` direction unless the conduct/contact combination makes direction not applicable to a deterministic view. Direction never follows from a free-form label alone. A provider may not author a direction field, preventing duplicate authority.

### 6.5 Completion

Completion is proposition-scoped and uses `threatened`, `attempted`, `completed`, `not_applicable`, or `undetermined`.

`threatened` represents stated or communicated prospective conduct. `attempted` represents a person-, self-, or object-directed physical attempt that did not complete the asserted target contact. `completed` represents completion of the asserted conduct, including contact-only conduct. `not_applicable` is used only when completion does not meaningfully apply to the encoded conduct. `undetermined` means completion applies but the narrative does not establish it.

Completion is provider-extracted and domain-validated. It is not inferred from a global contact value and does not by itself establish an interpersonal policy outcome.

### 6.6 Contact

Contact is proposition-scoped and uses `occurred`, `did_not_occur`, `undetermined`, or `not_applicable`. It describes contact attributable to the encoded conduct and encoded target only. Object contact therefore remains attached to the object-directed proposition and cannot become person contact.

Contact is provider-extracted and domain-validated. `did_not_occur` is an affirmative statement about absence of contact for an applicable conduct; `not_applicable` means contact is not meaningful for the conduct, such as a verbal threat; `undetermined` means it is meaningful but unresolved.

### 6.7 Temporal Scope

Temporal scope uses exactly `current_incident`, `historical`, or `undetermined`. Each proposition has one value. Mixed time is represented by multiple propositions, not by a `mixed` value. General dates, intervals, durations, and temporal logic are outside scope.

The provider extracts the scope from the normalized narrative. Domain validation prevents a correction that changes time from leaving the replaced proposition active. Policy receives the proposition scope but remains solely responsible for the operational treatment of validated historical content.

### 6.8 Assertion Status

The base assertion status uses exactly `affirmed`, `negated`, or `uncertain`.

- `affirmed` means the attributed or unattributed account asserts the proposition.
- `negated` means the account explicitly denies the proposition's content.
- `uncertain` means the account itself presents whether the proposition is asserted as unresolved.

`corrected`, `superseded`, and `disputed` are not base statuses. They require explicit relationships so their other endpoint and disputed dimension cannot be lost. Quoted language that is asserted to have been spoken uses the appropriate base status; quotation alone creates no special status. Purely hypothetical conduct is not a demonstrated required category and must not be promoted into a violence proposition unless the narrative presents it as a relevant assertion whose status can be represented by the existing vocabulary.

### 6.9 Negation

Negation is first represented by `assertion_status=negated` on the proposition whose conduct is denied. When the narrative also contains a distinct affirmative, uncertain, or attributed assertion that the denial explicitly opposes, a directed `negates` relationship is required from the negated proposition to that distinct target proposition.

A standalone denial does not require fabrication of an affirmative proposition merely to serve as a relationship target. It remains fully proposition-scoped through its own actor, conduct, target, completion, contact, time, attribution, and evidence. Negation may not globally affect unrelated propositions.

### 6.10 Correction and Supersession

A correction is represented by two propositions when both the earlier content and replacement content are present in the narrative, plus one directed `supersedes` relationship from the replacing proposition to the replaced proposition. The earlier proposition remains immutable narrative evidence but is excluded from the active assertion set.

If a correction only retracts earlier content and supplies no affirmative replacement, the later negated proposition supersedes the earlier proposition. If it replaces interpersonal conduct with object-directed, accidental, historical, or non-threatening content, both propositions retain their independent scoped values.

The provider extracts both propositions and the relationship. Deterministic derivation computes active-set membership. Neither validation nor derivation rewrites the earlier proposition. A superseded proposition cannot govern policy as active content.

### 6.11 Conflict

Competing accounts are represented as separate attributed or unattributed propositions plus a `conflicts_with` relationship. Conflict is semantically symmetric and is serialized once as a canonical unordered pair. The relationship contains a non-empty ordered set of disputed dimensions drawn only from the uncertainty-dimension vocabulary.

Conflict does not select a winner, rank sources, infer credibility, or adjudicate truth. Both non-superseded propositions remain in the active assertion set as competing assertions. Policy may receive their validated conflict and uncertainty structure but determines any outcome independently.

### 6.12 Uncertainty

An `Uncertainty` record identifies one proposition, one bounded dimension, and the evidence supporting the uncertainty. The permitted dimensions are `actor_identity`, `target_identity`, `conduct_type`, `direction`, `contact`, `completion`, `intentionality`, `temporal_scope`, `threat_meaning`, and `assertion_status`.

Uncertainty is provider-extracted when the narrative explicitly lacks, qualifies, or disputes a material value. It does not replace explicit `undetermined` values: the semantic field records the unresolved value and the uncertainty record records which dimension is unresolved. An uncertainty cannot be added merely because provider confidence is low.

An optional free-form extraction note may explain the source language for presentation, but it is non-authoritative, excluded from deterministic derivation, policy, and semantic equality, and cannot introduce a new uncertainty dimension.

### 6.13 Evidence Support

An `EvidenceExcerpt` has a required envelope-local identifier and a required non-empty exact excerpt copied from the normalized narrative submitted in the single provider request. Each distinct excerpt is stored once and may support multiple semantic subjects.

An `EvidenceSupport` links one evidence excerpt to exactly one proposition, relationship, or uncertainty record and identifies a bounded role: `supports_assertion`, `supports_negation`, `supports_supersession`, `supports_conflict`, or `supports_uncertainty`. A support role must be coherent with its subject type.

Every proposition, relationship, and uncertainty requires at least one evidence support. Multiple excerpts may support one subject, and one excerpt may support multiple subjects through separate support records. Evidence ordering does not establish strength or credibility.

Exact excerpt text is sufficient authoritative semantic evidence for the successor. Character offsets, line numbers, and normalized-to-raw position maps are absent from the authoritative envelope because normalization can change positions and the repository demonstrates no operational need for offsets. A runtime may derive an exact-match locator for display or artifact provenance only when deterministic; such a locator is non-authoritative, not evaluation truth, and must never replace the excerpt.

### 6.14 Attribution

Attribution is optional and present only when the narrative explicitly attributes an assertion. It contains one `source_kind` from `patient`, `staff`, `witness`, or `unspecified`, and an optional `source_ref` to an entity in the envelope.

`source_ref` is used when the narrative distinguishes the source sufficiently to maintain competing accounts. `source_kind=unspecified` is used for an explicitly mentioned but unclassified source. Absence of attribution means the narrative assertion is unattributed; it is not an unknown source object.

Attribution records who is reported as making an assertion, not whether it is true. They cannot contain credibility, confidence, rank, reliability, authority, or adjudication fields. Attribution is provider-extracted, validated, available to presentation and evaluation, and unavailable as a policy weighting mechanism.

### 6.15 Extraction Metadata

Extraction metadata is artifact provenance only. It may contain provider/model identity, extraction-contract identity, request identity, and provider-reported confidence for the response as a whole if later implementation retains that observation. It must not contain semantic facts, policy fields, workflow actions, recommendations, or participant credibility.

Provider confidence is optional artifact provenance, never deterministic truth, never a semantic comparison field, and never policy input. The envelope's normalized-input binding and exactly-one-request count are recorded by surrounding pipeline provenance rather than inferred from provider metadata.

## 7. Bounded Vocabularies

| Concept | Closed vocabulary | Absence and unknown rule |
|---|---|---|
| Entity kind | `person`, `people_collective`, `object`, `unspecified` | `unspecified` is explicit unknown; omission is invalid for an entity. |
| Conduct kind | `physical_conduct`, `threat_expression`, `threatening_movement`, `contact_only`, `undetermined` | `undetermined` is explicit unknown; no null. |
| Target kind | `entity`, `self`, `none`, `undetermined` | `none` is explicit inapplicability; `undetermined` is explicit unknown. |
| Derived direction | `interpersonal`, `object-directed`, `self-directed`, `undetermined` | Never provider-authored; no null. |
| Completion | `threatened`, `attempted`, `completed`, `not_applicable`, `undetermined` | `not_applicable` differs from unresolved. |
| Contact | `occurred`, `did_not_occur`, `undetermined`, `not_applicable` | No boolean or null substitute. |
| Temporal scope | `current_incident`, `historical`, `undetermined` | Mixed content requires multiple propositions. |
| Assertion status | `affirmed`, `negated`, `uncertain` | Correction and dispute require relationships. |
| Intentionality | `intentional`, `accidental`, `undetermined`, `not_applicable` | `not_applicable` only when intent has no meaning for the conduct. |
| Relationship kind | `negates`, `supersedes`, `conflicts_with` | No free-form relationship type. |
| Uncertainty dimension | `actor_identity`, `target_identity`, `conduct_type`, `direction`, `contact`, `completion`, `intentionality`, `temporal_scope`, `threat_meaning`, `assertion_status` | No free-form authoritative dimension. |
| Evidence support role | `supports_assertion`, `supports_negation`, `supports_supersession`, `supports_conflict`, `supports_uncertainty` | Notes cannot substitute for support. |
| Attribution source kind | `patient`, `staff`, `witness`, `unspecified` | Attribution omission means unattributed prose. |

No vocabulary has an implicit default. Unknown and inapplicable are distinct. Optional fields are omitted only when the concept is absent, such as unattributed prose or no source reference; they are not used to avoid an explicit `undetermined` or `not_applicable` value.

## 8. Identity and Reference Rules

1. All identifiers are non-empty strict strings, unique within their collection, and have envelope-local scope only.
2. Canonical identifier forms are `ENT-####` for entities, `PROP-####` for propositions, `REL-####` for relationships, `UNC-####` for uncertainties, `EVID-####` for evidence excerpts, and `SUP-####` for evidence supports, using one-based, zero-padded sequence numbers.
3. Sequence numbers follow canonical collection order. Gaps, duplicates, alternate prefixes, and identifier reuse across concept types are invalid.
4. Entity and proposition order follows first appearance of their earliest supporting exact excerpt in the normalized narrative. When one excerpt introduces multiple subjects, their order follows their appearance within the excerpt; an inseparable tie uses bounded vocabulary order and then identifier order. Relationship and uncertainty order follows the first endpoint proposition, then relationship or dimension vocabulary order, then remaining endpoint. Evidence excerpt order follows first exact occurrence in normalized narrative, with longer excerpt first for the same start and lexical order as the final tie-breaker. Evidence supports order by evidence identifier, subject kind, subject identifier, and support role.
5. Identifiers are stable within one serialized envelope and all artifacts derived from it. They are not cross-run real-world identities and must not be used to merge people or propositions across incidents.
6. Every actor, target, and attribution source reference must resolve to an entity in the same envelope. Every relationship endpoint must resolve to a proposition. Every uncertainty must resolve to a proposition. Every evidence support must resolve to both its evidence excerpt and subject.
7. Dangling references, ambiguous references, cross-incident references, and self-referential relationships are invalid.
8. The same exact evidence excerpt may have one identifier and many support records. Duplicate evidence-excerpt records with identical text and identical first occurrence are invalid.
9. Empty collections are explicit and have only the meanings defined in Section 5. A missing collection is invalid.

## 9. Relationship Rules

`negates` and `supersedes` are directed. `conflicts_with` is semantically symmetric but recorded once with the lexically smaller proposition identifier first. Reverse duplicates and repeated endpoint pairs of the same relationship kind are invalid.

A `negates` relationship originates at a proposition with `assertion_status=negated`. Its target must describe the explicitly opposed assertion. It cannot point to itself or be used to negate every proposition in an incident.

A `supersedes` relationship originates at the later replacing or retracting proposition and points to the earlier proposition. Both endpoints must have evidence supporting their narrative presence, and the relationship requires correction evidence. A proposition may supersede more than one earlier proposition when the narrative explicitly does so. An earlier proposition may have more than one replacement only when separate later assertions explicitly replace different dimensions; otherwise the state is invalid rather than repaired.

Supersession graphs must be acyclic. The active assertion set contains propositions with no incoming `supersedes` relationship, plus non-superseded competing assertions. Correction never deletes or mutates the earlier proposition.

A `conflicts_with` relationship joins two distinct, non-identical assertions whose accounts cannot both hold on at least one stated dimension. It must list one or more bounded disputed dimensions. It is invalid between exact semantic duplicates or between a proposition and a proposition that merely supplies additional compatible detail. Conflict does not make either endpoint inactive.

Negation and conflict may coexist when one account denies another. Supersession and conflict may coexist only when the narrative explicitly preserves a conflict after correction; a superseded-only disagreement is not active conflict. Duplicate semantic relationships with different identifiers are invalid. Cycles are prohibited for `supersedes`; symmetric conflict pairs do not constitute cycles, and directed negation cycles are invalid because they cannot express a coherent scoped denial.

## 10. Authority and Derivation Map

| Concept | Provider-extracted content | Deterministic derivation | Schema validation | Domain validation | Policy use | Presentation use | Evaluation use | Prohibited authority |
|---|---|---|---|---|---|---|---|---|
| Envelope identity | Schema and incident identifiers in the response contract | Input/envelope identity match | Exact shape, supported versions | None beyond binding | Version gate only | May label version | Required provenance | Cannot select policy outcome |
| Entity reference | Kind and narrative-grounded label | Canonical order only | Type, ID, enum, extras | Reference/role coherence | Only through typed derived view | May display label | Expected entities and differences | No universal identity or credibility |
| Proposition | Actor, conduct, target, completion, contact, time, intent, status | Direction and active membership | Required fields and enums | Cross-field coherence | Validated active semantics only | May summarize | Expected proposition authority | No document outcome or workflow action |
| Direction | None | From target structure and entity kind | Derived-view shape | Derivation input coherence | Permitted typed input | May display | Expected deterministic value | Provider cannot author it |
| Negation | Negated proposition and explicit link when applicable | Relationship canonicalization | Endpoint shape | Status and endpoint coherence | Validated active view | May explain | Expected status/link | No global negation |
| Supersession | Earlier/later propositions and link | Active assertion set | Endpoint shape | Direction, evidence, acyclicity | Superseded content excluded unless policy version explicitly consumes history | May show correction history | Expected link and active set | No deletion or truth repair |
| Conflict | Both assertions, dimensions, attribution | Symmetric canonical pair | Endpoint/dimension shape | Non-identity and evidence coherence | Validated conflict view | May show competing accounts | Expected relationship | No credibility ranking or winner |
| Uncertainty | Proposition, bounded dimension, evidence | Material candidate flags may be derived | ID, enum, reference | Field/dimension coherence | Structured dimensions only if policy version permits | Note may explain | Expected records; notes non-authoritative | No provider-confidence substitution |
| Evidence excerpt | Exact normalized-narrative text | Containment and canonical order | Non-empty strict text and IDs | Exact containment and coverage | Provenance only, not semantic inference | May quote exact text | Expected support and containment | No fuzzy repair or translated legacy evidence |
| Evidence support | Subject, excerpt, bounded role | Canonical order | Reference shape | Subject/role coherence and coverage | No independent outcome authority | May group evidence | Expected many-to-many links | No evidence weighting |
| Attribution | Explicit source kind and optional source ref | None | Enum/reference shape | Narrative-account coherence encoded by links | Cannot weight policy | May identify reported account | Expected attribution when asserted | No credibility or truth adjudication |
| Extraction metadata | Provider/model/request provenance and optional confidence | Request count from pipeline provenance | Strict bounded fields | None | Not available | May display provenance | Observed artifact only | No semantics, policy, or ground truth |
| Admissibility status | None | Stage result from validators | Structural pass/fail | Domain pass/fail | Gates policy | May display | Expected success/failure | Provider cannot author final admissibility |
| Candidate indicators | None | From validated active propositions and relationships | Typed/versioned view | Inputs already admissible | Permitted policy input | Optional summary | Expected derived paths where asserted | No free-form or confidence inputs |
| Policy decision | None | Policy engine only | Separate policy contract | Separate policy input validation | Authoritative only in policy boundary | May label | Expected policy outcome separately | Not semantic or provider authority |
| Display summary | None | Presentation mapper only | Presentation contract | None | None | Presentation-only | Not ground truth | Cannot feed validation or policy |

## 11. Structural Admissibility Rules

Schema validation performs no violence-domain reasoning. It must establish all of the following atomically:

- the candidate is a provider-independent value, not a provider SDK or provider-model object;
- exact envelope shape, supported schema identity and version, required fields, required collections, and forbidden extras;
- strict primitive types with no coercion;
- bounded enum membership and explicit `undetermined`/`not_applicable` values rather than silent defaults;
- non-empty identifiers and exact identifier form;
- unique identifiers within and across their applicable namespaces;
- exact proposition, target, entity, relationship, uncertainty, evidence, support, attribution, and metadata shapes;
- all reference existence and reference type correctness;
- collection order and sequential identifier agreement;
- non-empty exact evidence strings and non-empty required support collections;
- explicit empty collection semantics rather than omitted collections;
- absence of unbounded dictionaries, ad hoc stage payloads, provider SDK objects, policy fields, workflow fields, Salesforce fields, comparison fields, recommendations, and final admissibility fields; and
- absence of implicit defaults and unsupported nullable values.

On any issue, schema validation returns ordered typed issues, exposes no structurally admissible envelope, does not run domain validation, and performs no repair.

## 12. Domain Admissibility Rules

Domain validation accepts only a schema-admissible envelope and applies deterministic rules without inference, repair, defaulting, source ranking, or policy evaluation. It must enforce:

1. **Actor/action/target coherence.** Every proposition has an actor reference. Unknown actors use an `unspecified` entity. Entity targets resolve exactly as required by target kind; self targets do not carry a second reference.
2. **Direction coherence.** Interpersonal direction requires a person or people-collective target distinct from a known actor. Object-directed direction requires an object target. Self-directed direction requires `target_kind=self`. Unresolved identity yields `undetermined`, never a guessed direction.
3. **Conduct/completion coherence.** `threat_expression` may use `threatened` or `undetermined`, not `attempted` or `completed` physical conduct. `physical_conduct` may use `attempted`, `completed`, or `undetermined`. `contact_only` uses `completed`. `threatening_movement` may be `not_applicable` or `undetermined` unless the narrative proposition separately establishes an attempt.
4. **Completion/contact coherence.** Attempted person-directed physical conduct requires `did_not_occur` contact with that target. Completed person-directed physical conduct requires `occurred`. Completed object- or self-directed conduct requires occurred contact with its scoped target when the conduct entails striking/contacting that target. Any unresolved exception must be represented as `undetermined`, not a contradictory definite pair.
5. **Threat/contact coherence.** A pure threat expression uses `not_applicable` contact. Contact described elsewhere requires a separate proposition. Threatening movement cannot be upgraded to attempted physical conduct merely because contact did not occur.
6. **Accidental conduct.** `intentionality=accidental` is valid for contact-only or physical conduct but cannot itself establish interpersonal violence. Validation only checks the encoded combination; policy determines its treatment.
7. **Negation validity.** A negated proposition is scoped independently. Any `negates` relationship originates from it, targets a distinct proposition, and has negation evidence. No global cancellation is allowed.
8. **Supersession validity.** The replacement-to-earlier direction, correction evidence, endpoint ordering, and acyclic graph are required. Replaced propositions remain present but inactive.
9. **Conflict validity.** Conflict endpoints are distinct, separately evidenced assertions with at least one bounded disputed dimension. Attribution may differ but is not required. Exact duplicates cannot conflict.
10. **Temporal consistency.** One proposition has one temporal scope. Current and historical content in one narrative must remain separate. A timing correction must supersede, not mutate, the earlier temporal assertion.
11. **Uncertainty scope.** Every uncertainty dimension must be applicable to its proposition and correspond to an explicit unresolved semantic value or an explicit conflict on that dimension. `direction` uncertainty is valid only when its deterministic inputs cannot resolve direction; `threat_meaning` is valid only for threat expression, threatening movement, or undetermined conduct.
12. **Evidence.** Every proposition, relationship, and uncertainty has required support. Every excerpt is an exact substring of the normalized narrative. Whitespace-only, fabricated, fuzzy-matched, or semantically repaired evidence is invalid.
13. **Contradiction rejection.** Definite values that cannot coexist under these rules are rejected rather than reconciled. Uncertainty cannot be used to excuse an otherwise definite contradiction.
14. **Active-set safety.** Superseded propositions are excluded from the derived active set. Negated and disputed propositions remain active assertions with their status and conflict structure intact; they are not silently converted to affirmed facts.
15. **Policy gate.** No invalid proposition or envelope reaches policy. A single invalid semantic subject fails the entire envelope atomically for the case.

Domain validation does not decide final detection, write disposition, workflow action, clinical meaning, legal meaning, source credibility, or recommended response.

## 13. Deterministic Derivations

Only the following successor semantic views may be derived, using only schema- and domain-admissible typed inputs:

- **Direction:** input is each proposition's target structure, actor reference, and referenced entity kind; output is the Section 6.4 vocabulary.
- **Active assertion set:** input is all proposition identifiers and validated `supersedes` relationships; output is the canonically ordered propositions without incoming supersession edges. No content is deleted.
- **Relationship normalization:** input is validated relationship records; output canonicalizes symmetric conflict endpoint order, rejects duplicates, and preserves directed negation and supersession.
- **Evidence containment status:** input is the normalized narrative and each exact evidence excerpt; output is contained/not-contained plus deterministic first-match provenance outside semantic truth. Non-contained evidence fails domain validation.
- **Proposition admissibility status:** input is ordered schema and domain issue results; output is an envelope-level pass/fail carrier. Provider output cannot author it.
- **Policy candidate view:** input is the validated active assertion set, derived directions, scoped status/completion/contact/time/intentionality, bounded uncertainty, and conflict relationships; output is a typed and separately versioned policy-input view. It may expose aggregate candidate indicators such as presence of active current interpersonal propositions or active bounded uncertainty, but those indicators are not semantic fields and do not decide policy outcomes.

Derivation may not use free-form labels, extraction notes, provider confidence, presentation text, regex output, Salesforce output, observed evaluation output, or legacy global findings. It may not infer missing semantics, repair invalid content, create new propositions, or conduct a second model pass.

## 14. Policy Input Boundary

Policy receives exactly one of two typed inputs: an explicit upstream failure provenance, or a validated successor envelope accompanied by its versioned deterministic policy candidate view. It never receives a raw provider response, provider object, unvalidated candidate, compatibility finding, free-form uncertainty note, provider confidence, regex match, presentation summary, or Salesforce payload.

Policy may inspect active propositions, their derived directions, bounded scoped attributes, explicit assertion statuses, validated conflict/supersession structure, and bounded uncertainties only when those fields are included in its declared input-contract version. It may not parse labels or notes, infer absent semantics, rank attributions, or treat confidence as truth.

Superseded propositions are unavailable as active policy facts. If a future policy version requires knowledge that a correction occurred, it may consume a deterministic typed `correction_present` indicator derived from validated supersession, while the superseded content remains non-active. Historical, object-directed, self-directed, negated, disputed, uncertain, and accidental propositions remain available only as explicitly typed context; their existence does not automatically produce an interpersonal violence result.

Policy outcome, reason, failure provenance, Salesforce disposition, evaluation classification, and workflow action remain outside semantic authority. This specification deliberately does not define the final policy state enumeration.

## 15. Evaluation Contract Requirements

Successor evaluation authority must be repository-authored, strict, provider-independent, synthetic-only, and schema-versioned. Each case must contain a stable case identifier, the raw synthetic narrative, successor evaluation-schema identity/version, successor semantic-schema identity/version, and ordered asserted expectations.

For semantic success, expectations must represent:

- the complete ordered expected entity set;
- the complete ordered expected proposition set and proposition-scoped fields;
- expected derived direction for each proposition;
- expected negation, supersession, and conflict relationships;
- expected bounded uncertainties;
- expected exact evidence excerpts and many-to-many support links;
- expected attribution only where explicitly asserted by the narrative;
- the expected active assertion set;
- expected structural and domain validation success; and
- expected policy outcome and reasons as a separate policy expectation, never as semantic content.

For expected failure, the case must assert schema or domain failure and ordered bounded issue paths/codes, or explicitly mark a field as intentionally unasserted. Asserted and intentionally unasserted fields are mutually exclusive. Omission alone never means intentionally unasserted.

Comparison paths use stable identifier-addressed forms such as proposition, entity, relationship, uncertainty, and evidence identifiers followed by bounded field names. Differences separately classify missing expected subject, unexpected observed subject, scalar mismatch, collection mismatch, relationship mismatch, evidence omission, unsupported evidence, validation mismatch, and policy mismatch. Provider confidence and free-form notes are excluded from semantic equality.

Canonical case order is stable case identifier order. Within each expected envelope, Section 8 ordering applies. Expected ground truth cannot be created, repaired, or updated from provider, model, regex, application, compatibility, policy, comparison, baseline, or observed run output.

Successor runs, baselines, comparisons, and reports require new identities and the successor evaluation schema. Historical artifacts route to their creation-time loaders and comparators. Cross-schema comparisons are non-comparable unless a separately authorized comparator defines a lossless relationship; no such comparator is defined here.

## 16. Serialization and Versioning

The successor semantic schema identity is `violence-checker.proposition-semantics`; its initial version is `1.0.0`. The distinct identity prevents confusion with the current global semantic schema despite the initial semantic version number.

Serialization must be UTF-8, deterministic, strict, and lossless for every authoritative value. Object keys use a single contract-defined order or canonical sorted-key encoding consistently. Collections use the canonical order in Section 8 and must never be reordered by presentation preference. Enum values serialize exactly as specified. Identifiers and reference values are preserved exactly.

No field has an implicit default. Required fields and collections are always present. An absent optional concept is omitted only where this specification permits absence. Explicit semantic unknown uses `undetermined`; semantic inapplicability uses `not_applicable` or `none` as defined. Null cannot substitute for either. Empty collections are serialized explicitly and mean only that the relevant collection has no members.

Versioning follows semantic-version rules within the schema identity:

- patch versions may clarify validation or serialization without changing accepted semantic values;
- minor versions may add optional, bounded, backward-readable content without changing existing meaning;
- major versions are required for changed meaning, required fields, vocabularies, identity rules, relationship semantics, or validation behavior that rejects previously admissible envelopes.

Every consumer declares supported schema identity and version before reading content. Unsupported identity/version fails closed without inference or compatibility guessing. A version adapter, if separately authorized, must be deterministic, lossless for authoritative semantics, explicit in provenance, and must terminate before current semantic authority. No permanent dual-write is allowed.

## 17. Legacy Artifact Boundary

Current `SemanticFacts`, `ViolenceFinding`, compatibility findings, corpus records, runs, baselines, comparisons, reports, and preview payloads remain creation-time legacy schemas. They may be read only through schema identity/version and artifact creation-time routing. They do not govern successor execution and cannot be accepted as the current semantic envelope.

Historical artifacts must not be rewritten, reserialized, relabeled, rebaselined in place, or enriched with successor fields. Legacy observed evidence must not be translated into successor evidence because its global excerpts lack proposition-scoped support relationships and such translation would invent authority. Legacy confidence, uncertainty labels, compatibility classifications, and policy outcomes remain observations under their creation-time contracts.

The successor requires new run identities, baseline identities, comparison identities, report identities, corpus/evaluation schema versions, and loaders. Any bounded legacy reader terminates at the historical display or comparison boundary and cannot feed successor policy as current semantics. There is no permanent shadow model or dual-write.

## 18. Resolution of Design-Basis Open Questions

### A. Assertion attribution

The minimum representation is optional proposition attribution with bounded source kind (`patient`, `staff`, `witness`, `unspecified`) and an optional envelope-local source entity reference. Explicitly attributed competing accounts use separate propositions and, when distinguishable, separate source references. Unattributed narrative assertions omit attribution. No credibility, source ranking, truth adjudication, or participant-management system is introduced.

### B. Evidence locator

Exact excerpt text from the normalized inference narrative, linked to semantic subjects, is sufficient. Authoritative character offsets or other locators are absent because formatting-only normalization may change raw positions and the repository establishes no offset requirement. Deterministic runtime locators may be derived for display/provenance only; they are non-authoritative and cannot replace exact excerpts. Raw narrative remains the evidence authority.

### C. Contextual propositions

Historical, object-directed, self-directed, negated, corrected, and disputed content remains represented as independently scoped propositions. Supersession determines activity; direction, temporal scope, assertion status, conflict, and uncertainty retain context. None automatically governs interpersonal violence. Only validated active semantics cross the policy boundary, and policy independently determines their operational treatment.

### D. Uncertainty vocabulary

The bounded dimensions are actor identity, target identity, conduct type, direction, contact, completion, intentionality, temporal scope, threat meaning, and assertion status. They cover the demonstrated participant, action, contact, intent, timing, threat-meaning, and competing-assertion cases without an extensible free-form taxonomy. Optional explanatory notes are presentation/extraction context only and are excluded from policy and semantic equality.

## 19. Boundedness Assessment

| Review question | Result | Basis |
|---|---|---|
| All directly demonstrated distinctions represented? | Pass | Proposition scope covers compound, direction, completion/contact, time, negation, correction, conflict, uncertainty, attribution, and evidence cases. |
| Unrelated hospital-event ontology avoided? | Pass | Conduct and entity vocabularies are limited to violence-boundary distinctions. |
| Source credibility and truth adjudication avoided? | Pass | Attribution records source only; conflict retains both assertions. |
| One semantic authority preserved? | Pass | Only the validated successor envelope is current authority. |
| Global semantic shadow fields avoided? | Pass | Aggregate indicators are typed policy derivations, not semantic fields. |
| Permanent dual-write avoided? | Pass | Legacy schemas are creation-time readers only. |
| Deterministic validation/policy separation preserved? | Pass | Structural, domain, derivation, and policy responsibilities are independently bounded. |
| Historical artifact immutability preserved? | Pass | No translation or in-place rewrite is permitted. |
| Exactly one provider request preserved? | Pass | All semantic content is extracted in one response; no second pass exists. |
| Implementation can proceed without new semantic concepts? | Pass | Concepts, fields, vocabularies, references, authority, validation, derivation, evaluation, and versioning are specified. |
| Remaining questions non-blocking? | Pass | Section 22 records none. |

The specification remains bounded to the 48-case violence-detection evidence. It does not add injury scope, source credibility, general temporal logic, causal inference, motive, workflow, recommendations, or broader clinical/legal taxonomies.

## 20. Implementation Constraints

A later implementation must preserve the exact authority and behavior boundaries specified here. It must not:

- retain `ViolenceFinding` or an equivalent global record as coequal current authority;
- implement permanent dual-write or a shadow semantic model;
- use ad hoc dictionaries between provider, validation, derivation, policy, presentation, or evaluation stages;
- permit provider-specific objects beyond the provider boundary;
- permit the provider to author admissibility, policy outcomes/reasons, workflow actions, Salesforce dispositions, comparison results, evaluation classifications, clinical/legal/safety recommendations, or human-review decisions;
- infer, repair, or silently default invalid semantics during validation;
- parse free-form notes or confidence in deterministic policy;
- add a second provider or semantic inference pass;
- change raw-narrative authority or make normalization semantic;
- rewrite historical artifacts or translate legacy excerpts into proposition support;
- migrate corpus, evaluation, policy, preview, presentation, compatibility, tests, or active pipeline behavior without separate authorization; or
- expand this contract into unrelated domains.

Implementation must fail closed at unsupported schema versions and validation failures. It must preserve exactly one provider request per valid single case and produce no policy input when any successor proposition or relationship is inadmissible.

## 21. Acceptance Criteria for the Specification

This specification is accepted as design-complete when review confirms:

- all 23 required sections are present;
- all four design-basis questions are explicitly resolved;
- one proposition-oriented current semantic authority is defined;
- every required concept has purpose, authority, optionality, validation, derivation, consumption, and prohibited-use rules;
- closed vocabularies distinguish unknown, inapplicable, and absent values;
- proposition, entity, evidence, uncertainty, and relationship identities and canonical order are defined;
- negation, supersession, and conflict direction, duplicates, cycles, active-set behavior, and evidence linkage are defined;
- structural validation and violence-domain validation remain independent and non-inferential;
- deterministic derivations have exact typed inputs and exclusions;
- policy consumes only validated successor semantics and typed versioned views;
- evaluation represents asserted and intentionally unasserted expectations, stable paths, evidence, validation, policy, and synthetic-only authority;
- serialization, schema identity, versioning, failure behavior, and legacy routing are explicit;
- historical artifacts remain immutable and legacy contracts are non-authoritative for current execution;
- exactly-one-provider-request behavior remains invariant;
- no executable code, schema implementation, migration, corpus change, or active-pipeline authorization is present; and
- the boundedness assessment passes with no blocking unresolved semantic question.

## 22. Unresolved Questions

None. Repository evidence and the minimum bounded decisions in this specification resolve all questions required for successor implementation. Any later implementation choice that does not change these semantics is an implementation detail, not an unresolved semantic question.

## 23. Conclusion

The successor architecture is one versioned incident envelope containing proposition-scoped violence semantics, bounded entity references, explicit assertion relationships, bounded uncertainty, and exact linked narrative evidence. Deterministic validation gates it; deterministic derivation produces direction, activity, containment, and versioned policy inputs; policy and presentation remain separate authorities.

The design preserves raw-narrative authority, formatting-only normalization, one provider request, provider-boundary termination, strict failure behavior, independent evaluation truth, and immutable historical artifacts. It replaces document-level semantic authority without introducing a second long-term model or expanding beyond demonstrated violence-detection needs.
