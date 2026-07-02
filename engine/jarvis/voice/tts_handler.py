# tts_handler.py
"""
JARVIS Voice System - Text-to-Speech Handler (ElevenLabs)
=========================================================
Gerencia Text-to-Speech via ElevenLabs.
Faz JARVIS falar com voz natural e personalidade.

Configurações otimizadas para naturalidade:
- stability baixo = mais variação humana
- similarity_boost médio = consistência
- style = expressividade emocional
"""

import asyncio
import io
import queue
import threading
from typing import Optional

import sounddevice as sd
from config import Config

# Tenta importar elevenlabs - versões diferentes têm APIs diferentes
try:
    from elevenlabs import ElevenLabs

    ELEVENLABS_V2 = True
except ImportError:
    try:
        from elevenlabs import Voice, VoiceSettings, generate, set_api_key, stream

        ELEVENLABS_V2 = False
    except ImportError:
        raise ImportError("ElevenLabs não instalado. Execute: pip install elevenlabs")


class TTSHandler:
    """
    Gerencia Text-to-Speech via ElevenLabs.
    Faz JARVIS falar com voz natural.
    """

    def __init__(self):
        self.config = Config()
        self._audio_queue = queue.Queue()
        self._is_speaking = False
        self._playback_thread: Optional[threading.Thread] = None

        # Inicializa cliente baseado na versão do SDK
        if ELEVENLABS_V2:
            self._init_v2()
        else:
            self._init_v1()

        print(f"[TTS] Inicializado com voz: {self.config.ELEVENLABS_VOICE_ID}")

    def _init_v1(self):
        """Inicializa SDK v1 (elevenlabs < 1.0)."""
        set_api_key(self.config.ELEVENLABS_API_KEY)

        self.voice_settings = VoiceSettings(
            stability=self.config.VOICE_STABILITY,
            similarity_boost=self.config.VOICE_SIMILARITY,
            style=self.config.VOICE_STYLE,
            use_speaker_boost=self.config.VOICE_SPEAKER_BOOST,
        )

        self.voice = Voice(voice_id=self.config.ELEVENLABS_VOICE_ID, settings=self.voice_settings)

    def _init_v2(self):
        """Inicializa SDK v2 (elevenlabs >= 1.0)."""
        self.client = ElevenLabs(api_key=self.config.ELEVENLABS_API_KEY)

        self.voice_settings = {
            "stability": self.config.VOICE_STABILITY,
            "similarity_boost": self.config.VOICE_SIMILARITY,
            "style": self.config.VOICE_STYLE,
            "use_speaker_boost": self.config.VOICE_SPEAKER_BOOST,
        }

    async def speak(self, text: str, wait: bool = True) -> bool:
        """
        Faz JARVIS falar o texto.

        Args:
            text: O que JARVIS vai falar
            wait: Se True, espera terminar de falar antes de retornar

        Returns:
            True se sucesso, False se erro
        """
        if not text or not text.strip():
            return True

        try:
            if ELEVENLABS_V2:
                return await self._speak_v2(text, wait)
            else:
                return await self._speak_v1(text, wait)

        except Exception as e:
            print(f"[TTS ERROR] {e}")
            return False

    async def _speak_v1(self, text: str, wait: bool) -> bool:
        """Fala usando SDK v1."""
        try:
            audio = generate(text=text, voice=self.voice, model=self.config.ELEVENLABS_MODEL)

            if wait:
                stream(audio)
            else:
                # Fire and forget
                threading.Thread(target=lambda: stream(audio), daemon=True).start()

            return True

        except Exception as e:
            print(f"[TTS v1 ERROR] {e}")
            return False

    async def _speak_v2(self, text: str, wait: bool) -> bool:
        """Fala usando SDK v2."""
        try:
            # Gera áudio via API
            response = self.client.text_to_speech.convert(
                voice_id=self.config.ELEVENLABS_VOICE_ID,
                text=text,
                model_id=self.config.ELEVENLABS_MODEL,
                voice_settings=self.voice_settings,
            )

            # Coleta o áudio (response é um generator)
            audio_bytes = b""
            for chunk in response:
                audio_bytes += chunk

            if wait:
                await self._play_audio_blocking(audio_bytes)
            else:
                # Fire and forget
                asyncio.create_task(self._play_audio_async(audio_bytes))

            return True

        except Exception as e:
            print(f"[TTS v2 ERROR] {e}")
            return False

    async def _play_audio_blocking(self, audio_bytes: bytes):
        """Toca áudio de forma bloqueante."""
        try:
            # Usa sounddevice para playback
            import soundfile as sf

            # Carrega áudio do bytes
            audio_io = io.BytesIO(audio_bytes)
            data, samplerate = sf.read(audio_io)

            # Toca o áudio
            self._is_speaking = True
            sd.play(data, samplerate)
            sd.wait()  # Espera terminar
            self._is_speaking = False

        except ImportError:
            # Fallback: salva e toca com outro método
            await self._play_audio_fallback(audio_bytes)

    async def _play_audio_async(self, audio_bytes: bytes):
        """Toca áudio de forma assíncrona."""
        try:
            import soundfile as sf

            audio_io = io.BytesIO(audio_bytes)
            data, samplerate = sf.read(audio_io)

            self._is_speaking = True
            sd.play(data, samplerate)
            # Não espera
            self._is_speaking = False

        except ImportError:
            await self._play_audio_fallback(audio_bytes)

    async def _play_audio_fallback(self, audio_bytes: bytes):
        """Fallback: salva arquivo temporário e toca."""
        import platform
        import subprocess
        import tempfile

        # Salva em arquivo temporário
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            # Toca baseado no OS
            system = platform.system()

            if system == "Darwin":  # macOS
                subprocess.run(["afplay", temp_path], check=True)
            elif system == "Linux":
                subprocess.run(["mpg123", "-q", temp_path], check=True)
            elif system == "Windows":
                import winsound

                winsound.PlaySound(temp_path, winsound.SND_FILENAME)

        finally:
            # Remove arquivo temporário
            import os

            try:
                os.unlink(temp_path)
            except:
                pass

    async def speak_with_emotion(self, text: str, emotion: str = "neutral"):
        """
        Fala com emoção específica.
        Ajusta settings baseado na emoção.

        Args:
            text: Texto para falar
            emotion: excited, concerned, sarcastic, neutral
        """
        emotion_adjustments = {
            "excited": {"stability": 0.30, "similarity_boost": 0.80, "style": 0.50},
            "concerned": {"stability": 0.50, "similarity_boost": 0.70, "style": 0.30},
            "sarcastic": {"stability": 0.35, "similarity_boost": 0.75, "style": 0.40},
            "neutral": {
                "stability": self.config.VOICE_STABILITY,
                "similarity_boost": self.config.VOICE_SIMILARITY,
                "style": self.config.VOICE_STYLE,
            },
        }

        # Salva settings originais
        original_settings = (
            self.voice_settings.copy() if isinstance(self.voice_settings, dict) else None
        )

        # Aplica ajuste de emoção
        adjustments = emotion_adjustments.get(emotion, emotion_adjustments["neutral"])

        if ELEVENLABS_V2:
            self.voice_settings.update(adjustments)
        else:
            self.voice_settings = VoiceSettings(**adjustments)
            self.voice = Voice(
                voice_id=self.config.ELEVENLABS_VOICE_ID, settings=self.voice_settings
            )

        # Fala
        await self.speak(text)

        # Restaura settings
        if original_settings and ELEVENLABS_V2:
            self.voice_settings = original_settings
        elif not ELEVENLABS_V2:
            self._init_v1()

    def is_speaking(self) -> bool:
        """Retorna True se está falando no momento."""
        return self._is_speaking

    async def stop_speaking(self):
        """Para de falar imediatamente."""
        try:
            sd.stop()
            self._is_speaking = False
        except:
            pass


