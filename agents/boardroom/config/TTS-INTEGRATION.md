# 🔊 TTS INTEGRATION
## Configuração de Text-to-Speech para Boardroom Warfare

---

## PROVIDER: ELEVENLABS

ElevenLabs é o TTS recomendado por ter:
- Melhor qualidade em português brasileiro
- Múltiplas vozes distintas
- API fácil de integrar
- Clonagem de voz (opcional)

---

## CONFIGURAÇÃO INICIAL

### Pré-requisitos

1. **Conta ElevenLabs** - https://elevenlabs.io
2. **API Key** - Gerar em Settings > API
3. **Plano** - Starter ($5/mês) ou Creator ($22/mês)

### Variáveis de Ambiente

```bash
# Adicionar ao .env ou exportar
export ELEVENLABS_API_KEY="sua-api-key-aqui"
```

### Instalação

```bash
pip install elevenlabs pydub
```

---

## MAPEAMENTO DE VOZES

### ⚠️ AÇÃO NECESSÁRIA DO USUÁRIO

Você precisa selecionar vozes no ElevenLabs para cada personagem.

**Opção A: Vozes Pré-existentes (Mais Rápido)**
Use vozes da biblioteca do ElevenLabs.

**Opção B: Voice Cloning (Mais Autêntico)**
Clone vozes reais para cada personagem.

### Mapeamento Padrão

```yaml
voice_mapping:
  # SISTEMA
  NARRATOR:
    voice_id: "[CONFIGURAR]"       # Sugestão: "Daniel" ou voz grave BR
    description: "Voz grave, calma, sussurrada"
    settings:
      stability: 0.7
      similarity_boost: 0.8
      style: 0.3

  CITADOR:
    voice_id: "[CONFIGURAR]"       # Sugestão: Voz neutra BR
    description: "Voz neutra, sem emoção"
    settings:
      stability: 0.9
      similarity_boost: 0.9
      style: 0.0

  # AGENTS OF PERSON
  HORMOZI:
    voice_id: "[CONFIGURAR]"       # Sugestão: Voz masculina confiante EN
    description: "Voz alta, rápida, americana"
    settings:
      stability: 0.5
      similarity_boost: 0.75
      style: 0.6

  COLE_GORDON:
    voice_id: "[CONFIGURAR]"       # Sugestão: Voz masculina controlada EN
    description: "Voz grave, lenta, analítica"
    settings:
      stability: 0.8
      similarity_boost: 0.8
      style: 0.2

  BRUNSON:
    voice_id: "[CONFIGURAR]"       # Sugestão: Voz masculina energética EN
    description: "Voz média, rápida, entusiasmada"
    settings:
      stability: 0.4
      similarity_boost: 0.7
      style: 0.8

    voice_id: "[CONFIGURAR]"       # IMPORTANTE: Voz BR nativa
    description: "Voz média, português brasileiro"
    settings:
      stability: 0.6
      similarity_boost: 0.75
      style: 0.4

  # AGENTS OF POSITION
  CRO:
    voice_id: "[CONFIGURAR]"       # Voz assertiva
    description: "Voz alta, impaciente"
    settings:
      stability: 0.5
      similarity_boost: 0.7
      style: 0.5

  CFO:
    voice_id: "[CONFIGURAR]"       # Voz grave, seca
    description: "Voz grave, calculada"
    settings:
      stability: 0.8
      similarity_boost: 0.8
      style: 0.2

  CMO:
    voice_id: "[CONFIGURAR]"       # Voz articulada
    description: "Voz média, estratégica"
    settings:
      stability: 0.6
      similarity_boost: 0.75
      style: 0.4

  COO:
    voice_id: "[CONFIGURAR]"       # Voz firme
    description: "Voz média, pragmática"
    settings:
      stability: 0.7
      similarity_boost: 0.75
      style: 0.3

  # COUNCIL
  COUNCIL_CRITIC:
    voice_id: "[CONFIGURAR]"       # Voz inquisitiva
    description: "Voz questionadora"
    settings:
      stability: 0.6
      similarity_boost: 0.75
      style: 0.4

  COUNCIL_ADVOCATE:
    voice_id: "[CONFIGURAR]"       # Voz provocadora
    description: "Voz desafiadora"
    settings:
      stability: 0.5
      similarity_boost: 0.7
      style: 0.6

  COUNCIL_SYNTHESIZER:
    voice_id: "[CONFIGURAR]"       # Voz serena
    description: "Voz calma, ponderada"
    settings:
      stability: 0.8
      similarity_boost: 0.8
      style: 0.2
```

---

## API REFERENCE

### Gerar Áudio de Um Segmento

```python
from elevenlabs import generate, set_api_key, Voice, VoiceSettings

set_api_key("sua-api-key")

def generate_segment(text: str, voice_config: dict) -> bytes:
    """
    Gera áudio para um segmento de texto.

    Args:
        text: Texto a ser narrado
        voice_config: Configuração da voz (voice_id, settings)

    Returns:
        bytes: Áudio em formato mp3
    """
    audio = generate(
        text=text,
        voice=Voice(
            voice_id=voice_config["voice_id"],
            settings=VoiceSettings(
                stability=voice_config["settings"]["stability"],
                similarity_boost=voice_config["settings"]["similarity_boost"],
                style=voice_config["settings"]["style"],
            )
        ),
        model="eleven_multilingual_v2"  # Importante para PT-BR
    )
    return audio
```

### Listar Vozes Disponíveis

```python
from elevenlabs import voices

def list_available_voices():
    """Lista todas as vozes disponíveis na conta."""
    all_voices = voices()
    for voice in all_voices:
        print(f"Nome: {voice.name}, ID: {voice.voice_id}")
```

---

## LIMITES E CUSTOS

| Plano | Caracteres/mês | Custo | Episódios (~25min) |
|-------|----------------|-------|-------------------|
| Free | 10.000 | $0 | ~0.5 |
| Starter | 30.000 | $5/mês | ~1.5 |
| Creator | 100.000 | $22/mês | ~5 |
| Pro | 500.000 | $99/mês | ~25 |

**Estimativa:** Um episódio de 25 minutos tem ~15.000-20.000 caracteres.

---

## FALLBACK: GOOGLE CLOUD TTS

Se ElevenLabs não estiver disponível:

```python
from google.cloud import texttospeech

def generate_google_tts(text: str, voice_name: str, language: str = "pt-BR"):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language,
        name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    return response.audio_content
```

Vozes PT-BR recomendadas no Google:
- `pt-BR-Neural2-A` (feminina)
- `pt-BR-Neural2-B` (masculina)
- `pt-BR-Neural2-C` (feminina)
