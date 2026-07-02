"""
semantic_logger.py -- Event Stream Semântico do Pipeline MCE
============================================================

Em vez de mostrar "fase 4 concluída, 12 insights", mostra:

    [acme/F4] ⚡ INSIGHT CRÍTICO
        "Churn 50%→13% = R$150K por cada 5% reduzido"
        → Impacto: EBITDA meta R$9,88M | Owner: Fulano de Tal

    [acme/F3] 🔗 NOVA ENTIDADE
        "Operação Exemplo" → linked: Fulano de Tal, Acme B2B

    [founder/F7] 🤖 AGENTE CRIADO
        "example-expert" (threshold 10 menções atingido)
        → /agents/cargo/SALES/example-expert/

    [acme/F8] 🧬 DNA EXTRAÍDO
        FILOSOFIAS.yaml +2 · FRAMEWORKS.yaml +1

O sistema:
    1. Cada fase escreve eventos em .data/pipeline-events.jsonl
    2. O display lê e narra em tempo real
    3. Agrega arquivos na mesma fase — mostra tudo junto
    4. Nenhuma interrupção, nenhum quality gate

Usage:
    from engine.intelligence.pipeline.semantic_logger import PipelineEventWriter, PipelineDisplay

    # Em cada fase do process-jarvis:
    writer = PipelineEventWriter(slug="acme")
    writer.insight(priority="HIGH", text="Churn...", person="Fulano", impact="R$150K")
    writer.entity_created("Operação Exemplo", linked_to=["Fulano de Tal"])
    writer.agent_created("example-expert", reason="threshold 10 atingido")
    writer.dossier_updated("DOSSIER-FULANO-DE-TAL.md", sections_added=3, insights_added=12)
    writer.dna_extracted("acme", layers={"FILOSOFIAS": 2, "FRAMEWORKS": 1})
    writer.phase_complete(phase=4, phase_name="INSIGHT EXTRACTION")

    # O display (chamado pelo orchestrador):
    display = PipelineDisplay()
    display.render()  # Emite o painel atual via print()
"""

from __future__ import annotations

import fcntl
import json
import os
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any


@contextmanager
def _exclusive_lock(file_obj):
    """Acquire exclusive POSIX advisory lock on file. Released automatically.

    Required because POSIX guarantees atomic append ONLY for writes <= PIPE_BUF
    (4 KB on macOS). Larger payloads (Phase-5 dossiers, agent_created with full
    payload) can interleave under concurrent writers.

    Reference: STORY-OS-001 AC2-AC4 + roundtable 2026-05-06 finding F2.
    """
    fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_EVENTS_PATH = _PROJECT_ROOT / ".data" / "pipeline-events.jsonl"
_BATCH_STATUS_PATH = _PROJECT_ROOT / ".data" / "BATCH-STATUS.json"

PHASE_ICONS = {
    1: "🔍",
    2: "✂️ ",
    3: "🔗",
    4: "⚡",
    5: "📝",
    6: "📁",
    7: "🤖",
    8: "🧬",
}
PHASE_NAMES = {
    1: "INIT",
    2: "CHUNKING",
    3: "ENTITIES",
    4: "INSIGHTS",
    5: "NARRATIVE",
    6: "DOSSIER",
    7: "AGENTS",
    8: "FINALIZE+DNA",
}
PRIORITY_ICONS = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "CRITICAL": "🚨"}


# ---------------------------------------------------------------------------
# Event Writer — usado pelo process-jarvis em cada fase
# ---------------------------------------------------------------------------


