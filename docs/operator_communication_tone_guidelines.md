# Operator Communication Tone Guidelines

## Authority and scope

This document is the governing repository authority for all operator-facing communication. It governs the operator communication prompt, deterministic fallback communication, Streamlit presentation, operational fact presentation, decision-logic wording, Salesforce preview wording, provider-generated communication, and future communication evaluations.

This document establishes presentation policy only. It does not change incident facts, evidence requirements, validation, classification policy, application behavior, or the authority of any runtime contract.

> The purpose of operator communication is to help a hospital operator understand what happened.
>
> The purpose is not to explain how the software reached its conclusion.

> The UI does not expose repository fields one-for-one.
>
> The UI answers operator questions.

When another presentation convention conflicts with this document, this document controls the operator-facing wording. Underlying facts, evidence, and classifications remain controlled by their existing authorities.

## Primary operator questions

Operator-facing communication shall answer these questions in this order unless a specific surface requires otherwise:

1. What happened?
2. Who or what was involved?
3. Was it intentional?
4. When did it happen?
5. Why was this classified this way?

Answering these questions takes precedence over displaying internal fields or preserving their internal order.

## Incident-first principle

The Incident Summary is the primary communication artifact. Its responsibility is to synthesize the supported incident into concise, natural language.

The Incident Summary shall:

- describe the reported event;
- preserve chronology when chronology affects understanding;
- identify people or property when supported;
- remove repetition;
- improve readability; and
- remain faithful to validated repository truth.

The Incident Summary shall not:

- explain the classification;
- discuss repository reasoning;
- describe semantic processing; or
- expose implementation terminology.

The AI exists to transform fragmented clinical writing into concise, faithful incident descriptions. It does not exist merely to restate the classification.

> If the Incident Summary is not noticeably easier to understand than the original narrative, the communication has failed.

## Classification separation

Each surface has one distinct responsibility:

- The deterministic outcome and outcome subtitle answer: **What was the classification?**
- The Incident Summary answers: **What happened?**
- Why This Result answers: **Why does the reported incident produce this classification?**

These responsibilities shall remain distinct. The Incident Summary must not lead with or paraphrase the outcome. Why This Result must connect incident facts to workplace violence doctrine without recounting software operations.

## Voice and writing rules

Operator communication shall:

- describe the incident directly;
- explain the classification in plain language only on the surfaces responsible for explanation;
- remain concise, human-readable, and operational;
- name people by role and identify targeted property when the narrative supports doing so;
- distinguish reported events from earlier events when timing matters;
- state uncertainty without guessing; and
- use only facts supported by the narrative and admitted evidence.

The voice should sound like an experienced hospital safety analyst explaining an incident to another person. It should not sound like software explaining its internal reasoning. Prefer short sentences, concrete verbs, familiar role names, and natural descriptions of timing and intent.

Do not introduce a person, role, target, motive, action, time, injury, location, ongoing condition, or certainty that the supported incident record does not establish. Concision never permits dropping a fact that materially explains the classification.

## Language kept out of operator communication

The following implementation terms are prohibited in operator-facing communication unless a dedicated engineering view explicitly requires them:

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
| Direction | What Was Targeted | Hospital window |
| Current | When | During the event being reported |
| Historical | When | Before the event being reported |
| Interpersonal | Who Was Involved | Patient and registered nurse |
| Self-directed | Who Was Involved | Patient |
| Object-directed | What Was Targeted | Hospital window |

Never expose an internal enum when a natural explanation exists. Use the most specific supported role or target. If the narrative does not support identifying an actor or target, say only what is supported; do not manufacture specificity.

Assertion and Resolution shall normally remain hidden. Expose a correction or contradiction only when it is necessary to understand the incident or the classification.

## Communication surfaces

The same voice and translation rules apply to:

- Outcome
- Outcome subtitle
- Incident Summary
- Key Findings
- Why This Result
- Operational Facts
- Decision Logic
- Salesforce Preview
- deterministic fallback communication
- provider-generated communication

