"""Deterministic, presentation-only communication over repository authority."""

from typing import Dict, Optional

from src.comparison import ComparisonResult
from src.contracts import (
    AssertionStatus,
    CommunicationComparisonProjection,
    CommunicationPropositionFact,
    CommunicationRegexProjection,
    Completion,
    ConductKind,
    Contact,
    Direction,
    OperatorCommunication,
    OperatorCommunicationInput,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    RelationshipKind,
    SemanticIntentionality,
    TemporalScope,
    ValidationFailureStage,
    ValidationResult,
)


def construct_communication_input(
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
    regex_result: Dict[str, object],
    comparison: ComparisonResult,
    *,
    salesforce_preview_eligible: bool,
) -> OperatorCommunicationInput:
    """Copy validated facts into a narrow immutable presentation projection."""
    if not isinstance(validation_result, ValidationResult) or not validation_result.passed:
        raise ValueError("communication input requires successful validation")
    if not isinstance(policy_decision, PolicyDecision) or policy_decision.outcome == PolicyOutcome.WRITE_FAILED:
        raise ValueError("communication input requires a completed policy decision")
    if not isinstance(comparison, ComparisonResult):
        raise TypeError("communication input requires a ComparisonResult projection source")
    validated = validation_result.validated_envelope
    if validated is None:
        raise ValueError("communication input requires validated semantic facts")

    derived = {item.proposition_id: item for item in validated.derived.propositions}
    entity_labels = {item.entity_id: item.label for item in validated.envelope.entities}
    proposition_facts = tuple(
        CommunicationPropositionFact(
            actor_label=entity_labels.get(item.actor_ref),
            target_label=entity_labels.get(item.target.target_ref) if item.target.target_ref is not None else None,
            conduct_kind=item.conduct_kind,
            direction=derived[item.proposition_id].direction,
            completion=item.completion,
            contact=item.contact,
            temporal_scope=item.temporal_scope,
            intentionality=item.intentionality,
            assertion_status=item.assertion_status,
            active=derived[item.proposition_id].active,
        )
        for item in validated.envelope.propositions
    )
    matched_terms = regex_result.get("matched_terms", [])
    matched_patterns = regex_result.get("matched_patterns", [])
    match_count = len(matched_terms) + len(matched_patterns) if isinstance(matched_terms, list) and isinstance(matched_patterns, list) else 0
    return OperatorCommunicationInput(
        policy_outcome=policy_decision.outcome,
        policy_reason_codes=tuple(policy_decision.reason_codes),
        validation_status=validation_result.failure_stage,
        failure_provenance=policy_decision.failure_provenance,
        proposition_facts=proposition_facts,
        uncertainty_dimensions=tuple(item.dimension for item in validated.envelope.uncertainties),
        relationship_kinds=tuple(item.relationship_kind for item in validated.envelope.relationships),
        regex=CommunicationRegexProjection(
            detected=bool(regex_result.get("detected")),
            match_count=match_count,
        ),
        comparison=CommunicationComparisonProjection(
            semantic_validation_status=comparison.semantic_validation_status,
            classification_alignment=comparison.classification_alignment,
            material_difference_detected=comparison.material_difference_detected,
            display_status=comparison.display_status,
            observations=tuple(comparison.observations),
        ),
        salesforce_preview_eligible=salesforce_preview_eligible,
    )


def _active(facts: OperatorCommunicationInput) -> tuple[CommunicationPropositionFact, ...]:
    return tuple(item for item in facts.proposition_facts if item.active)


def _role(label: Optional[str], fallback: str = "person") -> str:
    """Return a concise human role while excluding identifier-like labels."""
    if label is None:
        return fallback
    words = label.strip().casefold().replace("_", " ").split()
    if words[:1] in (["a"], ["an"], ["the"]):
        words = words[1:]
    if not words or len(words) > 3:
        return fallback
    if any(not word.replace("-", "").isalpha() for word in words):
        return fallback
    return " ".join(words)


def _participant_findings(item: Optional[CommunicationPropositionFact]) -> list[str]:
    if item is None:
        return []
    findings: list[str] = []
    for label in (item.actor_label, item.target_label):
        role = _role(label, "")
        finding = f"{role.title()} identified" if role else ""
        if finding and finding.casefold() not in {value.casefold() for value in findings}:
            findings.append(finding)
    return findings


