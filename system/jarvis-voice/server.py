# server.py
"""
JARVIS Command Center - Backend Server
======================================
Servidor FastAPI que:
- Recebe comandos de voz via WebSocket
- Executa comandos no Mega Brain
- Transmite logs em tempo real
- Usa Claude Tool Calling para interpretar comandos
- TTS via Sesame CSM-1B (ultra-humanizado) com fallback ElevenLabs
"""

import asyncio
import json
import os
import subprocess
import sys
import base64
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Adiciona path do projeto
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from config import Config
from mega_brain_connector import MegaBrainConnector
from orchestrator import JARVIS_SYSTEM_PROMPT

#==============================
# TTS ENGINE - Sesame CSM-1B (estado da arte em humanização)
#==============================

# Flag para usar Sesame (True) ou ElevenLabs (False)
# NOTA: Sesame requer login no HuggingFace. Para ativar:
# 1. huggingface-cli login
# 2. Aceitar termos em https://huggingface.co/sesame/csm-1b
# 3. Mudar para True
USE_SESAME_TTS = False  # Usando ElevenLabs v3 com Audio Tags por enquanto
sesame_handler = None

def init_sesame():
    """Inicializa o handler Sesame (lazy loading)."""
    global sesame_handler
    if sesame_handler is None and USE_SESAME_TTS:
        try:
            from tts_sesame import SesameTTSHandler
            sesame_handler = SesameTTSHandler()
            print("[TTS] Sesame CSM-1B inicializado - Voz ultra-humanizada ativada")
        except Exception as e:
            print(f"[TTS] Sesame não disponível: {e}")
            print("[TTS] Usando ElevenLabs como fallback")

#==============================
# CONFIGURAÇÃO
#==============================

app = FastAPI(title="JARVIS Command Center", version="1.0.0")

# Clientes WebSocket conectados
connected_clients: List[WebSocket] = []

# Histórico de conversa
conversation_history: List[Dict] = []

# Connector do Mega Brain
mega_brain = MegaBrainConnector()

# Cliente Anthropic
anthropic = Anthropic(api_key=Config.ANTHROPIC_API_KEY)


#==============================
# FERRAMENTAS DISPONÍVEIS PARA JARVIS
#==============================

JARVIS_TOOLS = [
    {
        "name": "execute_command",
        "description": "Executa um comando do sistema Mega Brain. Use para processar arquivos, verificar status, consultar agentes, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "O comando a executar. Exemplos: 'mission status', 'scan-inbox', 'process-jarvis --batch 10', 'ask CRO sobre pricing'"
                },
                "description": {
                    "type": "string",
                    "description": "Descrição curta do que o comando faz (para o log)"
                }
            },
            "required": ["command", "description"]
        }
    },
    {
        "name": "run_python_script",
        "description": "Executa um script Python do diretório SCRIPTS/. Use para operações específicas como indexação RAG, health check, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "Nome do script (ex: 'health_check.py', 'rag_index.py --knowledge')"
                },
                "description": {
                    "type": "string",
                    "description": "Descrição do que o script faz"
                }
            },
            "required": ["script", "description"]
        }
    },
    {
        "name": "read_file",
        "description": "Lê conteúdo de um arquivo do projeto. Use para consultar estados, logs, documentos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Caminho relativo ao Mega Brain (ex: 'system/SESSION-STATE.md', '.claude/jarvis/STATE.json')"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "get_system_status",
        "description": "Obtém status completo do sistema Mega Brain: missão atual, pipeline, agentes, métricas.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_inbox",
        "description": "Lista arquivos pendentes no INBOX para processamento.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Filtrar por fonte (ex: 'COLE GORDON', 'ALEX HORMOZI'). Opcional."
                }
            },
            "required": []
        }
    },
    {
        "name": "consult_agent",
        "description": "Consulta um agente específico do sistema (CRO, CFO, CMO, CLOSER, etc).",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Nome do agente (CRO, CFO, CMO, COO, CLOSER, BDR, SDR, SALES-MANAGER)"
                },
                "question": {
                    "type": "string",
                    "description": "Pergunta para o agente"
                }
            },
            "required": ["agent", "question"]
        }
    }
]


