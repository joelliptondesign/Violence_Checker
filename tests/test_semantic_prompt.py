from src.semantic_prompt import SEMANTIC_EXTRACTION_PROMPT


def test_prompt_requires_one_proposition_envelope_and_exact_evidence():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()
    assert "violence-checker.proposition-semantics" in prompt
    assert "one response" in prompt
    assert "exact evidence" in prompt
    assert "supersedes" in prompt
    assert "conflicts_with" in prompt


def test_prompt_prohibits_policy_and_recommendations():
    prompt = SEMANTIC_EXTRACTION_PROMPT.lower()
    assert "do not make operational recommendations" in prompt
    assert "do not decide" in prompt
    assert "do not author a direction" in prompt
