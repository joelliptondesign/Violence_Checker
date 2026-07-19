"""Strict successor corpus loading, validation, and deterministic coverage."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import ConfigDict, StrictInt, StrictStr, ValidationError, field_validator

from src.contracts import SEMANTIC_SCHEMA_IDENTITY, SEMANTIC_SCHEMA_VERSION, ValidationFailureStage
from src.evaluation.contracts import (
    DocumentationQualityTag,
    EvaluationCase,
    EvaluationCategory,
    EvaluationContract,
    ExpectedSemanticOutcome,
)
from src.policy import evaluate_policy
from src.semantic_validation import validate_semantic_candidate


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = REPOSITORY_ROOT / "evaluation" / "corpus" / "successor_corpus.json"
LEGACY_CORPUS_PATH = REPOSITORY_ROOT / "evaluation" / "corpus" / "corpus.json"
CORPUS_IDENTITY = "violence-checker-synthetic-proposition-evaluation-corpus"
CORPUS_VERSION = "2.0.0"
CORPUS_SCHEMA_VERSION = "2.0.0"
EVALUATION_SCHEMA_VERSION = "2.0.0"


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
    cases: List[EvaluationCase]


class CorpusCoverageSummary(EvaluationContract):
    model_config = ConfigDict(strict=True, extra="forbid")

    corpus_identity: StrictStr
    corpus_version: StrictStr
    total_cases: StrictInt
    primary_categories: dict[StrictStr, StrictInt]
    documentation_quality_tags: dict[StrictStr, StrictInt]
    compound_cases: StrictInt
    expected_success: StrictInt
    expected_failure: StrictInt
    policy_outcomes: dict[StrictStr, StrictInt]


class CorpusValidationError(ValueError):
    def __init__(self, issues: List[CorpusValidationIssue]):
        self.issues = issues
        super().__init__("; ".join(f"{item.code.value}:{item.field}" for item in issues))


def _issue(code: CorpusIssueCode, field: str, message: str) -> CorpusValidationIssue:
    return CorpusValidationIssue(code=code, field=field, message=message)


def parse_corpus_text(text: str) -> CorpusDocument:
    try:
        return CorpusDocument.model_validate_json(text)
    except ValidationError as error:
        issues = [
            _issue(CorpusIssueCode.INVALID_SCHEMA, ".".join(str(part) for part in item["loc"]), item["msg"])
            for item in error.errors()
        ]
        raise CorpusValidationError(issues) from error


def validate_corpus(document: CorpusDocument) -> List[CorpusValidationIssue]:
    issues: list[CorpusValidationIssue] = []
    expected_header = {
        "corpus_identity": (CORPUS_IDENTITY, CorpusIssueCode.UNSUPPORTED_CORPUS_IDENTITY),
        "corpus_version": (CORPUS_VERSION, CorpusIssueCode.UNSUPPORTED_CORPUS_VERSION),
        "corpus_schema_version": (CORPUS_SCHEMA_VERSION, CorpusIssueCode.UNSUPPORTED_CORPUS_SCHEMA_VERSION),
        "evaluation_schema_version": (EVALUATION_SCHEMA_VERSION, CorpusIssueCode.UNSUPPORTED_EVALUATION_SCHEMA_VERSION),
        "semantic_schema_identity": (SEMANTIC_SCHEMA_IDENTITY, CorpusIssueCode.UNSUPPORTED_SEMANTIC_SCHEMA),
        "semantic_schema_version": (SEMANTIC_SCHEMA_VERSION, CorpusIssueCode.UNSUPPORTED_SEMANTIC_SCHEMA),
    }
    for field, (expected, code) in expected_header.items():
        if getattr(document, field) != expected:
            issues.append(_issue(code, field, f"Expected {expected}."))
    if not document.cases:
        issues.append(_issue(CorpusIssueCode.EMPTY_CORPUS, "cases", "Corpus must contain cases."))
        return issues
    case_ids = [case.case_id for case in document.cases]
    if len(case_ids) != len(set(case_ids)):
        issues.append(_issue(CorpusIssueCode.DUPLICATE_CASE_ID, "cases", "Case identifiers must be unique."))
    if case_ids != sorted(case_ids):
        issues.append(_issue(CorpusIssueCode.NON_CANONICAL_CASE_ORDER, "cases", "Cases must use stable identifier order."))

    for index, case in enumerate(document.cases):
        prefix = f"cases.{index}"
        if case.schema_version != EVALUATION_SCHEMA_VERSION:
            issues.append(_issue(CorpusIssueCode.CASE_SCHEMA_MISMATCH, f"{prefix}.schema_version", "Case schema version is unsupported."))
        truth = case.ground_truth
        if truth.semantic_outcome != ExpectedSemanticOutcome.SUCCESS or truth.semantic_envelope is None or truth.expected_derived is None or truth.policy_decision is None:
            issues.append(_issue(CorpusIssueCode.INVALID_GROUND_TRUTH, f"{prefix}.ground_truth", "Current successor cases require complete success expectations."))
            continue
        validation = validate_semantic_candidate(
            truth.semantic_envelope,
            incident_id=case.case_id,
            normalized_narrative=case.narrative,
        )
        if not validation.passed or validation.validated_envelope is None:
            issues.append(_issue(CorpusIssueCode.INVALID_GROUND_TRUTH, f"{prefix}.ground_truth.semantic_envelope", "Expected envelope is not admissible."))
            continue
        if validation.validated_envelope.derived != truth.expected_derived:
            issues.append(_issue(CorpusIssueCode.INVALID_GROUND_TRUTH, f"{prefix}.ground_truth.expected_derived", "Expected deterministic derivation does not match the envelope."))
        decision = evaluate_policy(validated=validation.validated_envelope)
        if decision != truth.policy_decision:
            issues.append(_issue(CorpusIssueCode.INVALID_GROUND_TRUTH, f"{prefix}.ground_truth.policy_decision", "Expected policy decision does not match deterministic policy."))

    represented_categories = {case.metadata.primary_category for case in document.cases}
    missing_categories = set(EvaluationCategory) - represented_categories
    if missing_categories:
        issues.append(_issue(CorpusIssueCode.MISSING_CATEGORY_COVERAGE, "cases.metadata.primary_category", f"Missing categories: {sorted(item.value for item in missing_categories)}"))
    represented_tags = {DocumentationQualityTag(tag) for case in document.cases for tag in case.metadata.documentation_quality_tags}
    missing_tags = set(DocumentationQualityTag) - represented_tags
    if missing_tags:
        issues.append(_issue(CorpusIssueCode.MISSING_DOCUMENTATION_TAG_COVERAGE, "cases.metadata.documentation_quality_tags", f"Missing tags: {sorted(item.value for item in missing_tags)}"))
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
    """Read the immutable creation-time corpus as historical JSON only."""
    raw = json.loads(LEGACY_CORPUS_PATH.read_text(encoding="utf-8"))
    required = {"cases", "corpus_identity", "corpus_schema_version", "corpus_version", "evaluation_schema_version"}
    if set(raw) != required or raw.get("evaluation_schema_version") != "1.0.0":
        raise ValueError("unsupported or malformed legacy corpus schema")
    return raw


def corpus_coverage(document: CorpusDocument) -> CorpusCoverageSummary:
    categories = Counter(case.metadata.primary_category.value for case in document.cases)
    tags = Counter(tag for case in document.cases for tag in case.metadata.documentation_quality_tags)
    outcomes = Counter(case.ground_truth.policy_decision.outcome.value for case in document.cases if case.ground_truth.policy_decision)
    successes = sum(case.ground_truth.semantic_outcome == ExpectedSemanticOutcome.SUCCESS for case in document.cases)
    return CorpusCoverageSummary(
        corpus_identity=document.corpus_identity,
        corpus_version=document.corpus_version,
        total_cases=len(document.cases),
        primary_categories={key: categories[key] for key in sorted(categories)},
        documentation_quality_tags={key: tags[key] for key in sorted(tags)},
        compound_cases=sum(case.metadata.compound for case in document.cases),
        expected_success=successes,
        expected_failure=len(document.cases) - successes,
        policy_outcomes={key: outcomes[key] for key in sorted(outcomes)},
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the successor evaluation corpus.")
    parser.add_argument("command", choices=("validate", "coverage"))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        document = load_corpus()
    except CorpusValidationError as error:
        print(json.dumps({"issues": [item.model_dump(mode="json") for item in error.issues], "status": "failed"}, sort_keys=True))
        return 1
    if args.command == "validate":
        print(json.dumps({"case_count": len(document.cases), "status": "passed"}, sort_keys=True))
    else:
        print(json.dumps(corpus_coverage(document).model_dump(mode="json"), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
