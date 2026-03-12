#!/usr/bin/env python3
"""
BOARDROOM WARFARE → NOTEBOOKLM INTEGRATION
Gera documentos otimizados para Audio Overview do Google NotebookLM

Este script substitui a integração com ElevenLabs TTS.
Os arquivos são salvos em /mnt/user-data/outputs/ (ou pasta configurada)
para upload manual no NotebookLM.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════

# Pasta padrão de outputs (Windows)
DEFAULT_OUTPUT_PATH = r"./output"

@dataclass
class NotebookLMConfig:
    """Configuração da integração NotebookLM"""
    output_path: str = DEFAULT_OUTPUT_PATH
    subfolder: str = "NOTEBOOKLM"  # Subpasta para organizar
    filename_format: str = "DEBATE-{tema}-{timestamp}.md"


# ═══════════════════════════════════════════════════════════════
# ESTRUTURAS DE DADOS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Participant:
    """Participante do debate"""
    name: str
    specialty: str
    position: str
    arguments: List[str]
    quote: str
    source: str


@dataclass
class Conflict:
    """Ponto de conflito"""
    description: str
    side_a: str
    side_a_position: str
    side_b: str
    side_b_position: str


@dataclass
class CouncilAnalysis:
    """Análise do Council"""
    central_question: str
    consensus_points: List[str]
    methodological_questions: List[str]
    risk_scenarios: List[str]
    synthesis: str
    scoring: Dict[str, int]
    followup_question: str


@dataclass
class DebateContent:
    """Conteúdo completo do debate"""
    title: str
    context: str
    participants: List[Participant]
    conflicts: List[Conflict]
    council: CouncilAnalysis
    sources: List[str]
    final_question: str
    dna_principles: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# GERADOR DE DOCUMENTO
# ═══════════════════════════════════════════════════════════════

def generate_notebooklm_document(debate: DebateContent) -> str:
    """
    Gera documento markdown otimizado para NotebookLM Audio Overview.
    
    O formato é estruturado para que os hosts do NotebookLM:
    - Entendam o contexto rapidamente
    - Assumam as perspectivas dos participantes
    - Debatam os pontos de conflito naturalmente
    - Concluam com a síntese e pergunta
    """
    
    doc = f"""# 🎙️ DEBATE: {debate.title}

> **Contexto para geração de podcast:** Este documento estrutura um debate 
> entre especialistas em negócios sobre {debate.title.lower()}. Os hosts 
> devem apresentar as diferentes perspectivas, debater os conflitos, e 
> concluir com a síntese do Council e a pergunta final ao ouvinte.

---

## 📋 O PROBLEMA

{debate.context}

**Pergunta central:** {debate.council.central_question}

"""

    # DNA/Constituição (se houver)
    if debate.dna_principles:
        doc += """---

## 📜 PRINCÍPIOS CONSTITUCIONAIS (DNA)

Antes do debate, os princípios que guiam a análise:

"""
        for i, principle in enumerate(debate.dna_principles, 1):
            doc += f"{i}. {principle}\n"
        doc += "\n"

    # Participantes
    doc += """---

## 🎭 AS PERSPECTIVAS EM CONFLITO

"""
    
    for i, p in enumerate(debate.participants, 1):
        doc += f"""### {p.name}
**Especialidade:** {p.specialty}

**Posição central:** {p.position}

**Argumentos:**
"""
        for j, arg in enumerate(p.arguments, 1):
            doc += f"- {arg}\n"
        
        doc += f"""
**Frase característica:** *"{p.quote}"*

**Fonte:** {p.source}

---

"""

    # Conflitos
    doc += """## ⚔️ OS PONTOS DE TENSÃO

"""
    for i, c in enumerate(debate.conflicts, 1):
        doc += f"""### Conflito {i}: {c.description}

| {c.side_a} | vs | {c.side_b} |
|------------|:--:|------------|
| {c.side_a_position} | ⚡ | {c.side_b_position} |

"""

    # Consensos
    doc += """---

## 🤝 ONDE TODOS CONCORDAM

"""
    for point in debate.council.consensus_points:
        doc += f"- {point}\n"

    # Council
    doc += f"""

---

## ⚖️ ANÁLISE DO COUNCIL

### O Crítico Metodológico questiona:
"""
    for q in debate.council.methodological_questions:
        doc += f'- *"{q}"*\n'

    doc += """
### O Advogado do Diabo alerta:
"""
    for r in debate.council.risk_scenarios:
        doc += f'- *"{r}"*\n'

    doc += f"""
