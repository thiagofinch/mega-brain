#!/usr/bin/env python3
"""
SKILL GENERATOR - Intelligence Layer v1.0
==========================================
Converte frameworks extraidos do DNA em Skills executaveis (SKILL.md).

Pipeline: Framework DNA -> SKILL.md
Inspirado no NERO pipeline do MMOS (128+ skills de 11 personas).

Le DNA layers de personas, identifica frameworks/metodologias,
e converte cada um em SKILL.md executavel com workflow, evidencia, etc.

Dependencias: Sprint 4 completo (roles com weighted_score)
Inspiracao: MMOS NERO pipeline, formato SKILL.md do aios-core

Versao: 1.0.0
Data: 2026-02-26
"""

import json
import re
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import load_registry, save_registry, load_taxonomy

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
INSIGHTS_DIR = BASE_DIR / "processing" / "insights"
CHUNKS_DIR = BASE_DIR / "processing" / "chunks"
SKILLS_OUTPUT_DIR = BASE_DIR / "knowledge" / "dna" / "skills"
SKILLS_REGISTRY_PATH = BASE_DIR / "knowledge" / "dna" / "_dna-skills-registry.yaml"

# ---------------------------------------------------------------------------
# FRAMEWORK EXTRACTION PATTERNS
# ---------------------------------------------------------------------------

# Patterns that indicate a framework or methodology in text
FRAMEWORK_INDICATORS = [
    # Named frameworks (e.g., "The CLOSER Framework", "NEPQ Method")
    r"(?:the\s+)?([A-Z][A-Z0-9\s-]{2,30})\s+(?:framework|method|model|system|process|approach|formula|technique|estrategia|metodo|processo|sistema)",
    # Step-based patterns (e.g., "Step 1: ..., Step 2: ...")
    r"(?:step|passo|etapa|fase)\s+[1-9][\s:.-]+([^\n]{10,80})",
    # Numbered lists that look like methodology (3+ items)
    r"(\d+)\)\s+([^\n]{10,80})",
    # Acronym-based (e.g., "SPIN", "BANT", "MEDDIC")
    r"\b([A-Z]{3,8})\b\s+(?:stands\s+for|significa|is\s+an?\s+(?:acronym|framework|method))",
    # "Rule of" patterns
    r"(?:rule|regra|lei)\s+(?:of|de|do|da)\s+(\w+(?:\s+\w+){0,3})",
    # "X-Step" patterns (e.g., "7-Step Close", "3-Step Qualification")
    r"(\d+)[-\s](?:step|passo|etapa)\s+(\w+(?:\s+\w+){0,3})",
]

# Patterns for extracting steps within a framework
STEP_PATTERNS = [
    r"(?:step|passo|etapa)\s+(\d+)[\s:.-]+([^\n]+)",
    r"(\d+)[\)\.]\s+([^\n]+)",
    r"(?:first|second|third|fourth|fifth|primeiro|segundo|terceiro|quarto|quinto)[\s:,]+([^\n]+)",
]

# Skill type classification
SKILL_TYPE_KEYWORDS = {
    "sequential": ["step", "passo", "etapa", "first", "then", "next", "depois", "apos"],
    "parallel": ["simultaneously", "at the same time", "while", "ao mesmo tempo", "enquanto"],
    "reference": ["guide", "reference", "checklist", "template", "guia", "referencia"],
}


# ---------------------------------------------------------------------------
# CORE: EXTRACT FRAMEWORKS
# ---------------------------------------------------------------------------
def extract_frameworks_from_text(text, source_id=None, persona=None):
    """
    Extract framework/methodology patterns from text.

    Returns list of framework dicts with name, steps, evidence, etc.
    """
    frameworks = []
    text_lower = text.lower()

    # 1. Find named frameworks
    for pattern in FRAMEWORK_INDICATORS[:3]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name = match.group(1).strip() if match.group(1) else ""
            if name and len(name) > 3 and not _is_noise(name):
                ctx_start = max(0, match.start() - 200)
                ctx_end = min(len(text), match.end() + 500)
                context = text[ctx_start:ctx_end]

                steps = _extract_steps_from_context(context)
                fw = {
                    "name": _clean_framework_name(name),
                    "raw_name": name,
                    "steps": steps,
                    "step_count": len(steps),
                    "source_id": source_id,
                    "persona": persona,
                    "evidence": context[:300].strip(),
                    "layer": _classify_layer(context),
                }
                if not _is_duplicate_framework(fw, frameworks):
                    frameworks.append(fw)

    # 2. Find step-sequence frameworks (unnamed but structured)
    step_sequences = _find_step_sequences(text)
    for seq in step_sequences:
        if seq["step_count"] >= 3:
            name = _infer_framework_name(seq["steps"], text)
            fw = {
                "name": name,
                "raw_name": f"Unnamed {seq['step_count']}-step process",
                "steps": seq["steps"],
                "step_count": seq["step_count"],
                "source_id": source_id,
                "persona": persona,
                "evidence": seq.get("context", "")[:300].strip(),
                "layer": _classify_layer(seq.get("context", "")),
            }
            if not _is_duplicate_framework(fw, frameworks):
                frameworks.append(fw)

    # 3. Find acronym-based frameworks
    for pattern in FRAMEWORK_INDICATORS[3:4]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            acronym = match.group(1).strip()
            if len(acronym) >= 3 and not _is_noise(acronym):
                ctx_start = max(0, match.start() - 100)
                ctx_end = min(len(text), match.end() + 300)
                context = text[ctx_start:ctx_end]
                fw = {
                    "name": acronym,
                    "raw_name": acronym,
                    "steps": [],
                    "step_count": 0,
                    "source_id": source_id,
                    "persona": persona,
                    "evidence": context[:300].strip(),
                    "layer": "L3",  # Acronyms are usually mental models
                }
                if not _is_duplicate_framework(fw, frameworks):
                    frameworks.append(fw)

    return frameworks


