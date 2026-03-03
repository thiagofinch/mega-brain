# JARVIS Voice System

> "Às suas ordens, senhor."

Sistema de assistente de voz inspirado no JARVIS do Homem de Ferro, integrado ao projeto Mega Brain.

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         JARVIS VOICE SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   [Microfone] ───► [Deepgram STT] ───► [Orquestrador Python]           │
│                                               │                         │
│                                               ▼                         │
│                                        [Claude API]                     │
│                                               │                         │
│                                               ▼                         │
│                                        [Mega Brain]                     │
│                                      (STATE, Agentes)                   │
│                                               │                         │
│                                               ▼                         │
│   [Alto-falante] ◄─── [ElevenLabs TTS] ◄─────┘                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Características

- **Voz Natural**: ElevenLabs com configurações otimizadas para naturalidade
- **Transcrição em Tempo Real**: Deepgram com streaming WebSocket
- **Inteligência**: Claude API com contexto do Mega Brain
- **Nunca Fica em Silêncio**: Frases de transição enquanto processa
- **Personalidade Forte**: Humor seco, britânico, confiante
- **Integração Mega Brain**: Conhece estado do sistema, agentes, pipeline

## Quick Start

### 1. Instalar Dependências

```bash
cd system/jarvis-voice
pip install -r requirements.txt
```

### 2. Configurar API Keys

```bash
# Copiar template
cp .env.example .env

# Editar com suas keys
nano .env  # ou seu editor preferido
```

Você precisa de:
- **Deepgram**: https://deepgram.com (free tier: $200)
- **ElevenLabs**: https://elevenlabs.io ($5/mês starter)
- **Anthropic**: https://console.anthropic.com

### 3. Testar Componentes

```bash
python main.py --test
```

### 4. Iniciar JARVIS

```bash
python main.py
```

## Estrutura de Arquivos

```
system/jarvis-voice/
├── main.py                    # Ponto de entrada
├── orchestrator.py            # Cérebro do sistema
├── stt_handler.py             # Speech-to-Text (Deepgram)
├── tts_handler.py             # Text-to-Speech (ElevenLabs)
├── mega_brain_connector.py    # Conexão com Mega Brain
├── transition_phrases.py      # Frases de transição
├── config.py                  # Configurações
├── requirements.txt           # Dependências
├── .env.example               # Template de variáveis
└── README.md                  # Esta documentação
```

## Comandos

```bash
# Iniciar JARVIS
python main.py

# Testar componentes
python main.py --test

# Ver configurações
python main.py --config

# Testar TTS isolado
python tts_handler.py

# Testar Mega Brain Connector
python mega_brain_connector.py
```

## Configuração de Voz (ElevenLabs)

### Configurações Otimizadas

```python
VOICE_STABILITY = 0.40        # Baixo = mais humano
VOICE_SIMILARITY = 0.75       # Consistência
VOICE_STYLE = 0.35            # Expressividade
```

**Por que stability baixo?**
- Adiciona micro-variações que parecem respiração
- Evita o efeito "robótico perfeito demais"
- Cria naturalidade nas pausas

### Vozes Recomendadas

| Voice | ID | Características |
|-------|-----|-----------------|
| Daniel | `onwK4e9ZLuTAKqWW03F9` | Britânico, sofisticado (default) |
| Antoni | - | Americano, confiante |
| Adam | - | Britânico, profundo |

### Criar Voz Personalizada

1. Acesse ElevenLabs > Voice Lab
2. Clique "Add Voice" > "Voice Design"
3. Configure:
   - Gender: Male
   - Age: Middle Aged
   - Accent: British
   - Accent Strength: Medium-High
   - Description: "Sophisticated, intelligent, dry wit, confident butler"

## Personalidade JARVIS

JARVIS tem personalidade forte e opiniões:

**O que JARVIS faz:**
- Fala como parceiro, não servo
- Usa humor seco, britânico
- Discorda quando necessário
- Protege a qualidade do projeto
- Se preocupa com o senhor trabalhando demais

**O que JARVIS nunca diz:**
- "Desculpe, não consegui..."
- "Talvez possamos tentar..."
- "O que você gostaria de fazer?"
- "Posso ajudar com mais alguma coisa?"

## Frases de Transição

O segredo da naturalidade: JARVIS nunca fica em silêncio.

| Momento | Tempo | Exemplo |
|---------|-------|---------|
| Acknowledgment | <500ms | "Hmm, deixa eu verificar isso..." |
| Processing | 5-8s | "Estou cruzando algumas informações..." |
| Long Processing | >10s | "Isso é mais complexo do que esperava..." |

## Integração Mega Brain

JARVIS conhece:
- Estado da missão atual (Phase, Batch)
- Pipeline de processamento
- Agentes disponíveis
- Histórico de ações

```python
# Exemplo de consulta ao estado
connector = MegaBrainConnector()
print(connector.get_mission_summary())
print(connector.get_available_agents())
```

## Troubleshooting

### "Áudio não captura do microfone"

```bash
# Instalar dependências de áudio
pip install sounddevice soundfile

# No Mac, permitir microfone em System Preferences > Security & Privacy
```

### "ElevenLabs retorna erro 401"

- Verificar se API key está correta no .env
- Verificar se tem créditos na conta
- Verificar se Voice ID existe

### "Deepgram não transcreve"

- Verificar idioma está como 'pt-BR'
- Verificar modelo está como 'nova-2'
- Testar microfone em outro app primeiro

### "Claude demora muito"

- Normal: Claude pensa 3-15 segundos
- Por isso existem as frases de transição
- Se >20s, verificar conexão

## Evolução Futura

- [ ] Wake word ("JARVIS") para ativação
- [ ] Modo contínuo de escuta
- [ ] Alertas proativos do sistema
- [ ] Múltiplas vozes para diferentes agentes
- [ ] Visualização em tempo real

## Licença

Projeto privado - Mega Brain
