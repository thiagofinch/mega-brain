#!/usr/bin/env python3
"""
JARVIS-BOARDROOM HOOK
Integração entre Pipeline Jarvis e Boardroom Warfare

Este módulo é chamado ao final do Pipeline Jarvis (Fase 8)
para oferecer a opção de gerar debates em áudio.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Importar gerador de áudio
try:
    from audio_generator import generate_episode_audio, parse_script
    AUDIO_GENERATOR_AVAILABLE = True
except ImportError:
    AUDIO_GENERATOR_AVAILABLE = False

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BOARDROOM_PATH = PROJECT_ROOT / "agents/boardroom"
TEMPLATES_PATH = BOARDROOM_PATH / "templates"
OUTPUTS_PATH = BOARDROOM_PATH / "outputs"
CONFIG_PATH = BOARDROOM_PATH / "config"


# ═══════════════════════════════════════════════════════════════
# DETECÇÃO DE PARTICIPANTES
# ═══════════════════════════════════════════════════════════════

KEYWORD_MAPPING = {
    # Keywords → Agents a convocar
    "comissão": ["COLE_GORDON", "HORMOZI", "CRO", "CFO"],
    "salário": ["COLE_GORDON", "HORMOZI", "CRO", "CFO"],
    "compensação": ["COLE_GORDON", "HORMOZI", "CRO", "CFO"],
    "vendas": ["COLE_GORDON", "HORMOZI", "CRO"],
    "closer": ["COLE_GORDON", "HORMOZI", "CRO"],
    "funil": ["BRUNSON", "HORMOZI", "CMO"],
    "conversão": ["BRUNSON", "HORMOZI", "CMO"],
    "landing": ["BRUNSON", "CMO"],
    "oferta": ["HORMOZI", "BRUNSON", "CRO"],
    "preço": ["HORMOZI", "CFO", "CRO"],
    "valor": ["HORMOZI", "BRUNSON"],
    "marketing": ["BRUNSON", "CMO"],
    "marca": ["BRUNSON", "CMO"],
}


def detect_participants(topic: str, content: str = "") -> Dict[str, List[str]]:
    """
    Detecta quais agentes devem participar do debate com base no tema.

    Returns:
        Dict com 'persons', 'positions', 'council'
    """
    combined_text = f"{topic} {content}".lower()

    persons = set()
    positions = set()

    for keyword, agents in KEYWORD_MAPPING.items():
        if keyword in combined_text:
            for agent in agents:
                if agent in ["HORMOZI", "COLE_GORDON", "BRUNSON"]:
                    persons.add(agent)
                else:
                    positions.add(agent)

    # Garantir mínimo de participantes
    if len(persons) < 2:
        persons.add("HORMOZI")

    if len(positions) < 2:
        positions.add("CRO")
        positions.add("CFO")

    return {
        "persons": list(persons)[:4],  # Max 4 persons
        "positions": list(positions)[:4],  # Max 4 positions
        "council": ["METHODOLOGICAL-CRITIC", "DEVILS-ADVOCATE", "SYNTHESIZER"]
    }


# ═══════════════════════════════════════════════════════════════
# GERAÇÃO DE SCRIPT
# ═══════════════════════════════════════════════════════════════

def generate_episode_script(
    topic: str,
    participants: Dict[str, List[str]],
    context: str = "",
    sources: List[str] = None
) -> str:
    """
    Gera script completo de episódio baseado no tema e participantes.

    Este é um template simplificado - o script real seria gerado
    usando o LLM com os templates da pasta TEMPLATES/.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    episode_id = f"BWE-{datetime.now().year}-{timestamp}"

    # Header do script
    script = f"""# ═══════════════════════════════════════════════════════════════
# BOARDROOM WARFARE
# Episódio: {topic}
# ID: {episode_id}
# Gerado: {datetime.now().isoformat()}
# ═══════════════════════════════════════════════════════════════

## METADADOS

```yaml
episode_id: "{episode_id}"
topic: "{topic}"
participants:
  persons: {json.dumps(participants['persons'])}
  positions: {json.dumps(participants['positions'])}
  council: {json.dumps(participants['council'])}
sources: {json.dumps(sources or [])}
```

---

## SCRIPT

[SOM: Porta de vidro fechando]

### ATO 1: ABERTURA

[NARRADOR]
(tom baixo, sussurrado)
"Sala de reuniões. O tema de hoje: {topic}.

Na mesa: {', '.join(participants['persons'][:2])}.
Executivos: {', '.join(participants['positions'][:2])}.
Observando: o Council.

Vamos observar."

[PAUSA 2 seg]

### ATO 2: CONSTITUIÇÃO

[NARRADOR]
"Antes do debate, a constituição."

[CITADOR]
"Referência: DNA Cognitivo, camada a ser determinada."

[NARRADOR]
"O princípio que guia: a ser inserido baseado no tema."

### ATO 3: DEBATE

[{participants['persons'][0]}]
"[POSIÇÃO INICIAL - a ser gerada com base no DNA do agente]"

"[RESPOSTA/CONTRAPONTO - a ser gerada]"

### ATO 4: EXECUTIVOS

[{participants['positions'][0]}]
"[PERSPECTIVA DO CARGO]"

[{participants['positions'][1] if len(participants['positions']) > 1 else 'CFO'}]
"[CONTRAPONTO]"

### ATO 5: COUNCIL

[SYNTHESIZER]
"Vou pedir uma pausa. Temos divergência. Critic?"

[METHODOLOGICAL-CRITIC]
"[QUESTIONAMENTO DE PREMISSA]"

[DEVILS-ADVOCATE]
"[CENÁRIO DE RISCO]"

[SYNTHESIZER]
"Minha síntese: [A SER GERADA]"

### ATO 6: RESOLUÇÃO

[SYNTHESIZER]
"Proposta final: [A SER GERADA]

SCORING:
- Viabilidade: X/10
- Impacto: X/10
- Risco: X/10

Score final: X.X"

### ATO 7: PERGUNTA

[NARRADOR]
"E você?

[PERGUNTA PROVOCATIVA RELACIONADA AO TEMA]

Essa é a pergunta que fica."

[SOM: Porta abrindo]

[NARRADOR]
"Até o próximo episódio de Boardroom Warfare."

# ═══════════════════════════════════════════════════════════════
# FIM DO EPISÓDIO
# ═══════════════════════════════════════════════════════════════
"""

    return script