def extract_frameworks_from_file(filepath):
    """Extract frameworks from a chunk file."""
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_id = data.get("source_id", data.get("source_hash", filepath.stem))
    persona = _detect_persona(source_id, data)

    chunks = data.get("chunks", [data])
    all_frameworks = []

    for chunk in chunks:
        text = chunk.get("content", "") or chunk.get("texto", "") or chunk.get("text", "")
        if not text:
            continue
        frameworks = extract_frameworks_from_text(text, source_id=source_id, persona=persona)
        all_frameworks.extend(frameworks)

    return {
        "source_id": source_id,
        "persona": persona,
        "frameworks_found": len(all_frameworks),
        "frameworks": all_frameworks,
    }


def scan_all_and_generate(registry=None, save=True):
    """Scan all chunks, extract frameworks, generate SKILL.md files."""
    if registry is None:
        registry = load_registry()

    # Phase 1: Extract all frameworks
    persona_frameworks = defaultdict(list)
    files_scanned = 0

    for fpath in sorted(CHUNKS_DIR.glob("*.json")):
        if fpath.name in ("CHUNKS-STATE.json", "_INDEX.json", "_rag_export.json"):
            continue

        result = extract_frameworks_from_file(fpath)
        files_scanned += 1

        persona = result["persona"] or "unknown"
        persona_frameworks[persona].extend(result["frameworks"])

    # Phase 2: Deduplicate frameworks per persona
    for persona in persona_frameworks:
        persona_frameworks[persona] = _deduplicate_frameworks(persona_frameworks[persona])

    # Phase 3: Generate SKILL.md for each framework
    total_skills = 0
    skills_registry = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_skills": 0,
        "personas": {},
    }

    for persona, frameworks in persona_frameworks.items():
        persona_slug = _slugify(persona)
        persona_skills = []

        for fw in frameworks:
            if fw["step_count"] < 2 and not fw["name"]:
                continue  # Skip frameworks without enough structure

            skill_id = f"dna-{persona_slug}-{_slugify(fw['name'])}"
            skill_type = _classify_skill_type(fw)

            skill = {
                "skill_id": skill_id,
                "source_persona": persona,
                "source_layer": fw.get("layer", "L3"),
                "name": fw["name"],
                "type": skill_type,
                "workflow_steps": fw["steps"],
                "step_count": fw["step_count"],
                "evidence": fw.get("evidence", ""),
                "source_id": fw.get("source_id", ""),
            }

            if save:
                _save_skill_md(persona_slug, skill)

            persona_skills.append(skill)
            total_skills += 1

        skills_registry["personas"][persona_slug] = {
            "skills_count": len(persona_skills),
            "skills": [s["skill_id"] for s in persona_skills],
        }

    skills_registry["total_skills"] = total_skills

    if save:
        _save_skills_registry(skills_registry)

    return {
        "files_scanned": files_scanned,
        "personas_found": len(persona_frameworks),
        "total_frameworks": sum(len(v) for v in persona_frameworks.values()),
        "total_skills_generated": total_skills,
        "per_persona": {
            k: len(v) for k, v in persona_frameworks.items()
        },
    }


