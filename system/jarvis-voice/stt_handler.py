# stt_handler.py
"""
JARVIS Voice System - Speech-to-Text Handler (Deepgram)
=======================================================
Gerencia Speech-to-Text via Deepgram.
Transcreve a voz do senhor em tempo real usando streaming.

Features:
- Streaming em tempo real
- Detecção automática de fim de fala
- Suporte a português brasileiro
"""

import asyncio
import json
import threading
from typing import Callable, Optional, Awaitable
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None
    print("[WARN] sounddevice não instalado. STT funcionará em modo limitado.")

try:
    import websockets
except ImportError:
    websockets = None
    print("[WARN] websockets não instalado.")

from config import Config


class STTHandler:
    """
    Gerencia Speech-to-Text via Deepgram.
    Transcreve a voz em tempo real usando WebSocket streaming.
    """

    def __init__(self, on_transcript_callback: Callable[[str], Awaitable[None]]):
        """
        Args:
            on_transcript_callback: Função async chamada quando transcrição é recebida
        """
        self.config = Config()
        self.on_transcript = on_transcript_callback
        self.is_listening = False
        self._websocket = None
        self._audio_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Buffer para acumular transcrições parciais
        self._partial_transcript = ""

    async def start_listening(self):
        """Inicia escuta contínua do microfone via streaming."""
        if self.is_listening:
            print("[STT] Já está escutando")
            return

        if not sd:
            print("[STT ERROR] sounddevice não disponível")
            return

        if not websockets:
            print("[STT ERROR] websockets não disponível")
            return

        self.is_listening = True
        self._loop = asyncio.get_event_loop()

        print("[STT] Iniciando escuta...")

        try:
            # URL do WebSocket Deepgram
            url = self._build_deepgram_url()

            # Headers com API key
            headers = {
                "Authorization": f"Token {self.config.DEEPGRAM_API_KEY}"
            }

            # Conecta ao WebSocket
            async with websockets.connect(url, extra_headers=headers) as ws:
                self._websocket = ws
                print("[STT] Conectado ao Deepgram")

                # Inicia thread de captura de áudio
                self._start_audio_capture()

                # Processa mensagens do WebSocket
                await self._process_websocket_messages(ws)

        except Exception as e:
            print(f"[STT ERROR] {e}")
        finally:
            self.is_listening = False
            self._websocket = None

    def _build_deepgram_url(self) -> str:
        """
        Constrói URL do WebSocket Deepgram com parâmetros otimizados para PT-BR.

        Otimizações aplicadas:
        - Endpointing mais longo (1200ms) para frases completas em português
        - Smart format para pontuação e capitalização automática
        - Numerals para converter números escritos
        - Keywords com boost para termos específicos do contexto
        """
        base = "wss://api.deepgram.com/v1/listen"

        # Parâmetros base
        params = [
            f"model={self.config.DEEPGRAM_MODEL}",
            f"language={self.config.DEEPGRAM_LANGUAGE}",
            "punctuate=true",
            "interim_results=true",           # Resultados parciais para feedback
            f"endpointing={self.config.DEEPGRAM_ENDPOINTING}",  # Mais tempo para PT-BR
            "vad_events=true",                # Voice Activity Detection
            "encoding=linear16",
            f"sample_rate={self.config.SAMPLE_RATE}",
            "channels=1",
        ]

        # Formatação inteligente
        if self.config.DEEPGRAM_SMART_FORMAT:
            params.append("smart_format=true")

        # Conversão de números
        if self.config.DEEPGRAM_NUMERALS:
            params.append("numerals=true")

        # Detectar filler words (é, né, tipo)
        if self.config.DEEPGRAM_FILLER_WORDS:
            params.append("filler_words=true")

        # Keywords com boost para melhor reconhecimento
        if hasattr(self.config, 'DEEPGRAM_KEYWORDS') and self.config.DEEPGRAM_KEYWORDS:
            for keyword in self.config.DEEPGRAM_KEYWORDS:
                # Encode the keyword for URL
                import urllib.parse
                encoded = urllib.parse.quote(keyword)
                params.append(f"keywords={encoded}")

        return f"{base}?{'&'.join(params)}"

    def _start_audio_capture(self):
        """Inicia captura de áudio em thread separada."""

        def capture_audio():
            """Loop de captura de áudio do microfone."""
            try:
                with sd.InputStream(
                    samplerate=self.config.SAMPLE_RATE,
                    channels=self.config.CHANNELS,
                    dtype=np.int16,
                    blocksize=self.config.CHUNK_SIZE,
                    callback=self._audio_callback
                ):
                    while self.is_listening:
                        sd.sleep(100)
            except Exception as e:
                print(f"[STT Audio ERROR] {e}")

        self._audio_thread = threading.Thread(target=capture_audio, daemon=True)
        self._audio_thread.start()

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback chamado quando há áudio disponível."""
        if status:
            print(f"[STT Audio Status] {status}")

        if self._websocket and self.is_listening:
            # Envia áudio para o WebSocket de forma assíncrona
            audio_bytes = indata.tobytes()
            asyncio.run_coroutine_threadsafe(
                self._send_audio(audio_bytes),
                self._loop
            )

    async def _send_audio(self, audio_bytes: bytes):
        """Envia bytes de áudio para o WebSocket."""
        try:
            if self._websocket:
                await self._websocket.send(audio_bytes)
        except Exception as e:
            print(f"[STT Send ERROR] {e}")

    async def _process_websocket_messages(self, ws):
        """Processa mensagens recebidas do WebSocket."""
        try:
            async for message in ws:
                if not self.is_listening:
                    break

                data = json.loads(message)
                await self._handle_deepgram_response(data)

        except websockets.exceptions.ConnectionClosed:
            print("[STT] Conexão fechada")
        except Exception as e:
            print(f"[STT Process ERROR] {e}")

    async def _handle_deepgram_response(self, data: dict):
        """Processa resposta do Deepgram."""
        # Ignora mensagens de metadados
        if data.get("type") == "Metadata":
            return

        # Extrai transcrição
        channel = data.get("channel", {})
        alternatives = channel.get("alternatives", [])

        if not alternatives:
            return

        transcript = alternatives[0].get("transcript", "").strip()
        is_final = data.get("is_final", False)
        speech_final = data.get("speech_final", False)

        if not transcript:
            return

        if is_final or speech_final:
            # Transcrição final - envia para callback
            print(f"[STT] Final: '{transcript}'")
            await self.on_transcript(transcript)
            self._partial_transcript = ""
        else:
            # Transcrição parcial - pode ser usada para feedback visual
            self._partial_transcript = transcript
            # Opcional: pode emitir evento de transcrição parcial

    def stop_listening(self):
        """Para a escuta."""
        print("[STT] Parando escuta...")
        self.is_listening = False

        if self._websocket:
            asyncio.run_coroutine_threadsafe(
                self._websocket.close(),
                self._loop
            ) if self._loop else None

    def get_partial_transcript(self) -> str:
        """Retorna transcrição parcial atual (para feedback visual)."""
        return self._partial_transcript


class STTHandlerSimple:
    """
    Versão simplificada do STT para ambientes sem streaming.
    Usa gravação em blocos e transcrição via API REST.
    """

    def __init__(self, on_transcript_callback: Callable[[str], Awaitable[None]]):
        self.config = Config()
        self.on_transcript = on_transcript_callback
        self.is_listening = False
        self._record_duration = 5  # Segundos por gravação

    async def start_listening(self):
        """Inicia escuta em modo simplificado (blocos de áudio)."""
        if not sd:
            print("[STT Simple ERROR] sounddevice não disponível")
            return

        self.is_listening = True
        print("[STT Simple] Iniciando escuta (modo blocos)...")

        while self.is_listening:
            try:
                # Grava bloco de áudio
                print("[STT Simple] Ouvindo...")
                audio = sd.rec(
                    int(self._record_duration * self.config.SAMPLE_RATE),
                    samplerate=self.config.SAMPLE_RATE,
                    channels=self.config.CHANNELS,
                    dtype=np.int16
                )
                sd.wait()

                if not self.is_listening:
                    break

                # Transcreve via API REST
                transcript = await self._transcribe_audio(audio)

                if transcript:
                    print(f"[STT Simple] Transcrito: '{transcript}'")
                    await self.on_transcript(transcript)

            except Exception as e:
                print(f"[STT Simple ERROR] {e}")
                await asyncio.sleep(1)

    async def _transcribe_audio(self, audio: np.ndarray) -> Optional[str]:
        """Transcreve áudio via API REST do Deepgram com otimizações PT-BR."""
        try:
            import aiohttp
            import urllib.parse

            # Parâmetros base
            params = [
                f"model={self.config.DEEPGRAM_MODEL}",
                f"language={self.config.DEEPGRAM_LANGUAGE}",
                "punctuate=true",
                "smart_format=true",
                "numerals=true",
            ]

            # Adiciona keywords se disponível
            if hasattr(self.config, 'DEEPGRAM_KEYWORDS') and self.config.DEEPGRAM_KEYWORDS:
                for keyword in self.config.DEEPGRAM_KEYWORDS:
                    encoded = urllib.parse.quote(keyword)
                    params.append(f"keywords={encoded}")

            url = f"https://api.deepgram.com/v1/listen?{'&'.join(params)}"

            headers = {
                "Authorization": f"Token {self.config.DEEPGRAM_API_KEY}",
                "Content-Type": "audio/raw"
            }

            # Converte para bytes
            audio_bytes = audio.tobytes()

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=audio_bytes) as response:
                    if response.status == 200:
                        data = await response.json()
                        alternatives = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [])
                        if alternatives:
                            return alternatives[0].get("transcript", "").strip()
                    else:
                        print(f"[STT Simple] API retornou {response.status}")

        except Exception as e:
            print(f"[STT Simple Transcribe ERROR] {e}")

        return None

    def stop_listening(self):
        """Para a escuta."""
        self.is_listening = False

    def get_partial_transcript(self) -> str:
        """Não suportado no modo simples."""
        return ""


***REMOVED***==============================
# FACTORY
***REMOVED***==============================

def create_stt_handler(callback: Callable[[str], Awaitable[None]]) -> STTHandler:
    """
    Factory para criar o STT handler apropriado.
    Tenta streaming, fallback para modo simples.
    """
    if websockets and sd:
        return STTHandler(callback)
    else:
        print("[STT] Usando modo simplificado (sem streaming)")
        return STTHandlerSimple(callback)


***REMOVED***==============================
# TESTE
***REMOVED***==============================

if __name__ == "__main__":
    import asyncio

    async def test_callback(text: str):
        print(f"\n🎤 TRANSCRITO: {text}\n")

    async def test():
        print("=" * 60)
        print("STT HANDLER - TESTE")
        print("=" * 60)

        Config.print_status()

        if not Config.DEEPGRAM_API_KEY:
            print("\n❌ DEEPGRAM_API_KEY não configurada!")
            print("   Configure no arquivo .env")
            return

        print("\n🎤 Testando STT...")
        print("   Fale algo para testar (Ctrl+C para parar)")

        try:
            stt = create_stt_handler(test_callback)

            # Escuta por 10 segundos de teste
            listen_task = asyncio.create_task(stt.start_listening())

            await asyncio.sleep(10)

            stt.stop_listening()
            await asyncio.sleep(1)

            print("\n✅ Teste concluído!")

        except KeyboardInterrupt:
            print("\n⏹️ Teste interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro no teste: {e}")

        print("=" * 60)

    asyncio.run(test())
