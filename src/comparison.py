"""Deterministic regex-versus-True-North-outcome comparison."""

from dataclasses import dataclass
from typing import Dict, List

from src.contracts import (
    FactDirection,
    PolicyDecision,
    PolicyOutcome,
    ResolutionStatus,
    TemporalScope,
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
    true_north_outcome: PolicyOutcome
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
    regex_detected = bool(regex_result.get("detected"))
    outcome = policy_decision.outcome
    if outcome == PolicyOutcome.UNABLE_TO_DETERMINE:
        alignment = "semantic_failure"
    elif outcome == PolicyOutcome.UNCERTAIN:
        alignment = "semantic_uncertain"
    elif regex_detected and outcome == PolicyOutcome.VIOLENCE_DETECTED:
        alignment = "aligned_positive"
    elif not regex_detected and outcome == PolicyOutcome.NO_VIOLENCE_DETECTED:
        alignment = "aligned_negative"
    elif regex_detected:
        alignment = "regex_positive_semantic_negative"
    else:
        alignment = "regex_negative_semantic_positive"

    divergence: list[str] = []
    if alignment == "semantic_failure":
        divergence.append("True North analysis could not produce a deterministic outcome.")
    elif alignment == "semantic_uncertain":
        divergence.append("True North analysis preserved material uncertainty instead of forcing a result.")
    elif alignment == "regex_positive_semantic_negative":
        divergence.append("Regex detected violence-related language, but validated incident facts did not satisfy the violence criteria.")
    elif alignment == "regex_negative_semantic_positive":
        divergence.append("Regex found no configured match, but validated incident facts satisfied the violence criteria.")

    enrichment: list[str] = []
    envelope = validation_result.validated_envelope
    derived = validation_result.derived_semantics
    if envelope is not None and derived is not None:
        active_ids = set(derived.active_fact_ids)
        active = [fact for fact in envelope.facts if fact.fact_id in active_ids]
        if any(fact.temporal_scope == TemporalScope.HISTORICAL for fact in envelope.facts):
            enrichment.append("True North preserves historical conduct without treating it as current.")
        if any(fact.direction == FactDirection.OBJECT_DIRECTED for fact in active):
            enrichment.append("True North identifies object-directed conduct.")
        if any(fact.direction == FactDirection.SELF_DIRECTED for fact in active):
            enrichment.append("True North identifies self-directed conduct.")
        if any(fact.resolution_status == ResolutionStatus.SUPERSEDED for fact in envelope.facts):
            enrichment.append("True North preserves supported corrections and excludes superseded facts.")
        if derived.contradiction_groups:
            enrichment.append("True North preserves unresolved contradictory accounts.")
        if any(fact.uncertainty for fact in active):
            enrichment.append("True North preserves explicitly unresolved operational facts.")
        if any(fact.evidence for fact in envelope.facts):
            enrichment.append("True North links exact narrative evidence to each operational fact.")

    observations = divergence + enrichment or ["No material difference identified."]
    if alignment == "semantic_failure":
        display = "Semantic Comparison Unavailable"
    elif divergence:
        display = "Material Difference Detected"
    elif enrichment:
        display = "Classification Aligned, Operational Context Added"
    else:
        display = "No Material Difference Identified"

    status = semantic_result.status.value
    if semantic_result.status == SemanticExtractionStatus.SUCCESS:
        status = "success" if validation_result.passed else validation_result.processing_status.value
    return ComparisonResult(
        incident=incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        validation_result=validation_result,
        true_north_outcome=outcome,
        semantic_validation_status=status,
        classification_alignment=alignment,
        material_difference_detected=bool(divergence or enrichment),
        divergence_observations=divergence,
        semantic_enrichment_observations=enrichment,
        display_status=display,
        observations=observations,
    )
