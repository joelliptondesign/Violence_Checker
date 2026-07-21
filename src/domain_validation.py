"""Deterministic fact, evidence, correction, and contradiction validation."""

import re
from collections import Counter, defaultdict

from src.contracts import (
    AssertionStatus,
    Conduct,
    DomainValidationResult,
    DomainValidationStatus,
    FactDirection,
    Intentionality,
    MaterialAttribute,
    ResolutionStatus,
    TemporalScope,
    TrueNorthSemanticEnvelope,
    UncertaintyDimension,
    ValidationIssue,
    ValidationIssueCode,
)


def _issue(code: ValidationIssueCode, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def _has_cycle(edges: list[tuple[str, str]]) -> bool:
    graph: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        graph[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(neighbor) for neighbor in graph[node]):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in list(graph))


def _support_text(fact, attribute: MaterialAttribute) -> str:
    return " ".join(
        item.excerpt.casefold()
        for item in fact.evidence
        if attribute in item.supports
    )


def _contains_denial(text: str) -> bool:
    return bool(re.search(r"\b(denied|denies|did not|didn't|never|no)\b", text))


def _contains_later_affirmation(text: str) -> bool:
    marker_and_action = re.search(
        r"\b(?:later\s+(?:confirmed|corrected)|correction|actually)\b.{0,120}"
        r"(?<!did not )(?<!didn't )(?:intentionally\s+)?"
        r"(?:hit|punched|struck|shoved|kicked|smashed|damaged|broke|threatened|swung at)\b",
        text,
    )
    return bool(marker_and_action)


def _contains_correction_marker(text: str) -> bool:
    return bool(re.search(
        r"\b(?:correction|corrected|updated\s+(?:note|report)|later\s+(?:confirmed|corrected))\b",
        text.casefold(),
    ))


def _contains_historical_temporal_evidence(text: str) -> bool:
    return bool(re.search(
        r"\b(?:"
        r"historical|history\s+of|previously|previous\s+(?:admission|visit|encounter)|"
        r"prior\s+(?:incident|event|admission|visit|encounter)|"
        r"last\s+(?:night|week|month|year)|"
        r"earlier\s+this\s+(?:week|month|year)|"
        r"\d+\s+(?:days?|weeks?|months?|years?|yrs?)\s+ago|"
        r"years?\s+ago|yrs?\s+ago"
        r")\b",
        text,
    ))


def _contains_unresolved_temporal_evidence(text: str) -> bool:
    return bool(re.search(
        r"\b(?:"
        r"unclear\s+whether\b.{0,120}\b(?:current|this\s+incident|during\s+the\s+current\s+event)|"
        r"(?:timing|timeframe|temporal\s+scope)\s+(?:is\s+)?(?:unclear|unknown|unresolved|not\s+recorded)|"
        r"conflicting\s+timing\s+accounts?|"
        r"copied[- ]forward\s+documentation\b.{0,120}\b(?:unresolved|unclear|unknown)\s+timing|"
        r"current\s+incident\s+fact\b.{0,120}\bunresolved|"
        r"insufficient\s+information\b.{0,120}\b(?:current|this\s+incident|during\s+the\s+current\s+event)|"
        r"may\s+have\s+happened\b.{0,120}\binsufficient\s+information"
        r")",
        text,
    ))


def _contains_current_blocking_temporal_ambiguity(text: str) -> bool:
    return bool(re.search(
        r"\b(?:"
        r"unclear\s+whether\b.{0,120}\b(?:current|this\s+incident|during\s+the\s+current\s+event)|"
        r"(?:timing|timeframe|temporal\s+scope)\s+(?:is\s+)?(?:unclear|unknown|unresolved|not\s+recorded)|"
        r"conflicting\s+timing\s+accounts?|"
        r"copied[- ]forward\s+documentation\b.{0,120}\b(?:unresolved|unclear|unknown)\s+timing|"
        r"insufficient\s+information\b.{0,120}\b(?:current|this\s+incident|during\s+the\s+current\s+event)"
        r")",
        text,
    ))


