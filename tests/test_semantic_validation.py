from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.app_logic import AnalysisResult, run_analysis
from src.compatibility_finding import CompatibilityFindingStatus, construct_compatibility_finding
from src.contracts import (
    DomainValidationStatus,
    ProviderStructuredResponse,
    SchemaValidationStatus,
    SemanticFacts,
    ValidationFailureStage,
    ValidationIssueCode,
)
from src.domain_validation import validate_semantic_domain
from src.models import Incident, Intentionality, ViolenceEventType
from src.schema_validation import validate_semantic_schema
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus
from src.semantic_validation import validate_semantic_candidate


def candidate(**overrides):
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


def facts(**overrides):
    return SemanticFacts(**candidate(**overrides))


def issue_codes(result):
    return [issue.code for issue in result.issues]


def test_schema_validation_accepts_valid_semantic_facts_and_mapping():
    from_model = validate_semantic_schema(facts())
    from_mapping = validate_semantic_schema(candidate())

    assert from_model.status == SchemaValidationStatus.PASSED
    assert from_mapping.status == SchemaValidationStatus.PASSED
    assert from_model.semantic_facts == from_mapping.semantic_facts


def test_schema_validation_reports_missing_fields_in_contract_order():
    value = candidate()
    del value["violence_present"]
    del value["event_type"]

    result = validate_semantic_schema(value)

    assert result.status == SchemaValidationStatus.FAILED
    assert [(issue.code, issue.field) for issue in result.issues] == [
        (ValidationIssueCode.MISSING_REQUIRED_FIELD, "violence_present"),
        (ValidationIssueCode.MISSING_REQUIRED_FIELD, "event_type"),
    ]
    assert result.semantic_facts is None


@pytest.mark.parametrize(
    "field",
    ["policy_decision", "salesforce_payload", "workflow_action", "unexpected"],
)
def test_schema_validation_rejects_unsupported_operational_fields(field):
    result = validate_semantic_schema(candidate(**{field: "not_allowed"}))

    assert result.status == SchemaValidationStatus.FAILED
    assert issue_codes(result) == [ValidationIssueCode.UNSUPPORTED_FIELD]
    assert result.issues[0].field == field


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"event_type": "physical"}, ValidationIssueCode.INVALID_EVENT_TYPE),
        ({"intentionality": "maybe"}, ValidationIssueCode.INVALID_INTENTIONALITY),
        ({"violence_present": 1}, ValidationIssueCode.INVALID_BOOLEAN),
        ({"actor": 7}, ValidationIssueCode.INVALID_ACTOR),
        ({"target": []}, ValidationIssueCode.INVALID_TARGET),
        ({"evidence_text": "quoted text"}, ValidationIssueCode.INVALID_EVIDENCE_COLLECTION),
        ({"evidence_text": ["valid", 4]}, ValidationIssueCode.INVALID_EVIDENCE_ITEM),
        ({"confidence": "0.8"}, ValidationIssueCode.INVALID_CONFIDENCE_TYPE),
        ({"confidence": -0.1}, ValidationIssueCode.CONFIDENCE_OUT_OF_RANGE),
        ({"confidence": 1.1}, ValidationIssueCode.CONFIDENCE_OUT_OF_RANGE),
        ({"uncertainty_notes": "uncertain"}, ValidationIssueCode.INVALID_UNCERTAINTY_COLLECTION),
        ({"uncertainty_notes": [3]}, ValidationIssueCode.INVALID_UNCERTAINTY_ITEM),
    ],
)
def test_schema_validation_returns_bounded_typed_failures(overrides, code):
    result = validate_semantic_schema(candidate(**overrides))

    assert result.status == SchemaValidationStatus.FAILED
    assert issue_codes(result) == [code]
    assert result.semantic_facts is None


def test_schema_validation_rejects_provider_and_sdk_like_objects():
    provider = ProviderStructuredResponse(**candidate())

    provider_result = validate_semantic_schema(provider)
    sdk_result = validate_semantic_schema(SimpleNamespace(output_parsed=provider))

    assert issue_codes(provider_result) == [ValidationIssueCode.PROVIDER_OBJECT_NOT_ALLOWED]
    assert issue_codes(sdk_result) == [ValidationIssueCode.INVALID_CANDIDATE_TYPE]