Provider-generated wording and fallback wording must communicate the same supported meaning. A provider response is not allowed a more speculative, technical, or expansive voice than the fallback.

### Outcome and outcome subtitle

State the deterministic classification and a short operator-facing description of that classification. Do not use this surface to summarize the incident.

### Incident Summary

Synthesize what happened in one or two concise sentences. Preserve important chronology, identify supported actors or property, remove repetitive chart language, and do not explain the classification.

### Key Findings

List concrete supported facts, not conclusions about internal criteria or processing.

Prefer:

- Patient lost balance
- Registered nurse contacted
- Physical contact occurred
- Contact appeared accidental
- Patient not combative

Avoid:

- Accidental conduct identified
- Intentional violence unsupported
- Criteria satisfied
- Assertion affirmed
- Resolution active

### Why This Result

Connect the incident facts to the workplace violence doctrine. Explain the relationship between what happened and the criteria, never how software processed the report.

Preferred:

> Physical contact occurred during the event being reported, but the account describes the contact as accidental. Accidental contact does not meet the workplace violence criteria.

Avoid:

> The validated facts establish accidental conduct.

For an uncertain result, identify the specific unanswered or conflicting point that prevents a firm classification. For an unable-to-determine result, state what information is missing without describing pipeline mechanics.

### Operational Facts

Operational Facts answers human questions. Use these labels:

- **What Happened**
- **Who Was Involved** or **What Was Targeted**
- **Intent**
- **When**

Do not use Conduct, Direction, Intentionality, Temporal Scope, Assertion, or Resolution as operator-facing labels. Translate internal enum values into natural language. When a correction matters, integrate it into **What Happened**, such as “The initial report of a strike was withdrawn; the final account says no contact occurred.” When incompatible supported accounts remain unresolved, explain the disagreement without displaying internal grouping or state labels.

### Decision Logic

Decision Logic provides a concise doctrinal statement for careful review. It may overlap with Why This Result, but it must remain about the relationship between the reported facts and the workplace violence criteria. It never explains how software reached the answer.

### Salesforce Preview

Use operator-ready incident wording, natural role or target descriptions, and the established classification. Do not serialize internal enum labels or engineering bookkeeping into narrative-facing preview fields. The preview remains illustrative and must not imply an external write, completed workflow, or follow-up action that did not occur.

## Technical Details

Technical Details may show supported evidence, operational facts, and deterministic reasoning needed for careful review. It shall not become an implementation debugger.

Do not expose semantic contracts, graph structures, repository bookkeeping, internal identifiers, request mechanics, raw provider metadata, or internal correction and contradiction identifiers. Exact evidence excerpts may be shown when useful. Even in Technical Details, labels and explanatory prose should remain understandable to an operator unless the view is explicitly designated for engineering use.

## Before and after: classification-first to incident-first

### Accidental contact

**Before — classification-first**

> No Violence Detected. Accidental conduct identified and intentional violence unsupported.

**After — incident-first**

> The patient lost balance while standing and bumped into the registered nurse who was helping them. The contact appeared accidental, and the patient was not combative.

The revised summary tells the operator what happened, who was involved, and the apparent intent before the separate explanation addresses classification.

### Intentional interpersonal assault

**Before — classification-first**

> Violence Detected. Criteria satisfied for intentional interpersonal physical contact.

**After — incident-first**

> The patient intentionally struck the registered nurse during the reported event.

The revised summary describes the event directly and leaves the doctrinal conclusion to Why This Result.

### Field translation

| Classification-first or internal wording | Incident-first or operator wording |
| --- | --- |
| Current | During the event being reported |
| Historical | Before the event being reported |
| Interpersonal | Patient and registered nurse |
| Object-directed | Hospital window |
| Self-directed | Patient |
| Assertion affirmed | Omit |
| Resolution active | Omit |
| Validated facts establish physical contact | The patient struck the nurse |

The operator wording is illustrative and may be used only when the supported incident record establishes it.

## Gold examples

