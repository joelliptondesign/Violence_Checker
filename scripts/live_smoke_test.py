from src.config import load_config
from src.fixtures import SYNTHETIC_INCIDENTS
from src.semantic_extractor import extract_semantic_envelope
from src.semantic_validation import validate_semantic_candidate


def main() -> int:
    config = load_config()
    case = next(
        item["incident"]
        for item in SYNTHETIC_INCIDENTS
        if item["incident"].incident_id == "CASE_008"
    )

    result = extract_semantic_envelope(case, config=config)
    print(f"status={result.status.value}")

    if result.semantic_candidate is not None:
        validation = validate_semantic_candidate(
            result.semantic_candidate,
            incident_id=case.incident_id,
            normalized_narrative=case.narrative,
        )
        if validation.validated_envelope is not None:
            print(validation.validated_envelope.envelope.model_dump_json())
        return 0

    print(result.failure_message or "semantic extraction failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
