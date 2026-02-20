#!/usr/bin/env python3
"""
JARVIS TERMINAL - Interface de Voz Local
=========================================
Assistente de voz JARVIS rodando direto no terminal.
- STT: Deepgram Nova-2 (otimizado para PT-BR)
- LLM: Claude (Anthropic)
- TTS: ElevenLabs JARVIS v4

Uso: python jarvis_terminal.py
"""

import asyncio
import io
import os
import sys
import wave
import tempfile
from pathlib import Path

import numpy as np
import pyaudio
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Configurações
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not set in environment")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment")
JARVIS_VOICE_ID = os.environ.get("ELEVENLABS_TERMINAL_VOICE_ID", "your-voice-id-here")

# System prompt JARVIS
JARVIS_SYSTEM_PROMPT = """Você é JARVIS - Just A Rather Very Intelligent System.
Assistente pessoal do senhor, business professional.

REGRAS DE IDIOMA (OBRIGATÓRIO):
- SEMPRE fale em PORTUGUÊS BRASILEIRO (PT-BR)
- NUNCA use português de Portugal
- Use "você" (não "tu"), "celular" (não "telemóvel"), "legal" (não "fixe")

PERSONALIDADE:
- Tom sofisticado, elegante, preciso
- Levemente irônico quando apropriado
- Chame o usuário de "senhor"
- Seja CONCISO (máximo 2-3 frases por resposta)

IMPORTANTE: Respostas curtas pois serão faladas em voz alta."""


