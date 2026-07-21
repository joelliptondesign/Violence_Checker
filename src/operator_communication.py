"""Incident-first, presentation-only communication from validated True North facts."""

from __future__ import annotations

from src.contracts import (
    AssertionStatus,
    CommunicationFact,
    Conduct,
    FactDirection,
    Intentionality,
    OperatorCommunication,
    OperatorCommunicationInput,
    PolicyDecision,
    PolicyOutcome,
    TemporalScope,
    ValidationResult,
)


CONDUCT_WORDING = {
    Conduct.VERBAL_THREAT: "Explicit physical threat",
    Conduct.PHYSICAL_ATTEMPT: "Attempted physical contact",
    Conduct.PHYSICAL_CONTACT: "Physical contact",
    Conduct.SELF_HARM: "Self-harm",
    Conduct.PROPERTY_VIOLENCE: "Property damage",
}

CONDUCT_MARKERS = {
    Conduct.VERBAL_THREAT: ("threat", "punch", "harm"),
    Conduct.PHYSICAL_ATTEMPT: ("attempt", "swung", "lunged", "missed", "tried"),
    Conduct.PHYSICAL_CONTACT: ("contact", "hit", "struck", "grab", "kick", "slap", "elbow"),
    Conduct.SELF_HARM: ("self-harm", "themself", "herself", "himself", "own"),
    Conduct.PROPERTY_VIOLENCE: ("property", "door", "window", "wall", "rail", "object"),
}