def _participant_phrase(role: str) -> str:
    if role in {"an object", "another person", "anyone", "someone", "somebody"}:
        return role
    return f"the {role}"


def _communication(summary: str, findings: list[str], why: str) -> OperatorCommunication:
    return OperatorCommunication(
        incident_summary=summary,
        key_findings=tuple(findings[:8]),
        why_this_result=why,
    )


def build_deterministic_communication(facts: OperatorCommunicationInput) -> OperatorCommunication:
    """Render concise operational fallback copy without adding incident facts."""
    if not isinstance(facts, OperatorCommunicationInput):
        raise TypeError("deterministic communication requires OperatorCommunicationInput")
    active = _active(facts)

    if facts.policy_outcome == PolicyOutcome.WRITE_UNCERTAIN:
        findings = _participant_findings(next(iter(active), None))
        if PolicyReasonCode.CONFLICTING_INFORMATION in facts.policy_reason_codes:
            summary = "The incident account contains conflicting information about possible current interpersonal violence."
            findings.extend(["Conflicting accounts identified", "Current event remains unclear"])
            why = "The AI understood that the supplied accounts conflict on a fact needed for the decision. Because the evidence does not establish one account over the other, the application criteria cannot be conclusively met or ruled out."
        else:
            summary = "The incident account indicates possible current interpersonal violence, but a material detail remains unclear."
            findings.extend(["Possible violence identified", "Material detail remains unclear"])
            why = "The AI found evidence of possible current interpersonal violence, but the supplied facts leave a decision-critical detail unresolved. That uncertainty prevents the application criteria from being conclusively met or ruled out."
        return _communication(summary, findings, why)

    if facts.policy_outcome == PolicyOutcome.WRITE_DETECTED:
        detected = next(
            (
                item for item in active
                if item.direction == Direction.INTERPERSONAL
                and item.assertion_status == AssertionStatus.AFFIRMED
            ),
            None,
        )
        findings = _participant_findings(detected)
        if detected is not None and detected.conduct_kind == ConductKind.PHYSICAL_CONDUCT:
            actor = _role(detected.actor_label)
            target = _role(detected.target_label, "another person")
            if detected.completion == Completion.ATTEMPTED:
                summary = f"The incident account shows that {_participant_phrase(actor)} attempted physical contact with {_participant_phrase(target)}, but no contact occurred."
                findings.extend(["Intentional assault attempted", "No physical contact"])
                why = "The AI understood the event as current, intentional, and directed toward another person. The supported attempt satisfies the application criteria even though physical contact did not occur."
            elif detected.contact == Contact.OCCURRED:
                summary = f"The incident account shows that {_participant_phrase(actor)} intentionally made physical contact with {_participant_phrase(target)} during the current event."
                findings.extend(["Intentional assault identified", "Physical contact confirmed"])
                why = "The AI understood the event as current, intentional physical conduct directed toward another person. The supplied account supports completed contact, which satisfies the application criteria for a detected result."
            else:
                summary = f"The incident account shows current intentional physical conduct by {_participant_phrase(actor)} toward {_participant_phrase(target)}."
                findings.extend(["Intentional assault identified", "Current event confirmed"])
                why = "The AI understood the event as current, intentional physical conduct directed toward another person. Those supported findings satisfy the application criteria for a detected result."
        else:
            actor = _role(detected.actor_label) if detected is not None else "person"
            target = _role(detected.target_label, "another person") if detected is not None else "another person"
            summary = f"The incident account shows that {_participant_phrase(actor)} made a current threat toward {_participant_phrase(target)}."
            findings.extend(["Verbal threat identified", "Current threat confirmed"])
            why = "The AI understood the supplied words as a current threat directed toward another person. That supported threat satisfies the application criteria for a detected result."
        return _communication(summary, findings, why)

    representative = next(iter(active), None)
    findings = _participant_findings(representative)
    accidental = next(
        (item for item in active if item.intentionality == SemanticIntentionality.ACCIDENTAL),
        None,
    )
    historical = next(
        (item for item in facts.proposition_facts if item.temporal_scope == TemporalScope.HISTORICAL),
        None,
    )
    if accidental is not None:
        actor = _role(accidental.actor_label)
        target = _role(accidental.target_label, "another person")
        summary = f"The incident account describes accidental contact between {_participant_phrase(actor)} and {_participant_phrase(target)}, not intentional interpersonal violence."
        findings = _participant_findings(accidental) + ["Accidental contact identified", "Intentional violence not supported"]
        why = "The AI understood that contact occurred but was accidental. Because the supplied facts do not support intentional conduct, the event does not satisfy the application criteria for a detected result."
    elif historical is not None:
        actor = _role(historical.actor_label)
        target = _role(historical.target_label, "another person")
        summary = f"The incident account describes interpersonal violence involving {_participant_phrase(actor)} and {_participant_phrase(target)} as historical context, not a current event."
        findings = _participant_findings(historical) + ["Historical event identified", "No current violence"]
        why = "The AI understood the violence reference as historical rather than part of the current incident. Because the supplied evidence does not establish current conduct, the application criteria are not satisfied."
    elif RelationshipKind.SUPERSEDES in facts.relationship_kinds or any(
        item.active and item.assertion_status == AssertionStatus.NEGATED for item in facts.proposition_facts
    ):
        actor = _role(representative.actor_label) if representative is not None else "person"
        summary = f"The incident account includes a correction or denial involving {_participant_phrase(actor)} and does not establish current interpersonal violence."
        findings.extend(["Correction or denial identified", "Current violence not supported"])
        why = "The AI understood that the supplied account corrected or denied the relevant conduct. The remaining evidence does not support current interpersonal violence, so the application criteria are not satisfied."
    elif any(item.active and item.direction == Direction.OBJECT_DIRECTED for item in facts.proposition_facts):
        item = next(item for item in active if item.direction == Direction.OBJECT_DIRECTED)
        actor = _role(item.actor_label)
        target = _role(item.target_label, "an object")
        summary = f"The incident account describes {_participant_phrase(actor)} directing conduct at {_participant_phrase(target)} rather than another person."
        findings.extend(["Object-directed conduct identified", "No person targeted"])
        why = "The AI understood that the conduct was directed at an object. Because the supplied evidence does not show conduct toward another person, the application criteria are not satisfied."
    elif any(item.active and item.direction == Direction.SELF_DIRECTED for item in facts.proposition_facts):
        item = next(item for item in active if item.direction == Direction.SELF_DIRECTED)
        actor = _role(item.actor_label)
        summary = f"The incident account describes self-directed conduct by {_participant_phrase(actor)} rather than conduct toward another person."
        findings.extend(["Self-directed conduct identified", "No other person targeted"])
        why = "The AI understood the conduct as self-directed. Because the supplied evidence does not show conduct toward another person, the application criteria are not satisfied."
    else:
        summary = "The incident account does not establish current interpersonal violence or a current threat."
        findings.extend(["No current violence", "No current threat"])
        why = "The AI did not find supplied evidence of current violence or a current threat directed toward another person. Without those supported findings, the application criteria are not satisfied."
    return _communication(summary, findings, why)