def test_schema_issue_ordering_is_deterministic():
    value = candidate(z_policy=True, a_salesforce=True)
    del value["actor"]

    first = validate_semantic_schema(value)
    second = validate_semantic_schema(value)

    assert first == second
    assert [(item.code, item.field) for item in first.issues] == [
        (ValidationIssueCode.MISSING_REQUIRED_FIELD, "actor"),
        (ValidationIssueCode.UNSUPPORTED_FIELD, "a_salesforce"),
        (ValidationIssueCode.UNSUPPORTED_FIELD, "z_policy"),
    ]


@pytest.mark.parametrize(
    "value",
    [
        facts(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            actor=None,
            target=None,
            intentionality=Intentionality.UNCLEAR,
            negated=True,
            evidence_text=["did not hit anyone"],
        ),
        facts(event_type=ViolenceEventType.VERBAL_THREAT, evidence_text=["threatened to hit the nurse"]),
        facts(),
        facts(
            event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
            contact_occurred=True,
            evidence_text=["patient struck the nurse"],
        ),
    ],
)
def test_domain_validation_accepts_supported_event_shapes(value):
    result = validate_semantic_domain(value)

    assert result.status == DomainValidationStatus.PASSED
    assert result.issues == []


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        (
            {"violence_present": True, "event_type": ViolenceEventType.NONE},
            ValidationIssueCode.VIOLENCE_WITH_EVENT_TYPE_NONE,
        ),
        (
            {"violence_present": False, "event_type": ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE},
            ValidationIssueCode.PHYSICAL_EVENT_WITHOUT_VIOLENCE,
        ),
        (
            {"event_type": ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE, "contact_occurred": False},
            ValidationIssueCode.COMPLETED_VIOLENCE_WITHOUT_CONTACT,
        ),
        (
            {
                "violence_present": False,
                "event_type": ViolenceEventType.NONE,
                "contact_occurred": True,
                "intentionality": Intentionality.ACCIDENTAL,
            },
            ValidationIssueCode.EVENT_TYPE_NONE_WITH_CONTACT,
        ),
        (
            {
                "violence_present": False,
                "event_type": ViolenceEventType.UNCLEAR,
                "contact_occurred": True,
                "intentionality": Intentionality.UNCLEAR,
            },
            ValidationIssueCode.NONVIOLENT_NONACCIDENTAL_CONTACT,
        ),
        (
            {"negated": True, "violence_present": True, "current_event": True},
            ValidationIssueCode.NEGATED_CURRENT_AFFIRMATIVE_VIOLENCE,
        ),
        (
            {"conflicting_information": True, "uncertainty_notes": []},
            ValidationIssueCode.CONFLICT_WITHOUT_UNCERTAINTY,
        ),
        (
            {"evidence_text": ["valid", "  "]},
            ValidationIssueCode.EMPTY_EVIDENCE_ITEM,
        ),
    ],
)
def test_domain_validation_returns_repository_grounded_typed_failures(overrides, code):
    result = validate_semantic_domain(facts(**overrides))

    assert result.status == DomainValidationStatus.FAILED
    assert code in issue_codes(result)


def test_injury_without_violence_does_not_force_violence():
    result = validate_semantic_domain(
        facts(
            violence_present=False,
            event_type=ViolenceEventType.NONE,
            injury_mentioned=True,
            intentionality=Intentionality.UNCLEAR,
            evidence_text=["old bruise was noted"],
        )
    )

    assert result.status == DomainValidationStatus.PASSED


def test_corrected_negated_statement_is_admissible_without_repair():
    value = facts(
        violence_present=False,
        event_type=ViolenceEventType.NONE,
        intentionality=Intentionality.UNCLEAR,
        negated=True,
        correction_present=True,
        evidence_text=["correction: patient did not strike the nurse"],
    )

    result = validate_semantic_domain(value)

    assert result.status == DomainValidationStatus.PASSED
    assert value.evidence_text == ["correction: patient did not strike the nurse"]


def test_conflicting_facts_require_explicit_uncertainty_or_unclear_type():
    with_note = facts(conflicting_information=True, uncertainty_notes=["Statements conflict."])
    unclear = facts(
        violence_present=False,
        event_type=ViolenceEventType.UNCLEAR,
        conflicting_information=True,
        intentionality=Intentionality.UNCLEAR,
    )

    assert validate_semantic_domain(with_note).passed is True
    assert validate_semantic_domain(unclear).passed is True


