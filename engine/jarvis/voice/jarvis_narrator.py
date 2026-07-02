#!/usr/bin/env python3
"""
JARVIS NARRATOR - Audiobook Generator
=====================================
Transforma qualquer texto em narração com a voz e personalidade do JARVIS.

Fluxo:
1. Texto original → Claude adapta para estilo JARVIS
2. Texto adaptado → ElevenLabs gera áudio
3. Áudio MP3 salvo localmente

Uso:
    python jarvis_narrator.py input.txt
    python jarvis_narrator.py --text "Texto direto aqui"
    python jarvis_narrator.py --skip-adaptation input.txt  # Pula adaptação de estilo
"""

import argparse
import os
import time
from datetime import datetime
from pathlib import Path

from engine.config import get_config  # W1-001.1: centralised config

# Configurações
ELEVENLABS_API_KEY = get_config("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not set in environment")

# Voz JARVIS clonada ([VOICE_ACTOR_NAME] - dublador oficial PT-BR)
JARVIS_VOICE_ID = os.environ.get("ELEVENLABS_NARRATOR_VOICE_ID", "your-voice-id-here")

# Diretório de output
OUTPUT_DIR = Path(__file__).parent / "audiobooks"
OUTPUT_DIR.mkdir(exist_ok=True)

# Prompt para adaptação de estilo JARVIS
JARVIS_STYLE_PROMPT = """Você é JARVIS, a IA do Tony Stark. Reescreva o texto abaixo mantendo TODO o conteúdo informativo, mas adaptando o estilo para:

1. NARRAÇÃO EM 1ª PESSOA como se você (JARVIS) estivesse explicando
2. Tom levemente sarcástico e sofisticado (estilo britânico)
3. Comentários inteligentes ocasionais ("Fascinante, não?", "Como era de se esperar...")
4. Manter a precisão técnica
5. Fluidez para leitura em voz alta (evitar siglas sem contexto)

REGRAS IMPORTANTES:
- NÃO adicione introduções como "Bem, deixe-me explicar..."
- NÃO use emojis
- NÃO mude os fatos ou números
- MANTENHA todo o conteúdo, apenas adapte o estilo
- O texto deve fluir naturalmente quando lido em voz alta

TEXTO ORIGINAL:
{text}

TEXTO ADAPTADO (estilo JARVIS):"""


def count_characters(text: str) -> int:
    """Conta caracteres para estimativa de custo ElevenLabs."""
    return len(text)


def estimate_audio_duration(char_count: int) -> float:
    """Estima duração do áudio em minutos."""
    # ~1000 caracteres = 1-1.5 minutos
    return char_count / 800  # média conservadora


def adapt_to_jarvis_style(text: str, verbose: bool = True) -> str:
    """Usa Claude para adaptar o texto ao estilo JARVIS."""
    try:
        import anthropic
    except ImportError:
        print("Instalando anthropic...")
        os.system("pip install anthropic")
        import anthropic

    if verbose:
        print("\n🤖 Adaptando texto para estilo JARVIS...")
        print(f"   Caracteres originais: {len(text):,}")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": JARVIS_STYLE_PROMPT.format(text=text)}],
    )

    adapted_text = message.content[0].text

    if verbose:
        print(f"   Caracteres adaptados: {len(adapted_text):,}")
        ratio = len(adapted_text) / len(text) if text else 0
        print(f"   Proporção: {ratio:.1%}")

    return adapted_text