def build_failure_communication(
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
) -> OperatorCommunication:
    """Present an explicit authoritative failure without repairing missing semantics."""
    if not isinstance(validation_result, ValidationResult):
        raise TypeError("failure communication requires ValidationResult")
    if not isinstance(policy_decision, PolicyDecision) or policy_decision.outcome != PolicyOutcome.WRITE_FAILED:
        raise ValueError("failure communication requires a failed policy decision")
    if policy_decision.failure_provenance is None:
        raise ValueError("failure communication requires explicit failure provenance")
    return OperatorCommunication(
        incident_summary="The incident could not be assessed because reliable incident details were unavailable.",
        key_findings=("Review could not complete", "Incident facts unavailable"),
        why_this_result="The AI analysis did not yield enough reliable information to complete the review, so the application criteria could not be evaluated.",
    )


def create_operator_communication(
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
    regex_result: Dict[str, object],
    comparison: ComparisonResult,
    *,
    salesforce_preview_eligible: bool,
) -> OperatorCommunication:
    if policy_decision.outcome == PolicyOutcome.WRITE_FAILED:
        return build_failure_communication(validation_result, policy_decision)
    facts = construct_communication_input(
        validation_result,
        policy_decision,
        regex_result,
        comparison,
        salesforce_preview_eligible=salesforce_preview_eligible,
    )
    return build_deterministic_communication(facts)
