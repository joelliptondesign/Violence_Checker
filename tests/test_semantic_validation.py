import pytest

from src.contracts import (
    AssertionStatus,
    CompletenessStatus,
    Conduct,
    FactDirection,
    IncidentDirection,
    Intentionality,
    MaterialAttribute,
    ProcessingStatus,
    ProviderFactCandidate,
    ProviderFactEvidenceCandidate,
    ProviderStructuredResponse,
    ResolutionStatus,
    TemporalScope,
    UncertaintyDimension,
    ValidationFailureStage,
    ValidationIssueCode,
)
from src.models import Incident
from src.provider_adapter import semantic_candidate_from_provider_response
from src.semantic_validation import validate_semantic_candidate, validation_not_run


BASE_SUPPORTS = [
    MaterialAttribute.CONDUCT,
    MaterialAttribute.DIRECTION,
    MaterialAttribute.INTENTIONALITY,
    MaterialAttribute.TEMPORAL_SCOPE,
    MaterialAttribute.ASSERTION_STATUS,
]


def fact(excerpt, **updates):
    values = dict(
        local_ref="fact",
        conduct=Conduct.PHYSICAL_CONTACT,
        direction=FactDirection.INTERPERSONAL,
        intentionality=Intentionality.INTENTIONAL,
        temporal_scope=TemporalScope.CURRENT,
        assertion_status=AssertionStatus.AFFIRMED,
        resolution_status=ResolutionStatus.ACTIVE,
        evidence=[ProviderFactEvidenceCandidate(excerpt=excerpt, supports=BASE_SUPPORTS)],
        uncertainty=[],
    )
    values.update(updates)
    return ProviderFactCandidate(**values)


def adapt(narrative, facts):
    return semantic_candidate_from_provider_response(
        ProviderStructuredResponse(facts=facts),
        incident=Incident(incident_id="CASE", narrative=narrative),
    )


def validate(envelope, narrative):
    return validate_semantic_candidate(
        envelope,
        incident_id="CASE",
        normalized_narrative=narrative,
    )


def test_valid_true_north_envelope_passes_with_repository_status_and_deterministic_derivation():
    narrative = "He intentionally punched a coworker today."
    result = validate(adapt(narrative, [fact(narrative)]), narrative)
    assert result.passed
    assert result.validated_envelope.facts[0].fact_id == "FACT-0001"
    assert result.processing_status == ProcessingStatus.SUCCESSFUL_ANALYSIS
    assert result.completeness_status == CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS
    assert result.derived_semantics.active_fact_ids == ("FACT-0001",)
    assert result.derived_semantics.superseded_fact_ids == ()
    assert result.derived_semantics.incident_direction == IncidentDirection.INTERPERSONAL
    assert "policy_candidate" not in type(result.derived_semantics).model_fields


def test_empty_fact_collection_is_semantically_admissible_but_carries_no_negative_conclusion():
    envelope = adapt("No qualifying fact was proposed.", [])
    result = validate(envelope, "No qualifying fact was proposed.")
    assert result.passed
    assert result.validated_envelope.facts == []
    assert result.processing_status == ProcessingStatus.SUCCESSFUL_ANALYSIS
    assert result.completeness_status == CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS
    assert result.derived_semantics.incident_direction == IncidentDirection.UNKNOWN
    assert set(type(result.validated_envelope).model_fields).isdisjoint({"policy_outcome", "completeness_status"})


def test_provider_object_is_rejected_before_domain_validation():
    narrative = "He intentionally punched a coworker today."
    result = validate_semantic_candidate(
        ProviderStructuredResponse(facts=[fact(narrative)]),
        incident_id="CASE",
        normalized_narrative=narrative,
    )
    assert result.failure_stage == ValidationFailureStage.SCHEMA
    assert result.processing_status == ProcessingStatus.SCHEMA_FAILURE
    assert result.completeness_status == CompletenessStatus.INCOMPLETE_ANALYSIS
    assert result.derived_semantics is None
    assert result.schema_validation.issues[0].code == ValidationIssueCode.PROVIDER_OBJECT_NOT_ALLOWED


