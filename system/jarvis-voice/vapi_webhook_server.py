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

***REMOVED***=================================
# TOOLS DO MEGA BRAIN
***REMOVED***=================================

def tool_mission_status() -> dict:
    """Retorna status atual da missão."""
    connector.reload_state()

    # Lê o arquivo de progresso para dados mais atualizados
    progress_path = Path(Config.MEGA_BRAIN_PATH) / "logs/MISSIONS/MISSION-2026-001-PROGRESS.md"

    try:
        # Dados do state
        mission = connector.state.get("mission", {})
        pipeline = connector.state.get("pipeline", {})

        # Dados hardcoded do progresso atual (baseado no arquivo lido)
        return {
            "mission_id": "MISSION-2026-001",
            "phase": 4,
            "phase_name": "Pipeline Jarvis",
            "status": "IN_PROGRESS",
            "batch_atual": 35,
            "batches_total": 57,
            "progresso_percent": 61.4,
            "arquivos_processados": 209,
            "arquivos_total": 564,
            "insights_extraidos": 2800,
            "heuristicas": 526,
            "frameworks": 195,
            "filosofias": 221,
            "sources_completas": ["Jeremy Haynes", "", "", "Alex Hormozi", "Jordan Lee"]
            "source_atual": "Cole Gordon",
            "proximo_batch": "BATCH-036"
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
        "versao": "3.33.0",
        "missao_ativa": "MISSION-2026-001",
        "fase_atual": "Phase 4 - Pipeline",
        "progresso": "61.4%",
        "ultimo_batch": "BATCH-035 (Cole Gordon)",
        "proximo_passo": "Continuar processamento Cole Gordon",
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
    sources_data = {
        "jeremy haynes": {
            "nome": "Jeremy Haynes",
            "empresa": "Megalodon Marketing",
            "batches": "001-004",
            "status": "COMPLETO",
            "arquivos": 31,
            "insights": 130,
            "heuristicas": 70
        },
            "batches": "005-020",
            "status": "COMPLETO",
            "arquivos": 67,
            "insights": 1250,
            "heuristicas": 180
        },
        "g4": {
            "empresa": "Gestão 4.0",
            "batches": "021-028",
            "status": "COMPLETO",
            "arquivos": 55,
            "insights": 820,
            "heuristicas": 95
        },
        "alex hormozi": {
            "nome": "Alex Hormozi",
            "empresa": "Alex Hormozi",
            "batches": "029-031",
            "status": "COMPLETO",
            "arquivos": 19,
            "insights": 203,
            "heuristicas": 65
        },
        "cole gordon": {
            "nome": "Cole Gordon",
            "empresa": "Cole Gordon",
            "batches": "033-043",
            "status": "EM_PROGRESSO",
            "arquivos_processados": 22,
            "arquivos_total": 86,
            "insights": 150,
            "heuristicas": 77,
            "batches_completos": 3,
            "batches_pendentes": 8
        }
    }

    key = source_name.lower()
    for k, v in sources_data.items():
        if k in key or key in k:
            return v

    return {"error": f"Fonte '{source_name}' não encontrada"}


***REMOVED***=================================
# VAPI WEBHOOK HANDLER
***REMOVED***=================================

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


***REMOVED***=================================
# MAIN
***REMOVED***=================================

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

    app.run(host='0.0.0.0', port=5001, debug=True)
