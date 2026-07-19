"""Typed aggregate adapters for current successor application results."""

from typing import Optional

from src.app_logic import AnalysisResult
from src.contracts import NormalizedIncident, PipelineResult, RegexResult, SalesforcePayload, ValidationResult


def validation_result_from_analysis(analysis: AnalysisResult) -> ValidationResult:
    return analysis.validation_result


def pipeline_result_from_analysis(analysis: AnalysisResult) -> PipelineResult:
    validated = analysis.validation_result.validated_envelope
    salesforce_payload: Optional[SalesforcePayload] = None
    if analysis.salesforce_preview is not None:
        salesforce_payload = SalesforcePayload.from_preview_dict(analysis.salesforce_preview)
    return PipelineResult(
        incident=analysis.incident,
        normalized_incident=analysis.normalized_incident or NormalizedIncident.from_incident(analysis.incident),
        regex_result=RegexResult.from_legacy_dict(analysis.regex_result),
        semantic_envelope=validated.envelope if validated is not None else None,
        derived_semantics=validated.derived if validated is not None else None,
        validation_result=validation_result_from_analysis(analysis),
        policy_decision=analysis.policy_decision,
        salesforce_payload=salesforce_payload,
        presentation_payload={
            "comparison_display_status": analysis.comparison.display_status,
            "semantic_validation_status": analysis.comparison.semantic_validation_status,
        },
        signature=analysis.signature,
    )
