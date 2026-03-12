#!/usr/bin/env python3
"""
CONTEXT ASSEMBLER - Smart Context Assembly (Phase 1.2)
======================================================
Mounts TRIMMED context per agent based on query analysis.
Reduces CLOSER 542KB → ~30KB by loading only relevant MEMORY sections.

Strategy:
- AGENT.md: first 50 lines (identity header)
- SOUL.md: complete (voice/personality, typically 10-17KB)
- DNA-CONFIG.yaml: complete (routing table, typically 6-24KB)
- MEMORY.md: ONLY sections relevant to query domains (biggest savings)

Zero external deps (stdlib + PyYAML only).

Versao: 1.0.0
Data: 2026-03-01
"""

import re
import sys
from pathlib import Path

from .query_analyzer import analyze_query, discover_agents, load_taxonomy

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DEFAULT_AGENT_HEADER_LINES = 50   # Lines from AGENT.md header
DEFAULT_MEMORY_BUDGET_KB = 30     # Max KB per agent from MEMORY
DEFAULT_MAX_SECTIONS = 10         # Max memory sections per agent
DEFAULT_TOTAL_BUDGET_KB = 150     # Total context budget across all agents

# Files to always load completely (small enough)
ALWAYS_FULL = {"SOUL.md", "DNA-CONFIG.yaml", "SOW.md", "SOW.json"}

# Files to load partially
PARTIAL_LOAD = {"AGENT.md": DEFAULT_AGENT_HEADER_LINES, "MEMORY.md": None}


# ---------------------------------------------------------------------------
# SECTION PARSER
# ---------------------------------------------------------------------------
class MemorySection:
    """Represents a ## section in MEMORY.md."""

    __slots__ = (
        "content",
        "domains_matched",
        "end_line",
        "relevance_score",
        "size_bytes",
        "start_line",
        "title",
    )

    def __init__(self, title: str, content: str, start_line: int, end_line: int):
        self.title = title
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.size_bytes = len(content.encode("utf-8"))
        self.relevance_score: float = 0.0
        self.domains_matched: list[str] = []


def parse_memory_sections(text: str) -> list[MemorySection]:
    """Parse MEMORY.md into ## sections."""
    lines = text.split("\n")
    sections: list[MemorySection] = []
    current_title = ""
    current_lines: list[str] = []
    current_start = 0

    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current_title or current_lines:
                content = "\n".join(current_lines)
                sections.append(MemorySection(
                    title=current_title,
                    content=content,
                    start_line=current_start,
                    end_line=i - 1,
                ))
            current_title = line[3:].strip()
            current_lines = [line]
            current_start = i
        else:
            current_lines.append(line)

    # Last section
    if current_title or current_lines:
        content = "\n".join(current_lines)
        sections.append(MemorySection(
            title=current_title,
            content=content,
            start_line=current_start,
            end_line=len(lines) - 1,
        ))

    return sections


# ---------------------------------------------------------------------------
# SECTION SCORING
# ---------------------------------------------------------------------------

# Priority sections (always include if they exist, regardless of domain match)
PRIORITY_SECTIONS = {
    "TEAM AGREEMENT",
    "QUEM SOU EU",
    "PADRÕES DECISÓRIOS",
    "PADRAO DECISORIO",
    "METADADOS DE CONTEXTO",
    "KNOWLEDGE BASE LOCATIONS",
}

# Low-priority patterns (batch dumps, changelog-like content)
LOW_PRIORITY_PATTERNS = [
    r"CONHECIMENTO CASCATEADO",
    r"BATCH-\d{3}",
    r"HISTÓRICO DE ATUALIZAÇÕES",
    r"PROTOCOLOS APLICÁVEIS",
    r"VALIDAÇÃO DE RASTREABILIDADE",
]


def _build_domain_keywords() -> dict[str, list[str]]:
    """Build domain_id → list of keywords for matching."""
    tax = load_taxonomy()
    domain_kw: dict[str, list[str]] = {}
    for dom in tax.get("dominios", []):
        did = dom["id"]
        keywords = [did, *dom.get("aliases", []), *dom.get("subdominios", [])]
        domain_kw[did] = [k.lower() for k in keywords]
    return domain_kw


