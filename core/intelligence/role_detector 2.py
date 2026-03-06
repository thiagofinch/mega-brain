#!/usr/bin/env python3
"""
ROLE DETECTOR - Intelligence Layer v2.0
========================================
Deteccao agnostica de cargos/funcoes em 3 niveis:
  1. DIRETA (peso 1.0) - nome do cargo aparece no texto
  2. INFERIDA (peso 0.7) - atividade descrita implica um cargo
  3. EMERGENTE (peso 0.5) - padroes genericos detectam role desconhecido

Mudancas vs v1.0:
- Vocabulario carregado de _ROLE_PATTERNS.yaml (nao hardcoded)
- Inferencia implicita via ACTIVITY_TO_ROLE_MAP
- Deteccao de roles emergentes (agnostico a qualquer dominio)
- Integracao com entity_normalizer para escrita no registry
- mention_breakdown (direct/inferred/emergent) + weighted_score

Versao: 2.0.0
Data: 2026-02-25
"""

import json
import re
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import (
    load_registry, save_registry, normalize_entity, load_taxonomy
)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
ROLE_PATTERNS_PATH = BASE_DIR / "scripts" / "_ROLE_PATTERNS.yaml"
TAXONOMY_PATH = BASE_DIR / "knowledge" / "dna" / "DOMAINS-TAXONOMY.yaml"
TRIGGER_CONFIG_PATH = BASE_DIR / "scripts" / "trigger_config.yaml"
TRIGGERS_LOG_PATH = BASE_DIR / "logs" / "triggers.jsonl"

# ---------------------------------------------------------------------------
# DETECTION WEIGHTS (configuravel)
# ---------------------------------------------------------------------------
WEIGHT_DIRECT = 1.0
WEIGHT_STRONG = 2.0
WEIGHT_INFERRED = 0.7
WEIGHT_EMERGENT = 0.5

# Max items in detection_history per role
MAX_DETECTION_HISTORY = 20


# ---------------------------------------------------------------------------
# DYNAMIC VOCABULARY LOADER
# ---------------------------------------------------------------------------
_patterns_cache = None
_inference_cache = None
_emergence_cache = None


