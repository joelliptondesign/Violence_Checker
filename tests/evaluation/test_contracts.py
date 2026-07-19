from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.contracts import (
    PipelineFailureProvenance,
    PolicyDecision,
    PolicyOutcome,
    PolicyReasonCode,
    SemanticFacts,
    ValidationFailureStage,
)
from src.evaluation import (
    BaselineClassification,
    BaselineComparison,
    BaselineComparisonObservation,
    BaselineObservationCode,
    CaseEvaluationResult,
    CaseEvaluationStatus,
    DifferenceClassification,
    DifferenceReasonCode,
    EvaluationArtifactProvenance,
    EvaluationCase,
    EvaluationCaseMetadata,
    EvaluationExecutionMode,
    ExpectedEvaluationOutcome,
    ExpectedField,
    ExpectedSemanticOutcome,
    FailurePattern,
    FieldDifference,
    NonComparableReason,
    ObservedEvaluationResult,
    ObservedSemanticOutcome,
    ObservedValidationOutcome,
    canonical_json,
)
from src.models import Intentionality, ViolenceEventType, ViolenceFinding


def semantic_facts() -> SemanticFacts:
    return SemanticFacts(
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


def compatibility_finding() -> ViolenceFinding:
    return ViolenceFinding.model_validate(semantic_facts().model_dump())


def policy_decision() -> PolicyDecision:
    return PolicyDecision(
        policy_id="violence_checker_write_disposition",
        policy_version="1.0.1",
        outcome=PolicyOutcome.WRITE_DETECTED,
        reason_codes=[PolicyReasonCode.AFFIRMATIVE_VIOLENCE_OR_THREAT],
        explanation="Validated facts indicate violence or a threat.",
    )


def provenance() -> EvaluationArtifactProvenance:
    return EvaluationArtifactProvenance(
        evaluation_schema_version="1.0.0",
        corpus_identity="test-only-contract-example",
        repository_commit="c411609c94d8b35a1276950316e2a135b6ff0d04",
        model_identifier=None,
        extraction_configuration_identity="semantic-prompt-contract",
        run_timestamp=datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc),
        execution_mode=EvaluationExecutionMode.TEST,
    )


def evaluation_case() -> EvaluationCase:
    return EvaluationCase(
        case_id="TEST_CASE_001",
        schema_version="1.0.0",
        synthetic=True,
        narrative="The patient threatened to hit the nurse.",
        metadata=EvaluationCaseMetadata(
            categories=["threat"],
            documentation_quality_tags=["direct_language", "single_event"],
            engineering_notes="Minimal contract-only example.",
        ),
        ground_truth=ExpectedEvaluationOutcome(
            semantic_outcome=ExpectedSemanticOutcome.SUCCESS,
            semantic_facts=semantic_facts(),
            compatibility_finding=compatibility_finding(),
            policy_decision=policy_decision(),
            intentionally_not_asserted=[
                ExpectedField.FAILURE_PROVENANCE,
                ExpectedField.VALIDATION_STAGE,
            ],
        ),
    )


def observed_success() -> ObservedEvaluationResult:
    return ObservedEvaluationResult(
        case_id="TEST_CASE_001",
        run_id="TEST_RUN_001",
        provenance=provenance(),
        semantic_outcome=ObservedSemanticOutcome.SUCCESS,
        validation_outcome=ObservedValidationOutcome.PASSED,
        semantic_facts=semantic_facts(),
        compatibility_finding=compatibility_finding(),
        policy_decision=policy_decision(),
    )


def material_difference(field: str = "semantic_facts.event_type") -> FieldDifference:
    return FieldDifference(
        field=field,
        expected_value="verbal_threat",
        observed_value="unclear",
        classification=DifferenceClassification.VALUE_MISMATCH,
        reason_code=DifferenceReasonCode.VALUES_DIFFER,
    )


def test_valid_contracts_compose_authoritative_repository_types() -> None:
    case = evaluation_case()
    observation = observed_success()

    assert isinstance(case.ground_truth.semantic_facts, SemanticFacts)
    assert isinstance(case.ground_truth.compatibility_finding, ViolenceFinding)
    assert isinstance(case.ground_truth.policy_decision, PolicyDecision)
    assert observation.semantic_facts == case.ground_truth.semantic_facts


def test_canonical_serialization_is_deterministic() -> None:
    first = canonical_json(evaluation_case())
    second = canonical_json(evaluation_case())

    assert first == second
    assert first.startswith('{"case_id":"TEST_CASE_001","ground_truth":')
    assert '"event_type":"verbal_threat"' in first