def test_historical_and_current_event_values_remain_distinct_and_admissible():
    historical = facts(
        violence_present=False,
        event_type=ViolenceEventType.NONE,
        current_event=False,
        intentionality=Intentionality.UNCLEAR,
        evidence_text=["assaulted years ago"],
    )
    current = facts(current_event=True)

    assert validate_semantic_domain(historical).passed is True
    assert validate_semantic_domain(current).passed is True
    assert historical.current_event is False
    assert current.current_event is True


def test_domain_issue_ordering_and_repeated_execution_are_deterministic():
    value = facts(
        violence_present=True,
        event_type=ViolenceEventType.NONE,
        contact_occurred=True,
        negated=True,
        evidence_text=["", "  "],
    )

    first = validate_semantic_domain(value)
    second = validate_semantic_domain(value)

    assert first == second
    assert issue_codes(first) == [
        ValidationIssueCode.VIOLENCE_WITH_EVENT_TYPE_NONE,
        ValidationIssueCode.EVENT_TYPE_NONE_WITH_CONTACT,
        ValidationIssueCode.NEGATED_CURRENT_AFFIRMATIVE_VIOLENCE,
        ValidationIssueCode.EMPTY_EVIDENCE_ITEM,
        ValidationIssueCode.EMPTY_EVIDENCE_ITEM,
    ]


def test_domain_validation_rejects_non_schema_valid_input_without_inference():
    with pytest.raises(TypeError):
        validate_semantic_domain(candidate())


def test_combined_validation_short_circuits_domain_after_schema_failure():
    domain = Mock(side_effect=AssertionError("domain validation must not run"))

    result = validate_semantic_candidate({"violence_present": True}, domain_validator=domain)

    assert result.failure_stage == ValidationFailureStage.SCHEMA
    assert result.domain_validation.status == DomainValidationStatus.NOT_RUN
    assert result.validated_facts is None
    domain.assert_not_called()


def test_combined_validation_exposes_facts_only_after_both_stages_pass():
    successful = validate_semantic_candidate(candidate())
    domain_failure = validate_semantic_candidate(
        candidate(event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE, contact_occurred=False)
    )

    assert successful.failure_stage == ValidationFailureStage.NONE
    assert successful.validated_facts is not None
    assert domain_failure.failure_stage == ValidationFailureStage.DOMAIN
    assert domain_failure.schema_validation.passed is True
    assert domain_failure.validated_facts is None
    assert validate_semantic_candidate(candidate()) == successful


def test_compatibility_constructor_rejects_raw_facts_and_accepts_validated_facts():
    raw = facts()
    rejected = construct_compatibility_finding(raw)
    validated = validate_semantic_candidate(raw).validated_facts
    accepted = construct_compatibility_finding(validated)

    assert rejected.status == CompatibilityFindingStatus.VALIDATION_FAILURE
    assert rejected.finding is None
    assert accepted.status == CompatibilityFindingStatus.SUCCESS
    assert accepted.finding.model_dump(mode="json") == raw.model_dump(mode="json")
    assert construct_compatibility_finding(validated) == accepted


@pytest.mark.parametrize(
    ("semantic_candidate", "stage", "status"),
    [
        ({"violence_present": True}, ValidationFailureStage.SCHEMA, "schema_validation_failure"),
        (
            candidate(event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE, contact_occurred=False),
            ValidationFailureStage.DOMAIN,
            "domain_validation_failure",
        ),
    ],
)
def test_analysis_validation_failure_blocks_finding_preview_and_comparison(
    semantic_candidate,
    stage,
    status,
):
    semantic_result = SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        semantic_candidate=semantic_candidate,
    )

    result = run_analysis(
        Incident(incident_id="CASE_X", narrative="patient swung at the nurse"),
        extractor=lambda _incident: semantic_result,
    )

    assert isinstance(result, AnalysisResult)
    assert result.validation_result.failure_stage == stage
    assert result.validation_result.validated_facts is None
    assert result.compatibility_result is None
    assert result.salesforce_preview is None
    assert result.comparison.classification_alignment == "semantic_failure"
    assert result.comparison.semantic_validation_status == status
    assert "validation failed" in result.comparison.divergence_observations[0].lower()
