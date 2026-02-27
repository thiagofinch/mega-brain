# BOARDROOM WARFARE - Guia de Integração
## Como integrar o sistema de debates com outros componentes

---

## 1. Integração com Pipeline Jarvis

### Ponto de Integração

O Boardroom Warfare se conecta ao Pipeline Jarvis na **Fase 8** (Finalização).

```
Pipeline Jarvis
│
├── Fase 1-7: Processamento normal
│
└── Fase 8: Finalização
    │
    └── 8.X: BOARDROOM HOOK ← Ponto de integração
        │
        ├── Detecta participantes relevantes
        ├── Gera script de debate
        └── Oferece opção de narração
```

### Como Ativar

No arquivo `jarvis_pipeline.py` ou equivalente, adicione ao final da Fase 8:

```python
from boardroom.jarvis_boardroom_hook import boardroom_hook

# Ao final da fase 8, após todos os outputs:
pipeline_outputs = [
    {
        "type": "playbook",
        "title": "Estrutura de Comissão para Time de Vendas",
        "path": "knowledge/playbooks/PLAYBOOK-COMISSAO.md",
        "content": "Conteúdo do playbook..."
    },
    {
        "type": "dossier",
        "title": "Dossiê Cole Gordon",
        "path": "knowledge/dossiers/persons/DOSSIER-COLE-GORDON.md",
        "content": "Conteúdo do dossiê..."
    }
]

# Chamar o hook
boardroom_hook(pipeline_outputs, auto_prompt=True)
```

### Formato do Output Esperado

```python
pipeline_outputs = [
    {
        "type": str,      # "playbook", "dossier", "source", etc.
        "title": str,     # Título do output
        "path": str,      # Caminho do arquivo gerado
        "content": str    # Conteúdo para análise de keywords (opcional)
    }
]
```

---

## 2. Detecção Automática de Participantes

### Mapeamento de Keywords

O sistema usa keywords para detectar quais agentes devem participar:

```python
KEYWORD_MAPPING = {
    # Tema → Agentes relevantes
    "comissão": ["COLE_GORDON", "HORMOZI", "CRO", "CFO"],
    "salário": ["COLE_GORDON", "HORMOZI", "CRO", "CFO"],
    "vendas": ["COLE_GORDON", "HORMOZI", "CRO"],
    "closer": ["COLE_GORDON", "HORMOZI", "CRO"],
    "funil": ["BRUNSON", "HORMOZI", "CMO"],
    "conversão": ["BRUNSON", "HORMOZI", "CMO"],
    "oferta": ["HORMOZI", "BRUNSON", "CRO"],
    "preço": ["HORMOZI", "CFO", "CRO"],
    "marketing": ["BRUNSON", "CMO"],
}
```

### Customização

Para adicionar novos mapeamentos, edite `scripts/jarvis_boardroom_hook.py`:

```python
# Adicionar novo mapeamento
KEYWORD_MAPPING["seu_tema"] = ["AGENT_1", "AGENT_2", "POSITION_1"]
```

### API de Detecção

```python
from boardroom.jarvis_boardroom_hook import detect_participants

participants = detect_participants(
    topic="Estrutura de comissão para closers",
    content="Texto adicional para análise..."
)

# Retorna:
{
    "persons": ["COLE_GORDON", "HORMOZI"],      # Max 4
    "positions": ["CRO", "CFO"],                 # Max 4
    "council": ["METHODOLOGICAL-CRITIC", "DEVILS-ADVOCATE", "SYNTHESIZER"]
}
```

---

## 3. Integração com ElevenLabs TTS

### Configuração Inicial

