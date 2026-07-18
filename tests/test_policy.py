from collections import Counter
from itertools import product
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from src.app_logic import AnalysisResult, run_analysis
from src.compatibility_finding import (
    CompatibilityFindingResult,
    CompatibilityFindingStatus,
    construct_compatibility_finding,
)
from src.contracts import (
    InputValidationResult,
    PipelineFailureProvenance,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    SemanticFacts,
    ValidationIssueCode,
)
from src.models import Incident, Intentionality, ViolenceEventType
from src.policy import POLICY_ID, POLICY_VERSION, evaluate_policy, failed_policy_decision
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from src.semantic_validation import validate_semantic_candidate


def fact_values(**overrides):
    values = {
        "violence_present": True,
        "event_type": ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
        "actor": "patient",
        "target": "nurse",
        "contact_occurred": False,
        "injury_mentioned": False,
        "current_event": True,
        "intentionality": Intentionality.INTENTIONAL,
        "negated": False,
        "correction_present": False,
        "conflicting_information": False,
        "evidence_text": ["patient swung at the nurse and missed"],
        "confidence": 0.8,
        "uncertainty_notes": [],
    }
    values.update(overrides)
    return values


def policy_inputs(**overrides):
    facts = SemanticFacts(**fact_values(**overrides))
    validation = validate_semantic_candidate(facts)
    assert validation.validated_facts is not None
    compatibility = construct_compatibility_finding(validation.validated_facts)
    assert compatibility.finding is not None
    return validation.validated_facts, compatibility.finding


def decision(**overrides):
    validated, finding = policy_inputs(**overrides)
    return evaluate_policy(validated_facts=validated, finding=finding)


def semantic_success(**overrides):
    return SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        semantic_candidate=SemanticFacts(**fact_values(**overrides)),
    )


def test_policy_contract_constructs_and_serializes_stably():
    value = PolicyDecision(
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        outcome=PolicyOutcome.WRITE_DETECTED,
        reason_codes=[PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT],
        explanation="Validated facts affirmatively represent violence or a threat.",
    )

    assert value.model_dump(mode="json") == {
        "policy_id": "violence_checker_write_disposition",
        "policy_version": "1.0.1",
        "outcome": "WRITE_DETECTED",
        "reason_codes": ["affirmative_violence_or_threat"],
        "explanation": "Validated facts affirmatively represent violence or a threat.",
        "failure_provenance": None,
    }
    assert value.model_dump_json() == value.model_dump_json()


def test_policy_outcomes_and_reason_codes_are_bounded():
    with pytest.raises(ValidationError):
        PolicyDecision(
            policy_id=POLICY_ID,
            policy_version=POLICY_VERSION,
            outcome="WRITE_SOMETHING_ELSE",
            reason_codes=[PolicyReasonCode.NO_VIOLENCE],
            explanation="invalid",
        )
    with pytest.raises(ValidationError):
        PolicyDecision(
            policy_id=POLICY_ID,
            policy_version=POLICY_VERSION,
            outcome=PolicyOutcome.WRITE_NOT_DETECTED,
            reason_codes=["unknown_reason"],
            explanation="invalid",
        )


def test_policy_contract_is_provider_independent_and_contains_no_salesforce_identity():
    fields = set(PolicyDecision.model_fields)
    serialized = decision().model_dump_json().lower()

    assert "provider" not in fields
    assert "openai" not in fields
    assert "salesforce" not in fields
    assert "credential" not in fields
    assert "openai" not in serialized
    assert "salesforce" not in serialized