#==============================
# EXECUTOR DE FERRAMENTAS
#==============================

async def broadcast_log(message: str, type: str = "info"):
    """Envia log para todos os clientes conectados."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "type": "log",
        "timestamp": timestamp,
        "message": message,
        "level": type
    }
    for client in connected_clients:
        try:
            await client.send_json(log_entry)
        except:
            pass


ALLOWED_COMMANDS = {
    "mission": ["python3", "SCRIPTS/mission_status.py"],
    "scan-inbox": ["python3", "SCRIPTS/inbox_auto_organize.py", "--report"],
    "process-jarvis": ["python3", "SCRIPTS/jarvis_pipeline.py"],
    "health": ["python3", "SCRIPTS/health_check.py"],
}

ALLOWED_SCRIPTS = {
    "health_check.py",
    "rag_index.py",
    "mission_status.py",
    "inbox_auto_organize.py",
    "jarvis_pipeline.py",
}


async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Executa uma ferramenta e retorna o resultado."""

    if tool_name == "execute_command":
        command = tool_input["command"]
        description = tool_input.get("description", command)

        await broadcast_log(f"🔧 Executando: {description}", "command")

        # Resolve command to an allowlisted entry
        cmd_args = None
        for prefix, args in ALLOWED_COMMANDS.items():
            if command.startswith(prefix):
                cmd_args = list(args)
                break

        if cmd_args is None:
            await broadcast_log(f"❌ Comando não permitido: {command}", "error")
            return f"Erro: comando '{command}' não está na lista de comandos permitidos"

        try:
            result = subprocess.run(
                cmd_args,
                shell=False,
                cwd=Config.MEGA_BRAIN_PATH,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout or result.stderr or "Comando executado sem output"
            await broadcast_log(f"✅ Concluído: {description}", "success")
            return output[:2000]
        except subprocess.TimeoutExpired:
            await broadcast_log(f"⏱️ Timeout: {description}", "warning")
            return "Comando excedeu timeout de 60 segundos"
        except Exception as e:
            await broadcast_log(f"❌ Erro: {str(e)}", "error")
            return f"Erro: {str(e)}"

    elif tool_name == "run_python_script":
        script = tool_input["script"]
        description = tool_input.get("description", script)

        # Validate script name: no path traversal, must be in allowlist
        script_basename = Path(script).name
        if ".." in script or "/" in script or "\\" in script:
            return "Erro: nome de script inválido"
        if script_basename not in ALLOWED_SCRIPTS:
            return f"Erro: script '{script_basename}' não está na lista de scripts permitidos"

        await broadcast_log(f"🐍 Executando script: {script_basename}", "command")

        try:
            result = subprocess.run(
                ["python3", f"SCRIPTS/{script_basename}"],
                shell=False,
                cwd=Config.MEGA_BRAIN_PATH,
                capture_output=True,
                text=True,
                timeout=120
            )
            output = result.stdout or result.stderr or "Script executado"
            await broadcast_log(f"✅ Script concluído", "success")
            return output[:2000]
        except Exception as e:
            await broadcast_log(f"❌ Erro no script: {str(e)}", "error")
            return f"Erro: {str(e)}"

    elif tool_name == "read_file":
        path = tool_input["path"]
        full_path = (Path(Config.MEGA_BRAIN_PATH) / path).resolve()
        base_path = Path(Config.MEGA_BRAIN_PATH).resolve()

        # Path traversal protection
        if not str(full_path).startswith(str(base_path)):
            return "Erro: acesso negado - caminho fora do Mega Brain"

        await broadcast_log(f"📄 Lendo: {path}", "info")

        try:
            content = full_path.read_text(encoding="utf-8")
            return content[:3000]
        except Exception as e:
            return f"Erro ao ler arquivo: {str(e)}"

    elif tool_name == "get_system_status":
        await broadcast_log("📊 Obtendo status do sistema...", "info")

        status = {
            "mission": mega_brain.get_mission_summary(),
            "agents": mega_brain.get_available_agents(),
            "context": mega_brain.get_context_for_claude()
        }
        return json.dumps(status, indent=2, ensure_ascii=False)

    elif tool_name == "list_inbox":
        source = tool_input.get("source", "")
        await broadcast_log(f"📥 Listando INBOX{' (' + source + ')' if source else ''}...", "info")

        inbox_path = Path(Config.MEGA_BRAIN_PATH) / "inbox"
        files = []

        for item in inbox_path.rglob("*.txt"):
            if source.upper() in str(item).upper():
                files.append(str(item.relative_to(inbox_path)))

        return f"Encontrados {len(files)} arquivos:\n" + "\n".join(files[:20])

    elif tool_name == "consult_agent":
        agent = tool_input["agent"].upper()
        question = tool_input["question"]

        await broadcast_log(f"🤖 Consultando agente {agent}...", "info")

        agent_context = mega_brain.get_agent_context(agent)
        if agent_context:
            return f"Contexto do {agent}:\n{agent_context[:2000]}"
        else:
            return f"Agente {agent} não encontrado"

    return "Ferramenta não reconhecida"


#==============================
# PROCESSADOR DE MENSAGENS COM TOOL CALLING
#==============================

async def process_message(user_message: str) -> str:
    """Processa mensagem do usuário com possível execução de ferramentas."""

    # Adiciona ao histórico
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Monta contexto do sistema
    system_context = mega_brain.get_context_for_claude()

    system_prompt = f"""
{JARVIS_SYSTEM_PROMPT}

═══════════════════════════════════════════════════════════════════════════════
                         ESTADO ATUAL DO MEGA BRAIN
═══════════════════════════════════════════════════════════════════════════════

{system_context}

═══════════════════════════════════════════════════════════════════════════════
                         CAPACIDADES DE EXECUÇÃO
═══════════════════════════════════════════════════════════════════════════════

Você tem acesso a ferramentas para EXECUTAR ações no sistema:
- execute_command: Executar comandos do Mega Brain
- run_python_script: Executar scripts Python
- read_file: Ler arquivos do projeto
- get_system_status: Obter status completo
- list_inbox: Listar arquivos pendentes
- consult_agent: Consultar agentes específicos

Quando o usuário pedir para fazer algo (processar, verificar, consultar),
USE as ferramentas apropriadas. Não apenas fale - EXECUTE.

Após executar, resuma o resultado de forma conversacional para voz.
"""

    # Primeira chamada - pode retornar tool_use
    response = anthropic.messages.create(
        model=Config.CLAUDE_MODEL,
        max_tokens=2048,
        system=system_prompt,
        tools=JARVIS_TOOLS,
        messages=conversation_history[-10:]  # Últimas 10 mensagens
    )

    # Processa resposta
    final_response = ""
    tool_results = []

    for block in response.content:
        if block.type == "text":
            final_response += block.text
        elif block.type == "tool_use":
            # Executa a ferramenta
            await broadcast_log(f"🔧 JARVIS chamando: {block.name}", "tool")
            result = await execute_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result
            })

    # Se houve uso de ferramentas, faz segunda chamada para resumir
    if tool_results:
        conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        conversation_history.append({
            "role": "user",
            "content": tool_results
        })

        # Segunda chamada para resumir resultados
        summary_response = anthropic.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt + "\n\nRESUMA os resultados das ferramentas de forma conversacional e concisa para falar por voz. Máximo 100 palavras.",
            messages=conversation_history[-10:]
        )

        final_response = summary_response.content[0].text

    # Adiciona resposta ao histórico
    conversation_history.append({
        "role": "assistant",
        "content": final_response
    })

    return final_response


