"""Deterministic loading, validation, and coverage for the authoritative corpus."""

from __future__ import annotations

import argparse
import json
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import ConfigDict, Field, StrictInt, StrictStr, ValidationError, model_validator

from src.compatibility_finding import construct_compatibility_finding
from src.contracts import PolicyOutcome
from src.evaluation.contracts import (
    DocumentationQualityTag,
    EvaluationCase,
    EvaluationCategory,
    EvaluationContract,
    ExpectedSemanticOutcome,
)
from src.evaluation.serialization import canonical_json
from src.policy import evaluate_policy
from src.semantic_validation import validate_semantic_candidate


CORPUS_SCHEMA_VERSION = "1.0.0"
EVALUATION_SCHEMA_VERSION = "1.0.0"
MINIMUM_CASES = 40
MAXIMUM_CASES = 80
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUTHORITATIVE_CORPUS_PATH = REPOSITORY_ROOT / "evaluation" / "corpus" / "corpus.json"


class CorpusIssueCode(str, Enum):
    JSON_INVALID = "json_invalid"
    DUPLICATE_JSON_KEY = "duplicate_json_key"
    DOCUMENT_INVALID = "document_invalid"
    UNSUPPORTED_CORPUS_SCHEMA_VERSION = "unsupported_corpus_schema_version"
    UNSUPPORTED_EVALUATION_SCHEMA_VERSION = "unsupported_evaluation_schema_version"
    EMPTY_CORPUS = "empty_corpus"
    CASE_COUNT_OUT_OF_RANGE = "case_count_out_of_range"
    DUPLICATE_CASE_IDENTIFIER = "duplicate_case_identifier"
    NON_DETERMINISTIC_CASE_ORDER = "non_deterministic_case_order"
    NON_DETERMINISTIC_METADATA_ORDER = "non_deterministic_metadata_order"
    INVALID_CATEGORY_VOCABULARY = "invalid_category_vocabulary"
    INVALID_DOCUMENTATION_TAG_VOCABULARY = "invalid_documentation_tag_vocabulary"
    MISSING_PRIMARY_CATEGORY = "missing_primary_category"
    MISSING_REQUIRED_CATEGORY = "missing_required_category"
    MISSING_REQUIRED_DOCUMENTATION_TAG = "missing_required_documentation_tag"
    MISSING_COMPOUND_CASE = "missing_compound_case"
    MISSING_POLICY_OUTCOME = "missing_policy_outcome"
    MISSING_HISTORICAL_CASE = "missing_historical_case"
    INVALID_GROUND_TRUTH = "invalid_ground_truth"
    COMPATIBILITY_MISMATCH = "compatibility_mismatch"
    POLICY_MISMATCH = "policy_mismatch"
    GENERATED_ARTIFACT_PRESENT = "generated_artifact_present"


class CorpusValidationIssue(EvaluationContract):
    code: CorpusIssueCode
    message: StrictStr
    case_id: Optional[StrictStr] = None


