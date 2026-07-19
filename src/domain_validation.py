"""Deterministic proposition-oriented violence-domain admissibility."""

from src.contracts import (
    AssertionStatus,
    Completion,
    ConductKind,
    Contact,
    Direction,
    DomainValidationResult,
    DomainValidationStatus,
    EntityKind,
    EvidenceSubjectKind,
    EvidenceSupportRole,
    RelationshipKind,
    SemanticIntentionality,
    TargetKind,
    UncertaintyDimension,
    ValidationIssue,
    ValidationIssueCode,
    ViolenceSemanticEnvelope,
)


def _issue(code: ValidationIssueCode, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def _direction(proposition, entities) -> Direction:
    target = proposition.target
    if target.target_kind == TargetKind.SELF:
        return Direction.SELF_DIRECTED
    if target.target_kind != TargetKind.ENTITY or target.target_ref is None:
        return Direction.UNDETERMINED
    actor = entities[proposition.actor_ref]
    target_entity = entities[target.target_ref]
    if target_entity.entity_kind == EntityKind.OBJECT:
        return Direction.OBJECT_DIRECTED
    if target_entity.entity_kind in {EntityKind.PERSON, EntityKind.PEOPLE_COLLECTIVE}:
        if actor.entity_kind == EntityKind.UNSPECIFIED or proposition.actor_ref == target.target_ref:
            return Direction.UNDETERMINED
        return Direction.INTERPERSONAL
    return Direction.UNDETERMINED


def _has_cycle(edges: list[tuple[str, str]]) -> bool:
    graph: dict[str, list[str]] = {}
    for source, target in edges:
        graph.setdefault(source, []).append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for neighbor in graph.get(node, []):
            if visit(neighbor):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def _enum_rank(value) -> int:
    return list(type(value)).index(value)


def _check_canonical_order(
    issues: list[ValidationIssue],
    *,
    field: str,
    actual: list[str],
    expected: list[str],
) -> None:
    if actual != expected:
        issues.append(
            _issue(
                ValidationIssueCode.INVALID_COLLECTION_ORDER,
                field,
                f"Collection is not canonical; expected {expected}.",
            )
        )


def validate_semantic_domain(
    envelope: ViolenceSemanticEnvelope,
    *,
    normalized_narrative: str,
) -> DomainValidationResult:
    """Validate encoded coherence and exact evidence without inference or repair."""
    if not isinstance(envelope, ViolenceSemanticEnvelope):
        raise TypeError("domain validation requires a schema-valid ViolenceSemanticEnvelope")

    issues: list[ValidationIssue] = []
    entities = {item.entity_id: item for item in envelope.entities}
    propositions = {item.proposition_id: item for item in envelope.propositions}
    relationships = {item.relationship_id: item for item in envelope.relationships}
    uncertainties = {item.uncertainty_id: item for item in envelope.uncertainties}

    evidence_positions = {
        item.evidence_id: normalized_narrative.find(item.text)
        for item in envelope.evidence_excerpts
    }
    proposition_index = {item.proposition_id: index for index, item in enumerate(envelope.propositions)}
    # Entity and proposition appearance order is represented by their sequential
    # identifiers. Exact excerpts deliberately have no authoritative offsets, so
    # validation cannot independently reorder multiple subjects sharing one excerpt
    # without semantic inference.
    _check_canonical_order(
        issues,
        field="relationships",
        actual=[item.relationship_id for item in envelope.relationships],
        expected=[
            item.relationship_id
            for item in sorted(
                envelope.relationships,
                key=lambda item: (
                    proposition_index[item.source_proposition_ref],
                    _enum_rank(item.relationship_kind),
                    proposition_index[item.target_proposition_ref],
                    item.relationship_id,
                ),
            )
        ],
    )
    _check_canonical_order(
        issues,
        field="uncertainties",
        actual=[item.uncertainty_id for item in envelope.uncertainties],
        expected=[
            item.uncertainty_id
            for item in sorted(
                envelope.uncertainties,
                key=lambda item: (
                    proposition_index[item.proposition_ref],
                    _enum_rank(item.dimension),
                    item.uncertainty_id,
                ),
            )
        ],
    )
    _check_canonical_order(
        issues,
        field="evidence_excerpts",
        actual=[item.evidence_id for item in envelope.evidence_excerpts],
        expected=[
            item.evidence_id
            for item in sorted(
                envelope.evidence_excerpts,
                key=lambda item: (
                    evidence_positions[item.evidence_id] if evidence_positions[item.evidence_id] >= 0 else len(normalized_narrative),
                    -len(item.text),
                    item.text,
                ),
            )
        ],
    )
    _check_canonical_order(
        issues,
        field="evidence_supports",
        actual=[item.support_id for item in envelope.evidence_supports],
        expected=[
            item.support_id
            for item in sorted(
                envelope.evidence_supports,
                key=lambda item: (
                    item.evidence_ref,
                    _enum_rank(item.subject_kind),
                    item.subject_ref,
                    _enum_rank(item.role),
                    item.support_id,
                ),
            )
        ],
    )

    for index, proposition in enumerate(envelope.propositions):
        field = f"propositions.{index}"
        direction = _direction(proposition, entities)
        if proposition.target.target_kind == TargetKind.ENTITY and proposition.target.target_ref == proposition.actor_ref:
            issues.append(_issue(ValidationIssueCode.INVALID_TARGET_REFERENCE, f"{field}.target", "Self direction must use target_kind self."))
        if proposition.conduct_kind == ConductKind.THREAT_EXPRESSION:
            if proposition.completion not in {Completion.THREATENED, Completion.UNDETERMINED} or proposition.contact != Contact.NOT_APPLICABLE:
                issues.append(_issue(ValidationIssueCode.INVALID_CONDUCT_COMBINATION, field, "Threat expression requires threatened or undetermined completion and not-applicable contact."))
        elif proposition.conduct_kind == ConductKind.PHYSICAL_CONDUCT:
            if proposition.completion not in {Completion.ATTEMPTED, Completion.COMPLETED, Completion.UNDETERMINED}:
                issues.append(_issue(ValidationIssueCode.INVALID_CONDUCT_COMBINATION, field, "Physical conduct has invalid completion."))
            if proposition.completion == Completion.ATTEMPTED and proposition.contact != Contact.DID_NOT_OCCUR:
                issues.append(_issue(ValidationIssueCode.INVALID_CONDUCT_COMBINATION, field, "Attempted physical conduct requires did-not-occur contact."))
            if proposition.completion == Completion.COMPLETED and proposition.contact != Contact.OCCURRED:
                issues.append(_issue(ValidationIssueCode.INVALID_CONDUCT_COMBINATION, field, "Completed physical conduct requires occurred contact."))
        elif proposition.conduct_kind == ConductKind.CONTACT_ONLY:
            if proposition.completion != Completion.COMPLETED or proposition.contact != Contact.OCCURRED:
                issues.append(_issue(ValidationIssueCode.INVALID_CONDUCT_COMBINATION, field, "Contact-only conduct requires completed and occurred."))
        elif proposition.conduct_kind == ConductKind.THREATENING_MOVEMENT:
            if proposition.completion not in {Completion.NOT_APPLICABLE, Completion.UNDETERMINED}:
                issues.append(_issue(ValidationIssueCode.INVALID_CONDUCT_COMBINATION, field, "Threatening movement cannot be upgraded to attempted or completed conduct."))
        if proposition.intentionality == SemanticIntentionality.ACCIDENTAL and proposition.conduct_kind not in {ConductKind.CONTACT_ONLY, ConductKind.PHYSICAL_CONDUCT}:
            issues.append(_issue(ValidationIssueCode.INVALID_CONDUCT_COMBINATION, f"{field}.intentionality", "Accidental intentionality is limited to contact or physical conduct."))
        if direction == Direction.INTERPERSONAL and proposition.target.target_kind != TargetKind.ENTITY:
            issues.append(_issue(ValidationIssueCode.INVALID_TARGET_REFERENCE, f"{field}.target", "Interpersonal direction requires an entity target."))

    seen_relationships: set[tuple[object, str, str]] = set()
    supersession_edges: list[tuple[str, str]] = []
    negation_edges: list[tuple[str, str]] = []
    for index, relationship in enumerate(envelope.relationships):
        field = f"relationships.{index}"
        key = (
            relationship.relationship_kind,
            relationship.source_proposition_ref,
            relationship.target_proposition_ref,
        )
        if key in seen_relationships:
            issues.append(_issue(ValidationIssueCode.INVALID_RELATIONSHIP, field, "Duplicate relationship is not allowed."))
        seen_relationships.add(key)
        source = propositions[relationship.source_proposition_ref]
        target = propositions[relationship.target_proposition_ref]
        if relationship.relationship_kind == RelationshipKind.NEGATES:
            negation_edges.append((source.proposition_id, target.proposition_id))
            if source.assertion_status != AssertionStatus.NEGATED:
                issues.append(_issue(ValidationIssueCode.INVALID_RELATIONSHIP, field, "Negates must originate from a negated proposition."))
        elif relationship.relationship_kind == RelationshipKind.SUPERSEDES:
            supersession_edges.append((source.proposition_id, target.proposition_id))
            if proposition_index[source.proposition_id] <= proposition_index[target.proposition_id]:
                issues.append(_issue(ValidationIssueCode.INVALID_RELATIONSHIP, field, "Supersedes must point from the later proposition to the earlier proposition."))
        elif source.model_dump(exclude={"proposition_id", "attribution"}) == target.model_dump(exclude={"proposition_id", "attribution"}):
            issues.append(_issue(ValidationIssueCode.INVALID_RELATIONSHIP, field, "Identical propositions cannot conflict."))
    if _has_cycle(supersession_edges) or _has_cycle(negation_edges):
        issues.append(_issue(ValidationIssueCode.RELATIONSHIP_CYCLE, "relationships", "Directed semantic relationships must be acyclic."))

    conflict_dimensions: dict[str, set[UncertaintyDimension]] = {}
    for relationship in envelope.relationships:
        if relationship.relationship_kind == RelationshipKind.CONFLICTS_WITH:
            for proposition_id in (relationship.source_proposition_ref, relationship.target_proposition_ref):
                conflict_dimensions.setdefault(proposition_id, set()).update(relationship.disputed_dimensions)
    for index, uncertainty in enumerate(envelope.uncertainties):
        proposition = propositions[uncertainty.proposition_ref]
        unresolved = {
            UncertaintyDimension.ACTOR_IDENTITY: entities[proposition.actor_ref].entity_kind == EntityKind.UNSPECIFIED,
            UncertaintyDimension.TARGET_IDENTITY: (
                proposition.target.target_kind == TargetKind.UNDETERMINED
                or (
                    proposition.target.target_ref is not None
                    and entities[proposition.target.target_ref].entity_kind == EntityKind.UNSPECIFIED
                )
            ),
            UncertaintyDimension.CONDUCT_TYPE: proposition.conduct_kind == ConductKind.UNDETERMINED,
            UncertaintyDimension.DIRECTION: _direction(proposition, entities) == Direction.UNDETERMINED,
            UncertaintyDimension.CONTACT: proposition.contact == Contact.UNDETERMINED,
            UncertaintyDimension.COMPLETION: proposition.completion == Completion.UNDETERMINED,
            UncertaintyDimension.INTENTIONALITY: proposition.intentionality == SemanticIntentionality.UNDETERMINED,
            UncertaintyDimension.TEMPORAL_SCOPE: proposition.temporal_scope.value == "undetermined",
            UncertaintyDimension.THREAT_MEANING: proposition.conduct_kind in {ConductKind.THREAT_EXPRESSION, ConductKind.THREATENING_MOVEMENT, ConductKind.UNDETERMINED},
            UncertaintyDimension.ASSERTION_STATUS: proposition.assertion_status == AssertionStatus.UNCERTAIN,
        }[uncertainty.dimension]
        disputed = uncertainty.dimension in conflict_dimensions.get(proposition.proposition_id, set())
        if not unresolved and not disputed:
            issues.append(_issue(ValidationIssueCode.INVALID_UNCERTAINTY, f"uncertainties.{index}", "Uncertainty does not correspond to an unresolved or disputed dimension."))

    evidence_ids = {item.evidence_id: item for item in envelope.evidence_excerpts}
    for index, evidence in enumerate(envelope.evidence_excerpts):
        if not evidence.text.strip() or evidence.text not in normalized_narrative:
            issues.append(_issue(ValidationIssueCode.EVIDENCE_NOT_CONTAINED, f"evidence_excerpts.{index}.text", "Evidence must be a non-empty exact narrative substring."))

    supported: set[tuple[EvidenceSubjectKind, str]] = set()
    for index, support in enumerate(envelope.evidence_supports):
        field = f"evidence_supports.{index}"
        supported.add((support.subject_kind, support.subject_ref))
        if support.evidence_ref not in evidence_ids:
            continue
        subject = None
        if support.subject_kind == EvidenceSubjectKind.PROPOSITION:
            subject = propositions[support.subject_ref]
            expected_role = EvidenceSupportRole.SUPPORTS_NEGATION if subject.assertion_status == AssertionStatus.NEGATED else EvidenceSupportRole.SUPPORTS_ASSERTION
            if support.role != expected_role:
                issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, field, "Evidence role is incoherent with proposition status."))
        elif support.subject_kind == EvidenceSubjectKind.RELATIONSHIP:
            subject = relationships[support.subject_ref]
            expected_role = {
                RelationshipKind.NEGATES: EvidenceSupportRole.SUPPORTS_NEGATION,
                RelationshipKind.SUPERSEDES: EvidenceSupportRole.SUPPORTS_SUPERSESSION,
                RelationshipKind.CONFLICTS_WITH: EvidenceSupportRole.SUPPORTS_CONFLICT,
            }[subject.relationship_kind]
            if support.role != expected_role:
                issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, field, "Evidence role is incoherent with relationship kind."))
        else:
            subject = uncertainties[support.subject_ref]
            if support.role != EvidenceSupportRole.SUPPORTS_UNCERTAINTY:
                issues.append(_issue(ValidationIssueCode.INVALID_EVIDENCE_SUPPORT, field, "Uncertainty requires uncertainty evidence role."))

    required_subjects = (
        {(EvidenceSubjectKind.PROPOSITION, item.proposition_id) for item in envelope.propositions}
        | {(EvidenceSubjectKind.RELATIONSHIP, item.relationship_id) for item in envelope.relationships}
        | {(EvidenceSubjectKind.UNCERTAINTY, item.uncertainty_id) for item in envelope.uncertainties}
    )
    for subject_kind, subject_ref in sorted(required_subjects - supported, key=lambda item: (item[0].value, item[1])):
        issues.append(_issue(ValidationIssueCode.MISSING_EVIDENCE_SUPPORT, subject_ref, f"{subject_kind.value} requires evidence support."))

    if issues:
        return DomainValidationResult(status=DomainValidationStatus.FAILED, issues=issues)
    return DomainValidationResult(status=DomainValidationStatus.PASSED)