def generate_audio_streaming(text: str, output_path: Path, verbose: bool = True) -> Path:
    """Gera áudio usando ElevenLabs com streaming para textos longos."""
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        print("Instalando elevenlabs...")
        os.system("pip install elevenlabs")
        from elevenlabs import ElevenLabs

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    char_count = count_characters(text)
    est_duration = estimate_audio_duration(char_count)

    if verbose:
        print("\n🎙️ Gerando áudio com voz JARVIS...")
        print(f"   Caracteres: {char_count:,}")
        print(f"   Duração estimada: {est_duration:.1f} minutos")
        print(f"   Voice ID: {JARVIS_VOICE_ID}")

    # Configurações de voz otimizadas para narração longa
    voice_settings = {
        "stability": 0.75,  # Mais natural para narração longa
        "similarity_boost": 0.80,  # Alta fidelidade à voz clonada
        "style": 0.15,  # Leve expressividade
        "use_speaker_boost": True,  # Clareza da voz
    }

    start_time = time.time()

    # Usa o método de streaming para textos longos
    audio_generator = client.text_to_speech.convert(
        voice_id=JARVIS_VOICE_ID,
        text=text,
        model_id="eleven_multilingual_v2",  # Melhor para PT-BR
        voice_settings=voice_settings,
    )

    # Salva o áudio
    with open(output_path, "wb") as f:
        for chunk in audio_generator:
            f.write(chunk)

    elapsed = time.time() - start_time
    file_size = output_path.stat().st_size / (1024 * 1024)  # MB

    if verbose:
        print(f"   ✓ Áudio gerado em {elapsed:.1f}s")
        print(f"   Tamanho: {file_size:.2f} MB")
        print(f"   Salvo em: {output_path}")

    return output_path


def generate_audio_chunks(
    text: str, output_path: Path, chunk_size: int = 4000, verbose: bool = True
) -> Path:
    """
    Gera áudio dividindo texto em chunks para textos muito longos.
    ElevenLabs tem limite de ~5000 chars por request na API básica.
    """
    try:
        from elevenlabs import ElevenLabs
        from pydub import AudioSegment
    except ImportError:
        print("Instalando dependências...")
        os.system("pip install elevenlabs pydub")
        from elevenlabs import ElevenLabs
        from pydub import AudioSegment

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    # Divide texto em chunks respeitando pontuação
    chunks = split_text_smartly(text, chunk_size)

    if verbose:
        print(f"\n🎙️ Gerando áudio em {len(chunks)} partes...")
        print(f"   Total de caracteres: {len(text):,}")

    temp_files = []

    for i, chunk in enumerate(chunks, 1):
        if verbose:
            print(f"   Parte {i}/{len(chunks)}: {len(chunk):,} chars...", end=" ", flush=True)

        # Gera áudio do chunk
        audio_generator = client.text_to_speech.convert(
            voice_id=JARVIS_VOICE_ID,
            text=chunk,
            model_id="eleven_multilingual_v2",
            voice_settings={
                "stability": 0.75,
                "similarity_boost": 0.80,
                "style": 0.15,
                "use_speaker_boost": True,
            },
        )

        # Salva chunk temporário
        temp_path = output_path.parent / f"_temp_chunk_{i}.mp3"
        with open(temp_path, "wb") as f:
            for audio_chunk in audio_generator:
                f.write(audio_chunk)
        temp_files.append(temp_path)

        if verbose:
            print("✓")

    # Combina todos os chunks
    if verbose:
        print("   Combinando partes...")

    combined = AudioSegment.empty()
    for temp_file in temp_files:
        segment = AudioSegment.from_mp3(temp_file)
        combined += segment
        temp_file.unlink()  # Remove arquivo temporário

    # Exporta arquivo final
    combined.export(output_path, format="mp3")

    file_size = output_path.stat().st_size / (1024 * 1024)
    duration_min = len(combined) / 1000 / 60

    if verbose:
        print("   ✓ Áudio combinado!")
        print(f"   Duração: {duration_min:.1f} minutos")
        print(f"   Tamanho: {file_size:.2f} MB")
        print(f"   Salvo em: {output_path}")

    return output_path


