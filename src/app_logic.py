from dataclasses import dataclass
from typing import Callable, Dict, Optional

from src.comparison import ComparisonResult, build_comparison_result
from src.models import Incident
from src.regex_baseline import detect_violence_terms
from src.salesforce_preview import build_salesforce_preview
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus, extract_violence_finding


@dataclass(frozen=True)
class AnalysisResult:
    incident: Incident
    regex_result: Dict[str, object]
    semantic_result: SemanticExtractionResult
    comparison: ComparisonResult
    salesforce_preview: Optional[Dict[str, object]]
    signature: str


def active_narrative_signature(incident: Incident) -> str:
    return f"{incident.incident_id}:{incident.narrative}"


def is_stale_result(stored_signature: Optional[str], active_signature: str) -> bool:
    return stored_signature is not None and stored_signature != active_signature


def should_display_analysis_result(
    stored_signature: Optional[str],
    active_signature: Optional[str],
) -> bool:
    return stored_signature is not None and active_signature is not None and stored_signature == active_signature


def validate_manual_narrative(narrative: str) -> str:
    if not narrative.strip():
        raise ValueError("Manual narrative must not be empty.")
    return narrative


def create_manual_incident(narrative: str, incident_id: str = "MANUAL_SESSION_001") -> Incident:
    return Incident(incident_id=incident_id, narrative=validate_manual_narrative(narrative))


def run_analysis(
    incident: Incident,
    *,
    extractor: Callable[[Incident], SemanticExtractionResult] = extract_violence_finding,
) -> AnalysisResult:
    regex_result = detect_violence_terms(incident.narrative)
    semantic_result = extractor(incident)
    comparison = build_comparison_result(incident, regex_result, semantic_result)

    preview = None
    if semantic_result.status == SemanticExtractionStatus.SUCCESS:
        preview = build_salesforce_preview(incident.incident_id, semantic_result)

    return AnalysisResult(
        incident=incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        comparison=comparison,
        salesforce_preview=preview,
        signature=active_narrative_signature(incident),
    )
