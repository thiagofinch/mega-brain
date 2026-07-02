#!/usr/bin/env python3
"""
post_task_suggester.py — Post-Task Capability Suggester (TIL-13)

Hook: Stop
Default: OPT-IN OFF. Reads mega-brain-core/core-config.yaml `post_task_suggestions.enabled`.
When disabled, returns zero-cost no-op within first 5ms.

PURPOSE
-------
Closes the "capability discovery gap": after every turn, scans recent conversation
for entities/intents the agent worked with and suggests AT MOST 1 capability that
was relevant but not used. Authority-aware: if current agent lacks permission,
suggests delegating to the right agent.

7-STEP PIPELINE (AC2)
---------------------
1. Read last N=5 turns from session transcript (transcript_path in stdin payload)
2. Extract entities/intents via pattern matching (regex + verb/noun list)
3. Cross-reference capability registry — keyword index fast path, embedding fallback
4. Filter out capabilities USED in last 3 turns (anti-repetition)
5. Filter by authority — drop capabilities the current agent isn't authorized to invoke
6. Rank by similarity x context_cost preference (low > medium > high)
7. Output max 1 suggestion (≥0.70 confidence threshold)

AUTHORITY-AWARE OUTPUT (AC3)
---------------------------
- If current agent CAN use cap: "Capability disponível: `{id}` via `{provider}`."
- If current agent CANNOT use cap: "Capability `{id}` could help here. Delegate to `@{agent}`."

TELEMETRY (AC6)
---------------
Appends a JSON line to .data/capability-hints-metrics.jsonl with event_type="post_task".

FAIL-OPEN — never blocks the Stop event. Any error swallowed, returns {"continue": True}.

Story: TIL-13 (Wave 3)
ADR: ADR-TIL-001 (hooks dir = Python only)
@po BLOCKERS resolved (2026-05-12):
  1. Path = .claude/hooks/post_task_suggester.py (not scripts/tool-onboarder/)
  2. AUTHORITY_BLOCKLIST hardcoded (TODO TIL-23 — proper machine-readable registry)
  3. core-config.yaml `post_task_suggestions` section added
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
CONFIG_PATH = PROJECT_ROOT / "mega-brain-core" / "core-config.yaml"
INDEX_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-keyword-index.json"
REGISTRY_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-registry.yaml"
DATA_DIR = PROJECT_ROOT / ".data"
EMB_PATH = DATA_DIR / "capability-embeddings.npy"
META_PATH = DATA_DIR / "capability-embeddings-meta.json"
METRICS_PATH = DATA_DIR / "capability-hints-metrics.jsonl"

# AC2 — pipeline knobs
N_TURNS_TO_READ = 5
N_TURNS_DEDUP = 3
MAX_SUGGESTIONS_PER_TURN = 1
SEMANTIC_TOP_K = 5

# AC4 — anti-noise defaults (overridable by core-config.yaml)
DEFAULT_CONFIDENCE_THRESHOLD = 0.70
DEFAULT_TRIVIAL_WORD_THRESHOLD = 50
DEFAULT_MAX_PER_TURN = 1

# AC3 — Authority blocklist (TODO TIL-23 — proper machine-readable authority registry)
# Mirrors `.claude/rules/agent-authority.md` Exclusive Authorities table.
# Format: operation_id -> allowed agent ids (no "@" prefix). 8 entries.
AUTHORITY_BLOCKLIST: dict[str, dict] = {
    "git_push": {"allowed_agents": ["devops", "mega-brain-master"]},
    "mcp_management": {"allowed_agents": ["devops", "mega-brain-master"]},
    "ci_cd_release": {"allowed_agents": ["devops", "mega-brain-master"]},
    "execute_epic": {"allowed_agents": ["pm", "mega-brain-master"]},
    "validate_story_draft": {"allowed_agents": ["po", "mega-brain-master"]},
    "create_story": {"allowed_agents": ["sm", "mega-brain-master"]},
    "story_scope_edit": {"allowed_agents": ["po", "mega-brain-master"]},
    "schema_ddl": {"allowed_agents": ["data-engineer", "architect", "mega-brain-master"]},
}

# Capability-to-operation mapping (for authority enforcement).
# Empty entry = capability is free (no exclusive authority).
CAPABILITY_AUTHORITY_HINTS: dict[str, str] = {
    "github_pr": "git_push",
}

# Context cost preference for ranking (AC2 step 6)
CONTEXT_COST_WEIGHT = {"low": 1.0, "medium": 0.85, "high": 0.65, None: 0.9, "unknown": 0.9}

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _append_metric(entry: dict) -> None:
    """Append one JSONL line to telemetry. Best-effort, never raise."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with METRICS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _get_active_agent_id() -> str:
    """Resolve active agent id. NOT MEGABRAIN_ACTIVE_AGENT (per @po clarification)."""
    return os.environ.get("CLAUDE_AGENT_ID") or os.environ.get("AGENT_ID") or "claude-main"


