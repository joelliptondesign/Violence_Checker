from src.semantic_prompt import SEMANTIC_EXTRACTION_PROMPT


def test_prompt_requires_one_semantic_candidate_response_and_exact_evidence():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()
    assert "structured semantic candidate response" in prompt
    assert "one response" in prompt
    assert "exact evidence" in prompt
    assert "supersedes" in prompt
    assert "conflicts_with" in prompt
    assert "do not return an incident identifier" in prompt
    assert "temporary" in prompt


def test_prompt_prohibits_policy_and_recommendations():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()
    assert "do not make operational recommendations" in prompt
    assert "do not decide" in prompt
    assert "do not author a direction" in prompt


def test_prompt_encodes_historical_disclosure_domain_admissibility():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()
    assert "disclosed assault from years ago" in prompt
    assert "affirmed historical physical-conduct" in prompt
    assert "completed completion and occurred contact" in prompt
    assert '"nothing happened today"' in prompt
    assert "contextual clarifiers, not separate conduct" in prompt
    assert "return exactly that one violence" in prompt
    assert "do not create current, negated" in prompt
    assert "historical, not uncertain" in prompt
    assert "supports_negation only for a negated proposition" in prompt


def test_prompt_encodes_provider_target_and_conduct_tuple_shapes():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()
    assert "target_kind of entity requires target_ref" in prompt
    assert "self or undetermined requires target_ref to be null" in prompt
    assert "contact_only always requires completed completion" in prompt
    assert "threatening movement must" in prompt
    assert "never attempted or completed" in prompt


def test_prompt_requires_complete_support_and_excludes_extraction_metadata():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()
    assert "never return an unsupported semantic subject" in prompt
    assert "conflicts_with relationship specifically requires supports_conflict" in prompt
    assert "do not return an incident identifier, extraction metadata" in prompt
    assert "violence-checker.proposition-extraction@1.0.0" not in prompt


def test_prompt_treats_explicit_striking_as_resolved_without_inventing_motive():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()
    assert "hitting, punching, or" in prompt
    assert "closed fist as intentional physical conduct" in prompt
    assert "identifies the contact as accidental" in prompt
    assert "does not separately state a motive" in prompt
