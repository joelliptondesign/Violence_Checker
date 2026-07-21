# True North Semantic Contract Specification

## Purpose

This specification defines the minimal incident-fact contract for a planned successor to the current proposition-oriented runtime. It translates `workplace_violence_doctrine.md` into explicit fields, evidence rules, validation requirements, deterministic derivations, and authority boundaries.

The contract is a target design, not executable code and not current runtime truth.

## Design Principles

1. Represent only distinctions with operational, evidence-integrity, deterministic-policy, or operator-communication value.
2. Keep semantic incident facts separate from repository bookkeeping and provider observations.
3. Require exact, fact-level evidence for every material assertion.
4. Preserve corrections and unresolved contradictions with narrow references rather than a general-purpose graph.
5. Reject or explicitly preserve uncertainty; never repair a candidate into affirmed truth.
6. Derive policy and incident summaries deterministically from validated facts.
7. Prefer a smaller replacement contract over legacy compatibility.

## Authority Boundaries

| Boundary | Authority |
| --- | --- |
| Raw normalized narrative | Evidence text and exact-excerpt containment |
| Provider | Candidate incident facts, candidate evidence links, and candidate uncertainty only |
| Repository adapter | Schema identity, schema version, incident identity, canonical fact/evidence identifiers and ordering, resolution status, extraction bookkeeping |
| Schema and evidence validators | Admissibility; rejection or explicit unresolved preservation |
| Validated contract | Sole successor semantic truth |
| Deterministic derivation | Active fact set, incident direction, and material uncertainty only; local indexes have no contract authority |
| Deterministic policy | Sole authority for the four classification outcomes |
| Communication layer | Presentation-only restatement of a bounded validated projection |

Provider confidence and prose have no repository, policy, or communication-fact authority. The provider may not return a policy outcome, a free-standing conclusion that violence is absent, or repository-owned analysis-completeness status.

## Target Contract Overview

The target semantic payload has one ordered `facts` collection. Each fact is independently evidence-linked and carries the material attributes required by doctrine:

```yaml
schema_identity: violence-checker.true-north-incident-facts
schema_version: 1.0.0
incident_id: repository-assigned
facts:
  - fact_id: repository-assigned
    conduct: verbal_threat | physical_attempt | physical_contact | self_harm | property_violence
    direction: interpersonal | self_directed | object_directed | unknown
    intentionality: intentional | accidental | unresolved
    temporal_scope: current | historical | unresolved
    assertion_status: affirmed | denied | disputed | unresolved
    resolution_status: active | superseded
    supersedes_fact_id: optional repository-remapped fact reference
    contradiction_group: optional repository-remapped narrow group identifier
    evidence:
      - excerpt: exact narrative substring
        supports: [one or more material attributes]
    uncertainty: [zero or more unresolved material attributes]
```

`incident_direction` is a deterministic projection, not a second provider-authored semantic field. It uses the full direction vocabulary, including `multiple`, over active qualifying fact candidates. Extraction metadata, provider identifiers, timestamps, request IDs, ordering keys, validation results, and analysis-completeness status remain outside `facts`.

The surrounding repository pipeline records `processing_status` (`admissible` or `failed`) and `completeness_status` (`complete` or `incomplete`) as repository-owned, non-semantic bookkeeping. These values report whether the governed extraction and validation process completed sufficiently for deterministic evaluation; they do not assert that violence occurred or did not occur. An empty `facts` collection has no policy meaning without this status.

## Field Definitions

