# Operator Communication Tone Guidelines

## Authority and scope

This document is the governing repository authority for all operator-facing communication. It governs the operator communication prompt, deterministic fallback communication, Streamlit presentation, operational fact presentation, decision-logic wording, Salesforce preview wording, provider-generated communication, and future communication evaluations.

This document establishes presentation policy only. It does not change incident facts, evidence requirements, validation, classification policy, application behavior, or the authority of any runtime contract.

> The UI does not expose repository fields one-for-one.
>
> The UI answers operator questions.

When another presentation convention conflicts with this document, this document controls the operator-facing wording. Underlying facts, evidence, and classifications remain controlled by their existing authorities.

## Primary operator questions

Every operator-facing display should help answer these questions:

1. What happened?
2. Who or what was involved?
3. Was it intentional?
4. When did it happen?
5. Why was this classified this way?

Answering these questions takes precedence over displaying internal fields or preserving their internal order.

## Voice and writing rules

Operator communication shall:

- describe the incident directly;
- explain the classification in plain language;
- remain concise, human-readable, and operational;
- name people by role and identify targeted property when the narrative supports doing so;
- distinguish reported events from earlier events when timing matters;
- state uncertainty without guessing; and
- use only facts supported by the narrative and admitted evidence.

The voice should sound like an experienced hospital safety analyst explaining an incident to another person. It should not sound like software explaining its internal reasoning. Prefer short sentences, concrete verbs, familiar role names, and natural descriptions of timing and intent.

Do not introduce a person, role, target, motive, action, time, injury, location, ongoing condition, or certainty that the supported incident record does not establish. Concision never permits dropping a fact that materially explains the classification.

## Language kept out of operator communication

The following implementation terms are prohibited in operator-facing communication unless a dedicated technical engineering view explicitly requires them:

- assertion
- affirmed
- resolution
- active fact
- superseded fact
- semantic
- semantic analysis
- validation
- validated facts
- proposition
- deterministic
- processing status
- completeness status
- temporal scope
- policy candidate
- contradiction group
- schema
- repository
- model determined
- classifier concluded
- system determined

These terms may remain in engineering documentation, contracts, tests, and purpose-built engineering diagnostics. Their presence there does not authorize their use in an operator display.

## Translate fields into operator concepts

Internal fields are inputs to communication, not labels for the operator. Translate them into the question they answer.

| Internal concept | Operator concept | Example wording |
| --- | --- | --- |
| Direction | Who Was Involved | Patient and registered nurse |
| Direction | What Was Targeted | Medication room door |
| Current | When | During the event being reported |
| Historical | When | Before the event being reported |
| Interpersonal | Who Was Involved | Visitor and security officer |
| Self-directed | Who Was Involved | Patient harmed themself |
| Object-directed | What Was Targeted | Waiting-room window |

Never expose an internal enum when a natural explanation exists. Use the most specific supported role or target. If the narrative does not support identifying an actor or target, say only what is supported; do not manufacture specificity.

Correction and bookkeeping fields are normally hidden. Do not show Assertion or Resolution labels. Explain a correction or conflicting account only when it materially affects what happened or why the result cannot be settled.

## Operational Facts

Operational Facts answers human questions rather than listing repository fields. Use these labels:

- **What Happened**
- **Who Was Involved** or **What Was Targeted**
- **Intent**
- **When**

Do not use Conduct, Direction, Intentionality, Temporal Scope, Assertion, or Resolution as operator-facing labels. Omit internal correction bookkeeping. When a correction matters, integrate it into **What Happened**, such as “The initial report of a strike was withdrawn; the final account says no contact occurred.” When incompatible supported accounts remain unresolved, explain the disagreement without displaying internal grouping or state labels.

## Decision Logic and Why This Result

Decision Logic explains how the reported incident relates to the workplace violence criteria. It never explains how software reached the answer.

Preferred:

> Physical contact occurred during the event being reported, but the account describes it as accidental. Accidental contact does not meet the workplace violence criteria.

Avoid:

> The validated facts establish accidental conduct.

Lead with the supported event, then connect its intent, timing, and target to the applicable criteria. For an uncertain result, identify the specific unanswered or conflicting point that prevents a firm classification. For an unable-to-determine result, state that the incident could not be assessed from the available information without describing pipeline mechanics.

## Communication surfaces

The same voice and translation rules apply to:

