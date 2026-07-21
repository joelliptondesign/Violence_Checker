"""Minimal True North builders shared by active boundary tests."""

from src.contracts import (
    EXTRACTION_CONTRACT_IDENTITY, SEMANTIC_SCHEMA_IDENTITY, SEMANTIC_SCHEMA_VERSION,
    AssertionStatus, Conduct, FactDirection, FactEvidence, IncidentFact,
    Intentionality, MaterialAttribute, ResolutionStatus, TemporalScope,
    TrueNorthSemanticEnvelope,
)


SUPPORTS = [
    MaterialAttribute.CONDUCT,
    MaterialAttribute.DIRECTION,
    MaterialAttribute.INTENTIONALITY,
    MaterialAttribute.TEMPORAL_SCOPE,
    MaterialAttribute.ASSERTION_STATUS,
]


def envelope(narrative="Patient struck the nurse.", incident_id="CASE_001"):
    """Return one repository-shaped operational fact without legacy graph authority."""
    return TrueNorthSemanticEnvelope(
        schema_identity=SEMANTIC_SCHEMA_IDENTITY,
        schema_version=SEMANTIC_SCHEMA_VERSION,
        extraction_contract_identity=EXTRACTION_CONTRACT_IDENTITY,
        incident_id=incident_id,
        facts=[IncidentFact(
            fact_id="FACT-0001",
            conduct=Conduct.PHYSICAL_CONTACT,
            direction=FactDirection.INTERPERSONAL,
            intentionality=Intentionality.INTENTIONAL,
            temporal_scope=TemporalScope.CURRENT,
            assertion_status=AssertionStatus.AFFIRMED,
            resolution_status=ResolutionStatus.ACTIVE,
            evidence=[FactEvidence(
                evidence_id="EVID-0001",
                excerpt=narrative,
                supports=SUPPORTS,
                start_offset=0,
                end_offset=len(narrative),
            )],
            uncertainty=[],
        )],
    )
