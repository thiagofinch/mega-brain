"""
core/governance/engine.py -- Governance Engine

Auto-generates architecture documentation from filesystem + config files.
Single Source of Truth: reads configs, writes docs.

Generated files:
- docs/architecture/coding-standards.md
- docs/architecture/tech-stack.md
- docs/architecture/source-tree.md
- docs/architecture/constitution.md        (CONST-002)
- .claude/rules/synapse-digest.md          (CONST-003)
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Try to import tomllib (Python 3.11+), fall back to tomli
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[import-not-found]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

import yaml

# -- PATHS -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_ARCH = ROOT / "docs" / "architecture"
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_JSON = ROOT / "package.json"
BIOME_JSON = ROOT / "biome.json"
PATHS_PY = ROOT / "core" / "paths.py"
AGENT_INDEX = ROOT / "agents" / "AGENT-INDEX.yaml"
SETTINGS_JSON = ROOT / ".claude" / "settings.json"
RULES_DIR = ROOT / "core" / "engine" / "rules"
SYNAPSE_DIGEST_PATH = ROOT / ".claude" / "rules" / "synapse-digest.md"
CONSTITUTION_PATH = DOCS_ARCH / "constitution.md"


def _ensure_docs_dir() -> None:
    """Ensure docs/architecture/ exists."""
    DOCS_ARCH.mkdir(parents=True, exist_ok=True)


def _read_toml(path: Path) -> dict[str, Any]:
    """Read TOML file."""
    if tomllib is None:
        # Fallback: parse basic TOML structure manually
        return _parse_basic_toml(path)
    with open(path, "rb") as f:
        return tomllib.load(f)


def _parse_basic_toml(path: Path) -> dict[str, Any]:
    """Basic TOML parser for when tomllib is unavailable."""
    content = path.read_text()
    result: dict[str, Any] = {}
    current_section: list[str] = []

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Section header: [tool.ruff] or [project]
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            current_section = section.split(".")
            # Ensure nested structure exists
            target = result
            for key in current_section:
                if key not in target:
                    target[key] = {}
                target = target[key]
            continue

        # Key-value pair
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # Parse value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("["):
                # Simple list parsing
                value = _parse_toml_list(value)
            elif value == "true":
                value = True
            elif value == "false":
                value = False
            elif value.isdigit():
                value = int(value)

            # Navigate to correct section
            target = result
            for section_key in current_section:
                target = target.setdefault(section_key, {})
            target[key] = value

    return result


def _parse_toml_list(value: str) -> list[str]:
    """Parse a simple TOML list."""
    # Remove brackets and split
    inner = value[1:-1].strip()
    if not inner:
        return []
    items = []
    for item in inner.split(","):
        item = item.strip().strip('"').strip("'")
        if item:
            items.append(item)
    return items


def _read_json(path: Path) -> dict[str, Any]:
    """Read JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _extract_routing_keys() -> list[str]:
    """Extract ROUTING keys from core/paths.py."""
    if not PATHS_PY.exists():
        return []

    content = PATHS_PY.read_text()
    # Find ROUTING = { ... } block
    match = re.search(r"ROUTING\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}", content, re.DOTALL)
    if not match:
        return []

    # Extract all quoted keys
    routing_block = match.group(1)
    keys = re.findall(r'"([^"]+)":', routing_block)
    return sorted(keys)


def _extract_prohibited_dirs() -> list[str]:
    """Extract PROHIBITED directories from core/paths.py."""
    if not PATHS_PY.exists():
        return []

    content = PATHS_PY.read_text()
    match = re.search(r"PROHIBITED\s*=\s*\[([^\]]+)\]", content, re.DOTALL)
    if not match:
        return []

    # Extract paths
    block = match.group(1)
    dirs = re.findall(r'ROOT\s*/\s*"([^"]+)"', block)
    dirs += re.findall(r'WORKSPACE\s*/\s*"([^"]+)"', block)
    return dirs


