# Workplace Violence Doctrine

## Purpose

This document defines the operational doctrine that successor implementations of Violence Checker must apply. It fixes the meaning of workplace violence, the four classification outcomes, evidence integrity, and the authority boundaries between semantic extraction, repository validation, deterministic policy, and operator communication.

It is a specification for later implementation. It does not describe the current runtime as migrated and does not change runtime behavior.

## Authority

This doctrine is the authoritative policy and semantic-design basis for the planned successor state. The current proposition-oriented runtime remains the active implementation until a separately authorized migration passes the gates in `true_north_migration_strategy.md`.

Authority is ordered as follows:

1. Correctness
2. Evidence integrity
3. Stability
4. Explainability
5. Simplicity
6. Performance

No lower-priority objective may weaken a higher-priority objective. Raw incident narrative is the evidence authority. Validated repository facts are semantic truth. Deterministic policy is the sole classification authority. A language model may propose bounded semantic candidates; it may not decide the final outcome.

## Operational Definition

**Violence Detected** means the current reported incident contains at least one active, affirmed, intentional qualifying-conduct fact.

The definition is incident-centered. It includes interpersonal, self-directed, and object-directed violence. Direction describes the incident but does not, by itself, determine whether violence occurred.

## Qualifying Conduct

Qualifying conduct is limited to:

- `verbal_threat`: an explicit threat of physical violence;
- `physical_attempt`: attempted physical violence without completed contact;
- `physical_contact`: completed physical violence;
- `self_harm`: self-directed violence;
- `property_violence`: intentional property-directed violence.

The distinction must be explicit. Profanity, insults, abuse, disturbing language, nonviolent misconduct, ambiguous movement, and contact described only as accidental do not become qualifying conduct without supporting evidence for one of these values.

## Direction

Incident direction uses:

- `interpersonal`: directed toward another person or people;
- `self_directed`: directed toward the actor's self;
- `object_directed`: directed toward property or another object;
- `multiple`: active qualifying facts span more than one known direction;
- `unknown`: the direction cannot be established from admissible evidence.

Direction describes the incident. Unknown direction alone does not force `Uncertain` when conduct, intentionality, temporal scope, assertion state, and active resolution otherwise establish qualifying violence. Conversely, a known direction never turns nonqualifying conduct into violence.

## Classification Outcomes

### Violence Detected

Use when at least one active fact is affirmed, intentional, current, and qualifying. Other nonqualifying or unresolved details do not suppress detection unless they create unresolved doubt about a material attribute of every otherwise qualifying fact.

### No Violence Detected

Use when repository validation establishes a successful, admissible, complete analysis and the validated incident facts contain no active, affirmed, intentional, current qualifying conduct and no material unresolved classification fact. This includes accidental contact, historical-only conduct, a denied allegation superseded by supported correction, profanity without a physical threat, nonviolent conduct, and other supported facts that do not meet this doctrine.

Absence of evidence is not evidence of absence. An empty provider fact list alone is insufficient, and the provider must not author a free-standing negative conclusion. Repository-owned analysis-completeness and admissibility status is non-semantic bookkeeping: it records whether the governed analysis and validation process completed, not whether violence occurred. `No Violence Detected` is a deterministic policy result, not a semantic fact or provider conclusion.

### Uncertain

Use when admissible semantic facts exist but a material fact required for classification remains unresolved. Material uncertainty includes unresolved contradictory accounts, intentionality, current-versus-historical scope, assertion state, or qualifying-conduct distinction. Unknown direction alone is not material when qualifying violence is otherwise established.

### Unable to Determine

Use when the repository cannot obtain a successful, admissible, complete semantic analysis. Causes include invalid input, provider failure, malformed provider output, schema-validation failure, evidence-integrity failure, incomplete analysis, or another pipeline failure that prevents deterministic evaluation.

The outcome distinctions are mandatory:

- `No Violence Detected`: admissible facts establish no qualifying current violence.
- `Uncertain`: admissible facts exist, but semantic truth material to the outcome is unresolved.
- `Unable to Determine`: semantic processing failed before deterministic classification could use admissible facts.

## Intentionality

Intentionality uses `intentional`, `accidental`, or `unresolved`.

Only intentional conduct can satisfy the operational definition. Accidental conduct does not qualify. If intentionality is material and unresolved, the outcome is `Uncertain`; completed contact is not presumed intentional. Intentionality must be directly evidenced or deterministically derived without contradicting the evidence.

## Temporal Scope

Temporal scope uses `current`, `historical`, or `unresolved`.

