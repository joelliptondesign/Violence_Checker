from src.contracts import (
    AssertionStatus,
    Completion,
    Contact,
    PipelineFailureProvenance,
    PolicyOutcome,
    SemanticIntentionality,
    TemporalScope,
    UncertaintyDimension,
)
from src.policy import evaluate_policy, failed_policy_decision
from src.presentation import (
    comparison_presentation,
    extracted_entity_rows,
    humanize_entity_category,
    humanize_entity_role,
    policy_outcome_label,
    policy_reason_explanations,
    salesforce_operator_rows,
    salesforce_payload_rows,
    semantic_summary,
    validated_evidence_excerpts,
)
from src.semantic_validation import validate_semantic_candidate
from tests.successor_helpers import envelope


def validated():
    result = validate_semantic_candidate(envelope(), incident_id="CASE_001", normalized_narrative="Patient struck the nurse.")
    return result.validated_envelope


def validation_result():
    return validate_semantic_candidate(
        envelope(),
        incident_id="CASE_001",
        normalized_narrative="Patient struck the nurse.",
    )


def test_presentation_maps_every_policy_outcome_without_inference():
    assert {outcome for outcome in PolicyOutcome} == set(__import__("src.presentation", fromlist=["POLICY_OUTCOME_LABELS"]).POLICY_OUTCOME_LABELS)


def test_successor_summary_uses_typed_derived_counts():
    value = validated()
    decision = evaluate_policy(validated=value)
    assert semantic_summary(value, decision) == "The narrative describes completed physical violence involving contact."


def test_failed_summary_and_reason_are_safe():
    decision = failed_policy_decision(PipelineFailureProvenance.PROVIDER_REQUEST)
    assert policy_outcome_label(decision) == "Analysis Failed"
    assert policy_reason_explanations(decision)
    assert "could not" in semantic_summary(None, decision).lower()


def test_stakeholder_language_is_plain_for_every_outcome():
    prohibited = {
        "proposition", "semantic envelope", "bounded uncertainty", "scoped semantic",
        "deterministic policy", "active-set", "schema-admissible", "provider validation",
    }
    detected_value = validated()
    uncertain_result = validate_semantic_candidate(
        envelope(
            completion=Completion.UNDETERMINED,
            contact=Contact.UNDETERMINED,
            uncertainty_dimension=UncertaintyDimension.CONTACT,
        ),
        incident_id="CASE_001",
        normalized_narrative="Patient may have struck the nurse.",
    ).validated_envelope
    values = [
        (detected_value, evaluate_policy(validated=detected_value)),
        (uncertain_result, evaluate_policy(validated=uncertain_result)),
        (None, failed_policy_decision(PipelineFailureProvenance.PROVIDER_REQUEST)),
    ]
    for value, decision in values:
        rendered = " ".join([
            policy_outcome_label(decision),
            semantic_summary(value, decision),
            *policy_reason_explanations(decision),
        ]).lower()
        assert not any(term in rendered for term in prohibited)


def test_accidental_and_historical_summaries_remain_distinct():
    accidental_narrative = "Patient bumped the nurse by accident."
    accidental = validate_semantic_candidate(
        envelope(narrative=accidental_narrative, intentionality=SemanticIntentionality.ACCIDENTAL),
        incident_id="CASE_001",
        normalized_narrative=accidental_narrative,
    ).validated_envelope
    historical_narrative = "Patient struck a nurse years ago."
    historical = validate_semantic_candidate(
        envelope(narrative=historical_narrative, temporal_scope=TemporalScope.HISTORICAL),
        incident_id="CASE_001",
        normalized_narrative=historical_narrative,
    ).validated_envelope
    assert "accidental contact" in semantic_summary(accidental, evaluate_policy(validated=accidental))
    assert "past event" in semantic_summary(historical, evaluate_policy(validated=historical))


def test_comparison_presentation_uses_plain_operational_language():
    value = comparison_presentation(
        "regex_positive_semantic_negative",
        ["Semantic extraction preserves historical conduct as proposition-scoped context."],
    )
    rendered = " ".join(value.__dict__.values()).lower()
    assert "keyword detector" in rendered
    assert "ai analysis" in rendered
    assert "historical conduct" in rendered
    assert "false alerts" in rendered
    assert not any(
        term in rendered
        for term in ("classification divergence", "deterministic policy", "validated propositions", "semantic enrichment")
    )


def test_entity_inspection_rows_are_readable_ordered_and_identifier_free():
    rows = extracted_entity_rows(validation_result())
    assert rows == [
        {"Role": "Patient", "Category": "Patient"},
        {"Role": "Nurse", "Category": "Clinical Staff"},
    ]
    assert all(set(row) == {"Role", "Category"} for row in rows)
    assert "ENT-" not in str(rows)
    assert humanize_entity_role("registered_nurse", "person") == "Registered Nurse"
    assert humanize_entity_category("security", "person") == "Security Staff"


def test_validated_evidence_is_deduplicated_in_source_order():
    result = validation_result()
    validated_value = result.validated_envelope
    first = validated_value.envelope.evidence_excerpts[0]
    duplicate = first.model_copy(update={"evidence_id": "EVIDENCE-OTHER"})
    duplicate_envelope = validated_value.envelope.model_copy(
        update={"evidence_excerpts": [first, duplicate]}
    )
    duplicate_validated = validated_value.model_copy(update={"envelope": duplicate_envelope})
    projected = result.model_copy(update={"validated_envelope": duplicate_validated})
    assert validated_evidence_excerpts(projected) == (first.text,)


def test_failed_validation_has_no_entities_or_evidence_for_inspection():
    failed = validation_result().model_copy(update={"validated_envelope": None})
    assert extracted_entity_rows(failed) == []
    assert validated_evidence_excerpts(failed) == ()


def test_salesforce_rows_preserve_payload_order_and_values_with_readable_operator_labels():
    payload = {
        "Illustrative_Incident_Identifier__c": "CASE_001",
        "Illustrative_Semantic_Schema__c": "schema@1",
        "Illustrative_Active_Propositions__c": ["PROP-0001", "PROP-0002"],
        "Illustrative_Interpersonal_Propositions__c": ["PROP-0001"],
        "Illustrative_Evidence__c": ["First excerpt", "Second excerpt"],
        "Illustrative_Validation_Status__c": "success",
        "Illustrative_Write_Disposition__c": "WRITE_DETECTED",
    }
    assert salesforce_operator_rows(payload) == [
        {"Field": "Incident Identifier", "Value": "CASE_001"},
        {"Field": "Write Disposition", "Value": "WRITE_DETECTED"},
        {"Field": "Evidence", "Value": "First excerpt\nSecond excerpt"},
    ]
    rows = salesforce_payload_rows(payload)
    assert [row["Field"] for row in rows] == list(payload)
    assert rows[0]["Value"] == payload["Illustrative_Incident_Identifier__c"]
    assert rows[2]["Value"] == "\n".join(payload["Illustrative_Active_Propositions__c"])
    assert rows[4]["Value"] == "\n".join(payload["Illustrative_Evidence__c"])
    assert payload["Illustrative_Active_Propositions__c"] == ["PROP-0001", "PROP-0002"]
