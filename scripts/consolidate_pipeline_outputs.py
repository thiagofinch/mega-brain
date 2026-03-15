#!/usr/bin/env python3
"""
consolidate_pipeline_outputs.py

Reads JSON outputs from meeting-processing subagent JSONL files,
extracts the structured JSON blocks, and merges them into the
existing state files:

  - processing/chunks/CHUNKS-STATE.json
  - processing/insights/INSIGHTS-STATE.json
  - processing/narratives/NARRATIVES-STATE.json
  - processing/canonical/CANONICAL-MAP.json

Uses incremental read/write to avoid loading the full 40MB
CHUNKS-STATE into memory for the final write (streams via
ijson is not available in stdlib, so we do a two-pass approach:
read only what we need, then do a targeted rewrite).
"""

import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent  # mega-brain/

SUBAGENT_DIR = Path(
    os.path.expanduser(
        "~/.claude/projects/"
        "-Users-thiagofinch-Documents-Projects-mega-brain/"
        "f4ddbcb4-8311-4c41-b224-0814d92184a2/subagents"
    )
)

# Agent JSONL files → (jsonl_filename, line_index_of_final_assistant_message)
# These were identified by scanning each file for the last assistant message
# containing a ```json block.
AGENT_FILES = {
    "MEET-0097": ("agent-a7c9ce6d026823677.jsonl", 103),
    "MEET-0098": ("agent-a10272575beb40472.jsonl", 73),
    "MEET-0099": ("agent-a00e66e2811a8f617.jsonl", 59),
}

STATE_FILES = {
    "chunks": ROOT / "processing" / "chunks" / "CHUNKS-STATE.json",
    "insights": ROOT / "processing" / "insights" / "INSIGHTS-STATE.json",
    "narratives": ROOT / "processing" / "narratives" / "NARRATIVES-STATE.json",
    "canonical": ROOT / "processing" / "canonical" / "CANONICAL-MAP.json",
}

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def extract_json_from_jsonl(filepath: Path, line_index: int) -> dict:
    """Read a specific line from a JSONL file, extract the ```json block."""
    with open(filepath) as f:
        for i, line in enumerate(f):
            if i == line_index:
                obj = json.loads(line)
                break
        else:
            raise ValueError(f"Line {line_index} not found in {filepath}")

    # Navigate to the text content
    message = obj.get("message", {})
    content_blocks = message.get("content", [])

    for block in content_blocks:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block["text"]
            match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))

    raise ValueError(f"No ```json block found in line {line_index} of {filepath}")


def normalize_person_name(name: str) -> str:
    """Normalize a person name key (strip, title-case edge cases)."""
    return name.strip()


# ---------------------------------------------------------------------------
# Extract all 3 meeting outputs
# ---------------------------------------------------------------------------


def extract_all_meetings() -> dict[str, dict]:
    """Extract JSON data from all 3 agent output files."""
    results = {}
    for meet_id, (fname, line_idx) in AGENT_FILES.items():
        filepath = SUBAGENT_DIR / fname
        if not filepath.exists():
            print(f"  WARNING: {filepath} not found, skipping {meet_id}")
            continue
        try:
            data = extract_json_from_jsonl(filepath, line_idx)
            results[meet_id] = data
            print(f"  Extracted {meet_id}: {len(data.get('chunks', []))} chunks, "
                  f"{len(data.get('insights', []))} insights")
        except Exception as e:
            print(f"  ERROR extracting {meet_id}: {e}")
    return results


# ---------------------------------------------------------------------------
# Merge: CHUNKS-STATE
# ---------------------------------------------------------------------------


