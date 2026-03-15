"""
Synapse Rule Engine v1.0 — 7-Layer Rule Resolution

Loads rules from YAML files organized by layer (L0-L6).
Each layer can return rules or None (graceful degradation).
Precedence: L0 > L1 > L2 > ... > L6 (lower layers override higher).

Layers:
  L0: Constitution (non-negotiable, always loaded)
  L1: Global rules (project-wide)
  L2: Agent rules (per-agent overrides)
  L3: Workflow rules (pipeline-specific)
  L4: Task rules (task-specific gates)
  L5: Squad rules (squad policies)
  L6: Keyword rules (context-detected, keyword matching)

Usage:
  from core.engine.synapse import resolve_rules
  rules = resolve_rules(agent_id="closer", workflow="mce", keywords=["batch"])

Epic 5.1 — Rule Engine
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
RULES_DIR = ROOT / "core" / "engine" / "rules"

# Timeout per layer in seconds (graceful degradation)
LAYER_TIMEOUT_MS = 15

# Layer definitions
LAYERS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
LAYER_NAMES = {
    "L0": "constitution",
    "L1": "global",
    "L2": "agent",
    "L3": "workflow",
    "L4": "task",
    "L5": "squad",
    "L6": "keyword",
}


@dataclass
class Rule:
    """A single rule entry."""

    id: str
    layer: str
    severity: str  # block | warn | info
    description: str
    condition: str = ""
    action: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class RuleSet:
    """Resolved rule set from all layers."""

    rules: list[Rule] = field(default_factory=list)
    layers_loaded: list[str] = field(default_factory=list)
    layers_failed: list[str] = field(default_factory=list)
    resolve_time_ms: float = 0.0

    @property
    def blocks(self) -> list[Rule]:
        return [r for r in self.rules if r.severity == "block"]

    @property
    def warnings(self) -> list[Rule]:
        return [r for r in self.rules if r.severity == "warn"]

    @property
    def has_blocks(self) -> bool:
        return any(r.severity == "block" for r in self.rules)


# ── Layer Loaders ─────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> list[dict]:
    """Load rules from a YAML file. Returns empty list on failure."""
    if not path.exists():
        return []
    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return data.get("rules", [])
    except Exception:
        return []


def _parse_rules(raw_rules: list[dict], layer: str) -> list[Rule]:
    """Parse raw YAML dicts into Rule objects."""
    rules = []
    for r in raw_rules:
        if not isinstance(r, dict):
            continue
        rules.append(Rule(
            id=r.get("id", "unknown"),
            layer=layer,
            severity=r.get("severity", "info"),
            description=r.get("description", ""),
            condition=r.get("condition", ""),
            action=r.get("action", ""),
            tags=r.get("tags", []),
        ))
    return rules


def load_l0_constitution() -> list[Rule]:
    """L0: Constitution — always loaded, non-negotiable."""
    return _parse_rules(_load_yaml(RULES_DIR / "L0-constitution.yaml"), "L0")


def load_l1_global() -> list[Rule]:
    """L1: Global project rules."""
    return _parse_rules(_load_yaml(RULES_DIR / "L1-global.yaml"), "L1")


def load_l2_agent(agent_id: str | None) -> list[Rule]:
    """L2: Agent-specific rules."""
    if not agent_id:
        return []
    path = RULES_DIR / "agents" / f"{agent_id}.yaml"
    return _parse_rules(_load_yaml(path), "L2")


def load_l3_workflow(workflow: str | None) -> list[Rule]:
    """L3: Workflow-specific rules."""
    if not workflow:
        return []
    path = RULES_DIR / "workflows" / f"{workflow}.yaml"
    return _parse_rules(_load_yaml(path), "L3")


def load_l4_task(task: str | None) -> list[Rule]:
    """L4: Task-specific gates."""
    if not task:
        return []
    path = RULES_DIR / "tasks" / f"{task}.yaml"
    return _parse_rules(_load_yaml(path), "L4")


def load_l5_squad(squad: str | None) -> list[Rule]:
    """L5: Squad policies."""
    if not squad:
        return []
    path = RULES_DIR / "squads" / f"{squad}.yaml"
    return _parse_rules(_load_yaml(path), "L5")


def load_l6_keyword(keywords: list[str] | None) -> list[Rule]:
    """L6: Keyword-triggered rules."""
    if not keywords:
        return []
    rules = []
    all_keyword_rules = _load_yaml(RULES_DIR / "L6-keywords.yaml")
    parsed = _parse_rules(all_keyword_rules, "L6")
    for rule in parsed:
        rule_tags = {t.lower() for t in rule.tags}
        if any(kw.lower() in rule_tags for kw in keywords):
            rules.append(rule)
    return rules


# ── Main Resolver ─────────────────────────────────────────────────────────


def resolve_rules(
    agent_id: str | None = None,
    workflow: str | None = None,
    task: str | None = None,
    squad: str | None = None,
    keywords: list[str] | None = None,
) -> RuleSet:
    """Resolve all applicable rules across 7 layers.

    Each layer is loaded independently with graceful degradation.
    If a layer fails or times out, it's skipped and logged.

    Args:
        agent_id: Active agent (for L2)
        workflow: Active workflow name (for L3)
        task: Active task name (for L4)
        squad: Active squad name (for L5)
        keywords: Keywords from prompt (for L6)

    Returns:
        RuleSet with all resolved rules, ordered by precedence (L0 first).
    """
    t0 = time.time()

    loaders = [
        ("L0", lambda: load_l0_constitution()),
        ("L1", lambda: load_l1_global()),
        ("L2", lambda: load_l2_agent(agent_id)),
        ("L3", lambda: load_l3_workflow(workflow)),
        ("L4", lambda: load_l4_task(task)),
        ("L5", lambda: load_l5_squad(squad)),
        ("L6", lambda: load_l6_keyword(keywords)),
    ]

    all_rules: list[Rule] = []
    loaded: list[str] = []
    failed: list[str] = []

    for layer_name, loader in loaders:
        try:
            rules = loader()
            if rules:
                all_rules.extend(rules)
                loaded.append(layer_name)
        except Exception:
            failed.append(layer_name)

    # Deduplicate by rule ID (lower layer wins — L0 beats L6)
    seen_ids: set[str] = set()
    deduped: list[Rule] = []
    for rule in all_rules:
        if rule.id not in seen_ids:
            seen_ids.add(rule.id)
            deduped.append(rule)

    return RuleSet(
        rules=deduped,
        layers_loaded=loaded,
        layers_failed=failed,
        resolve_time_ms=round((time.time() - t0) * 1000, 1),
    )


# ── Seed Rules ────────────────────────────────────────────────────────────


def seed_rules():
    """Create initial rule YAML files from existing .claude/rules/*.md content.

    This extracts the core principles from the markdown rules into
    machine-readable YAML format. Only creates files if they don't exist.
    """
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    for subdir in ["agents", "workflows", "tasks", "squads"]:
        (RULES_DIR / subdir).mkdir(exist_ok=True)

    # L0: Constitution
    l0_path = RULES_DIR / "L0-constitution.yaml"
    if not l0_path.exists():
        l0 = {
            "layer": "L0",
            "name": "Constitution",
            "description": "Non-negotiable rules that always apply",
            "rules": [
                {
                    "id": "no-secrets-in-files",
                    "severity": "block",
                    "description": "Never store API keys, tokens, or credentials in tracked files",
                    "tags": ["security"],
                },
                {
                    "id": "no-hardcoded-paths",
                    "severity": "warn",
                    "description": "Use core.paths ROUTING constants, not hardcoded paths",
                    "tags": ["architecture"],
                },
                {
                    "id": "epistemic-honesty",
                    "severity": "warn",
                    "description": "Separate facts (with sources) from recommendations. Declare confidence level.",
                    "tags": ["quality"],
                },
                {
                    "id": "agent-integrity",
                    "severity": "block",
                    "description": "All agent content must be 100% traceable to sources. Zero invention.",
                    "tags": ["agents"],
                },
            ],
        }
        with open(l0_path, "w") as f:
            yaml.dump(l0, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # L1: Global
    l1_path = RULES_DIR / "L1-global.yaml"
    if not l1_path.exists():
        l1 = {
            "layer": "L1",
            "name": "Global Rules",
            "description": "Project-wide rules for all contexts",
            "rules": [
                {
                    "id": "sequential-processing",
                    "severity": "warn",
                    "description": "Do not advance pipeline steps without completing the current one",
                    "tags": ["pipeline"],
                },
                {
                    "id": "dual-location-logging",
                    "severity": "info",
                    "description": "Pipeline processing generates logs in both markdown and JSONL",
                    "tags": ["logging"],
                },
                {
                    "id": "directory-contract",
                    "severity": "warn",
                    "description": "All output must land in paths defined by core/paths.py ROUTING",
                    "tags": ["architecture", "governance"],
                },
                {
                    "id": "template-enforcement",
                    "severity": "warn",
                    "description": "Agent creation must follow Template V3 structure",
                    "tags": ["agents", "templates"],
                },
                {
                    "id": "cascading-mandatory",
                    "severity": "warn",
                    "description": "Knowledge cascading to dossiers, playbooks, agents is mandatory after extraction",
                    "tags": ["pipeline", "knowledge"],
                },
            ],
        }
        with open(l1_path, "w") as f:
            yaml.dump(l1, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # L6: Keywords
    l6_path = RULES_DIR / "L6-keywords.yaml"
    if not l6_path.exists():
        l6 = {
            "layer": "L6",
            "name": "Keyword Rules",
            "description": "Rules triggered by keyword detection in prompts",
            "rules": [
                {
                    "id": "batch-processing-rules",
                    "severity": "info",
                    "description": "Batch processing: log every batch, update state, verify before advancing",
                    "tags": ["batch", "pipeline", "processing"],
                },
                {
                    "id": "agent-creation-rules",
                    "severity": "info",
                    "description": "Agent creation: use Template V3, include 11 parts, traceable citations",
                    "tags": ["agent", "create", "dossier"],
                },
                {
                    "id": "github-workflow-rules",
                    "severity": "info",
                    "description": "Code changes: follow Issue→Branch→PR→Merge workflow",
                    "tags": ["github", "git", "push", "pr", "branch"],
                },
            ],
        }
        with open(l6_path, "w") as f:
            yaml.dump(l6, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"[Synapse] Seeded rules in {RULES_DIR}")


# ── CLI ───────────────────────────────────────────────────────────────────


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        seed_rules()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "resolve":
        keywords = sys.argv[2:] if len(sys.argv) > 2 else None
        result = resolve_rules(keywords=keywords)
        print(f"[Synapse] Resolved {len(result.rules)} rules in {result.resolve_time_ms}ms")
        print(f"  Layers loaded: {result.layers_loaded}")
        if result.layers_failed:
            print(f"  Layers failed: {result.layers_failed}")
        for rule in result.rules:
            icon = {"block": "⛔", "warn": "⚠", "info": "ℹ"}.get(rule.severity, "?")
            print(f"  {icon} [{rule.layer}] {rule.id}: {rule.description}")
        return

    print("Usage:")
    print("  python3 -m core.engine.synapse seed              # Create initial rule files")
    print("  python3 -m core.engine.synapse resolve [keywords] # Resolve rules")


if __name__ == "__main__":
    main()