- Incident Summary
- Key Findings
- Why This Result
- Operational Facts
- Decision Logic
- Salesforce Preview
- deterministic fallback communication
- provider-generated communication

Provider-generated wording and fallback wording must communicate the same supported meaning. A provider response is not allowed a more speculative, technical, or expansive voice than the fallback.

### Incident Summary

State the event and its most classification-relevant context in one or two sentences. Include actor and target roles when supported. Do not start with the result unless no incident description is available.

### Key Findings

Use a short list of supported details that materially explain the event: action or words, involved roles or target, intent, timing, and any relevant correction or unresolved conflict. Avoid duplicating every available field.

### Why This Result

Connect the event to the workplace violence criteria in plain language. Do not cite internal state, identifiers, or software operations.

### Salesforce Preview

Use operator-ready incident wording, natural role or target descriptions, and the established classification. Do not serialize internal enum labels or engineering bookkeeping into narrative-facing preview fields. The preview remains illustrative and must not imply an external write, completed workflow, or follow-up action that did not occur.

## Technical Details

Technical Details may show supported evidence, operational facts, and deterministic reasoning needed for careful review. It shall not become an implementation debugger.

Do not expose semantic contracts, graph structures, repository bookkeeping, internal identifiers, request mechanics, raw provider metadata, or internal correction and contradiction identifiers. Exact evidence excerpts may be shown when useful. Even in Technical Details, labels and explanatory prose should remain understandable to an operator unless the view is explicitly designated for engineering use.

## Before and after

| Before | After |
| --- | --- |
| Current incident | During the event being reported |
| Interpersonal | Patient and registered nurse |
| Assertion affirmed | Omit |
| Resolution active | Omit |
| Validated facts establish physical contact | The patient struck the nurse |
| Accidental conduct identified | Contact appeared accidental |
| Intentional violence unsupported | No intentional aggression was reported |

The “after” wording is illustrative and must be used only when the incident record supports it.

## Gold examples

The examples below define the expected structure and tone. Names, roles, actions, targets, timing, corrections, and uncertainty must always be adapted to the supported incident record.

### Intentional interpersonal assault

**Incident Summary**

During the event being reported, a patient intentionally struck a registered nurse.

**Key Findings**

- The patient made physical contact with the nurse.
- The contact was described as intentional.
- The conduct occurred during the reported event.

**Why This Result**

An intentional physical assault against another person meets the workplace violence criteria.

**Operational Facts**

- **What Happened:** The patient struck the nurse.
- **Who Was Involved:** Patient and registered nurse.
- **Intent:** Intentional.
- **When:** During the event being reported.

**Decision Logic**

The reported event involved intentional physical contact against another person, so it meets the workplace violence criteria.

### Verbal threat

**Incident Summary**

A visitor threatened to harm a security officer during the event being reported.

**Key Findings**

- The visitor communicated a threat of physical harm.
- The threat was directed at the security officer.
- The threat occurred during the reported event.

**Why This Result**

An intentional threat of physical harm against another person meets the workplace violence criteria even when no physical contact occurs.

**Operational Facts**

- **What Happened:** The visitor threatened physical harm.
- **Who Was Involved:** Visitor and security officer.
- **Intent:** Intentional.
- **When:** During the event being reported.

**Decision Logic**

The visitor intentionally communicated a threat of physical harm toward another person, which meets the workplace violence criteria.

### Self-harm

**Incident Summary**

During the event being reported, a patient intentionally harmed themself.

**Key Findings**

- The patient directed the act toward themself.
- The act was described as intentional.
- The act occurred during the reported event.

**Why This Result**

Intentional self-directed physical harm is included in the workplace violence criteria.

**Operational Facts**

- **What Happened:** The patient harmed themself.
- **Who Was Involved:** Patient; the act was self-directed.
- **Intent:** Intentional.
- **When:** During the event being reported.

**Decision Logic**

The reported event involved intentional self-directed harm, so it meets the workplace violence criteria.

### Intentional property violence

**Incident Summary**

A patient intentionally kicked and damaged a medication room door during the event being reported.

**Key Findings**

- The patient used force against the door.
- The property damage was described as intentional.
- The conduct occurred during the reported event.

**Why This Result**

Intentional violence directed at property is included in the workplace violence criteria.

**Operational Facts**