| Field | Operational meaning | Provider authority | Repository authority | Evidence requirement | Deterministic derivation | Policy relevance | Communication relevance | Presence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `conduct` | The doctrinal qualifying-conduct distinction asserted by this fact | Candidate value or `null` only for explicit unresolved distinction | Validate or reject; never upgrade | Direct support for the exact conduct distinction, or support for potentially qualifying unresolved conduct | None | Required to test qualification | May be stated only when projected | Required; nullable only with `uncertainty: [conduct]` |
| `direction` | Direction of this conduct fact | Candidate value when evidenced; `unknown` otherwise | Validate evidence and derive incident aggregate | Required when explicitly stated; `unknown` needs no invented target | `incident_direction` derives from active facts | Unknown alone does not change detection | May be stated only when projected | Required |
| `intentionality` | Whether conduct was intentional, accidental, or unresolved | Candidate value | Validate or reject | Required because intent is material | No presumption from contact or severity | Only `intentional` can qualify; unresolved may yield `Uncertain` | May be stated only when projected | Required |
| `temporal_scope` | Whether conduct belongs to the current incident | Candidate value | Validate or reject | Required for `current` or `historical` | No inference from document placement alone | Only `current` can qualify; unresolved may yield `Uncertain` | May distinguish historical from current | Required |
| `assertion_status` | Whether the conduct claim is affirmed, denied, disputed, or unresolved | Candidate value | Validate conflicts and correction state | Required for the asserted state | May become `disputed` only from explicit unresolved contradictory evidence | Only active `affirmed` facts can qualify | May explain denial/dispute without resolving it | Required |
| `resolution_status` | Whether the fact controls now or has been superseded | None | Repository derives the value from validated candidate correction references | Supersession requires correction evidence on the later fact | A referenced earlier fact becomes `superseded`; otherwise `active` | Policy reads active facts only | May explain a supported correction | Required in repository envelope; absent from provider response |
| `evidence` | Exact excerpts and the material attributes each excerpt supports | Candidate excerpts and links | Verify containment, specificity, consistency, and coverage | At least one link; together links cover every material asserted attribute | IDs/order may be assigned; meaning may not be invented | Establishes admissibility | Not passed through unless explicitly needed and safely bounded | Required, non-empty |
| `uncertainty` | Material dimensions explicitly unresolved for this fact | Candidate dimensions | Validate correspondence to unresolved/disputed values and evidence | Each dimension requires supporting ambiguity or conflict evidence | Material-uncertainty projection is deterministic | Material unresolved dimensions may yield `Uncertain` | May explain only projected uncertainty | Required; empty allowed |
| `supersedes_fact_id` | Narrow correction link from a later fact to the earlier fact it replaces | Candidate local reference | Remap and validate later-to-earlier, acyclic reference | Correction/supersession evidence required | Drives `resolution_status` | Prevents stale allegation from qualifying | May support correction explanation | Optional |
| `contradiction_group` | Narrow identity shared by materially conflicting active facts | Candidate local group | Canonicalize and validate group membership | Conflict evidence required for each member | Drives disputed/material-uncertainty projection | Unresolved material group yields `Uncertain` | May state that accounts conflict | Optional |

Fact identity and the two narrow references are structural aids, not independent claims about violence.

## Allowed Values

### `conduct`

- `verbal_threat`: explicit threat of physical violence.
- `physical_attempt`: attempted physical violence without completed physical contact.
- `physical_contact`: completed physical violence.
- `self_harm`: self-directed violence.
- `property_violence`: intentional property-directed violence.

`conduct` may be `null` only when evidence establishes potentially qualifying conduct but cannot establish which listed distinction applies and `uncertainty` contains `conduct`. The contract deliberately omits a generic “violent” value and broad nonqualifying behavior categories.

### Repository analysis status

`processing_status` is `admissible` only after input, provider response, schema, domain, and evidence-integrity validation succeed; otherwise it is `failed`. `completeness_status` is `complete` only when repository validation establishes that the bounded analysis response is complete enough for deterministic classification; otherwise it is `incomplete`. These statuses are not provider fields, semantic facts, evidence about the incident, or conclusions about violence.

### `direction`

- `interpersonal`
- `self_directed`
- `object_directed`
- `unknown`
- `multiple` (deterministic `incident_direction` only)

`multiple` is derived when active facts contain two or more distinct known directions. Atomic facts do not store `multiple`; split them into the smallest separately supportable facts.

### `intentionality`

- `intentional`
- `accidental`
- `unresolved`

### `temporal_scope`

- `current`
- `historical`
- `unresolved`

### `assertion_status`

