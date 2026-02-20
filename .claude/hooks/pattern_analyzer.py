#!/usr/bin/env python3
"""
Pattern Analyzer - Layer 3 do META-AGENT System v1.0

FUNÇÃO: Detecta padrões de request e aprende preferências do usuário.
        Sugere criação de skills quando padrões recorrentes são detectados.

REGRA #28: META-AGENT QUALITY AWARENESS
PRINCÍPIO: Aprende INDIRETAMENTE, não pergunta
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LOGS_PATH = PROJECT_ROOT / "logs"
PATTERNS_LOG = LOGS_PATH / "learning_patterns.jsonl"
PREFERENCES_LOG = LOGS_PATH / "preferences.jsonl"
SKILL_SUGGESTIONS_LOG = LOGS_PATH / "skill_suggestions.jsonl"


# ═══════════════════════════════════════════════════════════════════════════
# FEEDBACK SIGNALS (APRENDIZADO INDIRETO)
# ═══════════════════════════════════════════════════════════════════════════

# Sinais de feedback detectados na resposta do usuário (pesos)
FEEDBACK_SIGNALS = {
    # Negativos (indicam insatisfação)
    "refaça": -15,
    "de novo": -15,
    "não era isso": -20,
    "errado": -15,
    "não gostei": -10,
    "muito resumido": -10,
    "faltou": -10,
    "incompleto": -10,
    "onde está": -5,
    "cadê": -5,
    "não tem": -10,

    # Positivos (indicam satisfação)
    "perfeito": +10,
    "exatamente": +10,
    "ótimo": +5,
    "isso mesmo": +5,
    "obrigado": +3,
    "show": +5,
    "massa": +5,
    "muito bom": +5,
    "excelente": +8,
}

# Threshold para sugerir criação de skill (baseado em DETECTION-PROTOCOL.md)
SKILL_SUGGESTION_THRESHOLD = 3


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN DETECTION
# ═══════════════════════════════════════════════════════════════════════════

# Categorias de padrão detectáveis
PATTERN_CATEGORIES = {
    "log_visual": {
        "keywords": ["log bonito", "log visual", "formatar log", "status formatado", "resumo visual"],
        "agent_hint": "chronicler"
    },
    "análise_financeira": {
        "keywords": ["roi", "unit economics", "margem", "lucratividade", "custos", "receita"],
        "agent_hint": "finance-agent"
    },
    "estrutura_time": {
        "keywords": ["time de vendas", "estrutura comercial", "org chart", "organograma", "equipe"],
        "agent_hint": "talent-agent"
    },
    "playbook": {
        "keywords": ["playbook", "manual", "guia", "passo a passo", "tutorial"],
        "agent_hint": None
    },
    "comparação": {
        "keywords": ["compare", "diferença entre", "versus", "vs", "comparar"],
        "agent_hint": None
    },
    "conselho": {
        "keywords": ["conselho", "council", "debate", "war room", "múltiplas perspectivas"],
        "agent_hint": "council"
    },
    "dna_extração": {
        "keywords": ["extrair dna", "dna cognitivo", "filosofias", "frameworks", "metodologias"],
        "agent_hint": "extract-dna"
    },
    "processo_inbox": {
        "keywords": ["processar inbox", "processar arquivos", "pipeline", "batch"],
        "agent_hint": "process-inbox"
    }
}


def detect_feedback_signal(response: str) -> Dict:
    """
    Detecta sinais de feedback na resposta do usuário.

    Aprende INDIRETAMENTE - não pergunta se gostou, detecta pelos sinais.
    """
    response_lower = response.lower()

    signals_found = []
    total_score = 0

    for signal, weight in FEEDBACK_SIGNALS.items():
        if signal in response_lower:
            signals_found.append({"signal": signal, "weight": weight})
            total_score += weight

    # Sinal implícito: resposta curta sem reclamação = aceitação
    word_count = len(response.split())
    if word_count < 10 and not signals_found:
        signals_found.append({"signal": "implicit_acceptance", "weight": 5})
        total_score += 5

    # Sinal implícito: resposta muito longa com correções = insatisfação
    if word_count > 50 and any(s["weight"] < 0 for s in signals_found):
        total_score -= 5  # Penalidade adicional

    return {
        "signals": signals_found,
        "total_score": total_score,
        "sentiment": "positive" if total_score > 0 else "negative" if total_score < 0 else "neutral",
        "word_count": word_count
    }


def track_request_pattern(prompt: str) -> Dict:
    """
    Rastreia padrão de request para detecção de skills potenciais.

    Usa scoring baseado em DETECTION-PROTOCOL.md existente.
    """
    pattern_scores = defaultdict(int)
    prompt_lower = prompt.lower()

    matched_keywords = []

    for pattern_name, config in PATTERN_CATEGORIES.items():
        for kw in config["keywords"]:
            if kw in prompt_lower:
                pattern_scores[pattern_name] += 1
                matched_keywords.append({"pattern": pattern_name, "keyword": kw})

    if pattern_scores:
        top_pattern = max(pattern_scores, key=pattern_scores.get)
        return {
            "detected_pattern": top_pattern,
            "score": pattern_scores[top_pattern],
            "all_scores": dict(pattern_scores),
            "matched_keywords": matched_keywords,
            "agent_hint": PATTERN_CATEGORIES.get(top_pattern, {}).get("agent_hint")
        }

    return {
        "detected_pattern": None,
        "score": 0,
        "all_scores": {},
        "matched_keywords": [],
        "agent_hint": None
    }


# ═══════════════════════════════════════════════════════════════════════════
# SKILL SUGGESTION
# ═══════════════════════════════════════════════════════════════════════════

def should_suggest_skill(pattern: str) -> Dict:
    """
    Verifica se deve sugerir criação de skill baseado no padrão.

    Threshold do DETECTION-PROTOCOL: ≥ 3 ocorrências do mesmo padrão.
    """
    # Conta ocorrências recentes do padrão
    recent_count = count_recent_pattern_occurrences(pattern, days=7)

    if recent_count >= SKILL_SUGGESTION_THRESHOLD:
        return {
            "suggest": True,
            "pattern": pattern,
            "occurrences": recent_count,
            "threshold": SKILL_SUGGESTION_THRESHOLD,
            "message": f"Pattern '{pattern}' detected {recent_count} times. Consider creating a skill."
        }

    return {
        "suggest": False,
        "pattern": pattern,
        "occurrences": recent_count,
        "threshold": SKILL_SUGGESTION_THRESHOLD,
        "remaining": SKILL_SUGGESTION_THRESHOLD - recent_count
    }


def count_recent_pattern_occurrences(pattern: str, days: int = 7) -> int:
    """Conta ocorrências recentes de um padrão no log."""
    if not PATTERNS_LOG.exists():
        return 0

    count = 0
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

    try:
        with open(PATTERNS_LOG, "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry.get("timestamp", "2000-01-01")).timestamp()
                    if entry_time >= cutoff and entry.get("pattern") == pattern:
                        count += 1
    except Exception:
        pass

    return count


def create_skill_suggestion(pattern: str, occurrences: int) -> Dict:
    """Cria sugestão de skill para o usuário."""
    suggestion = {
        "suggestion_id": f"SKILL-SUG-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "pattern": pattern,
        "occurrences": occurrences,
        "suggested_name": pattern.replace("_", "-"),
        "suggested_keywords": PATTERN_CATEGORIES.get(pattern, {}).get("keywords", []),
        "status": "pending",
        "created_skill": None
    }

    # Salva sugestão
    SKILL_SUGGESTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(SKILL_SUGGESTIONS_LOG, "a", encoding='utf-8') as f:
            f.write(json.dumps(suggestion, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return suggestion


# ═══════════════════════════════════════════════════════════════════════════
# PREFERENCE LEARNING
# ═══════════════════════════════════════════════════════════════════════════

def learn_preference(feedback_info: Dict, context: str, agent: str = None) -> Dict:
    """
    Aprende preferência baseado no feedback detectado.

    Não pergunta - aprende silenciosamente.
    """
    preference = {
        "timestamp": datetime.now().isoformat(),
        "context_preview": context[:100] if context else "",
        "agent": agent,
        "signals": feedback_info.get("signals", []),
        "sentiment": feedback_info.get("sentiment", "neutral"),
        "score": feedback_info.get("total_score", 0)
    }

    # Extrai aprendizados específicos
    if feedback_info.get("sentiment") == "negative":
        preference["learned"] = extract_negative_learning(feedback_info, context)
    elif feedback_info.get("sentiment") == "positive":
        preference["learned"] = extract_positive_learning(feedback_info, context)
    else:
        preference["learned"] = None

    # Salva preferência
    log_preference(preference)

    return preference


def extract_negative_learning(feedback: Dict, context: str) -> Dict:
    """Extrai aprendizado de feedback negativo."""
    signals = [s["signal"] for s in feedback.get("signals", [])]

    learning = {
        "type": "negative",
        "issues": []
    }

    if "muito resumido" in signals or "incompleto" in signals or "faltou" in signals:
        learning["issues"].append("output_too_short")
        learning["preference"] = "user prefers more detailed outputs"

    if "errado" in signals or "não era isso" in signals:
        learning["issues"].append("misunderstood_request")
        learning["preference"] = "need better request interpretation"

    if "refaça" in signals or "de novo" in signals:
        learning["issues"].append("quality_insufficient")
        learning["preference"] = "user has high quality standards"

    return learning


def extract_positive_learning(feedback: Dict, context: str) -> Dict:
    """Extrai aprendizado de feedback positivo."""
    return {
        "type": "positive",
        "validated": "current approach is working",
        "continue": True
    }


def log_preference(preference: Dict):
    """Loga preferência aprendida."""
    PREFERENCES_LOG.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(PREFERENCES_LOG, "a", encoding='utf-8') as f:
            f.write(json.dumps(preference, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def log_pattern(prompt: str, pattern_info: Dict):
    """Loga padrão detectado."""
    PATTERNS_LOG.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt_preview": prompt[:100] if prompt else "",
        "pattern": pattern_info.get("detected_pattern"),
        "score": pattern_info.get("score", 0),
        "matched_keywords": pattern_info.get("matched_keywords", []),
        "agent_hint": pattern_info.get("agent_hint")
    }

    try:
        with open(PATTERNS_LOG, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

def analyze_prompt(prompt: str) -> Dict:
    """
    Analisa prompt para padrões e retorna contexto enriquecido.

    Interface principal para integração com user_prompt_submit.py
    """
    pattern_info = track_request_pattern(prompt)

    result = {
        "timestamp": datetime.now().isoformat(),
        "pattern": pattern_info,
        "skill_suggestion": None
    }

    # Log pattern
    if pattern_info.get("detected_pattern"):
        log_pattern(prompt, pattern_info)

        # Verifica se deve sugerir skill
        skill_check = should_suggest_skill(pattern_info["detected_pattern"])
        if skill_check.get("suggest"):
            suggestion = create_skill_suggestion(
                pattern_info["detected_pattern"],
                skill_check["occurrences"]
            )
            result["skill_suggestion"] = suggestion

    return result


def analyze_response(user_response: str, original_context: str, agent: str = None) -> Dict:
    """
    Analisa resposta do usuário para feedback implícito.

    Interface para aprendizado de preferências.
    """
    feedback = detect_feedback_signal(user_response)

    result = {
        "timestamp": datetime.now().isoformat(),
        "feedback": feedback
    }

    # Aprende se há sinal claro
    if feedback.get("sentiment") != "neutral":
        preference = learn_preference(feedback, original_context, agent)
        result["preference_learned"] = preference

    return result


# ═══════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════

def get_pattern_statistics(days: int = 30) -> Dict:
    """Retorna estatísticas de padrões detectados."""
    if not PATTERNS_LOG.exists():
        return {"total": 0, "by_pattern": {}}

    stats = defaultdict(int)
    total = 0
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

    try:
        with open(PATTERNS_LOG, "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry.get("timestamp", "2000-01-01")).timestamp()
                    if entry_time >= cutoff:
                        pattern = entry.get("pattern")
                        if pattern:
                            stats[pattern] += 1
                            total += 1
    except Exception:
        pass

    return {
        "total": total,
        "days": days,
        "by_pattern": dict(stats),
        "top_patterns": sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5]
    }


def get_preference_statistics(days: int = 30) -> Dict:
    """Retorna estatísticas de preferências aprendidas."""
    if not PREFERENCES_LOG.exists():
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0}

    stats = {"positive": 0, "negative": 0, "neutral": 0}
    total = 0
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

    try:
        with open(PREFERENCES_LOG, "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry.get("timestamp", "2000-01-01")).timestamp()
                    if entry_time >= cutoff:
                        sentiment = entry.get("sentiment", "neutral")
                        stats[sentiment] = stats.get(sentiment, 0) + 1
                        total += 1
    except Exception:
        pass

    return {
        "total": total,
        "days": days,
        **stats,
        "satisfaction_rate": f"{(stats['positive'] / total * 100):.1f}%" if total > 0 else "N/A"
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "stats":
            print("Pattern Statistics (30 days):")
            stats = get_pattern_statistics()
            print(f"  Total patterns: {stats['total']}")
            print(f"  Top patterns: {stats['top_patterns']}")

            print("\nPreference Statistics (30 days):")
            pref_stats = get_preference_statistics()
            print(f"  Total: {pref_stats['total']}")
            print(f"  Positive: {pref_stats['positive']}")
            print(f"  Negative: {pref_stats['negative']}")
            print(f"  Satisfaction: {pref_stats['satisfaction_rate']}")

        elif command == "test":
            test_prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "me dá um log bonito visual"
            print(f"Testing prompt: {test_prompt}\n")

            result = analyze_prompt(test_prompt)
            print(f"Pattern detected: {result['pattern'].get('detected_pattern')}")
            print(f"Score: {result['pattern'].get('score')}")
            print(f"Agent hint: {result['pattern'].get('agent_hint')}")

            if result.get('skill_suggestion'):
                print(f"\nSkill suggestion: {result['skill_suggestion']}")

        else:
            print("Usage:")
            print("  python pattern_analyzer.py stats          - Show statistics")
            print("  python pattern_analyzer.py test <prompt>  - Test pattern detection")

    else:
        # Demo mode
        print("Pattern Analyzer - Layer 3 Demo\n")

        test_prompts = [
            "me dá um log bonito do Hormozi",
            "qual o ROI do projeto?",
            "compare Cole Gordon com Jeremy Miner",
            "preciso de um playbook de vendas"
        ]

        for prompt in test_prompts:
            result = analyze_prompt(prompt)
            pattern = result['pattern'].get('detected_pattern', 'None')
            score = result['pattern'].get('score', 0)
            print(f"'{prompt[:40]}...' -> Pattern: {pattern}, Score: {score}")
