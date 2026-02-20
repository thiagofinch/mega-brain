#!/usr/bin/env python3
"""
CREATE JARVIS VOICE CLONE v4 - PERFEITO
=======================================
Clone refinado da voz do JARVIS dos filmes Homem de Ferro.
Processo completo: Extrai segmentos -> Isola voz -> Cria clone -> Testa

Autor: JARVIS
"""

import os
import subprocess
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_DIR = f"{BASE_DIR}/jarvis_v4_sources"
SEGMENTS_DIR = f"{BASE_DIR}/jarvis_v4_segments"
ISOLATED_DIR = f"{BASE_DIR}/jarvis_v4_isolated"

VOICE_NAME = "JARVIS-Film-v4"
VOICE_DESCRIPTION = """Voz do JARVIS dos filmes Homem de Ferro (dublagem brasileira).
Eduardo Borgerth - dublador oficial do JARVIS em PT-BR.
Tom processado/robótico original dos filmes Marvel.
Características: clareza digital, precisão, elegância artificial.
Extraído de múltiplas cenas dos filmes com isolamento de voz."""


# Definir segmentos específicos onde JARVIS fala claramente
# Formato: (arquivo_fonte, inicio_segundos, duracao_segundos, nome)
SEGMENTS_TO_EXTRACT = [
    # 01_aprimoramentos - Tony pede melhorias ao JARVIS
    ("01_aprimoramentos.mp3", 0, 25, "aprim_01"),
    ("01_aprimoramentos.mp3", 30, 25, "aprim_02"),
    ("01_aprimoramentos.mp3", 60, 25, "aprim_03"),
    ("01_aprimoramentos.mp3", 100, 25, "aprim_04"),
    ("01_aprimoramentos.mp3", 140, 25, "aprim_05"),

    # 02_elemento - Criando novo elemento
    ("02_elemento.mp3", 0, 30, "elem_01"),
    ("02_elemento.mp3", 40, 30, "elem_02"),
    ("02_elemento.mp3", 80, 30, "elem_03"),
    ("02_elemento.mp3", 120, 30, "elem_04"),
    ("02_elemento.mp3", 160, 30, "elem_05"),
    ("02_elemento.mp3", 200, 30, "elem_06"),

    # 03_descobrindo - Descoberta
    ("03_descobrindo.mp3", 0, 30, "desc_01"),
    ("03_descobrindo.mp3", 40, 30, "desc_02"),
    ("03_descobrindo.mp3", 80, 30, "desc_03"),
    ("03_descobrindo.mp3", 110, 30, "desc_04"),

    # 04_ultron - JARVIS vs Ultron (importante - JARVIS sozinho)
    ("04_ultron.mp3", 0, 30, "ultron_01"),
    ("04_ultron.mp3", 35, 30, "ultron_02"),
    ("04_ultron.mp3", 65, 30, "ultron_03"),

    # 05_jonas - História completa (curto, usar inteiro)
    ("05_jonas.mp3", 0, 40, "jonas_full"),

    # 06_bomdia - Bom dia (curto, usar inteiro)
    ("06_bomdia.mp3", 0, 20, "bomdia_full"),
]


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def extract_segments():
    """Extrai segmentos específicos dos arquivos fonte."""
    print_header("FASE 1: EXTRAINDO SEGMENTOS")

    os.makedirs(SEGMENTS_DIR, exist_ok=True)

    success = 0
    for source, start, duration, name in SEGMENTS_TO_EXTRACT:
        source_path = os.path.join(SOURCES_DIR, source)
        output_path = os.path.join(SEGMENTS_DIR, f"{name}.mp3")

        if not os.path.exists(source_path):
            print(f"  ! {source} não encontrado")
            continue

        cmd = [
            "ffmpeg", "-y",
            "-i", source_path,
            "-ss", str(start),
            "-t", str(duration),
            "-acodec", "libmp3lame",
            "-ab", "192k",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"  ✓ {name}.mp3 ({duration}s)")
            success += 1
        else:
            print(f"  ✗ {name} falhou")

    print(f"\n✅ {success}/{len(SEGMENTS_TO_EXTRACT)} segmentos extraídos")
    return success


def isolate_voices():
    """Aplica Voice Isolation em todos os segmentos."""
    print_header("FASE 2: ISOLANDO VOZES")

    os.makedirs(ISOLATED_DIR, exist_ok=True)

    segments = sorted([f for f in os.listdir(SEGMENTS_DIR) if f.endswith(".mp3")])
    print(f"Segmentos para isolar: {len(segments)}")

    success = 0
    for seg in segments:
        input_path = os.path.join(SEGMENTS_DIR, seg)
        output_path = os.path.join(ISOLATED_DIR, seg.replace(".mp3", "_iso.mp3"))

        print(f"  Isolando: {seg}...", end=" ", flush=True)

        with open(input_path, "rb") as audio_file:
            response = requests.post(
                "https://api.elevenlabs.io/v1/audio-isolation",
                headers={"xi-api-key": ELEVENLABS_API_KEY},
                files={"audio": (seg, audio_file, "audio/mpeg")}
            )

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print("✓")
            success += 1
        else:
            print(f"✗ ({response.status_code})")

        # Rate limiting
        time.sleep(1)

    print(f"\n✅ {success}/{len(segments)} segmentos isolados")
    return success


