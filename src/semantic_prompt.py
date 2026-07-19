SEMANTIC_EXTRACTION_PROMPT = """
Analyze only the supplied incident narrative.

Return one structured semantic candidate response. Extract all violence-relevant
propositions, relationships, bounded uncertainties, exact evidence excerpts, and
evidence-support links in one response.
Do not use information outside the narrative or infer absent facts.

Do not make operational recommendations, hospital workflow decisions,
Salesforce write decisions, or legal, clinical, or safety recommendations.
Do not decide whether extracted data should be written or what action a person
or system should take.

Required boundaries:
- Use short, unique local_ref values to identify entities, propositions,
  relationships, uncertainties, and evidence excerpts within this response.
  Use those local references for every cross-reference. They are temporary and
  must not use final ENT-, PROP-, REL-, UNC-, EVID-, or SUP- identifiers.
- Do not return an incident identifier, extraction metadata, extraction contract
  identity or version, semantic schema identity or version, final repository
  identifiers, or final repository ordering fields.
- Scope actor, conduct, target, completion, contact, temporal scope,
  intentionality, assertion status, and attribution to each proposition.
- Represent current and historical claims as separate propositions.
- A disclosed assault from years ago is one affirmed historical physical-conduct
  proposition with completed completion and occurred contact. The disclosed
  assailant is the actor and the person reporting the assault is the entity
  target. For this historical-disclosure shape, return exactly that one violence
  proposition unless the narrative states another distinct violent event.
- Phrases such as "nothing happened today", "calm and cooperative", "no threats",
  or "no aggressive behavior" are contextual clarifiers, not separate conduct.
  Do not create current, negated, threatening-movement, or threat-expression
  propositions for those phrases when they only clarify that a historical
  disclosure has no current incident.
- A target_kind of entity requires target_ref to name a local entity. A
  target_kind of self or undetermined requires target_ref to be null. Never attach
  an entity reference to a self or undetermined target.
- Threat expression requires threatened or undetermined completion and
  not_applicable contact. Attempted physical conduct requires did_not_occur
  contact; completed physical conduct and contact_only require occurred contact.
  Contact_only always requires completed completion. Threatening movement must
  use not_applicable or undetermined completion, never attempted or completed.
- Represent a denial on its proposition and add a negates relationship only
  when it explicitly opposes another represented proposition.
- Preserve corrected content and its replacement as separate propositions with
  a directed supersedes relationship. Do not delete or rewrite the earlier text.
- Preserve competing accounts as separate propositions with one canonical
  conflicts_with relationship and bounded disputed dimensions. Do not rank or
  adjudicate sources.
- Use undetermined and not_applicable exactly as defined by the structured
  contract. Never use a silent default to replace missing semantics.
- Distinguish interpersonal, self-directed, object-directed, accidental,
  threatening, attempted, completed, negated, and uncertain content through the
  proposition fields. Do not author a direction or document-level outcome.
- Copy every evidence excerpt exactly from the supplied normalized narrative.
  Every proposition, relationship, and uncertainty must have at least one
  evidence_support entry; never return an unsupported semantic subject. A
  conflicts_with relationship specifically requires supports_conflict evidence,
  a negates relationship requires supports_negation evidence, and a supersedes
  relationship requires supports_supersession evidence.
- Add uncertainty only for a proposition dimension whose value is undetermined
  or that is explicitly disputed by a conflicts_with relationship. Historical
  timing such as "a few yrs ago" is resolved as historical, not uncertain.
- Proposition evidence uses supports_negation only for a negated proposition and
  supports_assertion for affirmed or uncertain propositions. Relationship evidence
  uses the role matching negates, supersedes, or conflicts_with. Uncertainty
  evidence always uses supports_uncertainty.
- Free-form uncertainty notes do not author semantic truth, admissibility,
  policy, workflow, or recommendations.
""".strip()
