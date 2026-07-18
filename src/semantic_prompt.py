SEMANTIC_EXTRACTION_PROMPT = """
Analyze only the supplied incident narrative.

Return only structured semantic facts extracted from the narrative. Do not use
any information outside the narrative. Do not infer facts that are not present.

Do not make operational recommendations, hospital workflow decisions,
Salesforce write decisions, or legal, clinical, or safety recommendations.
Do not decide whether extracted data should be written or what action a person
or system should take.

Required analysis:
- Preserve the distinction between current incident events and historical events.
- Treat current_event as whether the described violence, threat, intimidation,
  attempt, contact, or relevant correction occurred during the incident being
  reported. A current incident remains current even if it ended before the
  report was written.
- Historical disclosures unrelated to the reported incident must use
  current_event=false, even when the historical event involved violence.
- Identify negation, including statements that violence did not happen.
- Identify corrections and conflicting statements. When a later explicit and
  credible correction contradicts an earlier claim, represent the corrected
  semantic facts while still marking correction_present=true and
  conflicting_information=true when both claims appear.
- If a correction states that a person was not struck, kicked, contacted, or
  targeted, do not preserve the earlier person-directed violence claim in the
  extracted facts unless another part of the narrative independently
  supports a person-directed attempt or contact.
- Distinguish no violence, verbal threats, attempted physical violence,
  completed physical violence, and unclear events.
- Distinguish violence directed at a person from contact with an object.
  Kicking, striking, or contacting an object is not physical violence against a
  person unless the narrative supports a person-directed attempt or contact.
  Object-directed aggression may be event_type=unclear with
  violence_present=false when no person-directed attempt or contact is supported.
- Distinguish intentional contact from accidental contact. Accidental contact
  may have contact_occurred=true while violence_present=false. If accidental
  physical contact occurred without violence, use event_type=unclear rather
  than event_type=none so the contact can be represented.
- Threatening movement or language may be verbal_threat or unclear when
  supported by the narrative, but do not upgrade it to attempted physical
  violence without evidence of a person-directed physical attempt.
- Use evidence_text only for exact excerpts copied from the supplied narrative.
- Represent uncertainty explicitly in uncertainty_notes.
- Use confidence as a number from 0 through 1.

If the narrative lacks evidence for a field, use null for actor or target where
appropriate, false for unsupported boolean claims, unclear for intentionality
where appropriate, and explain uncertainty in uncertainty_notes.
""".strip()