# ---------------------------------------------------------------------------
# Config — AC7 opt-in gate
# ---------------------------------------------------------------------------


def _load_config() -> dict:
    """Load post_task_suggestions section from core-config.yaml.

    Returns defaults (enabled=False) if file missing, section absent, or YAML broken.
    """
    defaults = {
        "enabled": False,
        "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        "max_per_turn": DEFAULT_MAX_PER_TURN,
        "trivial_word_threshold": DEFAULT_TRIVIAL_WORD_THRESHOLD,
    }
    try:
        import yaml  # PyYAML
    except ImportError:
        return defaults
    try:
        if not CONFIG_PATH.exists():
            return defaults
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        section = data.get("post_task_suggestions") or {}
        defaults.update({k: v for k, v in section.items() if k in defaults})
        return defaults
    except Exception:
        return defaults


# ---------------------------------------------------------------------------
# Transcript reading — AC2 step 1
# ---------------------------------------------------------------------------


def _read_transcript_turns(transcript_path: str | None, n: int = N_TURNS_TO_READ) -> list[dict]:
    """Read last N turns from a Claude Code transcript JSONL file.

    Returns list of dicts: [{"role": ..., "text": ..., "tools_used": [...]}, ...]
    Empty list on any error or missing file.
    """
    if not transcript_path:
        return []
    p = Path(transcript_path)
    if not p.exists() or not p.is_file():
        return []

    entries: list[dict] = []
    try:
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []

    # Reduce to {role, text, tools_used} per turn (user OR assistant).
    turns: list[dict] = []
    for entry in entries:
        msg = entry.get("message") or entry
        role = msg.get("role") or entry.get("type") or ""
        if role not in ("user", "assistant"):
            continue
        content = msg.get("content")
        text_parts: list[str] = []
        tools_used: list[str] = []
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "text":
                    t = block.get("text") or ""
                    if t:
                        text_parts.append(t)
                elif btype == "tool_use":
                    tname = block.get("name")
                    if tname:
                        tools_used.append(str(tname))
                elif btype == "tool_result":
                    tc = block.get("content")
                    if isinstance(tc, list):
                        for sub in tc:
                            if isinstance(sub, dict) and sub.get("type") == "text":
                                text_parts.append(sub.get("text") or "")
                    elif isinstance(tc, str):
                        text_parts.append(tc)
        text = "\n".join(t for t in text_parts if t)
        turns.append({"role": role, "text": text, "tools_used": tools_used})

    return turns[-n:] if len(turns) > n else turns


# ---------------------------------------------------------------------------
# Trivial-turn detection — AC4c
# ---------------------------------------------------------------------------


def _is_trivial_turn(turns: list[dict], word_threshold: int) -> bool:
    """True if recent assistant activity is genuinely trivial.

    A turn is trivial ONLY if the AGGREGATE of recent assistant work is small.
    Looking at just the last assistant message produces false positives:
    the last assistant turn is often a short ack ("Feito, status OK") while
    the substantive work happened in earlier assistant turns (with tool calls).

    Trivial = (no tool calls across ANY recent assistant turn)
              AND (total assistant words < threshold)

    Regression fix 2026-05-13 (founder runtime probe):
    Original `last_assistant` logic missed tool_use in turn N when turn N+1
    was a short ack. Aggregate fix prevents that false-positive trivial flag.
    """
    assistant_turns = [t for t in turns if t.get("role") == "assistant"]
    if not assistant_turns:
        return True  # nothing to react to

    # Aggregate tool usage across recent assistant turns
    any_tool_calls = any(t.get("tools_used") for t in assistant_turns)
    if any_tool_calls:
        return False  # substantive work happened — not trivial

    # No tool calls — check if combined assistant text is substantial
    combined_text = "\n".join(t.get("text") or "" for t in assistant_turns)
    total_words = len(re.findall(r"\w+", combined_text))
    return total_words < word_threshold


