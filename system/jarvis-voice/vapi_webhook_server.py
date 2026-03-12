#!/usr/bin/env python3
"""
VAPI WEBHOOK SERVER - JARVIS MEGA BRAIN
========================================
Servidor que recebe chamadas do Vapi e executa tools no Mega Brain.

Endpoint: POST /vapi/webhook
Formato Vapi: https://docs.vapi.ai/server-url

Autor: JARVIS
"""

import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import do connector existente
from mega_brain_connector import MegaBrainConnector
from config import Config

app = Flask(__name__)
CORS(app)

# Inicializa connector
connector = MegaBrainConnector()

#=================================
# TOOLS DO MEGA BRAIN
#=================================

def tool_mission_status() -> dict:
    """Retorna status atual da missão."""
    connector.reload_state()

    # Lê o arquivo de progresso para dados mais atualizados
    progress_path = Path(Config.MEGA_BRAIN_PATH) / "logs/MISSIONS/MISSION-2026-001-PROGRESS.md"

    try:
        # Dados do state
        mission = connector.state.get("mission", {})
        pipeline = connector.state.get("pipeline", {})

        # Dynamic data from state file
        return {
            "mission_id": mission.get("id", ""),
            "phase": pipeline.get("phase", 0),
            "phase_name": pipeline.get("phase_name", ""),
            "status": pipeline.get("status", ""),
            "batch_atual": pipeline.get("batch_current", 0),
            "batches_total": pipeline.get("batch_total", 0),
            "progresso_percent": pipeline.get("percent_complete", 0),
            "arquivos_processados": 0,
            "arquivos_total": 0,
            "insights_extraidos": 0,
            "heuristicas": 0,
            "frameworks": 0,
            "filosofias": 0,
            "sources_completas": [],
            "source_atual": "",
            "proximo_batch": ""
        }
    except Exception as e:
        return {"error": str(e)}


def tool_inbox_status() -> dict:
    """Retorna status do INBOX."""
    inbox_path = Path(Config.MEGA_BRAIN_PATH) / "inbox"

    try:
        total_files = 0
        by_source = {}

        for source_dir in inbox_path.iterdir():
            if source_dir.is_dir() and not source_dir.name.startswith('.'):
                count = sum(1 for f in source_dir.rglob('*') if f.is_file())
                if count > 0:
                    by_source[source_dir.name] = count
                    total_files += count

        return {
            "total_arquivos": total_files,
            "por_fonte": by_source,
            "status": "ORGANIZADO" if total_files < 50 else "REQUER_ATENCAO"
        }
    except Exception as e:
        return {"error": str(e)}


def tool_agent_list() -> dict:
    """Lista agentes disponíveis."""
    agents = connector.get_available_agents()
    return {
        "total": len(agents),
        "agentes": agents[:20],  # Limita para voz
        "categorias": ["C-LEVEL", "SALES", "MARKETING", "operations", "persons"]
    }


def tool_system_summary() -> dict:
    """Resumo geral do sistema."""
    context = connector.get_context_for_claude()

    return {
        "sistema": "Mega Brain",
        "versao": "",
        "missao_ativa": "",
        "fase_atual": "",
        "progresso": "",
        "ultimo_batch": "",
        "proximo_passo": "",
        "saude": "OPERACIONAL"
    }


def tool_read_file(file_path: str) -> dict:
    """Lê conteúdo de um arquivo do Mega Brain."""
    try:
        full_path = Path(Config.MEGA_BRAIN_PATH) / file_path

        if not full_path.exists():
            return {"error": f"Arquivo não encontrado: {file_path}"}

        if not full_path.is_file():
            return {"error": f"Não é um arquivo: {file_path}"}

        # Limita tamanho para voz
        content = full_path.read_text(encoding='utf-8')
        if len(content) > 2000:
            content = content[:2000] + "\n... [truncado para voz]"

        return {
            "arquivo": file_path,
            "conteudo": content,
            "tamanho": full_path.stat().st_size
        }
    except Exception as e:
        return {"error": str(e)}


