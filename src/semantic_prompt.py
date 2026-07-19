SEMANTIC_EXTRACTION_PROMPT = """
Analyze only the supplied incident narrative.

Return one violence-checker.proposition-semantics envelope at schema version
1.0.0. Extract all violence-relevant propositions, relationships, bounded
uncertainties, exact evidence excerpts, and evidence-support links in one response.
Do not use information outside the narrative or infer absent facts.

Do not make operational recommendations, hospital workflow decisions,
Salesforce write decisions, or legal, clinical, or safety recommendations.
Do not decide whether extracted data should be written or what action a person
or system should take.

Required boundaries:
- Use canonical ENT-, PROP-, REL-, UNC-, EVID-, and SUP- identifiers and the
  contract-defined collection order.
- Scope actor, conduct, target, completion, contact, temporal scope,
  intentionality, assertion status, and attribution to each proposition.
- Represent current and historical claims as separate propositions.
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
  Every proposition, relationship, and uncertainty must have coherent support.
- Free-form notes and provider confidence are provenance only. They do not
  author semantic truth, admissibility, policy, workflow, or recommendations.
""".strip()
