import hashlib
import json
from pathlib import Path

from src.evaluation.contracts import AdversarialCondition, DocumentationQualityTag, EvaluationCategory
from src.evaluation.corpus import CORPUS_IDENTITY, corpus_coverage, load_corpus, load_legacy_corpus_document, validate_corpus


def test_true_north_corpus_loads_with_complete_required_coverage():
    corpus = load_corpus()
    assert corpus.corpus_identity == CORPUS_IDENTITY
    assert corpus.evaluation_schema_version == "3.0.0"
    assert not validate_corpus(corpus)
    assert [case.case_id for case in corpus.cases] == [f"TN_{index:03d}" for index in range(1, 25)]
    coverage = corpus_coverage(corpus)
    assert set(coverage.primary_categories) == {item.value for item in EvaluationCategory}
    assert set(coverage.documentation_quality_tags) == {item.value for item in DocumentationQualityTag}
    assert coverage.fixture_expectations == 8


def test_corpus_has_eight_explicit_adversarial_repository_cases():
    corpus = load_corpus()
    adversaries = [case for case in corpus.cases if case.adversarial_condition is not None]
    assert {case.adversarial_condition for case in adversaries} == set(AdversarialCondition)
    assert len(adversaries) == 8


def test_all_fixture_expectations_are_explicit_and_complete():
    expectations = load_corpus().fixture_expectations
    assert [item.fixture_id for item in expectations] == [f"CASE_{index:03d}" for index in range(1, 9)]
    assert all(item.expected_conduct for item in expectations)
    assert all(item.expected_processing_status.value == "successful_analysis" for item in expectations)


def test_historical_corpus_is_read_only_creation_time_family():
    path = Path("evaluation/corpus/corpus.json")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    raw = load_legacy_corpus_document()
    assert raw["evaluation_schema_version"] == "1.0.0"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