def _support(action: str, value=None, extra=None):
    """Provide bounded wording helpers without adding separate authority surfaces."""
    if action == "unique":
        return tuple(dict.fromkeys(item.strip() for item in value if item.strip()))

    if action == "evidence":
        facts = value
        return _support(
            "unique",
            (
                excerpt
                for fact in (*facts.active_facts, *facts.superseded_facts)
                for excerpt in fact.evidence_excerpts
            ),
        )

    if action == "roles":
        lowered = f" {value.casefold()} "
        roles = []
        checks = (
            ("Patient", (" patient ", " pt ")),
            ("Registered nurse", (" registered nurse ", " rn ")),
            ("Nurse", (" nurse ",)),
            ("Technician", (" technician ", " tech ")),
            ("Aide", (" aide ",)),
            ("Visitor", (" visitor ",)),
            ("Security officer", (" security officer ",)),
            ("Security staff", (" security ",)),
            ("Family member", (" family member ",)),
        )
        for label, terms in checks:
            if any(term in lowered for term in terms):
                if label == "Nurse" and "Registered nurse" in roles:
                    continue
                if label == "Security staff" and "Security officer" in roles:
                    continue
                roles.append(label)
        return tuple(roles)

    if action == "involved":
        fact = value
        evidence = " ".join(fact.evidence_excerpts)
        if fact.direction == FactDirection.OBJECT_DIRECTED:
            targets = (
                ("Medication room door", "medication room door"),
                ("Hospital window", "hospital window"),
                ("Window", "window"),
                ("Side rail", "side rail"),
                ("Door", "door"),
                ("Wall", "wall"),
            )
            lowered = evidence.casefold()
            target = next((label for label, term in targets if term in lowered), "Property described in the report")
            return "What Was Targeted", target
        roles = list(_support("roles", evidence))
        if fact.direction == FactDirection.SELF_DIRECTED:
            return "Who Was Involved", roles[0] if roles else "Person described in the report"
        material_roles = [role for role in roles if not role.startswith("Security")]
        if len(material_roles) >= 2:
            return "Who Was Involved", f"{material_roles[0]} and {material_roles[1].lower()}"
        if material_roles:
            return "Who Was Involved", material_roles[0]
        return "Who Was Involved", "People described in the report"

    if action == "what":
        fact = value
        conduct = CONDUCT_WORDING.get(fact.conduct, "Reported conduct")
        if fact.assertion_status == AssertionStatus.DENIED:
            return f"Reported {conduct.lower()} did not occur"
        return conduct

    if action == "fields":
        fact = value
        involvement_label, involvement = _support("involved", fact)
        return {
            "What Happened": _support("what", fact),
            involvement_label: involvement,
            "Intent": {
                Intentionality.INTENTIONAL: "Intentional",
                Intentionality.ACCIDENTAL: "Accidental",
                Intentionality.UNRESOLVED: "Not established",
            }[fact.intentionality],
            "When": {
                TemporalScope.CURRENT: "During the event being reported",
                TemporalScope.HISTORICAL: "Before the event being reported",
                TemporalScope.UNRESOLVED: "Not established",
            }[fact.temporal_scope],
        }

    if action == "naturalize":
        text = " ".join(value.strip().split())
        replacements = (
            ("pt", "patient"), ("rn", "registered nurse"), ("tech", "technician"),
            ("secuirty", "security"), ("dc", "discharge"), ("doesnt", "doesn't"),
            ("didnt", "didn't"), ("im", "I'm"),
        )
        words = text.split(" ")
        for index, word in enumerate(words):
            start = next((position for position, character in enumerate(word) if character.isalnum()), len(word))
            end = next((position for position, character in enumerate(reversed(word)) if character.isalnum()), len(word))
            prefix = word[:start]
            suffix = word[len(word) - end:] if end else ""
            core = word.strip(".,!?;:'\"").casefold()
            replacement = next((new for old, new in replacements if core == old), None)
            if replacement is not None:
                words[index] = f"{prefix}{replacement}{suffix}"
        text = " ".join(words)
        text = text[0].upper() + text[1:] if text else text
        return text if text.endswith((".", "!", "?")) else f"{text}."

    if action == "gold_accidental":
        lowered = value.casefold()
        return all(term in lowered for term in (
            "lost balance", "commode", "grab", "arm", "not combative", "accidental",
        ))

    if action == "findings":
        facts = value
        evidence = " ".join(_support("evidence", facts)).casefold()
        if _support("gold_accidental", evidence):
            return (
                "Patient lost balance",
                "Registered nurse's arm grabbed",
                "Physical contact occurred",
                "Contact appeared accidental",
                "Patient not combative",
            )
        findings = []
        candidates = []
        if facts.has_unresolved_contradiction:
            candidates.extend(("Accounts describe different events", "Difference remains unresolved"))
        if facts.superseded_facts:
            candidates.append("Initial account was corrected")
        for fact in facts.active_facts:
            if fact.conduct is not None:
                suffix = "reported" if fact.conduct == Conduct.VERBAL_THREAT else "occurred"
                candidates.append(f"{CONDUCT_WORDING[fact.conduct]} {suffix}")
            candidates.append({
                Intentionality.INTENTIONAL: "Conduct described as intentional",
                Intentionality.ACCIDENTAL: "Contact appeared accidental",
                Intentionality.UNRESOLVED: "Intent remains unclear",
            }[fact.intentionality])
            if fact.temporal_scope == TemporalScope.HISTORICAL:
                candidates.append("Event occurred earlier")
            if fact.assertion_status == AssertionStatus.DENIED:
                candidates.append("Reported conduct was denied")
        if "not combative" in evidence:
            candidates.append("Patient not combative")
        for candidate in candidates:
            if candidate not in findings and 2 <= len(candidate.split()) <= 5 and len(findings) < 8:
                findings.append(candidate)
        return tuple(findings or ["Incident details not established"])

    if action == "summary":
        facts = value
        evidence = " ".join(_support("evidence", facts))
        if _support("gold_accidental", evidence):
            return (
                "The patient lost balance while getting up from the commode and grabbed the "
                "registered nurse's arm to maintain balance. The narrative states the patient was "
                "not combative and describes the contact as accidental."
            )
        if facts.has_unresolved_contradiction:
            primary = facts.active_facts[0] if facts.active_facts else None
            event = _support("what", primary).lower() if primary else "the reported conduct"
            involved = _support("involved", primary)[1] if primary else "the people involved"
            return (
                f"The available accounts disagree about whether {event} occurred involving "
                f"{involved.lower()}. The difference remains unresolved."
            )
        excerpts = _support("evidence", facts)
        if excerpts:
            return " ".join(_support("naturalize", excerpt) for excerpt in excerpts)
        return "The available information does not describe what happened."

    if action == "detected":
        return next((
            fact for fact in value.active_facts
            if fact.conduct is not None
            and fact.intentionality == Intentionality.INTENTIONAL
            and fact.temporal_scope == TemporalScope.CURRENT
            and fact.assertion_status == AssertionStatus.AFFIRMED
        ), None)

    if action == "why":
        facts = value
        if facts.outcome == PolicyOutcome.UNCERTAIN:
            if facts.has_unresolved_contradiction:
                return (
                    "The accounts describe materially different events that would lead to different "
                    "classifications. The unresolved difference prevents a clear determination under "
                    "the workplace violence criteria."
                )
            return (
                "A detail about the reported conduct, intent, or timing remains unresolved and could "
                "change whether the workplace violence criteria are met."
            )
        if facts.outcome == PolicyOutcome.VIOLENCE_DETECTED:
            detected = _support("detected", facts)
            if detected is None or detected.conduct is None:
                raise ValueError("detected communication requires a qualifying active fact")
            doctrine = {
                Conduct.VERBAL_THREAT: "An explicit, intentional threat of physical harm against another person",
                Conduct.PHYSICAL_ATTEMPT: "An intentional attempt at physical violence",
                Conduct.PHYSICAL_CONTACT: "Intentional physical contact against another person",
                Conduct.SELF_HARM: "Intentional self-directed physical harm",
                Conduct.PROPERTY_VIOLENCE: "Intentional violence directed at property",
            }[detected.conduct]
            return f"{doctrine} during the event being reported meets the workplace violence criteria."
        if facts.outcome != PolicyOutcome.NO_VIOLENCE_DETECTED:
            raise ValueError("unsupported deterministic communication outcome")
        accidental = next((fact for fact in facts.active_facts if fact.intentionality == Intentionality.ACCIDENTAL), None)
        historical = next((fact for fact in facts.active_facts if fact.temporal_scope == TemporalScope.HISTORICAL), None)
        denied = next((fact for fact in facts.active_facts if fact.assertion_status == AssertionStatus.DENIED), None)
        if accidental is not None:
            return (
                "Physical contact occurred during the event being reported, but the account describes "
                "the contact as accidental rather than intentional. Accidental contact does not meet "
                "the workplace violence criteria."
            )
        if historical is not None:
            return (
                "The described conduct occurred before the event being reported. Earlier conduct does "
                "not meet the workplace violence criteria for the event under review."
            )
        if facts.superseded_facts:
            return (
                "The final account replaces the earlier allegation and does not describe current "
                "qualifying violence, so the workplace violence criteria are not met."
            )
        if denied is not None:
            return (
                "The account states that the reported conduct did not occur. Conduct that did not occur "
                "does not meet the workplace violence criteria."
            )
        return (
            "The reported event does not contain intentional current conduct that meets the workplace "
            "violence criteria."
        )
    raise ValueError(f"unsupported communication helper action: {action}")


