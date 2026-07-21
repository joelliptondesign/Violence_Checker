from src.app_logic import run_analysis
from src.contracts import Intentionality
from src.models import Incident
from src.presentation import (
    operational_fact_rows, policy_outcome_label, policy_reason_explanations,
    salesforce_operator_rows, salesforce_payload_rows, semantic_summary,
    validated_evidence_excerpts,
)
from tests.test_app_logic import candidate_for, extraction_for


def analysis(narrative="Patient intentionally struck the nurse today.", **updates):
    return run_analysis(Incident(incident_id="CASE_001", narrative=narrative), extractor=extraction_for(candidate_for(narrative, **updates)))


def test_operational_fact_rows_and_evidence_are_identifier_free():
    result = analysis()
    rows = operational_fact_rows(result.validation_result)
    assert rows == [{
        "Conduct": "Physical Contact", "Direction": "Interpersonal",
        "Intent": "Intentional", "Timing": "Current",
        "Assertion": "Affirmed", "Resolution": "Active",
    }]
    assert "FACT-" not in str(rows)
    assert validated_evidence_excerpts(result.validation_result) == (result.normalized_incident.normalized_narrative,)


def test_policy_copy_and_semantic_summary_use_true_north_outcomes():
    result = analysis()
    assert policy_outcome_label(result.policy_decision) == "Violence Detected"
    assert policy_reason_explanations(result.policy_decision)
    assert "qualifying conduct" in semantic_summary(result.validation_result, result.policy_decision)
    accidental = analysis("Patient accidentally contacted the nurse today.", intentionality=Intentionality.ACCIDENTAL)
    assert "accidental" in semantic_summary(accidental.validation_result, accidental.policy_decision)


def test_salesforce_rows_preserve_payload_order_and_readable_values():
    payload = analysis().salesforce_preview
    rows = salesforce_operator_rows(payload)
    assert rows[0] == {"Field": "Incident Identifier", "Value": "CASE_001"}
    assert any(row["Field"] == "Deterministic Outcome" for row in rows)
    detailed = salesforce_payload_rows(payload)
    assert [row["Field"] for row in detailed] == list(payload)
    assert all("proposition" not in row["Field"].lower() for row in detailed)
