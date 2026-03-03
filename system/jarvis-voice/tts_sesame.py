# tts_sesame.py
"""
JARVIS Voice System - Sesame CSM TTS Handler
=============================================
Integração com Sesame CSM-1B para voz ultra-humanizada.

Diferenciais do Sesame vs ElevenLabs tradicional:
- Memória conversacional (últimos ~30s de áudio como contexto)
- Hesitações naturais, correções, respiração
- Tom que se adapta ao contexto emocional
- Estado da arte em naturalidade de fala
"""

import os
import torch
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from collections import deque
import asyncio
import tempfile
import wave

# Verificar qual GPU está disponível
def get_device():
    """Detecta o melhor device disponível: CUDA > MPS > CPU"""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"  # Apple Silicon GPU
    else:
        return "cpu"

DEVICE = get_device()
print(f"[Sesame TTS] Device: {DEVICE}")


class SesameTTSHandler:
    """
    Handler de TTS usando Sesame CSM-1B.
    Mantém contexto conversacional para gerar voz mais natural.
    """

    def __init__(self, speaker_id: int = 0):
        """
        Inicializa o handler Sesame.

        Args:
            speaker_id: ID do speaker (0 = voz padrão masculina)
        """
        self.speaker_id = speaker_id
        self.model = None
        self.processor = None
        self.sample_rate = 24000  # Sesame usa 24kHz

        # Contexto conversacional - últimos N segundos de áudio gerado
        # Isso permite que o modelo "lembre" o tom da conversa
        self.audio_context: deque = deque(maxlen=5)  # Últimas 5 gerações
        self.text_context: deque = deque(maxlen=5)   # Últimos 5 textos

        # Cache de modelo carregado
        self._model_loaded = False

    def _load_model(self):
        """Carrega o modelo Sesame CSM-1B (lazy loading)."""
        if self._model_loaded:
            return

        print("[Sesame TTS] Carregando modelo CSM-1B... (primeira vez pode demorar)")

        try:
            from transformers import CsmForConditionalGeneration, AutoProcessor

            model_id = "sesame/csm-1b"

            # Carregar processor
            self.processor = AutoProcessor.from_pretrained(model_id)

            # Determinar dtype baseado no device
            if DEVICE == "cuda":
                dtype = torch.float16
            elif DEVICE == "mps":
                dtype = torch.float32  # MPS funciona melhor com float32
            else:
                dtype = torch.float32

            # Carregar modelo com otimizações para GPU
            self.model = CsmForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=dtype,
            )

            # Mover para device
            self.model = self.model.to(DEVICE)

            # Configurar para inferência rápida
            self.model.eval()

            # Habilitar cache para inferência mais rápida
            if DEVICE in ["cuda", "mps"]:
                self.model.generation_config.max_length = 500  # ~10s de áudio

            self._model_loaded = True
            print("[Sesame TTS] Modelo carregado com sucesso!")

        except Exception as e:
            print(f"[Sesame TTS] Erro ao carregar modelo: {e}")
            raise

    def _prepare_context(self, text: str) -> dict:
        """
        Prepara o contexto conversacional para geração.

        O Sesame usa contexto de áudio anterior para manter
        consistência de tom e estilo na conversa.
        """
        self._load_model()

        # Se temos contexto de áudio anterior, usar chat template
        if len(self.audio_context) > 0 and len(self.text_context) > 0:
            # Montar conversa com contexto
            conversation = []

            # Adicionar contexto anterior (últimas interações)
            for prev_text, prev_audio in zip(self.text_context, self.audio_context):
                conversation.append({
                    "role": str(self.speaker_id),
                    "content": [
                        {"type": "text", "text": prev_text},
                        {"type": "audio", "path": prev_audio}
                    ]
                })

            # Adicionar texto atual (sem áudio - é o que queremos gerar)
            conversation.append({
                "role": str(self.speaker_id),
                "content": [{"type": "text", "text": text}]
            })

            # Processar com chat template
            inputs = self.processor.apply_chat_template(
                conversation,
                tokenize=True,
                return_dict=True,
            ).to(DEVICE)

        else:
            # Primeira geração - sem contexto
            formatted_text = f"[{self.speaker_id}]{text}"
            inputs = self.processor(
                formatted_text,
                add_special_tokens=True,
                return_tensors="pt"
            ).to(DEVICE)

        return inputs

    def generate_audio(self, text: str) -> np.ndarray:
        """
        Gera áudio a partir de texto usando Sesame CSM.

        Args:
            text: Texto para converter em fala

        Returns:
            Array numpy com áudio em 24kHz
        """
        self._load_model()

        # Preparar inputs com contexto
        inputs = self._prepare_context(text)

        # Gerar áudio
        with torch.no_grad():
            audio_output = self.model.generate(
                **inputs,
                output_audio=True,
                do_sample=True,  # Sampling para mais naturalidade
                temperature=0.7,  # Criatividade moderada
            )

        # Extrair array de áudio
        audio_array = audio_output.cpu().numpy().squeeze()

        # Normalizar para [-1, 1]
        if audio_array.max() > 1.0 or audio_array.min() < -1.0:
            audio_array = audio_array / np.abs(audio_array).max()

        # Atualizar contexto para próximas gerações
        self.text_context.append(text)
        self.audio_context.append(audio_array)

        return audio_array

    def generate_audio_file(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Gera áudio e salva em arquivo WAV.

        Args:
            text: Texto para converter
            output_path: Caminho do arquivo (opcional)

        Returns:
            Caminho do arquivo gerado
        """
        audio_array = self.generate_audio(text)

        if output_path is None:
            output_path = tempfile.mktemp(suffix=".wav")

        # Salvar como WAV
        self.processor.save_audio(audio_array, output_path)

        return output_path

    async def speak(self, text: str) -> bytes:
        """
        Gera áudio de forma assíncrona e retorna bytes.

        Args:
            text: Texto para falar

        Returns:
            Bytes do áudio em formato WAV
        """
        # Rodar geração em thread separada para não bloquear
        loop = asyncio.get_event_loop()
        audio_array = await loop.run_in_executor(None, self.generate_audio, text)

        # Converter para bytes WAV
        import io
        buffer = io.BytesIO()

        # Converter float32 para int16
        audio_int16 = (audio_array * 32767).astype(np.int16)

        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        buffer.seek(0)
        return buffer.read()

    def clear_context(self):
        """Limpa o contexto conversacional."""
        self.audio_context.clear()
        self.text_context.clear()
        print("[Sesame TTS] Contexto limpo")

    def get_context_length(self) -> int:
        """Retorna número de interações no contexto."""
        return len(self.audio_context)


class HybridTTSHandler:
    """
    Handler híbrido que usa Sesame para qualidade máxima
    e fallback para ElevenLabs se necessário.
    """

    def __init__(self, prefer_sesame: bool = True):
        """
        Args:
            prefer_sesame: Se True, tenta Sesame primeiro
        """
        self.prefer_sesame = prefer_sesame
        self.sesame: Optional[SesameTTSHandler] = None
        self.elevenlabs_fallback = None

        # Tentar inicializar Sesame
        if prefer_sesame:
            try:
                self.sesame = SesameTTSHandler()
                print("[Hybrid TTS] Sesame CSM disponível")
            except Exception as e:
                print(f"[Hybrid TTS] Sesame não disponível: {e}")
                print("[Hybrid TTS] Usando ElevenLabs como fallback")

    async def speak(self, text: str) -> bytes:
        """Gera áudio usando o melhor engine disponível."""

        if self.sesame is not None:
            try:
                return await self.sesame.speak(text)
            except Exception as e:
                print(f"[Hybrid TTS] Erro no Sesame: {e}, tentando fallback...")

        # Fallback para ElevenLabs
        if self.elevenlabs_fallback is None:
            from tts_handler import create_tts_handler
            self.elevenlabs_fallback = create_tts_handler()

        return await self.elevenlabs_fallback.speak(text)

    def clear_context(self):
        """Limpa contexto do Sesame."""
        if self.sesame:
            self.sesame.clear_context()


def create_sesame_handler(speaker_id: int = 0) -> SesameTTSHandler:
    """Factory function para criar handler Sesame."""
    return SesameTTSHandler(speaker_id=speaker_id)


def create_hybrid_handler(prefer_sesame: bool = True) -> HybridTTSHandler:
    """Factory function para criar handler híbrido."""
    return HybridTTSHandler(prefer_sesame=prefer_sesame)


#==============================
# TESTE
#==============================

if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 60)
        print("TESTE DO SESAME CSM TTS")
        print("=" * 60)

        # Criar handler
        handler = SesameTTSHandler()

        # Testar geração sem contexto
        print("\n1. Gerando sem contexto...")
        text1 = "Olá senhor. Sistema JARVIS operacional e pronto para servir."
        audio1 = handler.generate_audio(text1)
        print(f"   Áudio gerado: {len(audio1)} samples ({len(audio1)/24000:.2f}s)")

        # Testar geração COM contexto (deve ter tom mais consistente)
        print("\n2. Gerando com contexto...")
        text2 = "Interessante. O senhor quer que eu verifique o status do sistema?"
        audio2 = handler.generate_audio(text2)
        print(f"   Áudio gerado: {len(audio2)} samples ({len(audio2)/24000:.2f}s)")

        # Salvar exemplo
        print("\n3. Salvando exemplo...")
        output_path = handler.generate_audio_file(
            "Devo admitir, senhor, que o sistema está funcionando melhor do que eu esperava. Não se acostume.",
            "/tmp/jarvis_sesame_test.wav"
        )
        print(f"   Salvo em: {output_path}")

        print("\n" + "=" * 60)
        print(f"Contexto atual: {handler.get_context_length()} interações")
        print("=" * 60)

    asyncio.run(test())