def score_section(
    section: MemorySection,
    query_domains: list[dict[str, float]],
    query_tokens: list[str],
) -> float:
    """
    Score a memory section's relevance to the query.

    Scoring:
    - Priority sections: +2.0 base
    - Domain keyword match: +1.0 per match
    - Query token match in title: +0.5 per match
    - Low priority patterns: -1.0
    - Size penalty: sections > 10KB get -0.3
    """
    score = 0.0
    title_lower = section.title.lower()
    content_lower = section.content[:2000].lower()  # Only scan first 2KB

    # Priority sections always included
    for priority in PRIORITY_SECTIONS:
        if priority.lower() in title_lower:
            score += 2.0
            break

    # Low priority penalty
    for pattern in LOW_PRIORITY_PATTERNS:
        if re.search(pattern, section.title, re.IGNORECASE):
            score -= 1.0
            break

    # Domain keyword matching
    domain_kw = _build_domain_keywords()
    domains_matched = []
    for dinfo in query_domains:
        did = dinfo["id"] if isinstance(dinfo, dict) else dinfo
        dscore = dinfo.get("score", 1.0) if isinstance(dinfo, dict) else 1.0
        keywords = domain_kw.get(did, [did.lower()])
        for kw in keywords:
            if kw in title_lower or kw in content_lower:
                score += 1.0 * dscore
                domains_matched.append(did)
                break

    # Query token matching in title
    for token in query_tokens:
        if len(token) > 2 and token in title_lower:
            score += 0.5

    # Size penalty for very large sections
    if section.size_bytes > 10240:
        score -= 0.3

    section.relevance_score = score
    section.domains_matched = list(set(domains_matched))
    return score


# ---------------------------------------------------------------------------
# CONTEXT ASSEMBLY
# ---------------------------------------------------------------------------
def _read_file_safe(path: Path) -> str:
    """Read file with UTF-8, return empty string on error."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _read_file_lines(path: Path, max_lines: int) -> str:
    """Read first N lines of a file."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return "".join(lines)
    except (OSError, UnicodeDecodeError):
        return ""


def assemble_agent_context(
    agent_name: str,
    agent_path: Path,
    query_domains: list[dict],
    query_tokens: list[str],
    memory_budget_kb: int = DEFAULT_MEMORY_BUDGET_KB,
    agent_header_lines: int = DEFAULT_AGENT_HEADER_LINES,
) -> dict:
    """
    Assemble trimmed context for a single agent.

    Returns:
        {
            "agent_name": str,
            "agent_path": str,
            "files": {
                "AGENT.md": str (header only),
                "SOUL.md": str (full),
                "DNA-CONFIG.yaml": str (full),
                "MEMORY.md": str (relevant sections only),
            },
            "total_size_bytes": int,
            "memory_sections_loaded": int,
            "memory_sections_total": int,
            "memory_reduction_pct": float,
        }
    """
    files: dict[str, str] = {}

    # 1. AGENT.md - header only
    agent_md = agent_path / "AGENT.md"
    if agent_md.exists():
        files["AGENT.md"] = _read_file_lines(agent_md, agent_header_lines)

    # 2. SOUL.md - complete
    soul_md = agent_path / "SOUL.md"
    if soul_md.exists():
        files["SOUL.md"] = _read_file_safe(soul_md)

    # 3. DNA-CONFIG.yaml - complete
    dna_config = agent_path / "DNA-CONFIG.yaml"
    if dna_config.exists():
        files["DNA-CONFIG.yaml"] = _read_file_safe(dna_config)

    # 4. MEMORY - trimmed by relevance
    #    Supports both monolithic MEMORY.md and split memory/ directory
    memory_md = agent_path / "MEMORY.md"
    memory_dir = agent_path / "memory"
    memory_sections_total = 0
    memory_sections_loaded = 0
    original_memory_size = 0

    # Load sections from split domain files or monolithic MEMORY.md
    sections: list[MemorySection] = []
    if memory_dir.exists() and memory_dir.is_dir():
        # Split memory: load from domain files
        for domain_file in sorted(memory_dir.glob("*.md")):
            domain_text = _read_file_safe(domain_file)
            original_memory_size += len(domain_text.encode("utf-8"))
            sections.extend(parse_memory_sections(domain_text))
        # Also include index MEMORY.md sections (priority sections)
        if memory_md.exists():
            index_text = _read_file_safe(memory_md)
            original_memory_size += len(index_text.encode("utf-8"))
            sections.extend(parse_memory_sections(index_text))
    elif memory_md.exists():
        # Monolithic MEMORY.md
        full_memory = _read_file_safe(memory_md)
        original_memory_size = len(full_memory.encode("utf-8"))
        sections = parse_memory_sections(full_memory)

    if sections:
        memory_sections_total = len(sections)

        # Score all sections
        for sec in sections:
            score_section(sec, query_domains, query_tokens)

        # Sort by relevance (highest first)
        sections.sort(key=lambda s: -s.relevance_score)

        # Select sections within budget
        budget_bytes = memory_budget_kb * 1024
        selected: list[MemorySection] = []
        current_bytes = 0

        for sec in sections:
            # Always include priority sections
            is_priority = any(
                p.lower() in sec.title.lower() for p in PRIORITY_SECTIONS
            )
            if sec.relevance_score <= -0.5 and not is_priority:
                continue
            if current_bytes + sec.size_bytes > budget_bytes and not is_priority:
                continue
            selected.append(sec)
            current_bytes += sec.size_bytes
            if current_bytes >= budget_bytes:
                break

        # Sort selected by original order (preserve document flow)
        selected.sort(key=lambda s: s.start_line)

        # Build trimmed memory
        memory_parts = [
            f"# MEMORY (trimmed: {len(selected)}/{memory_sections_total} sections, "
            f"query-relevant)\n"
        ]
        for sec in selected:
            memory_parts.append(sec.content)
        files["MEMORY.md"] = "\n\n".join(memory_parts)
        memory_sections_loaded = len(selected)

    # Calculate totals
    total_size = sum(len(v.encode("utf-8")) for v in files.values())
    reduction = 0.0
    if original_memory_size > 0:
        trimmed_size = len(files.get("MEMORY.md", "").encode("utf-8"))
        reduction = (1 - trimmed_size / original_memory_size) * 100

    return {
        "agent_name": agent_name,
        "agent_path": str(agent_path),
        "files": files,
        "total_size_bytes": total_size,
        "total_size_kb": round(total_size / 1024, 1),
        "memory_sections_loaded": memory_sections_loaded,
        "memory_sections_total": memory_sections_total,
        "memory_reduction_pct": round(reduction, 1),
    }


