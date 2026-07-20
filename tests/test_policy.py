import inspect

import pytest

from src.contracts import (
    AssertionStatus,
    CompletenessStatus,
    Conduct,
    FactDirection,
    IncidentDirection,
    Intentionality,
    MaterialAttribute,
    PolicyOutcome,
    PolicyReasonCode,
    ProcessingStatus,
    ProviderFactCandidate,
    ProviderFactEvidenceCandidate,
    ProviderStructuredResponse,
    ResolutionStatus,
    TemporalScope,
    UncertaintyDimension,
)
from src.models import Incident
from src.policy import evaluate_policy
from src.provider_adapter import semantic_candidate_from_provider_response
from src.semantic_validation import validate_semantic_candidate


BASE_SUPPORTS = [
    MaterialAttribute.CONDUCT,
    MaterialAttribute.DIRECTION,
    MaterialAttribute.INTENTIONALITY,
    MaterialAttribute.TEMPORAL_SCOPE,
    MaterialAttribute.ASSERTION_STATUS,
]


def fact(local_ref, excerpt, **updates):
    values = dict(
        local_ref=local_ref,
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


def validation(narrative, facts):
    envelope = semantic_candidate_from_provider_response(
        ProviderStructuredResponse(facts=facts),
        incident=Incident(incident_id="CASE", narrative=narrative),
    )
    result = validate_semantic_candidate(
        envelope,
        incident_id="CASE",
        normalized_narrative=narrative,
    )
    assert result.passed
    return result


def decision(narrative, facts):
    result = validation(narrative, facts)
    return evaluate_policy(
        validated=result.validated_envelope,
        processing_status=result.processing_status,
        completeness_status=result.completeness_status,
        derived=result.derived_semantics,
    )


@pytest.mark.parametrize("conduct,direction,narrative", [
    (Conduct.VERBAL_THREAT, FactDirection.INTERPERSONAL, "He intentionally threatened physical violence today."),
    (Conduct.PHYSICAL_ATTEMPT, FactDirection.INTERPERSONAL, "He intentionally swung at a coworker but missed today."),
    (Conduct.PHYSICAL_CONTACT, FactDirection.INTERPERSONAL, "He intentionally punched a coworker today."),
    (Conduct.SELF_HARM, FactDirection.SELF_DIRECTED, "She intentionally struck herself today."),
    (Conduct.PROPERTY_VIOLENCE, FactDirection.OBJECT_DIRECTED, "He intentionally smashed the office monitor today."),
])
def test_every_doctrinal_qualifying_conduct_is_detected(conduct, direction, narrative):
    result = decision(narrative, [fact("event", narrative, conduct=conduct, direction=direction)])
    assert result.outcome == PolicyOutcome.VIOLENCE_DETECTED
    assert result.reason_codes == [PolicyReasonCode.QUALIFYING_CURRENT_VIOLENCE]


def test_unknown_direction_alone_does_not_suppress_qualifying_violence():
    narrative = "The report confirms intentional physical violence today, but direction is unknown."
    result = validation(narrative, [fact(
        "event",
        narrative,
        direction=FactDirection.UNKNOWN,
        uncertainty=[UncertaintyDimension.DIRECTION],
    )])
    assert result.derived_semantics.incident_direction == IncidentDirection.UNKNOWN
    assert result.completeness_status == CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS
    policy = evaluate_policy(
        validated=result.validated_envelope,
        processing_status=result.processing_status,
        completeness_status=result.completeness_status,
        derived=result.derived_semantics,
    )
    assert policy.outcome == PolicyOutcome.VIOLENCE_DETECTED


@pytest.mark.parametrize("narrative,updates", [
    ("The cart accidentally bumped the employee today.", {"intentionality": Intentionality.ACCIDENTAL}),
    ("He intentionally punched a coworker last year.", {"temporal_scope": TemporalScope.HISTORICAL}),
    ("He denied intentionally punching a coworker today.", {"assertion_status": AssertionStatus.DENIED}),
])
def test_accidental_historical_and_denied_conduct_never_qualifies(narrative, updates):
    assert decision(narrative, [fact("event", narrative, **updates)]).outcome == PolicyOutcome.NO_VIOLENCE_DETECTED


@pytest.mark.parametrize("dimension,updates", [
    (UncertaintyDimension.CONDUCT, {"conduct": None}),
    (UncertaintyDimension.INTENTIONALITY, {"intentionality": Intentionality.UNRESOLVED}),
    (UncertaintyDimension.TEMPORAL_SCOPE, {"temporal_scope": TemporalScope.UNRESOLVED}),
    (UncertaintyDimension.ASSERTION_STATUS, {"assertion_status": AssertionStatus.UNRESOLVED}),
])
def test_material_unresolved_classification_facts_are_uncertain(dimension, updates):
    narrative = "The report preserves a potentially qualifying current incident fact as unresolved."
    result = decision(
        narrative,
        [fact("event", narrative, uncertainty=[dimension], **updates)],
    )
    assert result.outcome == PolicyOutcome.UNCERTAIN
    assert result.reason_codes == [PolicyReasonCode.MATERIAL_SEMANTIC_UNCERTAINTY]


def test_active_unresolved_qualifying_contradiction_is_uncertain():
    first_text = "Witness A said he intentionally punched the coworker today."
    second_text = "Witness B said he did not intentionally punch the coworker today."
    narrative = f"{first_text} {second_text}"
    supports = BASE_SUPPORTS + [MaterialAttribute.CONTRADICTION]
    facts = [
        fact(
            "account-a", first_text,
            assertion_status=AssertionStatus.DISPUTED,
            contradiction_group_local_ref="conflict",
            uncertainty=[UncertaintyDimension.ASSERTION_STATUS],
            evidence=[ProviderFactEvidenceCandidate(excerpt=first_text, supports=supports)],
        ),
        fact(
            "account-b", second_text,
            assertion_status=AssertionStatus.DISPUTED,
            contradiction_group_local_ref="conflict",
            uncertainty=[UncertaintyDimension.ASSERTION_STATUS],
            evidence=[ProviderFactEvidenceCandidate(excerpt=second_text, supports=supports)],
        ),
    ]
    result = decision(narrative, facts)
    assert result.outcome == PolicyOutcome.UNCERTAIN
    assert result.reason_codes == [
        PolicyReasonCode.UNRESOLVED_CONTRADICTION,
        PolicyReasonCode.MATERIAL_SEMANTIC_UNCERTAINTY,
    ]


def test_certain_qualifying_fact_is_detected_despite_unrelated_unresolved_fact():
    detected_text = "He intentionally punched a coworker today."
    unresolved_text = "A separate potentially qualifying event has unresolved intent today."
    narrative = f"{detected_text} {unresolved_text}"
    result = decision(narrative, [
        fact("detected", detected_text),
        fact(
            "unresolved", unresolved_text,
            intentionality=Intentionality.UNRESOLVED,
            uncertainty=[UncertaintyDimension.INTENTIONALITY],
        ),
    ])
    assert result.outcome == PolicyOutcome.VIOLENCE_DETECTED


def test_historical_contradiction_does_not_create_current_classification_uncertainty():
    first_text = "Witness A described an intentional punch last year."
    second_text = "Witness B disputed the intentional punch last year."
    narrative = f"{first_text} {second_text}"
    supports = BASE_SUPPORTS + [MaterialAttribute.CONTRADICTION]
    common = dict(
        temporal_scope=TemporalScope.HISTORICAL,
        assertion_status=AssertionStatus.DISPUTED,
        contradiction_group_local_ref="historical-conflict",
        uncertainty=[UncertaintyDimension.ASSERTION_STATUS],
    )
    result = decision(narrative, [
        fact("account-a", first_text, evidence=[ProviderFactEvidenceCandidate(excerpt=first_text, supports=supports)], **common),
        fact("account-b", second_text, evidence=[ProviderFactEvidenceCandidate(excerpt=second_text, supports=supports)], **common),
    ])
    assert result.outcome == PolicyOutcome.NO_VIOLENCE_DETECTED


def test_superseded_violent_fact_never_participates_in_classification():
    earlier_text = "Initial report: he intentionally shoved her today."
    later_text = "Later corrected: the contact was accidental today."
    narrative = f"{earlier_text} {later_text}"
    earlier = fact(
        "earlier", earlier_text,
        resolution_status=ResolutionStatus.SUPERSEDED,
    )
    later = fact(
        "later", later_text,
        intentionality=Intentionality.ACCIDENTAL,
        supersedes_local_ref="earlier",
        evidence=[ProviderFactEvidenceCandidate(
            excerpt=later_text,
            supports=BASE_SUPPORTS + [MaterialAttribute.SUPERSESSION],
        )],
    )
    result = validation(narrative, [later, earlier])
    assert result.derived_semantics.active_fact_ids == ("FACT-0002",)
    assert result.derived_semantics.superseded_fact_ids == ("FACT-0001",)
    assert evaluate_policy(
        validated=result.validated_envelope,
        processing_status=result.processing_status,
        completeness_status=result.completeness_status,
        derived=result.derived_semantics,
    ).outcome == PolicyOutcome.NO_VIOLENCE_DETECTED


def test_incident_direction_derives_interpersonal_self_object_multiple_and_unknown():
    interpersonal = "He intentionally punched a coworker today."
    self_directed = "She intentionally struck herself today."
    object_directed = "He intentionally smashed the office monitor today."
    cases = [
        ([fact("one", interpersonal)], interpersonal, IncidentDirection.INTERPERSONAL),
        ([fact("one", self_directed, conduct=Conduct.SELF_HARM, direction=FactDirection.SELF_DIRECTED)], self_directed, IncidentDirection.SELF_DIRECTED),
        ([fact("one", object_directed, conduct=Conduct.PROPERTY_VIOLENCE, direction=FactDirection.OBJECT_DIRECTED)], object_directed, IncidentDirection.OBJECT_DIRECTED),
        ([], "No semantic facts were extracted.", IncidentDirection.UNKNOWN),
    ]
    for facts, narrative, expected in cases:
        assert validation(narrative, facts).derived_semantics.incident_direction == expected

    narrative = f"{interpersonal} {self_directed}"
    result = validation(narrative, [
        fact("interpersonal", interpersonal),
        fact("self", self_directed, conduct=Conduct.SELF_HARM, direction=FactDirection.SELF_DIRECTED),
    ])
    assert result.derived_semantics.incident_direction == IncidentDirection.MULTIPLE


def test_complete_admissible_empty_analysis_is_no_violence_only_with_repository_status():
    result = validation("No semantic facts were extracted.", [])
    assert result.completeness_status == CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS
    policy = evaluate_policy(
        validated=result.validated_envelope,
        processing_status=result.processing_status,
        completeness_status=result.completeness_status,
        derived=result.derived_semantics,
    )
    assert policy.outcome == PolicyOutcome.NO_VIOLENCE_DETECTED


@pytest.mark.parametrize("status,reason", [
    (ProcessingStatus.PROVIDER_FAILURE, PolicyReasonCode.PROVIDER_FAILURE),
    (ProcessingStatus.SCHEMA_FAILURE, PolicyReasonCode.SCHEMA_FAILURE),
    (ProcessingStatus.VALIDATION_FAILURE, PolicyReasonCode.VALIDATION_FAILURE),
    (ProcessingStatus.PIPELINE_FAILURE, PolicyReasonCode.PIPELINE_FAILURE),
])
def test_processing_failures_are_unable_to_determine(status, reason):
    result = evaluate_policy(
        validated=None,
        processing_status=status,
        completeness_status=CompletenessStatus.INCOMPLETE_ANALYSIS,
        derived=None,
    )
    assert result.outcome == PolicyOutcome.UNABLE_TO_DETERMINE
    assert result.reason_codes == [reason]


def test_incomplete_or_malformed_success_state_is_unable_to_determine():
    incomplete = evaluate_policy(
        validated=None,
        processing_status=ProcessingStatus.SUCCESSFUL_ANALYSIS,
        completeness_status=CompletenessStatus.INCOMPLETE_ANALYSIS,
        derived=None,
    )
    malformed = evaluate_policy(
        validated=None,
        processing_status=ProcessingStatus.SUCCESSFUL_ANALYSIS,
        completeness_status=CompletenessStatus.COMPLETE_ADMISSIBLE_ANALYSIS,
        derived=None,
    )
    assert incomplete.outcome == malformed.outcome == PolicyOutcome.UNABLE_TO_DETERMINE
    assert incomplete.reason_codes == [PolicyReasonCode.INCOMPLETE_ANALYSIS]
    assert malformed.reason_codes == [PolicyReasonCode.MALFORMED_SEMANTIC_INPUT]


def test_tampered_derived_view_or_completeness_state_is_unable_to_determine():
    narrative = "He intentionally punched a coworker today."
    result = validation(narrative, [fact("event", narrative)])
    tampered_view = result.derived_semantics.model_copy(update={"active_fact_ids": ()})
    view_decision = evaluate_policy(
        validated=result.validated_envelope,
        processing_status=result.processing_status,
        completeness_status=result.completeness_status,
        derived=tampered_view,
    )
    completeness_decision = evaluate_policy(
        validated=result.validated_envelope,
        processing_status=result.processing_status,
        completeness_status=CompletenessStatus.UNRESOLVED_SEMANTIC_CONTENT,
        derived=result.derived_semantics,
    )
    assert view_decision.outcome == completeness_decision.outcome == PolicyOutcome.UNABLE_TO_DETERMINE
    assert view_decision.reason_codes == completeness_decision.reason_codes == [
        PolicyReasonCode.MALFORMED_SEMANTIC_INPUT,
    ]


def test_policy_has_no_provider_presentation_or_policy_candidate_input():
    assert set(inspect.signature(evaluate_policy).parameters) == {
        "validated", "processing_status", "completeness_status", "derived",
    }
    assert set(ProviderStructuredResponse.model_fields).isdisjoint({
        "processing_status", "completeness_status", "policy_outcome", "reason_codes",
    })
    assert {item.value for item in PolicyOutcome} == {
        "Violence Detected", "No Violence Detected", "Uncertain", "Unable to Determine",
    }
