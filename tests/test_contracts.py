from src.app_logic import AnalysisResult, active_narrative_signature
from src.comparison import build_comparison_result
from src.compatibility_finding import construct_compatibility_finding
from src.contract_adapters import pipeline_result_from_analysis, validation_result_from_analysis
from src.contracts import (
    DomainValidationStatus,
    NormalizedIncident,
    PipelineFailureProvenance,
    PolicyDecision,
    PolicyOutcome,
    ProviderStructuredResponse,
    RegexResult,
    SalesforcePayload,
    SemanticFacts,
    SchemaValidationStatus,
)
from src.models import Incident, Intentionality, ViolenceEventType, ViolenceFinding
from src.policy import evaluate_policy, failed_policy_decision
from src.salesforce_preview import build_salesforce_preview
from src.provider_adapter import semantic_candidate_from_provider_response
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from src.semantic_validation import validate_semantic_candidate, validation_not_run


def finding() -> ViolenceFinding:
    return ViolenceFinding(
        violence_present=True,
        event_type=ViolenceEventType.VERBAL_THREAT,
        actor="patient",
        target="nurse",
        contact_occurred=False,
        injury_mentioned=False,
        current_event=True,
        intentionality=Intentionality.INTENTIONAL,
        negated=False,
        correction_present=False,
        conflicting_information=False,
        evidence_text=["threatened to hit the nurse"],
        confidence=0.9,
        uncertainty_notes=[],
    )


def semantic_facts() -> SemanticFacts:
    value = finding()
    return SemanticFacts(
        violence_present=value.violence_present,
        event_type=value.event_type,
        actor=value.actor,
        target=value.target,
        contact_occurred=value.contact_occurred,
        injury_mentioned=value.injury_mentioned,
        current_event=value.current_event,
        intentionality=value.intentionality,
        negated=value.negated,
        correction_present=value.correction_present,
        conflicting_information=value.conflicting_information,
        evidence_text=list(value.evidence_text),
        confidence=value.confidence,
        uncertainty_notes=list(value.uncertainty_notes),
    )


def policy_for(value: ViolenceFinding) -> PolicyDecision:
    validated = validate_semantic_candidate(SemanticFacts.model_validate(value.model_dump())).validated_facts
    return evaluate_policy(validated_facts=validated, finding=value)


def test_normalized_incident_preserves_original_incident() -> None:
    incident = Incident(incident_id="CASE_X", narrative="Original narrative.")

    normalized = NormalizedIncident.from_incident(incident)

    assert normalized.incident_id == incident.incident_id
    assert normalized.original_narrative == incident.narrative
    assert normalized.normalized_narrative == incident.narrative
    assert normalized.normalization_applied is False


def test_regex_result_legacy_dict_round_trip() -> None:
    legacy = {
        "detected": True,
        "matched_terms": ["hit"],
        "matched_patterns": ["\\bhit\\b"],
    }

    contract = RegexResult.from_legacy_dict(legacy)

    assert contract.to_legacy_dict() == legacy


def test_provider_structured_response_adapter_terminates_provider_shape() -> None:
    provider_response = ProviderStructuredResponse.model_validate(semantic_facts().model_dump())

    candidate = semantic_candidate_from_provider_response(provider_response)
    validation = validate_semantic_candidate(candidate)

    assert validation.validated_facts is not None
    assert validation.validated_facts.facts == semantic_facts()
    assert not isinstance(candidate, ProviderStructuredResponse)


def test_semantic_facts_serialize_independently() -> None:
    facts = semantic_facts()

    serialized = facts.model_dump()

    assert serialized["event_type"] == "verbal_threat"
    assert serialized["intentionality"] == "intentional"
    assert serialized["evidence_text"] == ["threatened to hit the nurse"]


def test_salesforce_payload_round_trip_preserves_legacy_preview() -> None:
    incident = Incident(incident_id="CASE_X", narrative="The patient threatened to hit the nurse.")
    value = finding()
    preview = build_salesforce_preview(incident.incident_id, value, policy_for(value))

    payload = SalesforcePayload.from_preview_dict(preview)

    assert payload.to_preview_dict() == preview


def test_validation_adapter_preserves_semantic_failure_status() -> None:
    incident = Incident(incident_id="CASE_X", narrative="Narrative.")
    semantic_result = SemanticExtractionResult(
        status=SemanticExtractionStatus.STRUCTURED_RESPONSE_FAILURE,
        failure_message="missing output",
    )
    regex_result = {"detected": False, "matched_terms": [], "matched_patterns": []}
    validation_result = validation_not_run()
    comparison = build_comparison_result(incident, regex_result, semantic_result, validation_result)
    analysis = AnalysisResult(
        incident=incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        validation_result=validation_result,
        compatibility_result=None,
        policy_decision=failed_policy_decision(
            PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE
        ),
        comparison=comparison,
        salesforce_preview=None,
        signature=active_narrative_signature(incident),
    )

    validation = validation_result_from_analysis(analysis)

    assert validation.schema_validation.status == SchemaValidationStatus.NOT_RUN
    assert validation.domain_validation.status == DomainValidationStatus.NOT_RUN
    assert validation.passed is False


def test_pipeline_result_adapter_preserves_existing_analysis_outputs() -> None:
    incident = Incident(incident_id="CASE_X", narrative="The patient threatened to hit the nurse.")
    semantic_result = SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        semantic_candidate=semantic_facts(),
    )
    validation_result = validate_semantic_candidate(semantic_result.semantic_candidate)
    compatibility_result = construct_compatibility_finding(validation_result.validated_facts)
    regex_result = {"detected": True, "matched_terms": ["hit"], "matched_patterns": ["\\bhit\\b"]}
    comparison = build_comparison_result(
        incident,
        regex_result,
        semantic_result,
        validation_result,
        compatibility_result,
    )
    policy_decision = evaluate_policy(
        validated_facts=validation_result.validated_facts,
        finding=compatibility_result.finding,
    )
    preview = build_salesforce_preview(
        incident.incident_id,
        compatibility_result.finding,
        policy_decision,
    )
    analysis = AnalysisResult(
        incident=incident,
        regex_result=regex_result,
        semantic_result=semantic_result,
        validation_result=validation_result,
        compatibility_result=compatibility_result,
        policy_decision=policy_decision,
        comparison=comparison,
        salesforce_preview=preview,
        signature=active_narrative_signature(incident),
    )

    pipeline = pipeline_result_from_analysis(analysis)

    assert pipeline.incident == analysis.incident
    assert pipeline.regex_result.to_legacy_dict() == regex_result
    assert pipeline.operational_finding == compatibility_result.finding
    assert pipeline.policy_decision == policy_decision
    assert pipeline.policy_decision.outcome == PolicyOutcome.WRITE_DETECTED
    assert pipeline.salesforce_payload is not None
    assert pipeline.salesforce_payload.to_preview_dict() == preview