def assemble_debate_context(
    query: str,
    agent_names: list[str] | None = None,
    max_agents: int = 5,
    total_budget_kb: int = DEFAULT_TOTAL_BUDGET_KB,
) -> dict:
    """
    Assemble context for a full debate/conclave session.

    If agent_names is provided, uses those specific agents.
    Otherwise, auto-selects based on query analysis.

    Returns:
        {
            "query": str,
            "analysis": dict (from query_analyzer),
            "agents": [
                {
                    "agent_name": str,
                    "files": {...},
                    "total_size_kb": float,
                    ...
                }
            ],
            "total_context_kb": float,
            "savings_vs_full_load": str,
        }
    """
    # Analyze query
    analysis = analyze_query(query, max_agents=max_agents)
    available = discover_agents()

    # Determine which agents to load
    if agent_names:
        # User specified agents
        agents_to_load = []
        for name in agent_names:
            canonical = name.upper().replace("_", "-")
            if canonical in available:
                agents_to_load.append((canonical, 1.0, "user-specified"))
            else:
                # Try fuzzy match on directory names
                for avail_name in available:
                    if canonical in avail_name or avail_name in canonical:
                        agents_to_load.append((avail_name, 0.9, "fuzzy-match"))
                        break
    else:
        # Auto-select from analysis
        agents_to_load = [
            (a["name"], a["score"], a["reason"])
            for a in analysis["recommended_agents"]
        ]

    # Calculate per-agent budget
    num_agents = max(len(agents_to_load), 1)
    per_agent_budget = total_budget_kb // num_agents

    # Extract query tokens for section scoring
    query_lower = query.lower()
    query_tokens = [
        t for t in re.sub(r"[^\w\s-]", " ", query_lower).split()
        if len(t) > 2
    ]

    # Assemble context for each agent
    agent_contexts = []
    for agent_name, score, reason in agents_to_load:
        if agent_name not in available:
            continue
        ctx = assemble_agent_context(
            agent_name=agent_name,
            agent_path=available[agent_name],
            query_domains=analysis["domains"],
            query_tokens=query_tokens,
            memory_budget_kb=per_agent_budget,
        )
        ctx["selection_score"] = score
        ctx["selection_reason"] = reason
        agent_contexts.append(ctx)

    total_kb = sum(a["total_size_kb"] for a in agent_contexts)

    return {
        "query": query,
        "analysis": analysis,
        "agents": agent_contexts,
        "total_context_kb": round(total_kb, 1),
        "agent_count": len(agent_contexts),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m core.intelligence.context_assembler \"<query>\" [agent1,agent2]")
        print("Example: python3 -m core.intelligence.context_assembler \"Devo mudar comissao?\" CRO,CFO,CLOSER")
        sys.exit(1)

    query = sys.argv[1]
    agent_names = None
    if len(sys.argv) > 2:
        agent_names = [a.strip() for a in sys.argv[2].split(",")]

    result = assemble_debate_context(query, agent_names=agent_names)

    print(f"\n{'='*70}")
    print("CONTEXT ASSEMBLY")
    print(f"{'='*70}")
    print(f"Query: {result['query']}")
    print(f"Agents: {result['agent_count']}")
    print(f"Total context: {result['total_context_kb']}KB")
    print()

    for ctx in result["agents"]:
        print(f"  {ctx['agent_name']}:")
        print(f"    Size: {ctx['total_size_kb']}KB")
        print(f"    MEMORY: {ctx['memory_sections_loaded']}/{ctx['memory_sections_total']} sections")
        print(f"    MEMORY reduction: {ctx['memory_reduction_pct']}%")
        print(f"    Reason: {ctx.get('selection_reason', 'N/A')}")
        print()

    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
