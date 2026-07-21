"""Deterministic, repository-specific SITREC generation for Violence_Checker.

Generation is intentionally separate from generic governance validation.  The
generator converts a bounded set of repository facts into a complete
rehydration artifact; validators remain report-only consumers of the result.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .sitrec_router import (
    ARCHIVE_PATH,
    DECISION_UPDATE_CURRENT,
    extract_date,
    extract_document_date,
    route_sitrec,
)


DEFAULT_TITLE = "Violence Checker Successor Semantic Baseline"
CORPUS_PATH = Path("evaluation/corpus/successor_corpus.json")

GROUNDING_ANCHORS = (
    ("README.md", "Repository purpose, local execution, and operator entry points."),
    ("docs/architecture.md", "Current end-to-end architecture and authority boundaries."),
    ("docs/local_governance.md", "Repository-local generation, validation, and readiness commands."),
    ("docs/opord_004_verification_authority.md", "Permanent successor verification gates and test authority."),
    ("docs/semantic_design_basis.md", "Historical proposition design record; not current authority."),
    ("docs/successor_semantic_contract_specification.md", "Historical proposition successor specification."),
    ("docs/workplace_violence_doctrine.md", "Authoritative doctrine for the active True North runtime and evaluation."),
    ("docs/true_north_semantic_contract_specification.md", "Implemented incident-fact contract and evidence-integrity authority."),
    ("docs/true_north_migration_strategy.md", "Approved replacement order and remaining acceptance gates."),
    ("src/contracts.py", "Provider-independent semantic and pipeline contracts."),
    ("src/provider_adapter.py", "Provider boundary and conversion into repository contracts."),
    ("src/semantic_validation.py", "Schema admissibility enforcement."),
    ("src/domain_validation.py", "Violence-domain admissibility enforcement."),
    ("src/semantic_derivation.py", "Deterministic derived semantic views."),
    ("src/policy.py", "Sole deterministic illustrative disposition authority."),
    ("src/app_logic.py", "Application orchestration and request boundary."),
    ("src/operator_communication.py", "Narrative-free communication projection and deterministic fallback."),
    ("src/operator_communication_provider.py", "Presentation-only structured communication request boundary."),
    ("src/operator_communication_prompt.py", "Executive communication instructions."),
    ("src/presentation.py", "Executive comparison and Salesforce presentation projections."),
    ("app.py", "Executive information architecture and component ownership."),
    ("src/evaluation/", "Current evaluation contracts, execution, comparison, and reporting."),
    (CORPUS_PATH.as_posix(), "Repository-authored True North operational evaluation ground truth."),
    ("tests/", "Permanent deterministic behavioral verification authority."),
    ("tools/repo_governance/", "Supporting repository governance and SITREC generation tooling."),
)


@dataclass(frozen=True)
class SitrecFacts:
    operational_date: str
    case_count: int
    corpus_identity: str
    corpus_schema_version: str
    semantic_schema_identity: str
    semantic_schema_version: str
    prior_sitrecs: tuple[str, ...]


def validate_operational_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"SITREC date must be ISO YYYY-MM-DD: {value}") from error
    return parsed.isoformat()


def default_output_path(operational_date: str, title: str = DEFAULT_TITLE) -> Path:
    normalized_date = validate_operational_date(operational_date)
    return Path("docs") / f"SITREC - {normalized_date} {title}.md"


def _required_path(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.exists():
        raise ValueError(f"required SITREC grounding anchor is missing: {relative}")
    return path


def collect_sitrec_facts(root: Path, operational_date: str) -> SitrecFacts:
    normalized_date = validate_operational_date(operational_date)
    for relative, _description in GROUNDING_ANCHORS:
        _required_path(root, relative)

    corpus = json.loads(_required_path(root, CORPUS_PATH.as_posix()).read_text(encoding="utf-8"))
    cases = corpus.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{CORPUS_PATH.as_posix()} has no non-empty cases array")

    candidates = [*(root / "docs").glob("*SITREC*.md"), *(root / ARCHIVE_PATH).glob("*SITREC*.md")]
    prior_sitrecs = tuple(
        path.relative_to(root).as_posix()
        for path in sorted(candidates, key=lambda item: item.relative_to(root).as_posix())
        if extract_date(path) != normalized_date
    )
    return SitrecFacts(
        operational_date=normalized_date,
        case_count=len(cases),
        corpus_identity=str(corpus.get("corpus_identity", "missing")),
        corpus_schema_version=str(corpus.get("corpus_schema_version", "missing")),
        semantic_schema_identity=str(corpus.get("semantic_schema_identity", "missing")),
        semantic_schema_version=str(corpus.get("semantic_schema_version", "missing")),
        prior_sitrecs=prior_sitrecs,
    )


def _prior_sitrec_text(facts: SitrecFacts) -> str:
    if not facts.prior_sitrecs:
        return "No prior top-level SITREC is present."
    paths = ", ".join(f"`{path}`" for path in facts.prior_sitrecs)
    return f"Prior top-level SITRECs ({paths}) are historical provenance, not coequal current authorities."


def _grounding_table() -> str:
    rows = ["| Repository anchor | Grounded authority |", "| --- | --- |"]
    rows.extend(f"| `{path}` | {description} |" for path, description in GROUNDING_ANCHORS)
    return "\n".join(rows)


def render_sitrec(root: Path, operational_date: str, title: str = DEFAULT_TITLE) -> str:
    """Render a complete SITREC from repository-local, deterministic facts."""
    facts = collect_sitrec_facts(root, operational_date)
    sections = (
        (
            "A. SYSTEM IDENTITY",
            "Repository: `Violence_Checker`. This is a non-production local Python and Streamlit demonstration using the current True North incident-fact semantic authority, deterministic workplace-violence policy, and operational evaluation framework.",
        ),
        (
            "B. CURRENT STATE",
            f"Current repository facts: `TrueNorthSemanticEnvelope` is the sole current semantic authority. The True North runtime is active across extraction, repository adaptation, schema and domain validation, deterministic derivation and policy, application orchestration, comparison, illustrative Salesforce projection, bounded Operator Communication, presentation, and Streamlit. The repository-authored `{facts.corpus_identity}` contains {facts.case_count} synthetic operational cases under evaluation schema `{facts.corpus_schema_version}`, explicit expectations for all eight demonstration fixtures, and adversarial evidence-integrity coverage. Historical evaluation artifacts remain immutable, readable through their creation-time family, and non-authoritative. Live-provider evaluation, baseline acceptance, deployment, and hosted acceptance remain pending.",
        ),
        (
            "C. CORE INVARIANTS",
            "- Raw free-form narrative is the evidence authority; normalization is formatting-only.\n- Exactly one semantic extraction request is permitted per valid explicit analysis or selected live evaluation case; non-analysis interactions and invalid input issue zero provider requests.\n- Provider authority is limited to semantic candidates with temporary local references; provider SDK objects terminate at the adapter boundary.\n- Repository code owns identity, canonical ordering and references, processing and completeness status, validation, derivation, deterministic policy, and downstream representation.\n- Schema and domain validation fail closed before policy.\n- Evaluation compares only deterministic outcomes, operational facts, supported evidence, processing/completeness status, and doctrine compliance.\n- Operator Communication is presentation-only and cannot change repository authority.\n- No retries, semantic repair, silent semantic defaults, output-derived ground truth, compatibility reconstruction, or dual current semantic authority is permitted.\n- Historical evaluation artifacts remain byte-immutable and cannot become active True North authority.",
        ),
        (
            "D. SYSTEM MODEL",
            "`input validation` → formatting-only normalization → lexical baseline plus one structured operational-fact extraction → repository adapter → schema and domain/evidence validation → deterministic semantic views → four-outcome policy → comparison and illustrative Salesforce projection → bounded communication and presentation; offline evaluation compares the resulting repository truth against doctrine-authored operational expectations.",
        ),
        (
            "E. AUTHORITY MODEL",
            "| Component | Authority |\n| --- | --- |\n| True North operational corpus | Doctrine-authored deterministic evaluation expectations |\n| Raw narrative | Free-form evidence and excerpt-containment authority |\n| Provider | Bounded candidate operational facts with temporary references only |\n| Contract adapter | Provider termination and repository-owned identity/order/reference mapping |\n| Schema/domain validators | Admissibility and fail-closed rejection |\n| Semantic derivation | Active/superseded sets, contradiction membership, and incident direction |\n| Deterministic policy | Sole authority for the four doctrinal outcomes |\n| Operator Communication | Presentation-only projection with no semantic or policy authority |\n| Historical artifacts | Immutable creation-time evidence; non-authoritative for True North |\n| Tests | Permanent deterministic behavioral verification |\n| Governance tooling | Deterministic continuity and freshness checks; never application truth |",
        ),
        (
            "F. DATA / CONTRACT MODEL",
            f"Semantic schema `{facts.semantic_schema_identity}` version `{facts.semantic_schema_version}` defines one ordered operational fact collection with conduct, atomic direction, intentionality, temporal scope, assertion and resolution status, explicit uncertainty, fact-local evidence, and narrow correction or contradiction references. `PipelineResult` carries validation status, deterministic views, the four-outcome policy result, and optional illustrative Salesforce payload. Evaluation schema `{facts.corpus_schema_version}` compares only operational doctrine truth and has no proposition, entity, relationship, PolicyCandidateView, or retired pipeline-failure dependency. Recognized creation-time artifacts use schema `1.0.0` and remain readable but incomparable and non-authoritative.",
        ),
        (
            "G. SYSTEM BOUNDARIES",
            "The repository does not provide a real Salesforce connection or write, clinical decision support, legal or safety determination, hospital workflow, PHI handling, external persistence, authentication, customer-authority control, or FoxCommand Runtime integration. Use is restricted to synthetic demonstration data; real patient, PHI, confidential, or production incident data must not be submitted. Streamlit Community Cloud deployment remains a manual operator follow-on; no hosted deployment, hosted URL, or hosted acceptance is claimed. Provider types, provider metadata authority, and provider-authored disposition do not cross the provider boundary.",
        ),
        (
            "H. CURRENT CAPABILITIES",
            f"The app accepts fixtures and bounded free-form narratives, applies total deterministic policy, and builds policy-gated presentation projections. Technical details expose operational facts and supporting evidence without retired graph structures. Offline True North evaluation validates {facts.case_count} cases spanning threats, attempts, contact, self-harm, property violence, exclusions, corrections, contradictions, uncertainty, mixed directions, and adversarial evidence integrity. All eight demonstration fixtures have explicit outcome, conduct, direction, uncertainty, processing, and completeness expectations. Runs, within-family regression comparison, and reporting use evaluation schema `{facts.corpus_schema_version}`; accepting a new baseline remains a separate operator action.",
        ),
        (
            "I. KNOWN LIMITATIONS",
            "The lexical baseline is intentionally shallow. Provider quality is not guaranteed, and deterministic validation cannot prove unrestricted natural-language entailment. Live-provider evaluation is pending and non-deterministic even though its surrounding contracts are deterministic. No True North evaluation baseline has been accepted. Deployment and hosted acceptance have not occurred. Historical and True North artifact families remain intentionally incomparable.",
        ),
        (
            "J. INTERACTION MODEL",
            "Analysis begins only after explicit `Run Analysis`; invalid input and non-analysis interaction issue no semantic requests. A valid analysis performs lexical matching and one semantic extraction with SDK retries disabled. Communication generation is a separate presentation-only request and failure preserves deterministic fallback. Deterministic evaluation requires an injected executor and sends only case identity and narrative; live-provider evaluation is explicit and pending. Baseline acceptance and deployment are separate operator actions and never occur during evaluation or governance validation.",
        ),
        (
            "K. GUARANTEES",
            "Strict contracts reject malformed or inadmissible semantics before policy. Provider metadata cannot override deterministic repository bookkeeping. Policy is total over admissible states. Operator Communication cannot alter validation, policy, comparison, Salesforce eligibility, or Salesforce payload content, and deterministic fallback remains available when communication generation fails. Collections and serialized current artifacts have canonical ordering. Successor baseline acceptance rejects legacy runs. Existing governed artifact paths are protected from implicit overwrite. Repository generation is deterministic for the same operational date and repository state.",
        ),
        (
            "L. NON-GUARANTEES",
            "The repository does not guarantee model accuracy, exhaustive violence ontology coverage, production suitability, PHI-safe operation, human-review workflow, external-system persistence, hosted availability or acceptance, cross-schema semantic equivalence, or that governance validation proves application truth.",
        ),
        ("M. GROUNDING ANCHORS", _grounding_table()),
        (
            "N. SOURCE OF TRUTH RULE",
            "Repository state is authoritative. If this SITREC conflicts with code, contracts, corpus validation, tests, or deterministic governance output, the repository wins and this SITREC must be regenerated or corrected. The SITREC summarizes repository truth; it never supersedes it.",
        ),
        (
            "O. REHYDRATION INSTRUCTIONS",
            "1. Read `README.md`, `docs/architecture.md`, this SITREC, `docs/local_governance.md`, `docs/opord_004_verification_authority.md`, `docs/workplace_violence_doctrine.md`, `docs/true_north_semantic_contract_specification.md`, and `docs/true_north_migration_strategy.md`.\n2. Inspect the True North contracts, adapter, validation/derivation/policy chain, application and presentation runtime, `src/evaluation/`, and `evaluation/corpus/successor_corpus.json`.\n3. Inspect `git status --short` before mutation and preserve unrelated work.\n4. Run `python3 -m tools.repo_governance validate-all`; for readiness run `python3 -m tools.repo_governance baseline-readiness` without accepting a baseline.\n5. Preserve provider operational-fact authority, repository bookkeeping, request boundaries, fail-closed validation, deterministic policy, active True North evaluation, and historical artifact immutability.\n6. Treat live-provider evaluation, baseline acceptance, deployment, and hosted acceptance as separately authorized follow-on actions.\n7. Regenerate this artifact with the governed `sitrec` command whenever repository truth changes.",
        ),
        (
            "P. SITREC LIFECYCLE",
            f"This `{facts.operational_date}` record is the sole active top-level rehydration artifact. {_prior_sitrec_text(facts)} `America/Los_Angeles` determines the operational date. Routing occurs before every mutation: update the current-date record, or archive stale active records under `docs/archive/sitrecs/` before creating the current-date record.",
        ),
        (
            "Q. DAILY UNIQUENESS",
            f"Exactly one lifecycle-managed SITREC may represent `{facts.operational_date}` across active and archived records. The active generator target is `docs/SITREC - {facts.operational_date} {title}.md`; repeated same-day generation updates that record rather than creating a duplicate.",
        ),
        (
            "R. VALIDATION",
            "Generation and validation are separate responsibilities. After generation run `python3 -m tools.repo_governance validate-sitrec --path \"<generated path>\"`, `python3 -m tools.repo_governance validate-all`, and `python3 -m tools.repo_governance validate-heartbeat`. Baseline establishment additionally requires `python3 -m tools.repo_governance baseline-readiness`, protected-hash checks, generated-artifact freshness, and a clean committed Git state.",
        ),
        (
            "S. PLANNER / EXECUTOR RESPONSIBILITY MODEL",
            "Planner authority determines operational meaning, current-state synthesis, invariants, boundaries, and continuation guidance. Executor authority implements deterministic generation and validation infrastructure, performs only authorized mutations, preserves protected evidence, records required telemetry, and reports repository-grounded findings. Validation reports drift; it does not invent or override system truth.",
        ),
    )

    lines = [
        f"# SITREC - {facts.operational_date} {title}",
        "",
        "<!-- Generated by `python3 -m tools.repo_governance sitrec`; edit the generator profile when repository truth changes. -->",
        "",
        f"Operational Date: `{facts.operational_date}`",
        "Generation Inputs: repository paths declared in `tools/repo_governance/sitrec.py`; no network or provider execution.",
        "",
    ]
    for heading, body in sections:
        lines.extend((f"## {heading}", "", body, ""))
    return "\n".join(lines).rstrip() + "\n"


def _lifecycle_paths(root: Path) -> list[Path]:
    active = [path for path in (root / "docs").glob("*.md") if "sitrec" in path.name.lower()]
    archived = [path for path in (root / ARCHIVE_PATH).glob("*.md") if "sitrec" in path.name.lower()]
    return sorted([*active, *archived], key=lambda path: path.relative_to(root).as_posix())


def _validate_lifecycle_records(root: Path) -> None:
    by_date: dict[str, list[Path]] = {}
    for path in _lifecycle_paths(root):
        filename_date = extract_date(path)
        if filename_date is None:
            raise ValueError(f"SITREC filename has no valid operational date: {path.relative_to(root)}")
        document_date = extract_document_date(path.read_text(encoding="utf-8"))
        if document_date is None:
            raise ValueError(f"SITREC document has no valid Operational Date: {path.relative_to(root)}")
        if document_date != filename_date:
            raise ValueError(
                f"SITREC filename date {filename_date} disagrees with document Operational Date "
                f"{document_date}: {path.relative_to(root)}"
            )
        by_date.setdefault(filename_date, []).append(path)
    duplicates = {value: paths for value, paths in by_date.items() if len(paths) > 1}
    if duplicates:
        value = sorted(duplicates)[0]
        paths = ", ".join(path.relative_to(root).as_posix() for path in duplicates[value])
        raise ValueError(f"duplicate SITREC operational date {value}: {paths}")


def write_sitrec(
    root: Path,
    operational_date: str,
    output: Path | None = None,
    title: str = DEFAULT_TITLE,
    replace: bool = False,
) -> dict[str, object]:
    """Route, normalize, and generate the Pacific-date SITREC as one mutation stage."""
    root = root.resolve()
    normalized_date = validate_operational_date(operational_date)
    route = route_sitrec(root, normalized_date)
    _validate_lifecycle_records(root)

    current = [candidate for candidate in route.active_sitrecs if candidate.operational_date == normalized_date]
    if len(current) > 1:
        raise ValueError(f"multiple active SITRECs exist for {normalized_date}")

    expected_target = current[0].path if current else root / default_output_path(normalized_date, title)
    if output is not None and (root / output).resolve() != expected_target.resolve():
        raise ValueError(f"SITREC output must match routed target: {expected_target.relative_to(root)}")

    stale = [candidate.path for candidate in route.active_sitrecs if candidate.operational_date != normalized_date]
    archive_moves = [(path, root / ARCHIVE_PATH / path.name) for path in stale]
    for source, destination in archive_moves:
        if destination.exists():
            raise ValueError(
                f"refusing to overwrite archived SITREC: {destination.relative_to(root).as_posix()}"
            )

    # Verify deterministic inputs before beginning the filesystem mutation.
    collect_sitrec_facts(root, normalized_date)
    if archive_moves:
        (root / ARCHIVE_PATH).mkdir(parents=True, exist_ok=True)
        for source, destination in archive_moves:
            source.replace(destination)

    content = render_sitrec(root, normalized_date, title)
    expected_target.parent.mkdir(parents=True, exist_ok=True)
    existed = expected_target.exists()
    expected_target.write_text(content, encoding="utf-8")
    relative = expected_target.relative_to(root)
    return {
        "path": relative.as_posix(),
        "operational_date": normalized_date,
        "sections": 19,
        "bytes": len(content.encode("utf-8")),
        "replaced": existed or route.decision == DECISION_UPDATE_CURRENT,
        "router_decision": route.decision,
        "archived": [destination.relative_to(root).as_posix() for _source, destination in archive_moves],
    }