- `affirmed`
- `denied`
- `disputed`
- `unresolved`

### `resolution_status`

- `active`
- `superseded`

### `uncertainty`

Each value names a material unresolved attribute: `conduct`, `direction`, `intentionality`, `temporal_scope`, or `assertion_status`. `direction` uncertainty alone is non-material to detection if all other qualifying attributes are established.

## Invalid Combinations

Validation must reject at least these combinations:

- `self_harm` with a direction other than `self_directed`.
- `conduct: null` without `uncertainty: [conduct]`, or a settled conduct value paired with conduct uncertainty.
- `property_violence` with `accidental` intentionality.
- `property_violence` with `interpersonal` direction without separate evidence and a separate interpersonal fact.
- `physical_contact` supported by evidence that explicitly states contact did not occur.
- `physical_attempt` supported only by completed-contact evidence without evidence of an attempt distinction.
- Any affirmed fact whose evidence explicitly denies the fact, unless the same linked evidence contains a later supported correction that affirms it.
- `intentional` supported by evidence that describes the conduct as accidental.
- `current` supported only by evidence that describes the conduct as historical.
- `active` on a fact that is the validated target of a later active superseding correction.
- `superseded` without a valid later `supersedes_fact_id` reference and correction evidence.
- `disputed` without a contradiction group or other explicit conflict evidence.
- A contradiction group represented as settled affirmed truth when no supported resolution exists.
- An unresolved material value without the matching `uncertainty` dimension.
- A resolved value paired with the same uncertainty dimension, except `direction: unknown` paired with `uncertainty: [direction]`.
- A stored atomic `direction: multiple`.
- Any evidence link that names no supported attribute, references noncontained text, or purports to support an attribute contradicted by the excerpt.
- Treating an empty fact collection as a negative result without repository-owned `processing_status: admissible` and `completeness_status: complete`.

## Evidence Linkage

Each evidence item contains an exact non-empty substring of the normalized narrative and a non-empty `supports` list drawn from `conduct`, `direction`, `intentionality`, `temporal_scope`, `assertion_status`, `supersession`, and `contradiction`. Resolution status is deterministic bookkeeping and is not an evidence-support label.

The union of a fact's evidence links must cover each policy-relevant asserted attribute. Reuse of one excerpt is allowed only when that excerpt actually supports each linked attribute. A full-narrative excerpt is not blanket support. Exact containment is necessary but not sufficient: validators also apply explicit denial, accident, historical-scope, no-contact, property-direction, correction, and contradiction rules.

Evidence identifiers and canonical ordering may be repository-assigned if the implementation normalizes repeated excerpts. Such bookkeeping cannot change excerpt text or its support meaning.

## Correction Representation

Corrections use only `fact_id`, `resolution_status`, and `supersedes_fact_id`:

1. Preserve the earlier fact and its evidence.
2. Add the later corrected fact with its own evidence.
3. Point the later fact's `supersedes_fact_id` to the earlier fact.
4. Deterministically mark the earlier fact `superseded` and the later controlling fact `active`.
5. Reject cycles, forward-in-time inversions, missing evidence, and more than one active controlling correction for the same material claim.

An allegation followed by a denial is a correction only when the narrative establishes the denial as the supported controlling account. Otherwise encode both accounts as disputed members of a contradiction group. A denial followed by supported confirmation can supersede the denial. Copied-forward language has no extra weight and becomes superseded when a later supported correction controls.

## Contradiction Representation

Unresolved contradictory accounts use a shared `contradiction_group`. Each member retains its own exact evidence. Material members use `assertion_status: disputed` and include the disputed dimensions in `uncertainty`.

The group is deliberately not a general-purpose relationship graph. It carries no causal, temporal, identity, or evidentiary-weight semantics. If a later supported correction resolves the group, the losing facts become superseded and the controlling fact becomes active and settled. Until then, deterministic policy treats a material group as `Uncertain`.

## Deterministic Derivations

After validation, repository code derives:

- `active_facts`: facts not superseded by a valid later controlling correction;
- `active_qualifying_facts`: active facts whose `conduct` is in the allowed qualifying vocabulary;
- `incident_direction`: `unknown` when no active qualifying fact has known direction; the single known direction when all known active qualifying facts share it; `multiple` when they span two or more known directions;
- `material_uncertainty`: unresolved conduct, intentionality, temporal scope, assertion status, or unresolved material contradiction capable of changing the outcome;
- `detected_facts`: active, affirmed, intentional, current qualifying facts;
- a bounded communication projection from validated active facts and the policy decision.

Derivation cannot repair missing evidence, replace unresolved with settled values, or override explicit narrative evidence. Mechanical sets or indexes may be computed locally during evaluation, but they are not separately authoritative contracts, are not serialized as semantic truth, and cannot replace direct policy evaluation of validated facts.

## Deterministic Policy Inputs

Deterministic policy evaluates the validated target facts directly together with repository-owned processing and completeness status. There is no separately authoritative policy-candidate or policy-input aggregate contract. Policy may compute local, non-serialized indexes for execution efficiency only.

The direct inputs are:

- repository-owned processing and completeness status or typed failure state;
- active fact identity;
- conduct;
- direction and derived incident direction;
- intentionality;
- temporal scope;
- assertion status;
- material uncertainty and unresolved contradiction state.

Deterministic precedence is:

1. Failed or incomplete analysis → `Unable to Determine`.
2. Successful admissible complete analysis with unresolved material truth capable of changing classification → `Uncertain`.
3. At least one active, affirmed, intentional, current qualifying fact → `Violence Detected`.
4. Otherwise, successful admissible complete analysis with no active affirmed intentional current qualifying fact and no material unresolved classification fact → `No Violence Detected`.

Unknown direction alone is excluded from material uncertainty at step 2 when step 3 is otherwise satisfied. The fourth result is authored by deterministic policy; it is not carried in provider output or semantic facts. Empty facts alone never prove it.

## Communication Projection

The communication projection is constructed only after validation and deterministic policy. It contains the outcome, bounded reason codes, and only the active fact attributes necessary for Incident Summary, Key Findings, and Why This Result.

The projection excludes raw narrative by default and excludes injury, weapon, security response, property damage, actor identity, target identity, intent, conduct, direction, resolution, and outcome unless the corresponding value is deliberately included from validated truth. In particular, property damage is not implied by `property_violence`; only the validated conduct may be stated unless damage is separately represented by a future authorized contract.

Generated prose must pass factual-consistency checks against the projection. Failure to establish consistency selects deterministic repository-authored fallback text. Communication cannot alter policy or semantic state.

## Provider Response Boundary

The provider response may contain only candidate proposition values, temporary local fact/group references, exact evidence excerpts, support-attribute links, and explicit uncertainty. It must not contain resolution status, repository schema identity/version, incident identity, canonical IDs/order, extraction metadata, processing/completeness status, a free-standing negative conclusion, policy outcome, reason codes, communication prose, or compatibility payloads as authority.

The adapter terminates provider objects and assigns repository bookkeeping before strict validation. Malformed or unsupported output fails closed; no repair request or silent default is allowed.

## Repository Bookkeeping

Bookkeeping remains outside operational facts:

- semantic and extraction schema identities and versions;
- incident ID;
- canonical fact, evidence, contradiction-group, and support IDs;
- canonical ordering;
- fact resolution status derived from candidate supersession references;
- provider/model/request observations and timestamps;
- validation results, repository-owned processing/completeness status, and failure provenance;
- policy identity/version and reason codes;
- serialization and evaluation artifact metadata.

Bookkeeping may establish reference integrity and provenance but cannot establish violence.

## Schema Identity and Versioning

The planned semantic identity is `violence-checker.true-north-incident-facts`, initially `1.0.0`. This identity is distinct from the current `violence-checker.proposition-semantics` schema.

Every consumer declares supported identity and version. Unsupported identity or version fails closed. Additive optional bookkeeping changes may use a compatible version only when semantics do not change. Any change to field meaning, allowed values, evidence obligations, correction behavior, contradiction behavior, or policy interpretation requires a new semantic version and matched evaluation schema.

