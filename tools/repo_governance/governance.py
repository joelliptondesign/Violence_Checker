#!/usr/bin/env python3
"""Deterministic local governance utilities for Violence_Checker.

Provenance: adapted from read-only reference tooling in
`/Users/joellipton/Desktop/foxcommand-runtime/tools/repo_governance.py` and
`/Users/joellipton/Desktop/foxcommand-runtime/tools/validate_sitrec.py`.

This local version intentionally omits FoxCommand manifest lifecycle, runtime
boundary, closeout, deployment, and documentation synchronization behavior.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .sitrec import DEFAULT_TITLE, default_output_path, render_sitrec, write_sitrec


DEFAULT_REPOSITORY_TREE_PATH = Path("docs/generated/repository_tree.txt")
DEFAULT_KNOWLEDGE_GRAPH_PATH = Path("docs/generated/repository_knowledge_graph.md")
HEARTBEAT_PATH = Path("telemetry/executor_heartbeat.jsonl")
AUTHORIZED_BASELINE = "367a5369dc43c2d451a8bf2b41776cff85d5c64d"

PROTECTED_HASHES = {
    "docs/semantic_design_basis.md": "d014993c77719b623900f81c7598fd3d12ac31db223e870750637a32a4452248",
    "docs/successor_semantic_contract_specification.md": "5b538ec006b640507cc270d99fe1a525737ab1ce4480fb934e1dc971d60a580e",
    "docs/semantic_migration_and_legacy_strategy.md": "4760e8e033d8fc53a85661895455a7e01b9722368aa9d09cc2f26458f2a7f297",
    "evaluation/corpus/corpus.json": "5e981e374d5c767a42e50e3447c192368cd9f8b578bd428c13649d97e8768dcb",
    "evaluation/runs/initial-operational-evaluation-001.json": "08498932f6a54c6d89a3848519154d8060402a43cabec602e84af77c6bdc6d64",
    "evaluation/baselines/initial-evaluation-baseline-001.json": "2f5d843605db161bc7f112f8743ee8c04b38a7c0d12599fcb071a15206bbb09c",
    "evaluation/reports/initial-operational-comparison-001.json": "8897919f3e0bcb0ae48897eb6f768ba4021c3d0c456da51f3ce4e4aee4f6cefe",
    "evaluation/reports/initial-operational-evaluation-001.md": "ddf1f8577a17dc4b1374ee2aae70095bbe06798e2be42123ba220db50eaeb3b0",
}

EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".streamlit",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "env",
    "node_modules",
    "venv",
}

EXCLUDED_FILES = {
    ".DS_Store",
    ".env",
    "Thumbs.db",
}

SECRET_NAME_PATTERNS = (
    re.compile(r"(^|/)\.env($|\.)"),
    re.compile(r"(^|/)secrets\.toml$"),
)

REQUIRED_SITREC_SECTIONS = [
    "A. SYSTEM IDENTITY",
    "B. CURRENT STATE",
    "C. CORE INVARIANTS",
    "D. SYSTEM MODEL",
    "E. AUTHORITY MODEL",
    "F. DATA / CONTRACT MODEL",
    "G. SYSTEM BOUNDARIES",
    "H. CURRENT CAPABILITIES",
    "I. KNOWN LIMITATIONS",
    "J. INTERACTION MODEL",
    "K. GUARANTEES",
    "L. NON-GUARANTEES",
    "M. GROUNDING ANCHORS",
    "N. SOURCE OF TRUTH RULE",
    "O. REHYDRATION INSTRUCTIONS",
]

PROVIDER_FACING_MODULES = {
    "src/config.py",
    "src/semantic_extractor.py",
    "src/semantic_prompt.py",
    "src/salesforce_preview.py",
}

APPLICATION_COMPONENTS = {
    "app.py",
    "src/app_logic.py",
    "src/comparison.py",
    "src/fixtures.py",
    "src/models.py",
    "src/regex_baseline.py",
}

ENTRY_POINT_PATTERNS = (
    "app.py",
    "scripts/*.py",
    "tools/repo_governance/__main__.py",
)


@dataclass(frozen=True)
class Finding:
    path: str
    message: str


def resolve_repo_root(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=candidate,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"not a Git repository: {candidate}")
    return Path(result.stdout.strip()).resolve()


def ensure_inside_root(root: Path, path: Path) -> Path:
    target = path if path.is_absolute() else root / path
    target = target.resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError(f"output path escapes repository root: {target}") from error
    return target


def is_excluded(relative: Path) -> bool:
    parts = relative.parts
    if relative.name in EXCLUDED_FILES:
        return True
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    posix = relative.as_posix()
    return any(pattern.search(posix) for pattern in SECRET_NAME_PATTERNS)


def repository_entries(root: Path) -> list[str]:
    entries: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if is_excluded(relative):
            if path.is_dir():
                continue
            continue
        suffix = "/" if path.is_dir() else ""
        entries.append(relative.as_posix() + suffix)
    return sorted(entries)


def repository_files(root: Path) -> list[str]:
    return [entry for entry in repository_entries(root) if not entry.endswith("/")]


def build_repository_tree(root: Path) -> str:
    lines = [
        "# Violence_Checker Repository Tree",
        "",
        "Generated by `python3 -m tools.repo_governance repo-tree`.",
        "Entries are sorted, repository-relative, and exclude ignored local configuration, caches, transient environments, and `.git` internals.",
        "",
    ]
    lines.extend(repository_entries(root))
    return "\n".join(lines).rstrip() + "\n"


def write_repository_tree(root: Path, output: Path = DEFAULT_REPOSITORY_TREE_PATH) -> dict[str, object]:
    root = resolve_repo_root(root)
    target = ensure_inside_root(root, output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_repository_tree(root), encoding="utf-8")
    return {"path": target.relative_to(root).as_posix(), "entries": len(repository_entries(root))}


def parse_python_file(path: Path) -> tuple[list[str], list[str], list[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return [], [], []
    imports: set[str] = set()
    classes: set[str] = set()
    functions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.add(module)
        elif isinstance(node, ast.ClassDef):
            classes.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.add(node.name)
    return sorted(imports), sorted(classes), sorted(functions)


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _header in headers) + " |",
    ]
    output.extend("| " + " | ".join(row) + " |" for row in rows)
    return output


def sitrec_paths(root: Path) -> list[str]:
    docs = root / "docs"
    if not docs.exists():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in docs.glob("*.md")
        if "sitrec" in path.name.lower()
    )


def _sitrec_date(path: str) -> str | None:
    match = re.search(r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)", Path(path).name)
    return match.group(1) if match else None


def active_sitrec_paths(root: Path) -> list[str]:
    """Select the unique newest dated top-level SITREC as current."""
    dated = [(path, _sitrec_date(path)) for path in sitrec_paths(root)]
    valid = [(path, date) for path, date in dated if date is not None]
    if not valid:
        return []
    newest = max(date for _path, date in valid)
    return [path for path, date in valid if date == newest]


def build_knowledge_graph(root: Path) -> str:
    files = repository_files(root)
    python_files = [value for value in files if value.endswith(".py")]
    docs = [value for value in files if value.startswith("docs/") and value.endswith(".md")]
    tests = [
        value
        for value in files
        if value.startswith("tests/")
        and Path(value).name.startswith("test_")
        and value.endswith(".py")
    ]

    module_rows: list[list[str]] = []
    import_rows: list[list[str]] = []
    contract_rows: list[list[str]] = []
    for relative in python_files:
        imports, classes, functions = parse_python_file(root / relative)
        role = "provider-facing" if relative in PROVIDER_FACING_MODULES else "deterministic"
        if relative in APPLICATION_COMPONENTS:
            role = "deterministic application component"
        if relative.startswith("tests/"):
            role = "deterministic test"
        if relative.startswith("tools/repo_governance/"):
            role = "deterministic governance tooling"
        module_rows.append([f"`{relative}`", role, ", ".join(f"`{name}`" for name in classes) or "none", str(len(functions))])
        import_rows.append([f"`{relative}`", ", ".join(f"`{name}`" for name in imports) or "none"])
        for class_name in classes:
            if relative.startswith("src/") or relative.startswith("tools/repo_governance/"):
                contract_rows.append([f"`{class_name}`", f"`{relative}`"])

    test_rows: list[list[str]] = []
    for test_path in tests:
        if test_path.startswith("tests/evaluation/test_"):
            target = test_path.removeprefix("tests/evaluation/test_").removesuffix(".py")
            candidates = [f"src/evaluation/{target}.py"]
        else:
            target = test_path.removeprefix("tests/test_").removesuffix(".py")
            candidates = [f"src/{target}.py", f"{target}.py"]
        covered = next((candidate for candidate in candidates if candidate in files), "unresolved")
        test_rows.append([f"`{test_path}`", f"`{covered}`" if covered != "unresolved" else "unresolved"])

    entry_rows: list[list[str]] = []
    for pattern in ENTRY_POINT_PATTERNS:
        matches = sorted(path.relative_to(root).as_posix() for path in root.glob(pattern) if path.is_file())
        for match in matches:
            entry_rows.append([f"`{match}`", "local executable entry point"])

    boundary_rows = [
        ["Deterministic application components", ", ".join(f"`{path}`" for path in sorted(APPLICATION_COMPONENTS) if path in files)],
        ["Provider-facing components", ", ".join(f"`{path}`" for path in sorted(PROVIDER_FACING_MODULES) if path in files)],
        ["Current pipeline boundary", "`src/app_logic.py` orchestrates regex, semantic extraction, comparison, and Salesforce preview gating."],
        ["Unresolved relationships", "No repository-local static evidence connects this project to FoxCommand runtime application modules."],
    ]

    current_sitrecs = set(active_sitrec_paths(root))
    grouped_docs: dict[str, list[str]] = defaultdict(list)
    for doc in docs:
        if "SITREC" in Path(doc).name:
            group = "current SITREC" if doc in current_sitrecs else "historical SITREC"
            grouped_docs[group].append(doc)
        elif doc.startswith("docs/generated/"):
            grouped_docs["generated"].append(doc)
        else:
            grouped_docs["documentation"].append(doc)
    doc_rows = [[key, ", ".join(f"`{item}`" for item in values)] for key, values in sorted(grouped_docs.items())]

    lines = [
        "# Violence_Checker Repository Knowledge Graph",
        "",
        "Generated by `python3 -m tools.repo_governance knowledge-graph` from repository content.",
        "",
        "## Scope",
        "",
        "This graph records deterministic repository relationships discoverable from files, imports, tests, documentation names, and governance artifact locations. It does not infer clinical, production, or external integration claims.",
        "",
        "## Entry Points",
        "",
        *markdown_table(["Artifact", "Relationship"], entry_rows),
        "",
        "## Pipeline Boundaries",
        "",
        *markdown_table(["Boundary", "Repository evidence"], boundary_rows),
        "",
        "## Python Modules",
        "",
        *markdown_table(["Module", "Role", "Classes", "Function count"], module_rows),
        "",
        "## Import Relationships",
        "",
        *markdown_table(["Module", "Imports"], import_rows),
        "",
        "## Contracts",
        "",
        *markdown_table(["Contract", "Declared in"], sorted(contract_rows)),
        "",
        "## Tests",
        "",
        *markdown_table(["Test artifact", "Static target"], test_rows),
        "",
        "## Documentation",
        "",
        *markdown_table(["Documentation group", "Artifacts"], doc_rows),
        "",
        "## Governance Artifacts",
        "",
        *markdown_table(
            ["Artifact", "Relationship"],
            [
                ["`tools/repo_governance/`", "Local deterministic governance tooling copied and narrowed from foxcommand-runtime reference tooling."],
                ["`docs/generated/repository_tree.txt`", "Generated deterministic repository tree."],
                ["`docs/generated/repository_knowledge_graph.md`", "Generated deterministic repository knowledge graph."],
                ["`telemetry/executor_heartbeat.jsonl`", "Executor operations telemetry validated as JSONL."],
                [", ".join(f"`{path}`" for path in active_sitrec_paths(root)), "Active top-level SITREC candidates."],
            ],
        ),
        "",
        "## Unresolved Relationships",
        "",
        "- Test-to-module links are marked unresolved when no direct filename convention match exists.",
        "- Runtime relationships outside this repository are unresolved unless represented by repository-local files.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_knowledge_graph(root: Path, output: Path = DEFAULT_KNOWLEDGE_GRAPH_PATH) -> dict[str, object]:
    root = resolve_repo_root(root)
    target = ensure_inside_root(root, output)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = build_knowledge_graph(root)
    target.write_text(content, encoding="utf-8")
    return {"path": target.relative_to(root).as_posix(), "bytes": len(content.encode("utf-8"))}


def normalize_heading(line: str) -> str:
    line = re.sub(r"^#{1,6}\s*", "", line.strip())
    line = re.sub(r"\s+", " ", line)
    return line.upper()


def sitrec_section_positions(text: str) -> dict[str, int]:
    positions: dict[str, int] = {}
    for index, line in enumerate(text.splitlines()):
        normalized = normalize_heading(line)
        for section in REQUIRED_SITREC_SECTIONS:
            if normalized == section:
                positions.setdefault(section, index)
    return positions


def section_text(text: str, section: str) -> str:
    lines = text.splitlines()
    positions = sitrec_section_positions(text)
    if section not in positions:
        return ""
    start = positions[section] + 1
    next_indexes = [index for name, index in positions.items() if index > positions[section] and name != section]
    end = min(next_indexes) if next_indexes else len(lines)
    return "\n".join(lines[start:end]).strip()


def validate_sitrec_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    positions = sitrec_section_positions(text)
    findings: list[Finding] = []
    for section in REQUIRED_SITREC_SECTIONS:
        if section not in positions:
            findings.append(Finding(path.as_posix(), f"missing required section: {section}"))
    grounding = section_text(text, "M. GROUNDING ANCHORS")
    if not grounding:
        findings.append(Finding(path.as_posix(), "grounding section empty"))
    elif not re.search(r"(`[^`]+`)|(\[[^\]]+\]\s*\n\s*<[^>]+>)", grounding):
        findings.append(Finding(path.as_posix(), "grounding section has no artifact reference"))
    if "repository wins" not in section_text(text, "N. SOURCE OF TRUTH RULE").lower() and "repository state is authoritative" not in section_text(text, "N. SOURCE OF TRUTH RULE").lower():
        findings.append(Finding(path.as_posix(), "source-of-truth section does not declare repository primacy"))
    return findings


def validate_sitrec_lifecycle(root: Path) -> list[Finding]:
    paths = sitrec_paths(root)
    current = active_sitrec_paths(root)
    findings: list[Finding] = []
    undated = [path for path in paths if _sitrec_date(path) is None]
    if undated:
        findings.extend(Finding(path, "top-level SITREC filename has no ISO date") for path in undated)
    if len(current) != 1:
        findings.append(Finding("docs", "exactly one newest dated SITREC must be current"))
        return findings
    text = (root / current[0]).read_text(encoding="utf-8")
    identity = section_text(text, "A. SYSTEM IDENTITY").lower()
    state = section_text(text, "B. CURRENT STATE").lower()
    if "violence_checker" not in identity or "non-production" not in identity:
        findings.append(Finding(current[0], "current SITREC identity must name the repository and non-production boundary"))
    if "current" not in state or "semantic authority" not in state:
        findings.append(Finding(current[0], "current SITREC must state the current semantic authority"))
    if len(paths) > 1 and not any(term in text.lower() for term in ("supersedes", "prior sitrec", "historical sitrec")):
        findings.append(Finding(current[0], "current SITREC must classify prior SITRECs as provenance"))
    return findings


def validate_current_sitrec_generation(root: Path) -> list[Finding]:
    """Require the current SITREC to match deterministic repository generation."""
    current = active_sitrec_paths(root)
    if len(current) != 1:
        return []
    relative = current[0]
    operational_date = _sitrec_date(relative)
    if operational_date is None:
        return []
    path = root / relative
    try:
        expected = render_sitrec(root, operational_date, DEFAULT_TITLE)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [Finding(relative, f"unable to render deterministic SITREC: {error}")]
    if path.read_text(encoding="utf-8") != expected:
        return [Finding(relative, "current SITREC does not match deterministic generation output")]
    return []


def validate_generated_freshness(root: Path) -> list[Finding]:
    expected = {
        DEFAULT_REPOSITORY_TREE_PATH: build_repository_tree(root),
        DEFAULT_KNOWLEDGE_GRAPH_PATH: build_knowledge_graph(root),
    }
    findings: list[Finding] = []
    for relative, content in expected.items():
        path = root / relative
        if not path.is_file():
            findings.append(Finding(relative.as_posix(), "generated artifact is missing"))
        elif path.read_text(encoding="utf-8") != content:
            findings.append(Finding(relative.as_posix(), "generated artifact is stale"))
    return findings


def validate_protected_hashes(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for relative, expected in PROTECTED_HASHES.items():
        path = root / relative
        if not path.is_file():
            findings.append(Finding(relative, "protected artifact is missing"))
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            findings.append(Finding(relative, f"protected artifact hash changed: {actual}"))
    return findings


def validate_current_authority(root: Path) -> list[Finding]:
    forbidden = {
        "ViolenceFinding",
        "ViolenceEventType",
        "SemanticFacts",
        "ValidatedSemanticFacts",
        "CompatibilityFindingResult",
        "operational_finding",
        "compatibility_result",
    }
    findings: list[Finding] = []
    paths = [root / "app.py", *sorted((root / "src").rglob("*.py")), *sorted((root / "scripts").rglob("*.py"))]
    for path in paths:
        if path.name == "legacy_artifacts.py" or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for symbol in sorted(forbidden):
            if re.search(rf"\b{re.escape(symbol)}\b", text):
                findings.append(Finding(path.relative_to(root).as_posix(), f"current authority contains retired symbol: {symbol}"))
    if (root / "src" / "compatibility_finding.py").exists():
        findings.append(Finding("src/compatibility_finding.py", "retired compatibility module still exists"))
    return findings


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=True)


def validate_repository_state(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    staged = _git(root, "diff", "--cached", "--name-only")
    if staged.returncode != 0:
        findings.append(Finding(".git", "unable to inspect staged files"))
    elif staged.stdout.strip():
        findings.append(Finding(".git", "baseline candidate contains staged files"))
    ancestry = _git(root, "merge-base", "--is-ancestor", AUTHORIZED_BASELINE, "HEAD")
    if ancestry.returncode != 0:
        findings.append(Finding(".git", "HEAD does not descend from the authorized baseline"))
    whitespace = _git(root, "diff", "--check")
    if whitespace.returncode != 0:
        findings.append(Finding(".git", "Git diff contains whitespace errors"))
    return findings


def validate_baseline_readiness(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(validate_heartbeat_jsonl(root / HEARTBEAT_PATH))
    for path in sitrec_paths(root):
        findings.extend(validate_sitrec_file(root / path))
    findings.extend(validate_sitrec_lifecycle(root))
    findings.extend(validate_current_sitrec_generation(root))
    findings.extend(validate_generated_freshness(root))
    findings.extend(validate_protected_hashes(root))
    findings.extend(validate_current_authority(root))
    findings.extend(validate_repository_state(root))
    return findings


def validate_heartbeat_jsonl(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not path.exists():
        return [Finding(path.as_posix(), "heartbeat JSONL file is missing")]
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            findings.append(Finding(path.as_posix(), f"line {line_number} is blank"))
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as error:
            findings.append(Finding(path.as_posix(), f"line {line_number} is not valid JSON: {error.msg}"))
            continue
        if event.get("event_type") != "executor_ops":
            findings.append(Finding(path.as_posix(), f"line {line_number} event_type is not executor_ops"))
        if event.get("actor") != "codex":
            findings.append(Finding(path.as_posix(), f"line {line_number} actor is not codex"))
        payload = event.get("payload")
        if not isinstance(payload, dict):
            findings.append(Finding(path.as_posix(), f"line {line_number} payload is not an object"))
            continue
        operations = payload.get("operations")
        if not isinstance(operations, list) or not operations:
            findings.append(Finding(path.as_posix(), f"line {line_number} operations is not a non-empty list"))
            continue
        for operation_index, operation in enumerate(operations, start=1):
            if not isinstance(operation, dict):
                findings.append(Finding(path.as_posix(), f"line {line_number} operation {operation_index} is not an object"))
                continue
            if operation.get("mode") not in {"planned", "autonomous"}:
                findings.append(Finding(path.as_posix(), f"line {line_number} operation {operation_index} has invalid mode"))
            for key in ("action", "reason"):
                if not isinstance(operation.get(key), str) or not operation[key].strip():
                    findings.append(Finding(path.as_posix(), f"line {line_number} operation {operation_index} missing {key}"))
    return findings


def command_repo_tree(args: argparse.Namespace) -> int:
    summary = write_repository_tree(args.repo_root, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def command_knowledge_graph(args: argparse.Namespace) -> int:
    summary = write_knowledge_graph(args.repo_root, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def command_validate_heartbeat(args: argparse.Namespace) -> int:
    root = resolve_repo_root(args.repo_root)
    path = ensure_inside_root(root, args.path)
    findings = validate_heartbeat_jsonl(path)
    return print_findings("heartbeat JSONL validation", findings)


def command_validate_sitrec(args: argparse.Namespace) -> int:
    root = resolve_repo_root(args.repo_root)
    path = ensure_inside_root(root, args.path)
    findings = validate_sitrec_file(path)
    return print_findings("SITREC validation", findings)


def command_sitrec(args: argparse.Namespace) -> int:
    root = resolve_repo_root(args.repo_root)
    output = args.output or default_output_path(args.date, args.title)
    output = ensure_inside_root(root, output)
    summary = write_sitrec(
        root,
        operational_date=args.date,
        output=output.relative_to(root),
        title=args.title,
        replace=args.replace,
    )
    findings = validate_sitrec_file(root / str(summary["path"]))
    if findings:
        return print_findings("generated SITREC validation", findings)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def command_validate_all(args: argparse.Namespace) -> int:
    root = resolve_repo_root(args.repo_root)
    findings: list[Finding] = []
    findings.extend(validate_heartbeat_jsonl(root / HEARTBEAT_PATH))
    for path in sitrec_paths(root):
        findings.extend(validate_sitrec_file(root / path))
    findings.extend(validate_sitrec_lifecycle(root))
    findings.extend(validate_current_sitrec_generation(root))
    findings.extend(validate_generated_freshness(root))
    return print_findings("local governance validation", findings)


def _run_readiness_command(root: Path, command: list[str], label: str) -> list[Finding]:
    result = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout.rstrip())
        return []
    detail = (result.stdout + "\n" + result.stderr).strip()
    return [Finding(label, detail or f"command exited {result.returncode}")]


def command_baseline_readiness(args: argparse.Namespace) -> int:
    root = resolve_repo_root(args.repo_root)
    findings = validate_baseline_readiness(root)
    python = root / ".venv" / "bin" / "python"
    interpreter = str(python) if python.is_file() else sys.executable
    findings.extend(_run_readiness_command(root, [interpreter, "-m", "src.evaluation.corpus", "validate"], "evaluation corpus"))
    findings.extend(_run_readiness_command(root, [interpreter, "-m", "src.evaluation.corpus", "coverage"], "evaluation coverage"))
    if not args.skip_tests:
        findings.extend(_run_readiness_command(root, [interpreter, "-m", "pytest"], "automated tests"))
    return print_findings("repository baseline readiness", findings)


def print_findings(label: str, findings: list[Finding]) -> int:
    if findings:
        print(f"{label} findings:")
        for finding in findings:
            print(f"- {finding.path}: {finding.message}")
        return 1
    print(f"{label} passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Violence_Checker deterministic local governance tooling.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="explicit repository root or path inside it")
    subparsers = parser.add_subparsers(dest="command", required=True)

    repo_tree = subparsers.add_parser("repo-tree", help="generate deterministic repository tree")
    repo_tree.add_argument("--output", type=Path, default=DEFAULT_REPOSITORY_TREE_PATH)
    repo_tree.set_defaults(func=command_repo_tree)

    graph = subparsers.add_parser("knowledge-graph", help="generate deterministic repository knowledge graph")
    graph.add_argument("--output", type=Path, default=DEFAULT_KNOWLEDGE_GRAPH_PATH)
    graph.set_defaults(func=command_knowledge_graph)

    heartbeat = subparsers.add_parser("validate-heartbeat", help="validate executor heartbeat JSONL")
    heartbeat.add_argument("--path", type=Path, default=HEARTBEAT_PATH)
    heartbeat.set_defaults(func=command_validate_heartbeat)

    sitrec = subparsers.add_parser("validate-sitrec", help="validate one SITREC artifact")
    sitrec.add_argument("--path", type=Path, required=True)
    sitrec.set_defaults(func=command_validate_sitrec)

    generate_sitrec = subparsers.add_parser("sitrec", help="generate a complete deterministic Violence_Checker SITREC")
    generate_sitrec.add_argument("--date", required=True, help="operational date in ISO YYYY-MM-DD form")
    generate_sitrec.add_argument("--title", default=DEFAULT_TITLE, help="repository-specific SITREC title")
    generate_sitrec.add_argument("--output", type=Path, help="repository-local output path; defaults from date and title")
    generate_sitrec.add_argument("--replace", action="store_true", help="replace an existing same-path SITREC")
    generate_sitrec.set_defaults(func=command_sitrec)

    validate_all = subparsers.add_parser("validate-all", help="run local deterministic governance validators")
    validate_all.add_argument("--tree-output", type=Path, default=DEFAULT_REPOSITORY_TREE_PATH)
    validate_all.add_argument("--graph-output", type=Path, default=DEFAULT_KNOWLEDGE_GRAPH_PATH)
    validate_all.set_defaults(func=command_validate_all)

    readiness = subparsers.add_parser("baseline-readiness", help="validate the complete repository baseline candidate")
    readiness.add_argument("--skip-tests", action="store_true", help="omit the full test command when it was already run by the caller")
    readiness.set_defaults(func=command_baseline_readiness)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as error:
        print(f"repo_governance error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
