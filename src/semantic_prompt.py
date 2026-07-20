SEMANTIC_EXTRACTION_PROMPT = """
Analyze only the supplied normalized incident narrative and return one structured
semantic candidate response containing only operational incident facts.

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
  material attribute, and every explicit correction or contradiction link.
- Do not produce unsupported semantic facts or inferred outcomes. Do not infer
  intentionality from contact or severity, current scope from document placement,
  or interpersonal direction from property evidence.
- Evidence containing a denial cannot support an affirmed fact unless that same
  excerpt contains a later explicit correction affirming it. Accidental evidence
  cannot support intentionality. Historical evidence cannot support current
  scope. No-contact evidence cannot support physical_contact.

Fact integrity rules:
- self_harm requires self_directed direction.
- property_violence requires intentional intentionality and object_directed
  direction.
- null conduct requires conduct uncertainty; a resolved conduct value must not
  carry conduct uncertainty.
- unresolved intentionality, temporal scope, or assertion status requires the
  matching uncertainty dimension. Direction unknown may carry direction
  uncertainty.
- Preserve a supported correction as a later fact that references the earlier
  fact through supersedes_local_ref. Keep the earlier fact as superseded and the
  controlling later fact as active. Include supersession evidence on the later
  fact.
- Use a shared contradiction_group_local_ref only for unresolved materially conflicting active facts.
  Mark every member disputed, include the disputed
  uncertainty dimension, and include contradiction evidence for every member.
- Do not settle a denial, correction, or conflicting account unless the narrative
  explicitly establishes the controlling account.
- Use the smallest independently evidenced facts. Do not invent actor identity,
  target identity, motive, injury, weapon use, property damage, or causal links.
""".strip()
