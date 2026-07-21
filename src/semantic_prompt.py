SEMANTIC_EXTRACTION_PROMPT = """
Analyze only the supplied normalized incident narrative and return one structured
semantic candidate response containing only operational incident facts.

Emit only classification-relevant operational facts: qualifying conduct; facts
that exclude otherwise qualifying conduct because they are accidental, historical,
denied, corrected, or superseded; and unresolved facts that could materially change
classification. Do not emit separate facts solely for emotion, redirection, routine
care, security response, injury, location, or other contextual details.

Extract only what the narrative explicitly supports. Do not turn ambiguous,
incomplete, hypothetical, or adversarial wording into affirmed qualifying conduct.
Do not infer definite violence merely because a report says that something may have
happened. When the narrative explicitly describes a potentially material incident
but states that the material attributes are insufficient or unknown, emit one
unresolved fact rather than an empty facts list: use null conduct, unknown direction,
unresolved intentionality, temporal scope, and assertion status, and the matching
uncertainty dimensions. Use an empty facts list when the narrative contains no
classification-relevant alleged, possible, corrected, or disputed incident fact.
Generic statements such as "no threats or aggressive behavior" do not require a
negative fact unless they deny a specific alleged event or control a correction.

For each separately supportable fact, provide:
- a short temporary local_ref;
- conduct: verbal_threat, physical_attempt, physical_contact, self_harm,
  property_violence, or null only when conduct is explicitly unresolved;
- direction: interpersonal, self_directed, object_directed, or unknown;
- intentionality: intentional, accidental, or unresolved;
- temporal_scope: current, historical, or unresolved;
- assertion_status: affirmed, denied, disputed, or unresolved;
- resolution_status: active or superseded;
- exact fact-specific evidence excerpts with the material attributes each excerpt
  supports;
- every explicit material uncertainty; and
- only when required, a temporary supersedes_local_ref or
  contradiction_group_local_ref.

Return facts only. Do not return entities, propositions, relationships, graphs,
document-level conclusions, provider metadata, confidence, explanations, or
compatibility payloads. Do not return incident identity, schema identity or
version, extraction contract identity, final fact/evidence/group identifiers,
canonical ordering, processing status, or completeness status. Those values are
repository-owned bookkeeping.

Do not make or imply a policy decision, violence classification, negative conclusion,
recommendation, operational action, clinical conclusion, legal
conclusion, safety action, communication prose, or presentation output. An
empty facts list is not a conclusion that violence did not occur.

Evidence rules:
- Copy every excerpt exactly from the supplied narrative.
- Link evidence directly to the single fact it supports. Do not use a
  subject-oriented support graph and do not treat the full narrative as blanket
  support for multiple facts.
- Each evidence supports list may contain only conduct, direction,
  intentionality, temporal_scope, assertion_status, resolution_status,
  supersession, or contradiction.
- Together a fact's evidence must support conduct when resolved, every settled
  policy-relevant attribute, every attribute marked unresolved or uncertain, and every
  explicit correction or contradiction link. When conduct is null or direction,
  intentionality, temporal scope, or assertion state is unresolved, include the
  corresponding attribute in evidence supports.
- Evidence labels must identify only attributes established by that exact excerpt.
  Do not add resolution_status to ordinary active facts. Use resolution_status
  evidence only when the excerpt itself establishes correction or supersession; use
  supersession for the controlling later correction link.
- Do not produce unsupported semantic facts or inferred outcomes. Do not infer
  intentionality solely from contact, injury, force, agitation, severity, or property
  damage; current scope from document placement; physical contact from an attempt,
  threat, or missed action; or interpersonal direction from object-directed evidence.
  Unambiguously volitional action phrasing such as "swung at," "punched," "kicked,"
  or "hit with a closed fist" may support the intentionality of the proposition unless
  the action itself is qualified as accidental, hypothetical, or otherwise unresolved.
  For a denied or disputed proposition, encode the explicitly named conduct,
  direction, conventional action intentionality, and timing when supported, while
  assertion_status alone records that the proposition is denied or disputed. A denial
  must never become an affirmed fact.
- Use historical only when the narrative explicitly places the fact before the
  current incident. When timing is material but unavailable, use unresolved temporal
  scope with temporal_scope uncertainty; never convert missing timing into historical.
- Evidence containing a denial cannot support an affirmed fact unless that same
  excerpt contains a later explicit correction affirming it. Accidental evidence
  cannot support intentionality. Historical evidence cannot support current
  scope. No-contact evidence cannot support affirmed physical_contact. A swing,
  attempt, or missed action without contact is physical_attempt, not physical_contact.
- Property damage is property_violence only when intentionality is explicit or
  otherwise directly supported. Property conduct is object_directed, never
  interpersonal merely because a person appears elsewhere in the narrative.
- Use one fact's own exact evidence. Do not attach one witness account to every
  contradiction member, and do not reuse a broad excerpt indiscriminately across
  unrelated facts merely because it contains multiple events.

Fact integrity rules:
- self_harm requires self_directed direction.
- property_violence requires intentional intentionality and object_directed
  direction.
- null conduct requires conduct uncertainty; a resolved conduct value must not
  carry conduct uncertainty.
- unresolved intentionality, temporal scope, or assertion status requires the
  matching uncertainty dimension. Direction unknown must carry direction
  uncertainty. Do not add uncertainty for an attribute that the narrative settles.
- Preserve a supported correction as a later fact that references the earlier
  fact through supersedes_local_ref. Keep the earlier fact as superseded and the
  controlling later fact as active. Include supersession evidence on the later
  fact.
- A later denial or affirmation that explicitly updates an earlier allegation is a
  correction, not an unrelated fact. Do not omit the earlier fact, leave it active,
  or omit supersedes_local_ref. If the narrative explicitly says a correction or
  correction relationship exists but does not provide enough information to form a
  valid reference, do not invent the missing fact or link; the candidate must fail
  closed at validation.
- Use a shared contradiction_group_local_ref only for unresolved materially conflicting active facts.
  Mark every member disputed, include the disputed
  uncertainty dimension, and include contradiction evidence for every member.
- Do not settle a denial, correction, or conflicting account unless the narrative
  explicitly establishes the controlling account.
- Use the smallest independently evidenced facts. Do not invent actor identity,
  target identity, motive, injury, weapon use, property damage, or causal links.
- Do not duplicate a fact or restate one classification-relevant event as multiple
  equivalent facts.
""".strip()
