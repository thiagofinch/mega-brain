# JARVIS Narrator - Sistema de Audiobook

Sistema completo para transformar qualquer texto em narração com a voz e personalidade do JARVIS ([VOICE_ACTOR_NAME] - dublador oficial PT-BR).

## Uso Rápido

```bash
# Narrar arquivo de texto
python3 jarvis_narrator.py meu_relatorio.txt

# Narrar texto direto
python3 jarvis_narrator.py --text "Seu texto aqui"

# Verificar quota disponível
python3 jarvis_narrator.py --check-quota

# Pular adaptação de estilo (usa texto original)
python3 jarvis_narrator.py --skip-adaptation meu_arquivo.txt

# Forçar modo chunks (textos muito longos)
python3 jarvis_narrator.py --chunks livro_completo.txt
```

## O Que o Sistema Faz

```
┌─────────────────────────────────────────────────────────────┐
│  FLUXO JARVIS NARRATOR                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. TEXTO ORIGINAL                                          │
│     └─→ Seu relatório, artigo, documento                   │
│                                                             │
│  2. ADAPTAÇÃO DE ESTILO (Claude)                            │
│     └─→ Reescrito como se JARVIS estivesse narrando        │
│     └─→ Tom sarcástico, sofisticado, britânico             │
│     └─→ Mantém todos os fatos e números                    │
│                                                             │
│  3. GERAÇÃO DE ÁUDIO (ElevenLabs)                          │
│     └─→ Voz clonada do [VOICE_ACTOR_NAME]                    │
│     └─→ Modelo multilingual v2 (PT-BR otimizado)           │
│     └─→ Divisão automática para textos longos              │
│                                                             │
│  4. OUTPUT                                                  │
│     └─→ Arquivo MP3 em /audiobooks/                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Configuração

As credenciais estão em `.env`:

```env
ELEVENLABS_API_KEY=sk_...
ANTHROPIC_API_KEY=sk-ant-...
```

## Custos Estimados

| Duração do Áudio | Caracteres | Custo (Creator $22/mês) |
|------------------|------------|-------------------------|
| 5 minutos | ~4.000 | ~4% da quota mensal |
| 15 minutos | ~12.000 | ~12% da quota mensal |
| 1 hora | ~48.000 | ~48% da quota mensal |

## Arquivos Gerados

Os audiobooks são salvos em:
```
system/jarvis-voice/audiobooks/JARVIS_{nome}_{timestamp}.mp3
```

## Dependências

```bash
pip3 install elevenlabs anthropic pydub python-dotenv requests
```

## Voz Utilizada

- **Nome:** JARVIS-Brasil-v5
- **Voice ID:** (configurado via ELEVENLABS_NARRATOR_VOICE_ID em .env)
- **Dublador:** [VOICE_ACTOR_NAME] (voz oficial do JARVIS em PT-BR)
- **Tipo:** Professional Voice Clone

## Limites

- **ElevenLabs API:** ~5.000 chars por request (sistema divide automaticamente)
- **Quota mensal:** Depende do seu plano
- **Áudio máximo:** Sem limite (sistema combina chunks)

---

## Exemplos de Uso

### Narrar um relatório
```bash
python3 jarvis_narrator.py relatorio_vendas.txt
```

### Narrar sem mudar o estilo
```bash
python3 jarvis_narrator.py --skip-adaptation script_pronto.txt
```

### Verificar quanto pode produzir
```bash
python3 jarvis_narrator.py --check-quota
```

---
*JARVIS Voice System - Mega Brain*