No adapter may make two schemas coequal current authority. Temporary adapters terminate before the sole current semantic boundary and must be removed at cutover.

## Validation Requirements

Validation is strict, deterministic, provider-independent, and ordered:

1. Validate input and normalized-narrative authority.
2. Validate exact schema identity/version and reject extra or missing required fields.
3. Assign and validate canonical identifiers, ordering, and reference integrity.
4. Confirm every excerpt is an exact narrative substring.
5. Confirm fact-level evidence coverage for material attributes.
6. Apply explicit denial, accident, historical-scope, no-contact, property-direction, correction, and contradiction rules.
7. Validate allowed and invalid field combinations.
8. Validate supersession order, uniqueness, and acyclicity.
9. Validate contradiction-group membership and matching uncertainty.
10. Reject unsupported facts or preserve only explicitly evidenced unresolved state.
11. Assign repository-owned processing/completeness status without treating provider omission or an empty fact collection as a semantic negative conclusion.
12. Permit deterministic classification only after admissibility and completeness gates pass; otherwise return `Unable to Determine`.
13. Evaluate policy directly over validated facts; do not construct or serialize a separate policy-candidate aggregate.

Deterministic validation cannot prove unrestricted natural-language entailment. Adversarial evaluation must test the gap between substring containment and material support.

## Example Valid Contracts

The examples omit repository bookkeeping other than illustrative fact IDs. They are documentation, not executable runtime fixtures.

### Completed interpersonal assault

```yaml
facts:
  - fact_id: fact-1
    conduct: physical_contact
    direction: interpersonal
    intentionality: intentional
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: active
    evidence:
      - excerpt: "He intentionally punched his coworker today."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status]
    uncertainty: []
```

### Self-harm

```yaml
facts:
  - fact_id: fact-1
    conduct: self_harm
    direction: self_directed
    intentionality: intentional
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: active
    evidence:
      - excerpt: "She deliberately struck herself during the incident."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status]
    uncertainty: []
```

### Intentional property violence

```yaml
facts:
  - fact_id: fact-1
    conduct: property_violence
    direction: object_directed
    intentionality: intentional
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: active
    evidence:
      - excerpt: "He intentionally smashed the office monitor during today's incident."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status]
    uncertainty: []
```

### Accidental contact

```yaml
facts:
  - fact_id: fact-1
    conduct: physical_contact
    direction: interpersonal
    intentionality: accidental
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: active
    evidence:
      - excerpt: "The cart accidentally bumped the employee today."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status]
    uncertainty: []
```

This is admissible contact but does not qualify because intentionality is accidental.

### Explicit no qualifying conduct

```yaml
validated_semantics:
  facts: []
repository_analysis:
  processing_status: admissible
  completeness_status: complete
```

This example assumes the bounded narrative “He used profanity but made no threat and had no physical contact.” passed repository validation. The repository status says only that analysis completed; it does not assert absence. Deterministic policy returns `No Violence Detected` from the complete admissible analysis and validated fact state. The empty fact list alone would be insufficient.

### Historical violence

```yaml
facts:
  - fact_id: fact-1
    conduct: physical_contact
    direction: interpersonal
    intentionality: intentional
    temporal_scope: historical
    assertion_status: affirmed
    resolution_status: active
    evidence:
      - excerpt: "She reported that he intentionally punched a coworker last year."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status]
    uncertainty: []
```

### Corrected allegation

```yaml
facts:
  - fact_id: fact-1
    conduct: physical_contact
    direction: interpersonal
    intentionality: intentional
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: superseded
    evidence:
      - excerpt: "The initial report said he intentionally shoved her."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status]
    uncertainty: []
  - fact_id: fact-2
    conduct: physical_contact
    direction: interpersonal
    intentionality: accidental
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: active
    supersedes_fact_id: fact-1
    evidence:
      - excerpt: "The reporter later corrected the account: the contact was accidental."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status, supersession]
    uncertainty: []
```

### Unresolved witness contradiction

