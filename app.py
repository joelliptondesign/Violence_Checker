import streamlit as st
from typing import Optional, Tuple

from src.app_logic import (
    AnalysisResult,
    active_narrative_signature,
    create_manual_incident,
    is_stale_result,
    run_analysis,
    should_display_analysis_result,
)
from src.contracts import InputValidationResult
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Incident
from src.presentation import (
    policy_explanation,
    policy_outcome_label,
    policy_reason_explanations,
    validation_summary,
)
from src.semantic_extractor import SemanticExtractionStatus


ALIGNMENT_LABELS = {
    "aligned_positive": "Classification aligned: regex and semantic extraction both indicate violence-related content.",
    "aligned_negative": "Classification aligned: neither output indicates violence-related content.",
    "regex_positive_semantic_negative": "Classification divergence: regex positive, semantic negative.",
    "regex_negative_semantic_positive": "Classification divergence: regex negative, semantic positive.",
    "semantic_failure": "Semantic comparison unavailable.",
}


def _fixture_label(item: dict) -> str:
    incident = item["incident"]
    scenario = item["metadata"]["scenario_type"]
    return f"{incident.incident_id} - {scenario}"


def _selected_incident() -> Tuple[Optional[Incident], Optional[str]]:
    st.header("Narrative source")
    st.caption("Select a fixture or enter a manual narrative, then press Run Analysis.")
    mode = st.radio(
        "Narrative source",
        ["Synthetic fixture", "Manual narrative"],
        horizontal=True,
        index=None,
        label_visibility="collapsed",
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

    if mode is None:
        return None, None

    manual_text = st.text_area(
        "Manual narrative",
        height=140,
        placeholder="Enter a local demonstration narrative...",
    )
    if not manual_text.strip():
        return None, None
    return create_manual_incident(manual_text), "manual narrative"


def _display_regex_details(regex_result: dict) -> None:
    st.markdown("**Regex baseline**")
    st.caption("Illustrative lexical-only baseline; not Rochester Regional logic.")
    st.write(f"Detected: {regex_result['detected']}")
    st.write("Matched terms")
    st.write(regex_result["matched_terms"] or [])
    st.write("Matched patterns")
    st.code("\n".join(regex_result["matched_patterns"]) or "No patterns matched")


def _display_semantic_details(semantic_result, validation_result) -> None:
    st.markdown("**Semantic extraction and validation**")
    st.write(f"Result category: {semantic_result.status.value}")
    st.write(f"Validation stage: {validation_result.failure_stage.value}")
    st.write(f"Schema validation status: {validation_result.schema_validation.status.value}")
    st.write(f"Domain validation status: {validation_result.domain_validation.status.value}")

    if semantic_result.status != SemanticExtractionStatus.SUCCESS:
        st.write(f"Failure detail: {semantic_result.failure_message or 'Semantic extraction failed.'}")
        return

    if not validation_result.passed or validation_result.validated_facts is None:
        stage = validation_result.failure_stage.value
        issues = (
            validation_result.schema_validation.issues
            if stage == "schema"
            else validation_result.domain_validation.issues
        )
        st.write(f"Semantic {stage} validation failed.")
        for issue in issues:
            st.write(f"- {issue.code.value}: {issue.message}")
        return

    facts = validation_result.validated_facts.facts
    st.write(f"Violence present: {facts.violence_present}")
    st.write(f"Event type: {facts.event_type.value}")
    st.write(f"Actor: {facts.actor}")
    st.write(f"Target: {facts.target}")
    st.write(f"Contact occurred: {facts.contact_occurred}")
    st.write(f"Injury mentioned: {facts.injury_mentioned}")
    st.write(f"Current event: {facts.current_event}")
    st.write(f"Intentionality: {facts.intentionality.value}")
    st.write(f"Negation: {facts.negated}")
    st.write(f"Correction: {facts.correction_present}")
    st.write(f"Conflicting information: {facts.conflicting_information}")
    st.write(f"Confidence: {facts.confidence}")

    st.write("Evidence excerpts")
    st.write(facts.evidence_text or [])

    st.write("Uncertainty notes")
    st.write(facts.uncertainty_notes or [])


def _display_validation(validation_result) -> None:
    st.header("Validation")
    summary = validation_summary(validation_result)
    if validation_result.passed:
        st.success(summary)
    else:
        st.error(summary)


def _display_policy_details(decision) -> None:
    st.markdown("**Policy**")
    st.write(f"Policy identifier: {decision.policy_id}")
    st.write(f"Policy version: {decision.policy_version}")
    st.write(f"Internal outcome: {decision.outcome.value}")
    st.write(f"Reason codes: {[reason.value for reason in decision.reason_codes]}")
    st.write(f"Internal explanation: {decision.explanation}")
    if decision.failure_provenance is not None:
        st.write(f"Failure provenance: {decision.failure_provenance.value}")


def _display_policy(decision, *, include_technical_details: bool = True) -> None:
    st.header("AI Assessment")
    st.subheader(policy_outcome_label(decision))
    st.write(policy_explanation(decision))
    st.markdown("**Why this result**")
    for explanation in policy_reason_explanations(decision):
        st.write(f"- {explanation}")

    if include_technical_details:
        with st.expander("Technical Details", expanded=False):
            _display_policy_details(decision)


def _display_technical_details(result) -> None:
    with st.expander("Technical Details", expanded=False):
        _display_regex_details(result.regex_result)
        _display_semantic_details(result.semantic_result, result.validation_result)
        if result.compatibility_result is None:
            st.write("Compatibility construction: not available")
        else:
            st.write(
                f"Compatibility construction: {result.compatibility_result.status.value}"
            )
        _display_policy_details(result.policy_decision)


def _display_results(result) -> None:
    _display_validation(result.validation_result)
    _display_policy(result.policy_decision, include_technical_details=False)

    st.header("Comparison")
    if result.comparison.display_status == "Material Difference Detected":
        st.warning(result.comparison.display_status)
    elif result.comparison.display_status == "Semantic Comparison Unavailable":
        st.error(result.comparison.display_status)
    elif result.comparison.display_status == "Classification Aligned, Semantic Context Added":
        st.info(result.comparison.display_status)
    else:
        st.success(result.comparison.display_status)

    st.write(
        ALIGNMENT_LABELS.get(
            result.comparison.classification_alignment,
            result.comparison.classification_alignment,
        )
    )

    if result.comparison.divergence_observations:
        st.markdown("**Classification divergence**")
        for observation in result.comparison.divergence_observations:
            st.write(f"- {observation}")

    if result.comparison.semantic_enrichment_observations:
        st.markdown("**Semantic enrichment**")
        for observation in result.comparison.semantic_enrichment_observations:
            st.write(f"- {observation}")

    if not result.comparison.material_difference_detected:
        for observation in result.comparison.observations:
            st.write(f"- {observation}")

    st.header("Salesforce Preview")
    st.caption("Deterministic preview only. No Salesforce integration is performed.")
    if result.salesforce_preview is None:
        st.info("Preview is available only after successful validated semantic extraction.")
    else:
        st.json(result.salesforce_preview)

    _display_technical_details(result)


def main() -> None:
    st.title("Phase 0 Semantic Violence Detection Pre-PoC")
    st.write(
        "Synthetic local pre-PoC for comparing an illustrative regex baseline with validated semantic extraction."
    )

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
            analysis_outcome = run_analysis(incident)
        if isinstance(analysis_outcome, InputValidationResult):
            st.error(analysis_outcome.failure_message or "Incident input is invalid.")
            if analysis_outcome.policy_decision is not None:
                _display_policy(analysis_outcome.policy_decision)
            st.session_state.pop("analysis_result", None)
            st.session_state.pop("analysis_signature", None)
        else:
            analysis_result: AnalysisResult = analysis_outcome
            st.session_state["analysis_result"] = analysis_result
            st.session_state["analysis_signature"] = analysis_result.signature

    result = st.session_state.get("analysis_result")
    if should_display_analysis_result(st.session_state.get("analysis_signature"), active_signature) and result is not None:
        _display_results(result)


if __name__ == "__main__":
    main()