@pytest.mark.parametrize(
    ("failure", "reason"),
    [
        (PipelineFailureProvenance.INPUT_VALIDATION, PolicyReasonCode.INPUT_VALIDATION_FAILED),
        (
            PipelineFailureProvenance.PROVIDER_CONFIGURATION,
            PolicyReasonCode.PROVIDER_CONFIGURATION_FAILED,
        ),
        (PipelineFailureProvenance.PROVIDER_REQUEST, PolicyReasonCode.PROVIDER_REQUEST_FAILED),
        (
            PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE,
            PolicyReasonCode.PROVIDER_STRUCTURED_RESPONSE_FAILED,
        ),
        (
            PipelineFailureProvenance.PROVIDER_VALIDATION,
            PolicyReasonCode.PROVIDER_VALIDATION_FAILED,
        ),
        (PipelineFailureProvenance.SCHEMA_VALIDATION, PolicyReasonCode.SCHEMA_VALIDATION_FAILED),
        (PipelineFailureProvenance.DOMAIN_VALIDATION, PolicyReasonCode.DOMAIN_VALIDATION_FAILED),
        (
            PipelineFailureProvenance.COMPATIBILITY_CONSTRUCTION,
            PolicyReasonCode.COMPATIBILITY_CONSTRUCTION_FAILED,
        ),
        (
            PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT,
            PolicyReasonCode.UNSUPPORTED_POLICY_INPUT,
        ),
    ],
)
def test_each_typed_failure_maps_to_write_failed_with_provenance(failure, reason):
    result = failed_policy_decision(failure)

    assert result.outcome == PolicyOutcome.WRITE_FAILED
    assert result.reason_codes == [reason]
    assert result.failure_provenance == failure


def test_failure_precedence_overrides_admissible_detected_inputs():
    validated, finding = policy_inputs()

    result = evaluate_policy(
        validated_facts=validated,
        finding=finding,
        failure=PipelineFailureProvenance.PROVIDER_REQUEST,
    )

    assert result.outcome == PolicyOutcome.WRITE_FAILED
    assert result.reason_codes == [PolicyReasonCode.PROVIDER_REQUEST_FAILED]


@pytest.mark.parametrize(
    "overrides",
    [
        {"event_type": ViolenceEventType.UNCLEAR, "intentionality": Intentionality.UNCLEAR},
        {
            "conflicting_information": True,
            "uncertainty_notes": ["Statements remain in conflict."],
        },
    ],
)
def test_explicit_uncertainty_produces_write_uncertain(overrides):
    result = decision(**overrides)

    assert result.outcome == PolicyOutcome.WRITE_UNCERTAIN


def test_nonaffirmative_verbal_threat_is_explicitly_uncertain():
    result = decision(
        violence_present=False,
        event_type=ViolenceEventType.VERBAL_THREAT,
        contact_occurred=False,
        intentionality=Intentionality.INTENTIONAL,
    )

    assert result.outcome == PolicyOutcome.WRITE_UNCERTAIN
    assert result.reason_codes == [PolicyReasonCode.THREAT_WITHOUT_VIOLENCE_INDICATION]


def test_uncertainty_precedence_and_reason_order_are_deterministic():
    overrides = {
        "event_type": ViolenceEventType.UNCLEAR,
        "intentionality": Intentionality.UNCLEAR,
        "conflicting_information": True,
        "uncertainty_notes": ["Statements remain unresolved."],
    }

    first = decision(**overrides)
    second = decision(**overrides)

    assert first == second
    assert first.outcome == PolicyOutcome.WRITE_UNCERTAIN
    assert first.reason_codes == [
        PolicyReasonCode.CONFLICTING_INFORMATION,
        PolicyReasonCode.UNCLEAR_EVENT_TYPE,
        PolicyReasonCode.UNCLEAR_MATERIAL_INTENTIONALITY,
    ]


@pytest.mark.parametrize(
    "event_type",
    [
        ViolenceEventType.VERBAL_THREAT,
        ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
        ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
    ],
)
def test_supported_affirmative_events_produce_write_detected(event_type):
    overrides = {"event_type": event_type}
    if event_type == ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE:
        overrides["contact_occurred"] = True

    result = decision(**overrides)

    assert result.outcome == PolicyOutcome.WRITE_DETECTED
    assert result.reason_codes == [PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT]


def test_provider_confidence_alone_does_not_change_detected_outcome():
    low = decision(confidence=0.01)
    high = decision(confidence=1.0)

    assert low.outcome == PolicyOutcome.WRITE_DETECTED
    assert high.outcome == PolicyOutcome.WRITE_DETECTED
    assert low.reason_codes == high.reason_codes


