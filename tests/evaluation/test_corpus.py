import hashlib
import json
from pathlib import Path

from src.evaluation.contracts import DocumentationQualityTag, EvaluationCategory
from src.evaluation.corpus import corpus_coverage, load_corpus, load_legacy_corpus_document, validate_corpus


def test_successor_corpus_loads_atomically_with_48_stable_cases():
    corpus = load_corpus()
    assert not validate_corpus(corpus)
    assert [case.case_id for case in corpus.cases] == [f"EVAL_{index:03d}" for index in range(1, 49)]
    assert all(case.synthetic is True for case in corpus.cases)


def test_successor_corpus_preserves_legacy_narrative_bytes_and_metadata_authority():
    successor = load_corpus()
    legacy = load_legacy_corpus_document()
    legacy_by_id = {case["case_id"]: case for case in legacy["cases"]}
    for case in successor.cases:
        assert case.narrative.encode("utf-8") == legacy_by_id[case.case_id]["narrative"].encode("utf-8")
        assert case.synthetic == legacy_by_id[case.case_id]["synthetic"]
        assert case.metadata.model_dump(mode="json") == legacy_by_id[case.case_id]["metadata"]


def test_every_category_and_documentation_tag_is_preserved():
    coverage = corpus_coverage(load_corpus())
    assert set(coverage.primary_categories) == {item.value for item in EvaluationCategory}
    assert set(coverage.documentation_quality_tags) == {item.value for item in DocumentationQualityTag}
    assert set(coverage.primary_categories.values()) == {4}
    assert coverage.compound_cases == 21


def test_ground_truth_has_explicit_entities_propositions_supports_derivation_and_policy():
    for case in load_corpus().cases:
        truth = case.ground_truth
        envelope = truth.semantic_envelope
        assert envelope.entities and envelope.propositions
        assert envelope.evidence_excerpts and envelope.evidence_supports
        assert truth.expected_derived.active_proposition_ids
        assert truth.policy_decision is not None


def test_legacy_corpus_file_is_unchanged_creation_time_family():
    raw = json.loads(Path("evaluation/corpus/corpus.json").read_text())
    assert raw["corpus_identity"] == "violence-checker-synthetic-evaluation-corpus"
    assert raw["evaluation_schema_version"] == "1.0.0"
