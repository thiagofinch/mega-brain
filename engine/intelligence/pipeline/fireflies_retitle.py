"""fireflies_retitle.py -- Renomeador Temático de calls Fireflies (Story CALL-9)
================================================================================

Por que existe
--------------
O título de uma call no Fireflies vem do evento de agenda ("Fulano e Beltrano")
ou cai em genérico ("Reunião <Empresa> -- data") / código cru ("spo-noec-unk").
Nenhum reflete o TEMA real da conversa. Este módulo lê o conteúdo da transcrição
(o ``summary.overview`` que o Fireflies já gera), infere um título temático via
LLM (``LLMRouter``) e reescreve via ``updateMeetingTitle``.

Reuso (nada reinventado):
  - LLM:            engine.intelligence.pipeline.mce.llm_router.LLMRouter.run_prompt
  - Config/key:     engine.intelligence.pipeline.fireflies_config.load_config
  - Conteúdo:       _QUERY_FULL_TRANSCRIPT (summary.overview/keywords/action_items)
  - Mutation:       updateMeetingTitle (provada em services/google-meet/fix-fireflies-titles.mjs)

Segurança (alinha .claude/rules/extraction-no-fallbacks.md):
  - Sem sinal de conteúdo => retorna None e NÃO renomeia (nunca inventa título).
  - Dry-run é o padrão. --apply reescreve. updateMeetingTitle é reversível
    (Journey Log preserva from_title). Idempotente via state de IDs vistos.

CLI:
  python3 -m engine.intelligence.pipeline.fireflies_retitle                 # dry-run, 30d
  python3 -m engine.intelligence.pipeline.fireflies_retitle --user fulano   # 1 pessoa
  python3 -m engine.intelligence.pipeline.fireflies_retitle --backfill      # universo (2000)
  python3 -m engine.intelligence.pipeline.fireflies_retitle --apply         # reescreve
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from engine.intelligence.pipeline.fireflies_config import load_config
from engine.paths import DATA, LOGS, ROOT

# ── Paths ────────────────────────────────────────────────────────────────────
PROMPT_PATH = ROOT / "engine" / "intelligence" / "pipeline" / "mce" / "prompts" / "meeting-title.prompt.md"
STATE_PATH = DATA / "fireflies-retitle-seen.json"
JOURNAL_PATH = LOGS / "fireflies-retitle-journey.jsonl"
TEAM_SPACES_PATH = ROOT / "services" / "google-meet" / "team-spaces.json"

# ── Queries ──────────────────────────────────────────────────────────────────
_Q_LIST = "query($l:Int,$s:Int){ transcripts(limit:$l,skip:$s){ id title date organizer_email } }"
_Q_FULL = (
    "query($id:String!){ transcript(id:$id){ id title date organizer_email "
    "summary { overview keywords action_items } "
    "sentences { text } } }"
)
_M_RENAME = "mutation($i:UpdateMeetingTitleInput!){ updateMeetingTitle(input:$i){ title } }"

# ── Heurística de preservação ────────────────────────────────────────────────
# Títulos que JÁ descrevem o tema / reuniões recorrentes nomeadas → PRESERVAR.
_DESCRIPTIVE_RE = re.compile(
    r"\b(DAILY|ATA|SCORECARD|ACOMPANHAMENTO\s+SEMANAL|CHECKPOINT|DAILY\s+CS|"
    r"ALL[\s-]?HANDS|KICK[\s-]?OFF|ONBOARDING|MENTORIA|TREINAMENTO|WORKSHOP|"
    r"PLANNING|RETRO|REVIEW|1:1|ONE[\s-]?ON[\s-]?ONE)\b",
    re.IGNORECASE,
)
# Código cru do Meet ("spo-noec-unk", opcionalmente com sufixo) → REESCREVER.
_RAW_CODE_RE = re.compile(r"^[a-z]{3}-[a-z]{4}-[a-z]{3}\b", re.IGNORECASE)
# Genérico nosso ("Reunião <Empresa> — 2026-05-30") → REESCREVER.
# O token da empresa é configurável (MEGA_BRAIN_COMPANY_NAME); na ausência,
# casa "Reunião" seguido de uma palavra capitalizada (título genérico padrão).
_COMPANY_TOKEN = re.escape(os.environ.get("MEGA_BRAIN_COMPANY_NAME", "").strip())
_GENERIC_RE = re.compile(
    rf"^Reuni[aã]o\s+{_COMPANY_TOKEN}\b" if _COMPANY_TOKEN
    else r"^Reuni[aã]o\s+[A-ZÀ-Ý]\w+\b",
    re.IGNORECASE,
)
# Padrão "só nome de pessoa" (call 1:1 nomeada por participante) → REESCREVER.
# Sinais fortes (case-insensitive): "X <> Y", "X · Sua sessão".
_PERSON_PATTERNS = re.compile(r"<>|·|\bSua\s+sess[aã]o", re.IGNORECASE)
# Par de nomes próprios ligado por "e"/"and" — CASE-SENSITIVE para não casar
# conjunção em títulos temáticos ("Captação de leads e estruturação"); só casa
# quando ambos os lados começam com maiúscula ("Fulano e Beltrano").
_NAME_PAIR = re.compile(r"\b[A-ZÀ-Ý][\wÀ-ÿ'-]+\s+(?:e|and)\s+[A-ZÀ-Ý][\wÀ-ÿ'-]+")


def _looks_like_person(title: str) -> bool:
    """True se o título é só nome de participante (não descreve o tema)."""
    return bool(_PERSON_PATTERNS.search(title) or _NAME_PAIR.search(title))

# Sinal mínimo de conteúdo (chars) para autorizar geração; abaixo disso, None.
_MIN_SIGNAL_CHARS = 80
_MAX_TITLE_WORDS = 12


def is_descriptive(title: str) -> bool:
    """True = título já descreve o tema/recorrente => PRESERVAR (skip).

    False = candidato a reescrita (código cru, genérico, só-nome-de-pessoa,
    ou título curto demais para descrever um tema).
    """
    t = (title or "").strip()
    if not t:
        return False
    if _RAW_CODE_RE.match(t) or _GENERIC_RE.match(t):
        return False
    if _DESCRIPTIVE_RE.search(t):
        return True
    if _looks_like_person(t):
        return False
    # Título livre: preserva se tiver substância (>= 3 palavras); senão candidato.
    return len(t.split()) >= 3


def _clean_title(raw: str) -> str:
    """Normaliza a saída do LLM: tira aspas, fences, prefixos e ponto final."""
    t = (raw or "").strip()
    # primeira linha de conteúdo (ignora linhas de code-fence ```)
    lines = [ln.strip() for ln in t.splitlines() if ln.strip() and not ln.strip().startswith("```")]
    if lines:
        t = lines[0]
    t = t.strip().strip("`").strip('"').strip("'")
    t = re.sub(r"^(t[ií]tulo|title)\s*[:\-]\s*", "", t, flags=re.IGNORECASE)
    t = t.rstrip(".").strip()
    return t


def _build_input(transcript: dict[str, Any]) -> str:
    """Monta o texto-fonte para o prompt a partir do conteúdo da call."""
    summary = transcript.get("summary") or {}
    overview = (summary.get("overview") or "").strip()
    keywords = summary.get("keywords") or []
    actions = summary.get("action_items") or ""
    sentences = transcript.get("sentences") or []

    parts: list[str] = []
    if overview:
        parts.append(f"RESUMO:\n{overview}")
    if keywords:
        kw = ", ".join(keywords[:15]) if isinstance(keywords, list) else str(keywords)
        parts.append(f"PALAVRAS-CHAVE: {kw}")
    if actions:
        parts.append(f"AÇÕES: {str(actions)[:500]}")
    if not overview and sentences:
        text = " ".join((s.get("text") or "") for s in sentences[:40])
        if text.strip():
            parts.append(f"TRECHO:\n{text[:1500]}")
    return "\n\n".join(parts).strip()


def generate_thematic_title(transcript: dict[str, Any], router: Any = None) -> str | None:
    """Gera título temático do conteúdo. None se não houver sinal suficiente.

    ``router`` é injetável para teste (qualquer objeto com ``run_prompt``).
    """
    content = _build_input(transcript)
    if len(content) < _MIN_SIGNAL_CHARS:
        return None  # sem conteúdo => não inventa (extraction-no-fallbacks)

    if router is None:
        from engine.intelligence.pipeline.mce.llm_router import LLMRouter

        router = LLMRouter()

    prompt = PROMPT_PATH.read_text(encoding="utf-8").format(
        content=content[:6000],
        current_title=transcript.get("title", ""),
    )
    raw = router.run_prompt(prompt, step="meeting-title", max_output_tokens=60)
    title = _clean_title(raw)
    if not title or len(title.split()) > _MAX_TITLE_WORDS:
        return None
    # Não reescreve se a saída for igual ao título atual
    if title.strip().lower() == (transcript.get("title") or "").strip().lower():
        return None
    return title


# ── State / Journal ──────────────────────────────────────────────────────────
def _journal_ids() -> set[str]:
    """IDs já renomeados com sucesso, lidos do Journey Log (append-only).

    Esta é a fonte de verdade da idempotência: mesmo que o state file não
    persista (ex.: processo cortado antes do save final), o journal — escrito a
    cada rename — garante que nenhuma call seja renomeada duas vezes.
    """
    ids: set[str] = set()
    if JOURNAL_PATH.exists():
        for line in JOURNAL_PATH.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("ok") and e.get("transcript_id"):
                ids.add(e["transcript_id"])
    return ids


def _load_seen() -> set[str]:
    seen: set[str] = set()
    if STATE_PATH.exists():
        try:
            seen = set(json.loads(STATE_PATH.read_text(encoding="utf-8")).get("seen", []))
        except Exception:
            seen = set()
    return seen | _journal_ids()  # journal é a salvaguarda confiável


def _save_seen(seen: set[str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"seen": sorted(seen)}, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_PATH)  # gravação atômica


def _journal(entry: dict[str, Any]) -> None:
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── GraphQL ──────────────────────────────────────────────────────────────────
def _graphql(cfg: Any, query: str, variables: dict | None = None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    req = urllib.request.Request(
        cfg.graphql_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.api_key}",
            "User-Agent": "MegaBrain-FirefliesRetitle/1.0",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            if "errors" in result:
                # 429 vem como errors no corpo às vezes
                if any("too_many" in json.dumps(e).lower() for e in result["errors"]):
                    time.sleep(5 * (attempt + 1))
                    continue
                raise RuntimeError(f"GraphQL errors: {json.dumps(result['errors'])[:300]}")
            return result.get("data", {})
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError("GraphQL falhou após 5 tentativas")


def _resolve_user_email(user_slug: str | None) -> str | None:
    if not user_slug:
        return None
    team = json.loads(TEAM_SPACES_PATH.read_text(encoding="utf-8"))
    for s in team.get("spaces", []):
        if s.get("slug") == user_slug:
            return s.get("email")
    return None


# ── Orchestration ────────────────────────────────────────────────────────────
def retitle(
    days: int = 30,
    apply: bool = False,
    user: str | None = None,
    backfill: bool = False,
    router: Any = None,
) -> dict[str, int]:
    cfg = load_config()
    if not cfg.api_key:
        raise RuntimeError("FIREFLIES_API_KEY ausente no .env")

    user_email = _resolve_user_email(user)
    page_cap = 2000 if backfill else 800

    # listar
    all_items: list[dict] = []
    for skip in range(0, page_cap, 50):
        d = _graphql(cfg, _Q_LIST, {"l": 50, "s": skip})
        batch = d.get("transcripts") or []
        all_items.extend(batch)
        if len(batch) < 50:
            break
    cutoff_ms = (datetime.now(UTC).timestamp() - days * 86400) * 1000
    recent = [t for t in all_items if float(t.get("date") or 0) >= cutoff_ms]
    if user_email:
        recent = [t for t in recent if (t.get("organizer_email") or "").lower() == user_email.lower()]

    seen = _load_seen()
    stats = {"scanned": len(recent), "preserved": 0, "no_signal": 0, "already": 0, "to_change": 0, "changed": 0, "failed": 0}
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"\nRenomeador Temático  [{mode}]  janela {days}d  | {len(recent)} transcrições"
          f"{' | user=' + user if user else ''}\n")

    for t in recent:
        tid = t.get("id")
        if not tid or tid in seen:
            stats["already"] += 1
            continue
        cur = t.get("title") or ""
        if is_descriptive(cur):
            stats["preserved"] += 1
            continue
        # Erro por-item NUNCA aborta o batch (ex.: transcrição deletada => 404).
        try:
            full = _graphql(cfg, _Q_FULL, {"id": tid}).get("transcript") or {}
        except Exception as exc:
            if "not_found" in str(exc).lower():
                seen.add(tid)  # fantasma (deletada) — não re-tentar
            stats["failed"] += 1
            print(f"  ✗ fetch {tid[:10]}: {str(exc)[:70]}")
            continue
        new_title = generate_thematic_title(full, router=router)
        if not new_title:
            stats["no_signal"] += 1
            continue
        stats["to_change"] += 1
        date_s = datetime.fromtimestamp(float(t.get("date") or 0) / 1000, tz=UTC).strftime("%Y-%m-%d")
        print(f"  {'✓' if apply else '•'} {date_s}  \"{cur[:34]}\"  →  \"{new_title}\"")
        if apply:
            try:
                r = _graphql(cfg, _M_RENAME, {"i": {"id": tid, "title": new_title}})
                ok = bool(r.get("updateMeetingTitle"))
            except Exception as exc:
                ok = False
                if "not_found" in str(exc).lower():
                    seen.add(tid)  # fantasma — não re-tentar
                print(f"  ✗ rename {tid[:10]}: {str(exc)[:70]}")
            _journal({
                "ts": datetime.now(UTC).isoformat(),
                "transcript_id": tid, "from_title": cur, "to_title": new_title, "ok": ok,
            })
            if ok:
                stats["changed"] += 1
                seen.add(tid)
                if stats["changed"] % 10 == 0:
                    _save_seen(seen)  # checkpoint — resiste a corte do processo
            else:
                stats["failed"] += 1
            time.sleep(1.5)  # rate limit do Fireflies em mutations

    if apply:
        _save_seen(seen)

    print(f"\nResumo: {stats['to_change']} a renomear | "
          f"{stats['changed']} renomeados | {stats['failed']} falhas | "
          f"{stats['preserved']} preservados | {stats['no_signal']} sem conteúdo")
    if not apply:
        print("(DRY-RUN — nada alterado. Rode com --apply para renomear.)")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description="Renomeador temático de calls Fireflies (CALL-9)")
    ap.add_argument("--apply", action="store_true", help="reescreve os títulos (default: dry-run)")
    ap.add_argument("--days", type=int, default=30, help="janela em dias (default 30)")
    ap.add_argument("--user", type=str, default=None, help="slug do colaborador (team-spaces)")
    ap.add_argument("--backfill", action="store_true", help="varre o universo completo (até 2000)")
    args = ap.parse_args()
    retitle(days=args.days, apply=args.apply, user=args.user, backfill=args.backfill)


if __name__ == "__main__":
    main()