@pytest.mark.parametrize(
    ("overrides", "expected_reasons"),
    [
        (
            {},
            [PolicyReasonCode.NO_VIOLENCE],
        ),
        (
            {"negated": True},
            [PolicyReasonCode.NO_VIOLENCE, PolicyReasonCode.NEGATED_NON_EVENT],
        ),
        (
            {"negated": True, "correction_present": True},
            [
                PolicyReasonCode.NO_VIOLENCE,
                PolicyReasonCode.NEGATED_NON_EVENT,
                PolicyReasonCode.CORRECTED_NON_EVENT,
            ],
        ),
    ],
)
def test_supported_absence_produces_write_not_detected(overrides, expected_reasons):
    base = {
        "violence_present": False,
        "event_type": ViolenceEventType.NONE,
        "actor": None,
        "target": None,
        "intentionality": Intentionality.UNCLEAR,
        "evidence_text": ["no violence occurred"],
    }
    base.update(overrides)

    result = decision(**base)

    assert result.outcome == PolicyOutcome.WRITE_NOT_DETECTED
    assert result.reason_codes == expected_reasons


def test_unsupported_or_mismatched_inputs_fail_without_negative_default():
    validated, finding = policy_inputs()
    mismatched = finding.model_copy(update={"actor": "different actor"})

    missing = evaluate_policy()
    mismatch = evaluate_policy(validated_facts=validated, finding=mismatched)

    assert missing.outcome == PolicyOutcome.WRITE_FAILED
    assert mismatch.outcome == PolicyOutcome.WRITE_FAILED
    assert PolicyReasonCode.NO_VIOLENCE not in missing.reason_codes
    assert PolicyReasonCode.NO_VIOLENCE not in mismatch.reason_codes


def test_compatibility_equality_uses_identical_canonical_contract_fields():
    validated, finding = policy_inputs()
    facts = validated.facts

    assert set(type(facts).model_fields) == set(type(finding).model_fields)
    assert facts.model_dump() == finding.model_dump()
    assert facts.model_dump(mode="json") == finding.model_dump(mode="json")

    mismatched = finding.model_copy(update={"current_event": False})
    assert facts.model_dump(mode="json") != mismatched.model_dump(mode="json")
    assert evaluate_policy(
        validated_facts=validated,
        finding=mismatched,
    ).failure_provenance == PipelineFailureProvenance.UNSUPPORTED_POLICY_INPUT


@pytest.mark.parametrize(
    ("overrides", "expected_issue"),
    [
        (
            {"negated": True},
            ValidationIssueCode.NEGATED_CURRENT_AFFIRMATIVE_VIOLENCE,
        ),
        (
            {"conflicting_information": True},
            ValidationIssueCode.CONFLICT_WITHOUT_UNCERTAINTY,
        ),
        (
            {
                "violence_present": False,
                "event_type": ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
                "contact_occurred": True,
            },
            ValidationIssueCode.PHYSICAL_EVENT_WITHOUT_VIOLENCE,
        ),
    ],
)
def test_invalid_policy_states_are_rejected_before_policy(overrides, expected_issue):
    validation = validate_semantic_candidate(SemanticFacts(**fact_values(**overrides)))

    assert validation.validated_facts is None
    assert expected_issue in [issue.code for issue in validation.domain_validation.issues]


@pytest.mark.parametrize(
    ("overrides", "expected_reasons"),
    [
        (
            {"negated": True, "correction_present": True},
            [PolicyReasonCode.NEGATED_AFFIRMATIVE_FINDING],
        ),
        (
            {
                "negated": True,
                "conflicting_information": True,
                "uncertainty_notes": ["Statements conflict."],
            },
            [
                PolicyReasonCode.CONFLICTING_INFORMATION,
                PolicyReasonCode.NEGATED_AFFIRMATIVE_FINDING,
            ],
        ),
        (
            {
                "event_type": ViolenceEventType.UNCLEAR,
                "conflicting_information": True,
            },
            [PolicyReasonCode.CONFLICTING_INFORMATION, PolicyReasonCode.UNCLEAR_EVENT_TYPE],
        ),
    ],
)
def test_admissible_negation_correction_and_conflict_states_reach_uncertainty(
    overrides,
    expected_reasons,
):
    result = decision(**overrides)

    assert result.outcome == PolicyOutcome.WRITE_UNCERTAIN
    assert result.reason_codes == expected_reasons


