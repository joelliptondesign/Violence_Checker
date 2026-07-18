from typing import Optional

from src.app_logic import AnalysisResult
from src.contracts import (
    NormalizedIncident,
    PipelineResult,
    RegexResult,
    SalesforcePayload,
    ValidationResult,
)


def validation_result_from_analysis(analysis: AnalysisResult) -> ValidationResult:
    return analysis.validation_result


def pipeline_result_from_analysis(analysis: AnalysisResult) -> PipelineResult:
    semantic_facts = (
        analysis.validation_result.validated_facts.facts
        if analysis.validation_result.validated_facts is not None
        else None
    )

    salesforce_payload: Optional[SalesforcePayload] = None
    if analysis.salesforce_preview is not None:
        salesforce_payload = SalesforcePayload.from_preview_dict(analysis.salesforce_preview)

    return PipelineResult(
        incident=analysis.incident,
        normalized_incident=analysis.normalized_incident or NormalizedIncident.from_incident(analysis.incident),
        regex_result=RegexResult.from_legacy_dict(analysis.regex_result),
        semantic_facts=semantic_facts,
        validation_result=validation_result_from_analysis(analysis),
        operational_finding=(
            analysis.compatibility_result.finding
            if analysis.compatibility_result is not None
            else None
        ),
        policy_decision=analysis.policy_decision,
        salesforce_payload=salesforce_payload,
        presentation_payload={
            "comparison_display_status": analysis.comparison.display_status,
            "semantic_validation_status": analysis.comparison.semantic_validation_status,
        },
        signature=analysis.signature,
    )