```yaml
facts:
  - fact_id: fact-1
    conduct: physical_contact
    direction: interpersonal
    intentionality: intentional
    temporal_scope: current
    assertion_status: disputed
    resolution_status: active
    contradiction_group: conflict-1
    evidence:
      - excerpt: "Witness A said he intentionally punched the coworker today."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status, contradiction]
    uncertainty: [assertion_status]
  - fact_id: fact-2
    conduct: physical_contact
    direction: interpersonal
    intentionality: intentional
    temporal_scope: current
    assertion_status: disputed
    resolution_status: active
    contradiction_group: conflict-1
    evidence:
      - excerpt: "Witness B said the employee did not intentionally punch the coworker today."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status, contradiction]
    uncertainty: [assertion_status]
```

### Unknown-direction threat

```yaml
facts:
  - fact_id: fact-1
    conduct: verbal_threat
    direction: unknown
    intentionality: intentional
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: active
    evidence:
      - excerpt: "During today's incident, the employee deliberately threatened physical violence."
        supports: [conduct, intentionality, temporal_scope, assertion_status]
    uncertainty: [direction]
```

Unknown direction alone does not suppress `Violence Detected`.

### Mixed-direction incident

```yaml
facts:
  - fact_id: fact-1
    conduct: verbal_threat
    direction: interpersonal
    intentionality: intentional
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: active
    evidence:
      - excerpt: "He deliberately threatened to punch his coworker."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status]
    uncertainty: []
  - fact_id: fact-2
    conduct: property_violence
    direction: object_directed
    intentionality: intentional
    temporal_scope: current
    assertion_status: affirmed
    resolution_status: active
    evidence:
      - excerpt: "He then intentionally smashed an office chair."
        supports: [conduct, direction, intentionality, temporal_scope, assertion_status]
    uncertainty: []
derived:
  incident_direction: multiple
```

## Example Invalid Contracts

### Denial used as affirmation

```yaml
conduct: physical_contact
assertion_status: affirmed
evidence:
  - excerpt: "The employee denied making any physical contact."
    supports: [conduct, assertion_status]
```

Invalid because denial evidence cannot support an affirmed contact fact.

### Accident represented as intentional

```yaml
conduct: physical_contact
intentionality: intentional
evidence:
  - excerpt: "The contact was accidental."
    supports: [intentionality]
```

Invalid because the evidence contradicts the asserted intentionality.

### Historical evidence represented as current

```yaml
conduct: physical_contact
temporal_scope: current
evidence:
  - excerpt: "The fight occurred two years ago."
    supports: [temporal_scope]
```

Invalid because historical evidence cannot support current scope.

### No-contact evidence represented as completed contact

```yaml
conduct: physical_contact
evidence:
  - excerpt: "He swung but made no contact."
    supports: [conduct]
```

Invalid because the supported distinction is `physical_attempt`, not `physical_contact`.

### Property evidence used for interpersonal direction

```yaml
conduct: property_violence
direction: interpersonal
evidence:
  - excerpt: "She intentionally kicked the office door."
    supports: [conduct, direction]
```

Invalid because property-directed evidence does not support interpersonal direction.

### Superseded allegation left active

```yaml
facts:
  - fact_id: fact-1
    resolution_status: active
  - fact_id: fact-2
    resolution_status: active
    supersedes_fact_id: fact-1
```

Invalid because the validated target of supersession cannot remain active.

## Open Implementation Choices

The doctrine does not settle these bounded engineering choices:

- Whether evidence is stored inline per fact or normalized into an evidence table plus typed support links. The external semantics and fact-level coverage must be identical.
- Whether source attribution is needed to validate correction precedence or contradiction membership. If introduced, it must be narrow, evidence-backed, and excluded from policy unless doctrine is separately amended.
- The exact schema-version and evaluation-version increment policy beyond the required identity separation and fail-closed routing.
- The deterministic factual-consistency mechanism for generated communication and the conditions that select fallback.

None of these choices may broaden doctrine, weaken evidence integrity, create dual semantic authority, or preserve legacy structures solely for compatibility.
