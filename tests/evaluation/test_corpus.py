from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from src.evaluation.contracts import (
    DocumentationQualityTag,
    EvaluationCategory,
    ExpectedSemanticOutcome,
)
from src.evaluation.corpus import (
    AUTHORITATIVE_CORPUS_PATH,
    CORPUS_SCHEMA_VERSION,
    EVALUATION_SCHEMA_VERSION,
    MAXIMUM_CASES,
    MINIMUM_CASES,
    CorpusIssueCode,
    CorpusValidationError,
    corpus_coverage,
    load_corpus,
    parse_corpus_text,
    validate_corpus,
)
from src.evaluation.serialization import canonical_json


REPO_ROOT = Path(__file__).resolve().parents[2]


def corpus_payload() -> dict[str, object]:
    return json.loads(AUTHORITATIVE_CORPUS_PATH.read_text(encoding="utf-8"))


def parse_payload(payload: dict[str, object]):
    return parse_corpus_text(json.dumps(payload, sort_keys=True))


def issue_codes(error: CorpusValidationError) -> list[CorpusIssueCode]:
    return [issue.code for issue in error.issues]


def test_authoritative_corpus_loads_atomically() -> None:
    corpus = load_corpus()

    assert corpus.corpus_identity == "violence-checker-synthetic-evaluation-corpus"
    assert corpus.corpus_version == "1.0.0"
    assert corpus.corpus_schema_version == CORPUS_SCHEMA_VERSION
    assert corpus.evaluation_schema_version == EVALUATION_SCHEMA_VERSION
    assert validate_corpus(corpus) == []


def test_case_count_is_authorized_and_substantially_broader_than_fixtures() -> None:
    corpus = load_corpus()

    assert MINIMUM_CASES <= len(corpus.cases) <= MAXIMUM_CASES
    assert len(corpus.cases) == 48
    assert len(corpus.cases) > 8


def test_every_required_category_and_documentation_tag_is_represented() -> None:
    summary = corpus_coverage(load_corpus())

    assert summary.primary_categories == {category.value: 4 for category in EvaluationCategory}
    assert set(summary.documentation_quality_tags) == {
        tag.value for tag in DocumentationQualityTag
    }
    assert all(count > 0 for count in summary.documentation_quality_tags.values())


def test_compound_historical_and_policy_balance_are_represented() -> None:
    summary = corpus_coverage(load_corpus())

    assert summary.compound_cases == 21
    assert summary.historical_only == 4
    assert summary.policy_outcomes == {
        "WRITE_DETECTED": 15,
        "WRITE_UNCERTAIN": 18,
        "WRITE_NOT_DETECTED": 15,
        "WRITE_FAILED": 0,
    }


def test_case_identifiers_are_unique_stable_and_deterministically_ordered() -> None:
    identifiers = [case.case_id for case in load_corpus().cases]

    assert identifiers == [f"EVAL_{number:03d}" for number in range(1, 49)]
    assert identifiers == sorted(identifiers)
    assert len(identifiers) == len(set(identifiers))


def test_category_and_tag_collections_follow_bounded_vocabulary_order() -> None:
    corpus = load_corpus()
    category_order = {category.value: index for index, category in enumerate(EvaluationCategory)}
    tag_order = {tag.value: index for index, tag in enumerate(DocumentationQualityTag)}

    for case in corpus.cases:
        assert case.metadata.categories == [case.metadata.categories[0]] + sorted(
            case.metadata.categories[1:], key=lambda value: category_order[value]
        )
        assert case.metadata.documentation_quality_tags == sorted(
            case.metadata.documentation_quality_tags, key=lambda value: tag_order[value]
        )


def test_corpus_serialization_and_coverage_are_deterministic() -> None:
    first = load_corpus()
    second = load_corpus()

    assert canonical_json(first) == canonical_json(second)
    assert canonical_json(corpus_coverage(first)) == canonical_json(corpus_coverage(second))


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("corpus_schema_version", "2.0.0", CorpusIssueCode.UNSUPPORTED_CORPUS_SCHEMA_VERSION),
        (
            "evaluation_schema_version",
            "2.0.0",
            CorpusIssueCode.UNSUPPORTED_EVALUATION_SCHEMA_VERSION,
        ),
    ],
)
def test_schema_versions_are_enforced(field: str, value: str, code: CorpusIssueCode) -> None:
    payload = corpus_payload()
    payload[field] = value

    with pytest.raises(CorpusValidationError) as exc_info:
        parse_payload(payload)

    assert issue_codes(exc_info.value) == [code]


def test_empty_corpus_is_rejected() -> None:
    payload = corpus_payload()
    payload["cases"] = []
    document = parse_payload(payload)

    assert [issue.code for issue in validate_corpus(document)] == [CorpusIssueCode.EMPTY_CORPUS]


def test_duplicate_case_identifiers_are_rejected() -> None:
    payload = corpus_payload()
    cases = payload["cases"]
    assert isinstance(cases, list)
    cases[1]["case_id"] = cases[0]["case_id"]
    document = parse_payload(payload)

    assert CorpusIssueCode.DUPLICATE_CASE_IDENTIFIER in {
        issue.code for issue in validate_corpus(document)
    }