def create_voice_clone():
    """Cria o clone de voz v4."""
    print_header("FASE 3: CRIANDO CLONE v4")

    # Lista arquivos isolados
    audio_files = sorted([
        os.path.join(ISOLATED_DIR, f)
        for f in os.listdir(ISOLATED_DIR)
        if f.endswith(".mp3")
    ])

    print(f"Arquivos para clone: {len(audio_files)}")

    # Limitar a 25 arquivos (limite ElevenLabs)
    if len(audio_files) > 25:
        print(f"  ! Limitando a 25 arquivos (tinha {len(audio_files)})")
        audio_files = audio_files[:25]

    # Prepara files
    files = []
    for audio_path in audio_files:
        filename = os.path.basename(audio_path)
        files.append(("files", (filename, open(audio_path, "rb"), "audio/mpeg")))
        print(f"  + {filename}")

    data = {
        "name": VOICE_NAME,
        "description": VOICE_DESCRIPTION,
        "labels": json.dumps({
            "accent": "brazilian-portuguese",
            "age": "synthetic",
            "gender": "male",
            "use_case": "assistant"
        })
    }

    print(f"\n📤 Enviando para ElevenLabs...")

    response = requests.post(
        "https://api.elevenlabs.io/v1/voices/add",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        data=data,
        files=files
    )

    # Fecha arquivos
    for _, (_, file_obj, _) in files:
        file_obj.close()

    if response.status_code == 200:
        result = response.json()
        voice_id = result.get("voice_id")
        print(f"\n✅ VOZ v4 CRIADA!")
        print(f"   Voice ID: {voice_id}")

        # Salva Voice ID
        with open(f"{BASE_DIR}/voice_id_v4.txt", "w") as f:
            f.write(voice_id)

        return voice_id
    else:
        print(f"\n❌ Erro: {response.status_code}")
        print(response.text)
        return None


def configure_settings(voice_id: str):
    """Configura settings otimizados para JARVIS v4."""
    print_header("FASE 4: CONFIGURANDO SETTINGS")

    # Settings refinados para tom robótico do filme
    settings = {
        "stability": 0.65,           # Alta estabilidade = mais robótico
        "similarity_boost": 0.92,    # Máxima fidelidade ao som original
        "style": 0.10,               # Muito baixo = menos emocional, mais máquina
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
        print("✅ Settings configurados!")
        for k, v in settings.items():
            print(f"   {k}: {v}")
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        return False


def test_voice(voice_id: str):
    """Testa a voz com frases típicas do JARVIS."""
    print_header("FASE 5: TESTANDO VOZ")

    # Frases icônicas do JARVIS
    test_phrases = [
        "Bem-vindo de volta, senhor. Todos os sistemas operacionais.",
        "Estamos na fase quatro, batch trinta e cinco de cinquenta e sete.",
        "Senhor, detectei uma anomalia nos dados. Recomendo investigação imediata.",
        "Inicializando protocolo de segurança. Scan completo em andamento.",
        "A porcentagem de sucesso dessa operação é de oitenta e sete vírgula três por cento.",
        "Posso ser de mais alguma assistência, senhor?"
    ]

    # Settings otimizados para teste
    voice_settings = {
        "stability": 0.65,
        "similarity_boost": 0.92,
        "style": 0.10,
        "use_speaker_boost": True
    }

    for i, phrase in enumerate(test_phrases, 1):
        print(f"\n  Teste {i}: \"{phrase[:40]}...\"")

        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": phrase,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": voice_settings
            }
        )

        if response.status_code == 200:
            test_file = f"{BASE_DIR}/test_v4_{i}.mp3"
            with open(test_file, "wb") as f:
                f.write(response.content)
            print(f"  ✓ Salvo: test_v4_{i}.mp3")
        else:
            print(f"  ✗ Falhou: {response.status_code}")

        time.sleep(1)  # Rate limiting


def main():
    print("\n" + "=" * 60)
    print("JARVIS VOICE CLONE v4 - PROCESSO COMPLETO")
    print("=" * 60)
    print("\nObjetivo: Voz 100% idêntica ao filme")
    print("Fonte: Cenas dos filmes Homem de Ferro + Vingadores")

    # Fase 1: Extrair segmentos
    extracted = extract_segments()
    if extracted == 0:
        print("\n❌ Nenhum segmento extraído. Abortando.")
        return

    # Fase 2: Isolar vozes
    isolated = isolate_voices()
    if isolated == 0:
        print("\n❌ Nenhuma voz isolada. Abortando.")
        return

    # Fase 3: Criar clone
    voice_id = create_voice_clone()
    if not voice_id:
        print("\n❌ Clone não criado. Abortando.")
        return

    # Fase 4: Configurar settings
    configure_settings(voice_id)

    # Fase 5: Testar
    test_voice(voice_id)

    # Resumo final
    print("\n" + "=" * 60)
    print("JARVIS v4 - PROCESSO COMPLETO")
    print("=" * 60)
    print(f"\n🎯 Voice ID: {voice_id}")
    print(f"📁 Segmentos extraídos: {extracted}")
    print(f"🔊 Segmentos isolados: {isolated}")
    print(f"📝 Nome: {VOICE_NAME}")
    print(f"\n🎬 Fonte: Filmes Homem de Ferro + Vingadores")
    print(f"🤖 Tom: Robótico/Processado original")
    print(f"\n📂 Testes salvos em: {BASE_DIR}/test_v4_*.mp3")
    print("=" * 60)

    return voice_id


if __name__ == "__main__":
    main()