# ---------------------------------------------------------------------------
# SKILL MD GENERATION
# ---------------------------------------------------------------------------
def _save_skill_md(persona_slug, skill):
    """Generate and save SKILL.md file."""
    skill_dir = SKILLS_OUTPUT_DIR / persona_slug
    skill_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{_slugify(skill['name'])}.md"
    filepath = skill_dir / filename

    lines = [
        f"# {skill['name']}",
        f"",
        f"> **Skill ID:** {skill['skill_id']}",
        f"> **Source:** DNA Layer {skill['source_layer']} - {skill['source_persona']}",
        f"> **Type:** {skill['type']}",
        f"> **Version:** 1.0.0 (auto-generated)",
        f"",
    ]

    # When to Use
    lines.extend([
        f"## Quando Usar",
        f"",
        f"Framework aplicavel quando o contexto envolve {skill['source_persona']} "
        f"e a situacao requer um processo estruturado de {skill['name'].lower()}.",
        f"",
    ])

    # When NOT to Use
    lines.extend([
        f"## Quando NAO Usar",
        f"",
        f"- Contexto nao relacionado ao dominio original",
        f"- Quando uma abordagem mais simples resolve",
        f"- Quando o framework conflita com outro framework ativo",
        f"",
    ])

    # Workflow
    lines.extend([
        f"## Workflow",
        f"",
    ])
    if skill["workflow_steps"]:
        for i, step in enumerate(skill["workflow_steps"], 1):
            lines.append(f"{i}. {step}")
    else:
        lines.append(f"_Framework detectado mas steps nao extraidos automaticamente. "
                      f"Consultar evidencia original._")
    lines.append("")

    # Output
    lines.extend([
        f"## Output Esperado",
        f"",
        f"Resultado estruturado seguindo os {skill['step_count']} passos do framework.",
        f"",
    ])

    # Evidence
    lines.extend([
        f"## Evidencia e Atribuicao",
        f"",
        f"**Source ID:** {skill['source_id']}",
        f"",
        f"```",
        f"{skill['evidence'][:500]}",
        f"```",
        f"",
        f"---",
        f"Auto-gerado por Mega Brain Intelligence Layer | {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
    ])

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _save_skills_registry(registry_data):
    """Save _dna-skills-registry.yaml."""
    SKILLS_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SKILLS_REGISTRY_PATH, "w", encoding="utf-8") as f:
        yaml.dump(registry_data, f, default_flow_style=False, allow_unicode=True)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _clean_framework_name(name):
    """Clean and normalize framework name."""
    name = re.sub(r"\s+", " ", name.strip())
    # Remove common noise words at start
    name = re.sub(r"^(?:the|a|an|o|a)\s+", "", name, flags=re.IGNORECASE)
    return name.title() if name else "Unnamed Framework"


def _classify_layer(context):
    """Classify which DNA layer a framework belongs to."""
    ctx_lower = context.lower()
    if any(kw in ctx_lower for kw in ["step", "passo", "process", "processo", "how to", "como"]):
        return "L3"  # Mental models / processes
    if any(kw in ctx_lower for kw in ["believe", "acredit", "philosophy", "filosofia", "mindset"]):
        return "L4"  # Values / beliefs
    if any(kw in ctx_lower for kw in ["always", "never", "rule", "regra", "principle", "principio"]):
        return "L4"  # Values / principles
    if any(kw in ctx_lower for kw in ["feel", "emotion", "intuition", "gut", "instinto"]):
        return "L2"  # Recognition patterns
    return "L3"  # Default to mental models


def _classify_skill_type(fw):
    """Classify skill as sequential, parallel, or reference."""
    text = " ".join(fw.get("steps", [])).lower() + " " + fw.get("evidence", "").lower()

    for skill_type, keywords in SKILL_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return skill_type

    if fw["step_count"] >= 3:
        return "sequential"
    return "reference"