def _load_role_patterns():
    """Load role patterns from _ROLE_PATTERNS.yaml (cached)."""
    global _patterns_cache, _inference_cache, _emergence_cache
    if _patterns_cache is not None:
        return _patterns_cache, _inference_cache, _emergence_cache

    if not ROLE_PATTERNS_PATH.exists():
        _patterns_cache = {}
        _inference_cache = {}
        _emergence_cache = {"patterns": [], "stopwords": set()}
        return _patterns_cache, _inference_cache, _emergence_cache

    with open(ROLE_PATTERNS_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Separate role patterns from special sections
    role_patterns = {}
    inference_map = raw.pop("_inference_map", {})
    emergence_patterns = raw.pop("_emergence_patterns", [])
    emergence_stopwords = set(raw.pop("_emergence_stopwords", []))

    for key, val in raw.items():
        if key.startswith("_") or not isinstance(val, dict):
            continue
        role_patterns[key] = val

    _patterns_cache = role_patterns
    _inference_cache = inference_map
    _emergence_cache = {
        "patterns": emergence_patterns,
        "stopwords": emergence_stopwords,
    }
    return _patterns_cache, _inference_cache, _emergence_cache


def load_role_vocabulary():
    """
    Build complete role vocabulary from YAML sources.
    Merges _ROLE_PATTERNS.yaml (patterns) with DOMAINS-TAXONOMY.yaml (domains).
    """
    role_patterns, _, _ = _load_role_patterns()
    tax = load_taxonomy()
    taxonomy_cargos = tax.get("cargos", {})

    vocab = {}
    # All roles from patterns file
    for role_id, pdata in role_patterns.items():
        cargo_data = taxonomy_cargos.get(role_id, {})
        vocab[role_id] = {
            "patterns": pdata.get("patterns", []),
            "strong_patterns": pdata.get("strong_patterns", []),
            "exclude_patterns": pdata.get("exclude_patterns", []),
            "domains": (
                cargo_data.get("dominios_primarios", []) +
                cargo_data.get("dominios_secundarios", [])
            ),
        }

    # Roles in taxonomy without patterns (basic detection by name)
    for cargo_id, cargo_data in taxonomy_cargos.items():
        if cargo_id not in vocab:
            nice_name = cargo_id.lower().replace("-", " ")
            vocab[cargo_id] = {
                "patterns": [rf"\b{re.escape(nice_name)}\b"],
                "strong_patterns": [],
                "exclude_patterns": [],
                "domains": (
                    cargo_data.get("dominios_primarios", []) +
                    cargo_data.get("dominios_secundarios", [])
                ),
            }

    return vocab


# ---------------------------------------------------------------------------
# LEVEL 1: DIRECT DETECTION (peso 1.0 / 2.0)
# ---------------------------------------------------------------------------
def _detect_known_roles(text, role_vocab):
    """
    Detect roles by matching known patterns in text.
    Returns list of {name, type, weight, match, context}.
    """
    text_lower = text.lower()
    detections = []

    for role_canonical, vocab in role_vocab.items():
        role_matches = []

        # Check exclude patterns first
        excluded = False
        for exc_pattern in vocab.get("exclude_patterns", []):
            try:
                if re.search(exc_pattern, text_lower):
                    excluded = True
                    break
            except re.error:
                continue
        if excluded:
            continue

        # Strong patterns (weight: 2x)
        for pattern in vocab.get("strong_patterns", []):
            try:
                matches = list(re.finditer(pattern, text_lower))
            except re.error:
                continue
            for m in matches:
                context = _extract_context(text, m.start(), m.end())
                role_matches.append({
                    "sub_type": "strong",
                    "weight": WEIGHT_STRONG,
                    "match": m.group(),
                    "context": context,
                })

        # Normal patterns (weight: 1x)
        for pattern in vocab.get("patterns", []):
            try:
                matches = list(re.finditer(pattern, text_lower))
            except re.error:
                continue
            for m in matches:
                already = any(
                    d["match"] in m.group() or m.group() in d["match"]
                    for d in role_matches
                )
                if already:
                    continue
                context = _extract_context(text, m.start(), m.end())
                role_matches.append({
                    "sub_type": "normal",
                    "weight": WEIGHT_DIRECT,
                    "match": m.group(),
                    "context": context,
                })

        if role_matches:
            total_weight = sum(d["weight"] for d in role_matches)
            detections.append({
                "name": role_canonical,
                "type": "direct",
                "weight": total_weight,
                "raw_matches": len(role_matches),
                "contexts": [d["context"] for d in role_matches[:3]],
            })

    return detections


# ---------------------------------------------------------------------------
# LEVEL 2: INFERRED DETECTION (peso 0.7)
# ---------------------------------------------------------------------------
def _infer_roles_from_context(text):
    """
    Detect roles implied by activities described in text.
    E.g. "writing the sales page copy" → COPYWRITER
    Returns list of {name, type, weight, match, context}.
    """
    _, inference_map, _ = _load_role_patterns()
    if not inference_map:
        return []

    text_lower = text.lower()
    detections = []
    seen_roles = set()

    for role_canonical, patterns in inference_map.items():
        for pattern in patterns:
            try:
                matches = list(re.finditer(pattern, text_lower))
            except re.error:
                continue
            for m in matches:
                if role_canonical not in seen_roles:
                    context = _extract_context(text, m.start(), m.end())
                    detections.append({
                        "name": role_canonical,
                        "type": "inferred",
                        "weight": WEIGHT_INFERRED,
                        "activity": m.group(),
                        "contexts": [context],
                    })
                    seen_roles.add(role_canonical)

    return detections


# ---------------------------------------------------------------------------
# LEVEL 3: EMERGENT DETECTION (peso 0.5)
# ---------------------------------------------------------------------------
def _detect_emergent_roles(text, known_roles):
    """
    Detect roles NOT in the vocabulary using generic patterns.
    E.g. "our data scientist handles analytics" → DATA-SCIENTIST (emergent)
    Returns list of {name, type, weight, raw, context}.
    """
    _, _, emergence_data = _load_role_patterns()
    if not emergence_data.get("patterns"):
        return []

    text_lower = text.lower()
    stopwords = emergence_data.get("stopwords", set())
    detections = []
    seen = set()

    # Common trailing words that regex greedily captures but aren't role names
    trailing_noise = {
        "for", "is", "are", "was", "were", "in", "on", "at", "to", "of",
        "and", "or", "the", "a", "an", "who", "that", "this", "with",
        "all", "por", "para", "que", "com", "do", "da", "dos", "das",
        "no", "na", "nos", "nas", "de", "em", "um", "uma",
    }

    # Common English words that are NOT role names (broad filter for single-word matches)
    # Emergent detection is aggressive by design; this filter prevents noise.
    _common_non_roles = {
        # Verbs
        "have", "has", "had", "get", "got", "make", "made", "take", "took",
        "give", "gave", "want", "need", "know", "think", "say", "said",
        "go", "went", "come", "came", "see", "saw", "find", "found",
        "put", "set", "run", "ran", "let", "keep", "kept", "call",
        "try", "tried", "start", "stop", "pay", "paid", "build", "built",
        "close", "open", "send", "sent", "sell", "sold", "buy", "bought",
        "train", "hire", "fire", "qualify", "scale", "grow", "grew",
        "approach", "handle", "manage", "lead", "drive", "drove",
        # Adjectives / Adverbs
        "good", "bad", "best", "worst", "better", "worse", "right", "wrong",
        "big", "small", "long", "short", "high", "low", "fast", "slow",
        "exact", "same", "different", "many", "much", "more", "most",
        "less", "least", "only", "just", "really", "very", "even",
        "enough", "sure", "every", "whole", "entire", "real", "true",
        "top", "bottom", "front", "back", "full", "early", "late",
        # Nouns (generic, not roles)
        "time", "year", "month", "week", "day", "hour", "number", "money",
        "way", "thing", "point", "fact", "case", "place", "reason",
        "result", "end", "problem", "question", "answer", "example",
        "level", "type", "kind", "sort", "step", "stage", "process",
        "system", "model", "method", "plan", "goal", "value", "cost",
        "price", "rate", "deal", "offer", "call", "meeting", "event",
        "launch", "growth", "revenue", "profit", "loss", "margin",
        "lead", "leads", "pipeline", "funnel", "script", "pitch",
        "objection", "closing", "follow-up", "outreach", "campaign",
        "setting", "inbound", "outbound",
        # Pronouns / Determiners
        "you", "they", "them", "we", "us", "he", "she", "him", "her",
        "its", "my", "your", "his", "their", "our", "who", "what",
        # Compound noise
        "exact-same", "best-possible", "get-your", "train-your",
        "the-launch", "mortgage-leads",
    }

    for pattern in emergence_data["patterns"]:
        try:
            matches = re.findall(pattern, text_lower)
        except re.error:
            continue
        for match in matches:
            raw = match.strip()
            # Strip leading and trailing noise words (greedy regex artifact)
            words = raw.split()
            while words and words[-1] in trailing_noise:
                words.pop()
            while words and words[0] in trailing_noise:
                words.pop(0)
            raw = " ".join(words)

            # Filter noise
            if not raw or len(raw) < 3 or len(raw) > 40:
                continue
            # Check stopwords
            words = raw.split()
            if all(w in stopwords for w in words):
                continue
            if any(w in stopwords for w in words) and len(words) <= 1:
                continue

            # Single-word filter: must look like a plausible role name
            if len(words) == 1:
                word = words[0]
                if word in _common_non_roles:
                    continue
                # Very short single words are almost never roles
                if len(word) < 5:
                    continue

            # Multi-word filter: all words being common is noise
            if len(words) >= 2 and all(w in _common_non_roles for w in words):
                continue

            # Multi-word with pronoun/article pattern (e.g. "if-your", "get-your")
            if len(words) >= 2 and any(w in trailing_noise or w in stopwords for w in words):
                # At least one meaningful word must remain
                meaningful = [w for w in words if w not in trailing_noise and w not in stopwords and w not in _common_non_roles]
                if not meaningful:
                    continue

            normalized = raw.upper().replace(" ", "-")
            # Skip if already a known role
            if normalized in known_roles:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)

            detections.append({
                "name": normalized,
                "type": "emergent",
                "weight": WEIGHT_EMERGENT,
                "raw": raw,
                "contexts": [_extract_context(text, 0, min(100, len(text)))],
            })

    return detections