### Síntese Final:

> {debate.council.synthesis}

**Avaliação:**
"""
    total = 0
    for metric, score in debate.council.scoring.items():
        doc += f"- {metric}: **{score}/10**\n"
        total += score
    
    avg = total / len(debate.council.scoring)
    doc += f"\n**Score Final: {avg:.1f}/10**\n"

    # Fontes
    doc += """
---

## 📚 FONTES CITADAS

"""
    for source in debate.sources:
        doc += f"- {source}\n"

    # Pergunta final
    doc += f"""
---

## ❓ A PERGUNTA QUE FICA

> **{debate.final_question}**

{debate.council.followup_question}

---

## 🎧 NOTAS PARA O PODCAST

**Estrutura sugerida:**
1. Abrir contextualizando o problema (2 min)
2. Apresentar as perspectivas conflitantes (5 min)
3. Debater os pontos de tensão (8 min)
4. Trazer a análise do Council (3 min)
5. Fechar com a pergunta ao ouvinte (2 min)

**Tom:** Profissional mas acessível. Momentos de tensão são bem-vindos.

**Duração ideal:** 15-25 minutos
"""
    
    return doc


# ═══════════════════════════════════════════════════════════════
# SALVAMENTO
# ═══════════════════════════════════════════════════════════════

def save_document(content: str, tema: str, config: NotebookLMConfig = None) -> Path:
    """
    Salva o documento na pasta de outputs.
    
    Returns:
        Path do arquivo salvo
    """
    if config is None:
        config = NotebookLMConfig()
    
    # Criar pasta se necessário
    output_dir = Path(config.output_path) / config.subfolder
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Nome do arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tema_slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in tema)
    tema_slug = tema_slug.replace(" ", "-").lower()[:40]
    filename = f"DEBATE-{tema_slug}-{timestamp}.md"
    
    # Salvar
    filepath = output_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


# ═══════════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def create_notebooklm_debate(
    tema: str,
    contexto: str,
    participantes: List[Dict],
    conflitos: List[Dict],
    council_data: Dict,
    fontes: List[str],
    pergunta_final: str,
    principios_dna: List[str] = None
) -> Path:
    """
    Função principal para criar debate para NotebookLM.
    
    Args:
        tema: Título do debate
        contexto: Descrição do problema/situação
        participantes: Lista de dicts com dados dos participantes
        conflitos: Lista de dicts com pontos de conflito
        council_data: Dict com análise do council
        fontes: Lista de fontes citadas
        pergunta_final: Pergunta provocativa final
        principios_dna: Lista de princípios do DNA (opcional)
    
    Returns:
        Path do arquivo salvo
    """
    
    # Construir objetos
    participants = [
        Participant(
            name=p["name"],
            specialty=p.get("specialty", ""),
            position=p.get("position", ""),
            arguments=p.get("arguments", []),
            quote=p.get("quote", ""),
            source=p.get("source", "")
        )
        for p in participantes
    ]
    
    conflicts = [
        Conflict(
            description=c["description"],
            side_a=c.get("side_a", ""),
            side_a_position=c.get("side_a_position", ""),
            side_b=c.get("side_b", ""),
            side_b_position=c.get("side_b_position", "")
        )
        for c in conflitos
    ]
    
    council = CouncilAnalysis(
        central_question=council_data.get("central_question", f"Qual a melhor abordagem para {tema}?"),
        consensus_points=council_data.get("consensus", []),
        methodological_questions=council_data.get("questions", []),
        risk_scenarios=council_data.get("risks", []),
        synthesis=council_data.get("synthesis", ""),
        scoring=council_data.get("scoring", {}),
        followup_question=council_data.get("followup", "")
    )
    
    debate = DebateContent(
        title=tema,
        context=contexto,
        participants=participants,
        conflicts=conflicts,
        council=council,
        sources=fontes,
        final_question=pergunta_final,
        dna_principles=principios_dna or []
    )
    
    # Gerar documento
    document = generate_notebooklm_document(debate)
    
    # Salvar
    filepath = save_document(document, tema)
    
    return filepath


def print_success_message(filepath: Path):
    """Imprime mensagem de sucesso com instruções."""
    
    print("\n" + "═" * 65)
    print("✅ DOCUMENTO PRONTO PARA NOTEBOOKLM!")
    print("═" * 65)
    print(f"\n📁 Arquivo salvo em:\n   {filepath}")
    print("\n" + "─" * 65)
    print("📋 PRÓXIMOS PASSOS:")
    print("─" * 65)
    print("   1. Abra: notebooklm.google.com")
    print("   2. Crie um novo Notebook")
    print("   3. Clique em 'Add source' → Upload")
    print("   4. Selecione o arquivo acima")
    print("   5. Clique em 'Audio Overview' (ícone de fone)")
    print("   6. Aguarde ~2-5 minutos")
    print("\n🎧 O Google gerará um podcast de alta qualidade!")
    print("   - Vozes naturais com emoção")
    print("   - Risadas e expressões espontâneas") 
    print("   - Pronúncia correta (B2B → 'B two B')")
    print("   - Diálogo fluido e envolvente")
    print("═" * 65 + "\n")


# ═══════════════════════════════════════════════════════════════
# HOOK PARA PIPELINE JARVIS
# ═══════════════════════════════════════════════════════════════

def boardroom_notebooklm_hook(pipeline_outputs: List[Dict]) -> Optional[Path]:
    """
    Hook chamado ao final do Pipeline Jarvis.
    Substitui o hook anterior que usava ElevenLabs.
    
    Args:
        pipeline_outputs: Lista de outputs do pipeline
        
    Returns:
        Path do arquivo gerado ou None
    """
    
    if not pipeline_outputs:
        return None
    
    print("\n" + "═" * 65)
    print("📋 PROCESSAMENTO CONCLUÍDO")
    print("═" * 65)
    print("\nOutputs disponíveis:")
    for i, output in enumerate(pipeline_outputs, 1):
        print(f"   {i}. [{output.get('type', '?')}] {output.get('title', 'Sem título')}")
    
    print("\n" + "─" * 65)
    print("🎙️ BOARDROOM WARFARE → NOTEBOOKLM")
    print("─" * 65)
    print("\nDeseja gerar documento de debate para podcast?")
    print("\n   [1] SIM - Criar documento para NotebookLM")
    print("   [2] NÃO - Finalizar")
    
    choice = input("\nEscolha: ").strip()
    
    if choice != "1":
        print("\n✅ Finalizado sem gerar debate.")
        return None
    
    # Seleção de output
    print("\nQual output usar como base do debate?")
    try:
        selection = int(input("Número: ").strip()) - 1
        selected = pipeline_outputs[selection]
    except (ValueError, IndexError):
        print("❌ Seleção inválida.")
        return None
    
    # Aqui entraria a lógica de detecção de participantes
    # e montagem do debate baseado no output selecionado
    # Por enquanto, retorna placeholder
    
    print("\n⚙️ Gerando documento...")
    
    # TODO: Integrar com DNA, detectar participantes, etc.
    # Por enquanto, usar dados de exemplo
    
    return None  # Será implementado com integração completa


# ═══════════════════════════════════════════════════════════════
# TESTE / EXEMPLO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Exemplo de uso com debate sobre comissão de vendas"""
    
    filepath = create_notebooklm_debate(
        tema="Estrutura de Comissão para Time de Vendas B2B",
        
        contexto="""
Uma empresa de SaaS B2B com faturamento de 8 dígitos está enfrentando 
alta rotatividade no time de vendas. Os melhores closers estão saindo 
para concorrentes que oferecem comissões mais agressivas. 

O CEO precisa decidir: ajustar a estrutura de compensação ou manter 
o modelo atual e focar em outros fatores de retenção?

O time atual tem 12 closers, com ticket médio de R$ 45.000 e ciclo 
de vendas de 45 dias. A comissão atual é 8% flat.
        """,
        
        participantes=[
            {
                "name": "Alex Hormozi",
                "specialty": "Escala e aquisição de empresas",
                "position": "Comissão agressiva de 15% sem teto para atrair e reter os melhores",
                "arguments": [
                    "Os melhores vendedores querem upside ilimitado - teto é insulto",
                    "Se você preocupa com quanto vai pagar, está pensando pequeno",
                    "Vendedor caro que performa vale 10x o que custa",
                    "No his gym business, pagar mais atraiu os melhores do mercado"
                ],
                "quote": "Isso é coisa de pobre. Se o cara te faz ganhar 1 milhão, qual o problema de pagar 150 mil pra ele?",
                "source": "Offers Framework + Hormozi Podcast"
            },
            {
                "name": "Cole Gordon", 
                "specialty": "Sistemas de vendas high-ticket",
                "position": "Modelo híbrido com base sólida + variável + acelerador acima da meta",
                "arguments": [
                    "Comissão sem teto cria imprevisibilidade financeira perigosa",
                    "Vendedor bom em sistema ruim perde para vendedor médio em sistema bom",
                    "Base forte dá segurança, variável motiva, acelerador explode resultados",
                    "Em 300+ closers treinados, o híbrido teve 40% menos turnover"
                ],
                "quote": "Qual é o processo? Se não é sistemático, não escala. Ponto.",
                "source": "Cole Gordon + Remote Closing Methods"
            },
            {
                "specialty": "Gestão empresarial no contexto brasileiro",
                "position": "Qualquer modelo precisa considerar CLT e a realidade operacional local",
                "arguments": [
                    "Mudança de comissão sem acordo formal gera passivo trabalhista",
                    "O que funciona nos EUA não replica automaticamente no Brasil",
                    "Foco na execução - quem vai fazer isso funcionar todo dia?",
                    "Em 500 empresas analisadas, 70% dos problemas são de gestão, não de comissão"
                ],
                "quote": "Isso é papo de gringo. E a CLT? Quem vai assinar o distrato? Quem treina os novos?",
            }
        ],
        
        conflitos=[
            {
                "description": "Agressividade vs. Previsibilidade Financeira",
                "side_a": "Hormozi",
                "side_a_position": "Pagar muito para os melhores é investimento com ROI garantido",
                "side_b": "Cole Gordon + CFO",
                "side_b_position": "Precisa ser previsível para escalar sem quebrar o caixa"
            },
            {
                "description": "Modelo Americano vs. Realidade Brasileira",
                "side_a": "Hormozi + Cole",
                "side_a_position": "Os princípios são universais, só adaptar a execução",
                "side_b_position": "CLT, cultura e mercado brasileiro exigem modelo próprio"
            },
            {
                "description": "Otimizar para Excepcional vs. Otimizar para Sistema",
                "side_a": "Hormozi",
                "side_a_position": "Foque nos 20% excepcionais, o resto que vá embora",
                "side_b": "Cole Gordon",
                "side_b_position": "Sistema bom eleva a média e retém os bons por mais tempo"
            }
        ],
        
        council_data={
            "central_question": "Qual estrutura de comissão retém os melhores closers sem comprometer a saúde financeira da empresa?",
            "consensus": [
                "Vendedores excepcionais merecem remuneração excepcional",
                "O modelo atual de 8% flat está abaixo do mercado",
                "Qualquer mudança precisa de validação jurídica antes",
                "Problema pode não ser só comissão - precisa investigar"
            ],
            "questions": [
                "Estamos assumindo que o problema é comissão. Qual a evidência concreta?",
                "Os que saíram foram por dinheiro ou por gestão/ambiente?",
                "Se aumentarmos comissão, não vamos reter os medíocres também?"
            ],
            "risks": [
                "Aumentar comissão pode reter os vendedores errados - os bons saem por outros motivos",
                "Mudança abrupta sem acordo pode gerar 12 processos trabalhistas",
                "Modelo muito agressivo pode atrair mercenários sem fit cultural"
            ],
            "synthesis": "Implementar em duas fases: Fase 1 (90 dias) - avaliar o time atual com critérios claros, desligar bottom 20% com acordo, e recrutar 3 novos já no modelo novo. Fase 2 - implementar estrutura híbrida: R$ 5.000 base, 10% comissão, 15% acelerador acima de 120% da meta. Migrar os atuais com aceite formal documentado.",
            "scoring": {
                "Viabilidade": 8,
                "Impacto em Retenção": 8,
                "Risco Jurídico": 7,
                "Alinhamento Estratégico": 9
            },
            "followup": "E se você limpasse o time essa semana, teria coragem de dobrar a comissão dos que ficassem?"
        },
        
        fontes=[
            "**Offers Framework** (Alex Hormozi) - Conceito de oferta irresistível e valor percebido",
            "**Cole Gordon** (Cole Gordon) - Estrutura híbrida de compensação para high-ticket",
            "**DNA Cognitivo** - Princípio de alinhamento de incentivos individuais e coletivos"
        ],
        
        pergunta_final="Quantos vendedores medíocres você está pagando para ficarem confortáveis sendo medíocres?",
        
        principios_dna=[
            "Compensação deve alinhar incentivos individuais com resultados coletivos",
            "Vendedor bem pago que não performa é custo; vendedor mal pago que performa é risco",
            "A proporção fixo/variável deve refletir o controle sobre o resultado"
        ]
    )
    
    print_success_message(filepath)