def validate_semantic_domain(
    envelope: TrueNorthSemanticEnvelope,
    *,
    normalized_narrative: str,
) -> DomainValidationResult:
    """Enforce bounded encoded rules without unrestricted entailment or repair."""
    if not isinstance(envelope, TrueNorthSemanticEnvelope):
        raise TypeError("domain validation requires a schema-valid TrueNorthSemanticEnvelope")

    issues: list[ValidationIssue] = []
    fact_index = {fact.fact_id: index for index, fact in enumerate(envelope.facts)}
    correction_edges: list[tuple[str, str]] = []
    correction_targets: list[str] = []
    groups: dict[str, list[object]] = defaultdict(list)

    for index, fact in enumerate(envelope.facts):
        field = f"facts.{index}"
        uncertainty = set(fact.uncertainty)
        supports = {attribute for item in fact.evidence for attribute in item.supports}
        required = {
            MaterialAttribute.INTENTIONALITY,
            MaterialAttribute.TEMPORAL_SCOPE,
            MaterialAttribute.ASSERTION_STATUS,
        }
        if fact.conduct is not None or UncertaintyDimension.CONDUCT in uncertainty:
            required.add(MaterialAttribute.CONDUCT)
        if fact.direction != FactDirection.UNKNOWN or UncertaintyDimension.DIRECTION in uncertainty:
            required.add(MaterialAttribute.DIRECTION)
        if fact.supersedes_fact_id is not None:
            required.add(MaterialAttribute.SUPERSESSION)
        if fact.contradiction_group is not None:
            required.add(MaterialAttribute.CONTRADICTION)
        for attribute in sorted(required - supports, key=lambda value: value.value):
            issues.append(_issue(
                ValidationIssueCode.MISSING_EVIDENCE_SUPPORT,
                f"{field}.evidence",
                f"Fact evidence does not cover {attribute.value}.",
            ))

        unresolved_pairs = (
            (fact.conduct is None, UncertaintyDimension.CONDUCT),
            (fact.direction == FactDirection.UNKNOWN, UncertaintyDimension.DIRECTION),
            (fact.intentionality == Intentionality.UNRESOLVED, UncertaintyDimension.INTENTIONALITY),
            (fact.temporal_scope == TemporalScope.UNRESOLVED, UncertaintyDimension.TEMPORAL_SCOPE),
            (fact.assertion_status in {AssertionStatus.UNRESOLVED, AssertionStatus.DISPUTED}, UncertaintyDimension.ASSERTION_STATUS),
        )
        for unresolved, dimension in unresolved_pairs:
            if unresolved != (dimension in uncertainty):
                issues.append(_issue(
                    ValidationIssueCode.INVALID_UNCERTAINTY,
                    f"{field}.uncertainty",
                    f"{dimension.value} uncertainty must exactly match unresolved semantic state.",
                ))

        if fact.conduct == Conduct.SELF_HARM and fact.direction != FactDirection.SELF_DIRECTED:
            issues.append(_issue(ValidationIssueCode.INVALID_FACT_COMBINATION, field, "Self-harm requires self-directed direction."))
        if fact.conduct == Conduct.PROPERTY_VIOLENCE:
            if fact.direction != FactDirection.OBJECT_DIRECTED or fact.intentionality != Intentionality.INTENTIONAL:
                issues.append(_issue(ValidationIssueCode.INVALID_FACT_COMBINATION, field, "Property violence requires intentional object-directed conduct."))

        assertion_text = _support_text(fact, MaterialAttribute.ASSERTION_STATUS)
        if fact.assertion_status == AssertionStatus.AFFIRMED and _contains_denial(assertion_text) and not _contains_later_affirmation(assertion_text):
            issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, f"{field}.assertion_status", "Denial evidence cannot support an affirmed fact."))
        intentionality_text = _support_text(fact, MaterialAttribute.INTENTIONALITY)
        if fact.intentionality == Intentionality.INTENTIONAL and re.search(r"\b(accident|accidental|accidentally|unintentional)\b", intentionality_text):
            issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, f"{field}.intentionality", "Accidental evidence cannot support intentional conduct."))
        temporal_text = _support_text(fact, MaterialAttribute.TEMPORAL_SCOPE)
        if fact.temporal_scope == TemporalScope.CURRENT and (
            _contains_historical_temporal_evidence(temporal_text)
            or _contains_current_blocking_temporal_ambiguity(temporal_text)
        ):
            issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, f"{field}.temporal_scope", "Historical or materially ambiguous timing evidence cannot support current scope."))
        if fact.temporal_scope == TemporalScope.HISTORICAL and not _contains_historical_temporal_evidence(temporal_text):
            issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, f"{field}.temporal_scope", "Historical scope requires explicit historical timing evidence."))
        if fact.temporal_scope == TemporalScope.UNRESOLVED and not _contains_unresolved_temporal_evidence(temporal_text):
            issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, f"{field}.temporal_scope", "Unresolved temporal scope requires explicit materially ambiguous timing evidence."))
        conduct_text = _support_text(fact, MaterialAttribute.CONDUCT)
        if (
            fact.conduct == Conduct.PHYSICAL_CONTACT
            and fact.assertion_status == AssertionStatus.AFFIRMED
            and re.search(r"\b(no|without|did not|didn't)\s+(physical\s+)?(contact|hit|strike|struck|shove|shoved|touch)\b", conduct_text)
        ):
            issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, f"{field}.conduct", "No-contact evidence cannot support physical contact."))
        if fact.conduct == Conduct.PHYSICAL_ATTEMPT:
            completed = re.search(r"\b(hit|punched|struck|shoved|made contact|contact occurred)\b", conduct_text)
            attempted = re.search(r"\b(attempt|tried|missed|swung at|without contact)\b", conduct_text)
            if completed and not attempted:
                issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, f"{field}.conduct", "Completed-contact evidence alone cannot support a physical attempt."))

        prior_sort_key = None
        for evidence_index, evidence in enumerate(fact.evidence):
            evidence_field = f"{field}.evidence.{evidence_index}"
            position = normalized_narrative.find(evidence.excerpt)
            if position < 0:
                issues.append(_issue(ValidationIssueCode.EVIDENCE_NOT_CONTAINED, f"{evidence_field}.excerpt", "Evidence must be an exact narrative substring."))
            if evidence.start_offset is not None:
                if normalized_narrative[evidence.start_offset:evidence.end_offset] != evidence.excerpt:
                    issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_IDENTITY, evidence_field, "Evidence offsets do not identify the exact excerpt."))
            sort_key = (
                position if position >= 0 else len(normalized_narrative),
                -len(evidence.excerpt),
                evidence.excerpt,
                tuple(attribute.value for attribute in evidence.supports),
            )
            if prior_sort_key is not None and sort_key < prior_sort_key:
                issues.append(_issue(ValidationIssueCode.INVALID_COLLECTION_ORDER, f"{field}.evidence", "Fact evidence is not in canonical narrative order."))
            prior_sort_key = sort_key

        if fact.supersedes_fact_id is not None:
            correction_edges.append((fact.fact_id, fact.supersedes_fact_id))
            correction_targets.append(fact.supersedes_fact_id)
            if fact.supersedes_fact_id == fact.fact_id or fact.supersedes_fact_id not in fact_index:
                issues.append(_issue(ValidationIssueCode.INVALID_CORRECTION_REFERENCE, f"{field}.supersedes_fact_id", "Correction reference must resolve to a distinct fact."))
            elif fact_index[fact.supersedes_fact_id] >= index:
                issues.append(_issue(ValidationIssueCode.INVALID_CORRECTION_REFERENCE, f"{field}.supersedes_fact_id", "A correction must reference an earlier canonical fact."))
        if fact.contradiction_group is not None:
            groups[fact.contradiction_group].append(fact)

    if _has_cycle(correction_edges):
        issues.append(_issue(ValidationIssueCode.CORRECTION_CYCLE, "facts.supersedes_fact_id", "Correction references must be acyclic."))
    target_counts = Counter(correction_targets)
    for target, count in sorted(target_counts.items()):
        if count > 1:
            issues.append(_issue(ValidationIssueCode.INVALID_CORRECTION_REFERENCE, target, "A fact cannot have multiple controlling corrections."))
    target_set = set(correction_targets)
    if (
        _contains_correction_marker(normalized_narrative)
        and not correction_edges
        and all(fact.resolution_status == ResolutionStatus.ACTIVE for fact in envelope.facts)
    ):
        issues.append(_issue(
            ValidationIssueCode.INVALID_CORRECTION_REFERENCE,
            "facts.supersedes_fact_id",
            "An explicit correction marker requires a supported correction reference.",
        ))
    for fact in envelope.facts:
        if fact.fact_id in target_set and fact.resolution_status != ResolutionStatus.SUPERSEDED:
            issues.append(_issue(ValidationIssueCode.INVALID_CORRECTION_REFERENCE, fact.fact_id, "A corrected fact must be superseded."))
        if fact.resolution_status == ResolutionStatus.SUPERSEDED and fact.fact_id not in target_set:
            issues.append(_issue(ValidationIssueCode.INVALID_CORRECTION_REFERENCE, fact.fact_id, "A superseded fact requires a later correction reference."))
    for group_id, members in sorted(groups.items()):
        if len(members) < 2:
            issues.append(_issue(ValidationIssueCode.INVALID_CONTRADICTION_GROUP, group_id, "A contradiction group requires at least two facts."))
        for member in members:
            if member.resolution_status != ResolutionStatus.ACTIVE or member.assertion_status != AssertionStatus.DISPUTED:
                issues.append(_issue(ValidationIssueCode.INVALID_CONTRADICTION_GROUP, member.fact_id, "Unresolved contradiction members must be active and disputed."))
    for fact in envelope.facts:
        if fact.assertion_status == AssertionStatus.DISPUTED and fact.contradiction_group is None:
            issues.append(_issue(ValidationIssueCode.INVALID_CONTRADICTION_GROUP, fact.fact_id, "A disputed fact requires a contradiction group."))

    if issues:
        return DomainValidationResult(status=DomainValidationStatus.FAILED, issues=issues)
    return DomainValidationResult(status=DomainValidationStatus.PASSED)
