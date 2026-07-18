"""Deterministic adapter that terminates provider-facing structured output."""

from typing import Dict

from src.contracts import ProviderStructuredResponse


def semantic_candidate_from_provider_response(response: object) -> Dict[str, object]:
    provider_response = ProviderStructuredResponse.model_validate(response)
    return provider_response.model_dump()