def tool_source_status(source_name: str) -> dict:
    """Status de uma fonte específica."""
    sources_data = {}

    key = source_name.lower()
    for k, v in sources_data.items():
        if k in key or key in k:
            return v

    return {"error": f"Fonte '{source_name}' não encontrada"}


#=================================
# VAPI WEBHOOK HANDLER
#=================================

@app.route('/vapi/webhook', methods=['POST'])
def vapi_webhook():
    """
    Endpoint principal para Vapi.
    Recebe tool calls e retorna resultados.
    """
    try:
        data = request.json
        print(f"\n[VAPI] Webhook recebido: {json.dumps(data, indent=2)[:500]}")

        message_type = data.get('message', {}).get('type', '')

        # Tool call do assistente
        if message_type == 'tool-calls':
            tool_calls = data.get('message', {}).get('toolCalls', [])
            results = []

            for tool_call in tool_calls:
                tool_name = tool_call.get('function', {}).get('name', '')
                tool_args = tool_call.get('function', {}).get('arguments', {})
                tool_id = tool_call.get('id', '')

                print(f"[VAPI] Tool call: {tool_name} com args: {tool_args}")

                # Executa a tool apropriada (nomes conforme Vapi config)
                if tool_name in ['mission_status', 'get_mission_status']:
                    result = tool_mission_status()
                elif tool_name in ['inbox_status', 'get_inbox_status']:
                    result = tool_inbox_status()
                elif tool_name in ['agent_list', 'get_agents_list']:
                    result = tool_agent_list()
                elif tool_name in ['system_summary', 'get_system_summary']:
                    result = tool_system_summary()
                elif tool_name in ['source_status', 'get_source_status']:
                    source = tool_args.get('source_name', '')
                    result = tool_source_status(source)
                elif tool_name == 'read_file':
                    file_path = tool_args.get('file_path', '')
                    result = tool_read_file(file_path)
                else:
                    result = {"error": f"Tool '{tool_name}' não implementada"}

                results.append({
                    "toolCallId": tool_id,
                    "result": json.dumps(result, ensure_ascii=False)
                })

            return jsonify({"results": results})

        # Outros tipos de mensagem (status updates, etc.)
        elif message_type == 'status-update':
            status = data.get('message', {}).get('status', '')
            print(f"[VAPI] Status update: {status}")
            return jsonify({"status": "received"})

        elif message_type == 'end-of-call-report':
            print(f"[VAPI] Call ended")
            # Registra no connector
            connector.add_action("Voice call ended")
            return jsonify({"status": "received"})

        # Fallback
        return jsonify({"status": "ok"})

    except Exception as e:
        print(f"[VAPI] Erro: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "JARVIS Vapi Webhook",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/', methods=['GET'])
def root():
    """Root endpoint com info."""
    return jsonify({
        "service": "JARVIS Mega Brain - Vapi Webhook Server",
        "version": "1.0.0",
        "endpoints": {
            "/vapi/webhook": "POST - Vapi webhook handler",
            "/health": "GET - Health check"
        },
        "tools": [
            "mission_status - Status da missão atual",
            "inbox_status - Status do INBOX",
            "agent_list - Lista de agentes",
            "system_summary - Resumo do sistema",
            "source_status - Status de uma fonte específica"
        ]
    })


#=================================
# MAIN
#=================================

if __name__ == '__main__':
    print("=" * 60)
    print("JARVIS MEGA BRAIN - VAPI WEBHOOK SERVER")
    print("=" * 60)
    print(f"\nEndpoint: http://localhost:5000/vapi/webhook")
    print(f"Health:   http://localhost:5000/health")
    print("\nTools disponíveis:")
    print("  - mission_status")
    print("  - inbox_status")
    print("  - agent_list")
    print("  - system_summary")
    print("  - source_status")
    print("\n" + "=" * 60)

    app.run(host='127.0.0.1', port=5001, debug=False)
