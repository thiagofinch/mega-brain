#!/usr/bin/env python3
"""
BOARDROOM WARFARE - Audio Generator (Edge TTS)
Gera arquivos de audio a partir de scripts .md usando Edge TTS (gratuito)

Uso:
    python audio_generator_edge.py <script.md> [--output <output.mp3>]
"""

import os
import re
import asyncio
import argparse
from pathlib import Path
from typing import List
from dataclasses import dataclass
from datetime import datetime

# Configurar ffmpeg/ffprobe ANTES de importar pydub (Windows requirement)
_ffmpeg_bin = Path(r"C:\ffmpeg\bin")
_ffmpeg_path = _ffmpeg_bin / "ffmpeg.exe"
_ffprobe_path = _ffmpeg_bin / "ffprobe.exe"

if _ffmpeg_path.exists() and _ffprobe_path.exists():
    os.environ["FFMPEG_BINARY"] = str(_ffmpeg_path)
    os.environ["FFPROBE_BINARY"] = str(_ffprobe_path)
    os.environ["PATH"] = str(_ffmpeg_bin) + os.pathsep + os.environ.get("PATH", "")
    print(f"[OK] ffmpeg configurado: {_ffmpeg_path}")
else:
    print("[!] ffmpeg/ffprobe nao encontrados no caminho esperado")

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("[!] edge-tts nao instalado. Use: pip install edge-tts")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    AudioSegment.converter = str(_ffmpeg_path)
    AudioSegment.ffprobe = str(_ffprobe_path)
except ImportError:
    PYDUB_AVAILABLE = False
    print("[!] pydub nao instalado. Use: pip install pydub")


# ═══════════════════════════════════════════════════════════════
# CONFIGURACAO
# ═══════════════════════════════════════════════════════════════

OUTPUT_PATH = Path(__file__).parent.parent / "outputs" / "AUDIO"
TEMP_PATH = Path(__file__).parent.parent / "outputs" / "temp"

OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
TEMP_PATH.mkdir(parents=True, exist_ok=True)

# Mapeamento de vozes Edge TTS para speakers
# Vozes disponiveis pt-BR:
#   - pt-BR-AntonioNeural (Male) - voz grave, autoritaria
#   - pt-BR-FranciscaNeural (Female) - voz feminina padrao
#   - pt-BR-ThalitaMultilingualNeural (Female) - voz feminina multilingual

VOICE_MAPPING = {
    # Narracao principal - voz masculina grave
    "NARRATOR": "pt-BR-AntonioNeural",

    # Citador - voz neutra, feminina para contrastar
    "CITADOR": "pt-BR-FranciscaNeural",

    # C-Level executivos - alternar para diferenciar
    "CRO": "pt-BR-AntonioNeural",      # Revenue - assertivo
    "CFO": "pt-BR-FranciscaNeural",    # Finance - analitico

    # Council - vozes distintas
    "METHODOLOGICAL-CRITIC": "pt-BR-ThalitaMultilingualNeural",  # Critico
    "DEVILS-ADVOCATE": "pt-BR-AntonioNeural",                     # Provocador
    "SYNTHESIZER": "pt-BR-FranciscaNeural",                       # Sintetizador

    # Fallback
    "DEFAULT": "pt-BR-AntonioNeural"
}

# Ajustes de rate/pitch por speaker para diferenciar vozes iguais
VOICE_ADJUSTMENTS = {
    "NARRATOR": {"rate": "-5%", "pitch": "-5Hz"},      # Mais lento, mais grave
    "CITADOR": {"rate": "+0%", "pitch": "+0Hz"},       # Neutro
    "CRO": {"rate": "+10%", "pitch": "+0Hz"},          # Mais rapido, energico
    "CFO": {"rate": "-5%", "pitch": "+5Hz"},           # Mais lento, analitico
    "METHODOLOGICAL-CRITIC": {"rate": "+0%", "pitch": "-3Hz"},
    "DEVILS-ADVOCATE": {"rate": "+15%", "pitch": "+3Hz"},  # Agressivo
    "SYNTHESIZER": {"rate": "-10%", "pitch": "+0Hz"},      # Calmo, ponderado
}


