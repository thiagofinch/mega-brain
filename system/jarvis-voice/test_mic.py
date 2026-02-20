#!/usr/bin/env python3
"""
Teste de Microfone para JARVIS Voice
====================================
Execute este script para testar se o microfone está funcionando.
"""

import sounddevice as sd
import numpy as np
import time

print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                    TESTE DE MICROFONE - JARVIS                        ║
╚═══════════════════════════════════════════════════════════════════════╝
""")

# Mostra dispositivos
print("📱 Dispositivos de áudio:")
print(sd.query_devices())

print("\n" + "=" * 60)
print("🎤 Testando microfone por 5 segundos...")
print("   Fale algo para ver os níveis de áudio")
print("=" * 60 + "\n")

SAMPLE_RATE = 48000
DURATION = 5  # segundos

def audio_callback(indata, frames, time_info, status):
    """Mostra nível de áudio em tempo real."""
    volume = np.linalg.norm(indata) * 10
    bars = int(volume)
    print(f"\r🎤 Nível: {'█' * min(bars, 50):<50} {volume:.1f}", end='', flush=True)

try:
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.float32,
        callback=audio_callback
    ):
        time.sleep(DURATION)

    print("\n\n✅ Microfone funcionando!")
    print("\n👉 Agora execute: python3 main.py")

except Exception as e:
    print(f"\n\n❌ Erro no microfone: {e}")
    print("\n📝 Verifique:")
    print("   1. System Settings > Privacy & Security > Microphone")
    print("   2. Permita acesso ao Terminal")
