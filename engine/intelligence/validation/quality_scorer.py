"""Numeric quality scoring for Mega Brain pipeline outputs.

Scores content on 4 dimensions (0-25 each, total 0-100):
- Coverage: How much of the expected content is present
- Clarity: How clear and well-structured the content is
- Completeness: Whether all required sections exist
- Traceability: Whether sources are properly cited
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class QualityScore:
    """Quality score for a single content item."""

    item_id: str  # batch ID, agent ID, or file path
    item_type: str  # "batch", "agent", "playbook", "dossier"
    coverage: int  # 0-25
    clarity: int  # 0-25
    completeness: int  # 0-25
    traceability: int  # 0-25
    total: int  # 0-100 (sum of dimensions)
    grade: str  # A (90+), B (70-89), C (50-69), D (30-49), F (<30)
    timestamp: str
    details: dict  # dimension-specific notes


def _grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    if score >= 70:
        return "B"
    if score >= 50:
        return "C"
    if score >= 30:
        return "D"
    return "F"


def score_batch(batch_path: str | Path, batch_id: str | None = None) -> QualityScore:
    """Score a pipeline batch output.

    Evaluates the batch file on 4 dimensions:
    - Coverage: Checks for required sections (DNA elements, insights, references)
    - Clarity: Checks structure (headers, formatting, no garbled text)
    - Completeness: Checks all expected sections present
    - Traceability: Checks source citations (^[FONTE] markers)
    """
    batch_path = Path(batch_path)
    if not batch_path.exists():
        raise FileNotFoundError(f"Batch not found: {batch_path}")

    text = batch_path.read_text(encoding="utf-8")
    item_id = batch_id or batch_path.stem
    details: dict[str, str] = {}

    # Coverage (0-25): Check for DNA layer mentions
    dna_layers = ["PHILOSOPHIES", "MENTAL", "HEURISTICS", "FRAMEWORKS", "METHODOLOGIES"]
    layers_found = sum(1 for layer in dna_layers if layer.upper() in text.upper())
    coverage = min(25, int(layers_found / len(dna_layers) * 25))
    details["coverage"] = f"{layers_found}/{len(dna_layers)} DNA layers referenced"

    # Clarity (0-25): Check structure markers
    has_headers = text.count("#") >= 3
    has_sections = text.count("---") >= 2 or text.count("###") >= 2
    has_lists = text.count("- ") >= 5 or text.count("* ") >= 5
    line_count = len(text.splitlines())
    reasonable_length = 50 <= line_count <= 5000
    clarity_items = sum([has_headers, has_sections, has_lists, reasonable_length])
    clarity = min(25, int(clarity_items / 4 * 25))
    details["clarity"] = (
        f"headers={has_headers}, sections={has_sections}, lists={has_lists}, length={line_count}"
    )

    # Completeness (0-25): Check expected sections
    expected_markers = ["CONTEXTO", "DESTINO", "ARQUIVO", "BATCH", "FONTE"]
    markers_found = sum(1 for m in expected_markers if m.upper() in text.upper())
    completeness = min(25, int(markers_found / len(expected_markers) * 25))
    details["completeness"] = f"{markers_found}/{len(expected_markers)} expected markers"

    # Traceability (0-25): Check source citations
    citation_count = text.count("^[") + text.count("[FONTE")
    if citation_count >= 10:
        traceability = 25
    elif citation_count >= 5:
        traceability = 20
    elif citation_count >= 2:
        traceability = 15
    elif citation_count >= 1:
        traceability = 10
    else:
        traceability = 0
    details["traceability"] = f"{citation_count} citations found"

    total = coverage + clarity + completeness + traceability

    return QualityScore(
        item_id=item_id,
        item_type="batch",
        coverage=coverage,
        clarity=clarity,
        completeness=completeness,
        traceability=traceability,
        total=total,
        grade=_grade(total),
        timestamp=datetime.now(UTC).isoformat(),
        details=details,
    )


def score_agent(agent_dir: str | Path) -> QualityScore:
    """Score an agent's file completeness.

    Checks:
    - Coverage: Required files exist (AGENT.md, SOUL.md, MEMORY.md, DNA-CONFIG.yaml)
    - Clarity: AGENT.md has proper structure
    - Completeness: All 11 template parts present in AGENT.md
    - Traceability: ^[FONTE] citations in SOUL.md and MEMORY.md
    """
    agent_dir = Path(agent_dir)
    if not agent_dir.is_dir():
        raise NotADirectoryError(f"Agent directory not found: {agent_dir}")

    details: dict[str, str] = {}

    # Coverage: Required files
    required = ["AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml"]
    files_found = sum(1 for f in required if (agent_dir / f).exists())
    coverage = min(25, int(files_found / len(required) * 25))
    details["coverage"] = f"{files_found}/{len(required)} required files"

    # Clarity: AGENT.md structure
    agent_md = agent_dir / "AGENT.md"
    if agent_md.exists():
        text = agent_md.read_text(encoding="utf-8")
        has_ascii = "\u2554" in text or "\u250c" in text
        has_headers = text.count("##") >= 5
        has_parts = "PARTE" in text.upper() or "PART" in text.upper()
        clarity = min(25, sum([has_ascii, has_headers, has_parts]) * 8)
        details["clarity"] = f"ascii={has_ascii}, headers={has_headers}, parts={has_parts}"
    else:
        clarity = 0
        details["clarity"] = "AGENT.md missing"

    # Completeness: Template V3 parts
    if agent_md.exists():
        text = agent_md.read_text(encoding="utf-8")
        v3_parts = [
            "COMPOSICAO",
            "IDENTIDADE",
            "NEURAL",
            "OPERACIONAL",
            "VOZ",
            "DECISAO",
            "CONEXAO",
            "DEBATE",
            "MEMORIA",
            "EXPANSAO",
        ]
        parts_found = sum(1 for p in v3_parts if p.upper() in text.upper())
        completeness = min(25, int(parts_found / len(v3_parts) * 25))
        details["completeness"] = f"{parts_found}/{len(v3_parts)} V3 template parts"
    else:
        completeness = 0
        details["completeness"] = "AGENT.md missing"

    # Traceability: Citations in SOUL + MEMORY
    citation_count = 0
    for fname in ["SOUL.md", "MEMORY.md"]:
        fpath = agent_dir / fname
        if fpath.exists():
            text = fpath.read_text(encoding="utf-8")
            citation_count += text.count("^[") + text.count("[FONTE")
    traceability = min(25, citation_count * 2)
    details["traceability"] = f"{citation_count} citations in SOUL+MEMORY"

    total = coverage + clarity + completeness + traceability

    return QualityScore(
        item_id=agent_dir.name,
        item_type="agent",
        coverage=coverage,
        clarity=clarity,
        completeness=completeness,
        traceability=traceability,
        total=total,
        grade=_grade(total),
        timestamp=datetime.now(UTC).isoformat(),
        details=details,
    )


def persist_score(score: QualityScore, scores_file: str | Path | None = None) -> None:
    """Append score to JSONL file for trend tracking."""
    if scores_file is None:
        scores_file = Path(".data/quality_scores.jsonl")
    scores_file = Path(scores_file)
    scores_file.parent.mkdir(parents=True, exist_ok=True)

    with open(scores_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(score), ensure_ascii=False) + "\n")


def load_scores(scores_file: str | Path | None = None) -> list[QualityScore]:
    """Load all historical scores from JSONL file."""
    if scores_file is None:
        scores_file = Path(".data/quality_scores.jsonl")
    scores_file = Path(scores_file)

    if not scores_file.exists():
        return []

    scores: list[QualityScore] = []
    for line in scores_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            data = json.loads(line)
            scores.append(QualityScore(**data))
    return scores


def get_trend(item_id: str, scores_file: str | Path | None = None) -> list[int]:
    """Get score trend for a specific item over time."""
    all_scores = load_scores(scores_file)
    return [s.total for s in all_scores if s.item_id == item_id]