class TTSHandlerSimple:
    """
    Versão simplificada do TTS para ambientes sem dependências de áudio.
    Usa a API do ElevenLabs e reprodução via sistema.
    """

    def __init__(self):
        self.config = Config()

        if not ELEVENLABS_V2:
            set_api_key(self.config.ELEVENLABS_API_KEY)

        print("[TTS Simple] Inicializado (modo fallback)")

    async def speak(self, text: str, wait: bool = True) -> bool:
        """Fala usando método simplificado."""
        if not text or not text.strip():
            return True

        try:
            import platform
            import subprocess
            import tempfile

            import requests

            # Chama API diretamente
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.config.ELEVENLABS_VOICE_ID}"

            headers = {
                "xi-api-key": self.config.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            }

            data = {
                "text": text,
                "model_id": self.config.ELEVENLABS_MODEL,
                "voice_settings": {
                    "stability": self.config.VOICE_STABILITY,
                    "similarity_boost": self.config.VOICE_SIMILARITY,
                    "style": self.config.VOICE_STYLE,
                },
            }

            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            # Salva e toca
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(response.content)
                temp_path = f.name

            system = platform.system()

            if wait:
                if system == "Darwin":
                    subprocess.run(["afplay", temp_path])
                elif system == "Linux":
                    subprocess.run(["mpg123", "-q", temp_path])
            else:
                if system == "Darwin":
                    subprocess.Popen(["afplay", temp_path])
                elif system == "Linux":
                    subprocess.Popen(["mpg123", "-q", temp_path])

            return True

        except Exception as e:
            print(f"[TTS Simple ERROR] {e}")
            return False


# ==============================
# FACTORY
# ==============================


def create_tts_handler() -> TTSHandler:
    """
    Factory para criar o TTS handler apropriado.
    Tenta a versão completa, fallback para simples.
    """
    try:
        import sounddevice
        import soundfile

        return TTSHandler()
    except ImportError:
        print("[TTS] Dependências de áudio não encontradas, usando modo simples")
        return TTSHandlerSimple()


# ==============================
# TESTE
# ==============================

if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 60)
        print("TTS HANDLER - TESTE")
        print("=" * 60)

        Config.print_status()

        if not Config.ELEVENLABS_API_KEY:
            print("\n❌ ELEVENLABS_API_KEY não configurada!")
            print("   Configure no arquivo .env")
            return

        print("\n🎤 Testando TTS...")

        try:
            tts = create_tts_handler()

            print("   Falando frase de teste...")
            await tts.speak("Teste de voz. JARVIS online e operacional.")

            print("\n✅ TTS funcionando!")

        except Exception as e:
            print(f"\n❌ Erro no teste: {e}")

        print("=" * 60)

    asyncio.run(test())
