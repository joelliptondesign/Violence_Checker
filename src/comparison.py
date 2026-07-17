from dataclasses import dataclass
from typing import Dict, List

from src.models import Incident, Intentionality, ViolenceEventType
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


@dataclass(frozen=True)
class ComparisonResult:
    incident: Incident
    regex_result: Dict[str, object]
    semantic_result: SemanticExtractionResult
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
) -> ComparisonResult:
    classification_alignment = _classification_alignment(regex_result, semantic_result)
    divergence_observations = _build_divergence_observations(classification_alignment)
    semantic_enrichment_observations = _build_semantic_enrichment_observations(
        regex_result,
        semantic_result,
    )
    material_difference_detected = bool(divergence_observations or semantic_enrichment_observations)
    observations = divergence_observations + semantic_enrichment_observations
    display_status = _display_status(
        classification_alignment,
        divergence_observations,
        semantic_enrichment_observations,
    )

    if not observations:
        observations = ["No material difference identified."]

    return ComparisonResult(
        incident=incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        semantic_validation_status=semantic_result.status.value,
        classification_alignment=classification_alignment,
        material_difference_detected=material_difference_detected,
        divergence_observations=divergence_observations,
        semantic_enrichment_observations=semantic_enrichment_observations,
        display_status=display_status,
        observations=observations,
    )


def _classification_alignment(
    regex_result: Dict[str, object],
    semantic_result: SemanticExtractionResult,
) -> str:
    if semantic_result.status != SemanticExtractionStatus.SUCCESS:
        return "semantic_failure"

    finding = semantic_result.finding
    if finding is None:
        return "semantic_failure"

    regex_detected = bool(regex_result.get("detected"))

    if regex_detected and finding.violence_present:
        return "aligned_positive"

    if not regex_detected and not finding.violence_present:
        return "aligned_negative"

    if regex_detected and not finding.violence_present:
        return "regex_positive_semantic_negative"

    return "regex_negative_semantic_positive"


def _build_divergence_observations(classification_alignment: str) -> List[str]:
    if classification_alignment == "regex_positive_semantic_negative":
        return [
            "Regex detected violence-related language, but semantic extraction determined no violence."
        ]

    if classification_alignment == "regex_negative_semantic_positive":
        return [
            "Regex did not detect violence-related language, but semantic extraction determined violence was present."
        ]

    if classification_alignment == "semantic_failure":
        return ["Semantic extraction failed and no validated semantic comparison is available."]

    return []


def _build_semantic_enrichment_observations(
    regex_result: Dict[str, object],
    semantic_result: SemanticExtractionResult,
) -> List[str]:
    if semantic_result.status != SemanticExtractionStatus.SUCCESS or semantic_result.finding is None:
        return []

    finding = semantic_result.finding
    observations: List[str] = []

    _append_unique(
        observations,
        not finding.current_event,
        "Semantic extraction identifies the violence language as historical or non-current.",
    )
    _append_unique(
        observations,
        finding.event_type == ViolenceEventType.VERBAL_THREAT,
        "Semantic extraction distinguishes a verbal threat from physical violence.",
    )
    _append_unique(
        observations,
        finding.event_type == ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
        "Semantic extraction distinguishes attempted physical violence from completed contact.",
    )
    _append_unique(
        observations,
        finding.event_type == ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
        "Semantic extraction identifies completed physical violence.",
    )
    _append_unique(
        observations,
        finding.intentionality == Intentionality.ACCIDENTAL,
        "Semantic extraction identifies accidental contact rather than intentional violence.",
    )
    _append_unique(
        observations,
        finding.violence_present
        and finding.event_type != ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE
        and not finding.contact_occurred,
        "Semantic extraction identifies no person-directed physical contact.",
    )
    _append_unique(
        observations,
        finding.negated,
        "Semantic extraction identifies negated violence language.",
    )
    _append_unique(
        observations,
        finding.correction_present,
        "Semantic extraction applies or identifies a correction.",
    )
    _append_unique(
        observations,
        finding.conflicting_information,
        "Semantic extraction identifies conflicting statements.",
    )
    _append_unique(
        observations,
        finding.injury_mentioned,
        "Semantic extraction identifies an injury mention.",
    )
    _append_unique(
        observations,
        finding.actor is not None or finding.target is not None,
        "Semantic extraction identifies actor or target information not represented by regex.",
    )
    _append_unique(
        observations,
        bool(finding.evidence_text),
        "Semantic extraction provides supporting evidence excerpts not represented by regex.",
    )
    _append_unique(
        observations,
        bool(finding.uncertainty_notes) or finding.confidence < 1.0,
        "Semantic extraction provides confidence or uncertainty information not represented by regex.",
    )

    return observations


def _display_status(
    classification_alignment: str,
    divergence_observations: List[str],
    semantic_enrichment_observations: List[str],
) -> str:
    if classification_alignment == "semantic_failure":
        return "Semantic Comparison Unavailable"

    if divergence_observations:
        return "Material Difference Detected"

    if semantic_enrichment_observations:
        return "Classification Aligned, Semantic Context Added"

    return "No Material Difference Identified"


def _append_unique(observations: List[str], condition: bool, observation: str) -> None:
    if condition and observation not in observations:
        observations.append(observation)