def test_not_run_and_domain_failure_receive_repository_owned_failure_status():
    not_run = validation_not_run()
    assert not_run.processing_status == ProcessingStatus.PIPELINE_FAILURE
    assert not_run.completeness_status == CompletenessStatus.INCOMPLETE_ANALYSIS

    narrative = "He intentionally punched a coworker today."
    envelope = adapt(narrative, [fact(narrative)])
    failed = validate(envelope, "Different narrative")
    assert failed.failure_stage == ValidationFailureStage.DOMAIN
    assert failed.processing_status == ProcessingStatus.VALIDATION_FAILURE
    assert failed.completeness_status == CompletenessStatus.INCOMPLETE_ANALYSIS
    assert failed.derived_semantics is None


def test_repository_status_vocabularies_are_exact_and_absent_from_provider_contract():
    assert {item.value for item in ProcessingStatus} == {
        "successful_analysis", "provider_failure", "schema_failure",
        "validation_failure", "pipeline_failure",
    }
    assert {item.value for item in CompletenessStatus} == {
        "complete_admissible_analysis", "incomplete_analysis", "unresolved_semantic_content",
    }
    assert set(ProviderStructuredResponse.model_fields).isdisjoint({
        "processing_status", "completeness_status",
    })


@pytest.mark.parametrize("field,value,code", [
    ("schema_identity", "wrong", ValidationIssueCode.UNSUPPORTED_SCHEMA_IDENTITY),
    ("schema_version", "9.0.0", ValidationIssueCode.UNSUPPORTED_SCHEMA_VERSION),
    ("incident_id", "OTHER", ValidationIssueCode.INCIDENT_ID_MISMATCH),
])
def test_repository_identity_failures_are_typed(field, value, code):
    narrative = "He intentionally punched a coworker today."
    envelope = adapt(narrative, [fact(narrative)]).model_copy(update={field: value})
    result = validate(envelope, narrative)
    assert result.failure_stage == ValidationFailureStage.SCHEMA
    assert result.processing_status == ProcessingStatus.SCHEMA_FAILURE
    assert code in {issue.code for issue in result.schema_validation.issues}


def test_invalid_enumeration_and_dangling_correction_fail_schema():
    narrative = "He intentionally punched a coworker today."
    raw = adapt(narrative, [fact(narrative)]).model_dump(mode="json")
    raw["facts"][0]["direction"] = "multiple"
    assert validate(raw, narrative).failure_stage == ValidationFailureStage.SCHEMA

    envelope = adapt(narrative, [fact(narrative)])
    changed = envelope.facts[0].model_copy(update={"supersedes_fact_id": "FACT-9999"})
    result = validate(envelope.model_copy(update={"facts": [changed]}), narrative)
    assert ValidationIssueCode.DANGLING_REFERENCE in {issue.code for issue in result.schema_validation.issues}


def test_evidence_requires_exact_identity_containment_and_complete_attribute_coverage():
    narrative = "He intentionally punched a coworker today."
    envelope = adapt(narrative, [fact(narrative)])
    assert ValidationIssueCode.EVIDENCE_NOT_CONTAINED in {
        issue.code for issue in validate(envelope, "Different narrative").domain_validation.issues
    }

    evidence = envelope.facts[0].evidence[0].model_copy(
        update={"supports": BASE_SUPPORTS[:-1]},
    )
    changed = envelope.facts[0].model_copy(update={"evidence": [evidence]})
    result = validate(envelope.model_copy(update={"facts": [changed]}), narrative)
    assert ValidationIssueCode.MISSING_EVIDENCE_SUPPORT in {issue.code for issue in result.domain_validation.issues}


@pytest.mark.parametrize("narrative,updates", [
    ("The employee denied making any physical contact today.", {}),
    ("The cart accidentally bumped the employee today.", {}),
    ("He intentionally punched a coworker last year.", {}),
    ("The report states no physical contact occurred today.", {}),
])
def test_explicit_denial_accident_historical_and_no_contact_adversaries_fail(narrative, updates):
    envelope = adapt(narrative, [fact(narrative, **updates)])
    result = validate(envelope, narrative)
    assert result.failure_stage == ValidationFailureStage.DOMAIN
    assert ValidationIssueCode.INVALID_EVIDENCE_SUPPORT in {issue.code for issue in result.domain_validation.issues}