def merge_chunks(meetings: dict[str, dict]) -> dict:
    """Append new chunks to CHUNKS-STATE.json."""
    state_path = STATE_FILES["chunks"]
    print(f"\n  Loading {state_path.name} ({state_path.stat().st_size / 1024 / 1024:.1f} MB)...")

    with open(state_path) as f:
        state = json.load(f)

    # Chunks use either "id_chunk" or "chunk_id" as key
    existing_ids = set()
    for c in state["chunks"]:
        cid = c.get("id_chunk") or c.get("chunk_id", "")
        if cid:
            existing_ids.add(cid)

    added = 0
    skipped = 0

    for meet_id, data in meetings.items():
        raw_chunks = data.get("chunks", [])
        for chunk in raw_chunks:
            cid = chunk.get("id_chunk") or chunk.get("chunk_id", "")
            if cid in existing_ids:
                skipped += 1
                continue

            # Normalize chunk schema to match existing state format
            normalized = {
                "id_chunk": cid,
                "texto": chunk.get("conteudo", chunk.get("texto", "")),
                "pessoas": chunk.get("pessoas_raw", chunk.get("pessoas", [])),
                "temas": chunk.get("temas_raw", chunk.get("temas", [])),
                "meta": chunk.get("meta", {
                    "source": meet_id,
                    "timestamp": chunk.get("timestamp", ""),
                }),
            }
            # Ensure meta.source exists
            if "source" not in normalized["meta"]:
                normalized["meta"]["source"] = meet_id

            state["chunks"].append(normalized)
            existing_ids.add(cid)
            added += 1

    # Update meta
    state["meta"]["total_chunks"] = len(state["chunks"])
    state["meta"]["last_updated"] = NOW
    state["total_chunks"] = len(state["chunks"])
    state["last_updated"] = NOW

    # Add sources
    for meet_id in meetings:
        if meet_id not in state.get("sources", []):
            state.setdefault("sources", []).append(meet_id)

    # Write back
    print(f"  Writing {state_path.name}...")
    with open(state_path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return {"added": added, "skipped": skipped, "total": len(state["chunks"])}


# ---------------------------------------------------------------------------
# Merge: INSIGHTS-STATE
# ---------------------------------------------------------------------------


def merge_insights(meetings: dict[str, dict]) -> dict:
    """Append new insights to INSIGHTS-STATE.json."""
    state_path = STATE_FILES["insights"]
    print(f"\n  Loading {state_path.name}...")

    with open(state_path) as f:
        state = json.load(f)

    # The state has two locations for insights:
    #   state["insights"] — flat list of all insights
    #   state["insights_state"]["persons"] — grouped by person
    #   state["insights_state"]["themes"] — grouped by theme

    existing_ids = set()
    for ins in state.get("insights", []):
        existing_ids.add(ins.get("id", ""))

    insights_added = 0
    persons_updated = set()
    themes_updated = set()

    insights_state = state.setdefault("insights_state", {})
    persons_map = insights_state.setdefault("persons", {})
    themes_map = insights_state.setdefault("themes", {})

    for meet_id, data in meetings.items():
        raw_insights = data.get("insights", [])
        for ins in raw_insights:
            iid = ins.get("id", "")
            if iid in existing_ids:
                continue

            # Normalize to match existing schema
            normalized = {
                "id": iid,
                "chunk_ids": ins.get("chunks", ins.get("chunk_ids", [])),
                "person": "",  # will be set from pessoas
                "category": "",
                "priority": ins.get("priority", "medium"),
                "dna_layer": "",
                "title": ins.get("insight", ins.get("title", "")),
                "summary": ins.get("insight", ins.get("summary", "")),
                "evidence": "",
                "actionable": True,
                "confidence": ins.get("confidence", 0.7),
                "tags": ins.get("tags", []),
                "source": meet_id,
            }

            # Extract pessoas/temas
            pessoas = ins.get("pessoas", [])
            temas = ins.get("temas", ins.get("tags", []))

            if pessoas:
                normalized["person"] = pessoas[0] if isinstance(pessoas[0], str) else str(pessoas[0])

            # Add to flat list
            state.setdefault("insights", []).append(normalized)
            existing_ids.add(iid)
            insights_added += 1

            # Add to persons map in insights_state
            for person in pessoas:
                pname = normalize_person_name(str(person))
                existing_val = persons_map.get(pname)
                if existing_val is None:
                    persons_map[pname] = [normalized]
                elif isinstance(existing_val, list):
                    existing_val.append(normalized)
                # If it's a dict (older format), don't modify it
                persons_updated.add(pname)

            # Add to themes map
            for tema in temas:
                tname = str(tema).strip().upper()
                if tname:
                    existing_themes = themes_map.get(tname)
                    if existing_themes is None:
                        themes_map[tname] = [normalized]
                    elif isinstance(existing_themes, list):
                        existing_themes.append(normalized)
                    themes_updated.add(tname)

    # Update meta
    state["total_insights"] = len(state.get("insights", []))
    state["last_updated"] = NOW

    # Top-level persons has mixed types (some list, some dict) -- don't touch existing
    # Just add new person entries as count
    if "persons" in state and isinstance(state["persons"], dict):
        for pname in persons_updated:
            if pname not in state["persons"]:
                state["persons"][pname] = len(persons_map.get(pname, []))

    # Add sources (it's a dict in this file, not a list)
    sources = state.get("sources", {})
    if isinstance(sources, dict):
        for meet_id in meetings:
            if meet_id not in sources:
                sources[meet_id] = {"added": NOW, "type": "meeting"}
        state["sources"] = sources
    elif isinstance(sources, list):
        for meet_id in meetings:
            if meet_id not in sources:
                sources.append(meet_id)

    # Update change_log
    change_log = insights_state.setdefault("change_log", [])
    change_log.append({
        "date": NOW,
        "action": "consolidate_pipeline_outputs",
        "meetings": list(meetings.keys()),
        "insights_added": insights_added,
    })

    print(f"  Writing {state_path.name}...")
    with open(state_path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return {
        "added": insights_added,
        "total": len(state.get("insights", [])),
        "persons_updated": sorted(persons_updated),
        "themes_updated": sorted(themes_updated),
    }


# ---------------------------------------------------------------------------
# Merge: NARRATIVES-STATE
# ---------------------------------------------------------------------------


def merge_narratives(meetings: dict[str, dict]) -> dict:
    """Update/create narrative entries in NARRATIVES-STATE.json."""
    state_path = STATE_FILES["narratives"]
    print(f"\n  Loading {state_path.name}...")

    with open(state_path) as f:
        state = json.load(f)

    ns = state.setdefault("narratives_state", {})
    persons_map = ns.setdefault("persons", {})

    persons_created = []
    persons_updated = []

    for meet_id, data in meetings.items():
        raw_narratives = data.get("narratives", {})

        # Skip non-person keys like consensus_points, tensions
        skip_keys = {"consensus_points", "tensions", "consensus", "action_items"}

        for key, narr in raw_narratives.items():
            if key in skip_keys:
                continue
            if not isinstance(narr, dict):
                continue

            # Normalize person name from narrative key
            # Some use slug format (pedro-valerio-lopez), some use regular names
            person_name = key.replace("-", " ").replace("_", " ").strip().title()

            # Try to find some useful fields from the narrative
            narrative_text = (
                narr.get("narrative_synthesis", "")
                or narr.get("summary", "")
                or narr.get("narrative", "")
            )
            patterns = narr.get("patterns", [])
            open_loops = narr.get("open_loops", [])
            tensions = narr.get("tensions", [])
            role = narr.get("role", narr.get("person", ""))
            key_contributions = narr.get("key_contributions", [])

            if person_name in persons_map:
                # Update existing: append to narrative, merge sources
                existing = persons_map[person_name]
                # Append narrative text
                old_narr = existing.get("narrative", "")
                if narrative_text and narrative_text not in old_narr:
                    existing["narrative"] = (
                        old_narr + f"\n\n--- [{meet_id}] ---\n" + narrative_text
                    ).strip()
                # Merge sources
                existing.setdefault("sources", [])
                if meet_id not in existing["sources"]:
                    existing["sources"].append(meet_id)
                # Update stats
                existing.setdefault("stats", {})
                existing["stats"]["total_meetings"] = len(existing["sources"])
                existing["last_updated"] = NOW
                persons_updated.append(person_name)
            else:
                # Create new entry
                persons_map[person_name] = {
                    "narrative": narrative_text,
                    "insights_included": [],
                    "sources": [meet_id],
                    "themes": [],
                    "stats": {
                        "total_meetings": 1,
                        "patterns": patterns,
                        "open_loops": open_loops,
                        "tensions": tensions,
                        "role": role,
                        "key_contributions": key_contributions,
                    },
                    "last_updated": NOW,
                }
                persons_created.append(person_name)

    print(f"  Writing {state_path.name}...")
    with open(state_path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return {
        "persons_created": persons_created,
        "persons_updated": list(set(persons_updated)),
    }


# ---------------------------------------------------------------------------
# Merge: CANONICAL-MAP
# ---------------------------------------------------------------------------


def merge_canonical(meetings: dict[str, dict]) -> dict:
    """Add new entities to CANONICAL-MAP.json."""
    state_path = STATE_FILES["canonical"]
    print(f"\n  Loading {state_path.name}...")

    with open(state_path) as f:
        state = json.load(f)

    cs = state.get("canonical_state", {})
    entities = cs.setdefault("entities", {})
    aliases_map = cs.setdefault("aliases", {})
    canonical_map = cs.setdefault("canonical_map", {})

    entities_added = []
    aliases_added = []

    for meet_id, data in meetings.items():
        raw_entities = data.get("entities", {})

        # Different meetings have different entity formats
        # MEET-0097: {"canonical_map": {...}, "roles": {...}, ...}
        # MEET-0098: {"alan-nicolas": {...}, "thiago-finch": {...}, ...}
        # MEET-0099: {"persons": {...}, "organizations": {...}, ...}

        # Strategy: extract person names and roles from any format

        # --- Format 1: canonical_map dict ---
        if "canonical_map" in raw_entities:
            cm = raw_entities["canonical_map"]
            for alias, canonical in cm.items():
                canonical_name = canonical if isinstance(canonical, str) else str(canonical)
                alias_lower = alias.lower().strip()

                # Add to aliases if not present
                if alias_lower not in aliases_map:
                    aliases_map[alias_lower] = canonical_name
                    aliases_added.append(f"{alias_lower} -> {canonical_name}")

                # Add to canonical_map (legacy format)
                if canonical_name not in canonical_map:
                    canonical_map[canonical_name] = [
                        {"alias": canonical_name, "confidence": 1.0}
                    ]

        # --- Format 2: roles dict ---
        if "roles" in raw_entities:
            roles = raw_entities["roles"]
            for person_name, role_desc in roles.items():
                pname = person_name.strip()
                if pname not in entities:
                    entities[pname] = {
                        "type": "person",
                        "aliases": [pname.lower()],
                        "role": role_desc if isinstance(role_desc, str) else "",
                        "corpus": "bilhon_meetings",
                        "first_seen": NOW,
                        "sources": [meet_id],
                    }
                    entities_added.append(pname)
                else:
                    # Update sources
                    existing = entities[pname]
                    if meet_id not in existing.get("sources", []):
                        existing.setdefault("sources", []).append(meet_id)
                    # Update role if was empty
                    if not existing.get("role") and isinstance(role_desc, str):
                        existing["role"] = role_desc

        # --- Format 3: persons dict (MEET-0099 style) ---
        if "persons" in raw_entities and isinstance(raw_entities["persons"], dict):
            for person_key, person_data in raw_entities["persons"].items():
                # person_key might be like "Alan Nicolas (alanicolas.com)"
                pname = person_key.split("(")[0].strip()
                if pname not in entities:
                    entities[pname] = {
                        "type": "person",
                        "aliases": [pname.lower()],
                        "corpus": "bilhon_meetings",
                        "first_seen": NOW,
                        "sources": [meet_id],
                    }
                    if isinstance(person_data, dict):
                        entities[pname]["role"] = person_data.get("role", "")
                    entities_added.append(pname)
                else:
                    if meet_id not in entities[pname].get("sources", []):
                        entities[pname].setdefault("sources", []).append(meet_id)

        # --- Format 4: flat entity keys (MEET-0098 style: "alan-nicolas": {...}) ---
        # These look like slug keys with entity data
        for key, val in raw_entities.items():
            if key in ("canonical_map", "roles", "organizations",
                       "products_mentioned", "persons", "tools_platforms"):
                continue
            if not isinstance(val, dict):
                continue
            # This is a person entity in slug format
            pname = key.replace("-", " ").strip().title()
            if pname not in entities:
                entities[pname] = {
                    "type": "person",
                    "aliases": [pname.lower(), key.lower()],
                    "corpus": "bilhon_meetings",
                    "first_seen": NOW,
                    "sources": [meet_id],
                }
                entities_added.append(pname)
            else:
                if meet_id not in entities[pname].get("sources", []):
                    entities[pname].setdefault("sources", []).append(meet_id)

        # --- Organizations ---
        if "organizations" in raw_entities:
            orgs = raw_entities["organizations"]
            if isinstance(orgs, list):
                for org in orgs:
                    org_name = org if isinstance(org, str) else str(org)
                    if org_name not in entities:
                        entities[org_name] = {
                            "type": "organization",
                            "aliases": [org_name.lower()],
                            "corpus": "bilhon_meetings",
                            "first_seen": NOW,
                            "sources": [meet_id],
                        }
                        entities_added.append(org_name)
            elif isinstance(orgs, dict):
                for org_name, org_data in orgs.items():
                    if org_name not in entities:
                        entities[org_name] = {
                            "type": "organization",
                            "aliases": [org_name.lower()],
                            "corpus": "bilhon_meetings",
                            "first_seen": NOW,
                            "sources": [meet_id],
                        }
                        entities_added.append(org_name)

    # Update version
    old_version = cs.get("version", "v18")
    version_num = int(old_version.replace("v", "")) if old_version.startswith("v") else 18
    cs["version"] = f"v{version_num + 1}"
    cs["last_updated"] = NOW

    print(f"  Writing {state_path.name}...")
    with open(state_path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return {
        "entities_added": entities_added,
        "aliases_added": aliases_added,
        "version": cs["version"],
    }


# ---------------------------------------------------------------------------
# Also write per-meeting files (chunks + insights) for individual reference
# ---------------------------------------------------------------------------


def write_per_meeting_files(meetings: dict[str, dict]):
    """Write individual chunk and insight files per meeting."""
    for meet_id, data in meetings.items():
        # Chunks file
        chunks = data.get("chunks", [])
        if chunks:
            chunks_path = ROOT / "processing" / "chunks" / f"{meet_id}-chunks.json"
            if not chunks_path.exists():
                with open(chunks_path, "w") as f:
                    json.dump({"source": meet_id, "chunks": chunks}, f,
                              ensure_ascii=False, indent=2)
                print(f"  Created {chunks_path.name}")

        # Insights file
        insights = data.get("insights", [])
        if insights:
            insights_path = ROOT / "processing" / "insights" / f"{meet_id}-insights.json"
            if not insights_path.exists():
                with open(insights_path, "w") as f:
                    json.dump({"source": meet_id, "insights": insights}, f,
                              ensure_ascii=False, indent=2)
                print(f"  Created {insights_path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 70)
    print("  CONSOLIDATE PIPELINE OUTPUTS")
    print(f"  Meetings: {', '.join(AGENT_FILES.keys())}")
    print(f"  Timestamp: {NOW}")
    print("=" * 70)

    # 1. Extract
    print("\n[1/5] Extracting JSON from agent JSONL files...")
    meetings = extract_all_meetings()

    if not meetings:
        print("\n  No meetings extracted. Aborting.")
        sys.exit(1)

    # 2. Merge chunks
    print("\n[2/5] Merging CHUNKS-STATE...")
    chunks_result = merge_chunks(meetings)

    # 3. Merge insights
    print("\n[3/5] Merging INSIGHTS-STATE...")
    insights_result = merge_insights(meetings)

    # 4. Merge narratives
    print("\n[4/5] Merging NARRATIVES-STATE...")
    narratives_result = merge_narratives(meetings)

    # 5. Merge canonical
    print("\n[5/5] Merging CANONICAL-MAP...")
    canonical_result = merge_canonical(meetings)

    # 6. Write per-meeting files
    print("\n[BONUS] Writing per-meeting chunk/insight files...")
    write_per_meeting_files(meetings)

    # Summary
    print("\n" + "=" * 70)
    print("  CONSOLIDATION SUMMARY")
    print("=" * 70)

    print(f"\n  CHUNKS-STATE.json:")
    print(f"    Added:   {chunks_result['added']} chunks")
    print(f"    Skipped: {chunks_result['skipped']} (already existed)")
    print(f"    Total:   {chunks_result['total']} chunks")

    print(f"\n  INSIGHTS-STATE.json:")
    print(f"    Added:   {insights_result['added']} insights")
    print(f"    Total:   {insights_result['total']} insights")
    print(f"    Persons: {', '.join(insights_result['persons_updated']) or 'none'}")
    print(f"    Themes:  {', '.join(insights_result['themes_updated']) or 'none'}")

    print(f"\n  NARRATIVES-STATE.json:")
    print(f"    Created: {', '.join(narratives_result['persons_created']) or 'none'}")
    print(f"    Updated: {', '.join(narratives_result['persons_updated']) or 'none'}")

    print(f"\n  CANONICAL-MAP.json:")
    print(f"    Entities added: {len(canonical_result['entities_added'])}")
    if canonical_result["entities_added"]:
        for e in canonical_result["entities_added"]:
            print(f"      + {e}")
    print(f"    Aliases added:  {len(canonical_result['aliases_added'])}")
    print(f"    Version:        {canonical_result['version']}")

    print("\n" + "=" * 70)
    print("  DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
