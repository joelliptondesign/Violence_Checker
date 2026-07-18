from dataclasses import dataclass
from typing import Callable, Dict, Optional, Union

from src.comparison import ComparisonResult, build_comparison_result
from src.compatibility_finding import CompatibilityFindingResult, construct_compatibility_finding
from src.contracts import (
    InputValidationResult,
    NormalizedIncident,
    PipelineFailureProvenance,
    PolicyDecision,
    PolicyOutcome,
    ValidationFailureStage,
    ValidationResult,
)
from src.input_validation import validate_incident
from src.models import Incident
from src.narrative_normalizer import normalize_incident
from src.policy import evaluate_policy, failed_policy_decision
from src.regex_baseline import detect_violence_terms
from src.salesforce_preview import build_salesforce_preview
from src.semantic_validation import validate_semantic_candidate, validation_not_run
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus, extract_violence_finding


@dataclass(frozen=True)
class AnalysisResult:
    incident: Incident
    regex_result: Dict[str, object]
    semantic_result: SemanticExtractionResult
    validation_result: ValidationResult
    compatibility_result: Optional[CompatibilityFindingResult]
    policy_decision: PolicyDecision
    comparison: ComparisonResult
    salesforce_preview: Optional[Dict[str, object]]
    signature: str
    normalized_incident: Optional[NormalizedIncident] = None


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
    incident: object,
    *,
    extractor: Callable[[Incident], SemanticExtractionResult] = extract_violence_finding,
) -> Union[AnalysisResult, InputValidationResult]:
    input_validation = validate_incident(incident)
    if not input_validation.succeeded:
        return InputValidationResult(
            status=input_validation.status,
            issues=input_validation.issues,
            policy_decision=failed_policy_decision(PipelineFailureProvenance.INPUT_VALIDATION),
        )

    validated_incident = input_validation.incident
    if validated_incident is None:  # Contract consistency makes this unreachable.
        raise RuntimeError("successful input validation did not provide an incident")

    normalized_incident = normalize_incident(validated_incident)
    inference_incident = Incident(
        incident_id=normalized_incident.incident_id,
        narrative=normalized_incident.normalized_narrative,
    )
    regex_result = detect_violence_terms(normalized_incident.normalized_narrative)
    semantic_result = extractor(inference_incident)
    compatibility_result = None
    validation_result = validation_not_run()
    policy_decision: PolicyDecision
    if semantic_result.status == SemanticExtractionStatus.SUCCESS:
        validation_result = validate_semantic_candidate(semantic_result.semantic_candidate)
        if validation_result.passed and validation_result.validated_facts is not None:
            compatibility_result = construct_compatibility_finding(validation_result.validated_facts)

    if semantic_result.status != SemanticExtractionStatus.SUCCESS:
        provider_failures = {
            SemanticExtractionStatus.CONFIGURATION_FAILURE: PipelineFailureProvenance.PROVIDER_CONFIGURATION,
            SemanticExtractionStatus.REQUEST_FAILURE: PipelineFailureProvenance.PROVIDER_REQUEST,
            SemanticExtractionStatus.STRUCTURED_RESPONSE_FAILURE: (
                PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE
            ),
            SemanticExtractionStatus.VALIDATION_FAILURE: PipelineFailureProvenance.PROVIDER_VALIDATION,
        }
        policy_decision = failed_policy_decision(provider_failures[semantic_result.status])
    elif validation_result.failure_stage == ValidationFailureStage.SCHEMA:
        policy_decision = failed_policy_decision(PipelineFailureProvenance.SCHEMA_VALIDATION)
    elif validation_result.failure_stage == ValidationFailureStage.DOMAIN:
        policy_decision = failed_policy_decision(PipelineFailureProvenance.DOMAIN_VALIDATION)
    elif compatibility_result is None or not compatibility_result.succeeded:
        policy_decision = failed_policy_decision(
            PipelineFailureProvenance.COMPATIBILITY_CONSTRUCTION
        )
    else:
        policy_decision = evaluate_policy(
            validated_facts=validation_result.validated_facts,
            finding=compatibility_result.finding,
        )

    comparison = build_comparison_result(
        validated_incident,
        regex_result,
        semantic_result,
        validation_result,
        compatibility_result,
    )

    preview = None
    if (
        compatibility_result is not None
        and compatibility_result.succeeded
        and policy_decision.outcome != PolicyOutcome.WRITE_FAILED
    ):
        preview = build_salesforce_preview(
            validated_incident.incident_id,
            compatibility_result.finding,
            policy_decision,
            validation_status=semantic_result.status.value,
        )

    return AnalysisResult(
        incident=validated_incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        validation_result=validation_result,
        compatibility_result=compatibility_result,
        policy_decision=policy_decision,
        comparison=comparison,
        salesforce_preview=preview,
        signature=active_narrative_signature(validated_incident),
        normalized_incident=normalized_incident,
    )