def test_unresolved_values_require_matching_uncertainty_and_support():
    narrative = "Possible contact occurred today, but intent is unresolved."
    unresolved = fact(
        narrative,
        intentionality=Intentionality.UNRESOLVED,
        uncertainty=[UncertaintyDimension.INTENTIONALITY],
    )
    valid = validate(adapt(narrative, [unresolved]), narrative)
    assert valid.passed
    assert valid.completeness_status == CompletenessStatus.UNRESOLVED_SEMANTIC_CONTENT

    envelope = adapt(narrative, [unresolved])
    changed = envelope.facts[0].model_copy(update={"uncertainty": []})
    result = validate(envelope.model_copy(update={"facts": [changed]}), narrative)
    assert ValidationIssueCode.INVALID_UNCERTAINTY in {issue.code for issue in result.domain_validation.issues}


@pytest.mark.parametrize("conduct,direction,intentionality", [
    (Conduct.SELF_HARM, FactDirection.INTERPERSONAL, Intentionality.INTENTIONAL),
    (Conduct.PROPERTY_VIOLENCE, FactDirection.OBJECT_DIRECTED, Intentionality.ACCIDENTAL),
    (Conduct.PROPERTY_VIOLENCE, FactDirection.INTERPERSONAL, Intentionality.INTENTIONAL),
])
def test_invalid_doctrinal_fact_combinations_fail_domain(conduct, direction, intentionality):
    narrative = "The narrative explicitly states the described conduct occurred today."
    envelope = adapt(narrative, [fact(
        narrative,
        conduct=conduct,
        direction=direction,
        intentionality=intentionality,
    )])
    result = validate(envelope, narrative)
    assert ValidationIssueCode.INVALID_FACT_COMBINATION in {issue.code for issue in result.domain_validation.issues}


def test_supported_correction_requires_later_reference_evidence_and_resolution_state():
    narrative = "Initial report: he intentionally shoved her today. Later corrected: the contact was accidental today."
    earlier = fact(
        "Initial report: he intentionally shoved her today.",
        local_ref="earlier",
        resolution_status=ResolutionStatus.SUPERSEDED,
    )
    later = fact(
        "Later corrected: the contact was accidental today.",
        local_ref="later",
        intentionality=Intentionality.ACCIDENTAL,
        supersedes_local_ref="earlier",
        evidence=[ProviderFactEvidenceCandidate(
            excerpt="Later corrected: the contact was accidental today.",
            supports=BASE_SUPPORTS + [MaterialAttribute.SUPERSESSION],
        )],
    )
    envelope = adapt(narrative, [later, earlier])
    assert validate(envelope, narrative).passed
    assert envelope.facts[1].supersedes_fact_id == "FACT-0001"

    broken = envelope.facts[0].model_copy(update={"resolution_status": ResolutionStatus.ACTIVE})
    result = validate(envelope.model_copy(update={"facts": [broken, envelope.facts[1]]}), narrative)
    assert ValidationIssueCode.INVALID_CORRECTION_REFERENCE in {issue.code for issue in result.domain_validation.issues}


def test_unresolved_contradiction_requires_two_active_disputed_supported_members():
    first_text = "Witness A said he intentionally punched the coworker today."
    second_text = "Witness B said he did not intentionally punch the coworker today."
    narrative = f"{first_text} {second_text}"
    contradiction_supports = BASE_SUPPORTS + [MaterialAttribute.CONTRADICTION]
    first = fact(
        first_text,
        local_ref="account-a",
        assertion_status=AssertionStatus.DISPUTED,
        contradiction_group_local_ref="conflict",
        uncertainty=[UncertaintyDimension.ASSERTION_STATUS],
        evidence=[ProviderFactEvidenceCandidate(excerpt=first_text, supports=contradiction_supports)],
    )
    second = fact(
        second_text,
        local_ref="account-b",
        assertion_status=AssertionStatus.DISPUTED,
        contradiction_group_local_ref="conflict",
        uncertainty=[UncertaintyDimension.ASSERTION_STATUS],
        evidence=[ProviderFactEvidenceCandidate(excerpt=second_text, supports=contradiction_supports)],
    )
    assert validate(adapt(narrative, [second, first]), narrative).passed

    one_member = adapt(first_text, [first])
    result = validate(one_member, first_text)
    assert ValidationIssueCode.INVALID_CONTRADICTION_GROUP in {issue.code for issue in result.domain_validation.issues}


def test_domain_validation_is_deterministic():
    narrative = "The employee denied making any physical contact today."
    envelope = adapt(narrative, [fact(narrative)])
    assert validate(envelope, narrative) == validate(envelope, narrative)