# ---------------------------------------------------------------------------
# Entity / intent extraction — AC2 step 2
# ---------------------------------------------------------------------------

# Action verbs (PT-BR + EN) — surface intent
_ACTION_VERBS = {
    "send",
    "create",
    "read",
    "write",
    "find",
    "generate",
    "update",
    "delete",
    "fetch",
    "post",
    "publish",
    "schedule",
    "transcribe",
    "translate",
    "enviar",
    "criar",
    "ler",
    "escrever",
    "buscar",
    "encontrar",
    "gerar",
    "atualizar",
    "deletar",
    "publicar",
    "agendar",
    "transcrever",
    "traduzir",
    "analisar",
    "analyze",
}

# Tool-domain words — surface noun targets
_DOMAIN_WORDS = {
    "spreadsheet",
    "planilha",
    "email",
    "calendar",
    "calendario",
    "database",
    "banco",
    "video",
    "image",
    "imagem",
    "document",
    "documento",
    "slack",
    "notion",
    "github",
    "clickup",
    "tarefa",
    "task",
    "drive",
    "doc",
    "sheets",
    "supabase",
    "rag",
    "transcription",
    "transcricao",
    "meeting",
    "reuniao",
    "n8n",
    "workflow",
    "browser",
    "navegador",
    "screenshot",
    "crm",
    "lead",
    "vendas",
    "sales",
    "data",
    "dados",
}


def _extract_signal_text(turns: list[dict]) -> str:
    """Concat last user turn + last assistant turn (priority signal) into one string."""
    chunks: list[str] = []
    last_user = next((t for t in reversed(turns) if t.get("role") == "user"), None)
    last_assistant = next((t for t in reversed(turns) if t.get("role") == "assistant"), None)
    if last_user:
        chunks.append(last_user.get("text") or "")
    if last_assistant:
        chunks.append(last_assistant.get("text") or "")
    return "\n".join(chunks).strip()


def _has_any_signal(normalized: str) -> bool:
    """Quick guard: at least one action verb OR domain word present."""
    for kw in _ACTION_VERBS:
        if kw in normalized:
            return True
    for kw in _DOMAIN_WORDS:
        if kw in normalized:
            return True
    return False


# ---------------------------------------------------------------------------
# Keyword matching — AC2 step 3 fast path
# ---------------------------------------------------------------------------


def _load_index() -> dict | None:
    try:
        with INDEX_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _keyword_match(normalized: str, index: dict) -> list[tuple[str, str]]:
    """Returns list of (capability_id, matched_keyword) sorted by capability_id appearance."""
    entries = index.get("entries", []) or []
    seen: dict[str, str] = {}
    for e in entries:
        kw = e.get("keyword", "")
        cap_id = e.get("capability_id", "")
        if not kw or not cap_id:
            continue
        if kw in normalized and cap_id not in seen:
            seen[cap_id] = kw
    return [(cid, kw) for cid, kw in seen.items()]


# ---------------------------------------------------------------------------
# Semantic fallback — AC2 step 3 embedding path (TIL-12 infra)
# ---------------------------------------------------------------------------


def _semantic_topk(text: str, top_k: int = SEMANTIC_TOP_K) -> list[tuple[str, float]] | None:
    """Cosine top-K against capability embeddings. None if unavailable (fail-open)."""
    try:
        import numpy as np
    except ImportError:
        return None
    if not EMB_PATH.exists() or not META_PATH.exists():
        return None
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from engine.intelligence.rag.embedding_config import DIMENSIONS, MODEL
        from engine.intelligence.rag.hybrid_index import _openai_embed
    except Exception:
        return None
    try:
        matrix = np.load(EMB_PATH)
        with META_PATH.open(encoding="utf-8") as f:
            meta = json.load(f)
        cap_ids = [c["capability_id"] for c in meta.get("capabilities", [])]
        if matrix.shape[0] != len(cap_ids) or matrix.shape[1] != int(DIMENSIONS):
            return None
    except Exception:
        return None
    try:
        vec = _openai_embed([text[:8000]], model=MODEL, api_key=api_key, dimensions=int(DIMENSIONS))
        prompt_arr = np.asarray(vec[0], dtype=np.float32)
    except Exception:
        return None
    try:

        def _norm(a):
            n = np.linalg.norm(a, axis=-1, keepdims=True)
            n = np.where(n == 0, 1.0, n)
            return a / n

        mat_n = _norm(matrix)
        p_n = _norm(prompt_arr[None, :])[0]
        scores = (mat_n @ p_n).astype(np.float32)
        order = np.argsort(-scores)[:top_k]
        return [(cap_ids[int(i)], float(scores[int(i)])) for i in order]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Dedup — AC2 step 4
