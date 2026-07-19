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


DEFAULT_TITLE = "Violence Checker Successor Semantic Baseline"
CORPUS_PATH = Path("evaluation/corpus/successor_corpus.json")

GROUNDING_ANCHORS = (
    ("README.md", "Repository purpose, local execution, and operator entry points."),
    ("docs/architecture.md", "Current end-to-end architecture and authority boundaries."),
    ("docs/local_governance.md", "Repository-local generation, validation, and readiness commands."),
    ("docs/opord_004_verification_authority.md", "Permanent successor verification gates and test authority."),
    ("docs/semantic_design_basis.md", "Approved proposition-oriented semantic design authority."),
    ("docs/successor_semantic_contract_specification.md", "Approved successor contract and admissibility specification."),
    ("src/contracts.py", "Provider-independent semantic and pipeline contracts."),
    ("src/provider_adapter.py", "Provider boundary and conversion into repository contracts."),
    ("src/semantic_validation.py", "Schema admissibility enforcement."),
    ("src/domain_validation.py", "Violence-domain admissibility enforcement."),
    ("src/semantic_derivation.py", "Deterministic derived semantic views."),
    ("src/policy.py", "Sole deterministic illustrative disposition authority."),
    ("src/app_logic.py", "Application orchestration and request boundary."),
    ("src/evaluation/", "Current evaluation contracts, execution, comparison, and reporting."),
    (CORPUS_PATH.as_posix(), "Repository-authored successor ground truth."),
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

    prior_sitrecs = tuple(
        path.relative_to(root).as_posix()
        for path in sorted((root / "docs").glob("SITREC*.md"))
        if normalized_date not in path.name
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
            "Repository: `Violence_Checker`. This is a local Python and Streamlit demonstration of proposition-oriented violence semantics. Its mission is to compare a lexical baseline with structured semantic analysis and produce a deterministic, illustrative disposition. It is non-production. Repository governance supports continuity but does not redefine the application mission.",
        ),
        (
            "B. CURRENT STATE",
            f"Current repository facts: the approved successor architecture is active across provider extraction, deterministic adaptation, validation, derivation, policy, application orchestration, downstream presentation, and evaluation. `ViolenceSemanticEnvelope` is the sole current semantic authority. Live provider execution is restored: CASE_003, all eight stakeholder fixtures, and representative free-form manual narratives have completed their authorized workflows. Mobile usability is verified, and local plus Streamlit Community Cloud configuration is deployment-ready. The repository-authored `{facts.corpus_identity}` contains {facts.case_count} synthetic cases under evaluation schema `{facts.corpus_schema_version}`. Creation-time artifacts remain immutable and readable only through their creation-time schema family.",
        ),
        (
            "C. CORE INVARIANTS",
            "- Raw free-form narrative is the evidence authority; normalization is formatting-only.\n- Exactly one provider request is permitted per valid explicit analysis or selected live evaluation case; non-analysis interactions and invalid input issue zero.\n- Provider authority is limited to semantic candidates with temporary local references; provider SDK objects terminate at the adapter boundary.\n- Repository code owns incident identity, extraction metadata, semantic schema identity/version, canonical identifiers, ordering, final references, validation, derivation, policy, and downstream representation.\n- Schema validation and violence-domain validation fail closed before policy.\n- Derivation, policy, presentation, comparison, serialization, and reporting are deterministic.\n- No retries, semantic repair, silent semantic defaults, output-derived ground truth, compatibility reconstruction, or dual current semantic authority is permitted.\n- Historical evaluation artifacts remain byte-immutable and cannot be promoted into the successor baseline family.",
        ),
        (
            "D. SYSTEM MODEL",
            "`incident narrative` → formatting-only normalization → lexical baseline plus one structured extraction → provider-independent semantic envelope → schema validation → violence-domain validation → deterministic derived view → deterministic policy decision → aggregate pipeline result → deterministic presentation, preview, and evaluation consumers.",
        ),
        (
            "E. AUTHORITY MODEL",
            "| Component | Authority |\n| --- | --- |\n| Repository-authored corpus | Synthetic evaluation ground truth |\n| Raw narrative | Free-form evidence and excerpt-containment authority |\n| Provider | Bounded candidate semantic claims with temporary local references only |\n| Contract adapter | Provider termination; repository-owned incident/schema/extraction identity, canonical IDs/order, and final reference remapping |\n| Schema/domain validators | Admissibility and fail-closed rejection |\n| Semantic derivation | Typed active-set and direction views |\n| Deterministic policy | Sole illustrative disposition authority |\n| Tests | Permanent deterministic behavioral verification |\n| Governance tooling | Supporting generation, freshness, and readiness checks; never application truth |",
        ),
        (
            "F. DATA / CONTRACT MODEL",
            f"Semantic schema `{facts.semantic_schema_identity}` version `{facts.semantic_schema_version}` defines typed entities, propositions, relationships, uncertainties, evidence excerpts, evidence supports, and repository-assigned extraction metadata. The extraction contract identity is deterministic and cannot be overridden by provider output. `PipelineResult` carries the semantic envelope, derived view, validation outcome, and policy result without a compatibility or operational-finding authority. Current evaluation artifacts use schema `{facts.corpus_schema_version}`; recognized creation-time artifacts use schema `1.0.0` and remain intentionally incomparable with successor artifacts.",
        ),
        (
            "G. SYSTEM BOUNDARIES",
            "The repository does not provide a real Salesforce connection or write, clinical decision support, legal or safety determination, hospital workflow, PHI handling, external persistence, authentication, customer-authority control, or FoxCommand Runtime integration. Synthetic-only and no-PHI notices are mandatory. Streamlit Community Cloud deployment remains a manual operator follow-on; no hosted deployment, hosted URL, or hosted acceptance is claimed. Provider types, provider metadata authority, and provider-authored disposition do not cross the provider boundary.",
        ),
        (
            "H. CURRENT CAPABILITIES",
            f"The app accepts fixtures or unrestricted free-form manual narratives within deterministic input limits, shows lexical and proposition results, applies total deterministic policy, and builds a policy-gated illustrative Salesforce preview. CASE_003 completes as historical disclosure with no active current interpersonal violence; all eight stakeholder fixtures and representative manual violence, non-violence, and ambiguous narratives have completed verification. Mobile widths 390, 360, and 320 CSS pixels are verified with semantic-first stacking and no page-level overflow. Offline evaluation validates {facts.case_count} successor cases and supports explicit case selection, run creation, separately authorized baseline acceptance, within-family regression comparison, and evidence-only reports. Permanent Gate A–F tests and composed repository baseline-readiness governance protect the successor authority.",
        ),
        (
            "I. KNOWN LIMITATIONS",
            "The lexical baseline is intentionally shallow. Provider quality is not guaranteed. The ontology is bounded to repository-demonstrated distinctions. Live-provider evaluation is external and non-deterministic even though its surrounding contracts are deterministic. Streamlit Community Cloud deployment and hosted acceptance have not occurred. Creation-time and successor artifact families are intentionally incomparable. The static knowledge graph uses repository naming and AST evidence and leaves unresolved relationships explicit.",
        ),
        (
            "J. INTERACTION MODEL",
            "Analysis begins only after explicit `Run Analysis`. Import, startup, source and fixture selection, manual typing, and invalid input issue zero provider requests. Narrative changes invalidate stale output. A valid analysis performs lexical matching and exactly one provider request with SDK retries disabled, then all downstream steps are local and deterministic. Streamlit secrets override environment variables, which override ignored local `.env`; missing configuration fails safely. Mobile rendering places the stakeholder semantic result before regex detail. Live corpus execution is explicit and performs one request per valid selected case. Baseline acceptance and hosted deployment are separate operator actions and never occur during evaluation or governance validation.",
        ),
        (
            "K. GUARANTEES",
            "Strict contracts reject malformed or inadmissible semantics before policy. Provider metadata cannot override deterministic repository bookkeeping. Policy is total over admissible states. Collections and serialized current artifacts have canonical ordering. Successor baseline acceptance rejects legacy runs. Existing governed artifact paths are protected from implicit overwrite. Repository generation is deterministic for the same operational date and repository state.",
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
            "1. Read `README.md`, `docs/architecture.md`, this SITREC, `docs/local_governance.md`, and `docs/opord_004_verification_authority.md`.\n2. Inspect `src/contracts.py`, `src/provider_adapter.py`, the validation/derivation/policy chain, `src/app_logic.py`, `src/config.py`, `app.py`, `src/evaluation/`, and `evaluation/corpus/successor_corpus.json`.\n3. Inspect `git status --short` before mutation and preserve unrelated work.\n4. Run `python3 -m tools.repo_governance validate-all`; for baseline decisions run `python3 -m tools.repo_governance baseline-readiness`.\n5. Preserve provider semantic-only authority, repository bookkeeping, the one-request/zero-request boundaries, fail-closed validation, deterministic policy, sole successor authority, and historical artifact immutability.\n6. Treat Streamlit Community Cloud deployment and hosted acceptance as manual follow-on actions.\n7. Regenerate this artifact with the governed `sitrec` command whenever current repository truth changes.",
        ),
        (
            "P. SITREC LIFECYCLE",
            f"This `{facts.operational_date}` record is the unique newest current rehydration artifact. {_prior_sitrec_text(facts)} Update the same-date record rather than creating a duplicate; a later operational-date record supersedes it according to authorized repository lifecycle policy.",
        ),
        (
            "Q. DAILY UNIQUENESS",
            f"Exactly one top-level SITREC may represent `{facts.operational_date}`. The generator targets `docs/SITREC - {facts.operational_date} {title}.md` and requires explicit replacement to update an existing record.",
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


def write_sitrec(
    root: Path,
    operational_date: str,
    output: Path | None = None,
    title: str = DEFAULT_TITLE,
    replace: bool = False,
) -> dict[str, object]:
    target = root / (output or default_output_path(operational_date, title))
    target = target.resolve()
    try:
        relative = target.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"SITREC output path escapes repository root: {target}") from error
    if target.exists() and not replace:
        raise ValueError(f"SITREC already exists; pass --replace to update it: {relative.as_posix()}")
    content = render_sitrec(root, operational_date, title)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {
        "path": relative.as_posix(),
        "operational_date": validate_operational_date(operational_date),
        "sections": 19,
        "bytes": len(content.encode("utf-8")),
        "replaced": replace,
    }