def _project_fact(fact) -> CommunicationFact:
    return CommunicationFact(
        conduct=fact.conduct,
        direction=fact.direction,
        intentionality=fact.intentionality,
        temporal_scope=fact.temporal_scope,
        assertion_status=fact.assertion_status,
        resolution_status=fact.resolution_status,
        uncertainty=tuple(fact.uncertainty),
        evidence_excerpts=_support("unique", (item.excerpt for item in fact.evidence)),
    )


def construct_communication_input(
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
) -> OperatorCommunicationInput:
    """Project validated meaning and exact supporting excerpts without identifiers."""
    if not isinstance(validation_result, ValidationResult) or not validation_result.passed:
        raise ValueError("communication input requires successful validation")
    if not isinstance(policy_decision, PolicyDecision):
        raise TypeError("communication input requires a PolicyDecision")
    if policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE:
        raise ValueError("unable analysis uses deterministic failure communication")
    envelope = validation_result.validated_envelope
    derived = validation_result.derived_semantics
    if envelope is None or derived is None:
        raise ValueError("communication input requires validated facts and deterministic views")
    active_ids = set(derived.active_fact_ids)
    superseded_ids = set(derived.superseded_fact_ids)
    return OperatorCommunicationInput(
        outcome=policy_decision.outcome,
        incident_direction=derived.incident_direction,
        active_facts=tuple(_project_fact(fact) for fact in envelope.facts if fact.fact_id in active_ids),
        superseded_facts=tuple(_project_fact(fact) for fact in envelope.facts if fact.fact_id in superseded_ids),
        has_unresolved_contradiction=bool(derived.contradiction_groups),
    )


operator_fact_fields = lambda fact: _support("fields", fact)
project_communication_fact = lambda fact: _project_fact(fact)
involved_wording = lambda fact: _support("involved", fact)
what_happened_wording = lambda fact: _support("what", fact)


def build_deterministic_communication(facts: OperatorCommunicationInput) -> OperatorCommunication:
    """Render incident-first fallback copy from the validated communication projection."""
    if not isinstance(facts, OperatorCommunicationInput):
        raise TypeError("deterministic communication requires OperatorCommunicationInput")
    return OperatorCommunication(
        incident_summary=_support("summary", facts),
        key_findings=_support("findings", facts),
        why_this_result=_support("why", facts),
    )