@pytest.mark.parametrize("field", ["case_id", "schema_version"])
def test_evaluation_case_rejects_malformed_identifiers(field: str) -> None:
    data = evaluation_case().model_dump()
    data[field] = "   "

    with pytest.raises(ValidationError):
        EvaluationCase.model_validate(data)


def test_evaluation_case_requires_explicit_synthetic_designation() -> None:
    data = evaluation_case().model_dump()
    data["synthetic"] = False

    with pytest.raises(ValidationError):
        EvaluationCase.model_validate(data)


def test_evaluation_contracts_reject_unknown_fields() -> None:
    data = evaluation_case().model_dump()
    data["observed_result"] = semantic_facts().model_dump()

    with pytest.raises(ValidationError):
        EvaluationCase.model_validate(data)


def test_expected_success_requires_payload_and_rejects_failure_provenance() -> None:
    with pytest.raises(ValidationError):
        ExpectedEvaluationOutcome(
            semantic_outcome=ExpectedSemanticOutcome.SUCCESS,
            failure_provenance=PipelineFailureProvenance.PROVIDER_REQUEST,
        )


def test_expected_failure_rejects_success_payloads() -> None:
    with pytest.raises(ValidationError):
        ExpectedEvaluationOutcome(
            semantic_outcome=ExpectedSemanticOutcome.FAILURE,
            semantic_facts=semantic_facts(),
            validation_failure_stage=ValidationFailureStage.SCHEMA,
        )


def test_intentionally_unasserted_fields_cannot_also_be_asserted() -> None:
    with pytest.raises(ValidationError):
        ExpectedEvaluationOutcome(
            semantic_outcome=ExpectedSemanticOutcome.SUCCESS,
            semantic_facts=semantic_facts(),
            policy_decision=policy_decision(),
            intentionally_not_asserted=[ExpectedField.POLICY_DECISION],
        )


def test_observed_success_requires_passed_validation_and_facts() -> None:
    with pytest.raises(ValidationError):
        ObservedEvaluationResult(
            case_id="TEST_CASE_001",
            run_id="TEST_RUN_001",
            provenance=provenance(),
            semantic_outcome=ObservedSemanticOutcome.SUCCESS,
            validation_outcome=ObservedValidationOutcome.NOT_RUN,
        )


def test_observed_failure_rejects_fabricated_admissible_facts() -> None:
    with pytest.raises(ValidationError):
        ObservedEvaluationResult(
            case_id="TEST_CASE_001",
            run_id="TEST_RUN_001",
            provenance=provenance(),
            semantic_outcome=ObservedSemanticOutcome.FAILURE,
            validation_outcome=ObservedValidationOutcome.FAILED,
            validation_failure_stage=ValidationFailureStage.DOMAIN,
            semantic_facts=semantic_facts(),
            failure_provenance=PipelineFailureProvenance.DOMAIN_VALIDATION,
        )


def test_observed_provider_failure_requires_provenance_and_no_facts() -> None:
    result = ObservedEvaluationResult(
        case_id="TEST_CASE_001",
        run_id="TEST_RUN_001",
        provenance=provenance(),
        semantic_outcome=ObservedSemanticOutcome.FAILURE,
        validation_outcome=ObservedValidationOutcome.NOT_RUN,
        failure_provenance=PipelineFailureProvenance.PROVIDER_REQUEST,
    )

    assert result.semantic_facts is None
    assert result.compatibility_finding is None


def test_match_rejects_material_differences() -> None:
    with pytest.raises(ValidationError):
        CaseEvaluationResult(
            result_id="RESULT_001",
            case_id="TEST_CASE_001",
            observed_run_id="TEST_RUN_001",
            status=CaseEvaluationStatus.MATCH,
            field_differences=[material_difference()],
        )


def test_match_accepts_only_non_material_differences() -> None:
    result = CaseEvaluationResult(
        result_id="RESULT_001",
        case_id="TEST_CASE_001",
        observed_run_id="TEST_RUN_001",
        status=CaseEvaluationStatus.MATCH,
        field_differences=[
            FieldDifference(
                field="semantic_facts.event_type",
                expected_value="verbal_threat",
                observed_value="verbal_threat",
                classification=DifferenceClassification.MATCH,
                reason_code=DifferenceReasonCode.VALUES_EQUAL,
            )
        ],
    )

    assert result.status == CaseEvaluationStatus.MATCH


def test_partial_mismatch_requires_material_difference() -> None:
    with pytest.raises(ValidationError):
        CaseEvaluationResult(
            result_id="RESULT_001",
            case_id="TEST_CASE_001",
            observed_run_id="TEST_RUN_001",
            status=CaseEvaluationStatus.PARTIAL_MISMATCH,
            field_differences=[],
        )


