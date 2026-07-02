#!/usr/bin/env python3
"""LLM QUERY EXPANSION — STORY-GBA-F2.4 (PORT LITERAL from gbrain)
================================================================

Multi-query expansion: rewrite an ambiguous query into related variants
(synonyms / reframings) BEFORE retrieval so the retriever finds relevant
documents the literal query would miss.

This is a LITERAL port of gbrain (SHA 4ee530f), two source files fused into
one Python seam:

  - ``src/core/search/expansion.ts:57``  → ``expand_query()`` here
        (the word-count gate, the sanitization layer, the dedup+cap logic,
         and the OUTER fail-open ``catch { return [query] }``)
  - ``src/core/ai/gateway.ts:2162`` (``expand``) → ``_llm_expand()`` here
        (the LLM prompt + JSON parse + the INNER fail-open
         ``catch { ... return [query] }``)

⭐ THE LOAD-BEARING INVARIANT — FAIL-OPEN
-----------------------------------------
Expansion is *best-effort*. ANY failure (LLM error, timeout, bad JSON, no API
key, expansion disabled, short query) returns the ORIGINAL query alone. It
NEVER raises and NEVER drops the original query. This is the central value:
expansion can only ADD recall, never break retrieval. An expansion path that
can derail the query in a provider hiccup is the explicit anti-pattern the
story rejects.

gbrain expansion.ts comment, ported verbatim in spirit:
    "Original query + sanitized alternatives, deduped, capped at MAX_QUERIES."
    "Expansion failure is non-fatal."

Provider: OpenAI (Chat Completions, JSON object). gbrain's gateway is
provider-agnostic and defaults to ``openai:gpt-4o-mini`` for the expansion
slot; the mega-brain has ``OPENAI_API_KEY`` active (ANTHROPIC absent), so the
canonical provider here is OpenAI. The sanitization layer stays HERE (not in
any shared gateway), exactly as gbrain keeps it in ``expansion.ts`` —
prompt-injection defense is the RAG layer's responsibility.

Version: 1.0.0
Story:   STORY-GBA-F2.4
"""

from __future__ import annotations

import json
import re

from engine.config import get_config

# --- gbrain expansion.ts constants (ported verbatim) ------------------------
MAX_QUERIES = 3  # cap on [original + alternatives]
MIN_WORDS = 3  # queries shorter than this are not worth an LLM round-trip
MAX_QUERY_CHARS = 500  # sanitization truncation bound
MAX_ALTERNATIVES = 2  # gbrain caps sanitizeExpansionOutput at 2 (MAX_QUERIES-1)

# --- expansion model (gbrain default: openai:gpt-4o-mini) -------------------
DEFAULT_EXPANSION_MODEL = "gpt-4o-mini"
# (connect, read) timeout. gbrain wires the chat timeout into expansion
# (gateway.ts: "expansion had NO abortSignal; same stalled-socket class as
# chat. Default the chat timeout."). We mirror with a bounded HTTP timeout so a
# stalled socket fails-open instead of hanging retrieval.
EXPANSION_TIMEOUT = (5, 20)


def expansion_enabled() -> bool:
    """Resolve the expansion toggle (config-driven, default OFF).

    Mirrors gbrain's ``resolvedMode.expansion`` gate: expansion only fires
    when explicitly enabled. Default is OFF so retrieval behavior is unchanged
    unless an operator opts in — and so CI/eval never pays a network round-trip
    by accident.

    Truthy values (case-insensitive): ``1``, ``true``, ``yes``, ``on``.
    """
    raw = get_config("RAG_QUERY_EXPANSION", default="0")
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _count_words(query: str) -> int:
    """Word count for the MIN_WORDS gate.

    gbrain uses ``countCJKAwareWords`` (each CJK char counts as a word). We keep
    a whitespace split for the Latin-script corpus the mega-brain serves; the
    contract that matters — short queries skip the LLM — is preserved.
    """
    return len([w for w in query.strip().split() if w])


def sanitize_query_for_prompt(query: str) -> str:
    """Defense-in-depth sanitization BEFORE the query reaches the LLM.

    Literal port of ``expansion.ts::sanitizeQueryForPrompt``:
      - truncate to MAX_QUERY_CHARS
      - strip fenced code blocks
      - strip HTML/XML tags
      - strip leading injection prefixes (ignore/forget/system/...)
      - collapse whitespace
    """
    original = query
    q = query
    if len(q) > MAX_QUERY_CHARS:
        q = q[:MAX_QUERY_CHARS]
    q = re.sub(r"```[\s\S]*?```", " ", q)
    q = re.sub(r"</?[a-zA-Z][^>]*>", " ", q)
    q = re.sub(
        r"^(?:\s*(?:ignore|forget|disregard|override|system|assistant|human)[\s:]+)+",
        "",
        q,
        flags=re.IGNORECASE,
    )
    q = re.sub(r"\s+", " ", q).strip()
    if q != original:
        # Never log the query text itself (privacy — gbrain Fix 3/M1).
        print("[query_expansion] sanitize: stripped content from query before LLM expansion")
    return q