Only current-incident conduct can produce `Violence Detected`. Historical conduct mentioned in a current nonviolent event does not qualify as current violence. If current-versus-historical scope is material and unresolved, the outcome is `Uncertain`.

A fact narrated as part of the reported incident is `current` unless the narrative explicitly establishes that the fact is historical or the timing is materially ambiguous. Ordinary incident narratives do not require words such as "today," "current," or "this incident" to establish current scope.

Use `historical` only when the narrative explicitly places the conduct outside the reported incident, such as "last month," "previous admission," "history of assault," "previously struck staff," "earlier this year," or "prior incident."

Use `unresolved` only when timing itself is materially unclear, such as conflicting timing accounts, copied-forward documentation with unresolved timing, or insufficient information to determine whether the conduct belongs to the reported event. Missing explicit temporal words alone do not create unresolved temporal scope.

## Assertion and Resolution

Assertion status uses `affirmed`, `denied`, `disputed`, or `unresolved`. Resolution status uses `active` or `superseded`.

- `affirmed` states that the fact is asserted as having occurred.
- `denied` states that the fact is explicitly denied.
- `disputed` states that admissible accounts conflict and no supported resolution controls.
- `unresolved` states that the narrative does not settle whether the fact occurred.
- `active` means the fact remains part of current repository truth.
- `superseded` means a later supported correction replaces the fact for classification.

An affirmed fact qualifies only while active. Denied, disputed, unresolved, and superseded facts cannot independently produce `Violence Detected`.

## Corrections and Supersession

A later supported correction may supersede earlier evidence. The repository must preserve the correction boundary and must evaluate only the active state.

- An allegation followed only by a denial is not silently settled; if the accounts materially conflict without resolution, represent the matter as disputed and classify `Uncertain`.
- A denial followed by a supported confirmation may supersede the denial and leave an active affirmed fact.
- A supported correction replaces the earlier fact for policy; the earlier fact remains traceable but `superseded`.
- A copied-forward statement later corrected must not remain active merely because it appears more than once.
- A quoted threat denied by the alleged speaker remains disputed unless other admissible evidence resolves the conflict. A denial is not automatically controlling, and the quoted words are not automatically treated as an affirmed threat.
- Suspected intentional contact later confirmed accidental leaves the intentional allegation superseded and the accidental fact active.

Superseded allegations must never remain active. Correction handling must not rewrite the narrative or erase provenance.

## Contradictory Accounts

Conflicting witness or source accounts must be represented as an explicit unresolved contradiction when no supported resolution controls. The facts remain admissible as disputed information, but they cannot be represented as settled affirmed truth. A material unresolved contradiction produces `Uncertain`.

A general-purpose relationship graph is not doctrinally required. Narrow fact identity, active/superseded state, optional supersession reference, and contradiction-group identity are sufficient unless later implementation evidence demonstrates otherwise.

## Evidence Integrity

Evidence integrity is repository law. Every affirmed semantic fact must be directly supported by narrative evidence or deterministically derived without contradicting supported evidence. Every policy-relevant material attribute—conduct, intentionality, temporal scope, assertion status, and direction when explicitly available—requires fact-specific support.

The following rules apply:

- Literal excerpt containment is necessary but not sufficient; containment does not establish entailment.
- One full-narrative excerpt does not automatically support every fact.
- Evidence must be linked to the specific fact and material attributes it supports.
- Evidence containing explicit denial cannot support an affirmed fact unless the excerpt also contains a later supported correction that affirms it.
- Evidence describing accidental conduct cannot support intentional conduct.
- Evidence describing historical conduct cannot support current conduct.
- Evidence stating no physical contact cannot support `physical_contact`.
- Property evidence cannot support interpersonal direction without additional evidence.
- Superseded allegations cannot remain active.
- Unresolved contradictions cannot be encoded as settled facts.
- Absence of evidence is not evidence of absence.
- Validation may reject unsupported facts or preserve them only as unresolved; it must not silently convert them to affirmed truth.

Deterministic code cannot prove unrestricted natural-language entailment. The target reduces this risk with constrained fields, fact-level evidence linkage, exact excerpts, explicit contradiction and correction rules, strict validation, deterministic policy, and adversarial evaluation.

## Deterministic Policy Authority

Final classification is a total deterministic function of validated semantic facts plus repository-owned admissibility and analysis-completeness status. Provider confidence, free-form explanations, model-selected labels outside the contract, regex matches, and communication prose have no policy authority. The provider cannot assert that violence is absent or determine `No Violence Detected`.

