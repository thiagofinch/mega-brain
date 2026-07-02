#!/usr/bin/env python3
"""
rag_post_rebuild_validator.py -- Post-rebuild RAG integrity gate

Runs after modifications to .data/rag_*/ files or rebuild commands. Validates:
1. chunks.json and vectors.json are aligned (same count)
2. Embedding dim declared in metadata matches actual vector dim
3. Orphan rate (chunks pointing to non-existent source_file) < 5%

BLOCK (exit 2) on critical regressions.
Created: 2026-04-24 Wave 5 completion -- DECISION-F1 compliance enforcement.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def _load_event() -> dict:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}

    if not raw.strip():
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def main() -> int:
    event = _load_event()
    tool_input = event.get("tool_input", {})
    target = tool_input.get("file_path", "") or tool_input.get("command", "")

    if ".data/rag_" not in target and "rebuild" not in target:
        return 0

    problems: list[str] = []

    for bucket_dir in ("rag_business", "rag_index"):
        bucket_path = BASE_DIR / ".data" / bucket_dir
        if not bucket_path.exists():
            continue

        chunks_path = bucket_path / "chunks.json"
        vectors_path = bucket_path / "vectors.json"
        if not chunks_path.exists() or not vectors_path.exists():
            continue

        try:
            with chunks_path.open(encoding="utf-8") as handle:
                chunks = json.load(handle)
            with vectors_path.open(encoding="utf-8") as handle:
                vec_data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{bucket_dir}: cannot parse ({exc})")
            continue

        if not isinstance(chunks, list) or not isinstance(vec_data, dict):
            problems.append(f"{bucket_dir}: invalid file structure")
            continue

        vectors = vec_data.get("vectors", [])
        declared_dim = vec_data.get("dim")

        n_chunks = len(chunks)
        n_vectors = len(vectors) if isinstance(vectors, list) else 0

        if n_chunks != n_vectors and n_vectors > 0:
            problems.append(f"{bucket_dir}: chunks={n_chunks} != vectors={n_vectors}")

        if n_vectors > 0 and isinstance(vectors[0], list):
            actual_dim = len(vectors[0])
            if actual_dim != declared_dim:
                problems.append(f"{bucket_dir}: declared dim={declared_dim} != actual={actual_dim}")

        sample = chunks[:50] if len(chunks) > 50 else chunks
        missing = 0
        for chunk in sample:
            if not isinstance(chunk, dict):
                continue
            source_file = chunk.get("source_file", "")
            if source_file and not (BASE_DIR / source_file).exists():
                missing += 1

        if sample:
            orphan_rate = missing / len(sample)
            if orphan_rate > 0.05:
                problems.append(
                    f"{bucket_dir}: sample orphan rate {orphan_rate:.1%} > 5% (run rebuild --full)"
                )

    if problems:
        print("=== RAG POST-REBUILD VALIDATOR: FAIL ===", file=sys.stderr)
        for problem in problems:
            print(f"  x {problem}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