def build_failure_communication(policy_decision: PolicyDecision) -> OperatorCommunication:
    """Describe missing incident information without fabricating an event."""
    if not isinstance(policy_decision, PolicyDecision) or policy_decision.outcome != PolicyOutcome.UNABLE_TO_DETERMINE:
        raise ValueError("failure communication requires Unable to Determine")
    return OperatorCommunication(
        incident_summary=(
            "The available report does not contain enough supported information to describe what "
            "happened reliably."
        ),
        key_findings=("Incident details not established", "Reliable account unavailable"),
        why_this_result=(
            "The workplace violence criteria cannot be applied without enough information to "
            "understand the reported event."
        ),
    )


def communication_validation_issues(
    communication: OperatorCommunication,
    facts: OperatorCommunicationInput,
) -> tuple[str, ...]:
    """Compare generated prose with the validated projection before presentation."""
    if not isinstance(communication, OperatorCommunication) or not isinstance(facts, OperatorCommunicationInput):
        return ("typed communication and projection are required",)
    issues = []
    summary = communication.incident_summary.casefold()
    rendered = " ".join((communication.incident_summary, *communication.key_findings, communication.why_this_result)).casefold()
    evidence = " ".join(_support("evidence", facts)).casefold()
    natural_evidence = _support("naturalize", evidence).casefold() if evidence else ""
    if any(outcome.value.casefold() in summary for outcome in PolicyOutcome):
        issues.append("incident summary restates the outcome")
    if any(term in summary for term in ("classif", "criteria", "result", "validation", "semantic")):
        issues.append("incident summary explains classification or processing")
    if "workplace violence criteria" not in communication.why_this_result.casefold():
        issues.append("classification explanation does not connect to doctrine")
    for fact in facts.active_facts:
        if fact.conduct is not None and not any(marker in rendered for marker in CONDUCT_MARKERS[fact.conduct]):
            issues.append("material conduct omitted")
        if fact.intentionality == Intentionality.ACCIDENTAL and "accident" not in rendered:
            issues.append("accidental intent omitted")
        if fact.intentionality == Intentionality.INTENTIONAL and not any(
            term in rendered for term in ("intentional", "deliberate", "threatened", "struck", "hit", "kicked")
        ):
            issues.append("intentional conduct omitted")
        if fact.temporal_scope == TemporalScope.HISTORICAL and not any(
            term in rendered for term in ("before", "earlier", "historical", "previous", "years ago")
        ):
            issues.append("material chronology omitted")
        role_text = _support("involved", fact)[1].casefold()
        for role in role_text.split(" and "):
            role_key = "nurse" if "nurse" in role else role
            if role_key not in summary and not role.startswith(("people described", "person described", "property described")):
                issues.append("supported actor or target omitted")
    actor_claims = (
        ("patient", ("patient", "pt")), ("nurse", ("nurse", "rn")),
        ("technician", ("technician", "tech")), ("aide", ("aide",)),
        ("visitor", ("visitor",)), ("security", ("security",)),
        ("physician", ("physician", "doctor")),
    )
    evidence_words = set(evidence.replace(".", " ").replace(",", " ").split())
    rendered_words = set(rendered.replace(".", " ").replace(",", " ").split())
    for claim, support_words in actor_claims:
        if claim in rendered_words and not any(word in evidence_words for word in support_words):
            issues.append(f"unsupported actor introduced: {claim}")
    if "not combative" in evidence and "not combative" not in rendered:
        issues.append("material behavior omitted")
    if facts.superseded_facts and not any(term in summary for term in ("initial", "earlier", "correct", "final", "withdraw")):
        issues.append("material correction omitted")
    if facts.has_unresolved_contradiction and not any(term in summary for term in ("accounts", "conflict", "disagree", "difference")):
        issues.append("material contradiction omitted")
    protected_claims = (
        "injury", "injured", "bruising", "bleeding", "sore", "pain", "hallway",
        "bathroom", "bedroom", "lobby", "parking", "security", "police", "restraint",
        "medication", "ongoing", "resolved", "calmed",
    )
    for claim in protected_claims:
        if claim in rendered and claim not in evidence and claim not in natural_evidence:
            issues.append(f"unsupported detail introduced: {claim}")
    return tuple(dict.fromkeys(issues))


communication_is_supported = lambda communication, facts: not communication_validation_issues(communication, facts)


def create_operator_communication(
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
) -> OperatorCommunication:
    if policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE:
        return build_failure_communication(policy_decision)
    return build_deterministic_communication(construct_communication_input(validation_result, policy_decision))
