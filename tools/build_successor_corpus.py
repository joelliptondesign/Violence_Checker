"""Serialize manually authored successor ground truth without observed-output inputs.

The source corpus is read only for stable case identifiers, narrative bytes,
synthetic designation, and authored metadata. `_SPECS` is the independent
proposition-oriented semantic and policy authority.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.contracts import (
    AssertionStatus,
    Attribution,
    AttributionSourceKind,
    Completion,
    ConductKind,
    Contact,
    EntityKind,
    EntityReference,
    EvidenceExcerpt,
    EvidenceSubjectKind,
    EvidenceSupport,
    EvidenceSupportRole,
    ExtractionMetadata,
    PolicyOutcome,
    PropositionTarget,
    RelationshipKind,
    SEMANTIC_SCHEMA_IDENTITY,
    SEMANTIC_SCHEMA_VERSION,
    SemanticIntentionality,
    SemanticRelationship,
    SemanticUncertainty,
    TargetKind,
    TemporalScope,
    UncertaintyDimension,
    ViolenceProposition,
    ViolenceSemanticEnvelope,
)
from src.evaluation.contracts import ExpectedEvaluationOutcome, ExpectedSemanticOutcome
from src.evaluation.corpus import (
    CORPUS_IDENTITY,
    CORPUS_SCHEMA_VERSION,
    CORPUS_VERSION,
    EVALUATION_SCHEMA_VERSION,
    LEGACY_CORPUS_PATH,
)
from src.policy import evaluate_policy
from src.semantic_validation import validate_semantic_candidate


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evaluation" / "corpus" / "successor_corpus.json"


def p(actor, target, conduct, completion, contact, time, intent, status="affirmed", *, uncertainties=(), attribution=None):
    return {
        "actor": actor,
        "target": target,
        "conduct": conduct,
        "completion": completion,
        "contact": contact,
        "time": time,
        "intent": intent,
        "status": status,
        "uncertainties": list(uncertainties),
        "attribution": attribution,
    }


PATIENT = ("patient", "person")
UNSPECIFIED_ACTOR = ("unspecified actor", "unspecified")
CURRENT = "current_incident"
HISTORICAL = "historical"


_SPECS = {
    "EVAL_001": ([p(PATIENT, ("entity", "nurse", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_DETECTED"),
    "EVAL_002": ([p(PATIENT, ("entity", "technician", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_DETECTED"),
    "EVAL_003": ([p(PATIENT, ("entity", "nurse", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_DETECTED"),
    "EVAL_004": ([p(PATIENT, ("entity", "aide", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_DETECTED"),
    "EVAL_005": ([p(PATIENT, ("entity", "nurse", "person"), "physical_conduct", "attempted", "did_not_occur", CURRENT, "intentional")], [], "WRITE_DETECTED"),
    "EVAL_006": ([p(PATIENT, ("entity", "technician", "person"), "physical_conduct", "attempted", "did_not_occur", CURRENT, "intentional")], [], "WRITE_DETECTED"),
    "EVAL_007": ([
        p(PATIENT, ("entity", "unspecified person", "unspecified"), "physical_conduct", "completed", "occurred", HISTORICAL, "intentional"),
        p(PATIENT, ("entity", "anyone", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated"),
        p(PATIENT, ("entity", "nurse", "person"), "physical_conduct", "attempted", "did_not_occur", CURRENT, "intentional"),
    ], [], "WRITE_DETECTED"),
    "EVAL_008": ([p(PATIENT, ("entity", "staff", "people_collective"), "physical_conduct", "attempted", "did_not_occur", CURRENT, "intentional")], [], "WRITE_DETECTED"),
    "EVAL_009": ([p(PATIENT, ("entity", "nurse", "person"), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional")], [], "WRITE_DETECTED"),
    "EVAL_010": ([p(PATIENT, ("entity", "somebody", "unspecified"), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional", uncertainties=("target_identity", "direction"))], [], "WRITE_UNCERTAIN"),
    "EVAL_011": ([
        p(PATIENT, ("entity", "aide", "person"), "contact_only", "completed", "occurred", CURRENT, "accidental"),
        p(PATIENT, ("entity", "aide", "person"), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional"),
    ], [], "WRITE_DETECTED"),
    "EVAL_012": ([p(UNSPECIFIED_ACTOR, ("undetermined",), "undetermined", "undetermined", "undetermined", CURRENT, "undetermined", "uncertain", uncertainties=("actor_identity", "target_identity", "conduct_type", "direction", "contact", "completion", "intentionality", "threat_meaning", "assertion_status"), attribution=("witness", None))], [], "WRITE_UNCERTAIN"),
    "EVAL_013": ([p(PATIENT, ("entity", "nurse", "person"), "contact_only", "completed", "occurred", CURRENT, "accidental")], [], "WRITE_NOT_DETECTED"),
    "EVAL_014": ([p(PATIENT, ("entity", "aide", "person"), "contact_only", "completed", "occurred", CURRENT, "accidental")], [], "WRITE_NOT_DETECTED"),
    "EVAL_015": ([p(PATIENT, ("entity", "technician", "person"), "contact_only", "completed", "occurred", CURRENT, "accidental")], [], "WRITE_NOT_DETECTED"),
    "EVAL_016": ([p(PATIENT, ("entity", "staff member", "person"), "contact_only", "completed", "occurred", CURRENT, "accidental")], [], "WRITE_NOT_DETECTED"),
    "EVAL_017": ([p(("roommate", "person"), ("entity", "patient", "person"), "physical_conduct", "completed", "occurred", HISTORICAL, "intentional")], [], "WRITE_NOT_DETECTED"),
    "EVAL_018": ([p(("former caregiver", "person"), ("entity", "patient", "person"), "physical_conduct", "completed", "occurred", HISTORICAL, "intentional"), p(PATIENT, ("entity", "anyone", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated")], [], "WRITE_NOT_DETECTED"),
    "EVAL_019": ([p(("stranger", "person"), ("entity", "patient", "person"), "physical_conduct", "completed", "occurred", HISTORICAL, "intentional")], [], "WRITE_NOT_DETECTED"),
    "EVAL_020": ([
        p(UNSPECIFIED_ACTOR, ("entity", "patient", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional"),
        p(UNSPECIFIED_ACTOR, ("entity", "patient", "person"), "physical_conduct", "completed", "occurred", HISTORICAL, "intentional"),
        p(UNSPECIFIED_ACTOR, ("entity", "anyone", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated"),
    ], [("supersedes", 2, 1, ())], "WRITE_NOT_DETECTED"),
    "EVAL_021": ([p(PATIENT, ("entity", "anyone", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated"), p(PATIENT, ("entity", "anyone", "people_collective"), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional", "negated")], [], "WRITE_NOT_DETECTED"),
    "EVAL_022": ([p(UNSPECIFIED_ACTOR, ("entity", "patient", "person"), "physical_conduct", "completed", "occurred", HISTORICAL, "intentional"), p(PATIENT, ("entity", "anyone", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated"), p(PATIENT, ("entity", "anyone", "people_collective"), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional", "negated")], [], "WRITE_NOT_DETECTED"),
    "EVAL_023": ([p(PATIENT, ("none",), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional", "negated")], [], "WRITE_NOT_DETECTED"),
    "EVAL_024": ([p(PATIENT, ("entity", "aide", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated", attribution=("staff", "aide"))], [], "WRITE_NOT_DETECTED"),
    "EVAL_025": ([p(PATIENT, ("entity", "nurse", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional"), p(PATIENT, ("entity", "mattress", "object"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [("supersedes", 2, 1, ())], "WRITE_NOT_DETECTED"),
    "EVAL_026": ([p(PATIENT, ("entity", "staff", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional"), p(PATIENT, ("entity", "cart", "object"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [("supersedes", 2, 1, ())], "WRITE_NOT_DETECTED"),
    "EVAL_027": ([p(PATIENT, ("entity", "nurse", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional"), p(("glove", "object"), ("entity", "nurse", "person"), "contact_only", "completed", "occurred", CURRENT, "accidental")], [("supersedes", 2, 1, ())], "WRITE_NOT_DETECTED"),
    "EVAL_028": ([p(PATIENT, ("entity", "technician", "person"), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional"), p(PATIENT, ("entity", "technician", "person"), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional", "negated")], [("supersedes", 2, 1, ())], "WRITE_NOT_DETECTED"),
    "EVAL_029": ([p(PATIENT, ("entity", "aide", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", attribution=("witness", "witness one")), p(PATIENT, ("entity", "aide", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated", attribution=("witness", "witness two"))], [("conflicts_with", 1, 2, ("contact", "assertion_status"))], "WRITE_UNCERTAIN"),
    "EVAL_030": ([p(PATIENT, ("entity", "staff", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated", attribution=("patient", "patient")), p(PATIENT, ("entity", "staff", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", attribution=("staff", "staff"))], [("conflicts_with", 1, 2, ("assertion_status",))], "WRITE_UNCERTAIN"),
    "EVAL_031": ([p(PATIENT, ("entity", "technician", "person"), "physical_conduct", "attempted", "did_not_occur", CURRENT, "undetermined", attribution=("staff", "technician"), uncertainties=("intentionality",)), p(PATIENT, ("entity", "technician", "person"), "contact_only", "completed", "occurred", CURRENT, "undetermined", "uncertain", attribution=("staff", "nurse"), uncertainties=("intentionality", "assertion_status"))], [("conflicts_with", 1, 2, ("conduct_type", "completion", "contact", "intentionality", "assertion_status"))], "WRITE_UNCERTAIN"),
    "EVAL_032": ([p(PATIENT, ("entity", "nurse", "person"), "contact_only", "completed", "occurred", CURRENT, "accidental", attribution=("patient", "patient")), p(PATIENT, ("entity", "nurse", "person"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", attribution=("staff", "nurse"))], [("conflicts_with", 1, 2, ("conduct_type", "intentionality"))], "WRITE_UNCERTAIN"),
    "EVAL_033": ([p(PATIENT, ("entity", "wall", "object"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_NOT_DETECTED"),
    "EVAL_034": ([p(UNSPECIFIED_ACTOR, ("entity", "unspecified person", "unspecified"), "physical_conduct", "completed", "occurred", HISTORICAL, "intentional"), p(PATIENT, ("entity", "anyone", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated"), p(PATIENT, ("entity", "trash can", "object"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_NOT_DETECTED"),
    "EVAL_035": ([p(PATIENT, ("entity", "floor", "object"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_NOT_DETECTED"),
    "EVAL_036": ([p(PATIENT, ("entity", "paper sign", "object"), "physical_conduct", "completed", "occurred", CURRENT, "intentional"), p(PATIENT, ("entity", "empty chair", "object"), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_NOT_DETECTED"),
    "EVAL_037": ([p(PATIENT, ("self",), "physical_conduct", "completed", "occurred", CURRENT, "intentional")], [], "WRITE_NOT_DETECTED"),
    "EVAL_038": ([p(PATIENT, ("self",), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional"), p(PATIENT, ("entity", "staff", "people_collective"), "physical_conduct", "completed", "occurred", CURRENT, "intentional", "negated")], [], "WRITE_NOT_DETECTED"),
    "EVAL_039": ([p(PATIENT, ("self",), "physical_conduct", "completed", "occurred", CURRENT, "intentional"), p(PATIENT, ("entity", "staff", "people_collective"), "physical_conduct", "attempted", "did_not_occur", CURRENT, "intentional", "negated")], [], "WRITE_NOT_DETECTED"),
    "EVAL_040": ([p(PATIENT, ("self",), "physical_conduct", "completed", "occurred", CURRENT, "intentional"), p(PATIENT, ("entity", "others", "people_collective"), "threat_expression", "threatened", "not_applicable", CURRENT, "intentional", "negated")], [], "WRITE_NOT_DETECTED"),
    "EVAL_041": ([p(PATIENT, ("entity", "nurse", "person"), "undetermined", "undetermined", "undetermined", CURRENT, "undetermined", "uncertain", uncertainties=("conduct_type", "contact", "completion", "intentionality", "assertion_status"))], [], "WRITE_UNCERTAIN"),
    "EVAL_042": ([p(PATIENT, ("entity", "technician", "person"), "threatening_movement", "undetermined", "did_not_occur", CURRENT, "undetermined", "uncertain", uncertainties=("completion", "intentionality", "threat_meaning", "assertion_status"))], [], "WRITE_UNCERTAIN"),
    "EVAL_043": ([p(UNSPECIFIED_ACTOR, ("undetermined",), "physical_conduct", "completed", "occurred", CURRENT, "undetermined", "uncertain", uncertainties=("actor_identity", "target_identity", "direction", "intentionality", "assertion_status"))], [], "WRITE_UNCERTAIN"),
    "EVAL_044": ([p(PATIENT, ("entity", "nurse", "person"), "contact_only", "completed", "occurred", CURRENT, "undetermined", "uncertain", uncertainties=("intentionality", "assertion_status"))], [], "WRITE_UNCERTAIN"),
    "EVAL_045": ([p(PATIENT, ("entity", "staff", "people_collective"), "undetermined", "undetermined", "undetermined", CURRENT, "undetermined", "uncertain", uncertainties=("conduct_type", "contact", "completion", "intentionality", "assertion_status"))], [], "WRITE_UNCERTAIN"),
    "EVAL_046": ([p(UNSPECIFIED_ACTOR, ("undetermined",), "physical_conduct", "undetermined", "undetermined", CURRENT, "undetermined", "uncertain", uncertainties=("actor_identity", "target_identity", "direction", "contact", "completion", "intentionality", "assertion_status"))], [], "WRITE_UNCERTAIN"),
    "EVAL_047": ([p(UNSPECIFIED_ACTOR, ("entity", "nurse", "person"), "contact_only", "completed", "occurred", CURRENT, "undetermined", "uncertain", uncertainties=("actor_identity", "intentionality", "assertion_status"), attribution=("staff", "nurse"))], [], "WRITE_UNCERTAIN"),
    "EVAL_048": ([p(PATIENT, ("undetermined",), "threat_expression", "threatened", "not_applicable", "undetermined", "undetermined", "uncertain", uncertainties=("target_identity", "direction", "intentionality", "temporal_scope", "threat_meaning", "assertion_status"), attribution=("witness", None))], [], "WRITE_UNCERTAIN"),
}


def _enum(enum_type, value):
    return enum_type(value)


def _build_envelope(case_id: str, narrative: str, spec):
    proposition_specs, relationship_specs, expected_outcome = spec
    entity_defs = []

    def add_entity(definition):
        if definition is None:
            return None
        label, kind = definition
        for index, existing in enumerate(entity_defs, start=1):
            if existing == definition:
                return f"ENT-{index:04d}"
        entity_defs.append(definition)
        return f"ENT-{len(entity_defs):04d}"

    propositions = []
    uncertainty_specs = []
    for index, item in enumerate(proposition_specs, start=1):
        attribution = None
        if item["attribution"] is not None:
            source_kind, source_label = item["attribution"]
            source_ref = add_entity((source_label, "person")) if source_label else None
            attribution = Attribution(source_kind=AttributionSourceKind(source_kind), source_ref=source_ref)
        actor_ref = add_entity(item["actor"])
        target_spec = item["target"]
        target_kind = TargetKind(target_spec[0])
        target_ref = add_entity((target_spec[1], target_spec[2])) if target_kind == TargetKind.ENTITY else None
        proposition_id = f"PROP-{index:04d}"
        propositions.append(
            ViolenceProposition(
                proposition_id=proposition_id,
                actor_ref=actor_ref,
                conduct_kind=ConductKind(item["conduct"]),
                target=PropositionTarget(target_kind=target_kind, target_ref=target_ref),
                completion=Completion(item["completion"]),
                contact=Contact(item["contact"]),
                temporal_scope=TemporalScope(item["time"]),
                intentionality=SemanticIntentionality(item["intent"]),
                assertion_status=AssertionStatus(item["status"]),
                attribution=attribution,
            )
        )
        for dimension in item["uncertainties"]:
            uncertainty_specs.append((proposition_id, dimension))

    entities = [
        EntityReference(entity_id=f"ENT-{index:04d}", entity_kind=EntityKind(kind), label=label)
        for index, (label, kind) in enumerate(entity_defs, start=1)
    ]
    relationships = [
        SemanticRelationship(
            relationship_id=f"REL-{index:04d}",
            relationship_kind=RelationshipKind(kind),
            source_proposition_ref=f"PROP-{source:04d}",
            target_proposition_ref=f"PROP-{target:04d}",
            disputed_dimensions=[UncertaintyDimension(value) for value in dimensions],
        )
        for index, (kind, source, target, dimensions) in enumerate(relationship_specs, start=1)
    ]
    uncertainties = [
        SemanticUncertainty(
            uncertainty_id=f"UNC-{index:04d}",
            proposition_ref=proposition_ref,
            dimension=UncertaintyDimension(dimension),
        )
        for index, (proposition_ref, dimension) in enumerate(uncertainty_specs, start=1)
    ]
    evidence = [EvidenceExcerpt(evidence_id="EVID-0001", text=narrative)]
    supports = []

    def support(subject_kind, subject_ref, role):
        supports.append(
            EvidenceSupport(
                support_id=f"SUP-{len(supports) + 1:04d}",
                evidence_ref="EVID-0001",
                subject_kind=subject_kind,
                subject_ref=subject_ref,
                role=role,
            )
        )

    for proposition in propositions:
        role = EvidenceSupportRole.SUPPORTS_NEGATION if proposition.assertion_status == AssertionStatus.NEGATED else EvidenceSupportRole.SUPPORTS_ASSERTION
        support(EvidenceSubjectKind.PROPOSITION, proposition.proposition_id, role)
    for relationship in relationships:
        role = {
            RelationshipKind.NEGATES: EvidenceSupportRole.SUPPORTS_NEGATION,
            RelationshipKind.SUPERSEDES: EvidenceSupportRole.SUPPORTS_SUPERSESSION,
            RelationshipKind.CONFLICTS_WITH: EvidenceSupportRole.SUPPORTS_CONFLICT,
        }[relationship.relationship_kind]
        support(EvidenceSubjectKind.RELATIONSHIP, relationship.relationship_id, role)
    for uncertainty in uncertainties:
        support(EvidenceSubjectKind.UNCERTAINTY, uncertainty.uncertainty_id, EvidenceSupportRole.SUPPORTS_UNCERTAINTY)

    envelope = ViolenceSemanticEnvelope(
        schema_identity=SEMANTIC_SCHEMA_IDENTITY,
        schema_version=SEMANTIC_SCHEMA_VERSION,
        incident_id=case_id,
        entities=entities,
        propositions=propositions,
        relationships=relationships,
        uncertainties=uncertainties,
        evidence_excerpts=evidence,
        evidence_supports=supports,
        extraction_metadata=ExtractionMetadata(extraction_contract_identity="violence-checker.proposition-extraction@1.0.0"),
    )
    validation = validate_semantic_candidate(envelope, incident_id=case_id, normalized_narrative=narrative)
    if not validation.passed or validation.validated_envelope is None:
        raise ValueError(f"invalid manually authored case {case_id}: {validation.model_dump(mode='json')}")
    decision = evaluate_policy(validated=validation.validated_envelope)
    if decision.outcome != PolicyOutcome(expected_outcome):
        raise ValueError(f"policy expectation mismatch for {case_id}: {decision.outcome.value} != {expected_outcome}")
    ground_truth = ExpectedEvaluationOutcome(
        semantic_outcome=ExpectedSemanticOutcome.SUCCESS,
        semantic_envelope=envelope,
        expected_derived=validation.validated_envelope.derived,
        policy_decision=decision,
    )
    return ground_truth.model_dump(mode="json")


def build_document():
    legacy = json.loads(LEGACY_CORPUS_PATH.read_text(encoding="utf-8"))
    cases = []
    for source in legacy["cases"]:
        case_id = source["case_id"]
        if case_id not in _SPECS:
            raise ValueError(f"missing manually authored successor ground truth for {case_id}")
        cases.append(
            {
                "case_id": case_id,
                "schema_version": EVALUATION_SCHEMA_VERSION,
                "synthetic": source["synthetic"],
                "narrative": source["narrative"],
                "metadata": source["metadata"],
                "ground_truth": _build_envelope(case_id, source["narrative"], _SPECS[case_id]),
            }
        )
    if len(cases) != 48 or set(_SPECS) != {item["case_id"] for item in cases}:
        raise ValueError("successor corpus requires exactly the 48 stable authored cases")
    return {
        "corpus_identity": CORPUS_IDENTITY,
        "corpus_version": CORPUS_VERSION,
        "corpus_schema_version": CORPUS_SCHEMA_VERSION,
        "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
        "semantic_schema_identity": SEMANTIC_SCHEMA_IDENTITY,
        "semantic_schema_version": SEMANTIC_SCHEMA_VERSION,
        "cases": cases,
    }


def main() -> int:
    OUTPUT.write_text(
        json.dumps(build_document(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