The examples below define the required structure and incident-first tone. Names, roles, actions, targets, timing, corrections, and uncertainty must always be adapted to the supported incident record.

### Intentional interpersonal assault

**Outcome:** Violence Detected

**Outcome subtitle:** Intentional physical violence occurred during the reported event.

**Incident Summary:** The patient intentionally struck a registered nurse during the reported event.

**Key Findings**

- Patient struck registered nurse
- Physical contact occurred
- Contact was intentional
- Incident occurred during the event being reported

**Why This Result:** Intentional physical contact against another person meets the workplace violence criteria.

**Operational Facts**

- **What Happened:** The patient struck the nurse.
- **Who Was Involved:** Patient and registered nurse.
- **Intent:** Intentional.
- **When:** During the event being reported.

**Decision Logic:** The reported event involved intentional physical contact against another person, so it meets the workplace violence criteria.

### Explicit physical threat

**Outcome:** Violence Detected

**Outcome subtitle:** An intentional threat of physical harm occurred during the reported event.

**Incident Summary:** A visitor told a security officer that they would punch the officer during the reported event.

**Key Findings**

- Visitor threatened to punch security officer
- Threat described physical harm
- Threat was intentional
- Threat occurred during the event being reported

**Why This Result:** An explicit, intentional threat of physical harm against another person meets the workplace violence criteria even when no physical contact occurs.

**Operational Facts**

- **What Happened:** The visitor threatened to punch the officer.
- **Who Was Involved:** Visitor and security officer.
- **Intent:** Intentional.
- **When:** During the event being reported.

**Decision Logic:** The visitor intentionally communicated an explicit threat of physical harm toward another person, which meets the workplace violence criteria.

### Self-harm

**Outcome:** Violence Detected

**Outcome subtitle:** Intentional self-directed harm occurred during the reported event.

**Incident Summary:** The patient intentionally hit their own head against the wall during the reported event.

**Key Findings**

- Patient hit their head against wall
- Harm was directed at patient
- Act was intentional
- Act occurred during the event being reported

**Why This Result:** Intentional self-directed physical harm is included in the workplace violence criteria.

**Operational Facts**

- **What Happened:** The patient hit their head against the wall.
- **Who Was Involved:** Patient.
- **Intent:** Intentional.
- **When:** During the event being reported.

**Decision Logic:** The reported event involved intentional self-directed harm, so it meets the workplace violence criteria.

### Intentional property violence

**Outcome:** Violence Detected

**Outcome subtitle:** Intentional violence was directed at hospital property.

**Incident Summary:** The patient intentionally kicked and damaged a medication room door during the reported event.

**Key Findings**

- Patient kicked medication room door
- Door was damaged
- Property damage was intentional
- Incident occurred during the event being reported

**Why This Result:** Intentional violence directed at property is included in the workplace violence criteria.

**Operational Facts**

- **What Happened:** The patient kicked and damaged a door.
- **What Was Targeted:** Medication room door.
- **Intent:** Intentional.
- **When:** During the event being reported.

**Decision Logic:** The patient intentionally used force against hospital property during the reported event, so the incident meets the workplace violence criteria.

### Accidental contact

**Outcome:** No Violence Detected

**Outcome subtitle:** Physical contact occurred, but the account describes it as accidental.

**Incident Summary:** The patient lost balance while standing and bumped into the registered nurse who was helping them. The patient was not combative, and the contact appeared accidental.

**Key Findings**

- Patient lost balance
- Registered nurse contacted
- Physical contact occurred
- Contact appeared accidental
- Patient not combative

**Why This Result:** Physical contact occurred during the event being reported, but the account describes the contact as accidental. Accidental contact does not meet the workplace violence criteria.

**Operational Facts**

- **What Happened:** The patient lost balance and bumped into the nurse assisting them.
- **Who Was Involved:** Patient and registered nurse.
- **Intent:** Accidental.
- **When:** During the event being reported.

**Decision Logic:** The reported contact was accidental rather than intentional, so it does not meet the workplace violence criteria.

### Historical-only conduct

