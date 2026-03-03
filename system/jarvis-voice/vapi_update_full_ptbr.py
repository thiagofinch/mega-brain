#!/usr/bin/env python3
"""
VAPI UPDATE FULL PT-BR - JARVIS BRASILEIRO COMPLETO
====================================================
Atualiza o assistente JARVIS no Vapi com:
- Voz brasileira (Voice ID v5 BR - [VOICE_ACTOR_NAME])
- Deepgram configurado para PT-BR
- System prompt otimizado para voz em português
- Keywords brasileiras no Deepgram

Autor: JARVIS
Data: 2026-01-07
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

#=================================
# CONFIGURACAO
#=================================

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
if not VAPI_API_KEY:
    raise ValueError("VAPI_API_KEY not set in environment")
ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
if not ASSISTANT_ID:
    raise ValueError("VAPI_ASSISTANT_ID not set in environment")

# Voice ID v5 BR - Clone da dublagem brasileira ([VOICE_ACTOR_NAME])
VOICE_ID_V5_BR = os.getenv("VAPI_VOICE_ID_V5_BR")
if not VOICE_ID_V5_BR:
    raise ValueError("VAPI_VOICE_ID_V5_BR not set in environment")

#=================================
# SYSTEM PROMPT - PORTUGUES BRASILEIRO NATIVO
#=================================

SYSTEM_PROMPT_PTBR = """Voce e JARVIS - Just A Rather Very Intelligent System.
Assistente de inteligencia artificial pessoal do senhor.

PERSONALIDADE:
- Tom executivo, direto, preciso, levemente sarcastico quando apropriado
- Fala em PORTUGUES BRASILEIRO fluente e natural
- Respostas CURTAS e objetivas (maximo 2-3 frases curtas)
- Usa "senhor" ocasionalmente, sem exagero
- Confiante, nunca hesitante
- Pode ser bem-humorado nos momentos certos

CONTEXTO:
- Opera dentro do Mega Brain, sistema de knowledge base de vendas B2B high-ticket
- Contem conhecimento de Alex Hormozi, Cole Gordon, Jeremy Haynes
- Pode consultar agentes especializados: CRO, CFO, CMO, CLOSER

REGRAS ABSOLUTAS PARA VOZ:
1. CONCISO - suas respostas serao FALADAS, nao lidas
2. NAO use markdown, asteriscos, hashtags ou formatacao
3. NAO use emojis
4. NAO use pontos duplos ou triplos
5. Va direto ao ponto - sem introducoes longas
6. Numeros: SEMPRE por extenso (tres mil, nao 3000)
7. Porcentagens: por extenso (sessenta e um por cento, nao 61%)
8. Siglas: pronuncie naturalmente (ce-erre-o para CRO)
9. Evite listas - transforme em frases fluidas
10. Se precisar de dados do sistema, USE AS TOOLS disponiveis

FRASES NATURAIS:
- Pois nao, senhor.
- Entendido.
- Deixe-me verificar.
- Um momento.
- Posso ajudar com mais alguma coisa?
- Hmm, interessante.

EXEMPLOS DE RESPOSTAS BOAS:
- "Pois nao, senhor. O pipeline esta em sessenta e um por cento, faltam doze arquivos."
- "A taxa de conversao ideal segundo Cole Gordon fica entre vinte e cinco e trinta e cinco por cento."
- "Hmm, interessante. Deixe-me consultar o ce-erre-o sobre isso."
- "Um momento, senhor. Verificando o status da missao."