# ---------------------------------------------------------------------------
# CORE: DETECT ROLES IN TEXT (v2.0)
# ---------------------------------------------------------------------------
def detect_roles_in_text(text, source_id=None, registry=None):
    """
    Detect roles/positions mentioned in text using 3-level detection.

    Args:
        text: raw text to analyze
        source_id: source identifier for tracking
        registry: ENTITY-REGISTRY dict

    Returns:
        {
            "roles_detected": [{role, detection_type, weight, contexts}],
            "new_roles": [{role, detection_type}],
            "triggers_activated": [{role, trigger_type, details}]
        }
    """
    if registry is None:
        registry = load_registry()

    role_vocab = load_role_vocabulary()

    # Level 1: Direct detection (peso 1.0/2.0)
    direct_roles = _detect_known_roles(text, role_vocab)

    # Level 2: Inferred detection (peso 0.7)
    inferred_roles = _infer_roles_from_context(text)

    # Level 3: Emergent detection (peso 0.5)
    emergent_roles = _detect_emergent_roles(text, set(role_vocab.keys()))

    # Merge all detections
    all_detections = []
    roles_section = registry.setdefault("roles", {})

    for det in direct_roles + inferred_roles + emergent_roles:
        role_name = det["name"]

        # Ensure role exists in registry (via entity_normalizer for known,
        # direct creation for emergent)
        if role_name not in roles_section:
            if det["type"] == "emergent":
                # Create emergent candidate directly
                roles_section[role_name] = _create_role_entry(
                    role_name, source_id, status="emergent_candidate"
                )
            else:
                # Use normalize_entity for known roles (taxonomy lookup)
                result = normalize_entity(
                    role_name, "role", registry=registry,
                    source_id=source_id, auto_save=False
                )
                role_name = result["canonical"]

        # Update mention_breakdown and weighted_score
        role_data = roles_section.get(role_name)
        if role_data:
            _update_role_detection(role_data, det, source_id)

        all_detections.append({
            "role": role_name,
            "detection_type": det["type"],
            "weight": det["weight"],
            "contexts": det.get("contexts", []),
        })

    # Check triggers for all detected roles
    triggers = []
    for det in all_detections:
        trigger = _check_role_trigger(det["role"], registry)
        if trigger:
            triggers.append(trigger)

    # new_roles = emergent-only (roles not previously in vocabulary)
    new = [d for d in all_detections if d["detection_type"] == "emergent"]

    return {
        "roles_detected": all_detections,
        "new_roles": new,
        "triggers_activated": triggers,
    }


