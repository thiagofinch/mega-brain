#!/usr/bin/env python3
"""
ELEVENLABS VOICE CLONE - Eduardo Borgerth (JARVIS BR)
======================================================
Cria clone de voz usando a API do ElevenLabs.

Autor: JARVIS
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuração
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment")
VOICE_NAME = "JARVIS-Eduardo-Borgerth"
VOICE_DESCRIPTION = """Voz do dublador brasileiro Eduardo Borgerth como JARVIS.
Tom sofisticado, elegante, articulado.
Ironia sutil, confiança, precisão.
Português brasileiro com dicção impecável.
Dublador oficial do JARVIS nos filmes do Homem de Ferro em português."""

# Arquivos de áudio
SEGMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FILES = [
    f"{SEGMENTS_DIR}/segments/segment_01_intro.mp3",
    f"{SEGMENTS_DIR}/segments/segment_02_early.mp3",
    f"{SEGMENTS_DIR}/segments/segment_03_mid.mp3",
    f"{SEGMENTS_DIR}/segments/segment_04_late.mp3",
    f"{SEGMENTS_DIR}/segments/segment_05_end.mp3",
]


def create_voice_clone():
    """Cria clone de voz no ElevenLabs."""

    print("=" * 60)
    print("ELEVENLABS - CRIANDO CLONE DE VOZ")
    print("=" * 60)
    print(f"\nNome: {VOICE_NAME}")
    print(f"Arquivos: {len(AUDIO_FILES)}")

    # Prepara os arquivos
    files = []
    for audio_path in AUDIO_FILES:
        if os.path.exists(audio_path):
            filename = os.path.basename(audio_path)
            files.append(
                ("files", (filename, open(audio_path, "rb"), "audio/mpeg"))
            )
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {audio_path} não encontrado")

    if not files:
        print("\n❌ Nenhum arquivo de áudio encontrado!")
        return None

    # Dados do formulário
    data = {
        "name": VOICE_NAME,
        "description": VOICE_DESCRIPTION,
        "labels": json.dumps({
            "accent": "brazilian-portuguese",
            "description": "JARVIS dublagem BR",
            "age": "middle-aged",
            "gender": "male",
            "use_case": "assistant"
        })
    }

    print(f"\n📤 Enviando para ElevenLabs...")

    # Faz a requisição
    response = requests.post(
        "https://api.elevenlabs.io/v1/voices/add",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY
        },
        data=data,
        files=files
    )

    # Fecha os arquivos
    for _, (_, file_obj, _) in files:
        file_obj.close()

    if response.status_code == 200:
        result = response.json()
        voice_id = result.get("voice_id")
        print(f"\n✅ VOZ CRIADA COM SUCESSO!")
        print(f"   Voice ID: {voice_id}")
        print(f"   Nome: {VOICE_NAME}")

        # Salva o Voice ID
        with open(f"{SEGMENTS_DIR}/voice_id.txt", "w") as f:
            f.write(voice_id)

        print(f"\n📁 Voice ID salvo em: voice_id.txt")
        return voice_id
    else:
        print(f"\n❌ Erro ao criar voz: {response.status_code}")
        print(response.text)
        return None


def get_voice_settings(voice_id: str):
    """Obtém configurações da voz."""
    response = requests.get(
        f"https://api.elevenlabs.io/v1/voices/{voice_id}/settings",
        headers={"xi-api-key": ELEVENLABS_API_KEY}
    )
    return response.json() if response.status_code == 200 else None


def update_voice_settings(voice_id: str):
    """
    Atualiza configurações da voz para o estilo JARVIS.

    Settings otimizados:
    - stability: 0.40 (médio-baixo para naturalidade)
    - similarity_boost: 0.80 (alto para manter consistência)
    - style: 0.35 (expressividade moderada)
    """
    print(f"\n⚙️  Configurando voice settings...")

    settings = {
        "stability": 0.40,
        "similarity_boost": 0.80,
        "style": 0.35,
        "use_speaker_boost": True
    }

    response = requests.post(
        f"https://api.elevenlabs.io/v1/voices/{voice_id}/settings/edit",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json=settings
    )

    if response.status_code == 200:
        print("✅ Settings atualizados!")
        print(f"   stability: {settings['stability']}")
        print(f"   similarity_boost: {settings['similarity_boost']}")
        print(f"   style: {settings['style']}")
        return True
    else:
        print(f"❌ Erro ao atualizar settings: {response.status_code}")
        return False


def test_voice(voice_id: str, text: str = "Bem-vindo de volta, senhor. JARVIS online e operacional."):
    """Testa a voz gerada."""
    print(f"\n🔊 Testando voz...")

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.40,
                "similarity_boost": 0.80,
                "style": 0.35,
                "use_speaker_boost": True
            }
        }
    )

    if response.status_code == 200:
        test_file = f"{SEGMENTS_DIR}/test_jarvis_eduardo.mp3"
        with open(test_file, "wb") as f:
            f.write(response.content)
        print(f"✅ Áudio de teste salvo em: {test_file}")
        return test_file
    else:
        print(f"❌ Erro ao gerar áudio de teste: {response.status_code}")
        print(response.text)
        return None


if __name__ == "__main__":
    # Cria o clone
    voice_id = create_voice_clone()

    if voice_id:
        # Atualiza settings
        update_voice_settings(voice_id)

        # Testa a voz
        test_voice(voice_id)

        print("\n" + "=" * 60)
        print("RESUMO")
        print("=" * 60)
        print(f"\n🎯 Voice ID: {voice_id}")
        print(f"📝 Nome: {VOICE_NAME}")
        print("\nPróximo passo: Configurar este Voice ID no Vapi")
        print("=" * 60)