- **What Happened:** The patient kicked and damaged a door.
- **What Was Targeted:** Medication room door.
- **Intent:** Intentional.
- **When:** During the event being reported.

**Decision Logic**

The patient intentionally used force against hospital property during the reported event, so the incident meets the workplace violence criteria.

### Accidental contact

**Incident Summary**

A patient made physical contact with a nurse during the event being reported, but the contact appeared accidental.

**Key Findings**

- Physical contact occurred between the patient and nurse.
- The account describes the contact as accidental.
- No intentional aggression was reported.

**Why This Result**

Accidental physical contact does not meet the workplace violence criteria.

**Operational Facts**

- **What Happened:** The patient accidentally made contact with the nurse.
- **Who Was Involved:** Patient and nurse.
- **Intent:** Accidental.
- **When:** During the event being reported.

**Decision Logic**

Physical contact occurred during the reported event, but it was described as accidental. Accidental contact does not meet the workplace violence criteria.

### Historical-only conduct

**Incident Summary**

The patient described an intentional assault that occurred before the event being reported. No violent conduct was reported during the current event.

**Key Findings**

- The described assault occurred earlier.
- The reported event contains no current violent act or threat.

**Why This Result**

Earlier conduct provides context but does not establish workplace violence during the event under review.

**Operational Facts**

- **What Happened:** The patient described an earlier assault; no violence was reported in the event under review.
- **Who Was Involved:** Use the supported roles from the earlier account.
- **Intent:** The earlier assault was described as intentional.
- **When:** Before the event being reported.

**Decision Logic**

The only reported violent conduct occurred before the event under review, so it does not establish violence during this event.

### Corrected allegation

**Incident Summary**

The initial report said a patient struck a nurse, but that allegation was withdrawn. The final account says no physical contact occurred.

**Key Findings**

- An initial allegation of physical contact was corrected.
- The final account reports no contact.
- No other intentional aggression was reported.

**Why This Result**

The withdrawn allegation does not establish a violent act in the final account.

**Operational Facts**

- **What Happened:** The initial allegation of a strike was withdrawn; the final account reports no contact.
- **Who Was Involved:** Patient and nurse.
- **Intent:** No intentional aggression was reported in the final account.
- **When:** During the event being reported.

**Decision Logic**

The final account replaces the initial allegation and reports that no physical contact occurred. On that account, the event does not meet the workplace violence criteria.

### Unresolved contradiction

**Incident Summary**

One supported account says a patient intentionally struck a nurse, while another supported account says no contact occurred. The available information does not resolve the difference.

**Key Findings**

- The accounts disagree about whether physical contact occurred.
- The disagreement directly affects whether the event meets the criteria.
- The available information does not establish which account is correct.

**Why This Result**

The event cannot be classified with confidence because the unresolved accounts would lead to different results.

**Operational Facts**

- **What Happened:** Accounts conflict about whether the patient struck the nurse.
- **Who Was Involved:** Patient and nurse.
- **Intent:** Intentional in one account; not established in the other.
- **When:** During the event being reported.

**Decision Logic**

If the reported strike occurred, the event would meet the workplace violence criteria. Because another supported account says no contact occurred and the difference remains unresolved, the result is uncertain.

### Unable to determine

**Incident Summary**

The incident could not be assessed from the available information.

**Key Findings**

- There is not enough reliable incident information to determine what occurred.
- No classification should be inferred from the missing information.

**Why This Result**

A result requires enough supported information to describe the event and apply the workplace violence criteria.

**Operational Facts**

- **What Happened:** Unable to establish from the available information.
- **Who Was Involved or What Was Targeted:** Not established.
- **Intent:** Not established.
- **When:** Not established.

**Decision Logic**

The available information is insufficient to determine how the incident relates to the workplace violence criteria.

## Review checklist

Reviewers must confirm every applicable item before approving operator-facing communication:

- [ ] Communication describes the incident rather than the software.
- [ ] Internal semantic terminology is absent.
- [ ] Human-readable wording is used.
- [ ] Actors are named whenever supported.
- [ ] Internal enums are translated.
- [ ] Decision Logic explains the classification rather than repository mechanics.
- [ ] Unsupported facts are not introduced.
- [ ] Self-directed and property-directed violence are explained naturally.
- [ ] Corrections and contradictions are explained only when relevant.
- [ ] The overall tone resembles an experienced hospital safety analyst.
