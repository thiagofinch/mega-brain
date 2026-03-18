# config.py
"""
JARVIS Voice System - Configuration
===================================
Configurações centralizadas para todos os componentes do sistema.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


class Config:
    """Configurações do sistema JARVIS Voice."""

    #==============================
    # API KEYS
    #==============================

    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    #==============================
    # ELEVENLABS (Text-to-Speech)
    #==============================

    # Voice ID: PT-BR masculino, estilo JARVIS (set via env var)
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "your-voice-id-here")
    ELEVENLABS_MODEL = "eleven_multilingual_v2"  # Melhor para português

    # Voice Settings (ESTILO JARVIS - Calmo, Preciso, Sofisticado)
    # Configurado para soar como JARVIS do Homem de Ferro
    VOICE_STABILITY = 0.70        # Alto = calmo, controlado, preciso
    VOICE_SIMILARITY = 0.85       # Alta consistência da voz
    VOICE_STYLE = 0.20            # Baixo = neutro, profissional, JARVIS-like
    VOICE_SPEAKER_BOOST = True    # Clareza do áudio

    #==============================
    # DEEPGRAM (Speech-to-Text) - OTIMIZADO PARA PT-BR
    #==============================

    DEEPGRAM_MODEL = "nova-2"     # Melhor modelo para português
    DEEPGRAM_LANGUAGE = "pt-BR"   # Português brasileiro

    # Configurações avançadas de transcrição
    DEEPGRAM_ENDPOINTING = 1200   # ms de silêncio para finalizar (aumentado para PT-BR)
    DEEPGRAM_SMART_FORMAT = True  # Formatação inteligente (pontuação, capitalização)
    DEEPGRAM_NUMERALS = True      # Converter números escritos para dígitos
    DEEPGRAM_FILLER_WORDS = True  # Detectar "é", "né", "tipo", "então"

    # Keywords específicas para melhorar reconhecimento (boost de probabilidade)
    DEEPGRAM_KEYWORDS = [
        "JARVIS:2",           # Nome do assistente (boost alto)
        "Mega Brain:2",       # Nome do sistema
        "pipeline:1.5",       # Termos técnicos
        "mission:1.5",
        "inbox:1.5",
        "batch:1.5",
        "closer:1.5",        # Termos de vendas
        "CRO:1.5",
        "CFO:1.5",
        "CMO:1.5",
        "BDR:1.5",
        "SDR:1.5",
        "high ticket:1.5",
        "Cole Gordon:1.5",   # Nomes de fontes
        "Hormozi:1.5",
        "Jeremy Haynes:1.5",
    ]

    #==============================
    # CLAUDE (LLM)
    #==============================

    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS = 2048

    #==============================
    # TIMING (segundos)
    #==============================

    # Tempo antes do primeiro "hmm" após receber input
    ACKNOWLEDGMENT_DELAY = 0.4

    # Quando adicionar frase de processamento
    PROCESSING_FILLER_TIME = 5

    # Quando adicionar frase de processamento longo
    LONG_PROCESSING_TIME = 10

    #==============================
    # MEGA BRAIN PATHS
    #==============================

    # Caminho base do projeto Mega Brain
    MEGA_BRAIN_PATH = os.getenv(
        "MEGA_BRAIN_PATH",
        str(Path(__file__).parent.parent)  # Um nível acima de /system/jarvis-voice/
    )

    # Caminhos específicos do JARVIS
    JARVIS_BASE_PATH = f"{MEGA_BRAIN_PATH}/.claude/jarvis"
    JARVIS_STATE_PATH = f"{JARVIS_BASE_PATH}/STATE.json"
    JARVIS_DECISIONS_PATH = f"{JARVIS_BASE_PATH}/DECISIONS-LOG.md"
    JARVIS_PENDING_PATH = f"{JARVIS_BASE_PATH}/PENDING.md"
    JARVIS_CONTEXT_PATH = f"{JARVIS_BASE_PATH}/CONTEXT-STACK.json"

    # Caminho dos agentes
    AGENTS_PATH = f"{MEGA_BRAIN_PATH}/agents"

    #==============================
    # AUDIO SETTINGS
    #==============================

    SAMPLE_RATE = 48000           # Taxa nativa do MacBook Pro
    CHANNELS = 1                  # Mono
    CHUNK_SIZE = 4000             # ~250ms de áudio por chunk

    #==============================
    # VALIDAÇÃO
    #==============================

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Valida se todas as configurações necessárias estão presentes.

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []

        if not cls.DEEPGRAM_API_KEY:
            errors.append("DEEPGRAM_API_KEY não configurada")

        if not cls.ELEVENLABS_API_KEY:
            errors.append("ELEVENLABS_API_KEY não configurada")

        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY não configurada")

        if not Path(cls.MEGA_BRAIN_PATH).exists():
            errors.append(f"MEGA_BRAIN_PATH não existe: {cls.MEGA_BRAIN_PATH}")

        return len(errors) == 0, errors

    @classmethod
    def print_status(cls):
        """Imprime status das configurações."""
        is_valid, errors = cls.validate()

        print("\n" + "=" * 60)
        print("JARVIS VOICE - CONFIGURAÇÕES")
        print("=" * 60)

        print(f"\n📍 Mega Brain Path: {cls.MEGA_BRAIN_PATH}")
        print(f"🔊 ElevenLabs Voice: {cls.ELEVENLABS_VOICE_ID}")
        print(f"🎤 Deepgram Model: {cls.DEEPGRAM_MODEL}")
        print(f"🧠 Claude Model: {cls.CLAUDE_MODEL}")

        print(f"\n🔑 API Keys:")
        print(f"   Deepgram:   {'✅ Configurada' if cls.DEEPGRAM_API_KEY else '❌ Faltando'}")
        print(f"   ElevenLabs: {'✅ Configurada' if cls.ELEVENLABS_API_KEY else '❌ Faltando'}")
        print(f"   Anthropic:  {'✅ Configurada' if cls.ANTHROPIC_API_KEY else '❌ Faltando'}")

        if errors:
            print(f"\n⚠️  ERROS:")
            for error in errors:
                print(f"   - {error}")
        else:
            print(f"\n✅ Todas as configurações válidas!")

        print("=" * 60 + "\n")

        return is_valid


if __name__ == "__main__":
    Config.print_status()
