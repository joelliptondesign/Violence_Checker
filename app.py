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
from src.contracts import InputValidationResult, PolicyOutcome
from src.fixtures import SYNTHETIC_INCIDENTS
from src.models import Incident
from src.operator_communication_provider import generate_operator_communication
from src.presentation import (
    extracted_entity_rows,
    policy_outcome_label,
    policy_reason_explanations,
    salesforce_operator_rows,
    salesforce_payload_rows,
    validated_evidence_excerpts,
)


DECISION_LOGIC_EXPLANATION = (
    "The application reviewed who was involved, what happened, whether the conduct was "
    "intentional, and whether it occurred during the current incident. It then applied the "
    "workplace violence criteria to those confirmed details."
)


def _fixture_label(item: dict) -> str:
    incident = item["incident"]
    scenario = item["metadata"]["scenario_type"]
    return f"{incident.incident_id} - {scenario}"


def _selected_incident() -> Tuple[Optional[Incident], Optional[str]]:
    st.header("Incident Narrative")
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
        placeholder="Enter an incident narrative...",
    )
    if not manual_text.strip():
        return None, None
    return create_manual_incident(manual_text), "manual narrative"


def _display_operator_communication(communication) -> None:
    st.markdown("### Incident Summary")
    st.write(communication.incident_summary)
    st.markdown("### Key Findings")
    for finding in communication.key_findings:
        st.write(f"- {finding}")
    st.markdown("### Why This Result")
    st.write(communication.why_this_result)


def _display_regex_operator_view(regex_result: dict) -> None:
    st.header("Regex Keyword Detection")
    st.caption(
        "Traditional regular expression (regex) matching scans the incident narrative for predefined words and phrases."
    )
    detected = bool(regex_result.get("detected"))
    st.subheader("Potential Match" if detected else "No Match")
    st.markdown("**Evidence**")
    matched_terms = regex_result.get("matched_terms", [])
    if matched_terms:
        for term in matched_terms:
            st.write(f"- “{term}”")
    else:
        st.write("No configured keyword or phrase was detected.")
    st.markdown("**Limitations**")
    st.write("- Searches for matching words rather than the overall meaning.")
    st.write("- May miss important context or flag words used in a different way.")


def _display_regex_technical_details(regex_result: dict) -> None:
    with st.expander("Technical Details", expanded=False):
        st.html('<span class="regex-technical-details-marker" hidden></span>')
        st.markdown("**Keyword Matching**")
        st.write("The detector compares the narrative against predefined regular-expression patterns.")
        st.markdown("**Detected**")
        st.write("Yes" if regex_result.get("detected") else "No")
        st.markdown("**Matched Terms**")
        if regex_result.get("matched_terms"):
            for term in regex_result["matched_terms"]:
                st.write(f"- {term}")
        else:
            st.write("None")
        st.markdown("**Matched Patterns**")
        if regex_result.get("matched_patterns"):
            for pattern in regex_result["matched_patterns"]:
                st.write(f"- `{pattern}`")
        else:
            st.write("None")


def _display_ai_operator_view(result) -> None:
    st.header("AI-Powered Semantic Analysis")
    st.caption(
        "Reviews the incident as a whole, including who was involved, what occurred, and whether the reported conduct meets the workplace violence criteria."
    )
    st.subheader(policy_outcome_label(result.policy_decision))
    if result.policy_decision.outcome == PolicyOutcome.WRITE_FAILED:
        st.error(policy_reason_explanations(result.policy_decision)[0])
    elif result.communication is not None:
        _display_operator_communication(result.communication)