# ---------------------------------------------------------------------------


def _used_capabilities_recent(turns: list[dict], k: int = N_TURNS_DEDUP) -> set[str]:
    """Capability IDs that already surfaced as tool calls / keyword in last K turns.

    Heuristic: if the capability_id substring appears in turn text or tools_used,
    consider it "already used" → suppress re-suggestion.
    """
    recent = turns[-k:] if len(turns) > k else turns
    used: set[str] = set()
    for t in recent:
        text = (t.get("text") or "").lower()
        for tn in t.get("tools_used") or []:
            tn_l = str(tn).lower()
            used.add(tn_l)
            # Map common tool names to capability hints
            if "sheets" in tn_l or "spreadsheet" in tn_l:
                used.add("google_sheets_read")
                used.add("google_sheets_write")
            if "drive" in tn_l:
                used.add("google_drive_access")
            if "clickup" in tn_l:
                used.add("clickup_task_read")
                used.add("clickup_task_write")
        # Loose substring scan against capability ids — populated lazily by caller.
        # We defer to caller to filter; just track raw lowercase text for substring later.
        used.add(("__text__", text))  # marker; we use intersect logic in filter step
    return used


def _filter_recently_used(candidates: list[str], used_marker: set) -> list[str]:
    """Drop candidates that appeared in last 3 turns by direct id substring."""
    text_tokens = [m[1] for m in used_marker if isinstance(m, tuple) and m[0] == "__text__"]
    direct = {m for m in used_marker if isinstance(m, str)}
    kept: list[str] = []
    for c in candidates:
        c_l = c.lower()
        if c_l in direct:
            continue
        # substring scan in text
        if any(c_l in t for t in text_tokens):
            continue
        kept.append(c)
    return kept


# ---------------------------------------------------------------------------
# Authority filter — AC2 step 5 / AC3
# ---------------------------------------------------------------------------


def _required_agent_for(capability_id: str) -> str | None:
    """Return required agent id (no @) if capability has exclusive authority, else None."""
    op = CAPABILITY_AUTHORITY_HINTS.get(capability_id)
    if not op:
        return None
    rule = AUTHORITY_BLOCKLIST.get(op) or {}
    allowed = rule.get("allowed_agents") or []
    return allowed[0] if allowed else None


def _agent_can_use(capability_id: str, active_agent: str) -> bool:
    """True if active agent is in the allowed list for the capability's required operation.

    Capabilities with no authority hint → always allowed (free).
    """
    op = CAPABILITY_AUTHORITY_HINTS.get(capability_id)
    if not op:
        return True
    rule = AUTHORITY_BLOCKLIST.get(op) or {}
    allowed = set(rule.get("allowed_agents") or [])
    if not allowed:
        return True
    # claude-main is treated as conservative (NOT a specific agent → can't perform exclusive ops)
    bare = active_agent.lstrip("@")
    return bare in allowed


# ---------------------------------------------------------------------------
# Ranking — AC2 step 6
# ---------------------------------------------------------------------------


def _rank_candidates(
    candidates: list[tuple[str, float]],
    index: dict,
) -> list[tuple[str, float]]:
    """Re-score by (similarity x context_cost_weight). Return sorted desc."""
    resolved = (index or {}).get("resolvedCapabilities") or {}
    rescored: list[tuple[str, float]] = []
    for cid, sim in candidates:
        cost = (resolved.get(cid) or {}).get("context_cost_estimate")
        w = CONTEXT_COST_WEIGHT.get(cost, CONTEXT_COST_WEIGHT.get("unknown", 0.9))
        rescored.append((cid, float(sim) * float(w)))
    rescored.sort(key=lambda x: -x[1])
    return rescored


