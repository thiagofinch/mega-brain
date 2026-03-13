#!/usr/bin/env python3
"""
VIABILITY SCORER - Intelligence Layer v1.0
============================================
Scoring multidimensional APEX para avaliar viabilidade de criacao de agentes.

5 dimensoes (inspirado MMOS APEX):
A - Availability (volume de conteudo)
P - Persona Clarity (consistencia de voz)
E - Evolution (cobertura temporal)
X - Expertise (frameworks originais)
S - Strategic Fit (alinhamento com dominios)

Decisao:
- APEX >= 7.0 -> GO (criar agente completo)
- APEX 5.0-6.9 -> CONDICIONAL (criar com ressalvas)
- APEX < 5.0 -> NO-GO (apenas tracking)

Dependencias: Sprints 6 + 7 completos
Inspiracao: MMOS APEX scoring (6 dim), Squad Creator axioma-validator

Versao: 1.0.0
Data: 2026-02-26
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import load_registry, save_registry, load_taxonomy

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
QUALITY_GATES_PATH = BASE_DIR / "scripts" / "quality_gates.yaml"
CHUNKS_DIR = BASE_DIR / "processing" / "chunks"
VIABILITY_LOG_PATH = BASE_DIR / "logs" / "viability_scoring.jsonl"

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
def load_quality_config():
    """Load quality gates config including viability scoring rules."""
    if QUALITY_GATES_PATH.exists():
        with open(QUALITY_GATES_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_viability_config():
    """Get viability scoring configuration."""
    config = load_quality_config()
    return config.get("viability_scoring", {})


# ---------------------------------------------------------------------------
# APEX DIMENSIONS
# ---------------------------------------------------------------------------
DIMENSIONS = {
    "A_availability": {
        "description": "Volume e variedade de conteudo disponivel",
        "weight": 1.0,
    },
    "P_persona_clarity": {
        "description": "Consistencia de personalidade nas fontes",
        "weight": 0.9,
    },
    "E_evolution": {
        "description": "Cobertura temporal e evolucao",
        "weight": 0.8,
    },
    "X_expertise": {
        "description": "Frameworks originais e singularidade",
        "weight": 0.9,
    },
    "S_strategic_fit": {
        "description": "Alinhamento com objetivos do Mega Brain",
        "weight": 0.8,
    },
}


# ---------------------------------------------------------------------------
# CORE: SCORE A PERSON
# ---------------------------------------------------------------------------
def score_person(person_name, registry=None):
    """
    Calculate APEX viability score for a person.

    Returns:
        {
            "person": str,
            "scores": {dimension: {score, evidence, weight}},
            "apex_score": float (weighted average),
            "decision": "GO" | "CONDITIONAL" | "NO-GO",
            "rationale": str,
        }
    """
    if registry is None:
        registry = load_registry()

    persons = registry.get("persons", {})
    person_data = persons.get(person_name, {})

    if not person_data:
        return {
            "person": person_name,
            "scores": {},
            "apex_score": 0.0,
            "decision": "NO-GO",
            "rationale": f"Pessoa '{person_name}' nao encontrada no registry.",
        }

    taxonomy = load_taxonomy()

    # Calculate each dimension
    scores = {}

    # A - Availability
    scores["A_availability"] = _score_availability(person_name, person_data)

    # P - Persona Clarity
    scores["P_persona_clarity"] = _score_persona_clarity(person_name, person_data)

    # E - Evolution
    scores["E_evolution"] = _score_evolution(person_name, person_data)

    # X - Expertise
    scores["X_expertise"] = _score_expertise(person_name, person_data, registry)

    # S - Strategic Fit
    scores["S_strategic_fit"] = _score_strategic_fit(person_name, person_data, taxonomy)

    # Calculate weighted APEX score
    total_weighted = 0.0
    total_weight = 0.0
    for dim_id, dim_score in scores.items():
        weight = DIMENSIONS[dim_id]["weight"]
        total_weighted += dim_score["score"] * weight
        total_weight += weight

    apex_score = round(total_weighted / total_weight, 2) if total_weight > 0 else 0.0

    # Decision
    config = get_viability_config()
    decision_rules = config.get("decision_rules", {})
    go_threshold = decision_rules.get("go", 7.0)
    conditional_threshold = decision_rules.get("conditional", 5.0)

    if apex_score >= go_threshold:
        decision = "GO"
        rationale = f"APEX {apex_score} >= {go_threshold}. Agente completo recomendado."
    elif apex_score >= conditional_threshold:
        decision = "CONDITIONAL"
        rationale = f"APEX {apex_score} entre {conditional_threshold}-{go_threshold}. Criar com ressalvas."
    else:
        decision = "NO-GO"
        rationale = f"APEX {apex_score} < {conditional_threshold}. Apenas tracking."

    return {
        "person": person_name,
        "scores": scores,
        "apex_score": apex_score,
        "decision": decision,
        "rationale": rationale,
    }


def score_all_persons(registry=None, save=True):
    """Score all persons in registry."""
    if registry is None:
        registry = load_registry()

    persons = registry.get("persons", {})
    results = []

    for person_name in persons:
        result = score_person(person_name, registry=registry)
        results.append(result)

        # Update registry with viability score
        if save:
            persons[person_name]["viability_score"] = result["apex_score"]
            persons[person_name]["viability_decision"] = result["decision"]

    if save:
        save_registry(registry)
        _log_scores(results)

    results.sort(key=lambda x: -x["apex_score"])
    return results


# ---------------------------------------------------------------------------
# DIMENSION SCORERS
# ---------------------------------------------------------------------------
def _score_availability(person_name, person_data):
    """A - Volume and variety of available content."""
    sources = person_data.get("sources", [])
    mention_count = person_data.get("mention_count", 0)
    n_sources = len(sources)

    # Heuristic: more sources and mentions = more content
    if n_sources >= 10 and mention_count >= 50:
        score = 10
        evidence = f"{n_sources} sources, {mention_count} mentions (extensive)"
    elif n_sources >= 5 and mention_count >= 20:
        score = 8
        evidence = f"{n_sources} sources, {mention_count} mentions (good)"
    elif n_sources >= 3 and mention_count >= 10:
        score = 6
        evidence = f"{n_sources} sources, {mention_count} mentions (moderate)"
    elif n_sources >= 2:
        score = 5
        evidence = f"{n_sources} sources, {mention_count} mentions (minimal)"
    elif n_sources >= 1:
        score = 3
        evidence = f"{n_sources} source, {mention_count} mentions (scarce)"
    else:
        score = 1
        evidence = "No sources identified"

    return {
        "score": score,
        "evidence": evidence,
        "weight": DIMENSIONS["A_availability"]["weight"],
    }


def _score_persona_clarity(person_name, person_data):
    """P - Consistency of personality across sources."""
    domains = person_data.get("domains", [])
    has_dna = person_data.get("has_dna", False)
    has_agent = person_data.get("has_agent", False)

    # More domains with DNA = clearer persona
    if has_dna and has_agent and len(domains) >= 3:
        score = 10
        evidence = f"DNA extracted, agent exists, {len(domains)} domains (clear persona)"
    elif has_dna and len(domains) >= 2:
        score = 8
        evidence = f"DNA extracted, {len(domains)} domains (good clarity)"
    elif len(domains) >= 3:
        score = 6
        evidence = f"{len(domains)} domains identified (moderate clarity)"
    elif len(domains) >= 1:
        score = 4
        evidence = f"{len(domains)} domain(s) (limited clarity)"
    else:
        score = 2
        evidence = "No domains identified (unclear persona)"

    return {
        "score": score,
        "evidence": evidence,
        "weight": DIMENSIONS["P_persona_clarity"]["weight"],
    }


def _score_evolution(person_name, person_data):
    """E - Temporal coverage and evolution."""
    created_at = person_data.get("created_at", "")
    last_seen = person_data.get("last_seen", "")
    sources = person_data.get("sources", [])

    # Heuristic: more sources over longer time = more evolution
    # Since we don't have exact timestamps per source, estimate from count
    n_sources = len(sources)

    if n_sources >= 10:
        score = 8
        evidence = f"{n_sources} sources (likely spans significant time)"
    elif n_sources >= 5:
        score = 6
        evidence = f"{n_sources} sources (some temporal coverage)"
    elif n_sources >= 3:
        score = 5
        evidence = f"{n_sources} sources (limited temporal data)"
    else:
        score = 3
        evidence = f"{n_sources} source(s) (snapshot, minimal evolution data)"

    return {
        "score": score,
        "evidence": evidence,
        "weight": DIMENSIONS["E_evolution"]["weight"],
    }


def _score_expertise(person_name, person_data, registry):
    """X - Original frameworks and uniqueness."""
    # Check themes associated with this person's sources
    themes = registry.get("themes", {})
    person_sources = set(person_data.get("sources", []))

    # Count frameworks from same sources
    framework_count = 0
    for theme_name, theme_data in themes.items():
        theme_sources = set(theme_data.get("sources", []))
        if person_sources & theme_sources:
            framework_count += 1

    # Also check business_model for frameworks
    bm = person_data.get("business_model", {})
    has_business_model = bm.get("detected", False) if bm else False

    if framework_count >= 20 and has_business_model:
        score = 10
        evidence = f"{framework_count} associated themes/frameworks + business model (expert)"
    elif framework_count >= 10:
        score = 8
        evidence = f"{framework_count} associated themes/frameworks (deep expertise)"
    elif framework_count >= 5:
        score = 6
        evidence = f"{framework_count} associated themes/frameworks (moderate)"
    elif framework_count >= 2:
        score = 4
        evidence = f"{framework_count} associated themes/frameworks (limited)"
    else:
        score = 2
        evidence = f"{framework_count} themes (insufficient expertise data)"

    return {
        "score": score,
        "evidence": evidence,
        "weight": DIMENSIONS["X_expertise"]["weight"],
    }


def _score_strategic_fit(person_name, person_data, taxonomy):
    """S - Alignment with Mega Brain objectives."""
    domains = person_data.get("domains", [])
    person_name_upper = person_name.upper().replace(" ", "-")

    # Check if person is in taxonomy (prioritized)
    tax_pessoas = taxonomy.get("pessoas", {})
    is_taxonomy_person = person_name_upper in tax_pessoas

    # Core domains for Mega Brain
    core_domains = {"vendas", "offers", "scaling", "marketing", "hiring", "management"}
    domain_overlap = len(set(domains) & core_domains)

    if is_taxonomy_person and domain_overlap >= 3:
        score = 10
        evidence = f"Taxonomy persona with {domain_overlap} core domains (perfect fit)"
    elif is_taxonomy_person:
        score = 8
        evidence = f"Taxonomy persona with {domain_overlap} core domain(s) (strong fit)"
    elif domain_overlap >= 2:
        score = 7
        evidence = f"{domain_overlap} core domains aligned (good fit)"
    elif domain_overlap >= 1:
        score = 5
        evidence = f"{domain_overlap} core domain (partial fit)"
    else:
        score = 3
        evidence = f"No core domain overlap (tangential)"

    return {
        "score": score,
        "evidence": evidence,
        "weight": DIMENSIONS["S_strategic_fit"]["weight"],
    }


# ---------------------------------------------------------------------------
# QUALITY GATE CHECKER
# ---------------------------------------------------------------------------
def check_quality_gates(entity_type, entity_data, phase, registry=None):
    """
    Check all quality gates for a given phase and entity.

    Returns:
        {
            "passed": bool,
            "gates_checked": int,
            "gates_passed": int,
            "gates_failed": int,
            "vetos_triggered": int,
            "details": [{gate_id, name, passed, reason}],
        }
    """
    config = load_quality_config()
    gates = config.get("gates", {})
    vetos = config.get("veto_conditions", {})

    results = []
    veto_count = 0

    # Check gates for this phase
    for gate_id, gate in gates.items():
        if gate.get("phase") != phase:
            continue

        passed, reason = _evaluate_gate(gate, entity_data, registry)
        results.append({
            "gate_id": gate_id,
            "name": gate.get("name", ""),
            "type": gate.get("type", "auto"),
            "passed": passed,
            "reason": reason,
            "severity": gate.get("severity", "warning"),
        })

    # Check veto conditions
    for veto_id, veto in vetos.items():
        applies = veto.get("applies_to", [])
        if phase in applies:
            triggered, reason = _evaluate_veto(veto, entity_data)
            if triggered:
                veto_count += 1
                results.append({
                    "gate_id": veto_id,
                    "name": veto.get("name", ""),
                    "type": "veto",
                    "passed": False,
                    "reason": reason,
                    "severity": "blocking",
                })

    passed_count = sum(1 for r in results if r["passed"])
    failed_count = sum(1 for r in results if not r["passed"])
    all_passed = failed_count == 0

    return {
        "passed": all_passed,
        "gates_checked": len(results),
        "gates_passed": passed_count,
        "gates_failed": failed_count,
        "vetos_triggered": veto_count,
        "details": results,
    }


def _evaluate_gate(gate, entity_data, registry):
    """Evaluate a single quality gate."""
    phase = gate.get("phase", "")
    criteria = gate.get("criteria", [])

    if phase == "entity_detection":
        ws = entity_data.get("weighted_score", 0)
        sources = len(entity_data.get("sources", []))
        domain_ids = entity_data.get("domain_ids", [])

        if ws < 10:
            return False, f"weighted_score {ws} < 10"
        if sources < 2:
            return False, f"sources {sources} < 2"
        if not domain_ids:
            return False, "no domain_match"
        return True, "All criteria met"

    elif phase == "dossier_creation":
        score = entity_data.get("relevance_score", 0)
        occurrences = entity_data.get("occurrence_count", 0)
        sources = len(entity_data.get("sources", []))

        if score < 25.0:
            return False, f"relevance_score {score} < 25.0"
        if occurrences < 15:
            return False, f"occurrences {occurrences} < 15"
        if sources < 2:
            return False, f"sources {sources} < 2"
        return True, "All criteria met"

    elif phase == "agent_creation":
        ws = entity_data.get("weighted_score", 0)
        sow = entity_data.get("sow_generated", False)
        resps = len(entity_data.get("responsibilities", []))
        domain_ids = entity_data.get("domain_ids", [])

        if not sow:
            return False, "SOW not generated"
        if resps < 3:
            return False, f"responsibilities {resps} < 3"
        if not domain_ids:
            return False, "no domain_match"
        return True, "All criteria met"

    elif phase == "skill_generation":
        source_id = entity_data.get("source_id", "")
        steps = entity_data.get("workflow_steps", [])
        evidence = entity_data.get("evidence", "")

        if not source_id:
            return False, "no source_id"
        if len(steps) < 3:
            return False, f"steps {len(steps)} < 3"
        if len(evidence) < 50:
            return False, f"evidence too short ({len(evidence)} chars)"
        return True, "All criteria met"

    return True, "No specific checks for this phase"


def _evaluate_veto(veto, entity_data):
    """Evaluate a veto condition. Returns (triggered, reason)."""
    condition = veto.get("condition", "")

    if "< 2 fontes" in condition:
        sources = len(entity_data.get("sources", []))
        if sources < 2:
            return True, f"VETO: {sources} < 2 fontes"

    if "sem domain_match" in condition:
        domain_ids = entity_data.get("domain_ids", [])
        if not domain_ids:
            return True, "VETO: sem domain_match"

    if "sem frameworks" in condition:
        has_frameworks = entity_data.get("sow_generated", False)
        if not has_frameworks:
            return True, "VETO: agente generico sem frameworks"

    if "sem source_id" in condition:
        source_id = entity_data.get("source_id", "")
        if not source_id:
            return True, "VETO: sem source_id verificavel"

    return False, ""


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
def _log_scores(results):
    """Log viability scores to JSONL."""
    VIABILITY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    for result in results:
        log_entry = {
            "timestamp": now,
            "trigger_type": "viability_scoring",
            "person": result["person"],
            "apex_score": result["apex_score"],
            "decision": result["decision"],
            "dimension_scores": {
                k: v["score"] for k, v in result["scores"].items()
            },
        }
        with open(VIABILITY_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n=== VIABILITY SCORER (APEX) v1.0 ===\n")
        results = score_all_persons(save=True)

        for r in results:
            decision_icon = {"GO": "[GO]", "CONDITIONAL": "[??]", "NO-GO": "[NO]"}
            icon = decision_icon.get(r["decision"], "[??]")
            print(f"  {icon} {r['person']:25s}  APEX={r['apex_score']:5.2f}  {r['decision']}")
            for dim, scores in r["scores"].items():
                dim_short = dim.split("_")[0]
                print(f"       {dim_short}: {scores['score']:2d}/10 ({scores['evidence'][:50]})")
            print()

        # Summary
        go_count = sum(1 for r in results if r["decision"] == "GO")
        cond_count = sum(1 for r in results if r["decision"] == "CONDITIONAL")
        nogo_count = sum(1 for r in results if r["decision"] == "NO-GO")
        print(f"  SUMMARY: {go_count} GO | {cond_count} CONDITIONAL | {nogo_count} NO-GO")

    elif len(sys.argv) > 1 and sys.argv[1] != "--help":
        person = " ".join(sys.argv[1:])
        print(f"\n=== APEX Score for '{person}' ===\n")
        result = score_person(person)
        print(f"  APEX Score: {result['apex_score']}")
        print(f"  Decision:   {result['decision']}")
        print(f"  Rationale:  {result['rationale']}")
        print()
        for dim, scores in result["scores"].items():
            print(f"  {dim}: {scores['score']}/10")
            print(f"    Evidence: {scores['evidence']}")

    else:
        print("Uso:")
        print("  python3 viability_scorer.py --all              # Score all persons")
        print("  python3 viability_scorer.py 'Alex Hormozi'     # Score specific person")
        sys.exit(1)


if __name__ == "__main__":
    main()