1. **Obter API Key**: Criar conta em [elevenlabs.io](https://elevenlabs.io)

2. **Configurar variável de ambiente**:
```bash
export ELEVENLABS_API_KEY=your_api_key_here
```

3. **Mapear vozes**: Editar `CONFIG/voice_mapping.json`:
```json
{
    "NARRATOR": {
        "voice_id": "seu_voice_id_aqui",
        "settings": {
            "stability": 0.7,
            "similarity_boost": 0.8,
            "style": 0.3
        }
    },
    "HORMOZI": {
        "voice_id": "seu_voice_id_aqui",
        "settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.6
        }
    }
}
```

### Modelo Utilizado

O sistema usa `eleven_multilingual_v2` para suporte a português:

```python
audio = generate(
    text=segment.text,
    voice=Voice(
        voice_id=voice_config["voice_id"],
        settings=VoiceSettings(...)
    ),
    model="eleven_multilingual_v2"
)
```

### Fallback de Vozes

Se uma voz não está configurada, o sistema usa NARRATOR como fallback:

```python
voice_config = voice_mapping.get(speaker_key)
if not voice_config:
    voice_config = voice_mapping.get("NARRATOR")
```

---

## 4. Integração com DNA Cognitivo

### Consultando o DNA

Os agentes devem consultar seu DNA antes de gerar posições:

```
DNA Cognitivo (knowledge/dna/persons/{PESSOA}/)
│
├── CONFIG.yaml      → Metadados e fontes
├── PRINCIPIOS.yaml  → Princípios fundamentais
├── HEURISTICAS.yaml → Regras de decisão
├── FRAMEWORKS.yaml  → Modelos mentais
└── METODOLOGIAS.yaml → Processos e táticas
```

### No Script de Debate

O CITADOR referencia o DNA:

```markdown
[CITADOR]
"Referência: DNA Cognitivo de Hormozi, camada de Heurísticas,
princípio 'Pay per performance, not per presence'."
```

---

## 5. Integração com Sistema de Agentes

### Mapeamento Agent IA → Boardroom

| Agent IA (agents/) | Boardroom Agent |
|-----------------------|-----------------|
| AGENT-CRO | CRO |
| AGENT-CFO | CFO |
| AGENT-CMO | CMO |
| AGENT-COO | COO |
| AGENT-CLOSER | (via COLE_GORDON) |

### Usando Memórias dos Agentes

Os agentes podem consultar MEMORY para decisões precedentes:

```python
# Em geração de script
memory_path = "agents/cargo/C-LEVEL/CRO/MEMORY.md"
# Consultar decisões anteriores relevantes ao tema
```

---

## 6. Integração com Council System

### Ativação do Council

O Council é ativado automaticamente em todo episódio (Ato 5):

```
1. SYNTHESIZER → Resume posições do debate
2. METHODOLOGICAL-CRITIC → Questiona premissas
3. DEVILS-ADVOCATE → Ataca posição dominante
4. SYNTHESIZER → Propõe resolução + scoring
```

### Formato de Scoring

```markdown
SCORING:
- Viabilidade: 8/10 - implementável em 90 dias
- Impacto: 8/10 - resolve raiz, não sintoma
- Risco: 7/10 - risco controlado por fases
- Alinhamento: 9/10 - conecta com retenção
- Timing: 8/10 - momento adequado

Score final: 8.0 - Classificação: MUITO BOM
Recomendação: IMPLEMENTAR
```

---

## 7. Integração via CLI

### Comandos Disponíveis

```bash
# Gerar áudio de script existente
python agents/boardroom/scripts/audio_generator.py \
    agents/boardroom/outputs/scripts/episodio.md

# Com output customizado
python agents/boardroom/scripts/audio_generator.py \
    episodio.md \
    --output meu_episodio.mp3

# Dry-run (apenas parse)
python agents/boardroom/scripts/audio_generator.py \
    episodio.md \
    --dry-run
```

### Integração com Outros Scripts

```python
from boardroom.audio_generator import (
    parse_script,
    generate_episode_audio
)

# Parse de script
segments = parse_script(Path("script.md"))
print(f"{len(segments)} segmentos encontrados")

# Geração completa
audio_path = generate_episode_audio(
    script_path=Path("script.md"),
    output_path=Path("output.mp3")
)
```

---

## 8. Fluxo de Dados Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE INTEGRAÇÃO                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Pipeline Jarvis (Fases 1-7)                                        │
│       │                                                             │
│       ▼                                                             │
│  pipeline_outputs[] ──────────────────────────────────────────────┐ │
│       │                                                           │ │
│       ▼                                                           │ │
│  boardroom_hook()                                                 │ │
│       │                                                           │ │
│       ├── detect_participants(topic, content)                     │ │
│       │       │                                                   │ │
│       │       ├── KEYWORD_MAPPING                                 │ │
│       │       └── Returns: {persons, positions, council}          │ │
│       │                                                           │ │
│       ├── generate_episode_script()                               │ │
│       │       │                                                   │ │
│       │       ├── EPISODE-TEMPLATE.md                             │ │
│       │       ├── SCENE-TEMPLATES/*                               │ │
│       │       ├── DNA Cognitivo (para citações)                   │ │
│       │       └── Saves: OUTPUTS/scripts/BWE-*.md                 │ │
│       │                                                           │ │
│       └── [Se usuário aceitar narração]                           │ │
│               │                                                   │ │
│               ▼                                                   │ │
│           generate_episode_audio()                                │ │
│               │                                                   │ │
│               ├── parse_script() → Segments[]                     │ │
│               ├── voice_mapping.json                              │ │
│               ├── ElevenLabs API                                  │ │
│               │       └── eleven_multilingual_v2                  │ │
│               ├── pydub (concatenação)                            │ │
│               └── Saves: OUTPUTS/AUDIO/*.mp3                      │ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Troubleshooting

### Problema: "ElevenLabs não está instalado"

```bash
pip install elevenlabs
```

### Problema: "ELEVENLABS_API_KEY não configurada"

```bash
export ELEVENLABS_API_KEY=your_key_here
```

### Problema: "voice_id não configurado para: AGENT"

Editar `CONFIG/voice_mapping.json` e adicionar o voice_id correto.

### Problema: "pydub não instalado"

```bash
pip install pydub
# No Windows, também instalar ffmpeg
```

### Problema: Voz não reconhecida no script

Verificar se o nome do personagem está em CAIXA ALTA e corresponde ao mapeamento:

```markdown
# Correto
[HORMOZI]

# Incorreto
[Hormozi]
[Alex Hormozi]
```

---

## 10. Extensão do Sistema

### Adicionar Novo Agente

1. Adicionar em `KEYWORD_MAPPING` (jarvis_boardroom_hook.py)
2. Adicionar perfil em `CONFIG/VOICE-PROFILES.md`
3. Adicionar voice_id em `CONFIG/voice_mapping.json`
4. Testar com script de exemplo

### Adicionar Novo Tipo de Cena

1. Criar template em `TEMPLATES/SCENE-TEMPLATES/`
2. Seguir padrão dos templates existentes
3. Documentar em `TEMPLATES/EPISODE-TEMPLATE.md`

### Customizar Scoring

Editar a seção de Council em `TEMPLATES/SCENE-TEMPLATES/SCENE-COUNCIL.md`:

```markdown
SCORING:
- [Nova Dimensão]: [X]/10 - [justificativa]
```
