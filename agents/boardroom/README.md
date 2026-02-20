# BOARDROOM WARFARE
## Sistema de Debates em Áudio com Agentes IA

---

## Visão Geral

O **Boardroom Warfare** transforma decisões de negócio em episódios de debate imersivos em áudio. Digital twins de experts reconhecidos (Hormozi, Cole Gordon, etc.) debatem questões estratégicas, com avaliação do Council e síntese final.

```
┌─────────────────────────────────────────────────────────────────────┐
│  📥 INPUT                                                           │
│  └─ Tema/questão do Pipeline Jarvis ou input manual                │
│                                                                     │
│  🎭 DEBATE                                                          │
│  └─ Agents of Person + Agents of Position confrontam perspectivas  │
│                                                                     │
│  ⚖️ COUNCIL                                                         │
│  └─ Critic + Advocate + Synthesizer avaliam e pontuam              │
│                                                                     │
│  🎧 OUTPUT                                                          │
│  └─ Script .md + Áudio .mp3 com múltiplas vozes                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Pastas

```
agents/boardroom/
├── CONFIG/                        # Configurações do sistema
│   ├── BOARDROOM-CONFIG.md        # Config geral e regras
│   ├── VOICE-PROFILES.md          # Perfis de voz dos agentes
│   ├── TTS-INTEGRATION.md         # Integração com ElevenLabs
│   └── voice_mapping.json         # Mapeamento voice_id → agente
│
├── TEMPLATES/                     # Templates de episódio
│   ├── EPISODE-TEMPLATE.md        # Estrutura completa de episódio
│   └── SCENE-TEMPLATES/           # Templates de cenas
│       ├── SCENE-DNA-CONSULTATION.md  # Consulta à Constituição
│       ├── SCENE-AGENT-DEBATE.md      # Debate entre experts
│       ├── SCENE-COUNCIL.md           # Deliberação do Council
│       └── SCENE-QUESTION.md          # Pergunta final ao ouvinte
│
├── scripts/                       # Scripts Python
│   ├── audio_generator.py         # Gerador de áudio (ElevenLabs)
│   └── jarvis_boardroom_hook.py   # Hook de integração com Jarvis
│
├── OUTPUTS/                       # Arquivos gerados
│   ├── scripts/                   # Scripts .md gerados
│   ├── AUDIO/                     # Arquivos .mp3 finais
│   └── temp/                      # Arquivos temporários
│
├── WORKFLOWS/                     # Guias de workflow
│   └── WORKFLOW-AUDIO-GENERATION.md
│
├── README.md                      # Este arquivo
├── INTEGRATION-GUIDE.md           # Guia de integração
└── CHECKLIST-MASTER.md            # Checklist de implementação
```

---

## Agentes do Sistema

### Agents of Person (Digital Twins)

| Agente | Especialidade | Gatilhos |
|--------|---------------|----------|
| **HORMOZI** | Escala, agressividade, "pensar grande" | escala, crescimento, oferta, preço |
| **COLE_GORDON** | Sistemas de vendas, processos | vendas, closer, time, processo |
| **BRUNSON** | Funis, copy, marketing | funil, conversão, landing, marketing |

### Agents of Position (Executivos)

| Agente | Papel | Gatilhos |
|--------|-------|----------|
| **CRO** | Revenue, vendas | vendas, escala, crescimento |
| **CFO** | Finanças, viabilidade | comissão, salário, preço |
| **CMO** | Marketing, marca | funil, marketing, marca |
| **COO** | Operações, execução | time, processo, operação |

### Council (Avaliadores)

| Agente | Função |
|--------|--------|
| **SYNTHESIZER** | Sintetiza posições, propõe resolução, consolida scoring |
| **METHODOLOGICAL-CRITIC** | Questiona premissas e metodologia |
| **DEVILS-ADVOCATE** | Ataca posição dominante, expõe riscos |

---

## Estrutura de Episódio (7 Atos)

```
ATO 1: ABERTURA
└─ Narrador introduz tema e participantes

ATO 2: CONSTITUIÇÃO
└─ Citador lê princípio do DNA Cognitivo relevante

ATO 3: DEBATE
└─ Agents of Person confrontam perspectivas (mín. 3 rodadas)

ATO 4: EXECUTIVOS
└─ Agents of Position trazem perspectiva de cargo

ATO 5: COUNCIL
└─ Critic questiona → Advocate ataca → Synthesizer sintetiza

ATO 6: RESOLUÇÃO
└─ Proposta final com scoring (5 dimensões × /10)

ATO 7: PERGUNTA
└─ Narrador faz pergunta provocativa ao ouvinte
```

---

## Scoring do Council

| Dimensão | Descrição |
|----------|-----------|
| **Viabilidade** | Implementável no contexto atual? |
| **Impacto** | Qual o potencial de resultado? |
| **Risco** | Quais os riscos envolvidos? |
| **Alinhamento** | Conecta com objetivos maiores? |
| **Timing** | É o momento certo? |

**Score Final**: Média das 5 dimensões (0-10)

| Score | Classificação |
|-------|---------------|
| 9.0+ | EXCELENTE |
| 8.0-8.9 | MUITO BOM |
| 7.0-7.9 | BOM |
| 6.0-6.9 | ACEITÁVEL |
| <6.0 | REVISAR |

---

## Formato do Script

```markdown
[PERSONAGEM]
(instrução de tom/emoção)
"Texto da fala"

[SOM: descrição do efeito sonoro]

[PAUSA X seg]

[CITADOR]
"Referência: fonte específica."
```

---

## Quick Start

### 1. Via Pipeline Jarvis (Automático)

O hook é chamado automaticamente ao final da Fase 8 do Pipeline Jarvis:

```python
from boardroom.jarvis_boardroom_hook import boardroom_hook

# No final da fase 8:
boardroom_hook(pipeline_outputs)
```

### 2. Via CLI (Manual)

```bash
# Gerar áudio a partir de script existente
python scripts/audio_generator.py OUTPUTS/scripts/episodio.md

# Modo dry-run (apenas parse)
python scripts/audio_generator.py episodio.md --dry-run

# Especificar output
python scripts/audio_generator.py episodio.md --output meu_audio.mp3
```

### 3. Via Prompt Interativo

Após processar material no Pipeline Jarvis, o sistema pergunta:

```
📋 PROCESSAMENTO CONCLUÍDO
═══════════════════════════════════════════════════════════

🎬 BOARDROOM WARFARE
───────────────────────────────────────────────────────────

Deseja gerar episódio de debate para algum output?

[1] SIM - Selecionar tema para debate
[2] NÃO - Finalizar processamento
```

---

## Requisitos

### Dependências Python

```bash
pip install elevenlabs pydub
```

### Variáveis de Ambiente

```bash
export ELEVENLABS_API_KEY=your_key_here
```

### Configuração de Vozes

Editar `CONFIG/voice_mapping.json` com os voice_ids da sua conta ElevenLabs.

---

## Arquivos de Referência

| Arquivo | Propósito |
|---------|-----------|
| [INTEGRATION-GUIDE.md](INTEGRATION-GUIDE.md) | Como integrar com outros sistemas |
| [CHECKLIST-MASTER.md](CHECKLIST-MASTER.md) | Checklist de implementação |
| [CONFIG/VOICE-PROFILES.md](CONFIG/VOICE-PROFILES.md) | Perfis detalhados de cada voz |
| [TEMPLATES/EPISODE-TEMPLATE.md](TEMPLATES/EPISODE-TEMPLATE.md) | Template completo de episódio |

---

## Versão

**v1.0.0** - Sistema inicial com integração Jarvis + ElevenLabs TTS