**Outcome:** No Violence Detected

**Outcome subtitle:** The described violence happened before the event being reviewed.

**Incident Summary:** The patient described having intentionally struck a family member the previous day. No violent act or threat occurred during the event being reported.

**Key Findings**

- Patient described an earlier assault
- Assault occurred before reported event
- No current violent act reported
- No current threat reported

**Why This Result:** Earlier conduct provides context but does not establish workplace violence during the event under review.

**Operational Facts**

- **What Happened:** The patient described an earlier assault; no violence occurred during the event under review.
- **Who Was Involved:** Patient and family member.
- **Intent:** Earlier assault described as intentional.
- **When:** Before the event being reported.

**Decision Logic:** The only described violent conduct happened before the event under review, so it does not establish violence during this event.

### Corrected allegation

**Outcome:** No Violence Detected

**Outcome subtitle:** The final account reports that the alleged physical contact did not occur.

**Incident Summary:** The initial report said the patient struck a nurse, but the reporter withdrew that allegation and clarified that no physical contact occurred.

**Key Findings**

- Initial report alleged patient struck nurse
- Reporter withdrew allegation
- Final account reports no contact
- No other intentional aggression reported

**Why This Result:** The withdrawn allegation does not establish a violent act in the final account.

**Operational Facts**

- **What Happened:** The initial allegation of a strike was withdrawn; the final account reports no contact.
- **Who Was Involved:** Patient and nurse.
- **Intent:** No intentional aggression was reported in the final account.
- **When:** During the event being reported.

**Decision Logic:** The final account reports that no physical contact occurred, so the event does not meet the workplace violence criteria.

### Unresolved contradiction

**Outcome:** Uncertain

**Outcome subtitle:** The available accounts disagree about whether intentional physical contact occurred.

**Incident Summary:** One account says the patient intentionally struck a nurse, while another says no contact occurred. The available information does not resolve the difference.

**Key Findings**

- One account reports patient struck nurse
- Another account reports no contact
- Accounts remain unresolved
- Disagreement changes the possible classification

**Why This Result:** If the reported strike occurred, it would meet the workplace violence criteria; if no contact occurred, it would not. The unresolved accounts prevent a firm classification.

**Operational Facts**

- **What Happened:** Accounts conflict about whether the patient struck the nurse.
- **Who Was Involved:** Patient and nurse.
- **Intent:** Intentional in one account; not established in the other.
- **When:** During the event being reported.

**Decision Logic:** The accounts would lead to different classifications, and the available information does not establish which account is accurate.

### Insufficient information

**Outcome:** Unable to Determine

**Outcome subtitle:** The report does not contain enough incident information for classification.

**Incident Summary:** The report states only that an incident occurred and does not describe any action, words, people, property, intent, or timing.

**Key Findings**

- Report does not describe what happened
- People or property involved are not identified
- Intent is not established
- Timing is not established

**Why This Result:** The workplace violence criteria cannot be applied without enough information to understand the reported event.

**Operational Facts**

- **What Happened:** Not established from the available information.
- **Who Was Involved or What Was Targeted:** Not established.
- **Intent:** Not established.
- **When:** Not established.

**Decision Logic:** The available information does not describe an incident that can be compared with the workplace violence criteria.

## Acceptance checklist

Reviewers must confirm every applicable item before approving operator-facing communication:

- [ ] Does the Incident Summary describe what happened?
- [ ] Is the summary easier to understand than the original narrative?
- [ ] Does the summary avoid merely restating the classification?
- [ ] Are actors identified whenever supported?
- [ ] Are operator questions answered naturally?
- [ ] Does Why This Result explain doctrine rather than software?
- [ ] Are implementation terms absent?
- [ ] Would a hospital operator understand the incident without reading the raw narrative?
- [ ] Are internal enums translated into natural language?
- [ ] Are unsupported facts absent?
- [ ] Are corrections and contradictions included only when needed to understand the incident or result?
- [ ] Are the Outcome, Incident Summary, and Why This Result responsibilities kept distinct?
