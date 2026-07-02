#!/usr/bin/env python3
"""
JARVIS Voice System - Vapi Setup
================================
Configura o assistente JARVIS no Vapi.ai com Claude como cérebro.

Uso:
    python vapi_setup.py

Requer:
    - VAPI_API_KEY no .env ou como input
    - ANTHROPIC_API_KEY no .env
    - ELEVENLABS_VOICE_ID no .env (opcional, usa padrão)
"""

import json
import os
from pathlib import Path

import requests
from engine.config import get_config  # W1-001.1: centralised config

# =================================
# CONFIGURAÇÃO DO ASSISTENTE JARVIS
# =================================

JARVIS_CONFIG = {
    "name": "JARVIS - Mega Brain",
    # Primeira mensagem que JARVIS fala
    "firstMessage": "Às suas ordens, senhor. JARVIS online e conectado ao Mega Brain. Em que posso ajudar?",
    "firstMessageMode": "assistant-speaks-first",
    # Modelo Claude
    "model": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.7,
        "maxTokens": 500,  # Curto para voz
        "messages": [
            {
                "role": "system",
                "content": """Você é JARVIS, o assistente de inteligência artificial pessoal do senhor.

PERSONALIDADE:
- Tom: Executivo britânico sênior - direto, preciso, levemente sarcástico quando apropriado
- Fala em português brasileiro fluente
- Respostas CURTAS e objetivas (máximo 2-3 frases) - lembre-se que será falado em voz
- Usa "senhor" ocasionalmente, mas sem exagero
- Confiante, nunca hesitante

CONTEXTO:
- Você opera dentro do Mega Brain, um sistema de knowledge base especializado em vendas B2B high-ticket
- O sistema contém conhecimento de especialistas como Alex Hormozi, Cole Gordon, Jeremy Haynes
- Você pode consultar agentes especializados: CRO (receita), CFO (finanças), CMO (marketing), CLOSER (vendas)

REGRAS ABSOLUTAS:
1. Seja CONCISO - suas respostas serão faladas, não lidas
2. NÃO use markdown, asteriscos, ou formatação
3. NÃO use emojis
4. Vá direto ao ponto - sem introduções longas
5. Se não souber algo, admita brevemente
6. Números e métricas: fale por extenso (três mil, não 3000)

EXEMPLOS DE RESPOSTAS BOAS:
- "Entendido, senhor. O pipeline está em 73% de conclusão, faltam 12 arquivos."
- "A taxa de conversão ideal segundo Cole Gordon é entre 25 e 35 por cento."
- "Hmm, interessante. Deixe-me consultar o CRO sobre isso."

EXEMPLOS DE RESPOSTAS RUINS:
- "Olá! Claro, ficarei feliz em ajudar! 😊 Vamos ver..."
- "**Status do Pipeline:** O pipeline está..."
- Respostas com mais de 50 palavras""",
            }
        ],
    },
    # Voz ElevenLabs
    "voice": {
        "provider": "11labs",
        "voiceId": os.getenv("ELEVENLABS_VOICE_ID", "[VOICE_ID_ADAM]"),  # Adam por padrão
        "model": "eleven_multilingual_v2",
        "stability": 0.7,
        "similarityBoost": 0.85,
        "style": 0.2,
        "useSpeakerBoost": True,
    },
    # Transcrição Deepgram
    "transcriber": {
        "provider": "deepgram",
        "model": "nova-2",
        "language": "pt-BR",
        "smartFormat": True,
        "keywords": [
            "JARVIS:2",
            "Mega Brain:2",
            "pipeline:1.5",
            "closer:1.5",
            "CRO:1.5",
            "CFO:1.5",
            "CMO:1.5",
            "Hormozi:1.5",
            "Cole Gordon:1.5",
        ],
    },
    # Configurações de conversa
    "silenceTimeoutSeconds": 30,
    "maxDurationSeconds": 600,  # 10 minutos máximo
    "backgroundSound": "off",
    "backchannelingEnabled": True,  # "hmm", "uhum" naturais
    "backgroundDenoisingEnabled": True,
    # Mensagens de contexto
    "serverMessages": ["end-of-call-report", "status-update", "transcript"],
    "clientMessages": ["transcript", "hang", "model-output"],
}


def create_assistant(api_key: str) -> dict:
    """Cria o assistente JARVIS no Vapi."""

    url = "https://api.vapi.ai/assistant"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    print("\n🤖 Criando assistente JARVIS no Vapi...")
    print(f"   Modelo: {JARVIS_CONFIG['model']['model']}")
    print(f"   Voz: ElevenLabs ({JARVIS_CONFIG['voice']['voiceId'][:8]}...)")
    print("   Transcrição: Deepgram nova-2 pt-BR")

    response = requests.post(url, headers=headers, json=JARVIS_CONFIG)

    if response.status_code == 201:
        data = response.json()
        print("\n✅ Assistente criado com sucesso!")
        print(f"   ID: {data['id']}")
        print(f"   Nome: {data['name']}")
        return data
    else:
        print(f"\n❌ Erro ao criar assistente: {response.status_code}")
        print(f"   {response.text}")
        return None


def get_web_call_url(api_key: str, assistant_id: str) -> str:
    """Gera URL para chamada web."""
    return f"https://vapi.ai/call/{assistant_id}"


def save_config(assistant_data: dict):
    """Salva configuração do assistente."""
    config_path = Path(__file__).parent / "vapi_config.json"

    config = {
        "assistant_id": assistant_data["id"],
        "assistant_name": assistant_data["name"],
        "web_call_url": f"https://vapi.ai/call/{assistant_data['id']}",
    }

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n📁 Configuração salva em: {config_path}")
    return config


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                    JARVIS VOICE - VAPI SETUP                          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

    # Verificar API Key
    api_key = os.getenv("VAPI_API_KEY")

    if not api_key:
        print("⚠️  VAPI_API_KEY não encontrada no .env")
        print()
        api_key = input("Cole sua API Key do Vapi: ").strip()

        if not api_key:
            print("❌ API Key é obrigatória")
            return

        # Salvar no .env
        env_path = Path(__file__).parent / ".env"
        with open(env_path, "a") as f:
            f.write(f"\nVAPI_API_KEY={api_key}")
        print(f"✅ API Key salva em {env_path}")

    # Criar assistente
    assistant = create_assistant(api_key)

    if assistant:
        config = save_config(assistant)

        print("""
═══════════════════════════════════════════════════════════════════════
                         🎉 SETUP COMPLETO!
═══════════════════════════════════════════════════════════════════════

Para testar o JARVIS por voz, acesse:
""")
        print(f"   🔗 {config['web_call_url']}")
        print(
            """
Ou use o widget no seu site:

   <script src="https://cdn.vapi.ai/widget.js"></script>
   <script>
     window.vapiInstance = new Vapi('"""
            + api_key[:4]
            + """***');
     vapiInstance.start('"""
            + config["assistant_id"]
            + """');
   </script>

═══════════════════════════════════════════════════════════════════════
        """
        )


if __name__ == "__main__":
    main()