# ---------------------------------------------------------------------------
# Output formatting — AC5
# ---------------------------------------------------------------------------

MAX_OUTPUT_CHARS = 500


def _format_suggestion(
    capability_id: str,
    index: dict,
    active_agent: str,
) -> str | None:
    """Build the suggestion string per AC5 spec.

    Authority-aware (AC3): if active agent cannot use, output delegation form.
    """
    resolved = (index or {}).get("resolvedCapabilities") or {}
    cap = resolved.get(capability_id) or {}
    provider = (cap.get("resolved_provider") or {}).get("id") or "indisponivel"

    if not _agent_can_use(capability_id, active_agent):
        agent = _required_agent_for(capability_id) or "agent-com-autoridade"
        msg = f"Capability `{capability_id}` could help here. Delegate to `@{agent}` to use it."
        return msg[:MAX_OUTPUT_CHARS]

    action = _action_hint(capability_id)
    base = f"Capability disponivel: `{capability_id}` via `{provider}`. Sugestao: {action}"
    return base[:MAX_OUTPUT_CHARS]


# Curated action hints per capability (small set; falls back to generic).
_ACTION_HINTS: dict[str, str] = {
    "google_sheets_read": "leia a planilha para extrair os dados.",
    "google_sheets_write": "escreva no Sheets para registrar o resultado.",
    "google_drive_access": "acesse o Drive para listar/baixar o arquivo.",
    "clickup_task_read": "consulte tasks do ClickUp envolvidas.",
    "clickup_task_write": "crie ou atualize uma task no ClickUp.",
    "supabase_query": "consulte o Supabase para os dados estruturados.",
    "rag_search": "use rag_search para buscar conhecimento existente.",
    "meeting_transcription": "transcreva a reuniao via Fireflies/Whisper.",
    "slack_send": "envie a mensagem via Slack.",
    "github_pr": "abra o PR via @devops.",
    "n8n_workflow_trigger": "dispare o workflow N8N apropriado.",
    "web_search": "rode web_search para a referencia externa.",
    "browser_navigate": "use Playwright para navegar e validar visualmente.",
}


