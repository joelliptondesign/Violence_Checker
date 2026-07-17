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
    observations: List[str]


def build_comparison_result(
    incident: Incident,
    regex_result: Dict[str, object],
    semantic_result: SemanticExtractionResult,
) -> ComparisonResult:
    return ComparisonResult(
        incident=incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        semantic_validation_status=semantic_result.status.value,
        observations=_build_observations(regex_result, semantic_result),
    )


def _build_observations(
    regex_result: Dict[str, object],
    semantic_result: SemanticExtractionResult,
) -> List[str]:
    if semantic_result.status != SemanticExtractionStatus.SUCCESS:
        return ["Semantic extraction returned failure; no validated finding is available."]

    finding = semantic_result.finding
    if finding is None:
        return ["Semantic extraction returned failure; no validated finding is available."]

    observations: List[str] = []
    regex_detected = bool(regex_result.get("detected"))

    if regex_detected and (
        not finding.current_event or finding.event_type == ViolenceEventType.NONE
    ):
        observations.append(
            "Regex detected violence language while semantic extraction did not identify current violence."
        )

    if regex_detected and not finding.current_event:
        observations.append("Regex detected a term in historical or non-current context.")

    if regex_detected and (finding.negated or finding.correction_present):
        observations.append("Regex detected corrected or negated language.")

    if finding.event_type == ViolenceEventType.VERBAL_THREAT:
        observations.append("Semantic extraction distinguished threat language from physical contact.")

    if finding.event_type == ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE:
        observations.append("Semantic extraction distinguished attempted violence from completed violence.")

    if finding.intentionality == Intentionality.ACCIDENTAL:
        observations.append("Semantic extraction identified accidental contact.")

    if finding.conflicting_information:
        observations.append("Semantic extraction identified conflicting information.")

    if not observations:
        observations.append("Regex and semantic outputs do not show a highlighted difference.")

    return observations