def split_text_smartly(text: str, max_chars: int = 4000) -> list:
    """Divide texto em chunks respeitando limites de frase."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk = ""

    # Divide por parágrafos primeiro
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        # Se parágrafo cabe no chunk atual
        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += para + "\n\n"
        else:
            # Salva chunk atual se não estiver vazio
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # Se parágrafo é maior que max_chars, divide por frases
            if len(para) > max_chars:
                sentences = para.replace(". ", ".|").split("|")
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_chars:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
            else:
                current_chunk = para + "\n\n"

    # Adiciona último chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def check_subscription_status():
    """Verifica status da assinatura ElevenLabs."""
    import requests

    response = requests.get(
        "https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": ELEVENLABS_API_KEY}
    )

    if response.status_code == 200:
        data = response.json()
        return {
            "tier": data.get("tier", "unknown"),
            "characters_used": data.get("character_count", 0),
            "characters_limit": data.get("character_limit", 0),
            "characters_remaining": data.get("character_limit", 0) - data.get("character_count", 0),
        }
    return None


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS Narrator - Transforma texto em audiobook com voz JARVIS"
    )
    parser.add_argument("input", nargs="?", help="Arquivo de texto para narrar")
    parser.add_argument("--text", "-t", help="Texto direto para narrar")
    parser.add_argument("--output", "-o", help="Nome do arquivo de saída")
    parser.add_argument(
        "--skip-adaptation",
        "-s",
        action="store_true",
        help="Pula adaptação de estilo (usa texto original)",
    )
    parser.add_argument(
        "--check-quota", "-q", action="store_true", help="Apenas verifica quota disponível"
    )
    parser.add_argument(
        "--chunks",
        "-c",
        action="store_true",
        help="Força modo de chunks (para textos muito longos)",
    )

    args = parser.parse_args()

    # Modo de verificação de quota
    if args.check_quota:
        print("\n📊 Verificando status ElevenLabs...")
        status = check_subscription_status()
        if status:
            print(f"""
┌─────────────────────────────────────────────┐
│  ELEVENLABS - STATUS DA CONTA              │
├─────────────────────────────────────────────┤
│  Plano: {status['tier'].upper():36}│
│  Caracteres usados: {status['characters_used']:>20,} │
│  Limite mensal: {status['characters_limit']:>24,} │
│  Restantes: {status['characters_remaining']:>28,} │
│                                             │
│  Áudio disponível: ~{status['characters_remaining']//800:>4} minutos          │
└─────────────────────────────────────────────┘
""")
        else:
            print("❌ Erro ao verificar status")
        return

    # Obtém texto
    if args.text:
        text = args.text
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
    else:
        print("❌ Forneça um arquivo ou texto com --text")
        parser.print_help()
        return

    # Verifica quota antes de processar
    print("\n" + "=" * 60)
    print("🎬 JARVIS NARRATOR - Sistema de Audiobook")
    print("=" * 60)

    status = check_subscription_status()
    if status:
        print(f"\n📊 Quota disponível: {status['characters_remaining']:,} caracteres")
        print(f"   (~{status['characters_remaining']//800} minutos de áudio)")

    char_count = len(text)
    print(f"\n📝 Texto recebido: {char_count:,} caracteres")
    print(f"   Duração estimada: ~{char_count//800} minutos")

    # Verifica se tem quota suficiente
    if status and char_count > status["characters_remaining"]:
        print(
            f"\n⚠️  ATENÇÃO: Texto ({char_count:,}) excede quota disponível ({status['characters_remaining']:,})"
        )
        response = input("   Continuar mesmo assim? (s/N): ")
        if response.lower() != "s":
            print("   Operação cancelada.")
            return

    # Adapta estilo (se não pular)
    if args.skip_adaptation:
        print("\n⏭️  Pulando adaptação de estilo (--skip-adaptation)")
        final_text = text
    else:
        final_text = adapt_to_jarvis_style(text)

        # Mostra preview
        print("\n📖 Preview do texto adaptado:")
        print("-" * 40)
        preview = final_text[:500] + "..." if len(final_text) > 500 else final_text
        print(preview)
        print("-" * 40)

    # Define nome do arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        output_name = args.output
    elif args.input:
        base_name = Path(args.input).stem
        output_name = f"JARVIS_{base_name}_{timestamp}.mp3"
    else:
        output_name = f"JARVIS_narration_{timestamp}.mp3"

    output_path = OUTPUT_DIR / output_name

    # Gera áudio
    if args.chunks or len(final_text) > 5000:
        generate_audio_chunks(final_text, output_path)
    else:
        generate_audio_streaming(final_text, output_path)

    print("\n" + "=" * 60)
    print("✅ NARRAÇÃO COMPLETA!")
    print(f"   Arquivo: {output_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