@dataclass
class Segment:
    """Representa um segmento de audio a ser gerado."""
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
    (instrucao opcional)
    "Texto da fala"
    """
    segments = []

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex para capturar falas
    pattern = r'\[([A-Z_-]+)\]\s*(?:\(([^)]+)\))?\s*\n([^\[\n]+(?:\n(?!\[)[^\[\n]+)*)'

    matches = re.findall(pattern, content)

    for i, (speaker, instruction, text) in enumerate(matches):
        # Limpar texto
        text = text.strip()
        text = re.sub(r'^["\']|["\']$', '', text)  # Remove aspas
        text = re.sub(r'\[PAUSA.*?\]', '', text)    # Remove marcacoes de pausa
        text = re.sub(r'\[SOM:.*?\]', '', text)     # Remove marcacoes de som
        text = text.strip()

        if text:
            segments.append(Segment(
                index=i,
                speaker=speaker.strip(),
                text=text,
                instruction=instruction.strip() if instruction else ""
            ))

    return segments


# ═══════════════════════════════════════════════════════════════
# GERACAO DE AUDIO
# ═══════════════════════════════════════════════════════════════

async def generate_audio_segment(segment: Segment, output_file: Path) -> bool:
    """
    Gera audio para um segmento usando Edge TTS.
    """
    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError("edge-tts nao esta instalado")

    # Buscar voz para o speaker
    speaker_key = segment.speaker.upper().replace(" ", "-")
    voice = VOICE_MAPPING.get(speaker_key, VOICE_MAPPING["DEFAULT"])

    # Buscar ajustes de voz
    adjustments = VOICE_ADJUSTMENTS.get(speaker_key, {"rate": "+0%", "pitch": "+0Hz"})

    try:
        communicate = edge_tts.Communicate(
            text=segment.text,
            voice=voice,
            rate=adjustments["rate"],
            pitch=adjustments["pitch"]
        )

        await communicate.save(str(output_file))
        return True

    except Exception as e:
        print(f"       [X] Erro Edge TTS: {e}")
        return False


def generate_silence(duration_seconds: float) -> AudioSegment:
    """Gera segmento de silencio."""
    return AudioSegment.silent(duration=int(duration_seconds * 1000))


# ═══════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

async def generate_episode_audio(script_path: Path, output_path: Path = None) -> Path:
    """
    Pipeline completo de geracao de audio.

    Args:
        script_path: Caminho para o script .md
        output_path: Caminho para o arquivo de saida (opcional)

    Returns:
        Path do arquivo de audio gerado
    """
    if not PYDUB_AVAILABLE:
        raise RuntimeError("pydub nao esta instalado")

    print(f"\n{'='*60}")
    print("[MOVIE] BOARDROOM WARFARE - GERACAO DE AUDIO (Edge TTS)")
    print(f"{'='*60}\n")

    # 1. Parse do script
    print("[DOC] Parsing do script...")
    segments = parse_script(script_path)
    print(f"   {len(segments)} segmentos encontrados")

    # Mostrar speakers unicos
    unique_speakers = set(s.speaker for s in segments)
    print(f"   Speakers: {', '.join(sorted(unique_speakers))}")

    # 2. Gerar segmentos de audio
    print("\n[AUDIO] Gerando segmentos de audio...")
    audio_segments = []

    for i, segment in enumerate(segments):
        speaker_display = segment.speaker[:15].ljust(15)
        text_preview = segment.text[:40] + "..." if len(segment.text) > 40 else segment.text
        print(f"   [{i+1:02d}/{len(segments):02d}] {speaker_display} {text_preview}")

        temp_file = TEMP_PATH / f"segment_{i:04d}.mp3"

        try:
            success = await generate_audio_segment(segment, temp_file)

            if success and temp_file.exists():
                audio_segment = AudioSegment.from_mp3(temp_file)
                audio_segments.append(audio_segment)
                duration_sec = len(audio_segment) / 1000
                print(f"       [OK] {duration_sec:.1f}s")
            else:
                print(f"       [!] Usando silencio como placeholder")
                audio_segments.append(generate_silence(2))

        except Exception as e:
            print(f"       [X] Erro: {e}")
            audio_segments.append(generate_silence(2))

    # 3. Concatenar
    print("\n[LINK] Concatenando segmentos...")
    final_audio = AudioSegment.empty()

    for i, segment_audio in enumerate(audio_segments):
        final_audio += segment_audio
        # Pausa entre falas baseada no tipo de transicao
        if i < len(segments) - 1:
            current_speaker = segments[i].speaker
            next_speaker = segments[i + 1].speaker

            # Pausa maior entre speakers diferentes
            if current_speaker != next_speaker:
                final_audio += generate_silence(0.8)
            else:
                final_audio += generate_silence(0.4)

    # 4. Exportar
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_name = script_path.stem
        output_path = OUTPUT_PATH / f"{script_name}_{timestamp}.mp3"

    print(f"\n[SAVE] Exportando para: {output_path}")
    final_audio.export(output_path, format="mp3", bitrate="192k")

    # 5. Limpar arquivos temporarios
    print("\n[CLEAN] Limpando arquivos temporarios...")
    for temp_file in TEMP_PATH.glob("segment_*.mp3"):
        temp_file.unlink()

    # 6. Resumo
    duration_minutes = len(final_audio) / 1000 / 60
    print(f"\n{'='*60}")
    print("[OK] AUDIO GERADO COM SUCESSO")
    print(f"{'='*60}")
    print(f"   [FILE] Arquivo: {output_path}")
    print(f"   [TIME] Duracao: {duration_minutes:.1f} minutos")
    print(f"   [MASK] Vozes: {len(unique_speakers)}")
    print(f"   [COST] Custo: GRATUITO (Edge TTS)")
    print(f"{'='*60}\n")

    return output_path


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Gera audio a partir de scripts Boardroom Warfare (Edge TTS - gratuito)"
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
        help="Caminho para o arquivo de saida"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas parse o script, nao gera audio"
    )

    args = parser.parse_args()

    if not args.script.exists():
        print(f"[X] Script nao encontrado: {args.script}")
        return 1

    if args.dry_run:
        print("[SEARCH] Modo dry-run: apenas parsing")
        segments = parse_script(args.script)
        print(f"\n{len(segments)} segmentos encontrados:\n")

        # Agrupar por speaker
        speaker_counts = {}
        for s in segments:
            speaker_counts[s.speaker] = speaker_counts.get(s.speaker, 0) + 1

        print("Contagem por speaker:")
        for speaker, count in sorted(speaker_counts.items()):
            voice = VOICE_MAPPING.get(speaker, VOICE_MAPPING["DEFAULT"])
            print(f"  {speaker}: {count} falas -> {voice}")

        print("\nPrimeiros 5 segmentos:")
        for s in segments[:5]:
            print(f"  [{s.speaker}] {s.text[:60]}...")
        return 0

    try:
        output_path = asyncio.run(generate_episode_audio(args.script, args.output))
        print(f"\n[HEADPHONE] Para ouvir: {output_path}")
        return 0
    except Exception as e:
        print(f"\n[X] Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
