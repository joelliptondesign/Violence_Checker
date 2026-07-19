"""Deterministic adapter that terminates provider-facing structured output."""

from src.contracts import ProviderStructuredResponse, ViolenceSemanticEnvelope


def semantic_candidate_from_provider_response(response: object) -> ViolenceSemanticEnvelope:
    provider_response = ProviderStructuredResponse.model_validate(response)
    return ViolenceSemanticEnvelope.model_validate(provider_response.model_dump())