def _display_ai_technical_details(result) -> None:
    with st.expander("Technical Details", expanded=False):
        st.html('<span class="ai-technical-details-marker" hidden></span>')
        st.markdown("**Extracted Entities**")
        rows = extracted_entity_rows(result.validation_result)
        if rows:
            st.table(rows)
        else:
            st.write("No validated entities are available.")

        st.markdown("**Supporting Evidence**")
        evidence = validated_evidence_excerpts(result.validation_result)
        if evidence:
            for excerpt in evidence:
                st.write(f"- “{excerpt}”")
        else:
            st.write("No validated supporting evidence is available.")

        st.markdown("**Decision Logic**")
        st.write(DECISION_LOGIC_EXPLANATION)
        validated = result.validation_result.validated_envelope
        summary_lines = ["incident_facts:"]
        if validated is None:
            summary_lines.append("  confirmed_details_available: false")
        else:
            active_ids = set(validated.derived.active_proposition_ids)
            active_facts = [
                item for item in validated.envelope.propositions
                if item.proposition_id in active_ids
            ]
            direction_values = {
                item.direction.value
                for item in validated.derived.propositions
                if item.active
            }
            temporal_values = {item.temporal_scope.value for item in active_facts}
            intentionality_values = {item.intentionality.value for item in active_facts}
            contact_values = {item.contact.value for item in active_facts}
            assertion_values = {item.assertion_status.value for item in active_facts}

            current_incident = "not_applicable"
            if temporal_values:
                current_incident = "uncertain" if "undetermined" in temporal_values else "false"
                if "current_incident" in temporal_values:
                    current_incident = "uncertain" if "historical" in temporal_values else "true"

            interpersonal_conduct = "not_applicable"
            if direction_values:
                interpersonal_conduct = "uncertain" if "undetermined" in direction_values else "false"
                if "interpersonal" in direction_values:
                    interpersonal_conduct = "true"

            intentional_conduct = "not_applicable"
            if intentionality_values != {"not_applicable"}:
                intentional_conduct = "uncertain" if "undetermined" in intentionality_values else "false"
                if "intentional" in intentionality_values:
                    intentional_conduct = "true"

            physical_contact = "not_applicable"
            if contact_values != {"not_applicable"}:
                physical_contact = "uncertain" if "undetermined" in contact_values else "false"
                if "occurred" in contact_values:
                    physical_contact = (
                        "uncertain" if "did_not_occur" in contact_values else "true"
                    )

            assertion_confirmed = "not_applicable"
            if assertion_values:
                assertion_confirmed = "uncertain" if "uncertain" in assertion_values else "false"
                if "affirmed" in assertion_values:
                    assertion_confirmed = "uncertain" if "negated" in assertion_values else "true"

            entity_kinds = {item.entity_kind.value for item in validated.envelope.entities}
            summary_lines.extend(
                (
                    f"  participants_identified: {'true' if bool(entity_kinds & {'person', 'people_collective'}) else 'false'}",
                    f"  occurred_during_current_incident: {current_incident}",
                    f"  involved_another_person: {interpersonal_conduct}",
                    f"  conduct_was_intentional: {intentional_conduct}",
                    f"  physical_contact_occurred: {physical_contact}",
                    f"  reported_conduct_supported: {assertion_confirmed}",
                    "  conflicting_accounts: "
                    f"{'true' if validated.policy_candidate.active_conflict_relationships else 'false'}",
                )
            )
        summary_lines.extend(
            (
                "result:",
                f"  workplace_violence_assessment: {policy_outcome_label(result.policy_decision)}",
            )
        )
        st.code("\n".join(summary_lines), language="yaml")


def _display_salesforce_record(payload: dict[str, object]) -> None:
    st.header("Illustrative Salesforce Record")
    st.table(salesforce_operator_rows(payload))
    with st.expander("Salesforce Payload Details", expanded=False):
        st.html('<span class="salesforce-payload-details-marker" hidden></span>')
        st.table(salesforce_payload_rows(payload))


def _display_salesforce_empty_state() -> None:
    st.header("Illustrative Salesforce Record")
    st.write("No record generated for this result.")


def _display_results(result) -> None:
    st.html(
        """
        <style>
        .stApp { overflow-x: hidden; }
        [data-testid="stCode"] pre { white-space: pre-wrap; overflow-wrap: anywhere; }
        @media (max-width: 640px) {
          div[data-testid="stHorizontalBlock"]:has(.result-order-marker)
            > div[data-testid="stColumn"]:has(.semantic-result-marker) { order: 1; }
          div[data-testid="stHorizontalBlock"]:has(.result-order-marker)
            > div[data-testid="stColumn"]:has(.regex-result-marker) { order: 2; }
        }
        </style>
        """
    )
    regex_column, semantic_column = st.columns(2)
    with regex_column:
        st.html('<span class="result-order-marker regex-result-marker" hidden></span>')
        _display_regex_operator_view(result.regex_result)
        _display_regex_technical_details(result.regex_result)

    with semantic_column:
        st.html('<span class="result-order-marker semantic-result-marker" hidden></span>')
        _display_ai_operator_view(result)
        _display_ai_technical_details(result)

    if result.salesforce_preview is None:
        _display_salesforce_empty_state()
    else:
        _display_salesforce_record(result.salesforce_preview)


def main() -> None:
    st.title("Workplace Safety Intelligence")
    st.write(
        "AI reviews incident narratives to identify potential workplace violence, explain the reasoning, and support more consistent safety reporting."
    )

    incident, scenario_label = _selected_incident()

    if incident is None:
        st.write("No active incident selected.")
        st.session_state.pop("analysis_result", None)
        st.session_state.pop("analysis_signature", None)
        return

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
        with st.spinner("Analyzing the incident narrative..."):
            analysis_outcome = run_analysis(
                incident,
                communicator=generate_operator_communication,
            )
        if isinstance(analysis_outcome, InputValidationResult):
            st.error(analysis_outcome.failure_message or "Incident input is invalid.")
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