def policy_partition_inventory():
    booleans = (False, True)
    inventory = Counter()

    for (
        event_type,
        intentionality,
        violence_present,
        contact_occurred,
        injury_mentioned,
        current_event,
        negated,
        correction_present,
        conflicting_information,
        has_uncertainty_note,
    ) in product(
        ViolenceEventType,
        Intentionality,
        booleans,
        booleans,
        booleans,
        booleans,
        booleans,
        booleans,
        booleans,
        booleans,
    ):
        facts = SemanticFacts(
            **fact_values(
                violence_present=violence_present,
                event_type=event_type,
                contact_occurred=contact_occurred,
                injury_mentioned=injury_mentioned,
                current_event=current_event,
                intentionality=intentionality,
                negated=negated,
                correction_present=correction_present,
                conflicting_information=conflicting_information,
                uncertainty_notes=["unresolved"] if has_uncertainty_note else [],
            )
        )
        validation = validate_semantic_candidate(facts)
        if validation.validated_facts is None:
            inventory["domain_rejected"] += 1
            continue

        inventory["domain_admitted"] += 1
        compatibility = construct_compatibility_finding(validation.validated_facts)
        assert compatibility.finding is not None
        result = evaluate_policy(
            validated_facts=validation.validated_facts,
            finding=compatibility.finding,
        )
        inventory[result.outcome.value] += 1
        assert result.failure_provenance is None

    return inventory


def test_all_admissible_policy_partitions_have_an_explicit_nonterminal_outcome():
    first = policy_partition_inventory()
    second = policy_partition_inventory()

    assert first == second
    assert first == Counter(
        {
            "domain_rejected": 2228,
            "domain_admitted": 1612,
            "WRITE_UNCERTAIN": 1356,
            "WRITE_DETECTED": 160,
            "WRITE_NOT_DETECTED": 96,
        }
    )


@pytest.mark.parametrize(
    "notes",
    [
        [],
        ["Actor and target abbreviations pt and rn are preserved."],
        ["The secondary shorthand no loc is ambiguous."],
        ["Arbitrary free-form extraction caveat."],
    ],
)
def test_completed_assault_ignores_incidental_notes_as_policy_authority(notes):
    result = decision(
        event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
        contact_occurred=True,
        injury_mentioned=True,
        uncertainty_notes=notes,
    )

    assert result.outcome == PolicyOutcome.WRITE_DETECTED
    assert result.reason_codes == [PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT]
    assert result.policy_version == "1.0.1"


def test_material_structured_uncertainty_overrides_incidental_notes():
    result = decision(
        event_type=ViolenceEventType.UNCLEAR,
        intentionality=Intentionality.UNCLEAR,
        uncertainty_notes=["Abbreviations are preserved."],
    )

    assert result.outcome == PolicyOutcome.WRITE_UNCERTAIN
    assert result.reason_codes == [
        PolicyReasonCode.UNCLEAR_EVENT_TYPE,
        PolicyReasonCode.UNCLEAR_MATERIAL_INTENTIONALITY,
    ]


def test_policy_makes_no_provider_call(monkeypatch):
    provider = Mock(side_effect=AssertionError("policy must not construct a provider client"))
    monkeypatch.setattr("openai.OpenAI", provider)

    result = decision()

    assert result.outcome == PolicyOutcome.WRITE_DETECTED
    provider.assert_not_called()


def test_invalid_input_analysis_returns_write_failed_without_provider_call():
    result = run_analysis({"incident_id": "CASE_X", "narrative": "bad\x00input"})

    assert isinstance(result, InputValidationResult)
    assert result.policy_decision is not None
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED
    assert result.policy_decision.failure_provenance == PipelineFailureProvenance.INPUT_VALIDATION


