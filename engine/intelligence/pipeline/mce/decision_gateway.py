"""decision_gateway.py — Hybrid 6-Point Human Decision Gateway (Mode C)

Story MCE-11.20: 6 pontos de decisão humana — Modo C (Híbrido).

Mode C logic:
    CRITICAL decisions (D3, D4, D5, D6) → interactive prompt with 30s timeout
    FREQUENT decisions (D1, D2) → auto-proceed + log to DECISIONS-AWAITING-HUMAN.jsonl

When --non-interactive flag is active (MCE_NON_INTERACTIVE=1 or passed via
set_non_interactive()), ALL decisions fall through to log-only regardless of
criticality. Useful for cron runs and automated pipelines.

Decision IDs:
    D1 — Reprocessar arquivo já processado  (frequente → LOG)
    D2 — Duplicata parcial                  (frequente → LOG)
    D3 — Sobrescrever AGENT.md              (crítico   → PROMPT)
    D4 — Criar novo cargo agent             (crítico   → PROMPT)
    D5 — Template evolution NOVA_PARTE      (crítico   → PROMPT)
    D6 — Bypass enforcement                 (crítico   → PROMPT)

Usage::

    from engine.intelligence.pipeline.mce.decision_gateway import prompt_or_log, DecisionID

    # D1 — logged silently, returns True (proceed)
    ok = prompt_or_log(DecisionID.D1, source_id="fireflies:abc123", date="2026-05-10")

    # D4 — prompts user, returns True/False
    ok = prompt_or_log(DecisionID.D4, role="Closer", count=10)

    # D3 — prompts user, returns True/False
    ok = prompt_or_log(DecisionID.D3, agent_name="alex-hormozi")

Version: 1.0.0 (Story MCE-11.20)
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("mce.decision_gateway")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT: Path | None = None


def _project_root() -> Path:
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        try:
            from engine.paths import ROOT

            _PROJECT_ROOT = ROOT
        except ImportError:
            _PROJECT_ROOT = Path(__file__).resolve().parents[4]
    return _PROJECT_ROOT


def _decisions_log_path() -> Path:
    return _project_root() / ".data" / "artifacts" / "DECISIONS-AWAITING-HUMAN.jsonl"


# ---------------------------------------------------------------------------
# Non-interactive flag
# ---------------------------------------------------------------------------

_NON_INTERACTIVE_OVERRIDE: bool = False


def set_non_interactive(value: bool = True) -> None:
    """Force all decisions to log-only mode (used by --non-interactive flag)."""
    global _NON_INTERACTIVE_OVERRIDE
    _NON_INTERACTIVE_OVERRIDE = value


def is_non_interactive() -> bool:
    """Return True when running in non-interactive mode.

    Checks (in order):
    1. Python-level override set by set_non_interactive()
    2. MCE_NON_INTERACTIVE env var (any truthy string: 1, true, yes)
    3. Absence of a real TTY on stdin
    """
    if _NON_INTERACTIVE_OVERRIDE:
        return True
    env_val = os.environ.get("MCE_NON_INTERACTIVE", "").lower()
    if env_val in {"1", "true", "yes"}:
        return True
    # If stdin is not a TTY we cannot prompt interactively
    if not sys.stdin.isatty():
        return True
    return False


# ---------------------------------------------------------------------------
# Decision IDs
# ---------------------------------------------------------------------------


class DecisionID(str, Enum):
    D1 = "D1"  # Reprocessar arquivo já processado
    D2 = "D2"  # Duplicata parcial
    D3 = "D3"  # Sobrescrever AGENT.md
    D4 = "D4"  # Criar novo cargo agent
    D5 = "D5"  # Template evolution NOVA_PARTE
    D6 = "D6"  # Bypass enforcement

    @property
    def is_critical(self) -> bool:
        """Critical decisions require interactive prompt in Mode C."""
        return self in _CRITICAL_DECISIONS


_CRITICAL_DECISIONS: frozenset[DecisionID] = frozenset(
    {DecisionID.D3, DecisionID.D4, DecisionID.D5, DecisionID.D6}
)

# Default responses (conservative / safe) per decision
_DEFAULTS: dict[DecisionID, str] = {
    DecisionID.D1: "N",
    DecisionID.D2: "N",
    DecisionID.D3: "2",  # APENAS MEMORY
    DecisionID.D4: "Y",  # MCE-11.8: auto-create when CRITICAL threshold met (≥10 mentions)
    DecisionID.D5: "N",
    DecisionID.D6: "N",
}

# Auto-choice justification for logged (non-interactive) decisions
_AUTO_JUSTIFICATIONS: dict[DecisionID, str] = {
    DecisionID.D1: "Modo C: D1 é decisão frequente — pipeline retorna SKIP para evitar reprocessamento acidental",
    DecisionID.D2: "Modo C: D2 é decisão frequente — pipeline retorna SKIP para evitar chunks redundantes",
    DecisionID.D3: "Modo C non-interactive: default 2 (apenas MEMORY) escolhido automaticamente",
    DecisionID.D4: "Modo C non-interactive: default Y (auto-criar cargo agent) quando mention_count >= THRESHOLD_CRITICAL=10",
    DecisionID.D5: "Modo C non-interactive: default N (não aprovar NOVA_PARTE) escolhido automaticamente",
    DecisionID.D6: "Modo C non-interactive: default N (não bypassar) escolhido automaticamente",
}

# ---------------------------------------------------------------------------
# PT-BR JARVIS prompt templates
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATES: dict[DecisionID, str] = {
    DecisionID.D1: (
        "JARVIS: Esta fonte já foi processada em {date} (source_id: {source_id}). "
        "Reprocessar? Isso sobrescreve os chunks anteriores. [y/N] ({timeout}s timeout → N)"
    ),
    DecisionID.D2: (
        "JARVIS: Detectada duplicata parcial com {source_id} ({similarity_pct}% de similaridade). "
        "Continuar processamento pode gerar chunks redundantes. Prosseguir mesmo assim? [y/N] ({timeout}s → N)"
    ),
    DecisionID.D3: (
        "JARVIS: Novos insights de alto impacto encontrados para {agent_name}. "
        "Atualizar apenas MEMORY ou também o AGENT.md (identidade)? "
        "[1=MEMORY+AGENT / 2=APENAS MEMORY / 3=PULAR] ({timeout}s → 2)"
    ),
    DecisionID.D4: (
        "JARVIS: Role '{role}' atingiu {count} menções (threshold: 10). "
        "Criar cargo agent permanentemente? Esta ação cria arquivos em agents/external/cargo/. "
        "[y/N] ({timeout}s → N)"
    ),
    DecisionID.D5: (
        "JARVIS: Framework '{framework}' é relevante para {n_agents} agentes mas não cabe "
        "nas 10 PARTEs do template. Aprovar criação de NOVA_PARTE? [y/N] ({timeout}s → N)"
    ),
    DecisionID.D6: (
        "JARVIS: Enforcement bypass solicitado para {rule}. Razão: '{reason}'. "
        "Confirmar bypass? [y/N] ({timeout}s → N)"
    ),
}

# Question text used in JSONL log (same question user would see)
_QUESTION_TEMPLATES: dict[DecisionID, str] = {
    DecisionID.D1: (
        "Esta fonte já foi processada em {date} (source_id: {source_id}). "
        "Reprocessar? Isso sobrescreve os chunks anteriores."
    ),
    DecisionID.D2: (
        "Detectada duplicata parcial com {source_id} ({similarity_pct}% de similaridade). "
        "Continuar processamento pode gerar chunks redundantes. Prosseguir mesmo assim?"
    ),
    DecisionID.D3: (
        "Novos insights de alto impacto encontrados para {agent_name}. "
        "Atualizar apenas MEMORY ou também o AGENT.md (identidade)? "
        "[1=MEMORY+AGENT / 2=APENAS MEMORY / 3=PULAR]"
    ),
    DecisionID.D4: (
        "Role '{role}' atingiu {count} menções (threshold: 10). "
        "Criar cargo agent permanentemente? Esta ação cria arquivos em agents/external/cargo/."
    ),
    DecisionID.D5: (
        "Framework '{framework}' é relevante para {n_agents} agentes mas não cabe "
        "nas 10 PARTEs do template. Aprovar criação de NOVA_PARTE?"
    ),
    DecisionID.D6: (
        "Enforcement bypass solicitado para {rule}. Razão: '{reason}'. Confirmar bypass?"
    ),
}

PROMPT_TIMEOUT_SECS = 30


# ---------------------------------------------------------------------------
# JSONL log writer
# ---------------------------------------------------------------------------


def _log_decision(
    decision_id: DecisionID,
    question: str,
    auto_choice: str,
    justification: str,
    source_id: str = "",
    slug: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    """Append one entry to DECISIONS-AWAITING-HUMAN.jsonl.

    Non-fatal: exceptions are logged but never propagated.
    """
    log_path = _decisions_log_path()
    entry: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "decision_id": decision_id.value,
        "question": question,
        "auto_choice": auto_choice,
        "justification": justification,
        "source_id": source_id,
        "slug": slug,
    }
    if extra:
        entry.update(extra)

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        logger.debug("decision_gateway: logged %s auto_choice=%s", decision_id.value, auto_choice)
    except Exception as exc:
        logger.warning("decision_gateway: failed to write DECISIONS-AWAITING-HUMAN.jsonl: %s", exc)


# ---------------------------------------------------------------------------
# Timeout-aware interactive prompt
# ---------------------------------------------------------------------------


def _prompt_with_timeout(
    message: str,
    timeout: int = PROMPT_TIMEOUT_SECS,
    default: str = "N",
) -> str:
    """Present an interactive prompt on stderr with a timeout.

    Returns the user's input (stripped) or ``default`` on timeout / non-TTY.
    Uses SIGALRM on Unix; falls back to plain input() on non-Unix platforms.
    """
    print(f"\n{message}", file=sys.stderr, flush=True)

    # SIGALRM-based timeout (Unix only)
    if hasattr(signal, "SIGALRM"):

        def _timeout_handler(signum: int, frame: object) -> None:
            raise TimeoutError

        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)
        try:
            response = input("> ").strip()
            signal.alarm(0)
            return response if response else default
        except (TimeoutError, EOFError, KeyboardInterrupt):
            signal.alarm(0)
            print(f"\n[timeout {timeout}s → {default}]", file=sys.stderr, flush=True)
            return default
        finally:
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Non-Unix (Windows): plain input, no timeout
        try:
            response = input("> ").strip()
            return response if response else default
        except (EOFError, KeyboardInterrupt):
            return default


def _parse_yes(response: str) -> bool:
    """Return True if the user answered 'y' or 'yes' (case-insensitive)."""
    return response.strip().lower() in {"y", "yes", "s", "sim"}


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------


def prompt_or_log(
    decision_id: DecisionID,
    source_id: str = "",
    slug: str = "",
    timeout: int = PROMPT_TIMEOUT_SECS,
    **kwargs: Any,
) -> bool | str:
    """Gate a human decision point using Mode C logic.

    Mode C rules:
    - D1, D2 (frequent, low risk): always log silently, return default.
    - D3, D4, D5, D6 (critical): prompt interactively unless non-interactive mode
      is active, in which case log and return default.

    Args:
        decision_id: Which of the 6 decision points (DecisionID.D1 … D6).
        source_id:   Source identifier for the JSONL log (Fireflies/Read.ai ID or
                     composite key).
        slug:        Pipeline slug for the JSONL log.
        timeout:     Prompt timeout in seconds (default 30).
        **kwargs:    Template variables injected into the prompt/question text.
                     Examples:
                       D1: date="2026-05-10"
                       D2: similarity_pct=73
                       D3: agent_name="alex-hormozi"
                       D4: role="Closer", count=12
                       D5: framework="NEPQ", n_agents=3
                       D6: rule="R1", reason="emergency hotfix"

    Returns:
        bool: True = proceed / approve, False = skip / reject (D1, D2, D4, D5, D6).
        str:  "1" | "2" | "3" for D3 (MEMORY+AGENT / APENAS MEMORY / PULAR).
    """
    default = _DEFAULTS[decision_id]
    question = _render_template(_QUESTION_TEMPLATES[decision_id], timeout=timeout, **kwargs)

    # --- D1, D2: FREQUENT — always auto-log, never prompt ---
    if not decision_id.is_critical:
        auto_choice = default  # always "N" for D1, D2
        justification = _AUTO_JUSTIFICATIONS[decision_id]
        _log_decision(
            decision_id=decision_id,
            question=question,
            auto_choice=auto_choice,
            justification=justification,
            source_id=source_id,
            slug=slug,
            extra=kwargs or None,
        )
        logger.info(
            "decision_gateway: D%s (frequent) → auto=%s logged",
            decision_id.value,
            auto_choice,
        )
        return _interpret_default(decision_id, auto_choice)

    # --- D3, D4, D5, D6: CRITICAL ---

    if is_non_interactive():
        # Non-interactive: log and return default
        auto_choice = default
        justification = _AUTO_JUSTIFICATIONS[decision_id]
        _log_decision(
            decision_id=decision_id,
            question=question,
            auto_choice=auto_choice,
            justification=justification,
            source_id=source_id,
            slug=slug,
            extra=kwargs or None,
        )
        logger.info(
            "decision_gateway: D%s (critical, non-interactive) → auto=%s logged",
            decision_id.value,
            auto_choice,
        )
        return _interpret_default(decision_id, auto_choice)

    # Interactive prompt
    prompt_text = _render_template(_PROMPT_TEMPLATES[decision_id], timeout=timeout, **kwargs)
    response = _prompt_with_timeout(prompt_text, timeout=timeout, default=default)

    logger.info(
        "decision_gateway: D%s (critical, interactive) response=%r",
        decision_id.value,
        response,
    )

    # Log the human-made decision too (for auditability)
    _log_decision(
        decision_id=decision_id,
        question=question,
        auto_choice=response,
        justification="human_decision",
        source_id=source_id,
        slug=slug,
        extra={**(kwargs or {}), "interactive": True},
    )

    return _interpret_response(decision_id, response)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_template(template: str, timeout: int = PROMPT_TIMEOUT_SECS, **kwargs: Any) -> str:
    """Render a template string with kwargs, ignoring missing keys gracefully."""
    try:
        return template.format(timeout=timeout, **kwargs)
    except KeyError:
        # Partial render: substitute what we can, leave {missing_key} as-is
        import string

        class _SafeDict(dict):  # type: ignore[type-arg]
            def __missing__(self, key: str) -> str:
                return f"{{{key}}}"

        return string.Formatter().vformat(template, (), _SafeDict(timeout=timeout, **kwargs))


def _interpret_default(decision_id: DecisionID, default: str) -> bool | str:
    """Convert default string to the correct return type for each decision."""
    if decision_id == DecisionID.D3:
        return default  # "2" = apenas memory
    return _parse_yes(default)


def _interpret_response(decision_id: DecisionID, response: str) -> bool | str:
    """Convert user response to the correct return type for each decision."""
    if decision_id == DecisionID.D3:
        # Accept "1", "2", "3" — default to "2" otherwise
        r = response.strip()
        if r in {"1", "2", "3"}:
            return r
        # Treat "y"/"yes" as "1" (most permissive — update both)
        if _parse_yes(r):
            return "1"
        return "2"  # safe default: apenas memory
    return _parse_yes(response)


# ---------------------------------------------------------------------------
# Convenience wrappers for each decision point
# ---------------------------------------------------------------------------


def decide_d1_reprocess(source_id: str, date: str, slug: str = "") -> bool:
    """D1 — Should we reprocess a file already in the ingestion registry?

    Mode C: always auto-NO + log.
    Returns True (reprocess) or False (skip).
    """
    result = prompt_or_log(
        DecisionID.D1,
        source_id=source_id,
        slug=slug,
        date=date,
    )
    return bool(result)


def decide_d2_partial_duplicate(
    source_id: str,
    similarity_pct: int = 0,
    slug: str = "",
) -> bool:
    """D2 — Should we continue when a partial duplicate was detected?

    Mode C: always auto-NO + log.
    Returns True (continue) or False (skip).
    """
    result = prompt_or_log(
        DecisionID.D2,
        source_id=source_id,
        slug=slug,
        similarity_pct=similarity_pct,
    )
    return bool(result)


def decide_d3_update_agent_md(agent_name: str, slug: str = "") -> str:
    """D3 — How should we update an existing agent with new insights?

    Returns "1" (MEMORY+AGENT), "2" (APENAS MEMORY), or "3" (PULAR).
    Mode C: prompts user or defaults to "2" in non-interactive.
    """
    result = prompt_or_log(
        DecisionID.D3,
        source_id="",
        slug=slug,
        agent_name=agent_name,
    )
    return str(result)


def decide_d4_create_cargo_agent(role: str, count: int, slug: str = "") -> bool:
    """D4 — Should we auto-create a new cargo agent for a role at threshold?

    Returns True (create) or False (skip creation).
    Mode C: prompts user or defaults to False in non-interactive.
    """
    result = prompt_or_log(
        DecisionID.D4,
        source_id="",
        slug=slug,
        role=role,
        count=count,
    )
    return bool(result)


def decide_d5_template_evolution(
    framework: str,
    n_agents: int = 0,
    slug: str = "",
) -> bool:
    """D5 — Should we approve a NOVA_PARTE in the template for a framework?

    Returns True (approve) or False (skip).
    Mode C: prompts user or defaults to False in non-interactive.

    NOTE: Template evolution is not yet implemented. This is a NOP stub
    (blocked_by: template_evolution_not_implemented). Calling code should
    check return value but the feature itself requires a future story.
    """
    logger.debug(
        "decision_gateway: D5 called for framework=%s — "
        "template evolution not yet implemented (NOP stub, MCE-11.20)",
        framework,
    )
    result = prompt_or_log(
        DecisionID.D5,
        source_id="",
        slug=slug,
        framework=framework,
        n_agents=n_agents,
    )
    return bool(result)


def decide_d6_bypass_enforcement(rule: str, reason: str, slug: str = "") -> bool:
    """D6 — Should we allow a bypass of an enforcement rule?

    Returns True (allow bypass) or False (reject bypass).
    Mode C: always prompts regardless of non-interactive mode
    (D6 bypass silencioso é proibido — AC7).

    Exception: if MCE_NON_INTERACTIVE=1 AND MCE_FORCE_BYPASS_D6=1, allows
    automated bypass with explicit double-opt-in (useful for automated tests).
    """
    # D6 special case: bypass silencioso é proibido (story AC7).
    # Even in non-interactive mode we require explicit MCE_FORCE_BYPASS_D6=1.
    if is_non_interactive():
        force = os.environ.get("MCE_FORCE_BYPASS_D6", "").lower() in {"1", "true", "yes"}
        if not force:
            question = _render_template(
                _QUESTION_TEMPLATES[DecisionID.D6], rule=rule, reason=reason
            )
            _log_decision(
                decision_id=DecisionID.D6,
                question=question,
                auto_choice="N",
                justification=(
                    "Modo não-interativo: bypass D6 rejeitado automaticamente. "
                    "Defina MCE_FORCE_BYPASS_D6=1 para forçar em automação."
                ),
                source_id="",
                slug=slug,
                extra={"rule": rule, "reason": reason},
            )
            return False

    result = prompt_or_log(
        DecisionID.D6,
        source_id="",
        slug=slug,
        rule=rule,
        reason=reason,
    )
    return bool(result)