class CorpusDocument(EvaluationContract):
    corpus_identity: StrictStr
    corpus_version: StrictStr
    corpus_schema_version: StrictStr
    evaluation_schema_version: StrictStr
    cases: List[EvaluationCase]

    @model_validator(mode="after")
    def require_metadata(self) -> "CorpusDocument":
        for field_name in ("corpus_identity", "corpus_version"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty or whitespace")
        return self


class CorpusCoverageSummary(EvaluationContract):
    corpus_identity: StrictStr
    corpus_version: StrictStr
    total_cases: StrictInt
    primary_categories: dict[StrictStr, StrictInt]
    documentation_quality_tags: dict[StrictStr, StrictInt]
    expected_success: StrictInt
    expected_failure: StrictInt
    current_event: StrictInt
    historical_only: StrictInt
    policy_outcomes: dict[StrictStr, StrictInt]
    compound_cases: StrictInt


class CorpusValidationError(ValueError):
    """Atomic failure carrying bounded, deterministically ordered issues."""

    def __init__(self, issues: List[CorpusValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(f"{issue.code.value}: {issue.message}" for issue in issues))


class _DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def parse_corpus_text(text: str) -> CorpusDocument:
    """Parse one complete corpus atomically, rejecting duplicate JSON keys."""

    try:
        raw = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except _DuplicateKeyError as error:
        raise CorpusValidationError(
            [
                CorpusValidationIssue(
                    code=CorpusIssueCode.DUPLICATE_JSON_KEY,
                    message=f"duplicate JSON key: {error}",
                )
            ]
        ) from error
    except json.JSONDecodeError as error:
        raise CorpusValidationError(
            [
                CorpusValidationIssue(
                    code=CorpusIssueCode.JSON_INVALID,
                    message=f"invalid JSON at line {error.lineno}, column {error.colno}",
                )
            ]
        ) from error

    if isinstance(raw, dict):
        if raw.get("corpus_schema_version") != CORPUS_SCHEMA_VERSION:
            raise CorpusValidationError(
                [
                    CorpusValidationIssue(
                        code=CorpusIssueCode.UNSUPPORTED_CORPUS_SCHEMA_VERSION,
                        message=f"supported corpus schema version is {CORPUS_SCHEMA_VERSION}",
                    )
                ]
            )
        if raw.get("evaluation_schema_version") != EVALUATION_SCHEMA_VERSION:
            raise CorpusValidationError(
                [
                    CorpusValidationIssue(
                        code=CorpusIssueCode.UNSUPPORTED_EVALUATION_SCHEMA_VERSION,
                        message=f"supported evaluation schema version is {EVALUATION_SCHEMA_VERSION}",
                    )
                ]
            )

    try:
        return CorpusDocument.model_validate_json(text)
    except ValidationError as error:
        raise CorpusValidationError(
            [
                CorpusValidationIssue(
                    code=CorpusIssueCode.DOCUMENT_INVALID,
                    message=json.dumps(error.errors(include_url=False), sort_keys=True, default=str),
                )
            ]
        ) from error


def _issue(
    code: CorpusIssueCode,
    message: str,
    case_id: Optional[str] = None,
) -> CorpusValidationIssue:
    return CorpusValidationIssue(code=code, message=message, case_id=case_id)


def validate_corpus(document: CorpusDocument) -> List[CorpusValidationIssue]:
    """Return every bounded corpus-level and ground-truth integrity issue."""

    issues: List[CorpusValidationIssue] = []
    cases = document.cases
    if not cases:
        issues.append(_issue(CorpusIssueCode.EMPTY_CORPUS, "corpus must contain cases"))
        return issues
    if not MINIMUM_CASES <= len(cases) <= MAXIMUM_CASES:
        issues.append(
            _issue(
                CorpusIssueCode.CASE_COUNT_OUT_OF_RANGE,
                f"case count must be between {MINIMUM_CASES} and {MAXIMUM_CASES}",
            )
        )

    identifiers = [case.case_id for case in cases]
    seen: set[str] = set()
    for case_id in identifiers:
        if case_id in seen:
            issues.append(
                _issue(CorpusIssueCode.DUPLICATE_CASE_IDENTIFIER, "duplicate case identifier", case_id)
            )
        seen.add(case_id)
    if identifiers != sorted(identifiers):
        issues.append(
            _issue(
                CorpusIssueCode.NON_DETERMINISTIC_CASE_ORDER,
                "cases must be ordered lexicographically by stable case identifier",
            )
        )

    present_categories = {
        case.metadata.primary_category for case in cases if case.metadata.primary_category is not None
    }
    present_tags = {tag for case in cases for tag in case.metadata.documentation_quality_tags}
    category_order = {category.value: index for index, category in enumerate(EvaluationCategory)}
    tag_order = {tag.value: index for index, tag in enumerate(DocumentationQualityTag)}
    for case in cases:
        if case.schema_version != document.evaluation_schema_version:
            issues.append(
                _issue(
                    CorpusIssueCode.UNSUPPORTED_EVALUATION_SCHEMA_VERSION,
                    "case schema version does not match corpus evaluation schema version",
                    case.case_id,
                )
            )
        if case.metadata.primary_category is None:
            issues.append(
                _issue(CorpusIssueCode.MISSING_PRIMARY_CATEGORY, "primary category is required", case.case_id)
            )
        unknown_categories = [
            value for value in case.metadata.categories if value not in category_order
        ]
        unknown_tags = [
            value for value in case.metadata.documentation_quality_tags if value not in tag_order
        ]
        if unknown_categories:
            issues.append(
                _issue(
                    CorpusIssueCode.INVALID_CATEGORY_VOCABULARY,
                    f"unknown categories: {unknown_categories}",
                    case.case_id,
                )
            )
        else:
            ordered_categories = [case.metadata.categories[0]] + sorted(
                case.metadata.categories[1:], key=lambda value: category_order[value]
            )
            if case.metadata.categories != ordered_categories:
                issues.append(
                    _issue(
                        CorpusIssueCode.NON_DETERMINISTIC_METADATA_ORDER,
                        "categories must follow bounded vocabulary order",
                        case.case_id,
                    )
                )
        if unknown_tags:
            issues.append(
                _issue(
                    CorpusIssueCode.INVALID_DOCUMENTATION_TAG_VOCABULARY,
                    f"unknown documentation tags: {unknown_tags}",
                    case.case_id,
                )
            )
        elif case.metadata.documentation_quality_tags != sorted(
            case.metadata.documentation_quality_tags,
            key=lambda value: tag_order[value],
        ):
            issues.append(
                _issue(
                    CorpusIssueCode.NON_DETERMINISTIC_METADATA_ORDER,
                    "documentation tags must follow bounded vocabulary order",
                    case.case_id,
                )
            )
        truth = case.ground_truth
        if truth.semantic_outcome == ExpectedSemanticOutcome.SUCCESS:
            if truth.semantic_facts is None or truth.compatibility_finding is None or truth.policy_decision is None:
                issues.append(
                    _issue(
                        CorpusIssueCode.INVALID_GROUND_TRUTH,
                        "expected success requires semantic facts, compatibility finding, and policy decision",
                        case.case_id,
                    )
                )
                continue
            validation = validate_semantic_candidate(truth.semantic_facts)
            if not validation.passed or validation.validated_facts is None:
                issues.append(
                    _issue(
                        CorpusIssueCode.INVALID_GROUND_TRUTH,
                        "expected semantic facts are not admissible",
                        case.case_id,
                    )
                )
                continue
            compatibility = construct_compatibility_finding(validation.validated_facts)
            if compatibility.finding != truth.compatibility_finding:
                issues.append(
                    _issue(
                        CorpusIssueCode.COMPATIBILITY_MISMATCH,
                        "expected compatibility finding does not exactly match semantic facts",
                        case.case_id,
                    )
                )
            expected_policy = evaluate_policy(
                validated_facts=validation.validated_facts,
                finding=compatibility.finding,
            )
            if expected_policy != truth.policy_decision:
                issues.append(
                    _issue(
                        CorpusIssueCode.POLICY_MISMATCH,
                        "expected policy decision does not match current policy authority",
                        case.case_id,
                    )
                )

    for category in EvaluationCategory:
        if category not in present_categories:
            issues.append(
                _issue(CorpusIssueCode.MISSING_REQUIRED_CATEGORY, f"missing category: {category.value}")
            )
    for tag in DocumentationQualityTag:
        if tag.value not in present_tags:
            issues.append(
                _issue(
                    CorpusIssueCode.MISSING_REQUIRED_DOCUMENTATION_TAG,
                    f"missing documentation tag: {tag.value}",
                )
            )
    if not any(case.metadata.compound for case in cases):
        issues.append(_issue(CorpusIssueCode.MISSING_COMPOUND_CASE, "compound cases are required"))

    policy_outcomes = {
        case.ground_truth.policy_decision.outcome
        for case in cases
        if case.ground_truth.policy_decision is not None
    }
    for outcome in (
        PolicyOutcome.WRITE_DETECTED,
        PolicyOutcome.WRITE_UNCERTAIN,
        PolicyOutcome.WRITE_NOT_DETECTED,
    ):
        if outcome not in policy_outcomes:
            issues.append(
                _issue(CorpusIssueCode.MISSING_POLICY_OUTCOME, f"missing policy outcome: {outcome.value}")
            )
    if not any(
        case.ground_truth.semantic_facts is not None
        and not case.ground_truth.semantic_facts.current_event
        for case in cases
    ):
        issues.append(_issue(CorpusIssueCode.MISSING_HISTORICAL_CASE, "historical-only case is required"))
    return issues


def corpus_coverage(document: CorpusDocument) -> CorpusCoverageSummary:
    """Calculate deterministic counts without executing semantic extraction."""

    categories = {
        category.value: sum(
            case.metadata.primary_category == category for case in document.cases
        )
        for category in EvaluationCategory
    }
    tags = {
        tag.value: sum(tag.value in case.metadata.documentation_quality_tags for case in document.cases)
        for tag in DocumentationQualityTag
    }
    outcomes = {
        outcome.value: sum(
            case.ground_truth.policy_decision is not None
            and case.ground_truth.policy_decision.outcome == outcome
            for case in document.cases
        )
        for outcome in (
            PolicyOutcome.WRITE_DETECTED,
            PolicyOutcome.WRITE_UNCERTAIN,
            PolicyOutcome.WRITE_NOT_DETECTED,
            PolicyOutcome.WRITE_FAILED,
        )
    }
    success = sum(
        case.ground_truth.semantic_outcome == ExpectedSemanticOutcome.SUCCESS
        for case in document.cases
    )
    historical = sum(
        case.ground_truth.semantic_facts is not None
        and not case.ground_truth.semantic_facts.current_event
        for case in document.cases
    )
    return CorpusCoverageSummary(
        corpus_identity=document.corpus_identity,
        corpus_version=document.corpus_version,
        total_cases=len(document.cases),
        primary_categories=categories,
        documentation_quality_tags=tags,
        expected_success=success,
        expected_failure=len(document.cases) - success,
        current_event=len(document.cases) - historical,
        historical_only=historical,
        policy_outcomes=outcomes,
        compound_cases=sum(case.metadata.compound for case in document.cases),
    )


def load_corpus() -> CorpusDocument:
    """Load only the canonical authoritative corpus or fail atomically."""

    document = parse_corpus_text(AUTHORITATIVE_CORPUS_PATH.read_text(encoding="utf-8"))
    issues = validate_corpus(document)
    if issues:
        raise CorpusValidationError(issues)
    return document


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and inspect the synthetic evaluation corpus.")
    parser.add_argument("command", choices=("validate", "coverage"))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        document = load_corpus()
    except (CorpusValidationError, OSError) as error:
        if isinstance(error, CorpusValidationError):
            payload = {"status": "failed", "issues": [issue.model_dump(mode="json") for issue in error.issues]}
        else:
            payload = {"status": "failed", "issues": [{"code": "corpus_unavailable", "message": str(error)}]}
        print(json.dumps(payload, sort_keys=True))
        return 1
    if args.command == "validate":
        print(json.dumps({"case_count": len(document.cases), "status": "passed"}, sort_keys=True))
    else:
        print(canonical_json(corpus_coverage(document)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
