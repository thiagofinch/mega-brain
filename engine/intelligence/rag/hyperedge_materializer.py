#!/usr/bin/env python3
"""Hyperedge materializer — STORY-HGA-F2.2 (HE-001 materialization + durable overlay).

Turns ONE real meeting transcript into ONE living hyperedge in the production graph:
a 9-participant call is stored as a single `meeting` fact (1 node-event H + 9 member
edges PARTICIPA) instead of 36 lossy binary pairs. This fulfils the epic's success
criterion #2 ("group events as ONE fact") — the primitive `add_hyperedge` has existed
since STORY-HGA-F2.1, but no hyperedge had actually been written to the production graph.

This module is a THIN materializer. It does NOT reimplement star-expansion: it
*invokes* `KnowledgeGraph.add_hyperedge` (graph_builder.py:334), the sole, proven
primitive. Its two jobs are:

  1. Parse the call header `Participants:` line → resolve `PESSOA:{local-part}` ids,
     drop the Fireflies bot, upsert the 9 person nodes idempotently (RNF-G2: all
     participants must exist BEFORE add_hyperedge, which raises on a missing node).
  2. Solve DURABILITY (constraint R1, @architect): `rebuild.py:97-98` does
     `graph = build_graph(); graph.save()` on every `cmd_finalize`, OVERWRITING
     graph.json wholesale. A hyperedge written straight into graph.json would be
     ephemeral. So the materialized hyperedge is persisted to a sidecar
     `he-overlay.json` and replayed by `_replay_hyperedge_overlay` at the end of
     `build_graph()` — re-derived every rebuild, exactly like Hyper-Extract re-derives
     its hypergraph on export (`hypergraph.py` @ 4e333f847f1d). Overlay absent/empty =
     no-op → legacy graph.json byte-identical.

RNF-G1: the hyperedge `metadata` (bucket, meet_id) rides on the EDGE — `Edge.to_dict`
serializes `metadata`, `Entity.to_dict` does NOT. `add_hyperedge` already merges the
caller `metadata` dict onto each member edge's bookkeeping (graph_builder.py:425-426),
so passing `metadata={"bucket": ..., "meet_id": ...}` lands it on the durable edge,
never on the lossy person node.

CLI (Art. I — CLI First, no UI):
    python3 -m engine.intelligence.rag.hyperedge_materializer \
        --call "<path>" [--rel-label meeting] [--exclude-bots] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from engine.intelligence.rag.graph_builder import (
    GRAPH_DIR,
    GRAPH_FILE,
    Entity,
    KnowledgeGraph,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
# The durable sidecar lives next to graph.json under .data/ (gitignored — runtime
# operational state, never tracked). Replayed by build_graph() on every rebuild.
OVERLAY_FILE = GRAPH_DIR / "he-overlay.json"

# Bot domains never count as human participants (fred@fireflies.ai is the recorder).
BOT_DOMAINS = frozenset({"fireflies.ai"})


# ---------------------------------------------------------------------------
# HEADER PARSER
# ---------------------------------------------------------------------------
def _slug_from_email(email: str) -> str:
    """`jane.doe@example.com` → `jane.doe` (local-part, lowercased)."""
    return email.split("@", 1)[0].strip().lower()


def _is_bot(email: str, *, exclude_bots: bool) -> bool:
    """Fireflies bot is dropped unconditionally; --exclude-bots is reserved for
    future bot domains (today it is a superset of the always-on Fireflies drop)."""
    domain = email.split("@", 1)[-1].strip().lower() if "@" in email else ""
    if domain in BOT_DOMAINS:
        return True
    return exclude_bots and domain in BOT_DOMAINS


def parse_participants(
    call_path: Path, *, exclude_bots: bool = True
) -> list[str]:
    """Extract human participant emails from the `Participants:` header line.

    Split by comma, strip each item, drop `@fireflies.ai` (and any bot when
    --exclude-bots). For [MEET-1376] this resolves exactly 9 humans, dropping
    `fred@fireflies.ai`.

    Returns the raw human emails (order preserved); slug/id resolution is done by
    the caller so dry-run can show both.
    """
    text = call_path.read_text(encoding="utf-8")
    m = re.search(r"^Participants:\s*(.+)$", text, flags=re.MULTILINE)
    if not m:
        raise ValueError(f"no 'Participants:' header line in {call_path}")

    emails = [p.strip() for p in m.group(1).split(",") if p.strip()]
    humans = [e for e in emails if not _is_bot(e, exclude_bots=exclude_bots)]
    if not humans:
        raise ValueError(f"no human participants resolved from {call_path}")
    return humans


def parse_date(call_path: Path) -> str:
    """Extract the call date (YYYY-MM-DD) from the `Date:` header. Falls back to ''."""
    text = call_path.read_text(encoding="utf-8")
    m = re.search(r"^Date:\s*(\d{4}-\d{2}-\d{2})", text, flags=re.MULTILINE)
    return m.group(1) if m else ""


def parse_atomic_facts(call_path: Path, *, max_facts: int = 2) -> list[str]:
    """Pull 1-2 verbatim summary bullets as the hyperedge's evidence trail.

    NOT structured extraction (story OUT-of-scope) — just the first 1-2 SUMMARY
    bullets verbatim, so the hyperedge carries an anti-hallucination citation.
    """
    text = call_path.read_text(encoding="utf-8")
    m = re.search(r"--- SUMMARY ---\s*(.+?)(?:\n---|\Z)", text, flags=re.DOTALL)
    if not m:
        return []
    facts: list[str] = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("-"):
            fact = line.lstrip("-").strip().rstrip()
            # strip markdown bold markers but keep the verbatim wording
            fact = fact.replace("**", "")
            if fact:
                facts.append(fact)
        if len(facts) >= max_facts:
            break
    return facts


def _meet_id_from_path(call_path: Path) -> str:
    """`[MEET-1376] ...txt` → `MEET-1376`. Falls back to the stem."""
    m = re.search(r"\[([A-Z]+-\d+)\]", call_path.name)
    return m.group(1) if m else call_path.stem


# ---------------------------------------------------------------------------
# NODE UPSERT (RNF-G2: all participants exist BEFORE add_hyperedge)
# ---------------------------------------------------------------------------
def _label_for(slug: str) -> str:
    """`jane.doe` → `Jane Doe` (title-cased; real name unavailable here)."""
    return slug.replace(".", " ").replace("-", " ").title()


def upsert_person_nodes(
    graph: KnowledgeGraph, emails: list[str]
) -> tuple[list[str], dict[str, str]]:
    """Idempotently upsert `PESSOA:{slug}` nodes; return (ids, id→label map).

    - id   = `PESSOA:{local-part-lowercased}`
    - type = "pessoa"
    - label= local-part title-cased (real name unavailable from the header alone)
    - person = slug
    Skip silently if the node already exists (no duplicate, no label overwrite). The
    label map is persisted in the overlay so replay can self-upsert these nodes.
    """
    ids: list[str] = []
    labels: dict[str, str] = {}
    for email in emails:
        slug = _slug_from_email(email)
        node_id = f"PESSOA:{slug}"
        label = _label_for(slug)
        if node_id not in graph.entities:
            graph.add_entity(
                Entity(
                    entity_id=node_id,
                    entity_type="pessoa",
                    label=label,
                    person=slug,
                )
            )
        ids.append(node_id)
        labels[node_id] = label
    return ids, labels


# ---------------------------------------------------------------------------
# OVERLAY PERSISTENCE (durability — constraint R1)
# ---------------------------------------------------------------------------
def _load_overlay(overlay_path: Path) -> list[dict]:
    """Read the sidecar overlay; absent/empty/corrupt → empty list (no-op)."""
    if not overlay_path.exists():
        return []
    try:
        data = json.loads(overlay_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    entries = data.get("hyperedges", []) if isinstance(data, dict) else []
    return entries if isinstance(entries, list) else []


def write_overlay_entry(entry: dict, overlay_path: Path = OVERLAY_FILE) -> None:
    """Append a hyperedge entry to the durable overlay, idempotent on `he_id`.

    The overlay is the re-applicable source-of-truth that survives the
    rebuild.py:97-98 overwrite. Each entry carries everything add_hyperedge needs to
    be replayed deterministically.
    """
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    entries = _load_overlay(overlay_path)

    existing = {e.get("he_id") for e in entries}
    if entry["he_id"] not in existing:
        entries.append(entry)

    payload = {"version": "1.0.0", "hyperedges": entries}
    overlay_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _overlay_entry(
    *,
    he_id: str,
    participants: list[str],
    participant_labels: dict[str, str],
    rel_label: str,
    t_start: list[str],
    atomic_facts: list[str],
    metadata: dict,
) -> dict:
    """Build a deterministic, replay-ready overlay entry for one hyperedge.

    Carries ``participant_labels`` so the replay can self-upsert the person nodes —
    business participants aren't in the external DNA dir that build_graph reads, so
    the overlay must be self-contained to survive rebuild.py:97-98.
    """
    return {
        "he_id": he_id,
        "participants": participants,
        "participant_labels": participant_labels,
        "rel_label": rel_label,
        "rel_type": "PARTICIPA",
        "t_start": t_start,
        "atomic_facts": atomic_facts,
        "metadata": metadata,
    }


# ---------------------------------------------------------------------------
# MATERIALIZE
# ---------------------------------------------------------------------------
def materialize_call(
    call_path: Path,
    *,
    rel_label: str = "meeting",
    exclude_bots: bool = True,
    dry_run: bool = False,
    graph: KnowledgeGraph | None = None,
    overlay_path: Path = OVERLAY_FILE,
    graph_path: Path = GRAPH_FILE,
) -> dict:
    """Materialize ONE call as ONE living hyperedge + durable overlay entry.

    Loads the live graph (unless one is injected for tests), upserts the human
    participant nodes (RNF-G2), invokes the F2.1 primitive ONCE, persists the
    durable overlay entry, and saves the graph. `--dry-run` plans without mutating.

    Returns a report dict (participants, he_id, counts).
    """
    emails = parse_participants(call_path, exclude_bots=exclude_bots)
    date = parse_date(call_path) or ""
    facts = parse_atomic_facts(call_path)
    meet_id = _meet_id_from_path(call_path)
    metadata = {"bucket": "business", "meet_id": meet_id}

    # Resolve ids deterministically so dry-run can show the plan without mutating.
    participant_ids = sorted(f"PESSOA:{_slug_from_email(e)}" for e in emails)
    # The primitive sorts participants for the H id — mirror it for the plan.
    he_id = f"he::{rel_label}::" + "|".join(participant_ids)

    report = {
        "call": str(call_path),
        "meet_id": meet_id,
        "rel_label": rel_label,
        "participants": participant_ids,
        "participant_count": len(participant_ids),
        "he_id": he_id,
        "t_start": [date] if date else [],
        "atomic_facts": facts,
        "dry_run": dry_run,
    }

    if dry_run:
        return report

    # Real run: load the live graph (or use the injected one), upsert nodes, invoke.
    if graph is None:
        graph = KnowledgeGraph()
        graph.load(graph_path)  # absent → empty graph; materialization still works

    ids, labels = upsert_person_nodes(graph, emails)  # RNF-G2: all 9 exist BEFORE call

    # Idempotent live-apply: the H id is the sorted-set of participants, so re-running
    # the CLI on an already-materialized graph must NOT double the member edges (the
    # add_entity is idempotent but add_edge always appends). When the H already has its
    # member edges, skip the live re-expansion — the overlay (below) stays the source
    # of truth and the next rebuild re-derives a clean star anyway.
    already = any(
        e.source == he_id and e.rel_type == "PARTICIPA" for e in graph.edges
    )
    if already:
        real_he_id = he_id
    else:
        # UMA chamada — REUSE puro da primitiva F2.1, zero reimplementação de star.
        real_he_id = graph.add_hyperedge(
            participants=ids,
            rel_label=rel_label,
            t_start=[date] if date else None,
            atomic_facts=facts or None,
            metadata=metadata,  # RNF-G1: lands on the EDGE via add_hyperedge merge
        )
    report["he_id"] = real_he_id

    # Durable overlay (constraint R1) — survives rebuild.py:97-98 overwrite.
    write_overlay_entry(
        _overlay_entry(
            he_id=real_he_id,
            participants=ids,
            participant_labels=labels,
            rel_label=rel_label,
            t_start=[date] if date else [],
            atomic_facts=facts,
            metadata=metadata,
        ),
        overlay_path,
    )

    # Apply on the live graph too (the overlay re-applies it on the NEXT rebuild).
    graph.save(graph_path)

    member_edges = [
        e for e in graph.edges if e.source == real_he_id and e.rel_type == "PARTICIPA"
    ]
    report["member_edges"] = len(member_edges)
    report["hyperedge_nodes"] = sum(
        1 for e in graph.entities.values() if e.type == "hyperedge"
    )
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize a call transcript into ONE living hyperedge."
    )
    parser.add_argument("--call", required=True, help="path to the call .txt transcript")
    parser.add_argument(
        "--rel-label", default="meeting", help="relation label (default: meeting)"
    )
    parser.add_argument(
        "--exclude-bots",
        action="store_true",
        default=True,
        help="drop bot participants (Fireflies dropped unconditionally; default on)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the plan (N person nodes + 1 hyperedge) WITHOUT mutating the graph",
    )
    args = parser.parse_args(argv)

    call_path = Path(args.call)
    if not call_path.exists():
        print(f"[hyperedge_materializer] call not found: {call_path}", file=sys.stderr)
        return 1

    report = materialize_call(
        call_path,
        rel_label=args.rel_label,
        exclude_bots=args.exclude_bots,
        dry_run=args.dry_run,
    )

    tag = "DRY-RUN" if report["dry_run"] else "MATERIALIZED"
    print(f"[hyperedge_materializer] {tag} — {report['meet_id']}")
    print(f"  rel_label     : {report['rel_label']}")
    print(f"  participants  : {report['participant_count']}")
    for pid in report["participants"]:
        print(f"    - {pid}")
    print(f"  hyperedge id  : {report['he_id']}")
    print(f"  t_start       : {report['t_start']}")
    print(f"  atomic_facts  : {len(report['atomic_facts'])}")
    if not report["dry_run"]:
        print(f"  member edges  : {report.get('member_edges')} (PARTICIPA)")
        print(f"  hyperedge nodes (live graph): {report.get('hyperedge_nodes')}")
        print(f"  overlay       : {OVERLAY_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