def test_failure_requires_ordered_failure_pattern() -> None:
    result = CaseEvaluationResult(
        result_id="RESULT_001",
        case_id="TEST_CASE_001",
        observed_run_id="TEST_RUN_001",
        status=CaseEvaluationStatus.FAILURE,
        failure_patterns=[FailurePattern.PROVIDER_FAILURE, FailurePattern.MISSING_OBSERVATION],
    )

    assert result.failure_patterns == [
        FailurePattern.PROVIDER_FAILURE,
        FailurePattern.MISSING_OBSERVATION,
    ]


def test_non_comparable_requires_explicit_provenance() -> None:
    with pytest.raises(ValidationError):
        CaseEvaluationResult(
            result_id="RESULT_001",
            case_id="TEST_CASE_001",
            observed_run_id="TEST_RUN_001",
            status=CaseEvaluationStatus.NON_COMPARABLE,
        )

    result = CaseEvaluationResult(
        result_id="RESULT_001",
        case_id="TEST_CASE_001",
        observed_run_id="TEST_RUN_001",
        status=CaseEvaluationStatus.NON_COMPARABLE,
        non_comparable_reason=NonComparableReason.OBSERVATION_FAILED,
    )
    assert result.non_comparable_reason == NonComparableReason.OBSERVATION_FAILED


@pytest.mark.parametrize("classification", list(BaselineClassification))
def test_baseline_classification_constructs_with_both_identities(
    classification: BaselineClassification,
) -> None:
    comparison = BaselineComparison(
        comparison_id=f"BASELINE_{classification.value}",
        prior_result_id="RESULT_PRIOR",
        current_result_id="RESULT_CURRENT",
        classification=classification,
        observations=[
            BaselineComparisonObservation(
                code=BaselineObservationCode.CASE_STATUS_UNCHANGED,
                detail="Contract-only observation.",
            )
        ],
    )

    assert comparison.prior_result_id == "RESULT_PRIOR"
    assert comparison.current_result_id == "RESULT_CURRENT"


def test_baseline_classification_rejects_missing_result_identity() -> None:
    with pytest.raises(ValidationError):
        BaselineComparison(
            comparison_id="BASELINE_001",
            prior_result_id=" ",
            current_result_id="RESULT_CURRENT",
            classification=BaselineClassification.INCOMPARABLE,
            observations=[
                BaselineComparisonObservation(
                    code=BaselineObservationCode.PROVENANCE_INCOMPATIBLE,
                    detail="Repository commits cannot be compared.",
                )
            ],
        )


def test_ordered_collections_preserve_caller_order() -> None:
    result = CaseEvaluationResult(
        result_id="RESULT_001",
        case_id="TEST_CASE_001",
        observed_run_id="TEST_RUN_001",
        status=CaseEvaluationStatus.PARTIAL_MISMATCH,
        field_differences=[material_difference("z_field"), material_difference("a_field")],
    )

    assert [item.field for item in result.field_differences] == ["z_field", "a_field"]
    serialized = canonical_json(result)
    assert serialized.index("z_field") < serialized.index("a_field")


def test_field_difference_rejects_non_json_artifact_values() -> None:
    with pytest.raises(ValidationError):
        FieldDifference(
            field="semantic_facts.event_type",
            expected_value=object(),
            observed_value="verbal_threat",
            classification=DifferenceClassification.VALUE_MISMATCH,
            reason_code=DifferenceReasonCode.VALUES_DIFFER,
        )


def test_metadata_ground_truth_and_narrative_are_structurally_separate() -> None:
    payload = evaluation_case().model_dump(mode="json")

    assert set(payload) == {
        "case_id",
        "schema_version",
        "synthetic",
        "narrative",
        "metadata",
        "ground_truth",
    }
    assert "narrative" not in payload["metadata"]
    assert "narrative" not in payload["ground_truth"]
    assert "engineering_notes" not in payload["ground_truth"]


def test_contract_construction_makes_no_provider_call(monkeypatch: pytest.MonkeyPatch) -> None:
    import openai

    def fail_provider_construction(*args: object, **kwargs: object) -> None:
        raise AssertionError("evaluation contracts must not construct a provider client")

    monkeypatch.setattr(openai, "OpenAI", fail_provider_construction)

    assert evaluation_case().case_id == "TEST_CASE_001"
    assert observed_success().semantic_outcome == ObservedSemanticOutcome.SUCCESS
