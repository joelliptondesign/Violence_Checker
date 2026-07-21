from src.semantic_prompt import SEMANTIC_EXTRACTION_PROMPT


def normalized_prompt():
    return " ".join(SEMANTIC_EXTRACTION_PROMPT.casefold().split())


def test_prompt_requests_only_true_north_operational_facts_and_exact_evidence():
    prompt = SEMANTIC_EXTRACTION_PROMPT.casefold()
    for required in (
        "operational incident facts", "conduct", "direction", "intentionality",
        "temporal_scope", "assertion_status", "exact fact-specific evidence",
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
    assert "unresolved materially conflicting facts" in prompt
    assert "not correction targets" in prompt


def test_prompt_limits_facts_and_closes_observed_evidence_and_timing_gaps():
    prompt = SEMANTIC_EXTRACTION_PROMPT.casefold()
    assert "emit only classification-relevant operational facts" in prompt
    assert "do not emit separate facts solely for emotion" in prompt
    assert "every attribute marked unresolved or uncertain" in prompt
    assert "volitional action phrasing" in prompt
    assert "never convert missing timing into historical" in prompt
    assert "do not duplicate a fact" in prompt


def test_prompt_preserves_denied_proposition_attributes_without_affirming_conduct():
    prompt = normalized_prompt()
    assert "for a denied or disputed proposition" in prompt
    assert "assertion_status alone records" in prompt
    assert "a denial must never become an affirmed fact" in prompt
    assert "no-contact evidence cannot support affirmed physical_contact" in prompt


def test_prompt_keeps_ambiguous_insufficient_and_generic_negative_text_non_definite():
    prompt = normalized_prompt()
    assert "ambiguous, incomplete, hypothetical, or adversarial wording" in prompt
    assert "emit one unresolved fact rather than an empty facts list" in prompt
    assert "generic statements" in prompt
    assert "do not require a negative fact" in prompt


def test_prompt_enforces_contact_direction_intentionality_and_evidence_boundaries():
    prompt = normalized_prompt()
    assert "missed action without contact is physical_attempt" in prompt
    assert "property damage is property_violence only when intentionality" in prompt
    assert "property conduct is object_directed" in prompt
    assert "direction unknown must carry direction uncertainty" in prompt
    assert "resolution status is repository-derived" in prompt
    assert "do not reuse a broad excerpt indiscriminately" in prompt


def test_prompt_requires_supported_correction_and_fact_local_contradiction_evidence():
    prompt = normalized_prompt()
    assert "leave it active" in prompt
    assert "omit supersedes_local_ref" in prompt
    assert "candidate must fail closed at validation" in prompt
    assert "do not attach one witness account to every contradiction member" in prompt
