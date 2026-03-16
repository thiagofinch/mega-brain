#!/usr/bin/env python3
"""
CONTEXT ASSEMBLER - Smart Context Assembly (Phase 1.2 + Phase 3 RAG)
=====================================================================
Mounts TRIMMED context per agent based on query analysis.
Reduces CLOSER 542KB → ~30KB by loading only relevant MEMORY sections.
Phase 3 addition: augments file-based context with RAG semantic search.

Strategy:
- AGENT.md: first 50 lines (identity header)
- SOUL.md: complete (voice/personality, typically 10-17KB)
- DNA-CONFIG.yaml: complete (routing table, typically 6-24KB)
- MEMORY.md: ONLY sections relevant to query domains (biggest savings)
- RAG_CONTEXT: top-K chunks from bucket-filtered semantic search (Phase 3)

Zero external deps (stdlib + PyYAML only).

Versao: 2.0.0
Data: 2026-03-16
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

from .query_analyzer import analyze_query, discover_agents, load_taxonomy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DEFAULT_AGENT_HEADER_LINES = 50  # Lines from AGENT.md header
DEFAULT_MEMORY_BUDGET_KB = 30  # Max KB per agent from MEMORY
DEFAULT_MAX_SECTIONS = 10  # Max memory sections per agent
DEFAULT_TOTAL_BUDGET_KB = 150  # Total context budget across all agents

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
                sections.append(
                    MemorySection(
                        title=current_title,
                        content=content,
                        start_line=current_start,
                        end_line=i - 1,
                    )
                )
            current_title = line[3:].strip()
            current_lines = [line]
            current_start = i
        else:
            current_lines.append(line)

    # Last section
    if current_title or current_lines:
        content = "\n".join(current_lines)
        sections.append(
            MemorySection(
                title=current_title,
                content=content,
                start_line=current_start,
                end_line=len(lines) - 1,
            )
        )

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
            is_priority = any(p.lower() in sec.title.lower() for p in PRIORITY_SECTIONS)
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


# ---------------------------------------------------------------------------
# RAG SEARCH (Phase 3 -- bucket-filtered semantic search)
# ---------------------------------------------------------------------------
DEFAULT_RAG_TOP_K = 8  # Chunks per bucket search
DEFAULT_RAG_MAX_BUDGET_KB = 30  # Max KB for RAG context (from total budget)

# Mode → allowed buckets for RAG search
MODE_TO_BUCKETS: dict[str, list[str]] = {
    "expert-only": ["external"],
    "business": ["external", "business"],
    "full-3d": ["external", "business", "personal"],
    "personal": ["personal"],
    "company-only": ["business"],
}


def _search_rag_buckets(
    query: str,
    buckets: list[str],
    max_chars: int,
    top_k: int = DEFAULT_RAG_TOP_K,
) -> dict:
    """Search RAG indexes across specified buckets, return formatted context.

    Uses bucket_query_router for per-bucket search with graceful degradation:
    if indexes are missing or the import fails, returns empty results.

    Args:
        query: The search query.
        buckets: Which knowledge buckets to search (e.g. ["external", "business"]).
        max_chars: Maximum characters for RAG context output.
        top_k: Number of results per bucket search.

    Returns:
        {
            "context": str (formatted RAG chunks for LLM consumption),
            "sources": [{"chunk_id", "source_file", "person", "bucket", "score"}],
            "chunks_used": int,
            "total_chars": int,
            "error": str | None,
        }
    """
    try:
        from core.intelligence.rag.bucket_query_router import query as rag_query
    except ImportError as exc:
        logger.debug("RAG bucket_query_router not available: %s", exc)
        return {
            "context": "",
            "sources": [],
            "chunks_used": 0,
            "total_chars": 0,
            "error": f"bucket_query_router import failed: {exc}",
        }

    all_results: list[dict] = []
    for bucket in buckets:
        try:
            results = rag_query(query, bucket=bucket, top_k=top_k)
            all_results.extend(results)
        except Exception as exc:
            logger.debug("RAG search failed for bucket '%s': %s", bucket, exc)
            continue

    if not all_results:
        return {
            "context": "",
            "sources": [],
            "chunks_used": 0,
            "total_chars": 0,
            "error": None,
        }

    # Sort merged results by score descending
    all_results.sort(key=lambda r: r.get("score", 0), reverse=True)

    # Deduplicate by chunk_id
    seen_ids: set[str] = set()
    unique_results: list[dict] = []
    for item in all_results:
        cid = item.get("chunk_id", "")
        if cid and cid in seen_ids:
            continue
        if cid:
            seen_ids.add(cid)
        unique_results.append(item)

    # Build context string within char budget
    parts: list[str] = []
    sources: list[dict] = []
    total_chars = 0

    for r in unique_results:
        text = r.get("text_preview", r.get("text", ""))
        if not text:
            continue

        chunk_id = r.get("chunk_id", "")
        person = r.get("person", "")
        bucket_name = r.get("bucket", "")

        entry = f"[RAG:{chunk_id}]"
        if person:
            entry += f" ({person})"
        if bucket_name:
            entry += f" [{bucket_name}]"
        entry += f" {text}"

        if total_chars + len(entry) > max_chars:
            break

        parts.append(entry)
        sources.append({
            "chunk_id": chunk_id,
            "source_file": r.get("source_file", ""),
            "person": person,
            "bucket": bucket_name,
            "score": r.get("score", 0),
        })
        total_chars += len(entry)

    return {
        "context": "\n\n".join(parts),
        "sources": sources,
        "chunks_used": len(sources),
        "total_chars": total_chars,
        "error": None,
    }


def _determine_rag_buckets(analysis: dict) -> list[str]:
    """Determine which RAG buckets to search based on query analysis.

    Uses domain signals to infer the Conclave mode, then maps to buckets.
    Falls back to ["external"] if no strong signal is detected.
    """
    domains = analysis.get("domains", [])
    domain_ids = {d["id"] if isinstance(d, dict) else d for d in domains}

    # Business signals: operacoes, financeiro, hiring
    business_domains = {"operacoes", "financeiro", "hiring"}
    has_business = bool(domain_ids & business_domains)

    # Default to external (expert knowledge)
    if has_business:
        return ["external", "business"]
    return ["external"]


def assemble_debate_context(
    query: str,
    agent_names: list[str] | None = None,
    max_agents: int = 5,
    total_budget_kb: int = DEFAULT_TOTAL_BUDGET_KB,
    use_rag: bool = True,
    rag_buckets: list[str] | None = None,
    rag_top_k: int = DEFAULT_RAG_TOP_K,
) -> dict:
    """
    Assemble context for a full debate/conclave session.

    If agent_names is provided, uses those specific agents.
    Otherwise, auto-selects based on query analysis.

    Phase 3 addition: when use_rag=True, augments file-based agent context
    with semantically relevant RAG chunks from bucket-filtered indexes.
    RAG uses remaining budget after file-based context is assembled.

    Args:
        query: The strategic question to debate.
        agent_names: Explicit agent list, or None for auto-selection.
        max_agents: Maximum agents to auto-select.
        total_budget_kb: Total context budget in KB (~150KB default).
        use_rag: If True, append RAG semantic search results (default: True).
        rag_buckets: Explicit bucket list for RAG. If None, auto-detected
            from query domains (e.g. expert-only=["external"],
            business=["external","business"]).
        rag_top_k: Number of RAG chunks to retrieve per bucket.

    Returns:
        {
            "query": str,
            "analysis": dict (from query_analyzer),
            "agents": [{...agent context...}],
            "total_context_kb": float,
            "agent_count": int,
            "rag_context": str (formatted RAG chunks, or "" if disabled/failed),
            "rag_sources": [{"chunk_id", "source_file", "person", "bucket", "score"}],
            "rag_chunks_used": int,
            "rag_error": str | None,
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
            (a["name"], a["score"], a["reason"]) for a in analysis["recommended_agents"]
        ]

    # Calculate per-agent budget (reserve RAG budget from total)
    rag_budget_kb = DEFAULT_RAG_MAX_BUDGET_KB if use_rag else 0
    file_budget_kb = total_budget_kb - rag_budget_kb
    num_agents = max(len(agents_to_load), 1)
    per_agent_budget = file_budget_kb // num_agents

    # Extract query tokens for section scoring
    query_lower = query.lower()
    query_tokens = [t for t in re.sub(r"[^\w\s-]", " ", query_lower).split() if len(t) > 2]

    # Assemble context for each agent (file-based)
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

    file_total_kb = sum(a["total_size_kb"] for a in agent_contexts)

    # --- Phase 3: RAG semantic search augmentation ---
    rag_result: dict = {
        "context": "",
        "sources": [],
        "chunks_used": 0,
        "total_chars": 0,
        "error": None,
    }

    if use_rag:
        # Determine remaining budget for RAG
        file_total_bytes = int(file_total_kb * 1024)
        total_budget_bytes = total_budget_kb * 1024
        remaining_bytes = max(total_budget_bytes - file_total_bytes, 0)
        # Cap RAG to its own budget or remaining space, whichever is smaller
        rag_max_chars = min(rag_budget_kb * 1024, remaining_bytes)

        if rag_max_chars > 0:
            # Determine buckets: explicit > auto-detected from analysis
            effective_buckets = rag_buckets or _determine_rag_buckets(analysis)

            try:
                rag_result = _search_rag_buckets(
                    query=query,
                    buckets=effective_buckets,
                    max_chars=rag_max_chars,
                    top_k=rag_top_k,
                )
            except Exception as exc:
                logger.warning("RAG search failed, continuing without: %s", exc)
                rag_result["error"] = str(exc)

    # Calculate total including RAG
    rag_kb = round(rag_result.get("total_chars", 0) / 1024, 1)
    total_kb = round(file_total_kb + rag_kb, 1)

    return {
        "query": query,
        "analysis": analysis,
        "agents": agent_contexts,
        "total_context_kb": total_kb,
        "agent_count": len(agent_contexts),
        # RAG context (Phase 3)
        "rag_context": rag_result.get("context", ""),
        "rag_sources": rag_result.get("sources", []),
        "rag_chunks_used": rag_result.get("chunks_used", 0),
        "rag_error": rag_result.get("error"),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print('Usage: python3 -m core.intelligence.context_assembler "<query>" [agent1,agent2]')
        print(
            'Example: python3 -m core.intelligence.context_assembler "Devo mudar comissao?" CRO,CFO,CLOSER'
        )
        sys.exit(1)

    query = sys.argv[1]
    agent_names = None
    if len(sys.argv) > 2:
        agent_names = [a.strip() for a in sys.argv[2].split(",")]

    result = assemble_debate_context(query, agent_names=agent_names)

    print(f"\n{'=' * 70}")
    print("CONTEXT ASSEMBLY (v2 + RAG)")
    print(f"{'=' * 70}")
    print(f"Query: {result['query']}")
    print(f"Agents: {result['agent_count']}")
    print(f"Total context: {result['total_context_kb']}KB")
    print()

    for ctx in result["agents"]:
        print(f"  {ctx['agent_name']}:")
        print(f"    Size: {ctx['total_size_kb']}KB")
        print(
            f"    MEMORY: {ctx['memory_sections_loaded']}/{ctx['memory_sections_total']} sections"
        )
        print(f"    MEMORY reduction: {ctx['memory_reduction_pct']}%")
        print(f"    Reason: {ctx.get('selection_reason', 'N/A')}")
        print()

    # RAG context stats (Phase 3)
    rag_chunks = result.get("rag_chunks_used", 0)
    rag_error = result.get("rag_error")
    if rag_chunks > 0:
        rag_sources = result.get("rag_sources", [])
        buckets_hit = sorted({s.get("bucket", "?") for s in rag_sources})
        print("  RAG Context:")
        print(f"    Chunks used: {rag_chunks}")
        print(f"    Buckets searched: {', '.join(buckets_hit)}")
        print("    Top sources:")
        for src in rag_sources[:5]:
            print(f"      [{src.get('bucket', '?')}] {src.get('chunk_id', '?')} "
                  f"(score: {src.get('score', 0):.4f})")
        print()
    elif rag_error:
        print(f"  RAG Context: unavailable ({rag_error})")
        print()
    else:
        print("  RAG Context: no results")
        print()

    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