class PipelineEventWriter:
    """Escrita de eventos semânticos durante o pipeline. Thread-safe via append atômico.

    batch_id identifica a ingestão — cada /process-inbox invocation tem um ID único.
    Múltiplas ingestões simultâneas (Fireflies + Drive + YouTube) ficam isoladas.
    O display agrupa por batch_id e mostra seções separadas por fonte.
    """

    def __init__(
        self,
        slug: str,
        batch_id: str = "",
        source: str = "inbox",
        project_root: Path | None = None,
    ):
        self.slug = slug
        self.batch_id = batch_id or os.environ.get("PIPELINE_BATCH_ID", "default")
        self.source = source  # "fireflies" | "google_drive" | "youtube" | "inbox"
        root = project_root or _PROJECT_ROOT
        self._path = root / ".data" / "pipeline-events.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, event_type: str, data: dict[str, Any]) -> None:
        event = {
            "ts": time.time(),
            "slug": self.slug,
            "batch_id": self.batch_id,
            "source": self.source,
            "type": event_type,
            **data,
        }
        line = json.dumps(event, ensure_ascii=False) + "\n"
        # POSIX advisory lock — safe for payloads > PIPE_BUF (4 KB).
        # See _exclusive_lock docstring + STORY-OS-001 AC2.
        with open(self._path, "a", encoding="utf-8") as f:
            with _exclusive_lock(f):
                f.write(line)
                f.flush()

    # -- Eventos de fase --

    def phase_start(self, phase: int, file_path: str = "") -> None:
        self._write(
            "phase_start",
            {"phase": phase, "phase_name": PHASE_NAMES.get(phase, "?"), "file": file_path},
        )

    def phase_complete(self, phase: int, phase_name: str = "", summary: dict | None = None) -> None:
        self._write(
            "phase_complete",
            {
                "phase": phase,
                "phase_name": phase_name or PHASE_NAMES.get(phase, "?"),
                "summary": summary or {},
            },
        )

    # -- Eventos de conteúdo --

    def insight(
        self,
        priority: str,
        text: str,
        person: str = "",
        theme: str = "",
        impact: str = "",
        action_item: str = "",
    ) -> None:
        self._write(
            "insight",
            {
                "priority": priority,
                "text": text[:120],
                "person": person,
                "theme": theme,
                "impact": impact,
                "action_item": action_item,
            },
        )

    def entity_created(
        self, name: str, entity_type: str = "concept", linked_to: list[str] | None = None
    ) -> None:
        self._write(
            "entity_created",
            {
                "name": name,
                "entity_type": entity_type,
                "linked_to": linked_to or [],
            },
        )

    def entity_updated(self, name: str, aliases_added: int = 0, sources_added: int = 0) -> None:
        self._write(
            "entity_updated",
            {"name": name, "aliases_added": aliases_added, "sources_added": sources_added},
        )

    def dossier_created(
        self, filename: str, person: str = "", sections: int = 0, insights: int = 0
    ) -> None:
        self._write(
            "dossier_created",
            {"filename": filename, "person": person, "sections": sections, "insights": insights},
        )

    def dossier_updated(
        self,
        filename: str,
        sections_added: int = 0,
        insights_added: int = 0,
        decisions_added: int = 0,
    ) -> None:
        self._write(
            "dossier_updated",
            {
                "filename": filename,
                "sections_added": sections_added,
                "insights_added": insights_added,
                "decisions_added": decisions_added,
            },
        )

    def agent_created(self, agent_name: str, reason: str = "", path: str = "") -> None:
        self._write("agent_created", {"agent_name": agent_name, "reason": reason, "path": path})

    def agent_updated(
        self, agent_name: str, memory_entries: int = 0, frameworks_added: int = 0
    ) -> None:
        self._write(
            "agent_updated",
            {
                "agent_name": agent_name,
                "memory_entries": memory_entries,
                "frameworks_added": frameworks_added,
            },
        )

    def agent_queued_l3(self, agent_name: str, reason: str = "") -> None:
        """Agente novo → L3 approval queue (Art. VII)."""
        self._write("agent_queued_l3", {"agent_name": agent_name, "reason": reason})

    def dna_extracted(self, person: str, layers: dict[str, int]) -> None:
        """DNA cognitivo extraído — layers = {FILOSOFIAS: 3, FRAMEWORKS: 2, ...}"""
        self._write(
            "dna_extracted", {"person": person, "layers": layers, "total": sum(layers.values())}
        )

    def chunk_batch(self, count: int, avg_words: int = 0) -> None:
        self._write("chunk_batch", {"count": count, "avg_words": avg_words})

    def narrative_synthesized(
        self,
        persons_updated: int = 0,
        themes_updated: int = 0,
        open_loops: int = 0,
        tensions: int = 0,
    ) -> None:
        self._write(
            "narrative_synthesized",
            {
                "persons_updated": persons_updated,
                "themes_updated": themes_updated,
                "open_loops": open_loops,
                "tensions": tensions,
            },
        )

    def rag_indexed(self, bucket: str, chunks_added: int, vectors_added: int) -> None:
        self._write(
            "rag_indexed",
            {"bucket": bucket, "chunks_added": chunks_added, "vectors_added": vectors_added},
        )

    def trigger_fired(self, trigger_name: str, detail: str = "") -> None:
        """Qualquer trigger ativado durante o pipeline."""
        self._write("trigger_fired", {"trigger_name": trigger_name, "detail": detail})

    def file_complete(
        self, file_path: str, phases_completed: int = 8, duration_s: float = 0
    ) -> None:
        self._write(
            "file_complete",
            {
                "file": file_path,
                "phases_completed": phases_completed,
                "duration_s": round(duration_s, 1),
            },
        )


