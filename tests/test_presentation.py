from src.contracts import (
    PipelineFailureProvenance,
    PolicyOutcome,
    PolicyReasonCode,
    SemanticFacts,
    ValidationFailureStage,
)
from src.models import Intentionality, ViolenceEventType
from src.policy import failed_policy_decision
from src.presentation import (
    POLICY_EXPLANATIONS,
    POLICY_OUTCOME_LABELS,
    POLICY_REASON_EXPLANATIONS,
    VALIDATION_SUMMARIES,
    policy_explanation,
    policy_outcome_label,
    policy_reason_explanations,
    semantic_summary,
    validation_summary,
)
from src.semantic_validation import validate_semantic_candidate, validation_not_run


def test_every_policy_outcome_has_a_stakeholder_label_and_explanation():
    assert set(POLICY_OUTCOME_LABELS) == set(PolicyOutcome)
    assert set(POLICY_EXPLANATIONS) == set(PolicyOutcome)
    assert POLICY_OUTCOME_LABELS == {
        PolicyOutcome.WRITE_DETECTED: "Violence Detected",
        PolicyOutcome.WRITE_UNCERTAIN: "Uncertain",
        PolicyOutcome.WRITE_NOT_DETECTED: "No Violence Detected",
        PolicyOutcome.WRITE_FAILED: "Unable to Determine",
    }


def test_every_internal_reason_code_has_a_human_readable_explanation():
    assert set(POLICY_REASON_EXPLANATIONS) == set(PolicyReasonCode)
    assert all("_" not in explanation for explanation in POLICY_REASON_EXPLANATIONS.values())


def test_policy_presentation_is_deterministic_and_does_not_change_contract():
    decision = failed_policy_decision(PipelineFailureProvenance.DOMAIN_VALIDATION)

    assert policy_outcome_label(decision) == policy_outcome_label(decision)
    assert policy_explanation(decision) == policy_explanation(decision)
    assert policy_reason_explanations(decision) == [
        "The extracted information contained an invalid combination of facts."
    ]
    assert decision.outcome == PolicyOutcome.WRITE_FAILED
    assert decision.reason_codes == [PolicyReasonCode.DOMAIN_VALIDATION_FAILED]


def semantic_values(**overrides):
    values = {
        "violence_present": False,
        "event_type": ViolenceEventType.NONE,
        "actor": None,
        "target": None,
        "contact_occurred": False,
        "injury_mentioned": False,
        "current_event": True,
        "intentionality": Intentionality.UNCLEAR,
        "negated": False,
        "correction_present": False,
        "conflicting_information": False,
        "evidence_text": ["No violence occurred."],
        "confidence": 0.8,
        "uncertainty_notes": [],
    }
    values.update(overrides)
    return values


def test_every_validation_stage_has_a_deterministic_summary():
    results = {
        ValidationFailureStage.NOT_RUN: validation_not_run(),
        ValidationFailureStage.NONE: validate_semantic_candidate(
            SemanticFacts(**semantic_values())
        ),
        ValidationFailureStage.SCHEMA: validate_semantic_candidate(
            {"violence_present": False}
        ),
        ValidationFailureStage.DOMAIN: validate_semantic_candidate(
            SemanticFacts(
                **semantic_values(
                    violence_present=True,
                    event_type=ViolenceEventType.NONE,
                )
            )
        ),
    }

    assert set(results) == set(ValidationFailureStage)
    for stage, result in results.items():
        assert result.failure_stage == stage
        assert validation_summary(result) == VALIDATION_SUMMARIES[stage]


def test_validation_summary_mapping_covers_every_stage():
    assert set(VALIDATION_SUMMARIES) == set(ValidationFailureStage)


def test_detected_semantic_summary_is_deterministic_and_human_readable():
    validation = validate_semantic_candidate(
        SemanticFacts(
            **semantic_values(
                violence_present=True,
                event_type=ViolenceEventType.COMPLETED_PHYSICAL_VIOLENCE,
                actor="pt",
                target="rn",
                contact_occurred=True,
                injury_mentioned=True,
                intentionality=Intentionality.INTENTIONAL,
                evidence_text=["pt hit rn"],
                uncertainty_notes=["Abbreviations are preserved."],
            )
        )
    )
    from src.compatibility_finding import construct_compatibility_finding
    from src.policy import evaluate_policy

    compatibility = construct_compatibility_finding(validation.validated_facts)
    decision = evaluate_policy(
        validated_facts=validation.validated_facts,
        finding=compatibility.finding,
    )

    assert semantic_summary(validation.validated_facts, decision) == (
        "pt is described as responsible for completed physical violence involving rn. "
        "Physical contact occurred. An injury was documented."
    )
    assert "completed_physical_violence" not in semantic_summary(
        validation.validated_facts, decision
    )


def test_failed_semantic_summary_is_safe_without_validated_facts():
    decision = failed_policy_decision(PipelineFailureProvenance.PROVIDER_REQUEST)

    assert semantic_summary(None, decision) == (
        "Semantic analysis was unable to produce validated facts."
    )