def sanitize_expansion_output(alternatives: list) -> list[str]:
    """Validate LLM-produced alternatives. LLM output is UNTRUSTED.

    Literal port of ``expansion.ts::sanitizeExpansionOutput``:
      - drop non-strings
      - strip control chars, truncate
      - dedup (case-insensitive)
      - cap at MAX_ALTERNATIVES (2)
    """
    seen: set[str] = set()
    out: list[str] = []
    for raw in alternatives:
        if not isinstance(raw, str):
            continue
        s = re.sub(r"[\x00-\x1f\x7f]", "", raw).strip()
        if not s:
            continue
        if len(s) > MAX_QUERY_CHARS:
            s = s[:MAX_QUERY_CHARS]
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= MAX_ALTERNATIVES:
            break
    return out


def _llm_expand(query: str) -> list[str]:
    """Call the OpenAI Chat Completions API to expand a sanitized query.

    Literal port of ``gateway.ts::expand``: returns ``[original, *expansions]``;
    on ANY failure returns ``[query]`` (INNER fail-open). The caller
    (``expand_query``) wraps this in a second try/except (OUTER fail-open), so
    the original query survives even an unexpected exception class.

    Returns the original query PLUS up to ~4 LLM rewrites. Never raises.
    """
    api_key = get_config("OPENAI_API_KEY")
    if not api_key:
        # gbrain: ``if (!isAvailable('expansion')) return [query];``
        return [query]

    model = get_config("RAG_EXPANSION_MODEL", default=DEFAULT_EXPANSION_MODEL)

    # gbrain prompt (gateway.ts), ported verbatim:
    prompt = "\n".join(
        [
            "Rewrite the search query below into 3-4 different, related queries "
            "that would help find relevant documents.",
            "Return ONLY a JSON object of the form {\"queries\": [...]}. "
            "Do NOT include the original query in the result.",
            "Each rewrite should emphasize different aspects, synonyms, or framings.",
            "",
            f"Query: {query}",
        ]
    )

    try:
        import requests

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
            timeout=EXPANSION_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        expansions = parsed.get("queries", []) if isinstance(parsed, dict) else []
        if not isinstance(expansions, list):
            expansions = []

        # Dedup + include the original query (gateway.ts tail).
        seen: set[str] = set()
        all_q: list[str] = []
        for q in [query, *expansions]:
            if not isinstance(q, str) or not q.strip():
                continue
            k = q.lower().strip()
            if k in seen:
                continue
            seen.add(k)
            all_q.append(q)
        return all_q if all_q else [query]
    except Exception:
        # gbrain: "Expansion is best-effort: on failure, fall back to the
        # original query alone." INNER fail-open.
        return [query]


def expand_query(query: str) -> list[str]:
    """Expand a query into related variants. ALWAYS returns the original first.

    Literal port of ``expansion.ts::expandQuery``. Returns
    ``[query, *alternatives]`` deduped and capped at MAX_QUERIES (3). On ANY
    failure path returns ``[query]`` — the OUTER fail-open that guarantees
    retrieval is never derailed:

      - query shorter than MIN_WORDS words → ``[query]`` (skip LLM)
      - no expansion provider / disabled   → ``[query]``
      - sanitization empties the query     → ``[query]``
      - LLM error / timeout / bad JSON     → ``[query]`` (via ``_llm_expand``)
      - ANY unexpected exception           → ``[query]`` (this try/except)

    The original ``query`` is preserved EXACTLY (not the sanitized copy) as the
    first element, so downstream retrieval always runs the user's real query.
    """
    try:
        if _count_words(query) < MIN_WORDS:
            return [query]

        sanitized = sanitize_query_for_prompt(query)
        if not sanitized:
            return [query]

        # _llm_expand returns [sanitized, *raw_expansions]; alternatives are
        # everything after the first entry. Re-validate them (untrusted).
        gateway_results = _llm_expand(sanitized)
        alternatives = gateway_results[1:]
        sanitized_alts = sanitize_expansion_output(alternatives)

        # Original query (verbatim) + sanitized alternatives, deduped, capped.
        all_q = [query, *sanitized_alts]
        unique_keys: list[str] = []
        seen: set[str] = set()
        for q in all_q:
            k = q.lower().strip()
            if k in seen:
                continue
            seen.add(k)
            unique_keys.append(k)
        capped = unique_keys[:MAX_QUERIES]
        # Map each surviving key back to its original-cased string.
        return [next((orig for orig in all_q if orig.lower().strip() == k), k) for k in capped]
    except Exception:
        # OUTER fail-open: nothing the expansion layer does may break the query.
        return [query]
