#!/usr/bin/env python3
"""
Memory Hints Injector v1.0 (Mega Brain) - Bracket-Aware Agent Memory Enhancement

Implements MIS (Memory Integration System) for bracket-aware memory injection
that adapts to context window usage.

BRACKETS:
  FRESH    (60-100% context remaining) -> No extra memory needed
  MODERATE (40-60%)  -> Brief memory reminder (~50 tokens)
  DEPLETED (25-40%)  -> Extended memory reinforcement (~200 tokens)
  CRITICAL (0-25%)   -> Full memory + handoff warning (~1000 tokens)

INTEGRATION:
  - Runs at UserPromptSubmit, AFTER skill_router.py
  - Tracks prompt_count in STATE.json (mis.prompt_count)
  - Reads from canonical agent path via AGENT-INDEX.yaml (resolve_agent_path.py)
  - Fallback to .claude/agent-memory/ for unindexed agents
  - Returns feedback with memory hints when bracket warrants it

FAIL-OPEN: Never blocks user input. Returns {"continue": true} on any error.

Hook Type: UserPromptSubmit
"""

import json
import os
import re as _re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
STATE_DIR = PROJECT_ROOT / ".claude" / "jarvis"
STATE_FILE = STATE_DIR / "STATE.json"

# Import canonical path resolver (MOD-001: reads from agent directories, not .claude/agent-memory/)
try:
    sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "hooks"))
    from resolve_agent_path import resolve_memory_path

    _HAS_RESOLVER = True
except ImportError:
    _HAS_RESOLVER = False
    AGENT_MEMORY_DIR = PROJECT_ROOT / ".claude" / "agent-memory"

# Context Brackets
BRACKET_LAYER_MAP = {
    "FRESH": {"layer": 0, "max_tokens": 0, "max_lines": 0},
    "MODERATE": {"layer": 1, "max_tokens": 50, "max_lines": 5},
    "DEPLETED": {"layer": 2, "max_tokens": 200, "max_lines": 20},
    "CRITICAL": {"layer": 3, "max_tokens": 1000, "max_lines": 50},
}

DEFAULTS = {
    "avg_tokens_per_prompt": 1500,
    "max_context": 200000,
}

INTERNAL_TIMEOUT_MS = 80

# ---------------------------------------------------------------------------
# ADAPTIVE CONTEXT SCORER INTEGRATION (GAP-07)
# Uses intent-based budget when bracket >= MODERATE.
# Fails open to existing bracket system if import or classification fails.
# ---------------------------------------------------------------------------
_HAS_SCORER = False
_score_context_budget = None
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    from core.intelligence.context_scorer import score_context_budget as _scb

    _score_context_budget = _scb
    _HAS_SCORER = True
except Exception:
    pass

_INTENT_QUICK_PATTERNS = [
    ("greeting", _re.compile(r"^(hi|hello|hey|oi|bom dia|boa tarde|boa noite)\b", _re.I)),
    ("meta", _re.compile(r"(quem .+ voc|what are you|who are you|seu nome)", _re.I)),
    ("hierarchical", _re.compile(r"(compar|hierarq|priori[tz]|rank|cascad)", _re.I)),
    ("cross_expert", _re.compile(r"(cross.?expert|todas as fontes|all sources|combin)", _re.I)),
    ("analytical", _re.compile(r"(anali[sz]|estrat|why|por.?qu[eê]|implic|trade.?off)", _re.I)),
    ("factual_complex", _re.compile(r"(framework|metodolog|how.+work|como funciona|expli)", _re.I)),
]


def _quick_classify_intent(prompt_text: str) -> str:
    """Lightweight intent classification (~0.1ms). No heavy imports."""
    if not prompt_text or len(prompt_text) < 3:
        return "factual_simple"
    for intent, pattern in _INTENT_QUICK_PATTERNS:
        if pattern.search(prompt_text[:200]):
            return intent
    return "factual_complex" if len(prompt_text.split()) > 10 else "factual_simple"


def calculate_bracket(context_percent):
    """Calculate context bracket from remaining context percentage."""
    if not isinstance(context_percent, (int, float)):
        return "CRITICAL"
    if context_percent >= 60:
        return "FRESH"
    if context_percent >= 40:
        return "MODERATE"
    if context_percent >= 25:
        return "DEPLETED"
    return "CRITICAL"


def estimate_context_percent(prompt_count, avg_tokens=None, max_context=None):
    """Estimate percentage of context remaining based on prompt count."""
    avg = avg_tokens or DEFAULTS["avg_tokens_per_prompt"]
    mx = max_context or DEFAULTS["max_context"]

    if not isinstance(prompt_count, (int, float)) or prompt_count < 0:
        return 100
    if mx <= 0:
        return 0

    used = prompt_count * avg
    percent = 100 - (used / mx * 100)
    return max(0.0, min(100.0, percent))


