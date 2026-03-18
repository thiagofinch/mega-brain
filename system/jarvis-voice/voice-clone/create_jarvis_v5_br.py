#!/usr/bin/env python3
"""
CREATE JARVIS VOICE CLONE v5 - DUBLAGEM BRASILEIRA
===================================================
Clone da voz do JARVIS com áudios ESPECIFICAMENTE da dublagem brasileira.
[VOICE_ACTOR_NAME] - dublador oficial do JARVIS no Brasil.

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
SOURCES_DIR = f"{BASE_DIR}/jarvis_v5_br"
SEGMENTS_DIR = f"{BASE_DIR}/jarvis_v5_segments"
ISOLATED_DIR = f"{BASE_DIR}/jarvis_v5_isolated"

VOICE_NAME = "JARVIS-Brasil-v5"
VOICE_DESCRIPTION = """Voz do JARVIS - Dublagem BRASILEIRA oficial.
Dublador: [VOICE_ACTOR_NAME].
Extraído dos filmes Homem de Ferro e Vingadores - versão Brasil.
Tom: processado, digital, robótico, elegante.
Idioma: Português do BRASIL (PT-BR) exclusivamente."""


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def get_duration(file_path):
    """Obtém duração do arquivo em segundos."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except:
        return 0


def extract_segments():
    """Extrai segmentos dos arquivos fonte."""
    print_header("FASE 1: EXTRAINDO SEGMENTOS DA DUBLAGEM BR")

    os.makedirs(SEGMENTS_DIR, exist_ok=True)

    # Lista arquivos fonte
    sources = sorted([f for f in os.listdir(SOURCES_DIR) if f.endswith(".mp3")])
    print(f"Arquivos fonte: {len(sources)}")

    segments_created = 0

    for source in sources:
        source_path = os.path.join(SOURCES_DIR, source)
        duration = get_duration(source_path)
        print(f"\n  {source}: {duration:.1f}s")

        # Estratégia: extrair segmentos de 20-30s ao longo do arquivo
        base_name = source.replace(".mp3", "")
        segment_length = 25  # segundos
        overlap = 5  # segundos de sobreposição

        start = 0
        seg_num = 1

        while start < duration - 10:  # pelo menos 10s restantes
            seg_duration = min(segment_length, duration - start)
            output_name = f"{base_name}_seg{seg_num:02d}.mp3"
            output_path = os.path.join(SEGMENTS_DIR, output_name)

            cmd = [
                "ffmpeg", "-y",
                "-i", source_path,
                "-ss", str(start),
                "-t", str(seg_duration),
                "-acodec", "libmp3lame",
                "-ab", "192k",
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                print(f"    ✓ {output_name} ({seg_duration:.0f}s)")
                segments_created += 1
            else:
                print(f"    ✗ {output_name} falhou")

            start += segment_length - overlap
            seg_num += 1

    print(f"\n✅ {segments_created} segmentos extraídos")
    return segments_created


def isolate_voices():
    """Aplica Voice Isolation em todos os segmentos."""
    print_header("FASE 2: ISOLANDO VOZES (ElevenLabs)")

    os.makedirs(ISOLATED_DIR, exist_ok=True)

    segments = sorted([f for f in os.listdir(SEGMENTS_DIR) if f.endswith(".mp3")])
    print(f"Segmentos para isolar: {len(segments)}")

    success = 0
    for i, seg in enumerate(segments, 1):
        input_path = os.path.join(SEGMENTS_DIR, seg)
        output_path = os.path.join(ISOLATED_DIR, seg.replace(".mp3", "_iso.mp3"))

        print(f"  [{i}/{len(segments)}] {seg}...", end=" ", flush=True)

        try:
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

        except Exception as e:
            print(f"✗ ({e})")

        time.sleep(0.5)  # Rate limiting

    print(f"\n✅ {success}/{len(segments)} segmentos isolados")
    return success


def create_voice_clone():
    """Cria o clone de voz v5 - Brasil."""
    print_header("FASE 3: CRIANDO CLONE v5 (BRASIL)")

    # Lista arquivos isolados
    audio_files = sorted([
        os.path.join(ISOLATED_DIR, f)
        for f in os.listdir(ISOLATED_DIR)
        if f.endswith(".mp3")
    ])

    print(f"Arquivos para clone: {len(audio_files)}")

    # Limitar a 25 arquivos (limite ElevenLabs)
    if len(audio_files) > 25:
        print(f"  ! Selecionando os 25 melhores (maior tamanho)")
        # Ordenar por tamanho (maiores = mais conteúdo)
        audio_files = sorted(audio_files, key=lambda x: os.path.getsize(x), reverse=True)[:25]

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
        print(f"\n✅ VOZ v5 BRASIL CRIADA!")
        print(f"   Voice ID: {voice_id}")

        # Salva Voice ID
        with open(f"{BASE_DIR}/voice_id_v5_br.txt", "w") as f:
            f.write(voice_id)

        return voice_id
    else:
        print(f"\n❌ Erro: {response.status_code}")
        print(response.text)
        return None


def configure_settings(voice_id: str):
    """Configura settings otimizados para JARVIS - máximo robótico."""
    print_header("FASE 4: CONFIGURANDO SETTINGS (MÁXIMO ROBÓTICO)")

    # Settings para máxima consistência e tom robótico
    settings = {
        "stability": 0.90,           # Máximo = sem variação
        "similarity_boost": 0.98,    # Máximo = fiel ao original
        "style": 0.0,                # Zero = sem emoção = robótico
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
    """Testa a voz com frases em português brasileiro."""
    print_header("FASE 5: TESTANDO VOZ (PT-BR)")

    # Frases em português brasileiro com vocabulário específico
    test_phrases = [
        "Bom dia, senhor. Todos os sistemas estão operacionais.",
        "Estamos na fase quatro. O progresso está em sessenta e um por cento.",
        "Senhor, detectei uma anomalia nos arquivos. Recomendo uma verificação.",
        "A missão atual tem cinquenta e sete batches pendentes.",
        "Posso ajudar com mais alguma coisa, senhor?",
        "Iniciando protocolo de análise. Isso vai demorar só um minuto."
    ]

    voice_settings = {
        "stability": 0.90,
        "similarity_boost": 0.98,
        "style": 0.0,
        "use_speaker_boost": True
    }

    for i, phrase in enumerate(test_phrases, 1):
        print(f"\n  Teste {i}: \"{phrase[:45]}...\"")

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
            test_file = f"{BASE_DIR}/test_v5_br_{i}.mp3"
            with open(test_file, "wb") as f:
                f.write(response.content)
            print(f"  ✓ Salvo: test_v5_br_{i}.mp3")
        else:
            print(f"  ✗ Falhou: {response.status_code}")

        time.sleep(1)


def main():
    print("\n" + "=" * 60)
    print("JARVIS VOICE CLONE v5 - DUBLAGEM BRASILEIRA")
    print("=" * 60)
    print("\n🇧🇷 Objetivo: Voz 100% português do BRASIL")
    print("🎭 Dublador: [VOICE_ACTOR_NAME]")
    print("🤖 Tom: Robótico, processado, digital")

    # Fase 1
    extracted = extract_segments()
    if extracted == 0:
        print("\n❌ Nenhum segmento extraído. Abortando.")
        return

    # Fase 2
    isolated = isolate_voices()
    if isolated == 0:
        print("\n❌ Nenhuma voz isolada. Abortando.")
        return

    # Fase 3
    voice_id = create_voice_clone()
    if not voice_id:
        print("\n❌ Clone não criado. Abortando.")
        return

    # Fase 4
    configure_settings(voice_id)

    # Fase 5
    test_voice(voice_id)

    # Resumo
    print("\n" + "=" * 60)
    print("JARVIS v5 BRASIL - COMPLETO")
    print("=" * 60)
    print(f"\n🎯 Voice ID: {voice_id}")
    print(f"📁 Segmentos extraídos: {extracted}")
    print(f"🔊 Segmentos isolados: {isolated}")
    print(f"📝 Nome: {VOICE_NAME}")
    print(f"\n🇧🇷 Dublagem: BRASILEIRA ([VOICE_ACTOR_NAME])")
    print(f"🤖 Tom: Máximo robótico (stability=0.90, style=0)")
    print(f"\n📂 Testes: {BASE_DIR}/test_v5_br_*.mp3")
    print("=" * 60)

    return voice_id


if __name__ == "__main__":
    main()