@pytest.mark.parametrize(
    ("status", "provenance"),
    [
        (
            SemanticExtractionStatus.CONFIGURATION_FAILURE,
            PipelineFailureProvenance.PROVIDER_CONFIGURATION,
        ),
        (SemanticExtractionStatus.REQUEST_FAILURE, PipelineFailureProvenance.PROVIDER_REQUEST),
        (
            SemanticExtractionStatus.STRUCTURED_RESPONSE_FAILURE,
            PipelineFailureProvenance.PROVIDER_STRUCTURED_RESPONSE,
        ),
        (
            SemanticExtractionStatus.VALIDATION_FAILURE,
            PipelineFailureProvenance.PROVIDER_VALIDATION,
        ),
    ],
)
def test_provider_failures_produce_write_failed_and_no_preview(status, provenance):
    semantic_result = SemanticExtractionResult(status=status, failure_message="bounded failure")

    result = run_analysis(
        Incident(incident_id="CASE_X", narrative="incident narrative"),
        extractor=lambda _incident: semantic_result,
    )

    assert isinstance(result, AnalysisResult)
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED
    assert result.policy_decision.failure_provenance == provenance
    assert result.salesforce_preview is None


@pytest.mark.parametrize(
    ("semantic_candidate", "provenance"),
    [
        ({"violence_present": True}, PipelineFailureProvenance.SCHEMA_VALIDATION),
        (
            fact_values(
                event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
                contact_occurred=False,
            ),
            PipelineFailureProvenance.DOMAIN_VALIDATION,
        ),
    ],
)
def test_validation_failures_produce_write_failed_and_no_preview(
    semantic_candidate,
    provenance,
):
    result = run_analysis(
        Incident(incident_id="CASE_X", narrative="incident narrative"),
        extractor=lambda _incident: SemanticExtractionResult(
            status=SemanticExtractionStatus.SUCCESS,
            semantic_candidate=semantic_candidate,
        ),
    )

    assert isinstance(result, AnalysisResult)
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED
    assert result.policy_decision.failure_provenance == provenance
    assert result.salesforce_preview is None


def test_compatibility_failure_produces_write_failed_and_no_preview(monkeypatch):
    monkeypatch.setattr(
        "src.app_logic.construct_compatibility_finding",
        lambda _validated: CompatibilityFindingResult(
            status=CompatibilityFindingStatus.VALIDATION_FAILURE,
            failure_message="bounded compatibility failure",
        ),
    )

    result = run_analysis(
        Incident(incident_id="CASE_X", narrative="patient swung at nurse"),
        extractor=lambda _incident: semantic_success(),
    )

    assert isinstance(result, AnalysisResult)
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED
    assert (
        result.policy_decision.failure_provenance
        == PipelineFailureProvenance.COMPATIBILITY_CONSTRUCTION
    )
    assert result.salesforce_preview is None


@pytest.mark.parametrize(
    ("overrides", "outcome"),
    [
        ({}, PolicyOutcome.WRITE_DETECTED),
        (
            {"event_type": ViolenceEventType.UNCLEAR, "intentionality": Intentionality.UNCLEAR},
            PolicyOutcome.WRITE_UNCERTAIN,
        ),
        (
            {
                "violence_present": False,
                "event_type": ViolenceEventType.NONE,
                "actor": None,
                "target": None,
                "intentionality": Intentionality.UNCLEAR,
            },
            PolicyOutcome.WRITE_NOT_DETECTED,
        ),
    ],
)
def test_valid_analysis_produces_policy_and_allowed_preview(overrides, outcome):
    result = run_analysis(
        Incident(incident_id="CASE_X", narrative="incident narrative"),
        extractor=lambda _incident: semantic_success(**overrides),
    )

    assert isinstance(result, AnalysisResult)
    assert result.policy_decision.outcome == outcome
    assert result.salesforce_preview is not None
    assert result.salesforce_preview["Illustrative_Write_Disposition__c"] == outcome.value


def test_comparison_cannot_override_policy_outcome():
    result = run_analysis(
        Incident(incident_id="CASE_X", narrative="language with no regex match"),
        extractor=lambda _incident: semantic_success(
            event_type=ViolenceEventType.VERBAL_THREAT,
            evidence_text=["language with no regex match"],
        ),
    )

    assert isinstance(result, AnalysisResult)
    assert result.comparison.classification_alignment == "regex_negative_semantic_positive"
    assert result.policy_decision.outcome == PolicyOutcome.WRITE_DETECTED