def load_state():
    """Load STATE.json safely."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    """Save STATE.json safely."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_active_agent(state):
    """Get active agent slug from state."""
    session = state.get("session", {})
    agent = session.get("agent_active")
    if agent and isinstance(agent, str) and agent.strip():
        return agent.strip()
    return None


def estimate_tokens(text):
    """Rough token estimation (~4 chars per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def read_agent_memory_hints(agent_slug, max_lines, max_tokens):
    """
    Read memory hints from agent's MEMORY.md, respecting token budget.
    Reads from the END of the file (most recent entries) working backwards.
    Uses canonical path resolver (AGENT-INDEX.yaml) with .claude/agent-memory/ fallback.
    """
    if _HAS_RESOLVER:
        memory_path = resolve_memory_path(PROJECT_ROOT, agent_slug)
    else:
        memory_path = AGENT_MEMORY_DIR / agent_slug / "MEMORY.md"
    if not memory_path.exists():
        return ""

    try:
        content = memory_path.read_text(encoding="utf-8")
    except Exception:
        return ""

    lines = content.split("\n")
    if len(lines) < 10:
        return ""

    useful_lines = []
    tokens_used = 0

    for line in reversed(lines):
        stripped = line.strip()

        if not stripped:
            if useful_lines:
                useful_lines.insert(0, "")
            continue

        if stripped.startswith("# ") and len(useful_lines) == 0:
            continue
        if stripped.startswith("> ") and len(useful_lines) == 0:
            continue

        line_tokens = estimate_tokens(stripped)

        if tokens_used + line_tokens > max_tokens:
            break
        if len(useful_lines) >= max_lines:
            break

        useful_lines.insert(0, line)
        tokens_used += line_tokens

    result = "\n".join(useful_lines).strip()

    while result.startswith("---"):
        result = result[3:].strip()

    return result


def main():
    """Main hook execution."""
    start_time = time.time()

    try:
        raw_input = sys.stdin.read()

        # Parse hook input for user prompt (needed for intent classification)
        _user_prompt = ""
        try:
            hook_data = json.loads(raw_input) if raw_input.strip() else {}
            _user_prompt = hook_data.get("query", hook_data.get("prompt", ""))
        except (json.JSONDecodeError, AttributeError):
            pass

        state = load_state()
        if not state:
            print(json.dumps({"continue": True}))
            return

        # MIS Prompt Counter
        session_id = state.get("session_id", "")
        mis = state.setdefault("mis", {})

        if mis.get("session_id") != session_id:
            mis["session_id"] = session_id
            mis["prompt_count"] = 0

        prompt_count = mis.get("prompt_count", 0) + 1
        mis["prompt_count"] = prompt_count

        # Calculate Bracket
        context_percent = estimate_context_percent(prompt_count)
        bracket = calculate_bracket(context_percent)
        mis["bracket"] = bracket
        mis["context_percent"] = round(context_percent, 1)

        save_state(state)

        # Check if memory hints needed
        layer_config = BRACKET_LAYER_MAP.get(bracket, BRACKET_LAYER_MAP["FRESH"])
        max_tokens = layer_config["max_tokens"]
        max_lines = layer_config["max_lines"]

        # Adaptive scorer override: intent-based budget when bracket >= MODERATE
        if max_tokens > 0 and _HAS_SCORER and _user_prompt:
            try:
                intent = _quick_classify_intent(_user_prompt)
                scored_chars = _score_context_budget(intent)
                scored_tokens = scored_chars // 4  # match estimate_tokens ratio
                if scored_tokens == 0:
                    max_tokens = 0
                elif scored_tokens > max_tokens:
                    max_tokens = min(scored_tokens, BRACKET_LAYER_MAP["CRITICAL"]["max_tokens"])
                    max_lines = min(scored_tokens // 10, BRACKET_LAYER_MAP["CRITICAL"]["max_lines"])
            except Exception:
                pass  # fail open: keep original bracket-based values

        if max_tokens <= 0:
            print(json.dumps({"continue": True}))
            return

        # Timeout check
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > INTERNAL_TIMEOUT_MS * 0.5:
            print(json.dumps({"continue": True}))
            return

        # Get active agent
        raw_slug = get_active_agent(state)
        if not raw_slug:
            print(json.dumps({"continue": True}))
            return

        agent_slug = raw_slug

        # Read memory hints
        hints = read_agent_memory_hints(agent_slug, max_lines, max_tokens)

        # Final timeout check
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > INTERNAL_TIMEOUT_MS:
            print(json.dumps({"continue": True}))
            return

        # Return feedback
        if hints:
            if bracket == "CRITICAL":
                prefix = f"[MIS:{bracket}] Context at {round(context_percent)}%. Memory reinforcement for @{agent_slug}:"
            else:
                prefix = f"[MIS:{bracket}] @{agent_slug} memory:"

            feedback = f"{prefix}\n{hints}"
            print(json.dumps({"continue": True, "feedback": feedback}))
        else:
            print(json.dumps({"continue": True}))

    except Exception:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