def _get_directory_tree(
    path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0
) -> list[str]:
    """Generate directory tree representation."""
    if current_depth >= max_depth:
        return []

    lines = []
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return []

    # Filter out common noise
    skip_patterns = {
        "__pycache__",
        ".git",
        "node_modules",
        ".venv",
        "venv",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "*.egg-info",
        ".DS_Store",
        "*.pyc",
        ".coverage",
    }

    entries = [e for e in entries if e.name not in skip_patterns and not e.name.endswith(".pyc")]

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "

        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            extension = "    " if is_last else "│   "
            lines.extend(
                _get_directory_tree(entry, prefix + extension, max_depth, current_depth + 1)
            )
        else:
            lines.append(f"{prefix}{connector}{entry.name}")

    return lines


# -- CONST-001: INTROSPECTION HELPERS ----------------------------------------


def _deterministic_timestamp(input_files: list[Path]) -> str:
    """Return deterministic timestamp based on max mtime of input files.

    Uses the newest modification time across all input files instead of
    datetime.now(). This ensures idempotent output when inputs haven't changed.
    """
    max_mtime = 0.0
    for f in input_files:
        if f.exists():
            max_mtime = max(max_mtime, f.stat().st_mtime)
    if max_mtime == 0.0:
        # Fallback if no files found -- use a fixed epoch
        return "1970-01-01 00:00 UTC"
    return datetime.fromtimestamp(max_mtime, tz=UTC).strftime("%Y-%m-%d %H:%M UTC")


def _extract_agent_registry() -> list[dict[str, Any]]:
    """Read agents/AGENT-INDEX.yaml and return grouped agent counts.

    Returns list of {type, count, example} dicts per agent type.
    """
    if not AGENT_INDEX.exists():
        return []

    data = yaml.safe_load(AGENT_INDEX.read_text())
    if not data:
        return []

    result = []

    # External agents
    external = data.get("external", [])
    if external:
        example = external[0]["id"] if external else ""
        result.append({"type": "external", "count": len(external), "example": example})

    # Conclave agents
    conclave = data.get("conclave", [])
    if conclave:
        example = conclave[0]["id"] if conclave else ""
        result.append({"type": "conclave", "count": len(conclave), "example": example})

    # Cargo agents -- nested by subcategory
    cargo = data.get("cargo", {})
    cargo_count = 0
    cargo_example = ""
    if isinstance(cargo, dict):
        for _subcat, agents in cargo.items():
            if isinstance(agents, list):
                cargo_count += len(agents)
                if not cargo_example and agents:
                    cargo_example = agents[0]["id"]
    if cargo_count:
        result.append({"type": "cargo", "count": cargo_count, "example": cargo_example})

    return result


def _extract_mce_pipeline_steps() -> list[dict[str, str]]:
    """Return hardcoded list of 12 MCE pipeline steps.

    Hardcoded per architect decision: orchestrate.py (27K) does not export
    step names. Step names sourced from deep-dive-megabrain-full-system.md.
    A change to orchestrate.py triggers governance regeneration anyway.
    """
    return [
        {"step": "0", "name": "Detect", "script": "workflow_detector.py", "type": "deterministic"},
        {"step": "1", "name": "Ingest", "script": "orchestrate.py", "type": "deterministic"},
        {"step": "2", "name": "Batch", "script": "batch_auto_creator.py", "type": "deterministic"},
        {"step": "3", "name": "Chunk", "script": "prompt-1.1-chunking.md", "type": "llm"},
        {"step": "4", "name": "Entity Extraction", "script": "gemini_analyzer.py", "type": "llm"},
        {"step": "5", "name": "Insight/DNA Extraction", "script": "prompt-2.1-insight-extraction.md", "type": "llm"},
        {"step": "6", "name": "MCE Behavioral", "script": "prompt-mce-behavioral.md", "type": "llm"},
        {"step": "7", "name": "MCE Identity", "script": "prompt-mce-identity.md", "type": "llm"},
        {"step": "8", "name": "MCE Voice", "script": "prompt-mce-voice.md", "type": "llm"},
        {"step": "9", "name": "Identity Checkpoint", "script": "human-review", "type": "manual"},
        {"step": "10", "name": "Consolidation", "script": "dossier-compilation.md", "type": "llm"},
        {"step": "11", "name": "Finalize", "script": "orchestrate.py", "type": "deterministic"},
    ]


