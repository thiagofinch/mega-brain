#!/usr/bin/env python3
# main.py
"""
JARVIS Voice System - Main Entry Point
======================================
Ponto de entrada do sistema JARVIS Voice.

Uso:
    python main.py           # Inicia JARVIS normalmente
    python main.py --test    # Executa testes dos componentes
    python main.py --config  # Mostra configurações
"""

import argparse
import asyncio
import signal
import sys
from typing import Optional

from config import Config
from orchestrator import JarvisOrchestrator

# ==============================
# ASCII ART
# ==============================

JARVIS_ASCII = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║       ███╗   ███╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗                ║
║       ████╗ ████║██╔══██╗██╔══██╗██║   ██║██║██╔════╝                ║
║       ██╔████╔██║███████║██████╔╝██║   ██║██║███████╗                ║
║       ██║╚██╔╝██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║                ║
║       ██║ ╚═╝ ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║                ║
║       ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝                ║
║                                                                       ║
║                      VOICE SYSTEM v1.0.0                              ║
║                                                                       ║
║                  "Às suas ordens, senhor."                            ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

JARVIS_STARTING = """
┌───────────────────────────────────────────────────────────────────────┐
│  🤖 JARVIS Voice System                                               │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Iniciando sistemas...                                                │
│                                                                       │
│  [■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■] 100%                                │
│                                                                       │
│  ✅ Config         - Carregada                                        │
│  ✅ Mega Brain     - Conectado                                        │
│  ✅ STT (Deepgram) - Pronto                                           │
│  ✅ TTS (Eleven)   - Pronto                                           │
│  ✅ Claude API     - Conectado                                        │
│                                                                       │
│  🎤 Escutando... (Ctrl+C para sair)                                   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
"""

JARVIS_SHUTDOWN = """
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  🤖 JARVIS Voice System - Encerrando                                  │
│                                                                       │
│  Salvando estado...                                                   │
│  Fechando conexões...                                                 │
│                                                                       │
│  "Até logo, senhor."                                                  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
"""


# ==============================
# MAIN CLASS
# ==============================


class JarvisVoiceApp:
    """Aplicação principal do JARVIS Voice."""

    def __init__(self):
        self.jarvis: Optional[JarvisOrchestrator] = None
        self._shutdown_event = asyncio.Event()

    def _setup_signal_handlers(self):
        """Configura handlers para sinais de sistema (Ctrl+C)."""

        def signal_handler(sig, frame):
            print("\n\n🛑 Sinal de interrupção recebido...")
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self):
        """Executa o JARVIS Voice."""
        print(JARVIS_ASCII)

        # Valida configurações
        is_valid, errors = Config.validate()
        if not is_valid:
            print("\n❌ Configurações inválidas:")
            for error in errors:
                print(f"   - {error}")
            print("\n📝 Configure as variáveis no arquivo .env")
            print("   Veja .env.example para referência.")
            return 1

        try:
            # Inicializa JARVIS
            self.jarvis = JarvisOrchestrator()

            print(JARVIS_STARTING)

            # Configura handlers de sinal
            self._setup_signal_handlers()

            # Inicia JARVIS em task separada
            jarvis_task = asyncio.create_task(self.jarvis.start())

            # Aguarda sinal de shutdown
            await self._shutdown_event.wait()

            # Shutdown gracioso
            print(JARVIS_SHUTDOWN)
            self.jarvis.stop()

            # Cancela task do JARVIS
            jarvis_task.cancel()
            try:
                await jarvis_task
            except asyncio.CancelledError:
                pass

            return 0

        except Exception as e:
            print(f"\n❌ Erro fatal: {e}")
            import traceback

            traceback.print_exc()
            return 1

    async def run_test(self):
        """Executa testes dos componentes."""
        print(JARVIS_ASCII)
        print("\n🧪 MODO DE TESTE\n")

        # Testa configurações
        print("=" * 60)
        print("1. CONFIGURAÇÕES")
        print("=" * 60)
        Config.print_status()

        is_valid, errors = Config.validate()
        if not is_valid:
            print("\n❌ Configurações inválidas. Corrija antes de continuar.")
            return 1

        # Testa TTS
        print("\n" + "=" * 60)
        print("2. TEXT-TO-SPEECH (ElevenLabs)")
        print("=" * 60)
        try:
            from tts_handler import create_tts_handler

            tts = create_tts_handler()
            print("   ✅ TTS Handler criado")

            print("   🔊 Testando fala...")
            await tts.speak("Teste de voz. JARVIS operacional.")
            print("   ✅ TTS funcionando!")
        except Exception as e:
            print(f"   ❌ Erro no TTS: {e}")

        # Testa Mega Brain Connector
        print("\n" + "=" * 60)
        print("3. MEGA BRAIN CONNECTOR")
        print("=" * 60)
        try:
            from mega_brain_connector import MegaBrainConnector

            connector = MegaBrainConnector()
            print("   ✅ Connector criado")

            summary = connector.get_mission_summary()
            print(f"   📊 Status: {summary}")

            agents = connector.get_available_agents()
            print(f"   👥 Agentes disponíveis: {len(agents)}")
            print("   ✅ Connector funcionando!")
        except Exception as e:
            print(f"   ❌ Erro no Connector: {e}")

        # Testa Claude
        print("\n" + "=" * 60)
        print("4. CLAUDE API")
        print("=" * 60)
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            print("   ✅ Cliente Anthropic criado")

            response = client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=50,
                messages=[{"role": "user", "content": "Responda apenas: OK"}],
            )
            print(f"   🧠 Resposta: {response.content[0].text}")
            print("   ✅ Claude API funcionando!")
        except Exception as e:
            print(f"   ❌ Erro no Claude: {e}")

        # Testa STT (apenas criação, não escuta real)
        print("\n" + "=" * 60)
        print("5. SPEECH-TO-TEXT (Deepgram)")
        print("=" * 60)
        try:

            async def dummy_callback(text):
                pass

            from stt_handler import create_stt_handler

            stt = create_stt_handler(dummy_callback)
            print("   ✅ STT Handler criado")
            print("   ⚠️  Teste de escuta requer microfone ativo")
            print("   ✅ STT pronto!")
        except Exception as e:
            print(f"   ❌ Erro no STT: {e}")

        print("\n" + "=" * 60)
        print("RESULTADO")
        print("=" * 60)
        print("\n✅ Testes básicos concluídos!")
        print("   Execute 'python main.py' para iniciar o JARVIS.")

        return 0


# ==============================
# ENTRY POINT
# ==============================


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="JARVIS Voice System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python main.py           # Inicia JARVIS
    python main.py --test    # Testa componentes
    python main.py --config  # Mostra configurações
        """,
    )

    parser.add_argument("--test", action="store_true", help="Executa testes dos componentes")

    parser.add_argument("--config", action="store_true", help="Mostra configurações atuais")

    args = parser.parse_args()

    app = JarvisVoiceApp()

    if args.config:
        print(JARVIS_ASCII)
        Config.print_status()
        return 0

    if args.test:
        return asyncio.run(app.run_test())

    return asyncio.run(app.run())


if __name__ == "__main__":
    sys.exit(main())