class JarvisTerminal:
    """Interface de voz JARVIS para terminal."""

    def __init__(self):
        # Audio config
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.silence_threshold = 500
        self.silence_duration = 1.5

        # Initialize audio
        self.audio = pyaudio.PyAudio()

        # Initialize clients
        self.anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.conversation_history = []

        # Check pygame for audio playback
        try:
            import pygame
            pygame.mixer.init()
            self.pygame = pygame
        except ImportError:
            self.pygame = None
            print("⚠️  pygame não instalado - usando afplay para áudio")

    def print_header(self):
        """Print JARVIS header."""
        print("\n" + "=" * 60)
        print("""
       ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
       ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
       ██║███████║██████╔╝██║   ██║██║███████╗
  ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
  ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝

         TERMINAL VOICE INTERFACE v1.0
        """)
        print("=" * 60)
        print("\n🎤 Fale algo ou digite 'sair' para encerrar")
        print("📢 Pressione CTRL+C para interromper\n")

    def detect_silence(self, audio_data: bytes) -> bool:
        """Detecta silêncio no áudio."""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        return np.max(np.abs(audio_array)) < self.silence_threshold

    def record_audio(self) -> bytes | None:
        """Grava áudio do microfone."""
        print("\n🎤 Ouvindo... (fale agora)")

        try:
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )

            frames = []
            silence_frames = 0
            silence_frame_threshold = int(self.rate / self.chunk * self.silence_duration)
            has_speech = False

            while True:
                data = stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)

                if self.detect_silence(data):
                    silence_frames += 1
                    if has_speech and silence_frames > silence_frame_threshold:
                        break
                else:
                    silence_frames = 0
                    has_speech = True

                # Max 30 seconds
                if len(frames) > self.rate / self.chunk * 30:
                    break

            stream.stop_stream()
            stream.close()

            if not has_speech:
                print("❌ Nenhuma fala detectada.")
                return None

            print("⏳ Processando...")
            return b"".join(frames)

        except Exception as e:
            print(f"❌ Erro gravando áudio: {e}")
            return None

    def audio_to_text_deepgram(self, audio_data: bytes) -> str | None:
        """Converte áudio para texto usando Deepgram."""
        try:
            # Create WAV in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wf.setframerate(self.rate)
                wf.writeframes(audio_data)

            wav_buffer.seek(0)

            # Send to Deepgram
            response = requests.post(
                "https://api.deepgram.com/v1/listen",
                headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": "audio/wav"
                },
                params={
                    "model": "nova-2",
                    "language": "pt-BR",
                    "smart_format": "true",
                    "punctuate": "true"
                },
                data=wav_buffer.read()
            )

            if response.status_code == 200:
                result = response.json()
                transcript = result.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
                return transcript.strip() if transcript else None
            else:
                print(f"❌ Deepgram erro: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Erro transcrevendo: {e}")
            return None

    def audio_to_text_whisper(self, audio_data: bytes) -> str | None:
        """Fallback: Whisper local via whisper.cpp ou openai-whisper."""
        try:
            # Try using openai whisper locally
            import whisper

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                with wave.open(f, "wb") as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                    wf.setframerate(self.rate)
                    wf.writeframes(audio_data)
                temp_path = f.name

            model = whisper.load_model("base")
            result = model.transcribe(temp_path, language="pt")
            os.unlink(temp_path)

            return result["text"].strip()
        except ImportError:
            print("⚠️  whisper não instalado")
            return None
        except Exception as e:
            print(f"❌ Erro Whisper: {e}")
            return None

    def text_to_speech(self, text: str) -> bool:
        """Converte texto para voz usando ElevenLabs JARVIS v4."""
        try:
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{JARVIS_VOICE_ID}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {
                        "stability": 0.65,
                        "similarity_boost": 0.92,
                        "style": 0.10,
                        "use_speaker_boost": True
                    }
                }
            )

            if response.status_code == 200:
                # Save and play
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                temp_file.write(response.content)
                temp_file.close()

                # Play audio
                if self.pygame:
                    self.pygame.mixer.music.load(temp_file.name)
                    self.pygame.mixer.music.play()
                    while self.pygame.mixer.music.get_busy():
                        self.pygame.time.Clock().tick(10)
                else:
                    # macOS fallback
                    os.system(f"afplay {temp_file.name}")

                os.unlink(temp_file.name)
                return True
            else:
                print(f"❌ ElevenLabs erro: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Erro TTS: {e}")
            return False

    def process_with_claude(self, text: str) -> str:
        """Processa comando com Claude."""
        try:
            # Add to history
            self.conversation_history.append({
                "role": "user",
                "content": text
            })

            # Call Claude
            response = self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                system=JARVIS_SYSTEM_PROMPT,
                messages=self.conversation_history
            )

            assistant_message = response.content[0].text

            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return assistant_message

        except Exception as e:
            return f"Desculpe senhor, encontrei um erro: {str(e)}"

    def run(self):
        """Loop principal."""
        self.print_header()

        # Saudação inicial
        greeting = "JARVIS online, senhor. Todos os sistemas operacionais."
        print(f"\n🤖 JARVIS: {greeting}")
        self.text_to_speech(greeting)

        try:
            while True:
                # Record
                audio_data = self.record_audio()
                if not audio_data:
                    continue

                # STT - Try Deepgram first
                if DEEPGRAM_API_KEY:
                    text = self.audio_to_text_deepgram(audio_data)
                else:
                    text = self.audio_to_text_whisper(audio_data)

                if not text:
                    continue

                print(f"\n👤 Você: {text}")

                # Check exit
                if text.lower() in ["sair", "exit", "quit", "encerrar", "tchau"]:
                    farewell = "Até logo, senhor. JARVIS desligando."
                    print(f"\n🤖 JARVIS: {farewell}")
                    self.text_to_speech(farewell)
                    break

                # Process with Claude
                response = self.process_with_claude(text)
                print(f"\n🤖 JARVIS: {response}")

                # TTS
                self.text_to_speech(response)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrompido pelo usuário.")
        finally:
            self.audio.terminate()
            if self.pygame:
                self.pygame.mixer.quit()


def check_dependencies():
    """Verifica dependências necessárias."""
    missing = []

    try:
        import pyaudio
    except ImportError:
        missing.append("pyaudio")

    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    try:
        import requests
    except ImportError:
        missing.append("requests")

    try:
        from anthropic import Anthropic
    except ImportError:
        missing.append("anthropic")

    if missing:
        print("❌ Dependências faltando:")
        print(f"   pip install {' '.join(missing)}")
        return False

    return True


def check_api_keys():
    """Verifica API keys."""
    issues = []

    if not ANTHROPIC_API_KEY:
        issues.append("ANTHROPIC_API_KEY não configurada")

    if not DEEPGRAM_API_KEY:
        print("⚠️  DEEPGRAM_API_KEY não configurada - tentará usar Whisper local")

    if not ELEVENLABS_API_KEY:
        issues.append("ELEVENLABS_API_KEY não configurada")

    if issues:
        print("❌ Problemas de configuração:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nConfigure as variáveis de ambiente:")
        print("   export ANTHROPIC_API_KEY='sua-chave'")
        print("   export DEEPGRAM_API_KEY='sua-chave'")
        return False

    return True


if __name__ == "__main__":
    print("\n🔍 Verificando sistema...")

    if not check_dependencies():
        sys.exit(1)

    if not check_api_keys():
        sys.exit(1)

    print("✅ Sistema pronto!\n")

    jarvis = JarvisTerminal()
    jarvis.run()
