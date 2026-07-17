import pytest

from src.models import Intentionality, ViolenceEventType, ViolenceFinding
from src.salesforce_preview import build_salesforce_preview, preview_field_names
from src.semantic_extractor import SemanticExtractionResult, SemanticExtractionStatus


def valid_finding():
    return ViolenceFinding(
        violence_present=True,
        event_type=ViolenceEventType.ATTEMPTED_PHYSICAL_VIOLENCE,
        actor="pt",
        target="rn",
        contact_occurred=False,
        injury_mentioned=False,
        current_event=True,
        intentionality=Intentionality.INTENTIONAL,
        negated=False,
        correction_present=False,
        conflicting_information=False,
        evidence_text=["pt swung at rn missed"],
        confidence=0.9,
        uncertainty_notes=["missed indicates no contact"],
    )


def success_result():
    return SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        finding=valid_finding(),
    )


def test_successful_validated_finding_produces_deterministic_dictionary():
    first = build_salesforce_preview("CASE_008", success_result())
    second = build_salesforce_preview("CASE_008", success_result())

    assert first == second
    assert first["Illustrative_Incident_Identifier__c"] == "CASE_008"


def test_expected_illustrative_fields_are_present():
    preview = build_salesforce_preview("CASE_008", success_result())

    assert list(preview.keys()) == preview_field_names()


def test_evidence_remains_unchanged():
    preview = build_salesforce_preview("CASE_008", success_result())

    assert preview["Illustrative_Evidence__c"] == ["pt swung at rn missed"]


def test_failure_results_do_not_produce_write_back_payloads():
    with pytest.raises(ValueError):
        build_salesforce_preview(
            "CASE_008",
            SemanticExtractionResult(status=SemanticExtractionStatus.VALIDATION_FAILURE),
        )


def test_invalid_objects_are_rejected():
    with pytest.raises(TypeError):
        build_salesforce_preview(
            "CASE_008",
            SemanticExtractionResult(status=SemanticExtractionStatus.SUCCESS, finding=None),
        )