# ---------------------------------------------------------------------------
# Event Reader + Aggregator
# ---------------------------------------------------------------------------


class PipelineEventAggregator:
    """Lê pipeline-events.jsonl e agrega por fase/tipo para o display."""

    def __init__(self, project_root: Path | None = None):
        root = project_root or _PROJECT_ROOT
        self._path = root / ".data" / "pipeline-events.jsonl"
        self._batch_path = root / ".data" / "BATCH-STATUS.json"

    def read_events(self, since_ts: float = 0) -> list[dict]:
        if not self._path.exists():
            return []
        events = []
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get("ts", 0) >= since_ts:
                        events.append(ev)
                except json.JSONDecodeError:
                    continue
        return events

    def batch_status(self) -> dict:
        if not self._batch_path.exists():
            return {}
        with open(self._batch_path) as f:
            return json.load(f)

    def aggregate(self) -> dict:
        events = self.read_events()
        agg: dict[str, Any] = {
            "by_phase": defaultdict(lambda: {"completed": 0, "in_progress": set()}),
            "insights_high": [],
            "insights_medium": [],
            "entities_new": [],
            "dossiers_created": [],
            "dossiers_updated": [],
            "agents_created": [],
            "agents_updated": [],
            "agents_queued_l3": [],
            "dna_extractions": [],
            "triggers": [],
            "files_complete": [],
            "rag_total_chunks": 0,
            "active_slugs": set(),
        }
        for ev in events:
            slug = ev.get("slug", "?")
            agg["active_slugs"].add(slug)
            t = ev.get("type", "")
            if t == "phase_complete":
                agg["by_phase"][ev.get("phase", 0)]["completed"] += 1
            elif t == "phase_start":
                agg["by_phase"][ev.get("phase", 0)]["in_progress"].add(slug)
            elif t == "insight":
                p = ev.get("priority", "LOW")
                item = {
                    "slug": slug,
                    "priority": p,
                    "text": ev.get("text", ""),
                    "person": ev.get("person", ""),
                    "impact": ev.get("impact", ""),
                }
                if p in ("HIGH", "CRITICAL"):
                    agg["insights_high"].append(item)
                else:
                    agg["insights_medium"].append(item)
            elif t == "entity_created":
                agg["entities_new"].append(
                    {"slug": slug, "name": ev.get("name", ""), "linked_to": ev.get("linked_to", [])}
                )
            elif t == "dossier_created":
                agg["dossiers_created"].append(
                    {
                        "slug": slug,
                        "filename": ev.get("filename", ""),
                        "insights": ev.get("insights", 0),
                    }
                )
            elif t == "dossier_updated":
                agg["dossiers_updated"].append(
                    {
                        "slug": slug,
                        "filename": ev.get("filename", ""),
                        "insights_added": ev.get("insights_added", 0),
                        "sections_added": ev.get("sections_added", 0),
                    }
                )
            elif t == "agent_created":
                agg["agents_created"].append(
                    {
                        "slug": slug,
                        "agent": ev.get("agent_name", ""),
                        "reason": ev.get("reason", ""),
                    }
                )
            elif t == "agent_updated":
                agg["agents_updated"].append(
                    {
                        "slug": slug,
                        "agent": ev.get("agent_name", ""),
                        "memory": ev.get("memory_entries", 0),
                    }
                )
            elif t == "agent_queued_l3":
                agg["agents_queued_l3"].append(
                    {
                        "slug": slug,
                        "agent": ev.get("agent_name", ""),
                        "reason": ev.get("reason", ""),
                    }
                )
            elif t == "dna_extracted":
                agg["dna_extractions"].append(
                    {
                        "slug": slug,
                        "person": ev.get("person", ""),
                        "layers": ev.get("layers", {}),
                        "total": ev.get("total", 0),
                    }
                )
            elif t == "trigger_fired":
                agg["triggers"].append(
                    {
                        "slug": slug,
                        "trigger": ev.get("trigger_name", ""),
                        "detail": ev.get("detail", ""),
                    }
                )
            elif t == "rag_indexed":
                agg["rag_total_chunks"] += ev.get("chunks_added", 0)
            elif t == "file_complete":
                agg["files_complete"].append(
                    {"slug": slug, "file": ev.get("file", ""), "duration": ev.get("duration_s", 0)}
                )

        return agg


