from dataclasses import dataclass
from enum import Enum
from typing import Optional

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from src.config import AppConfig, load_config
from src.contracts import ProviderStructuredResponse
from src.models import Incident
from src.provider_adapter import semantic_candidate_from_provider_response
from src.semantic_prompt import SEMANTIC_EXTRACTION_PROMPT


class SemanticExtractionStatus(str, Enum):
    SUCCESS = "success"
    CONFIGURATION_FAILURE = "configuration_failure"
    REQUEST_FAILURE = "openai_request_failure"
    STRUCTURED_RESPONSE_FAILURE = "structured_response_failure"
    VALIDATION_FAILURE = "pydantic_validation_failure"


@dataclass(frozen=True)
class SemanticExtractionResult:
    status: SemanticExtractionStatus
    semantic_candidate: Optional[object] = None
    failure_message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status == SemanticExtractionStatus.SUCCESS and self.semantic_candidate is None:
            raise ValueError("successful semantic extraction requires a semantic candidate")
        if self.status != SemanticExtractionStatus.SUCCESS and self.semantic_candidate is not None:
            raise ValueError("failed semantic extraction cannot contain a semantic candidate")

    @property
    def succeeded(self) -> bool:
        return self.status == SemanticExtractionStatus.SUCCESS


def extract_semantic_envelope(
    incident: Incident,
    *,
    config: Optional[AppConfig] = None,
    client: Optional[object] = None,
) -> SemanticExtractionResult:
    resolved_config = config or load_config()
    if not resolved_config.openai_api_key:
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.CONFIGURATION_FAILURE,
            failure_message="OPENAI_API_KEY is required for semantic extraction.",
        )

    resolved_client = client or OpenAI(
        api_key=resolved_config.openai_api_key,
        max_retries=0,
    )

    try:
        response = resolved_client.responses.parse(
            model=resolved_config.openai_model,
            instructions=SEMANTIC_EXTRACTION_PROMPT,
            input=incident.narrative,
            text_format=ProviderStructuredResponse,
        )
    except OpenAIError as exc:
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.REQUEST_FAILURE,
            failure_message=exc.__class__.__name__,
        )
    except ValidationError as exc:
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.VALIDATION_FAILURE,
            failure_message=exc.__class__.__name__,
        )
    except Exception as exc:
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.REQUEST_FAILURE,
            failure_message=exc.__class__.__name__,
        )

    parsed = getattr(response, "output_parsed", None)
    if parsed is None:
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.STRUCTURED_RESPONSE_FAILURE,
            failure_message="Structured output was missing from the response.",
        )

    try:
        semantic_candidate = semantic_candidate_from_provider_response(parsed, incident=incident)
    except (ValidationError, ValueError, TypeError) as exc:
        return SemanticExtractionResult(
            status=SemanticExtractionStatus.VALIDATION_FAILURE,
            failure_message=exc.__class__.__name__,
        )

    return SemanticExtractionResult(
        status=SemanticExtractionStatus.SUCCESS,
        semantic_candidate=semantic_candidate,
    )
