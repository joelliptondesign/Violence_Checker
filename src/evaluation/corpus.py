"""Loading and deterministic validation for the True North operational corpus."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import StrictInt, StrictStr, ValidationError

from src.contracts import (
    EXTRACTION_CONTRACT_IDENTITY, SEMANTIC_SCHEMA_IDENTITY, SEMANTIC_SCHEMA_VERSION,
    AssertionStatus, CompletenessStatus, Conduct, FactEvidence, IncidentFact,
    Intentionality, PolicyOutcome, ProcessingStatus, ResolutionStatus, TemporalScope,
    TrueNorthSemanticEnvelope, ValidationFailureStage,
)
from src.evaluation.contracts import (
    DocumentationQualityTag, EvaluationCase, EvaluationCategory, EvaluationContract,
    ExpectedSemanticOutcome, FixtureExpectation,
)
from src.policy import evaluate_policy
from src.semantic_validation import validate_semantic_candidate


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = REPOSITORY_ROOT / "evaluation" / "corpus" / "successor_corpus.json"
LEGACY_CORPUS_PATH = REPOSITORY_ROOT / "evaluation" / "corpus" / "corpus.json"
CORPUS_IDENTITY = "violence-checker-true-north-operational-evaluation"
CORPUS_VERSION = "3.0.0"
CORPUS_SCHEMA_VERSION = "3.0.0"
EVALUATION_SCHEMA_VERSION = "3.0.0"


class CorpusIssueCode(str, Enum):
    INVALID_JSON = "invalid_json"
    INVALID_SCHEMA = "invalid_schema"
    UNSUPPORTED_CORPUS_IDENTITY = "unsupported_corpus_identity"
    UNSUPPORTED_CORPUS_VERSION = "unsupported_corpus_version"
    UNSUPPORTED_CORPUS_SCHEMA_VERSION = "unsupported_corpus_schema_version"
    UNSUPPORTED_EVALUATION_SCHEMA_VERSION = "unsupported_evaluation_schema_version"
    UNSUPPORTED_SEMANTIC_SCHEMA = "unsupported_semantic_schema"
    EMPTY_CORPUS = "empty_corpus"
    DUPLICATE_CASE_ID = "duplicate_case_id"
    NON_CANONICAL_CASE_ORDER = "non_canonical_case_order"
    CASE_SCHEMA_MISMATCH = "case_schema_mismatch"
    INVALID_GROUND_TRUTH = "invalid_ground_truth"
    MISSING_CATEGORY_COVERAGE = "missing_category_coverage"
    MISSING_DOCUMENTATION_TAG_COVERAGE = "missing_documentation_tag_coverage"
    INVALID_FIXTURE_AUTHORITY = "invalid_fixture_authority"


class CorpusValidationIssue(EvaluationContract):
    code: CorpusIssueCode
    field: StrictStr
    message: StrictStr


class CorpusDocument(EvaluationContract):
    corpus_identity: StrictStr
    corpus_version: StrictStr
    corpus_schema_version: StrictStr
    evaluation_schema_version: StrictStr
    semantic_schema_identity: StrictStr
    semantic_schema_version: StrictStr
    fixture_expectations: tuple[FixtureExpectation, ...]
    cases: tuple[EvaluationCase, ...]


class CorpusCoverageSummary(EvaluationContract):
    corpus_identity: StrictStr
    corpus_version: StrictStr
    total_cases: StrictInt
    primary_categories: dict[StrictStr, StrictInt]
    documentation_quality_tags: dict[StrictStr, StrictInt]
    compound_cases: StrictInt
    expected_success: StrictInt
    expected_failure: StrictInt
    policy_outcomes: dict[StrictStr, StrictInt]
    fixture_expectations: StrictInt


class CorpusValidationError(ValueError):
    def __init__(self, issues: List[CorpusValidationIssue]):
        self.issues = issues
        super().__init__("; ".join(f"{item.code.value}:{item.field}" for item in issues))


def _issue(code: CorpusIssueCode, field: str, message: str) -> CorpusValidationIssue:
    return CorpusValidationIssue(code=code, field=field, message=message)


def parse_corpus_text(text: str) -> CorpusDocument:
    try:
        return CorpusDocument.model_validate_json(text)
    except (ValidationError, ValueError) as error:
        if isinstance(error, ValidationError):
            detail = "; ".join(".".join(str(part) for part in item["loc"]) for item in error.errors())
        else:
            detail = str(error)
        raise CorpusValidationError([_issue(CorpusIssueCode.INVALID_SCHEMA, "corpus", detail)]) from error


def semantic_candidate_for_case(case: EvaluationCase) -> TrueNorthSemanticEnvelope:
    """Build repository-shaped test input from operational corpus setup only."""
    facts: list[IncidentFact] = []
    evidence_index = 1
    group_names = sorted({fact.contradiction_group for fact in case.ground_truth.operational_facts if fact.contradiction_group})
    groups = {name: f"CGRP-{index:04d}" for index, name in enumerate(group_names, 1)}
    for index, expected in enumerate(case.ground_truth.operational_facts, 1):
        evidence: list[FactEvidence] = []
        for item in expected.evidence:
            start = case.narrative.find(item.excerpt)
            evidence.append(FactEvidence(
                evidence_id=f"EVID-{evidence_index:04d}",
                excerpt=item.excerpt,
                supports=list(item.supports),
                start_offset=start if start >= 0 and case.narrative.find(item.excerpt, start + 1) < 0 else None,
                end_offset=start + len(item.excerpt) if start >= 0 and case.narrative.find(item.excerpt, start + 1) < 0 else None,
            ))
            evidence_index += 1
        facts.append(IncidentFact(
            fact_id=f"FACT-{index:04d}",
            conduct=expected.conduct,
            direction=expected.direction,
            intentionality=expected.intentionality,
            temporal_scope=expected.temporal_scope,
            assertion_status=expected.assertion_status,
            resolution_status=expected.resolution_status,
            uncertainty=list(expected.uncertainty),
            evidence=evidence,
            supersedes_fact_id=(
                f"FACT-{expected.correction_of_fact + 1:04d}"
                if expected.correction_of_fact is not None else None
            ),
            contradiction_group=groups.get(expected.contradiction_group),
        ))
    return TrueNorthSemanticEnvelope(
        schema_identity=SEMANTIC_SCHEMA_IDENTITY,
        schema_version=SEMANTIC_SCHEMA_VERSION,
        extraction_contract_identity=EXTRACTION_CONTRACT_IDENTITY,
        incident_id=case.case_id,
        facts=facts,
    )


def _qualifying_conduct(validation) -> tuple[Conduct, ...]:
    if not validation.passed or validation.validated_envelope is None or validation.derived_semantics is None:
        return ()
    active = set(validation.derived_semantics.active_fact_ids)
    values = {
        fact.conduct for fact in validation.validated_envelope.facts
        if fact.fact_id in active and fact.conduct is not None
        and fact.intentionality == Intentionality.INTENTIONAL
        and fact.temporal_scope == TemporalScope.CURRENT
        and fact.assertion_status == AssertionStatus.AFFIRMED
    }
    return tuple(value for value in Conduct if value in values)


def validate_corpus(document: CorpusDocument) -> List[CorpusValidationIssue]:
    issues: list[CorpusValidationIssue] = []
    headers = {
        "corpus_identity": (CORPUS_IDENTITY, CorpusIssueCode.UNSUPPORTED_CORPUS_IDENTITY),
        "corpus_version": (CORPUS_VERSION, CorpusIssueCode.UNSUPPORTED_CORPUS_VERSION),
        "corpus_schema_version": (CORPUS_SCHEMA_VERSION, CorpusIssueCode.UNSUPPORTED_CORPUS_SCHEMA_VERSION),
        "evaluation_schema_version": (EVALUATION_SCHEMA_VERSION, CorpusIssueCode.UNSUPPORTED_EVALUATION_SCHEMA_VERSION),
        "semantic_schema_identity": (SEMANTIC_SCHEMA_IDENTITY, CorpusIssueCode.UNSUPPORTED_SEMANTIC_SCHEMA),
        "semantic_schema_version": (SEMANTIC_SCHEMA_VERSION, CorpusIssueCode.UNSUPPORTED_SEMANTIC_SCHEMA),
    }
    for field, (expected, code) in headers.items():
        if getattr(document, field) != expected:
            issues.append(_issue(code, field, f"Expected {expected}."))
    if not document.cases:
        return [*issues, _issue(CorpusIssueCode.EMPTY_CORPUS, "cases", "Corpus must contain cases.")]
    ids = [case.case_id for case in document.cases]
    if len(ids) != len(set(ids)):
        issues.append(_issue(CorpusIssueCode.DUPLICATE_CASE_ID, "cases", "Case identifiers must be unique."))
    if ids != sorted(ids):
        issues.append(_issue(CorpusIssueCode.NON_CANONICAL_CASE_ORDER, "cases", "Cases must use stable identifier order."))
    for index, case in enumerate(document.cases):
        prefix = f"cases.{index}"
        if case.schema_version != EVALUATION_SCHEMA_VERSION:
            issues.append(_issue(CorpusIssueCode.CASE_SCHEMA_MISMATCH, f"{prefix}.schema_version", "Case schema version is unsupported."))
            continue
        validation = validate_semantic_candidate(
            semantic_candidate_for_case(case), incident_id=case.case_id, normalized_narrative=case.narrative,
        )
        truth = case.ground_truth
        decision = evaluate_policy(
            validated=validation.validated_envelope,
            processing_status=validation.processing_status,
            completeness_status=validation.completeness_status,
            derived=validation.derived_semantics,
        )
        observed_codes = tuple(issue.code for issue in (
            validation.schema_validation.issues + validation.domain_validation.issues
        ))
        checks = (
            validation.processing_status == truth.processing_status,
            validation.completeness_status == truth.completeness_status,
            validation.failure_stage == truth.validation_failure_stage,
            decision.outcome == truth.deterministic_outcome,
            _qualifying_conduct(validation) == truth.qualifying_conduct,
            set(observed_codes) == set(truth.validation_issue_codes),
            (validation.passed) == (truth.semantic_outcome == ExpectedSemanticOutcome.SUCCESS),
        )
        if validation.derived_semantics is not None:
            checks += (validation.derived_semantics.incident_direction == truth.incident_direction,)
        if not all(checks):
            issues.append(_issue(CorpusIssueCode.INVALID_GROUND_TRUTH, f"{prefix}.ground_truth", "Operational expectation does not match deterministic repository behavior."))
    represented = {case.metadata.primary_category for case in document.cases}
    missing = set(EvaluationCategory) - represented
    if missing:
        issues.append(_issue(CorpusIssueCode.MISSING_CATEGORY_COVERAGE, "cases.metadata.primary_category", f"Missing: {sorted(item.value for item in missing)}"))
    tags = {tag for case in document.cases for tag in case.metadata.documentation_quality_tags}
    missing_tags = set(DocumentationQualityTag) - tags
    if missing_tags:
        issues.append(_issue(CorpusIssueCode.MISSING_DOCUMENTATION_TAG_COVERAGE, "cases.metadata.documentation_quality_tags", f"Missing: {sorted(item.value for item in missing_tags)}"))
    fixture_ids = tuple(item.fixture_id for item in document.fixture_expectations)
    if fixture_ids != tuple(f"CASE_{index:03d}" for index in range(1, 9)):
        issues.append(_issue(CorpusIssueCode.INVALID_FIXTURE_AUTHORITY, "fixture_expectations", "All eight fixtures require canonical explicit expectations."))
    return issues


def load_corpus(path: Path = CORPUS_PATH) -> CorpusDocument:
    try:
        document = parse_corpus_text(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise CorpusValidationError([_issue(CorpusIssueCode.INVALID_JSON, "corpus", "Corpus file is unavailable.")]) from error
    issues = validate_corpus(document)
    if issues:
        raise CorpusValidationError(issues)
    return document


def load_legacy_corpus_document() -> dict[str, object]:
    raw = json.loads(LEGACY_CORPUS_PATH.read_text(encoding="utf-8"))
    required = {"cases", "corpus_identity", "corpus_schema_version", "corpus_version", "evaluation_schema_version"}
    if set(raw) != required or raw.get("evaluation_schema_version") != "1.0.0":
        raise ValueError("unsupported or malformed legacy corpus schema")
    return raw


def corpus_coverage(document: CorpusDocument) -> CorpusCoverageSummary:
    categories = Counter(case.metadata.primary_category.value for case in document.cases)
    tags = Counter(tag.value for case in document.cases for tag in case.metadata.documentation_quality_tags)
    outcomes = Counter(case.ground_truth.deterministic_outcome.value for case in document.cases)
    successes = sum(case.ground_truth.semantic_outcome == ExpectedSemanticOutcome.SUCCESS for case in document.cases)
    return CorpusCoverageSummary(
        corpus_identity=document.corpus_identity, corpus_version=document.corpus_version,
        total_cases=len(document.cases),
        primary_categories={key: categories[key] for key in sorted(categories)},
        documentation_quality_tags={key: tags[key] for key in sorted(tags)},
        compound_cases=sum(case.metadata.compound for case in document.cases),
        expected_success=successes, expected_failure=len(document.cases) - successes,
        policy_outcomes={key: outcomes[key] for key in sorted(outcomes)},
        fixture_expectations=len(document.fixture_expectations),
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the True North evaluation corpus.")
    parser.add_argument("command", choices=("validate", "coverage"))
    args = parser.parse_args(argv)
    try:
        document = load_corpus()
    except CorpusValidationError as error:
        print(json.dumps({"issues": [item.model_dump(mode="json") for item in error.issues], "status": "failed"}, sort_keys=True))
        return 1
    value = {"case_count": len(document.cases), "status": "passed"} if args.command == "validate" else corpus_coverage(document).model_dump(mode="json")
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
