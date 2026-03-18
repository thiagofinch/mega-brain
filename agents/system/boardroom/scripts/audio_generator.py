#!/usr/bin/env python3
"""
BOARDROOM WARFARE - Audio Generator
Gera arquivos de áudio a partir de scripts .md

Uso:
    python audio_generator.py <script.md> [--output <output.mp3>]
"""

import os
import re
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env do diretorio raiz do projeto
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
    print(f"[OK] .env carregado de: {_env_path}")
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

# Imports condicionais para TTS
try:
    from elevenlabs import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("[!] ElevenLabs nao instalado. Use: pip install elevenlabs")

elevenlabs_client = None

# Configurar ffmpeg/ffprobe ANTES de importar pydub (Windows requirement)
_ffmpeg_bin = Path(r"C:\ffmpeg\bin")
_ffmpeg_path = _ffmpeg_bin / "ffmpeg.exe"
_ffprobe_path = _ffmpeg_bin / "ffprobe.exe"

if _ffmpeg_path.exists() and _ffprobe_path.exists():
    # Metodo 1: Environment variables (Windows primary method)
    os.environ["FFMPEG_BINARY"] = str(_ffmpeg_path)
    os.environ["FFPROBE_BINARY"] = str(_ffprobe_path)
    # Metodo 2: Add to PATH
    os.environ["PATH"] = str(_ffmpeg_bin) + os.pathsep + os.environ.get("PATH", "")
    print(f"[OK] ffmpeg configurado: {_ffmpeg_path}")
    print(f"[OK] ffprobe configurado: {_ffprobe_path}")
else:
    print("[!] ffmpeg/ffprobe nao encontrados no caminho esperado")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    # Metodo 3: Class attributes (backup method)
    AudioSegment.converter = str(_ffmpeg_path)
    AudioSegment.ffprobe = str(_ffprobe_path)
except ImportError:
    PYDUB_AVAILABLE = False
    print("[!] pydub nao instalado. Use: pip install pydub")


# ═══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════

CONFIG_PATH = Path(__file__).parent.parent / "config" / "voice_mapping.json"
OUTPUT_PATH = Path(__file__).parent.parent / "outputs" / "AUDIO"
TEMP_PATH = Path(__file__).parent.parent / "outputs" / "temp"

# Criar pastas se não existirem
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
TEMP_PATH.mkdir(parents=True, exist_ok=True)


@dataclass
class Segment:
    """Representa um segmento de áudio a ser gerado."""
    index: int
    speaker: str
    text: str
    instruction: str = ""


# ═══════════════════════════════════════════════════════════════
# PARSING DO SCRIPT
# ═══════════════════════════════════════════════════════════════

def parse_script(script_path: Path) -> List[Segment]:
    """
    Parse um script .md e extrai os segmentos de fala.

    Formato esperado:
    [PERSONAGEM]
    (instrução opcional)
    "Texto da fala"
    """
    segments = []

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex para capturar falas
    # [PERSONAGEM]\n(instrução)?\n"texto" ou texto sem aspas
    pattern = r'\[([A-Z_-]+)\]\s*(?:\(([^)]+)\))?\s*\n([^[\n]+(?:\n(?!\[)[^[\n]+)*)'

    matches = re.findall(pattern, content)

    for i, (speaker, instruction, text) in enumerate(matches):
        # Limpar texto
        text = text.strip()
        text = re.sub(r'^["\']|["\']$', '', text)  # Remove aspas
        text = re.sub(r'\[PAUSA.*?\]', '', text)    # Remove marcações de pausa (serão tratadas depois)
        text = re.sub(r'\[SOM:.*?\]', '', text)     # Remove marcações de som
        text = text.strip()

        if text:
            segments.append(Segment(
                index=i,
                speaker=speaker.strip(),
                text=text,
                instruction=instruction.strip() if instruction else ""
            ))

    return segments


