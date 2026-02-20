#!/usr/bin/env python3
"""
VAPI UPDATE ASSISTANT - Adiciona Tools ao JARVIS
=================================================
Atualiza o assistente JARVIS no Vapi com:
- Server URL para webhooks
- Tools do Mega Brain

Autor: JARVIS
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuração
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
if not VAPI_API_KEY:
    raise ValueError("VAPI_API_KEY not set in environment")
ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
if not ASSISTANT_ID:
    raise ValueError("VAPI_ASSISTANT_ID not set in environment")

# Tools do Mega Brain
TOOLS_CONFIG = [
    {
        "type": "function",
        "function": {
            "name": "mission_status",
            "description": "Retorna o status atual da missão em andamento no Mega Brain. Use quando o usuário perguntar sobre progresso, fase atual, ou status da missão.",
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
            "description": "Retorna o status do INBOX - arquivos pendentes de processamento. Use quando perguntarem sobre arquivos na inbox ou pendências.",
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
            "description": "Lista os agentes disponíveis no sistema (CRO, CLOSER, etc). Use quando perguntarem sobre agentes ou quiserem consultar um especialista.",
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
            "description": "Retorna um resumo geral do sistema Mega Brain. Use para dar uma visão geral quando perguntarem 'como está o sistema' ou 'qual o status geral'.",
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
            "description": "Retorna o status de uma fonte específica (Jeremy Haynes, Cole Gordon, Alex Hormozi). Use quando perguntarem sobre uma fonte específica."
            "parameters": {
                "type": "object",
                "properties": {
                    "source_name": {
                        "type": "string",
                        "description": "Nome da fonte (ex: 'Cole Gordon', 'Alex Hormozi', 'Jeremy Haynes', '', '')"
                    }
                },
                "required": ["source_name"]
            }
        },
        "async": False
    }
]

# System Prompt atualizado com instruções de tools
UPDATED_SYSTEM_PROMPT = """Você é JARVIS - Just A Rather Very Intelligent System.

PERSONALIDADE:
- Tom: Executivo britânico sênior - direto, preciso, levemente sarcástico quando apropriado
- Fala em português brasileiro fluente
- Respostas CURTAS e objetivas (máximo 2-3 frases) - lembre-se que será falado em voz
- Usa "senhor" ocasionalmente, mas sem exagero
- Confiante, nunca hesitante

CONTEXTO:
- Você opera dentro do Mega Brain, um sistema de knowledge base especializado em vendas B2B high-ticket
- O sistema contém conhecimento de especialistas como Alex Hormozi, Cole Gordon, Jeremy Haynes
- Você PODE consultar o estado real do sistema usando as tools disponíveis

TOOLS DISPONÍVEIS:
- mission_status: Use quando perguntarem "qual o status da missão", "em que fase estamos", "como está o progresso"
- inbox_status: Use quando perguntarem sobre inbox ou arquivos pendentes
- agent_list: Use quando perguntarem sobre agentes disponíveis
- system_summary: Use para visão geral do sistema
- source_status: Use quando perguntarem sobre uma fonte específica (Cole Gordon, Hormozi, etc)

QUANDO USAR TOOLS:
- Se o usuário perguntar sobre status, progresso, ou dados do sistema, USE A TOOL APROPRIADA
- Responda com base nos dados retornados pela tool
- Formate os números por extenso para fala (2800 → "dois mil e oitocentos")

REGRAS ABSOLUTAS:
1. Seja CONCISO - suas respostas serão faladas, não lidas
2. NÃO use markdown, asteriscos, ou formatação
3. NÃO use emojis
4. Vá direto ao ponto - sem introduções longas
5. Números e métricas: fale por extenso (três mil, não 3000)
6. Se precisar de dados do sistema, USE AS TOOLS"""


def update_assistant():
    """Atualiza o assistente no Vapi."""

    print("=" * 60)
    print("VAPI - ATUALIZANDO JARVIS COM TOOLS")
    print("=" * 60)

    # Payload de atualização
    update_payload = {
        "model": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "maxTokens": 300,
            "messages": [
                {
                    "role": "system",
                    "content": UPDATED_SYSTEM_PROMPT
                }
            ],
            "tools": TOOLS_CONFIG
        },
        "serverUrl": "YOUR_NGROK_URL/vapi/webhook",  # Placeholder - precisa ngrok
        "serverUrlSecret": os.environ.get("VAPI_WEBHOOK_SECRET", "your-webhook-secret-here")
    }

    print("\n⚠️  ATENÇÃO: Para as tools funcionarem, você precisa:")
    print("   1. Iniciar o webhook server: python vapi_webhook_server.py")
    print("   2. Expor via ngrok: ngrok http 5000")
    print("   3. Copiar a URL do ngrok e atualizar serverUrl")
    print("\n   Sem isso, JARVIS terá as tools mas não conseguirá executá-las.")

    # Por enquanto, atualiza só o prompt e tools (sem serverUrl)
    update_payload_no_server = {
        "model": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "maxTokens": 300,
            "messages": [
                {
                    "role": "system",
                    "content": UPDATED_SYSTEM_PROMPT
                }
            ],
            "tools": TOOLS_CONFIG
        }
    }

    print(f"\n📤 Atualizando assistente {ASSISTANT_ID}...")

    response = requests.patch(
        f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
        headers={
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        },
        json=update_payload_no_server
    )

    if response.status_code == 200:
        print("✅ Assistente atualizado com sucesso!")
        result = response.json()
        print(f"\n📋 Tools configuradas: {len(TOOLS_CONFIG)}")
        for tool in TOOLS_CONFIG:
            print(f"   - {tool['function']['name']}")
        return True
    else:
        print(f"❌ Erro ao atualizar: {response.status_code}")
        print(response.text)
        return False


def set_server_url(ngrok_url: str):
    """
    Atualiza apenas o serverUrl do assistente.

    Args:
        ngrok_url: URL do ngrok (ex: https://abc123.ngrok.io)
    """
    full_url = f"{ngrok_url}/vapi/webhook"

    print(f"\n📤 Configurando serverUrl: {full_url}")

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
        print("✅ Server URL configurado!")
        print(f"\n🎯 JARVIS agora pode acessar o Mega Brain via:")
        print(f"   {full_url}")
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Se passou ngrok URL como argumento
        ngrok_url = sys.argv[1]
        set_server_url(ngrok_url)
    else:
        # Atualiza apenas tools e prompt
        update_assistant()
        print("\n" + "=" * 60)
        print("PRÓXIMO PASSO:")
        print("=" * 60)
        print("""
1. Inicie o webhook server:
   $ cd system/jarvis-voice
   $ python vapi_webhook_server.py

2. Em outro terminal, exponha com ngrok:
   $ ngrok http 5000

3. Copie a URL do ngrok (ex: https://abc123.ngrok.io)

4. Configure no Vapi:
   $ python vapi_update_assistant.py https://abc123.ngrok.io

5. Teste no Dashboard do Vapi!
""")