def _action_hint(capability_id: str) -> str:
    return _ACTION_HINTS.get(
        capability_id,
        f"invoque `{capability_id}` ou delegue ao agente apropriado.",
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def _emit_telemetry(
    *,
    enabled: bool,
    suggested: str | None,
    similarity: float | None,
    confidence_threshold: float,
    latency_ms: float,
    reason: str,
    active_agent: str,
    transcript_hash: str,
    was_trivial: bool,
) -> None:
    entry = {
        "timestamp": _now_iso(),
        "event_type": "post_task",
        "enabled": enabled,
        "suggested_capability": suggested or "none",
        "similarity_score": similarity,
        "confidence_threshold": confidence_threshold,
        "latency_ms": round(latency_ms, 3),
        "reason": reason,
        "active_agent": active_agent,
        "transcript_hash": transcript_hash,
        "was_trivial": was_trivial,
        "was_acted_on": None,  # set by next-turn tracker (not in scope for v1 inline)
    }
    _append_metric(entry)


def main() -> None:
    t0 = time.perf_counter()
    suggested: str | None = None
    similarity: float | None = None
    reason = "init"
    was_trivial = False
    confidence_threshold = DEFAULT_CONFIDENCE_THRESHOLD
    active_agent = _get_active_agent_id()
    transcript_hash = ""

    try:
        # ---- AC7: opt-in gate (zero-cost no-op when disabled) ----
        cfg = _load_config()
        enabled = bool(cfg.get("enabled", False))
        confidence_threshold = float(cfg.get("confidence_threshold", DEFAULT_CONFIDENCE_THRESHOLD))
        max_per_turn = int(cfg.get("max_per_turn", DEFAULT_MAX_PER_TURN))
        trivial_word_threshold = int(
            cfg.get("trivial_word_threshold", DEFAULT_TRIVIAL_WORD_THRESHOLD)
        )

        # Always read stdin to drain pipe (avoid SIGPIPE for caller)
        try:
            raw = sys.stdin.read()
        except Exception:
            raw = ""

        if not enabled:
            reason = "disabled_opt_out"
            print(json.dumps({"continue": True}))
            return

        # Parse hook payload
        hook_data: dict = {}
        if raw and raw.strip():
            try:
                hook_data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                hook_data = {}

        transcript_path = hook_data.get("transcript_path") or hook_data.get("transcriptPath")

        # ---- AC2 step 1: read N=5 last turns ----
        turns = _read_transcript_turns(transcript_path, n=N_TURNS_TO_READ)
        if not turns:
            reason = "no_transcript_turns"
            print(json.dumps({"continue": True}))
            return

        # ---- AC4c: trivial turn detection ----
        was_trivial = _is_trivial_turn(turns, trivial_word_threshold)
        if was_trivial:
            reason = "trivial_turn"
            print(json.dumps({"continue": True}))
            return

        # ---- AC2 step 2: signal extraction ----
        signal = _extract_signal_text(turns)
        if not signal:
            reason = "no_signal_text"
            print(json.dumps({"continue": True}))
            return
        transcript_hash = _prompt_hash(signal)
        normalized = _normalize_text(signal)
        if not _has_any_signal(normalized):
            reason = "no_action_or_domain_words"
            print(json.dumps({"continue": True}))
            return

        # ---- AC2 step 3: keyword fast path → embedding fallback ----
        index = _load_index() or {}
        kw_matches = _keyword_match(normalized, index)

        candidates: list[tuple[str, float]] = []
        if kw_matches:
            # Keyword hit → fixed high confidence (cap at 0.95)
            for cid, _kw in kw_matches[:SEMANTIC_TOP_K]:
                candidates.append((cid, 0.90))
            reason = "keyword_match"
        else:
            topk = _semantic_topk(signal, top_k=SEMANTIC_TOP_K)
            if topk:
                candidates = topk
                reason = "embedding_match"
            else:
                reason = "no_match"

        if not candidates:
            print(json.dumps({"continue": True}))
            return

        # ---- AC2 step 4: dedup against last 3 turns ----
        used_marker = _used_capabilities_recent(turns, k=N_TURNS_DEDUP)
        kept_ids = _filter_recently_used([cid for cid, _ in candidates], used_marker)
        candidates = [c for c in candidates if c[0] in kept_ids]
        if not candidates:
            reason = "all_recently_used"
            print(json.dumps({"continue": True}))
            return

        # ---- AC2 step 6: rank by similarity x context_cost ----
        ranked = _rank_candidates(candidates, index)

        # ---- AC2 step 7 + AC4: max 1 suggestion ≥ threshold ----
        if not ranked:
            reason = "empty_after_rank"
            print(json.dumps({"continue": True}))
            return
        top_id, top_score = ranked[0]
        similarity = top_score
        if top_score < confidence_threshold:
            reason = "below_threshold"
            print(json.dumps({"continue": True}))
            return

        # ---- AC3 + AC5: format with authority-awareness ----
        suggestion_text = _format_suggestion(top_id, index, active_agent)
        if not suggestion_text:
            reason = "format_failed"
            print(json.dumps({"continue": True}))
            return

        suggested = top_id

        # AC4: max_per_turn (default 1) — we already cap to 1 via top-rank.
        # If max_per_turn=0, behave as no-op.
        if max_per_turn < 1:
            reason = "max_per_turn_zero"
            print(json.dumps({"continue": True}))
            return

        # Emit suggestion using systemMessage (Stop hooks allow it).
        payload = {
            "continue": True,
            "systemMessage": f"[POST-TASK] {suggestion_text}",
        }
        print(json.dumps(payload, ensure_ascii=False))
        reason = "suggested"

    except Exception as exc:  # fail-open
        print(f"[post_task_suggester] swallowed: {exc}", file=sys.stderr)
        print(json.dumps({"continue": True}))
        reason = f"error:{type(exc).__name__}"
    finally:
        # AC6 telemetry
        try:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            _emit_telemetry(
                enabled=bool(locals().get("enabled", False)),
                suggested=suggested,
                similarity=similarity,
                confidence_threshold=confidence_threshold,
                latency_ms=latency_ms,
                reason=reason,
                active_agent=active_agent,
                transcript_hash=transcript_hash,
                was_trivial=was_trivial,
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