#==============================
# ENDPOINTS
#==============================

@app.get("/")
async def root():
    """Serve a página principal."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para comunicação em tempo real."""
    await websocket.accept()
    connected_clients.append(websocket)

    await broadcast_log("🤖 JARVIS Command Center conectado", "success")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                user_message = data.get("content", "")

                # Envia confirmação
                await websocket.send_json({
                    "type": "user_message",
                    "content": user_message
                })

                await broadcast_log(f"🎤 Recebido: {user_message[:50]}...", "info")

                # Processa mensagem
                response = await process_message(user_message)

                # Envia resposta
                await websocket.send_json({
                    "type": "jarvis_response",
                    "content": response
                })

            elif data.get("type") == "tts_request":
                # Gera áudio via ElevenLabs
                text = data.get("text", "")
                audio_url = await generate_tts(text)
                await websocket.send_json({
                    "type": "audio",
                    "url": audio_url
                })

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        await broadcast_log("🔌 Cliente desconectado", "warning")


@app.post("/api/message")
async def api_message(data: dict):
    """Endpoint REST para mensagens (fallback)."""
    user_message = data.get("message", "")
    response = await process_message(user_message)
    return {"response": response}


@app.get("/api/status")
async def api_status():
    """Status do sistema."""
    return {
        "status": "online",
        "clients": len(connected_clients),
        "mega_brain": mega_brain.get_mission_summary()
    }