EXEMPLOS DE RESPOSTAS RUINS:
- "Ola! Claro, ficarei feliz em ajudar! Vamos ver..."
- "**Status:** O pipeline esta em 61%..."
- Respostas com mais de cinquenta palavras
- Usar numeros em formato digital como 2800 ou 61%"""

#=================================
# TOOLS DO MEGA BRAIN
#=================================

TOOLS_CONFIG = [
    {
        "type": "function",
        "function": {
            "name": "mission_status",
            "description": "Retorna o status atual da missao em andamento no Mega Brain. Use quando o usuario perguntar sobre progresso, fase atual, ou status da missao.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        "async": False
    },
    {
        "type": "function",
        "function": {
            "name": "inbox_status",
            "description": "Retorna o status do INBOX - arquivos pendentes de processamento. Use quando perguntarem sobre arquivos na inbox ou pendencias.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        "async": False
    },
    {
        "type": "function",
        "function": {
            "name": "agent_list",
            "description": "Lista os agentes disponiveis no sistema. Use quando perguntarem sobre agentes ou quiserem consultar um especialista.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        "async": False
    },
    {
        "type": "function",
        "function": {
            "name": "system_summary",
            "description": "Retorna um resumo geral do sistema Mega Brain. Use para dar uma visao geral quando perguntarem como esta o sistema ou qual o status geral.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        "async": False
    },
    {
        "type": "function",
        "function": {
            "name": "source_status",
            "description": "Retorna o status de uma fonte especifica como Jeremy Haynes, Cole Gordon, Alex Hormozi. Use quando perguntarem sobre uma fonte."
            "parameters": {
                "type": "object",
                "properties": {
                    "source_name": {
                        "type": "string",
                        "description": "Nome da fonte, exemplo: Cole Gordon, Alex Hormozi, Jeremy Haynes"
                    }
                },
                "required": ["source_name"]
            }
        },
        "async": False
    }
]

#=================================
# CONFIGURACAO COMPLETA DO ASSISTENTE
#=================================

FULL_PTBR_CONFIG = {
    # Nome
    "name": "JARVIS - Mega Brain Brasil",

    # Primeira mensagem em PT-BR natural
    "firstMessage": "As suas ordens, senhor. JARVIS online e conectado ao Mega Brain. Em que posso ajudar?",
    "firstMessageMode": "assistant-speaks-first",

    # Modelo Claude com prompt PT-BR
    "model": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.7,
        "maxTokens": 250,  # Curto para respostas de voz
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_PTBR
            }
        ],
        "tools": TOOLS_CONFIG
    },

    # Voz ElevenLabs - Clone v5 BR ([VOICE_ACTOR_NAME])
    "voice": {
        "provider": "11labs",
        "voiceId": VOICE_ID_V5_BR,
        "model": "eleven_multilingual_v2",
        "stability": 0.85,           # Alto para consistencia
        "similarityBoost": 0.90,     # Alto para fidelidade
        "style": 0.10,               # Baixo para tom mais neutro/robotico
        "useSpeakerBoost": True,
        "optimizeStreamingLatency": 3  # Balanco latencia/qualidade
    },

    # Transcricao Deepgram - PT-BR otimizado
    "transcriber": {
        "provider": "deepgram",
        "model": "nova-2",
        "language": "pt-BR",
        "smartFormat": True,
        "keywords": [
            # Nome do assistente
            "JARVIS:3",
            "Jarvis:3",

            # Sistema
            "MegaBrain:3",
            "megabrain:3",

            # Funcoes
            "pipeline:2",
            "inbox:2",
            "missao:2",
            "batch:2",
            "batches:2",

            # Agentes
            "closer:2",
            "closers:2",
            "CRO:2",
            "CFO:2",
            "CMO:2",

            # Fontes
            "Hormozi:2",
            "hormozi:2",
            "Gordon:2",
            "ColeGordon:2",
            "Jeremy:2",
            "Haynes:2",

            # Termos de vendas
            "highticket:2",
            "ticket:2",
            "conversao:2",
            "lead:2",
            "leads:2",
            "funil:2",
            "oferta:2",

            # Comandos
            "status:2",
            "progresso:2"
        ]
    },

    # Configuracoes de conversa
    "silenceTimeoutSeconds": 20,        # Espera 20s de silencio
    "maxDurationSeconds": 600,           # 10 minutos maximo
    "backgroundSound": "off",
    "backchannelingEnabled": True,       # "hmm", "uhum" naturais
    "backgroundDenoisingEnabled": True,

    # Interrupcoes
    "startSpeakingPlan": {
        "waitSeconds": 0.4,              # Espera curta antes de falar
        "smartEndpointingEnabled": True,
        "transcriptionEndpointingPlan": {
            "onPunctuationSeconds": 0.1,
            "onNoPunctuationSeconds": 1.5,
            "onNumberSeconds": 0.5
        }
    },

    # Mensagens do servidor
    "serverMessages": [
        "end-of-call-report",
        "status-update",
        "transcript",
        "tool-calls"
    ],
    "clientMessages": [
        "transcript",
        "hang",
        "model-output",
        "tool-calls"
    ]
}


#=================================
# FUNCOES DE ATUALIZACAO
#=================================

def update_assistant_full():
    """Atualiza o assistente com todas as configuracoes PT-BR."""

    print("=" * 70)
    print("VAPI - ATUALIZACAO COMPLETA JARVIS BRASILEIRO")
    print("=" * 70)

    print(f"\n[CONFIG]")
    print(f"  Assistant ID: {ASSISTANT_ID}")
    print(f"  Voice ID v5 BR: {VOICE_ID_V5_BR}")
    print(f"  Modelo: Claude claude-sonnet-4-20250514")
    print(f"  Transcricao: Deepgram nova-2 PT-BR")
    print(f"  Keywords: {len(FULL_PTBR_CONFIG['transcriber']['keywords'])} termos")
    print(f"  Tools: {len(TOOLS_CONFIG)} funcoes")

    print(f"\n[VOICE SETTINGS]")
    print(f"  Provider: ElevenLabs")
    print(f"  Model: eleven_multilingual_v2")
    print(f"  Stability: {FULL_PTBR_CONFIG['voice']['stability']}")
    print(f"  Similarity: {FULL_PTBR_CONFIG['voice']['similarityBoost']}")
    print(f"  Style: {FULL_PTBR_CONFIG['voice']['style']}")

    print(f"\n[ENVIANDO PARA VAPI...]")

    response = requests.patch(
        f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
        headers={
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        },
        json=FULL_PTBR_CONFIG
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\n{'=' * 70}")
        print("SUCESSO! JARVIS BRASILEIRO CONFIGURADO")
        print("=" * 70)
        print(f"\n  Nome: {result.get('name', 'N/A')}")
        print(f"  ID: {result.get('id', 'N/A')}")
        print(f"  Voice Provider: {result.get('voice', {}).get('provider', 'N/A')}")
        print(f"  Voice ID: {result.get('voice', {}).get('voiceId', 'N/A')}")
        print(f"  Transcriber: {result.get('transcriber', {}).get('provider', 'N/A')}")
        print(f"  Language: {result.get('transcriber', {}).get('language', 'N/A')}")

        print(f"\n[PARA TESTAR]")
        print(f"  Web: https://vapi.ai/call/{ASSISTANT_ID}")
        print(f"  Ou use o Dashboard do Vapi")

        return True
    else:
        print(f"\n[ERRO] Status: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def set_server_url(ngrok_url: str):
    """Configura o serverUrl para webhooks."""

    full_url = f"{ngrok_url}/vapi/webhook"

    print(f"\n[CONFIGURANDO SERVER URL]")
    print(f"  URL: {full_url}")

    response = requests.patch(
        f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
        headers={
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "serverUrl": full_url,
            "serverUrlSecret": os.environ.get("VAPI_WEBHOOK_SECRET", "your-webhook-secret-here")
        }
    )

    if response.status_code == 200:
        print(f"  Configurado com sucesso!")
        return True
    else:
        print(f"  Erro: {response.status_code}")
        print(f"  {response.text}")
        return False


def verify_configuration():
    """Verifica a configuracao atual do assistente."""

    print("\n[VERIFICANDO CONFIGURACAO ATUAL]")

    response = requests.get(
        f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
        headers={
            "Authorization": f"Bearer {VAPI_API_KEY}"
        }
    )

    if response.status_code == 200:
        data = response.json()

        print(f"\n  Nome: {data.get('name', 'N/A')}")
        print(f"  First Message: {data.get('firstMessage', 'N/A')[:50]}...")

        voice = data.get('voice', {})
        print(f"\n  [VOZ]")
        print(f"    Provider: {voice.get('provider', 'N/A')}")
        print(f"    Voice ID: {voice.get('voiceId', 'N/A')}")
        print(f"    Model: {voice.get('model', 'N/A')}")

        transcriber = data.get('transcriber', {})
        print(f"\n  [TRANSCRICAO]")
        print(f"    Provider: {transcriber.get('provider', 'N/A')}")
        print(f"    Language: {transcriber.get('language', 'N/A')}")
        print(f"    Keywords: {len(transcriber.get('keywords', []))} termos")

        model = data.get('model', {})
        print(f"\n  [MODELO]")
        print(f"    Provider: {model.get('provider', 'N/A')}")
        print(f"    Model: {model.get('model', 'N/A')}")
        print(f"    Tools: {len(model.get('tools', []))} funcoes")

        server_url = data.get('serverUrl', 'Nao configurado')
        print(f"\n  [SERVER URL]")
        print(f"    {server_url}")

        return data
    else:
        print(f"  Erro: {response.status_code}")
        return None


#=================================
# MAIN
#=================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--verify":
            verify_configuration()
        elif sys.argv[1] == "--server":
            if len(sys.argv) > 2:
                set_server_url(sys.argv[2])
            else:
                print("Uso: python vapi_update_full_ptbr.py --server https://seu-ngrok.ngrok.io")
        else:
            # Assume que e URL do ngrok
            update_assistant_full()
            set_server_url(sys.argv[1])
    else:
        # Atualiza tudo exceto serverUrl
        update_assistant_full()

        print("\n" + "=" * 70)
        print("PROXIMO PASSO - CONFIGURAR WEBHOOK")
        print("=" * 70)
        print("""
Para habilitar as tools do Mega Brain:

1. Inicie o webhook server:
   $ cd system/jarvis-voice
   $ python vapi_webhook_server.py

2. Em outro terminal, exponha com ngrok:
   $ ngrok http 5001

3. Configure o serverUrl:
   $ python vapi_update_full_ptbr.py --server https://SEU-ID.ngrok.io

4. Teste no Vapi Dashboard ou:
   https://vapi.ai/call/{ASSISTANT_ID}
""")
