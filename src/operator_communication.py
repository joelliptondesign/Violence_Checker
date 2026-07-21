"""Deterministic presentation-only communication from validated True North facts."""

from __future__ import annotations

from src.contracts import (
    AssertionStatus,
    CommunicationFact,
    Conduct,
    Intentionality,
    OperatorCommunication,
    OperatorCommunicationInput,
    PolicyDecision,
    PolicyOutcome,
    ResolutionStatus,
    TemporalScope,
    ValidationResult,
)


def _project_fact(fact) -> CommunicationFact:
    return CommunicationFact(
        conduct=fact.conduct,
        direction=fact.direction,
        intentionality=fact.intentionality,
        temporal_scope=fact.temporal_scope,
        assertion_status=fact.assertion_status,
        resolution_status=fact.resolution_status,
        uncertainty=tuple(fact.uncertainty),
    )


def construct_communication_input(
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
) -> OperatorCommunicationInput:
    """Project only validated operational meaning needed by the three output sections."""
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
        active_facts=tuple(
            _project_fact(fact) for fact in envelope.facts if fact.fact_id in active_ids
        ),
        superseded_facts=tuple(
            _project_fact(fact) for fact in envelope.facts if fact.fact_id in superseded_ids
        ),
        has_unresolved_contradiction=bool(derived.contradiction_groups),
    )


def _communication(summary: str, findings: tuple[str, ...], why: str) -> OperatorCommunication:
    return OperatorCommunication(
        incident_summary=summary,
        key_findings=findings,
        why_this_result=why,
    )


def _detected_fact(facts: OperatorCommunicationInput) -> CommunicationFact | None:
    return next((
        fact for fact in facts.active_facts
        if fact.conduct is not None
        and fact.intentionality == Intentionality.INTENTIONAL
        and fact.temporal_scope == TemporalScope.CURRENT
        and fact.assertion_status == AssertionStatus.AFFIRMED
    ), None)


def build_deterministic_communication(facts: OperatorCommunicationInput) -> OperatorCommunication:
    """Render bounded fallback copy without inventing actors or consequences."""
    if not isinstance(facts, OperatorCommunicationInput):
        raise TypeError("deterministic communication requires OperatorCommunicationInput")

    if facts.outcome == PolicyOutcome.UNCERTAIN:
        if facts.has_unresolved_contradiction:
            return _communication(
                "The incident account contains unresolved conflicting information about potentially qualifying conduct.",
                ("Conflicting accounts remain", "Outcome remains uncertain"),
                "The validated accounts conflict on information required for classification, and no supported correction establishes a controlling account.",
            )
        return _communication(
            "The incident account contains potentially qualifying conduct, but a classification-critical detail remains unresolved.",
            ("Potential conduct identified", "Material detail unresolved"),
            "The validated facts do not settle conduct, intent, timing, or assertion state sufficiently to produce a definitive result.",
        )

    if facts.outcome == PolicyOutcome.VIOLENCE_DETECTED:
        detected = _detected_fact(facts)
        if detected is None or detected.conduct is None:
            raise ValueError("detected communication requires a qualifying active fact")
        content = {
            Conduct.VERBAL_THREAT: (
                "An explicit threat of physical violence was reported during the current incident.",
                ("Verbal threat identified", "Current incident confirmed"),
                "The validated facts establish an active, affirmed, intentional, current threat of physical violence.",
            ),
            Conduct.PHYSICAL_ATTEMPT: (
                "An intentional attempt at physical violence was reported during the current incident.",
                ("Physical attempt identified", "Current incident confirmed"),
                "The validated facts establish active, affirmed, intentional, current attempted physical violence.",
            ),
            Conduct.PHYSICAL_CONTACT: (
                "Intentional physical violence involving contact was reported during the current incident.",
                ("Physical violence identified", "Contact conduct confirmed"),
                "The validated facts establish active, affirmed, intentional, current physical contact.",
            ),
            Conduct.SELF_HARM: (
                "Intentional self-directed violence was reported during the current incident.",
                ("Self-directed violence identified", "Current incident confirmed"),
                "The validated facts establish active, affirmed, intentional, current self-directed violence.",
            ),
            Conduct.PROPERTY_VIOLENCE: (
                "Intentional property-directed violence was reported during the current incident.",
                ("Property violence identified", "Current incident confirmed"),
                "The validated facts establish active, affirmed, intentional, current property-directed violence.",
            ),
        }[detected.conduct]
        return _communication(*content)

    if facts.outcome != PolicyOutcome.NO_VIOLENCE_DETECTED:
        raise ValueError("unsupported deterministic communication outcome")
    accidental = next((
        fact for fact in facts.active_facts
        if fact.intentionality == Intentionality.ACCIDENTAL
    ), None)
    historical = next((
        fact for fact in facts.active_facts
        if fact.temporal_scope == TemporalScope.HISTORICAL
    ), None)
    denied = next((
        fact for fact in facts.active_facts
        if fact.assertion_status == AssertionStatus.DENIED
    ), None)
    if accidental is not None:
        return _communication(
            "The incident account describes accidental conduct rather than intentional violence.",
            ("Accidental conduct identified", "Intentional violence unsupported"),
            "The validated facts establish accidental conduct, which does not satisfy the intentional-conduct requirement.",
        )
    if historical is not None:
        return _communication(
            "The incident account describes historical conduct rather than violence during the current incident.",
            ("Historical conduct identified", "No current violence"),
            "The validated facts place the conduct outside the current incident, so it does not satisfy the current-scope requirement.",
        )
    if facts.superseded_facts:
        return _communication(
            "A supported correction supersedes the earlier allegation, and the active facts do not establish current qualifying violence.",
            ("Correction controls outcome", "Earlier account superseded"),
            "Deterministic classification excludes superseded facts and evaluates only the supported active correction.",
        )
    if denied is not None:
        return _communication(
            "The active incident facts deny the potentially qualifying conduct.",
            ("Conduct explicitly denied", "Violence not established"),
            "The validated active assertion is denied rather than affirmed, so it does not satisfy the classification criteria.",
        )
    return _communication(
        "Complete admissible analysis contains no active facts that establish intentional current qualifying violence.",
        ("No qualifying violence", "Analysis completed"),
        "The validated facts contain no active, affirmed, intentional, current qualifying conduct and no material unresolved classification fact.",
    )


def build_failure_communication(policy_decision: PolicyDecision) -> OperatorCommunication:
    """Describe an unable-to-determine result without fabricating incident facts."""
    if not isinstance(policy_decision, PolicyDecision) or policy_decision.outcome != PolicyOutcome.UNABLE_TO_DETERMINE:
        raise ValueError("failure communication requires Unable to Determine")
    return _communication(
        "The incident could not be classified because a complete admissible analysis was unavailable.",
        ("Review could not complete", "Outcome unavailable"),
        "The application did not receive sufficient validated information to apply the classification criteria deterministically.",
    )


def create_operator_communication(
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
) -> OperatorCommunication:
    if policy_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE:
        return build_failure_communication(policy_decision)
    return build_deterministic_communication(
        construct_communication_input(validation_result, policy_decision)
    )