# ═══════════════════════════════════════════════════════════════
# HOOK PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def boardroom_hook(
    pipeline_outputs: List[Dict],
    auto_prompt: bool = True
) -> Optional[Path]:
    """
    Hook chamado ao final do Pipeline Jarvis.

    Args:
        pipeline_outputs: Lista de outputs do pipeline
            [{"type": "playbook", "title": "...", "path": "..."}, ...]
        auto_prompt: Se True, pergunta ao usuário

    Returns:
        Path do áudio gerado ou None
    """

    if not pipeline_outputs:
        return None

    # ─────────────────────────────────────────────────────────────
    # PROMPT AO USUÁRIO
    # ─────────────────────────────────────────────────────────────

    print("\n" + "═" * 60)
    print("📋 PROCESSAMENTO CONCLUÍDO")
    print("═" * 60)
    print("\nOutputs gerados:")
    for i, output in enumerate(pipeline_outputs, 1):
        print(f"  {i}. [{output.get('type', 'unknown')}] {output.get('title', 'Sem título')}")

    print("\n" + "─" * 60)
    print("🎬 BOARDROOM WARFARE")
    print("─" * 60)
    print("\nDeseja gerar episódio de debate para algum output?")
    print("\n[1] SIM - Selecionar tema para debate")
    print("[2] NÃO - Finalizar processamento")

    if not auto_prompt:
        return None

    choice = input("\nSua escolha: ").strip()

    if choice != "1":
        print("\n✅ Processamento finalizado sem debate.")
        return None

    # ─────────────────────────────────────────────────────────────
    # SELEÇÃO DE TEMA
    # ─────────────────────────────────────────────────────────────

    print("\nSelecione o output para debate:")
    for i, output in enumerate(pipeline_outputs, 1):
        print(f"  [{i}] {output.get('title', 'Sem título')}")

    try:
        selection = int(input("\nNúmero: ").strip()) - 1
        selected = pipeline_outputs[selection]
    except (ValueError, IndexError):
        print("❌ Seleção inválida.")
        return None

    topic = selected.get('title', 'Tema do debate')
    content = selected.get('content', '')

    # ─────────────────────────────────────────────────────────────
    # DETECÇÃO DE PARTICIPANTES
    # ─────────────────────────────────────────────────────────────

    participants = detect_participants(topic, content)

    print(f"\n🎭 Participantes detectados:")
    print(f"   Experts: {', '.join(participants['persons'])}")
    print(f"   Executivos: {', '.join(participants['positions'])}")
    print(f"   Council: {', '.join(participants['council'])}")

    confirm = input("\nConfirmar participantes? [S/n]: ").strip().lower()
    if confirm == 'n':
        # TODO: Permitir customização
        print("⚠️ Customização de participantes ainda não implementada.")

    # ─────────────────────────────────────────────────────────────
    # GERAÇÃO DO SCRIPT
    # ─────────────────────────────────────────────────────────────

    print("\n📝 Gerando script do episódio...")

    script = generate_episode_script(
        topic=topic,
        participants=participants,
        context=content,
        sources=[selected.get('path', '')]
    )

    # Salvar script
    script_filename = f"BWE-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    script_path = OUTPUTS_PATH / "scripts" / script_filename
    script_path.parent.mkdir(parents=True, exist_ok=True)

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script)

    print(f"   ✅ Script salvo: {script_path}")

    # ─────────────────────────────────────────────────────────────
    # PROMPT PARA NARRAÇÃO
    # ─────────────────────────────────────────────────────────────

    print("\n" + "─" * 60)
    print("🎧 NARRAÇÃO")
    print("─" * 60)
    print("\nDeseja iniciar a narração do debate?")
    print("\n[SIM] - Gerar áudio agora")
    print("[NÃO] - Apenas salvar script")

    narrate = input("\nSua escolha: ").strip().upper()

    if narrate != "SIM":
        print(f"\n✅ Script salvo em: {script_path}")
        print("   Para gerar áudio depois:")
        print(f"   python audio_generator.py {script_path}")
        return script_path

    # ─────────────────────────────────────────────────────────────
    # GERAÇÃO DE ÁUDIO
    # ─────────────────────────────────────────────────────────────

    if not AUDIO_GENERATOR_AVAILABLE:
        print("\n⚠️ audio_generator não disponível.")
        print(f"   Script salvo em: {script_path}")
        return script_path

    print("\n🔊 Iniciando geração de áudio...")

    try:
        audio_path = generate_episode_audio(script_path)

        print("\n" + "═" * 60)
        print("✅ EPISÓDIO GERADO COM SUCESSO")
        print("═" * 60)
        print(f"\n📁 Script: {script_path}")
        print(f"🎧 Áudio: {audio_path}")
        print(f"\n🔗 Para ouvir agora:")
        print(f"   open {audio_path}  # Mac")
        print(f"   xdg-open {audio_path}  # Linux")
        print("═" * 60)

        return audio_path

    except Exception as e:
        print(f"\n❌ Erro ao gerar áudio: {e}")
        print(f"   Script salvo em: {script_path}")
        return script_path


# ═══════════════════════════════════════════════════════════════
# INTEGRAÇÃO DIRETA COM JARVIS
# ═══════════════════════════════════════════════════════════════

def integrate_with_jarvis_pipeline():
    """
    Função para ser importada pelo jarvis_pipeline.py

    Adicione ao final da Fase 8 do Pipeline Jarvis:

    from boardroom.jarvis_boardroom_hook import boardroom_hook

    # No final da fase 8:
    boardroom_hook(pipeline_outputs)
    """
    pass


if __name__ == "__main__":
    # Teste standalone
    test_outputs = [
        {
            "type": "playbook",
            "title": "Estrutura de Comissão para Time de Vendas",
            "path": "04-PLAYBOOK/PLAYBOOK-COMISSAO.md",
            "content": "Playbook sobre estrutura de comissão, closer, vendas high-ticket"
        },
        {
            "type": "dossier",
            "title": "Dossiê Cole Gordon - Vendas",
            "path": "03-KNOWLEDGE/dossiers/DOSSIE-COLE-GORDON.md",
            "content": "Dossiê sobre Cole Gordon e suas metodologias de vendas"
        }
    ]

    boardroom_hook(test_outputs)