def extract_pauses(script_path: Path) -> List[Tuple[int, float]]:
    """
    Extrai marcações de pausa do script.

    Retorna lista de (posição, duração_segundos)
    """
    pauses = []

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Encontra [PAUSA X seg]
    pattern = r'\[PAUSA\s+(\d+)\s*seg\]'

    for match in re.finditer(pattern, content):
        # Posição aproximada no texto
        position = match.start()
        duration = int(match.group(1))
        pauses.append((position, duration))

    return pauses


# ═══════════════════════════════════════════════════════════════
# GERAÇÃO DE ÁUDIO
# ═══════════════════════════════════════════════════════════════

def load_voice_mapping() -> Dict:
    """Carrega mapeamento de vozes do arquivo de configuração."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"[!] Arquivo de configuracao nao encontrado: {CONFIG_PATH}")
        print("   Usando mapeamento padrão.")
        return get_default_voice_mapping()


def get_default_voice_mapping() -> Dict:
    """Retorna mapeamento padrão (voice_ids precisam ser configurados)."""
    return {
        "NARRATOR": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.7, "similarity_boost": 0.8, "style": 0.3}},
        "CITADOR": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.9, "similarity_boost": 0.9, "style": 0.0}},
        "HORMOZI": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.6}},
        "COLE_GORDON": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.8, "similarity_boost": 0.8, "style": 0.2}},
        "COLE GORDON": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.8, "similarity_boost": 0.8, "style": 0.2}},
        "BRUNSON": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.4, "similarity_boost": 0.7, "style": 0.8}},
        "CRO": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.5, "similarity_boost": 0.7, "style": 0.5}},
        "CFO": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.8, "similarity_boost": 0.8, "style": 0.2}},
        "CMO": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.4}},
        "COO": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.7, "similarity_boost": 0.75, "style": 0.3}},
        "METHODOLOGICAL-CRITIC": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.4}},
        "DEVILS-ADVOCATE": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.5, "similarity_boost": 0.7, "style": 0.6}},
        "SYNTHESIZER": {"voice_id": "NOT_CONFIGURED", "settings": {"stability": 0.8, "similarity_boost": 0.8, "style": 0.2}},
    }


def generate_audio_segment(segment: Segment, voice_mapping: Dict) -> bytes:
    """
    Gera áudio para um segmento usando ElevenLabs.
    """
    if not ELEVENLABS_AVAILABLE:
        raise RuntimeError("ElevenLabs não está instalado")

    # Normalizar nome do speaker
    speaker_key = segment.speaker.upper().replace(" ", "_")

    # Buscar configuração da voz
    voice_config = voice_mapping.get(speaker_key)
    if not voice_config:
        print(f"[!] Voz nao configurada para: {segment.speaker}")
        print(f"   Usando NARRATOR como fallback")
        voice_config = voice_mapping.get("NARRATOR")

    if voice_config["voice_id"] == "NOT_CONFIGURED":
        raise RuntimeError(f"voice_id não configurado para: {segment.speaker}")

    # Gerar áudio
    audio = elevenlabs_client.text_to_speech.convert(
        voice_id=voice_config["voice_id"],
        text=segment.text,
        model_id="eleven_multilingual_v2",
        voice_settings={
            "stability": voice_config["settings"]["stability"],
            "similarity_boost": voice_config["settings"]["similarity_boost"],
            "style": voice_config["settings"].get("style", 0.0),
        }
    )

    return b"".join(audio)


def generate_silence(duration_seconds: float) -> AudioSegment:
    """Gera segmento de silêncio."""
    return AudioSegment.silent(duration=int(duration_seconds * 1000))


# ═══════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def generate_episode_audio(script_path: Path, output_path: Path = None) -> Path:
    """
    Pipeline completo de geração de áudio.

    Args:
        script_path: Caminho para o script .md
        output_path: Caminho para o arquivo de saída (opcional)

    Returns:
        Path do arquivo de áudio gerado
    """
    if not PYDUB_AVAILABLE:
        raise RuntimeError("pydub não está instalado")

    print(f"\n{'='*60}")
    print("[MOVIE] BOARDROOM WARFARE - GERACAO DE AUDIO")
    print(f"{'='*60}\n")

    # 1. Parse do script
    print("[DOC] Parsing do script...")
    segments = parse_script(script_path)
    print(f"   {len(segments)} segmentos encontrados")

    # 2. Carregar mapeamento de vozes
    print("\n[MASK] Carregando mapeamento de vozes...")
    voice_mapping = load_voice_mapping()

    # 3. Verificar API key
    global elevenlabs_client
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY não configurada")
    elevenlabs_client = ElevenLabs(api_key=api_key)
    print("   [OK] API Key configurada")

    # 4. Gerar segmentos de audio
    print("\n[AUDIO] Gerando segmentos de audio...")
    audio_segments = []

    for i, segment in enumerate(segments):
        print(f"   [{i+1}/{len(segments)}] {segment.speaker}: {segment.text[:50]}...")

        try:
            audio_bytes = generate_audio_segment(segment, voice_mapping)

            # Salvar temporariamente
            temp_file = TEMP_PATH / f"segment_{i:04d}.mp3"
            with open(temp_file, 'wb') as f:
                f.write(audio_bytes)

            # Carregar como AudioSegment
            audio_segment = AudioSegment.from_mp3(temp_file)
            audio_segments.append(audio_segment)

            print(f"       [OK] {len(audio_segment)}ms")

        except Exception as e:
            print(f"       [X] Erro: {e}")
            # Adicionar silêncio como placeholder
            audio_segments.append(generate_silence(2))

    # 5. Concatenar
    print("\n[LINK] Concatenando segmentos...")
    final_audio = AudioSegment.empty()

    for i, segment_audio in enumerate(audio_segments):
        final_audio += segment_audio
        # Adicionar pequena pausa entre falas
        final_audio += generate_silence(0.5)

    # 6. Exportar
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_name = script_path.stem
        output_path = OUTPUT_PATH / f"{script_name}_{timestamp}.mp3"

    print(f"\n[SAVE] Exportando para: {output_path}")
    final_audio.export(output_path, format="mp3", bitrate="192k")

    # 7. Limpar arquivos temporarios
    print("\n[CLEAN] Limpando arquivos temporarios...")
    for temp_file in TEMP_PATH.glob("segment_*.mp3"):
        temp_file.unlink()

    # 8. Resumo
    duration_minutes = len(final_audio) / 1000 / 60
    print(f"\n{'='*60}")
    print("[OK] AUDIO GERADO COM SUCESSO")
    print(f"{'='*60}")
    print(f"   [FILE] Arquivo: {output_path}")
    print(f"   [TIME] Duracao: {duration_minutes:.1f} minutos")
    print(f"   [MASK] Vozes: {len(set(s.speaker for s in segments))}")
    print(f"{'='*60}\n")

    return output_path


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Gera áudio a partir de scripts Boardroom Warfare"
    )
    parser.add_argument(
        "script",
        type=Path,
        help="Caminho para o script .md"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Caminho para o arquivo de saída"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas parse o script, não gera áudio"
    )

    args = parser.parse_args()

    if not args.script.exists():
        print(f"[X] Script nao encontrado: {args.script}")
        return 1

    if args.dry_run:
        print("[SEARCH] Modo dry-run: apenas parsing")
        segments = parse_script(args.script)
        print(f"\n{len(segments)} segmentos encontrados:\n")
        for s in segments:
            print(f"  [{s.speaker}] {s.text[:60]}...")
        return 0

    try:
        output_path = generate_episode_audio(args.script, args.output)
        print(f"\n[HEADPHONE] Para ouvir: {output_path}")
        return 0
    except Exception as e:
        print(f"\n[X] Erro: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