def _extract_synapse_rule_summary() -> list[dict[str, Any]]:
    """Read all YAML files in core/engine/rules/ and return per-layer summary.

    Returns list of {layer, name, count, rules} dicts.
    Each rules entry is {id, severity, description, tags}.
    """
    if not RULES_DIR.exists():
        return []

    result = []
    for yaml_path in sorted(RULES_DIR.glob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        if not data or "rules" not in data:
            continue

        rules = data["rules"]
        rule_entries = []
        for r in rules:
            rule_entries.append({
                "id": r.get("id", ""),
                "severity": r.get("severity", "info"),
                "description": r.get("description", ""),
                "tags": r.get("tags", []),
            })

        result.append({
            "layer": data.get("layer", yaml_path.stem),
            "name": data.get("name", ""),
            "count": len(rules),
            "rules": rule_entries,
        })

    return result


def _extract_hook_summary() -> list[dict[str, Any]]:
    """Read .claude/settings.json and return hook counts per event type.

    Returns list of {event, count, examples} dicts.
    """
    if not SETTINGS_JSON.exists():
        return []

    data = _read_json(SETTINGS_JSON)
    hooks_config = data.get("hooks", {})

    result = []
    for event, entries in sorted(hooks_config.items()):
        count = 0
        examples: list[str] = []
        if isinstance(entries, list):
            for entry in entries:
                hook_list = entry.get("hooks", [])
                count += len(hook_list)
                for h in hook_list[:3]:
                    cmd = h.get("command", "")
                    # Extract script name from command
                    parts = cmd.split()
                    if len(parts) >= 2:
                        script = Path(parts[-1].strip("'\"")).name
                        examples.append(script)
        result.append({"event": event, "count": count, "examples": examples[:3]})

    return result


# -- GENERATORS (existing) ---------------------------------------------------


def generate_coding_standards() -> str:
    """Generate coding-standards.md from pyproject.toml and biome.json."""
    _ensure_docs_dir()

    pyproject = _read_toml(PYPROJECT) if PYPROJECT.exists() else {}
    biome = _read_json(BIOME_JSON) if BIOME_JSON.exists() else {}

    # Extract config sections
    ruff = pyproject.get("tool", {}).get("ruff", {})
    ruff_lint = ruff.get("lint", {})
    pyright = pyproject.get("tool", {}).get("pyright", {})
    pytest = pyproject.get("tool", {}).get("pytest", {}).get("ini_options", {})
    biome_formatter = biome.get("formatter", {})
    biome_js = biome.get("javascript", {}).get("formatter", {})

    timestamp = _deterministic_timestamp([PYPROJECT, BIOME_JSON])

    content = f"""# Coding Standards

> **Auto-generated by Governance Engine**
> **Last updated:** {timestamp}
> **Source:** pyproject.toml, biome.json

---

## Python Standards

### Ruff Configuration

| Setting | Value |
|---------|-------|
| Target Version | `{ruff.get("target-version", "py311")}` |
| Line Length | `{ruff.get("line-length", 100)}` |
| Source Dirs | `{", ".join(ruff.get("src", ["core"]))}` |

### Lint Rules (Selected)

```
{", ".join(ruff_lint.get("select", ["E", "F", "W"]))}
```

### Ignored Rules

| Rule | Reason |
|------|--------|
"""

    # Add ignored rules
    ignored = ruff_lint.get("ignore", [])
    for rule in ignored[:10]:  # Limit to first 10
        content += f"| `{rule}` | See pyproject.toml |\n"

    if len(ignored) > 10:
        content += f"| ... | +{len(ignored) - 10} more rules |\n"

    content += f"""
### Pyright Configuration

| Setting | Value |
|---------|-------|
| Python Version | `{pyright.get("pythonVersion", "3.11")}` |
| Type Checking Mode | `{pyright.get("typeCheckingMode", "basic")}` |
| Include | `{", ".join(pyright.get("include", ["core"]))}` |

### Pytest Configuration

| Setting | Value |
|---------|-------|
| Test Paths | `{", ".join(pytest.get("testpaths", ["tests/python"]))}` |
| File Pattern | `{pytest.get("python_files", "test_*.py")}` |

---

## JavaScript Standards

### Biome Formatter

| Setting | Value |
|---------|-------|
| Indent Style | `{biome_formatter.get("indentStyle", "space")}` |
| Indent Width | `{biome_formatter.get("indentWidth", 2)}` |
| Line Width | `{biome_formatter.get("lineWidth", 100)}` |

### JS Formatter

| Setting | Value |
|---------|-------|
| Quote Style | `{biome_js.get("quoteStyle", "single")}` |
| Semicolons | `{biome_js.get("semicolons", "always")}` |
| Trailing Commas | `{biome_js.get("trailingCommas", "all")}` |

---

## File Conventions

| Type | Convention |
|------|------------|
| Python files | `snake_case.py` |
| Config files | `SCREAMING-CASE.yaml` or `kebab-case.json` |
| Markdown docs | `SCREAMING-CASE.md` for configs, `Title-Case.md` for guides |
| Hooks | `snake_case.py` in `.claude/hooks/` |

---

*This document is auto-generated. Do not edit manually.*
*To regenerate: `python -c "from core.governance import generate_coding_standards; print(generate_coding_standards())"`*
"""

    output_path = DOCS_ARCH / "coding-standards.md"
    output_path.write_text(content)
    return str(output_path)


def generate_tech_stack() -> str:
    """Generate tech-stack.md from package.json and pyproject.toml."""
    _ensure_docs_dir()

    package = _read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    pyproject = _read_toml(PYPROJECT) if PYPROJECT.exists() else {}

    project = pyproject.get("project", {})
    optional_deps = project.get("optional-dependencies", {})

    timestamp = _deterministic_timestamp([PACKAGE_JSON, PYPROJECT])

    content = f"""# Tech Stack

> **Auto-generated by Governance Engine**
> **Last updated:** {timestamp}
> **Source:** package.json, pyproject.toml

---

## Project Info

| Field | Value |
|-------|-------|
| Name | `{package.get("name", project.get("name", "mega-brain"))}` |
| Version | `{package.get("version", project.get("version", "unknown"))}` |
| Python | `>={project.get("requires-python", "3.11").replace(">=", "")}` |
| Node | `{package.get("engines", {}).get("node", ">=18.0.0")}` |

---

## Python Dependencies

### Core
"""

    # Core dependencies
    core_deps = project.get("dependencies", [])
    for dep in core_deps:
        content += f"- `{dep}`\n"

    # Optional dependency groups
    for group, deps in optional_deps.items():
        content += f"\n### {group.title()}\n"
        for dep in deps:
            content += f"- `{dep}`\n"

    content += """
---

## Node Dependencies

### Runtime
"""

    for name, version in package.get("dependencies", {}).items():
        content += f"- `{name}`: {version}\n"

    content += "\n### Development\n"
    for name, version in package.get("devDependencies", {}).items():
        content += f"- `{name}`: {version}\n"

    content += """
---

## CLI Commands

| Command | Script |
|---------|--------|
"""

    for script, cmd in package.get("scripts", {}).items():
        # Truncate long commands
        cmd_display = cmd if len(cmd) < 60 else cmd[:57] + "..."
        content += f"| `npm run {script}` | `{cmd_display}` |\n"

    content += """
---

*This document is auto-generated. Do not edit manually.*
"""

    output_path = DOCS_ARCH / "tech-stack.md"
    output_path.write_text(content)
    return str(output_path)


def generate_source_tree() -> str:
    """Generate source-tree.md from filesystem + ROUTING keys."""
    _ensure_docs_dir()

    routing_keys = _extract_routing_keys()
    prohibited = _extract_prohibited_dirs()

    timestamp = _deterministic_timestamp([PATHS_PY])

    content = f"""# Source Tree

> **Auto-generated by Governance Engine**
> **Last updated:** {timestamp}
> **Source:** filesystem, core/paths.py

---

## Directory Structure

```
mega-brain/
"""

    # Generate tree for key directories
    key_dirs = [
        "core",
        "agents",
        ".claude",
        "knowledge",
        "workspace",
        "bin",
        "docs",
        "reference",
        "system",
    ]

    for dir_name in key_dirs:
        dir_path = ROOT / dir_name
        if dir_path.exists() and dir_path.is_dir():
            content += f"├── {dir_name}/\n"
            tree_lines = _get_directory_tree(dir_path, "│   ", max_depth=2)
            for line in tree_lines[:20]:  # Limit per directory
                content += line + "\n"
            if len(tree_lines) > 20:
                content += f"│   └── ... (+{len(tree_lines) - 20} more)\n"

    count = len(routing_keys)
    content += f"""```

---

## ROUTING Keys ({count} total)

Output paths managed by `core/paths.py`:

| Category | Keys |
|----------|------|
"""

    # Group routing keys by prefix
    categories: dict[str, list[str]] = {}
    for key in routing_keys:
        prefix = key.split("_")[0] if "_" in key else "general"
        categories.setdefault(prefix, []).append(key)

    for category, keys in sorted(categories.items()):
        keys_display = ", ".join(f"`{k}`" for k in keys[:5])
        if len(keys) > 5:
            keys_display += f" (+{len(keys) - 5} more)"
        content += f"| {category} | {keys_display} |\n"

    content += """
---

## Prohibited Directories

These directories are deprecated or restricted:

"""

    for dir_name in prohibited:
        content += f"- `{dir_name}/` -- Do not create new files here\n"

    content += """
---

## Layer System

| Layer | Description | Git Status |
|-------|-------------|------------|
| L1 | Community (core, .claude, bin) | Tracked |
| L2 | Pro (agents/cargo, knowledge/external populated) | Tracked |
| L3 | Personal (knowledge/personal, .data, logs) | Gitignored |

---

*This document is auto-generated. Do not edit manually.*
"""

    output_path = DOCS_ARCH / "source-tree.md"
    output_path.write_text(content)
    return str(output_path)


# -- CONST-002: CONSTITUTION GENERATOR ---------------------------------------


def generate_constitution() -> str:
    """Generate docs/architecture/constitution.md.

    Produces a system constitution under 200 lines using introspection helpers
    from CONST-001. Idempotent: running twice on unchanged inputs produces
    identical output.
    """
    _ensure_docs_dir()

    # Gather all introspection data
    agent_registry = _extract_agent_registry()
    mce_steps = _extract_mce_pipeline_steps()
    synapse_summary = _extract_synapse_rule_summary()
    hook_summary = _extract_hook_summary()
    routing_keys = _extract_routing_keys()

    # Compute totals
    total_agents = sum(entry["count"] for entry in agent_registry)
    total_rules = sum(entry["count"] for entry in synapse_summary)
    total_hooks = sum(entry["count"] for entry in hook_summary)
    total_routing = len(routing_keys)

    # Input files for deterministic timestamp
    input_files = [AGENT_INDEX, SETTINGS_JSON, PATHS_PY, PYPROJECT, PACKAGE_JSON]
    for yaml_path in sorted(RULES_DIR.glob("*.yaml")):
        input_files.append(yaml_path)
    timestamp = _deterministic_timestamp(input_files)

    # Compute content checksum (all input file mtimes concatenated)
    checksum_input = "|".join(
        f"{f.name}:{f.stat().st_mtime}" for f in input_files if f.exists()
    )
    checksum = hashlib.sha256(checksum_input.encode()).hexdigest()[:12]

    # Read tech stack info
    pyproject = _read_toml(PYPROJECT) if PYPROJECT.exists() else {}
    package = _read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    project = pyproject.get("project", {})

    # Build constitution
    lines: list[str] = []
    lines.append("# Mega Brain System Constitution")
    lines.append("")
    lines.append("> **Auto-generated by Governance Engine**")
    lines.append(f"> **Generated:** {timestamp}")
    lines.append(f"> **Checksum:** {checksum}")
    lines.append("> **Source files:** AGENT-INDEX.yaml, settings.json, paths.py, core/engine/rules/*.yaml")
    lines.append("> **Regenerate:** `python3 -m core.governance.engine constitution`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # -- System Identity
    lines.append("## System Identity")
    lines.append("")
    lines.append("Mega Brain is an AI-powered knowledge management system that transforms expert")
    lines.append("materials (videos, PDFs, transcriptions) into structured playbooks, DNA schemas,")
    lines.append("and mind-clone agents. Three knowledge buckets (external, business, personal)")
    lines.append(f"feed {total_agents} agents through a 12-step MCE pipeline, governed by")
    lines.append(f"{total_rules} Synapse rules and {total_hooks} lifecycle hooks.")
    lines.append("")

    # -- MCE Pipeline
    lines.append("## MCE Pipeline (12 steps)")
    lines.append("")
    lines.append("| Step | Name | Script | Type |")
    lines.append("|------|------|--------|------|")
    for s in mce_steps:
        lines.append(f"| {s['step']} | {s['name']} | `{s['script']}` | {s['type']} |")
    lines.append("")

    # -- Agent Registry
    lines.append("## Agent Registry")
    lines.append("")
    lines.append(f"**Total agents:** {total_agents}")
    lines.append("")
    lines.append("| Type | Count | Example |")
    lines.append("|------|-------|---------|")
    for entry in agent_registry:
        lines.append(f"| {entry['type']} | {entry['count']} | `{entry['example']}` |")
    lines.append("")

    # -- Knowledge Architecture
    lines.append("## Knowledge Architecture")
    lines.append("")
    lines.append("| Bucket | Path | Content |")
    lines.append("|--------|------|---------|")
    lines.append("| External | `knowledge/external/` | Expert courses, DNA, dossiers, playbooks |")
    lines.append("| Business | `knowledge/business/` | Meetings, calls, insights, SOPs |")
    lines.append("| Personal | `knowledge/personal/` | Founder cognitive, messages, email |")
    lines.append("")
    lines.append("**RAG Pipelines:** A (BM25), B (Hybrid), C (Graph+Hybrid), D (Full), E (Contextual)")
    lines.append("")

    # -- ROUTING Contract
    lines.append("## ROUTING Contract")
    lines.append("")
    lines.append(f"**{total_routing} routing keys** defined in `core/paths.py`.")
    lines.append("")
    # Group and show categories
    categories: dict[str, int] = {}
    for key in routing_keys:
        prefix = key.split("_")[0] if "_" in key else "general"
        categories[prefix] = categories.get(prefix, 0) + 1
    cat_parts = [f"{cat} ({count})" for cat, count in sorted(categories.items())]
    lines.append("Categories: " + ", ".join(cat_parts))
    lines.append("")
    lines.append("Reference: `core/paths.py` ROUTING dict. All output paths MUST use these constants.")
    lines.append("")

    # -- Active Rules (Synapse)
    lines.append("## Active Rules (Synapse)")
    lines.append("")
    lines.append(f"**{total_rules} rules** across {len(synapse_summary)} layers.")
    lines.append("")
    lines.append("| Layer | Name | Count | Example IDs |")
    lines.append("|-------|------|-------|-------------|")
    for layer_info in synapse_summary:
        example_ids = ", ".join(r["id"] for r in layer_info["rules"][:3])
        lines.append(
            f"| {layer_info['layer']} | {layer_info['name']} | {layer_info['count']} | {example_ids} |"
        )
    lines.append("")
    lines.append("Resolution engine: `core/engine/synapse.py`. Digest: `.claude/rules/synapse-digest.md`.")
    lines.append("")

    # -- Hook System
    lines.append("## Hook System")
    lines.append("")
    lines.append(f"**{total_hooks} hooks** across {len(hook_summary)} lifecycle events.")
    lines.append("")
    lines.append("| Event | Count | Key Hooks |")
    lines.append("|-------|-------|-----------|")
    for h in hook_summary:
        examples_str = ", ".join(f"`{e}`" for e in h["examples"])
        lines.append(f"| {h['event']} | {h['count']} | {examples_str} |")
    lines.append("")

    # -- Tech Stack
    python_ver = project.get("requires-python", ">=3.11")
    node_ver = package.get("engines", {}).get("node", ">=18.0.0")
    pkg_version = package.get("version", project.get("version", "unknown"))

    lines.append("## Tech Stack")
    lines.append("")
    lines.append("| Component | Version |")
    lines.append("|-----------|---------|")
    lines.append(f"| Python | `{python_ver}` |")
    lines.append(f"| Node.js | `{node_ver}` |")
    lines.append(f"| Package | `{pkg_version}` |")
    lines.append("| Key deps | PyYAML, watchdog, transitions |")
    lines.append("| Hooks constraint | stdlib + PyYAML only |")
    lines.append("")

    # -- Governance
    lines.append("## Governance")
    lines.append("")
    lines.append("### Amendment Process")
    lines.append("")
    lines.append("1. Edit source of truth (YAML rules, AGENT-INDEX, paths.py, pyproject.toml)")
    lines.append("2. Run `python3 -m core.governance.engine all` to regenerate all docs")
    lines.append("3. Constitution and digest auto-update via PostToolUse hook")
    lines.append("")
    lines.append("### Versioning")
    lines.append("")
    lines.append("Constitution version tracks AGENT-INDEX.yaml version field.")
    lines.append("")
    lines.append("### Gate Severities")
    lines.append("")
    lines.append("| Severity | Behavior |")
    lines.append("|----------|----------|")
    lines.append("| block | Prevents action, requires resolution |")
    lines.append("| warn | Allows action, logs warning |")
    lines.append("| info | Informational, no enforcement |")
    lines.append("")

    # -- Generation Metadata
    lines.append("## Generation Metadata")
    lines.append("")
    lines.append(f"- **Timestamp:** {timestamp}")
    lines.append(f"- **Checksum:** {checksum}")
    lines.append(f"- **Input files:** {len(input_files)} files")
    lines.append("- **Engine:** `core/governance/engine.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Auto-generated. Do not edit. Regenerate: `python3 -m core.governance.engine constitution`*")

    content = "\n".join(lines) + "\n"

    CONSTITUTION_PATH.write_text(content)
    return str(CONSTITUTION_PATH)


# -- CONST-003: SYNAPSE DIGEST GENERATOR -------------------------------------


def generate_synapse_digest() -> str:
    """Generate .claude/rules/synapse-digest.md.

    Reads all Synapse YAML rule files and produces a human-readable digest
    that Claude Code loads as project instructions. Target: under 100 lines.
    Replaces the 17 hand-maintained markdown rule files with 1 auto-generated file.
    """
    # Ensure output directory exists
    SYNAPSE_DIGEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    synapse_summary = _extract_synapse_rule_summary()
    total_rules = sum(entry["count"] for entry in synapse_summary)
    total_layers = len(synapse_summary)

    # Input files for timestamp
    input_files = list(sorted(RULES_DIR.glob("*.yaml")))
    timestamp = _deterministic_timestamp(input_files)

    lines: list[str] = []
    lines.append("# Synapse Rules Digest (Auto-Generated)")
    lines.append("")
    lines.append(f"> Generated: {timestamp}")
    lines.append("> Source: core/engine/rules/*.yaml")
    lines.append(f"> Rules: {total_rules} across {total_layers} layers")
    lines.append("")

    # Emit rules grouped by layer
    for layer_info in synapse_summary:
        layer = layer_info["layer"]
        name = layer_info["name"]

        # Determine header suffix based on layer
        if layer == "L0":
            header = f"## {layer}: {name} (block/warn -- always active)"
        elif layer == "L1":
            header = f"## {layer}: {name} (project-wide)"
        elif layer == "L6":
            header = f"## {layer}: {name} (keyword-triggered)"
        else:
            header = f"## {layer}: {name}"

        lines.append(header)
        lines.append("")

        for rule in layer_info["rules"]:
            severity = rule["severity"]
            if severity == "block":
                icon = "\u26d4"
            elif severity == "warn":
                icon = "\u26a0"
            else:
                icon = "\u2139"

            desc = rule["description"].replace("\n", " ").strip()
            entry = f"- {icon} **{rule['id']}** [{severity}]: {desc}"

            # L6 rules show tags
            if layer == "L6" and rule["tags"]:
                entry += f"  tags: {', '.join(rule['tags'])}"

            lines.append(entry)

        lines.append("")

    # Protocol references
    lines.append("## Protocol References")
    lines.append("")
    lines.append("For full protocol documents, see:")
    lines.append("- Agent cognition: `reference/AGENT-COGNITION-PROTOCOL.md`")
    lines.append("- Agent integrity: `reference/AGENT-INTEGRITY-PROTOCOL.md`")
    lines.append("- Epistemic standards: `reference/EPISTEMIC-PROTOCOL.md`")
    lines.append("- Directory contract: `reference/DIRECTORY-CONTRACT.md`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Auto-generated. Do not edit. Regenerate: `python3 -m core.governance.engine digest`*")

    content = "\n".join(lines) + "\n"

    SYNAPSE_DIGEST_PATH.write_text(content)
    return str(SYNAPSE_DIGEST_PATH)


# -- CONST-004: WIRING -------------------------------------------------------


def generate_all() -> dict[str, str]:
    """Generate all governance documentation.

    Returns:
        Dict mapping doc type to output path (5 keys).
    """
    return {
        "coding-standards": generate_coding_standards(),
        "tech-stack": generate_tech_stack(),
        "source-tree": generate_source_tree(),
        "constitution": generate_constitution(),
        "synapse-digest": generate_synapse_digest(),
    }


# -- CLI ---------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import time

    COMMANDS = {
        "coding-standards": generate_coding_standards,
        "tech-stack": generate_tech_stack,
        "source-tree": generate_source_tree,
        "constitution": generate_constitution,
        "digest": generate_synapse_digest,
    }

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "all":
            start = time.monotonic()
            results = generate_all()
            elapsed = time.monotonic() - start
            for doc_type, path in results.items():
                print(f"Generated: {path}")
            print(f"Completed in {elapsed:.2f}s")
        elif cmd in COMMANDS:
            start = time.monotonic()
            path = COMMANDS[cmd]()
            elapsed = time.monotonic() - start
            print(f"Generated: {path} ({elapsed:.2f}s)")
        else:
            print(f"Unknown command: {cmd}")
            print(f"Usage: python engine.py [{' | '.join([*COMMANDS, 'all'])}]")
            sys.exit(1)
    else:
        # Default: generate all
        start = time.monotonic()
        results = generate_all()
        elapsed = time.monotonic() - start
        for doc_type, path in results.items():
            print(f"Generated: {path}")
        print(f"Completed in {elapsed:.2f}s")