def test_missing_primary_and_unknown_vocabularies_return_bounded_issues() -> None:
    payload = corpus_payload()
    cases = payload["cases"]
    assert isinstance(cases, list)
    cases[0]["metadata"]["primary_category"] = None
    cases[0]["metadata"]["categories"] = ["unbounded_category"]
    cases[0]["metadata"]["documentation_quality_tags"] = ["unbounded_tag"]
    document = parse_payload(payload)

    codes = {issue.code for issue in validate_corpus(document)}
    assert CorpusIssueCode.MISSING_PRIMARY_CATEGORY in codes
    assert CorpusIssueCode.INVALID_CATEGORY_VOCABULARY in codes
    assert CorpusIssueCode.INVALID_DOCUMENTATION_TAG_VOCABULARY in codes


def test_duplicate_json_keys_are_rejected() -> None:
    text = '{"corpus_schema_version":"1.0.0","corpus_schema_version":"1.0.0"}'

    with pytest.raises(CorpusValidationError) as exc_info:
        parse_corpus_text(text)

    assert issue_codes(exc_info.value) == [CorpusIssueCode.DUPLICATE_JSON_KEY]


@pytest.mark.parametrize(
    ("mutation", "value"),
    [
        ("unknown", "not allowed"),
        ("synthetic", False),
        ("narrative", "   "),
    ],
)
def test_unknown_fields_non_synthetic_cases_and_malformed_narratives_are_rejected(
    mutation: str,
    value: object,
) -> None:
    payload = corpus_payload()
    cases = payload["cases"]
    assert isinstance(cases, list)
    if mutation == "unknown":
        cases[0]["provider_output"] = value
    else:
        cases[0][mutation] = value

    with pytest.raises(CorpusValidationError) as exc_info:
        parse_payload(payload)

    assert issue_codes(exc_info.value) == [CorpusIssueCode.DOCUMENT_INVALID]


def test_contradictory_expected_failure_with_success_payload_is_rejected() -> None:
    payload = corpus_payload()
    cases = payload["cases"]
    assert isinstance(cases, list)
    cases[0]["ground_truth"]["semantic_outcome"] = "failure"
    cases[0]["ground_truth"]["failure_provenance"] = "provider_request"

    with pytest.raises(CorpusValidationError) as exc_info:
        parse_payload(payload)

    assert issue_codes(exc_info.value) == [CorpusIssueCode.DOCUMENT_INVALID]


def test_expected_success_requires_manually_authored_payloads() -> None:
    payload = corpus_payload()
    cases = payload["cases"]
    assert isinstance(cases, list)
    cases[0]["ground_truth"]["semantic_facts"] = None

    with pytest.raises(CorpusValidationError) as exc_info:
        parse_payload(payload)

    assert issue_codes(exc_info.value) == [CorpusIssueCode.DOCUMENT_INVALID]


def test_expected_failure_cannot_fabricate_success_facts() -> None:
    payload = corpus_payload()
    cases = payload["cases"]
    assert isinstance(cases, list)
    truth = cases[0]["ground_truth"]
    truth["semantic_outcome"] = "failure"
    truth["validation_failure_stage"] = "schema"
    truth["failure_provenance"] = "schema_validation"

    with pytest.raises(CorpusValidationError):
        parse_payload(payload)


def test_ground_truth_composes_existing_contracts_and_is_complete() -> None:
    corpus = load_corpus()

    assert all(case.ground_truth.semantic_outcome == ExpectedSemanticOutcome.SUCCESS for case in corpus.cases)
    assert all(case.ground_truth.semantic_facts is not None for case in corpus.cases)
    assert all(case.ground_truth.compatibility_finding is not None for case in corpus.cases)
    assert all(case.ground_truth.policy_decision is not None for case in corpus.cases)
    assert all(
        case.ground_truth.semantic_facts.model_dump(mode="json")
        == case.ground_truth.compatibility_finding.model_dump(mode="json")
        for case in corpus.cases
    )


def test_semantic_input_is_structurally_separate_from_metadata_and_expectations() -> None:
    payload = corpus_payload()

    for case in payload["cases"]:
        assert isinstance(case["narrative"], str)
        assert "metadata" not in case["narrative"]
        assert "ground_truth" not in case["narrative"]
        assert set(case).isdisjoint({"observed_result", "provider_output", "output_parsed"})


def test_loader_imports_no_openai_sdk_and_contains_no_provider_execution() -> None:
    path = REPO_ROOT / "src" / "evaluation" / "corpus.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imports.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert "openai" not in imports
    assert "src.semantic_extractor" not in imports
    assert "extract_violence_finding" not in path.read_text(encoding="utf-8")


def test_loading_corpus_makes_zero_provider_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    import openai

    def fail_provider_construction(*args: object, **kwargs: object) -> None:
        raise AssertionError("corpus loading must not construct a provider client")

    monkeypatch.setattr(openai, "OpenAI", fail_provider_construction)

    assert len(load_corpus().cases) == 48


def test_generated_artifacts_cannot_change_corpus_authority() -> None:
    artifact = REPO_ROOT / "evaluation" / "runs" / "test-authority-separation.json"
    artifact.write_text('{"observed":"not corpus truth"}\n', encoding="utf-8")
    try:
        assert len(load_corpus().cases) == 48
    finally:
        artifact.unlink(missing_ok=True)


def test_demonstration_fixture_source_remains_byte_for_byte_unchanged() -> None:
    fixture_bytes = (REPO_ROOT / "src" / "fixtures.py").read_bytes()

    assert hashlib.sha256(fixture_bytes).hexdigest() == (
        "8b99c65481d9f9642bbed5e2b194c4727d78ad6c3c2f32d78a9935e2c258d271"
    )