def _create_role_entry(role_name, source_id=None, status="tracking"):
    """Create a new role entry with v2.0 fields."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "canonical": role_name,
        "aliases": [],
        "mention_count": 0,
        "mention_breakdown": {"direct": 0, "inferred": 0, "emergent": 0},
        "weighted_score": 0.0,
        "sources": [source_id] if source_id else [],
        "has_agent": False,
        "domain_ids": [],
        "responsibilities": [],
        "status": status,
        "detection_history": [],
        "created_at": now,
        "last_seen": now,
    }


def _update_role_detection(role_data, detection, source_id):
    """Update a role's mention data with a new detection."""
    det_type = detection["type"]
    weight = detection["weight"]

    # Ensure v2.0 fields exist (backward compat)
    if "mention_breakdown" not in role_data:
        old_count = role_data.get("mention_count", 0)
        role_data["mention_breakdown"] = {
            "direct": old_count, "inferred": 0, "emergent": 0
        }
    if "weighted_score" not in role_data:
        role_data["weighted_score"] = float(role_data.get("mention_count", 0))
    if "detection_history" not in role_data:
        role_data["detection_history"] = []

    # Increment breakdown
    breakdown = role_data["mention_breakdown"]
    breakdown[det_type] = breakdown.get(det_type, 0) + 1

    # Update total mention_count
    role_data["mention_count"] = (
        breakdown.get("direct", 0) +
        breakdown.get("inferred", 0) +
        breakdown.get("emergent", 0)
    )

    # Recalculate weighted_score
    role_data["weighted_score"] = (
        breakdown.get("direct", 0) * WEIGHT_DIRECT +
        breakdown.get("inferred", 0) * WEIGHT_INFERRED +
        breakdown.get("emergent", 0) * WEIGHT_EMERGENT
    )

    # Add source
    if source_id:
        sources = role_data.setdefault("sources", [])
        if source_id not in sources:
            sources.append(source_id)

    # Update detection_history (capped)
    history = role_data.setdefault("detection_history", [])
    history_entry = {
        "type": det_type,
        "weight": weight,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if source_id:
        history_entry["source"] = source_id
    if det_type == "inferred" and "activity" in detection:
        history_entry["activity"] = detection["activity"][:100]
    if det_type == "emergent" and "raw" in detection:
        history_entry["raw"] = detection["raw"][:60]
    if detection.get("contexts"):
        history_entry["context"] = detection["contexts"][0][:120]

    history.append(history_entry)
    # Keep only last N entries
    if len(history) > MAX_DETECTION_HISTORY:
        role_data["detection_history"] = history[-MAX_DETECTION_HISTORY:]

    # Update last_seen
    role_data["last_seen"] = datetime.now(timezone.utc).isoformat()

    # Status lifecycle: emergent_candidate → tracking → active
    _update_role_status(role_data)


def _update_role_status(role_data):
    """Update role status based on weighted_score and sources."""
    ws = role_data.get("weighted_score", 0)
    n_sources = len(role_data.get("sources", []))
    current = role_data.get("status", "tracking")

    # Don't downgrade from active
    if current == "active":
        return

    if ws >= 10 and n_sources >= 2:
        role_data["status"] = "active"
    elif ws >= 5 and n_sources >= 1:
        role_data["status"] = "tracking"
    elif ws >= 3:
        if current == "emergent_candidate":
            role_data["status"] = "tracking"
    # else keep current status


# ---------------------------------------------------------------------------
# FILE-LEVEL DETECTION
# ---------------------------------------------------------------------------
def detect_roles_in_chunk(chunk_data, source_id=None, registry=None):
    """Detect roles in a chunk, handling all chunk formats."""
    text = ""
    if "content" in chunk_data:
        text = chunk_data["content"]
    elif "texto" in chunk_data:
        text = chunk_data["texto"]
    elif "text" in chunk_data:
        text = chunk_data["text"]

    if not text:
        return {"roles_detected": [], "new_roles": [], "triggers_activated": []}

    return detect_roles_in_text(text, source_id=source_id, registry=registry)


def detect_roles_in_file(filepath, registry=None, save=True):
    """
    Detect roles across all chunks in a file.
    Returns aggregated results.
    """
    if registry is None:
        registry = load_registry()

    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_id = data.get("source_id", data.get("source_hash", filepath.stem))

    if "chunks" in data:
        chunks = data["chunks"]
    else:
        chunks = [data]

    all_detections = defaultdict(lambda: {"direct": 0, "inferred": 0, "emergent": 0})
    all_triggers = []
    all_new_roles = []

    for chunk in chunks:
        result = detect_roles_in_chunk(chunk, source_id=source_id, registry=registry)
        for det in result["roles_detected"]:
            all_detections[det["role"]][det["detection_type"]] += 1
        for det in result["new_roles"]:
            all_detections[det["role"]][det["detection_type"]] += 1
            all_new_roles.append(det)
        all_triggers.extend(result["triggers_activated"])

    if save:
        save_registry(registry)

    # Deduplicate triggers
    seen_triggers = set()
    unique_triggers = []
    for t in all_triggers:
        key = (t["role"], t["trigger_type"])
        if key not in seen_triggers:
            seen_triggers.add(key)
            unique_triggers.append(t)

    # Build summary
    role_summary = []
    for role, breakdown in sorted(all_detections.items(),
                                   key=lambda x: sum(x[1].values()), reverse=True):
        total = sum(breakdown.values())
        role_summary.append({
            "role": role,
            "total_mentions": total,
            "breakdown": dict(breakdown),
        })

    return {
        "source_id": source_id,
        "roles_detected": role_summary,
        "new_roles": all_new_roles,
        "triggers_activated": unique_triggers,
        "chunk_count": len(chunks),
    }


# ---------------------------------------------------------------------------
# SCAN ALL CHUNKS
# ---------------------------------------------------------------------------
def scan_all_chunks(registry=None, save=True):
    """Scan ALL chunk files for role mentions."""
    if registry is None:
        registry = load_registry()

    chunks_dir = BASE_DIR / "processing" / "chunks"
    all_detections = defaultdict(lambda: {"direct": 0, "inferred": 0, "emergent": 0})
    all_triggers = []
    all_new_roles = []
    files_scanned = 0

    for fpath in sorted(chunks_dir.glob("*.json")):
        if fpath.name in ("CHUNKS-STATE.json", "_INDEX.json", "_rag_export.json"):
            continue

        result = detect_roles_in_file(fpath, registry=registry, save=False)
        files_scanned += 1

        for det in result["roles_detected"]:
            for dtype, count in det.get("breakdown", {}).items():
                all_detections[det["role"]][dtype] += count
        for det in result.get("new_roles", []):
            all_new_roles.append(det)
        all_triggers.extend(result["triggers_activated"])

    if save:
        save_registry(registry)

    # Deduplicate triggers
    seen = set()
    unique_triggers = []
    for t in all_triggers:
        key = (t["role"], t["trigger_type"])
        if key not in seen:
            seen.add(key)
            unique_triggers.append(t)

    # Build sorted summary
    summary = []
    for role, breakdown in sorted(all_detections.items(),
                                   key=lambda x: sum(x[1].values()), reverse=True):
        total = sum(breakdown.values())
        ws = (breakdown.get("direct", 0) * WEIGHT_DIRECT +
              breakdown.get("inferred", 0) * WEIGHT_INFERRED +
              breakdown.get("emergent", 0) * WEIGHT_EMERGENT)
        summary.append({
            "role": role,
            "total_mentions": total,
            "weighted_score": round(ws, 1),
            "breakdown": dict(breakdown),
        })

    return {
        "files_scanned": files_scanned,
        "roles_detected": summary,
        "new_roles": all_new_roles,
        "triggers_activated": unique_triggers,
    }


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _extract_context(text, start, end, window=80):
    """Extract surrounding context around a match."""
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    context = text[ctx_start:ctx_end].strip()
    if ctx_start > 0:
        context = "..." + context
    if ctx_end < len(text):
        context = context + "..."
    return context


def _check_role_trigger(role_canonical, registry):
    """Check if a role has crossed the threshold for agent creation (tiered)."""
    if TRIGGER_CONFIG_PATH.exists():
        with open(TRIGGER_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    else:
        return None

    cargo_thresholds = config.get("thresholds", {}).get("agent_creation_cargo", {})

    role_data = registry.get("roles", {}).get(role_canonical, {})
    weighted_score = role_data.get("weighted_score", role_data.get("mention_count", 0))
    source_count = len(role_data.get("sources", []))
    has_agent = role_data.get("has_agent", False)

    if has_agent:
        return None

    # Check tiered thresholds
    tier = None

    # Tier 1: Established
    est = cargo_thresholds.get("established", {})
    if est:
        min_ws = est.get("min_weighted_score", cargo_thresholds.get("min_mentions", 10))
        min_src = est.get("min_sources", cargo_thresholds.get("min_sources", 2))
        if weighted_score >= min_ws and source_count >= min_src:
            tier = "established"

    # Tier 2: Emerging (only if not established)
    if tier is None:
        emg = cargo_thresholds.get("emerging", {})
        if emg:
            min_ws = emg.get("min_weighted_score", 5)
            min_src = emg.get("min_sources", 1)
            if weighted_score >= min_ws and source_count >= min_src:
                tier = "emerging"
                # Check promotion rules
                promo = emg.get("promotion_rules", {})
                if promo:
                    promo_ws = promo.get("min_weighted_score", 15)
                    promo_src = promo.get("min_sources", 2)
                    if weighted_score >= promo_ws and source_count >= promo_src:
                        tier = "established"

    if tier == "established":
        trigger = {
            "role": role_canonical,
            "trigger_type": "create_agent",
            "tier": "established",
            "weighted_score": weighted_score,
            "source_count": source_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _log_trigger(trigger)
        return trigger

    return None


def _log_trigger(trigger):
    """Log trigger activation to triggers.jsonl."""
    TRIGGERS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TRIGGERS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(trigger, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n=== ROLE DETECTOR v2.0: Full Scan ===\n")
        result = scan_all_chunks(save=True)
        print(f"Files scanned: {result['files_scanned']}")

        print(f"\n--- Roles Detected ({len(result['roles_detected'])}) ---")
        print(f"{'Role':<30} {'Total':>6} {'WScore':>7} {'Direct':>7} {'Infer':>7} {'Emerg':>7}")
        print("-" * 74)
        for det in result["roles_detected"]:
            bd = det.get("breakdown", {})
            print(f"  {det['role']:<28} {det['total_mentions']:>6} "
                  f"{det['weighted_score']:>7.1f} "
                  f"{bd.get('direct', 0):>7} {bd.get('inferred', 0):>7} "
                  f"{bd.get('emergent', 0):>7}")

        if result.get("new_roles"):
            unique_new = set(d["role"] for d in result["new_roles"])
            print(f"\n--- EMERGENT ROLES ({len(unique_new)}) ---")
            for role in sorted(unique_new):
                print(f"  [NEW] {role}")

        if result["triggers_activated"]:
            print(f"\n--- TRIGGERS ACTIVATED ({len(result['triggers_activated'])}) ---")
            for t in result["triggers_activated"]:
                print(f"  [!] {t['role']}: {t['trigger_type']} "
                      f"(ws={t.get('weighted_score', '?')}, "
                      f"tier={t.get('tier', '?')}, "
                      f"sources={t.get('source_count', '?')})")
        else:
            print(f"\nNo new triggers activated.")

    elif len(sys.argv) > 1 and sys.argv[1] == "--text":
        text = " ".join(sys.argv[2:])
        result = detect_roles_in_text(text)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    elif len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"\n=== ROLE DETECTOR v2.0: {filepath} ===\n")
        result = detect_roles_in_file(filepath)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    else:
        print("Uso:")
        print("  python3 role_detector.py --all              # Scan all chunk files")
        print("  python3 role_detector.py <filepath>         # Scan single file")
        print("  python3 role_detector.py --text 'o closer deve...'  # Test text")
        sys.exit(1)


if __name__ == "__main__":
    main()
