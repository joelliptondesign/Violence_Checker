from src.semantic_prompt import SEMANTIC_EXTRACTION_PROMPT


def test_prompt_requests_only_true_north_operational_facts_and_exact_evidence():
    prompt = SEMANTIC_EXTRACTION_PROMPT.casefold()
    for required in (
        "operational incident facts", "conduct", "direction", "intentionality",
        "temporal_scope", "assertion_status", "resolution_status", "exact fact-specific evidence",
        "uncertainty", "supersedes_local_ref", "contradiction_group_local_ref",
    ):
        assert required in prompt


def test_prompt_removes_legacy_semantic_graph_and_provider_bookkeeping_authority():
    prompt = SEMANTIC_EXTRACTION_PROMPT.casefold()
    assert "do not return entities, propositions, relationships, graphs" in prompt
    assert "repository-owned bookkeeping" in prompt
    for prohibited_authority in (
        "incident identity", "schema identity or", "extraction contract identity",
        "final fact/evidence/group identifiers", "canonical ordering", "processing status",
        "completeness status",
    ):
        assert prohibited_authority in prompt


def test_prompt_explicitly_prohibits_policy_recommendations_and_unsupported_facts():
    prompt = SEMANTIC_EXTRACTION_PROMPT.casefold()
    assert "do not make or imply a policy decision" in prompt
    assert "negative conclusion" in prompt
    assert "recommendation" in prompt
    assert "do not produce unsupported semantic facts or inferred outcomes" in prompt
    assert "empty facts list is not a conclusion" in prompt


def test_prompt_encodes_fact_level_evidence_and_integrity_adversaries():
    prompt = SEMANTIC_EXTRACTION_PROMPT.casefold()
    assert "single fact it supports" in prompt
    assert "subject-oriented support graph" in prompt
    assert "denial cannot support an affirmed fact" in prompt
    assert "accidental evidence" in prompt
    assert "historical evidence" in prompt
    assert "no-contact evidence" in prompt
    assert "unresolved materially conflicting active facts" in prompt


def test_prompt_limits_facts_and_closes_observed_evidence_and_timing_gaps():
    prompt = SEMANTIC_EXTRACTION_PROMPT.casefold()
    assert "emit only classification-relevant operational facts" in prompt
    assert "do not emit separate facts solely for emotion" in prompt
    assert "every attribute marked unresolved or uncertain" in prompt
    assert "volitional action phrasing" in prompt
    assert "never convert missing timing into historical" in prompt
    assert "do not duplicate a fact" in prompt
