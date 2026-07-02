"""Ground Truth Generator for RAGAS evaluation.

Generates (query, expected_chunk_ids) pairs from HEURISTICAS.yaml files.
Used by ragas_evaluator.py to compute IDBasedContextPrecision baseline.

Story: STORY-RAG-9 (S9) — Phase 2 Wave 5
Date: 2026-04-12

Output: .data/ragas/ground_truth_200.jsonl
Format per line: {"query": str, "expected_chunk_ids": [str, ...], "person": str, "heuristic_id": str}

Strategy:
  - Read heuristicas.yaml for all persons in knowledge/external/dna/persons/
  - Each heuristic with source_chunks → generate a question from name/description
  - Filter to confidence >= 0.80 for quality
  - Target: 200 pairs (all available if < 200)
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DNA_BASE = Path(__file__).resolve().parents[3] / "knowledge" / "external" / "dna" / "persons"
MIN_CONFIDENCE = 0.70  # Default: include HIGH + MEDIUM confidence entries
TARGET_PAIRS = 200  # Aspirational; limited by entries with source_chunks in DNA


# ---------------------------------------------------------------------------
# QUERY GENERATION
# ---------------------------------------------------------------------------
def _heuristic_to_query(heuristic: dict) -> str:
    """Generate a natural language question from a heuristic entry."""
    name = heuristic.get("name", "")
    description = heuristic.get("description", "")

    # Use the name as a question anchor
    name_clean = name.rstrip(".").strip()

    # Generate question based on content type
    if "%" in name or any(c.isdigit() for c in name[:20]):
        return f"What is the specific metric or threshold for: {name_clean}?"
    if ":" in name:
        concept = name.split(":")[0].strip()
        return f"Explain the {concept} strategy and how it works."
    if description and len(description) > len(name):
        # Use description to form question
        words = description.split()[:8]
        return f"How does '{' '.join(words[:5])}' work in practice?"

    return f"What is the principle behind: {name_clean}?"


# ---------------------------------------------------------------------------
# GENERATOR
# ---------------------------------------------------------------------------
def generate_pairs(
    min_confidence: float = MIN_CONFIDENCE,
    target: int = TARGET_PAIRS,
) -> list[dict]:
    """Generate ground truth pairs from all HEURISTICAS.yaml files.

    Returns:
        List of dicts: {"query", "expected_chunk_ids", "person", "heuristic_id"}
    """
    pairs: list[dict] = []

    if not DNA_BASE.exists():
        return pairs

    for person_dir in sorted(DNA_BASE.iterdir()):
        if not person_dir.is_dir() or person_dir.name.startswith(("_", ".")):
            continue
        if len(pairs) >= target:
            break

        # Include all DNA layers with source_chunks, prioritizing heuristicas
        yaml_files = sorted(
            person_dir.glob("*.yaml"),
            key=lambda p: (
                0
                if p.name == "heuristicas.yaml"
                else 1
                if p.name == "frameworks.yaml"
                else 2
                if p.name == "metodologias.yaml"
                else 3
            ),
        )

        for yaml_path in yaml_files:
            if yaml_path.name == "CONFIG.yaml":
                continue
            if len(pairs) >= target:
                break

            try:
                with open(yaml_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except Exception:
                continue

            if not isinstance(data, dict):
                continue

            person = data.get("person", person_dir.name)
            entries = data.get("entries", [])

            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                # Quality filter — confidence can be float or "HIGH"/"MEDIUM"/"LOW"
                raw_conf = entry.get("confidence", entry.get("priority", 0.0))
                _cmap = {"HIGH": 0.90, "MEDIUM": 0.70, "LOW": 0.50}
                if isinstance(raw_conf, str):
                    confidence = _cmap.get(raw_conf.upper(), 0.70)
                else:
                    try:
                        confidence = float(raw_conf)
                    except (TypeError, ValueError):
                        confidence = 0.70
                if confidence < min_confidence:
                    continue

                # Must have source_chunks for ground truth
                source_chunks = entry.get("source_chunks", [])
                if not source_chunks:
                    continue

                heuristic_id = entry.get("id", "")
                query = _heuristic_to_query(entry)

                pairs.append(
                    {
                        "query": query,
                        "expected_chunk_ids": [str(c) for c in source_chunks],
                        "person": person,
                        "layer": yaml_path.stem,
                        "heuristic_id": heuristic_id,
                        "confidence": confidence,
                        "heuristic_name": entry.get("name", ""),
                    }
                )

                if len(pairs) >= target:
                    break

    return pairs[:target]


def save_pairs(pairs: list[dict], output_path: Path | None = None) -> Path:
    """Save ground truth pairs to JSONL file."""
    if output_path is None:
        root = Path(__file__).resolve().parents[3]
        ragas_dir = root / ".data" / "ragas"
        ragas_dir.mkdir(parents=True, exist_ok=True)
        output_path = ragas_dir / "ground_truth_200.jsonl"

    with open(output_path, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    return output_path


def load_pairs(path: Path | None = None) -> list[dict]:
    """Load ground truth pairs from JSONL."""
    if path is None:
        root = Path(__file__).resolve().parents[3]
        path = root / ".data" / "ragas" / "ground_truth_200.jsonl"
    if not path.exists():
        return []
    pairs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    pairs.append(json.loads(line))
                except Exception:
                    continue
    return pairs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    print("Generating ground truth pairs from HEURISTICAS.yaml...")
    pairs = generate_pairs()
    if not pairs:
        print("No pairs generated. Check knowledge/external/dna/persons/ exists.")
        return

    out = save_pairs(pairs)
    print(f"Generated {len(pairs)} pairs → {out}")

    # Stats
    by_person: dict[str, int] = {}
    for p in pairs:
        by_person[p["person"]] = by_person.get(p["person"], 0) + 1
    print("\nBy person:")
    for person, count in sorted(by_person.items(), key=lambda x: -x[1]):
        print(f"  {person}: {count}")


if __name__ == "__main__":
    main()
