"""Deterministic regex-versus-successor comparison without semantic inference."""

from dataclasses import dataclass
from typing import Dict, List

from src.contracts import (
    Direction,
    PolicyDecision,
    PolicyOutcome,
    RelationshipKind,
    TemporalScope,
    ValidationFailureStage,
    ValidationResult,
)
from src.models import Incident
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


@dataclass(frozen=True)
class ComparisonResult:
    incident: Incident
    regex_result: Dict[str, object]
    semantic_result: SemanticExtractionResult
    validation_result: ValidationResult
    semantic_validation_status: str
    classification_alignment: str
    material_difference_detected: bool
    divergence_observations: List[str]
    semantic_enrichment_observations: List[str]
    display_status: str
    observations: List[str]


def build_comparison_result(
    incident: Incident,
    regex_result: Dict[str, object],
    semantic_result: SemanticExtractionResult,
    validation_result: ValidationResult,
    policy_decision: PolicyDecision,
) -> ComparisonResult:
    if semantic_result.status != SemanticExtractionStatus.SUCCESS or not validation_result.passed:
        alignment = "semantic_failure"
    else:
        regex_detected = bool(regex_result.get("detected"))
        semantic_detected = policy_decision.outcome == PolicyOutcome.WRITE_DETECTED
        if regex_detected and semantic_detected:
            alignment = "aligned_positive"
        elif not regex_detected and not semantic_detected:
            alignment = "aligned_negative"
        elif regex_detected:
            alignment = "regex_positive_semantic_negative"
        else:
            alignment = "regex_negative_semantic_positive"

    divergence: list[str] = []
    if alignment == "semantic_failure":
        if validation_result.failure_stage == ValidationFailureStage.SCHEMA:
            divergence.append("Semantic schema validation failed and comparison is unavailable.")
        elif validation_result.failure_stage == ValidationFailureStage.DOMAIN:
            divergence.append("Semantic domain validation failed and comparison is unavailable.")
        else:
            divergence.append("Semantic extraction failed and no validated comparison is available.")
    elif alignment == "regex_positive_semantic_negative":
        divergence.append("Regex detected violence-related language, but deterministic policy found no affirmed current interpersonal violence.")
    elif alignment == "regex_negative_semantic_positive":
        divergence.append("Regex did not detect violence-related language, but validated propositions support current interpersonal violence.")

    enrichment: list[str] = []
    validated = validation_result.validated_envelope
    if validated is not None:
        envelope = validated.envelope
        derived = {item.proposition_id: item for item in validated.derived.propositions}
        if any(item.temporal_scope == TemporalScope.HISTORICAL for item in envelope.propositions):
            enrichment.append("Semantic extraction preserves historical conduct as proposition-scoped context.")
        directions = {item.direction for item in derived.values()}
        if Direction.OBJECT_DIRECTED in directions:
            enrichment.append("Semantic extraction distinguishes object-directed conduct.")
        if Direction.SELF_DIRECTED in directions:
            enrichment.append("Semantic extraction distinguishes self-directed conduct.")
        if any(item.relationship_kind == RelationshipKind.SUPERSEDES for item in envelope.relationships):
            enrichment.append("Semantic extraction preserves an explicit correction and supersession relationship.")
        if any(item.relationship_kind == RelationshipKind.CONFLICTS_WITH for item in envelope.relationships):
            enrichment.append("Semantic extraction preserves competing assertions without selecting a winner.")
        if envelope.uncertainties:
            enrichment.append("Semantic extraction provides proposition-scoped bounded uncertainty.")
        if envelope.evidence_supports:
            enrichment.append("Semantic extraction links exact narrative evidence to semantic subjects.")

    observations = divergence + enrichment
    if not observations:
        observations = ["No material difference identified."]
    if alignment == "semantic_failure":
        display = "Semantic Comparison Unavailable"
    elif divergence:
        display = "Material Difference Detected"
    elif enrichment:
        display = "Classification Aligned, Semantic Context Added"
    else:
        display = "No Material Difference Identified"

    status = semantic_result.status.value
    if semantic_result.status == SemanticExtractionStatus.SUCCESS:
        if validation_result.failure_stage == ValidationFailureStage.SCHEMA:
            status = "schema_validation_failure"
        elif validation_result.failure_stage == ValidationFailureStage.DOMAIN:
            status = "domain_validation_failure"
        else:
            status = "success"
    return ComparisonResult(
        incident=incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        validation_result=validation_result,
        semantic_validation_status=status,
        classification_alignment=alignment,
        material_difference_detected=bool(divergence or enrichment),
        divergence_observations=divergence,
        semantic_enrichment_observations=enrichment,
        display_status=display,
        observations=observations,
    )