#==============================
# TTS (Text-to-Speech) - Sesame CSM + ElevenLabs Fallback
#==============================

async def generate_tts_sesame(text: str) -> str:
    """
    Gera áudio via Sesame CSM-1B (ultra-humanizado).

    Diferenciais:
    - Memória conversacional (mantém tom consistente)
    - Hesitações naturais, respiração, correções
    - Tom que se adapta ao contexto emocional
    """
    global sesame_handler

    try:
        init_sesame()

        if sesame_handler is not None:
            # Gera áudio com Sesame
            audio_bytes = await sesame_handler.speak(text)

            # Retorna como base64 data URL (WAV)
            audio_base64 = base64.b64encode(audio_bytes).decode()
            return f"data:audio/wav;base64,{audio_base64}"

    except Exception as e:
        print(f"[TTS] Erro no Sesame: {e}, usando fallback ElevenLabs...")

    # Fallback para ElevenLabs
    return await generate_tts_elevenlabs(text)


async def generate_tts_elevenlabs(text: str) -> str:
    """
    Gera áudio via ElevenLabs com modelo multilingual otimizado para PT-BR.

    Usa eleven_multilingual_v2 que tem:
    - Excelente pronúncia de português brasileiro
    - Naturalidade e entonação corretas
    - Melhor compreensão de contexto em português
    """
    import requests

    # Usa texto direto - multilingual_v2 não suporta Audio Tags
    # mas tem pronúncia muito superior para português
    print(f"[TTS] Gerando: {text[:80]}...")

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{Config.ELEVENLABS_VOICE_ID}",
        headers={
            "xi-api-key": Config.ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Melhor para português
            "voice_settings": {
                "stability": Config.VOICE_STABILITY,           # 0.70 - Calmo e preciso
                "similarity_boost": Config.VOICE_SIMILARITY,   # 0.85 - Consistente
                "style": Config.VOICE_STYLE,                   # 0.20 - Profissional
                "use_speaker_boost": Config.VOICE_SPEAKER_BOOST
            }
        }
    )

    if response.status_code == 200:
        # Retorna como base64 data URL
        audio_base64 = base64.b64encode(response.content).decode()
        return f"data:audio/mpeg;base64,{audio_base64}"
    else:
        print(f"[TTS] Erro ElevenLabs: {response.status_code} - {response.text}")
        return ""


async def generate_tts(text: str) -> str:
    """
    Gera áudio usando o melhor engine disponível.

    Prioridade:
    1. Sesame CSM-1B (se GPU disponível) - MELHOR QUALIDADE
    2. ElevenLabs (fallback) - Boa qualidade
    """
    if USE_SESAME_TTS:
        return await generate_tts_sesame(text)
    else:
        return await generate_tts_elevenlabs(text)


#==============================
# MAIN
#==============================

if __name__ == "__main__":
    # Cria diretório static se não existir
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)

    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                    JARVIS COMMAND CENTER                              ║
║                                                                       ║
║                    Servidor iniciando...                              ║
║                                                                       ║
║             Acesse: http://localhost:8000                             ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")

    uvicorn.run(app, host="127.0.0.1", port=8000)
