import streamlit as st
from typing import Optional, Tuple

from src.app_logic import (
    active_narrative_signature,
    create_manual_incident,
    is_stale_result,
    run_analysis,
    should_display_analysis_result,
)
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Incident
from src.semantic_extractor import SemanticExtractionStatus


def _fixture_label(item: dict) -> str:
    incident = item["incident"]
    scenario = item["metadata"]["scenario_type"]
    return f"{incident.incident_id} - {scenario}"


def _selected_incident() -> Tuple[Optional[Incident], Optional[str]]:
    mode = st.radio(
        "Narrative source",
        ["Select a source", "Synthetic fixture", "Manual narrative"],
        horizontal=True,
    )

    if mode == "Synthetic fixture":
        fixture = st.selectbox(
            "Synthetic case",
            SYNTHETIC_INCIDENTS,
            format_func=_fixture_label,
            index=None,
            placeholder="Choose CASE_001 through CASE_008",
        )
        if fixture is None:
            return None, None
        incident = fixture["incident"]
        return incident, fixture["metadata"]["scenario_type"]

    if mode == "Select a source":
        return None, None

    manual_text = st.text_area(
        "Manual narrative",
        height=140,
        placeholder="Enter a local demonstration narrative...",
    )
    if not manual_text.strip():
        return None, None
    return create_manual_incident(manual_text), "manual narrative"


def _display_regex(regex_result: dict) -> None:
    st.header("Regex Baseline")
    st.caption("Illustrative lexical-only baseline; not Rochester Regional logic.")
    st.write(f"Detected: {regex_result['detected']}")
    st.write("Matched terms")
    st.write(regex_result["matched_terms"] or [])
    st.write("Matched patterns")
    st.code("\n".join(regex_result["matched_patterns"]) or "No patterns matched")


def _display_semantic(result) -> None:
    st.header("Semantic Extraction")
    st.write(f"Result category: {result.status.value}")

    if result.status != SemanticExtractionStatus.SUCCESS:
        st.error(result.failure_message or "Semantic extraction failed.")
        return

    finding = result.finding
    st.write(f"Violence present: {finding.violence_present}")
    st.write(f"Event type: {finding.event_type.value}")
    st.write(f"Actor: {finding.actor}")
    st.write(f"Target: {finding.target}")
    st.write(f"Contact occurred: {finding.contact_occurred}")
    st.write(f"Injury mentioned: {finding.injury_mentioned}")
    st.write(f"Current event: {finding.current_event}")
    st.write(f"Intentionality: {finding.intentionality.value}")
    st.write(f"Negation: {finding.negated}")
    st.write(f"Correction: {finding.correction_present}")
    st.write(f"Conflicting information: {finding.conflicting_information}")
    st.write(f"Confidence: {finding.confidence}")

    st.write("Evidence excerpts")
    st.write(finding.evidence_text or [])

    st.write("Uncertainty notes")
    st.write(finding.uncertainty_notes or [])


def _display_results(result) -> None:
    left, right = st.columns(2)
    with left:
        _display_regex(result.regex_result)
    with right:
        _display_semantic(result.semantic_result)

    st.subheader("Semantic Validation Status")
    st.write(result.comparison.semantic_validation_status)

    st.header("Comparison")
    for observation in result.comparison.observations:
        st.write(f"- {observation}")

    st.header("Salesforce Preview")
    st.caption("Deterministic preview only. No Salesforce integration is performed.")
    if result.salesforce_preview is None:
        st.info("Preview is available only after successful validated semantic extraction.")
    else:
        st.json(result.salesforce_preview)


def main() -> None:
    st.title("Phase 0 Semantic Violence Detection Pre-PoC")
    st.write(
        "Synthetic local pre-PoC for comparing an illustrative regex baseline with validated semantic extraction."
    )
    st.info(
        "Synthetic data only. The regex baseline is illustrative, lexical-only, and not Rochester Regional's actual implementation."
    )
    st.caption("Select a fixture or enter a manual narrative, then press Run Analysis.")

    incident, scenario_label = _selected_incident()

    if incident is None:
        st.header("Incident Narrative")
        st.write("No active incident selected.")
        st.info("Choose a synthetic fixture or enter a non-empty manual narrative before running analysis.")
        st.session_state.pop("analysis_result", None)
        st.session_state.pop("analysis_signature", None)
        return

    st.header("Incident Narrative")
    meta_left, meta_right = st.columns(2)
    with meta_left:
        st.write(f"Case: {incident.incident_id}")
    with meta_right:
        st.write(f"Scenario: {scenario_label}")
    st.text_area("Original narrative used for analysis", incident.narrative, height=130, disabled=True)

    active_signature = active_narrative_signature(incident)
    if is_stale_result(st.session_state.get("analysis_signature"), active_signature):
        st.session_state.pop("analysis_result", None)
        st.session_state.pop("analysis_signature", None)

    if st.button("Run Analysis", type="primary"):
        with st.spinner("Running regex baseline and semantic extraction..."):
            analysis_result = run_analysis(incident)
        st.session_state["analysis_result"] = analysis_result
        st.session_state["analysis_signature"] = analysis_result.signature

    result = st.session_state.get("analysis_result")
    if should_display_analysis_result(st.session_state.get("analysis_signature"), active_signature) and result is not None:
        _display_results(result)


if __name__ == "__main__":
    main()