def _extract_steps_from_context(context):
    """Extract numbered/sequential steps from context text."""
    steps = []
    for pattern in STEP_PATTERNS:
        matches = re.finditer(pattern, context, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            step_text = groups[-1].strip() if groups else ""
            if step_text and len(step_text) > 5 and not _is_noise(step_text):
                steps.append(step_text[:200])

    # Deduplicate while preserving order
    seen = set()
    unique_steps = []
    for s in steps:
        norm = s.lower()[:50]
        if norm not in seen:
            seen.add(norm)
            unique_steps.append(s)

    return unique_steps[:15]  # Cap at 15 steps


def _find_step_sequences(text):
    """Find sequences of numbered steps in text."""
    sequences = []
    lines = text.split("\n")

    current_steps = []
    current_start = 0

    for i, line in enumerate(lines):
        match = re.match(r"^\s*(\d+)[\)\.:\s]+(.{10,200})", line)
        if match:
            step_num = int(match.group(1))
            step_text = match.group(2).strip()

            if step_num == 1 or (current_steps and step_num == len(current_steps) + 1):
                if step_num == 1 and current_steps:
                    # Save previous sequence
                    if len(current_steps) >= 3:
                        ctx_start = max(0, current_start - 100)
                        ctx_end = min(len(text), i * 80)
                        sequences.append({
                            "steps": current_steps,
                            "step_count": len(current_steps),
                            "context": text[ctx_start:ctx_end][:500],
                        })
                    current_steps = []
                    current_start = i

                current_steps.append(step_text)
        else:
            if current_steps and len(current_steps) >= 3:
                ctx_start = max(0, current_start - 100)
                sequences.append({
                    "steps": current_steps,
                    "step_count": len(current_steps),
                    "context": "\n".join(lines[max(0, current_start - 2):i])[:500],
                })
            current_steps = []

    # Don't forget last sequence
    if current_steps and len(current_steps) >= 3:
        sequences.append({
            "steps": current_steps,
            "step_count": len(current_steps),
            "context": "\n".join(lines[-min(20, len(lines)):])[:500],
        })

    return sequences


def _infer_framework_name(steps, full_text):
    """Try to infer a name for an unnamed framework from its steps."""
    if not steps:
        return "Unnamed Process"

    # Look at the context right before the steps
    first_step = steps[0]
    idx = full_text.find(first_step)
    if idx > 20:
        before = full_text[max(0, idx - 200):idx].strip()
        # Look for a title/header before the steps
        lines = before.split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line and 5 < len(line) < 60 and not line[0].isdigit():
                return line.rstrip(":").strip().title()

    # Fallback: use verb from first step
    first_word = steps[0].split()[0] if steps[0] else "Process"
    return f"{first_word.title()} Framework ({len(steps)} Steps)"


def _is_duplicate_framework(new_fw, existing):
    """Check if framework is duplicate of an existing one."""
    new_name_lower = new_fw["name"].lower()
    for fw in existing:
        if fw["name"].lower() == new_name_lower:
            return True
        # Check if steps overlap significantly
        if fw["steps"] and new_fw["steps"]:
            overlap = len(set(s.lower()[:30] for s in fw["steps"]) &
                          set(s.lower()[:30] for s in new_fw["steps"]))
            if overlap >= 3:
                return True
    return False


def _deduplicate_frameworks(frameworks):
    """Deduplicate a list of frameworks."""
    unique = []
    for fw in frameworks:
        if not _is_duplicate_framework(fw, unique):
            unique.append(fw)
    return unique


def _detect_persona(source_id, data):
    """Detect which persona this content belongs to."""
    # Check source_id for person name hints
    if not source_id:
        return None

    source_lower = source_id.lower()
    persona_hints = {
        "hormozi": "Alex Hormozi",
        "cole": "Cole Gordon",
        "gordon": "Cole Gordon",
        "sam": "Sam Oven",
        "oven": "Sam Oven",
        "jordan": "Jordan Lee",
        "miner": "Jeremy Miner",
        "haynes": "Jeremy Haynes",
        "brunson": "Russell Brunson",
    }

    for hint, persona in persona_hints.items():
        if hint in source_lower:
            return persona

    # Check metadata
    meta_persona = data.get("persona", data.get("speaker", data.get("author")))
    if meta_persona:
        return meta_persona

    return None


def _is_noise(text):
    """Check if text is noise (too generic, stop words, etc.)."""
    noise_words = {
        "the", "a", "an", "this", "that", "these", "those",
        "and", "or", "but", "if", "then", "so", "because",
        "you", "your", "they", "them", "we", "our", "i", "my",
        "it", "its", "is", "are", "was", "were", "be",
    }
    words = text.lower().split()
    if len(words) <= 1:
        return True
    if all(w in noise_words for w in words):
        return True
    if len(text) < 4:
        return True
    return False


def _slugify(text):
    """Convert text to slug format."""
    if not text:
        return "unknown"
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:50].strip("-")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n=== SKILL GENERATOR v1.0: Full Scan ===\n")
        result = scan_all_and_generate(save=True)
        print(f"Files scanned:           {result['files_scanned']}")
        print(f"Personas found:          {result['personas_found']}")
        print(f"Total frameworks:        {result['total_frameworks']}")
        print(f"Skills generated:        {result['total_skills_generated']}")

        if result["per_persona"]:
            print(f"\n--- Per Persona ---")
            for persona, count in sorted(result["per_persona"].items(),
                                          key=lambda x: -x[1]):
                print(f"  {persona:30s}  {count} frameworks")

    elif len(sys.argv) > 1:
        filepath = sys.argv[1]
        result = extract_frameworks_from_file(filepath)
        print(f"\nSource: {result['source_id']}")
        print(f"Persona: {result['persona']}")
        print(f"Frameworks found: {result['frameworks_found']}")
        for fw in result["frameworks"]:
            print(f"\n  [{fw.get('layer', '?')}] {fw['name']} ({fw['step_count']} steps)")
            for i, step in enumerate(fw["steps"][:5], 1):
                print(f"    {i}. {step[:80]}")

    else:
        print("Uso:")
        print("  python3 skill_generator.py --all        # Scan all + generate skills")
        print("  python3 skill_generator.py <filepath>   # Extract from single file")
        sys.exit(1)


if __name__ == "__main__":
    main()
