"""Single-pass application orchestration over the True North runtime."""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Union

from src.comparison import ComparisonResult, build_comparison_result
from src.contracts import (
    CompletenessStatus,
    InputValidationResult,
    NormalizedIncident,
    OperatorCommunication,
    OperatorCommunicationInput,
    PipelineResult,
    PolicyDecision,
    PolicyOutcome,
    ProcessingStatus,
    ValidationResult,
)
from src.input_validation import validate_incident
from src.models import Incident
from src.narrative_normalizer import normalize_incident
from src.operator_communication import (
    communication_is_supported,
    create_operator_communication,
    construct_communication_input,
)
from src.operator_communication_provider import OperatorCommunicationResult
from src.policy import evaluate_policy
from src.regex_baseline import detect_violence_terms
from src.salesforce_preview import build_salesforce_preview
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus, extract_semantic_envelope
from src.semantic_validation import validate_semantic_candidate, validation_not_run


@dataclass(frozen=True)
class AnalysisResult:
    incident: Incident
    regex_result: Dict[str, object]
    semantic_result: SemanticExtractionResult
    validation_result: ValidationResult
    policy_decision: PolicyDecision
    comparison: ComparisonResult
    salesforce_preview: Optional[Dict[str, object]]
    communication: OperatorCommunication
    signature: str
    normalized_incident: NormalizedIncident
    pipeline_result: PipelineResult


def active_narrative_signature(incident: Incident) -> str:
    return f"{incident.incident_id}:{incident.narrative}"


def is_stale_result(stored_signature: Optional[str], active_signature: str) -> bool:
    return stored_signature is not None and stored_signature != active_signature


def should_display_analysis_result(stored_signature: Optional[str], active_signature: Optional[str]) -> bool:
    return stored_signature is not None and active_signature is not None and stored_signature == active_signature


def validate_manual_narrative(narrative: str) -> str:
    if not narrative.strip():
        raise ValueError("Manual narrative must not be empty.")
    return narrative


def create_manual_incident(narrative: str, incident_id: str = "MANUAL_SESSION_001") -> Incident:
    return Incident(incident_id=incident_id, narrative=validate_manual_narrative(narrative))


def _policy_for_validation(validation_result: ValidationResult) -> PolicyDecision:
    return evaluate_policy(
        validated=validation_result.validated_envelope,
        processing_status=validation_result.processing_status,
        completeness_status=validation_result.completeness_status,
        derived=validation_result.derived_semantics,
    )


def run_analysis(
    incident: object,
    *,
    extractor: Callable[[Incident], SemanticExtractionResult] = extract_semantic_envelope,
    communicator: Optional[Callable[[OperatorCommunicationInput], OperatorCommunicationResult]] = None,
) -> Union[AnalysisResult, InputValidationResult]:
    input_validation = validate_incident(incident)
    if not input_validation.succeeded:
        return InputValidationResult(
            status=input_validation.status,
            issues=input_validation.issues,
            policy_decision=evaluate_policy(
                validated=None,
                processing_status=ProcessingStatus.PIPELINE_FAILURE,
                completeness_status=CompletenessStatus.INCOMPLETE_ANALYSIS,
                derived=None,
            ),
        )
    validated_incident = input_validation.incident
    if validated_incident is None:
        raise RuntimeError("successful input validation did not provide an incident")

    normalized_incident = normalize_incident(validated_incident)
    inference_incident = Incident(
        incident_id=normalized_incident.incident_id,
        narrative=normalized_incident.normalized_narrative,
    )
    regex_result = detect_violence_terms(inference_incident.narrative)
    semantic_result = extractor(inference_incident)
    validation_result = validation_not_run()
    if semantic_result.status == SemanticExtractionStatus.SUCCESS:
        validation_result = validate_semantic_candidate(
            semantic_result.semantic_candidate,
            incident_id=inference_incident.incident_id,
            normalized_narrative=inference_incident.narrative,
        )
        policy_decision = _policy_for_validation(validation_result)
    else:
        policy_decision = evaluate_policy(
            validated=None,
            processing_status=ProcessingStatus.PROVIDER_FAILURE,
            completeness_status=CompletenessStatus.INCOMPLETE_ANALYSIS,
            derived=None,
        )

    comparison = build_comparison_result(
        validated_incident,
        regex_result,
        semantic_result,
        validation_result,
        policy_decision,
    )
    preview = None
    if validation_result.passed and policy_decision.outcome != PolicyOutcome.UNABLE_TO_DETERMINE:
        preview = build_salesforce_preview(validation_result, policy_decision)

    communication = create_operator_communication(validation_result, policy_decision)
    if communicator is not None and policy_decision.outcome != PolicyOutcome.UNABLE_TO_DETERMINE:
        communication_input = construct_communication_input(validation_result, policy_decision)
        try:
            generated = communicator(communication_input)
            if (
                generated.succeeded
                and generated.communication is not None
                and communication_is_supported(generated.communication, communication_input)
            ):
                communication = generated.communication
        except Exception:
            pass  # Presentation generation cannot change deterministic authority.

    signature = active_narrative_signature(validated_incident)
    pipeline_result = PipelineResult(
        incident=validated_incident,
        normalized_incident=normalized_incident,
        regex_result=regex_result,
        validation_result=validation_result,
        policy_decision=policy_decision,
        salesforce_payload=preview,
        signature=signature,
    )
    return AnalysisResult(
        incident=validated_incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        validation_result=validation_result,
        policy_decision=policy_decision,
        comparison=comparison,
        salesforce_preview=preview,
        communication=communication,
        signature=signature,
        normalized_incident=normalized_incident,
        pipeline_result=pipeline_result,
    )