Policy evaluates validated active incident facts directly; it does not consume a separately authoritative policy-candidate aggregate. Mechanical indexes may exist only as local, non-serialized implementation details inside policy evaluation. Policy must apply the four outcomes consistently: failed or incomplete processing maps to `Unable to Determine`; material unresolved semantic truth capable of changing the classification maps to `Uncertain`; an active affirmed intentional current qualifying fact maps to `Violence Detected`; otherwise successful, admissible, complete analysis with no such fact maps to `No Violence Detected`.

## Communication Authority

The communication layer receives only validated repository truth and deterministic outcome data. Its projection contains only facts needed to produce:

- Incident Summary;
- Key Findings;
- Why This Result.

It must not introduce injury, weapon, security response, property damage, actor identity, target identity, intent, conduct, direction, resolution, or outcome unless that item is present in the validated projection. It may organize and restate projected truth; it may not invent, embellish, infer, contradict, or resolve facts.

Generated communication is presentation-only. Output must pass factual-consistency checks against the projection; if consistency cannot be established, the repository must use a deterministic fallback.

## Explicit Non-Goals

This doctrine does not:

- implement or migrate runtime behavior;
- define clinical, legal, disciplinary, emergency-response, or workplace-intervention action;
- establish injury severity, weapon use, actor identity, target identity, motive, or property damage as required semantic fields;
- treat direction as an independent violence criterion;
- make a language model, regex matcher, or communication generator the policy authority;
- authorize real incident data, deployment, a live-provider run, baseline acceptance, or external-system writes;
- require a general-purpose semantic graph or preserve legacy concepts for compatibility.

## Doctrine Decision Table

| Scenario | Material semantic state | Outcome | Reason |
| --- | --- | --- | --- |
| Explicit threat | Active, affirmed, intentional, current `verbal_threat` | Violence Detected | Explicit threat of physical violence qualifies. |
| Physical attempt | Active, affirmed, intentional, current `physical_attempt` | Violence Detected | Attempted physical violence qualifies without contact. |
| Completed interpersonal contact | Active, affirmed, intentional, current `physical_contact`; interpersonal | Violence Detected | Completed intentional physical violence qualifies. |
| Self-harm | Active, affirmed, intentional, current `self_harm`; self-directed | Violence Detected | Self-directed violence qualifies. |
| Intentional property violence | Active, affirmed, intentional, current `property_violence`; object-directed | Violence Detected | Intentional property-directed violence qualifies. |
| Accidental contact | Active, affirmed, accidental, current contact | No Violence Detected | Intentionality is not satisfied. |
| Historical-only conduct | Active, affirmed, intentional, historical qualifying conduct | No Violence Detected | The current-incident scope is not satisfied. |
| Corrected allegation | Violent allegation superseded by supported active denial or nonviolent correction | No Violence Detected | Superseded allegations do not remain active. |
| Unresolved contradiction | Material accounts remain disputed in one contradiction group | Uncertain | Required semantic truth is unresolved. |
| Profanity without physical threat | Active current abuse with no qualifying conduct | No Violence Detected | Offensive language alone is not qualifying conduct. |
| Insufficient information | No admissible facts because input or semantic processing failed | Unable to Determine | Deterministic evaluation has no admissible semantic input. |
| Qualifying violence with unknown direction | Active, affirmed, intentional, current qualifying fact; direction unknown | Violence Detected | Unknown direction alone does not suppress detection. |
| Mixed-direction incident | Active qualifying facts span at least two known directions | Violence Detected; direction `multiple` | Direction summarizes the incident and does not negate qualifying facts. |

## Acceptance Examples

1. “The employee said, ‘I will punch you,’ and confirmed the statement.” The supported current fact is an intentional affirmed `verbal_threat`: `Violence Detected`.
2. “She swung at a coworker but missed.” The supported current fact is an intentional affirmed `physical_attempt`: `Violence Detected`.
3. “He struck the wall on purpose.” The supported current fact is intentional affirmed `property_violence`: `Violence Detected`, object-directed.
4. “The cart rolled and bumped the employee by accident.” The active fact is accidental contact: `No Violence Detected`.
5. “The report first said he shoved her; the reporter later corrected that no shove occurred.” The alleged contact is superseded by the supported correction: `No Violence Detected`, assuming admissible facts establish no other qualifying conduct.
6. “One witness says he punched a coworker; another says no punch occurred, and the report does not resolve the accounts.” The material assertion remains disputed: `Uncertain`.
7. “The narrative cannot be parsed into a valid evidence-linked contract.” No admissible semantic facts are available: `Unable to Determine`.
8. “During today's calm meeting, the employee disclosed a fight from last year.” The violence is historical only: `No Violence Detected` for the current incident.