# ---------------------------------------------------------------------------
# Display Renderer
# ---------------------------------------------------------------------------

W = 72  # panel width


def _bar(done: int, total: int, width: int = 20) -> str:
    if total == 0:
        return "░" * width
    filled = round(done / total * width)
    return "█" * filled + "░" * (width - filled)


def _trunc(s: str, n: int) -> str:
    return s[: n - 1] + "…" if len(s) > n else s


class PipelineDisplay:
    """Renderiza painel ASCII consolidado e semântico para o chat."""

    def __init__(self, total_files: int = 0, project_root: Path | None = None):
        self.total = total_files
        self._agg = PipelineEventAggregator(project_root)

    def render(self) -> str:
        """Gera e retorna o painel como string. Chame print(display.render())."""
        agg = self._agg.aggregate()
        batch = self._agg.batch_status()

        files_done = len(agg["files_complete"])
        total = self.total or batch.get("total", 0) or 1
        _pct = files_done / total

        lines: list[str] = []

        def ln(s: str = "") -> None:
            lines.append(s)

        # Header
        ln(f"╔{'═' * W}╗")
        ln(
            f"║  MCE PIPELINE {'▸':>2} {total} arquivos {'▸':>2} {len(agg['active_slugs'])} slugs ativos{' ' * max(0, W - 46)}║"
        )
        ln(f"╠{'═' * W}╣")

        # Progress bar
        bar = _bar(files_done, total, 40)
        eta = batch.get("eta", "--:--")
        ln(f"║  {bar} {files_done}/{total} ▸ ETA {eta}{' ' * max(0, W - 52)}║")

        # Phase summary
        ln(f"╠{'═' * W}╣")
        for phase in range(1, 9):
            icon = PHASE_ICONS.get(phase, "  ")
            name = PHASE_NAMES.get(phase, f"F{phase}")
            phase_data = agg["by_phase"].get(phase, {})
            done = phase_data.get("completed", 0) if isinstance(phase_data, dict) else 0
            active = phase_data.get("in_progress", set()) if isinstance(phase_data, dict) else set()
            bar_ph = _bar(done, total, 16)
            active_str = f"  ↻ {','.join(list(active)[:3])}" if active else ""
            ln(
                f"║  F{phase} {icon} {name:<12} {bar_ph} {done:>3}✓{active_str:<20}{' ' * max(0, W - 67)}║"
            )

        # Semantic events section
        ln(f"╠{'═' * W}╣")
        ln(f"║  EVENTOS RECENTES{' ' * (W - 18)}║")
        ln(f"╠{'═' * W}╣")

        # HIGH insights (last 3)
        for item in agg["insights_high"][-3:]:
            icon = PRIORITY_ICONS.get(item["priority"], "•")
            slug = item["slug"]
            text = _trunc(item["text"], 52)
            impact = f" → {item['impact']}" if item.get("impact") else ""
            ln(f"║  {icon} [{slug}/F4] {text}{' ' * max(0, W - 12 - len(slug) - len(text))}║")
            if impact:
                ln(
                    f"║       {_trunc(impact, W - 9)}{' ' * max(0, W - 7 - len(_trunc(impact, W-9)))}║"
                )

        # New entities (last 3)
        for item in agg["entities_new"][-3:]:
            name = item["name"]
            linked = " → " + ", ".join(item["linked_to"][:2]) if item.get("linked_to") else ""
            ln(
                f"║  🔗 [{item['slug']}/F3] {_trunc(name + linked, W - 16)}{' ' * max(0, W - 16 - len(_trunc(name + linked, W-16)))}║"
            )

        # Dossiers created/updated (last 3)
        for item in (agg["dossiers_created"] + agg["dossiers_updated"])[-3:]:
            verb = "CRIADO" if item in agg["dossiers_created"] else "UPDATE"
            fn = item.get("filename", "?")
            n_ins = item.get("insights", item.get("insights_added", 0))
            n_sec = item.get("sections", item.get("sections_added", 0))
            detail = f"+{n_ins} insights" + (f" +{n_sec} seções" if n_sec else "")
            ln(
                f"║  📁 {verb} {_trunc(fn, 35)} {detail}{' ' * max(0, W - 12 - len(_trunc(fn,35)) - len(detail))}║"
            )

        # Agents created
        for item in agg["agents_created"][-2:]:
            ln(
                f"║  🤖 AGENTE CRIADO: {item['agent']}{' — ' + item['reason'] if item.get('reason') else ''}{' ' * max(0, W - 22 - len(item['agent']))}║"
            )

        # Agents L3 queued
        for item in agg["agents_queued_l3"][-2:]:
            ln(
                f"║  ⏳ L3 QUEUE: {item['agent']} (aguarda aprovação){' ' * max(0, W - 42 - len(item['agent']))}║"
            )

        # DNA extractions
        for item in agg["dna_extractions"][-2:]:
            layers_str = " · ".join(f"{k} +{v}" for k, v in item["layers"].items())
            ln(
                f"║  🧬 DNA [{item['person']}] {_trunc(layers_str, W - 20)}{' ' * max(0, W - 12 - len(item['person']) - len(_trunc(layers_str, W-20)))}║"
            )

        # Triggers
        for item in agg["triggers"][-2:]:
            ln(
                f"║  ⚡ TRIGGER: {item['trigger']}{' — ' + item['detail'][:30] if item.get('detail') else ''}{' ' * 5}║"
            )

        # RAG summary
        if agg["rag_total_chunks"] > 0:
            ln(f"╠{'═' * W}╣")
            ln(
                f"║  RAG business: +{agg['rag_total_chunks']} chunks indexados{' ' * max(0, W - 30 - len(str(agg['rag_total_chunks'])))}║"
            )

        ln(f"╚{'═' * W}╝")

        return "\n".join(lines)

    def emit(self) -> None:
        """Emite o painel via print (para aparecer no chat como feedback)."""
        print(self.render())
