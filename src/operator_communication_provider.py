"""Single-request OpenAI boundary for presentation-only communication."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from src.config import AppConfig, load_config
from src.contracts import OperatorCommunication, OperatorCommunicationInput
from src.operator_communication_prompt import OPERATOR_COMMUNICATION_PROMPT


class OperatorCommunicationStatus(str, Enum):
    SUCCESS = "success"
    CONFIGURATION_FAILURE = "configuration_failure"
    REQUEST_FAILURE = "request_failure"
    STRUCTURED_RESPONSE_FAILURE = "structured_response_failure"
    VALIDATION_FAILURE = "validation_failure"


@dataclass(frozen=True)
class OperatorCommunicationResult:
    status: OperatorCommunicationStatus
    communication: Optional[OperatorCommunication] = None
    failure_message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status == OperatorCommunicationStatus.SUCCESS and self.communication is None:
            raise ValueError("successful communication generation requires a communication payload")
        if self.status != OperatorCommunicationStatus.SUCCESS and self.communication is not None:
            raise ValueError("failed communication generation cannot contain a communication payload")

    @property
    def succeeded(self) -> bool:
        return self.status == OperatorCommunicationStatus.SUCCESS


def generate_operator_communication(
    facts: OperatorCommunicationInput,
    *,
    config: Optional[AppConfig] = None,
    client: Optional[object] = None,
) -> OperatorCommunicationResult:
    """Attempt one strict structured request using only narrowed deterministic facts."""
    if not isinstance(facts, OperatorCommunicationInput):
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.VALIDATION_FAILURE,
            failure_message="OperatorCommunicationInput is required.",
        )
    resolved_config = config or load_config()
    if not resolved_config.openai_api_key:
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.CONFIGURATION_FAILURE,
            failure_message="OPENAI_API_KEY is required for operator communication.",
        )

    resolved_client = client or OpenAI(
        api_key=resolved_config.openai_api_key,
        max_retries=0,
    )
    try:
        response = resolved_client.responses.parse(
            model=resolved_config.openai_communication_model,
            instructions=OPERATOR_COMMUNICATION_PROMPT,
            input=facts.model_dump_json(),
            text_format=OperatorCommunication,
        )
    except OpenAIError as exc:
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.REQUEST_FAILURE,
            failure_message=exc.__class__.__name__,
        )
    except ValidationError as exc:
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.VALIDATION_FAILURE,
            failure_message=exc.__class__.__name__,
        )
    except Exception as exc:
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.REQUEST_FAILURE,
            failure_message=exc.__class__.__name__,
        )

    response_status = getattr(response, "status", "completed")
    if response_status != "completed":
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.STRUCTURED_RESPONSE_FAILURE,
            failure_message=f"Unsupported response status: {response_status}",
        )
    parsed = getattr(response, "output_parsed", None)
    if parsed is None:
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.STRUCTURED_RESPONSE_FAILURE,
            failure_message="Structured output was missing from the response.",
        )
    try:
        communication = OperatorCommunication.model_validate(parsed)
    except (ValidationError, ValueError, TypeError) as exc:
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.VALIDATION_FAILURE,
            failure_message=exc.__class__.__name__,
        )
    summary = communication.incident_summary.casefold()
    rendered = " ".join((
        communication.incident_summary,
        *communication.key_findings,
        communication.why_this_result,
    )).casefold()
    evidence = " ".join(
        excerpt
        for fact in (*facts.active_facts, *facts.superseded_facts)
        for excerpt in fact.evidence_excerpts
    ).casefold()
    issues = []
    if facts.outcome.value.casefold() in summary or any(
        term in summary for term in ("classif", "criteria", "result", "validation", "semantic")
    ):
        issues.append("incident summary must describe the event without explaining classification")
    if "workplace violence criteria" not in communication.why_this_result.casefold():
        issues.append("classification explanation must connect the incident to doctrine")
    evidence_words = set(evidence.replace(".", " ").replace(",", " ").split())
    summary_words = set(summary.replace(".", " ").replace(",", " ").split())
    for claim, support_words in (
        ("patient", ("patient", "pt")), ("nurse", ("nurse", "rn")),
        ("technician", ("technician", "tech")), ("aide", ("aide",)),
        ("visitor", ("visitor",)), ("security", ("security",)),
        ("physician", ("physician", "doctor")),
    ):
        if claim in summary_words and not any(word in evidence_words for word in support_words):
            issues.append(f"unsupported actor introduced: {claim}")
    for fact in facts.active_facts:
        conduct_terms = {
            "verbal_threat": ("threat", "punch", "harm"),
            "physical_attempt": ("attempt", "swung", "lunged", "missed", "tried"),
            "physical_contact": ("contact", "hit", "struck", "grab", "kick", "slap", "elbow"),
            "self_harm": ("self-harm", "themself", "herself", "himself", "own"),
            "property_violence": ("property", "door", "window", "wall", "rail", "object"),
        }.get(fact.conduct.value if fact.conduct is not None else "", ())
        if conduct_terms and not any(term in rendered for term in conduct_terms):
            issues.append("material conduct omitted")
        if fact.intentionality.value == "accidental" and "accident" not in rendered:
            issues.append("accidental intent omitted")
        if fact.temporal_scope.value == "historical" and not any(
            term in rendered for term in ("before", "earlier", "historical", "previous", "years ago")
        ):
            issues.append("material chronology omitted")
    for claim in (
        "injury", "injured", "bruising", "bleeding", "sore", "pain", "hallway",
        "bathroom", "bedroom", "lobby", "parking", "security", "police", "restraint",
        "medication", "ongoing", "resolved", "calmed",
    ):
        if claim in rendered and claim not in evidence:
            issues.append(f"unsupported detail introduced: {claim}")
    if issues:
        return OperatorCommunicationResult(
            status=OperatorCommunicationStatus.VALIDATION_FAILURE,
            failure_message="; ".join(issues),
        )
    return OperatorCommunicationResult(
        status=OperatorCommunicationStatus.SUCCESS,
        communication=communication,
    )
