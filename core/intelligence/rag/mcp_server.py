#!/usr/bin/env python3
"""
MCP KNOWLEDGE SERVER - Phase 5.2
===================================
Exposes the Mega Brain knowledge retrieval system as MCP tools.

Tools available:
  - search_knowledge: Hybrid search with filters
  - search_cross_expert: Graph query for cross-expert synthesis
  - search_deep: Full pipeline with all layers
  - get_agent_context: Trimmed context for a specific agent
  - resolve_chunk: chunk_id → source → text
  - graph_query: Query knowledge graph for entity relationships
  - agent_lookup: Look up agent by name across categories
  - dossier_search: Search dossiers by topic or person
  - pipeline_status: Get pipeline operational status
  - quality_report: Get recent quality scores

Usage:
  python3 -m core.intelligence.rag.mcp_server

MCP config (.mcp.json):
  {
    "mega-brain-knowledge": {
      "command": "python3",
      "args": ["-m", "core.intelligence.rag.mcp_server"]
    }
  }

Versao: 2.0.0
Data: 2026-03-14
"""

import json
import sys
from typing import Any

# ---------------------------------------------------------------------------
# MCP PROTOCOL (stdio JSON-RPC)
# ---------------------------------------------------------------------------
# The MCP server communicates via stdin/stdout using JSON-RPC 2.0.
# We implement the minimal MCP protocol for tool serving.


def _send_response(id: Any, result: Any) -> None:
    """Send JSON-RPC response."""
    response = {"jsonrpc": "2.0", "id": id, "result": result}
    msg = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}")
    sys.stdout.flush()


def _send_error(id: Any, code: int, message: str) -> None:
    """Send JSON-RPC error."""
    response = {
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message},
    }
    msg = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# TOOL DEFINITIONS
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "search_knowledge",
        "description": (
            "Search the Mega Brain knowledge base using hybrid retrieval "
            "(vector + BM25 + reranking). Returns ranked chunks with sources. "
            "Use for any factual question about expert knowledge."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results (default 10)",
                    "default": 10,
                },
                "person": {
                    "type": "string",
                    "description": "Filter by person (e.g. 'alex-hormozi')",
                },
                "domain": {
                    "type": "string",
                    "description": "Filter by domain (e.g. 'vendas')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_cross_expert",
        "description": (
            "Search across experts using knowledge graph + associative memory. "
            "Best for finding how different experts approach the same topic. "
            "Uses HippoRAG PageRank for cross-expert discovery."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query about cross-expert perspectives",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results (default 15)",
                    "default": 15,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_deep",
        "description": (
            "Deep search using full pipeline: hybrid + graph + ontology + "
            "associative memory. Maximum recall, slower (~500ms). "
            "Use for complex analytical queries."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Complex analytical query",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results (default 20)",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_agent_context",
        "description": (
            "Get trimmed context for a specific agent, filtered by query "
            "relevance. Returns only the most relevant sections of the agent's "
            "knowledge base. Much smaller than loading full agent files."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question/topic to filter context for",
                },
                "agent_name": {
                    "type": "string",
                    "description": "Agent name (e.g. 'closer', 'cro', 'cfo')",
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Max context tokens (default 8000)",
                    "default": 8000,
                },
            },
            "required": ["query", "agent_name"],
        },
    },
    {
        "name": "resolve_chunk",
        "description": (
            "Resolve a chunk_id to its full text and source information. "
            "Use when you need the complete text of a retrieved chunk."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "chunk_id": {
                    "type": "string",
                    "description": "The chunk ID to resolve (e.g. 'HEUR-AH-025')",
                },
            },
            "required": ["chunk_id"],
        },
    },
]


# ---------------------------------------------------------------------------
# TOOL HANDLERS
# ---------------------------------------------------------------------------
def handle_search_knowledge(params: dict) -> dict:
    """Handle search_knowledge tool call."""
    from .adaptive_router import Pipeline, route_query

    query = params.get("query", "")
    top_k = params.get("top_k", 10)
    person = params.get("person")
    domain = params.get("domain")

    # Use hybrid pipeline
    result = route_query(query, pipeline=Pipeline.HYBRID)

    # Apply filters
    results = result.get("results", [])
    if person:
        results = [r for r in results if person.lower() in r.get("person", "").lower()]
    if domain:
        results = [r for r in results if domain.lower() in r.get("domain", "").lower()]

    return {
        "query": query,
        "results": results[:top_k],
        "context": result.get("context", ""),
        "sources": result.get("sources", [])[:top_k],
        "latency_ms": result.get("latency_ms", 0),
    }


def handle_search_cross_expert(params: dict) -> dict:
    """Handle search_cross_expert tool call."""
    from .adaptive_router import Pipeline, route_query

    query = params.get("query", "")
    top_k = params.get("top_k", 15)

    result = route_query(query, pipeline=Pipeline.HYBRID_GRAPH)

    return {
        "query": query,
        "strategy": result.get("graph_strategy", ""),
        "results": result.get("results", [])[:top_k],
        "context": result.get("context", ""),
        "sources": result.get("sources", [])[:top_k],
        "latency_ms": result.get("latency_ms", 0),
    }


def handle_search_deep(params: dict) -> dict:
    """Handle search_deep tool call."""
    from .adaptive_router import Pipeline, route_query

    query = params.get("query", "")
    top_k = params.get("top_k", 20)

    result = route_query(query, pipeline=Pipeline.FULL)

    return {
        "query": query,
        "results": result.get("results", [])[:top_k],
        "graph_results": result.get("graph_results", [])[:10],
        "hybrid_results": result.get("hybrid_results", [])[:10],
        "context": result.get("context", ""),
        "sources": result.get("sources", [])[:top_k],
        "latency_ms": result.get("latency_ms", 0),
    }


def handle_get_agent_context(params: dict) -> dict:
    """Handle get_agent_context tool call."""
    from .hybrid_query import build_rag_context

    query = params.get("query", "")
    agent_name = params.get("agent_name", "")
    max_tokens = params.get("max_tokens", 8000)

    # Search with person filter
    result = build_rag_context(query, top_k=20, max_tokens=max_tokens)

    if "error" in result:
        return result

    return {
        "agent": agent_name,
        "query": query,
        "context": result.get("context", ""),
        "sources": result.get("sources", []),
        "chunks_used": result.get("chunks_used", 0),
        "latency_ms": result.get("latency_ms", 0),
    }


def handle_resolve_chunk(params: dict) -> dict:
    """Handle resolve_chunk tool call."""
    from .hybrid_index import get_index

    chunk_id = params.get("chunk_id", "")
    idx = get_index()

    if not idx.built:
        return {"error": "Index not built"}

    # Search through chunks for matching ID
    for chunk in idx.chunks:
        if chunk.get("chunk_id") == chunk_id:
            return {
                "chunk_id": chunk_id,
                "text": chunk.get("text", ""),
                "source_file": chunk.get("source_file", ""),
                "person": chunk.get("person", ""),
                "domain": chunk.get("domain", ""),
                "section": chunk.get("section", ""),
                "layer": chunk.get("layer", ""),
            }

    return {"error": f"Chunk not found: {chunk_id}"}


# Tool handler dispatch
TOOL_HANDLERS = {
    "search_knowledge": handle_search_knowledge,
    "search_cross_expert": handle_search_cross_expert,
    "search_deep": handle_search_deep,
    "get_agent_context": handle_get_agent_context,
    "resolve_chunk": handle_resolve_chunk,
}

# ---------------------------------------------------------------------------
# EXTENDED TOOLS (from mcp_tools.py)
# ---------------------------------------------------------------------------
from .mcp_tools import EXTENDED_TOOL_HANDLERS, EXTENDED_TOOLS

TOOLS.extend(EXTENDED_TOOLS)
TOOL_HANDLERS.update(EXTENDED_TOOL_HANDLERS)


# ---------------------------------------------------------------------------
# MCP SERVER LOOP
# ---------------------------------------------------------------------------
def handle_request(request: dict) -> None:
    """Handle a single MCP JSON-RPC request."""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        _send_response(
            req_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "mega-brain-knowledge",
                    "version": "2.0.0",
                },
            },
        )

    elif method == "notifications/initialized":
        pass  # No response needed for notifications

    elif method == "tools/list":
        _send_response(req_id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            _send_error(req_id, -32601, f"Unknown tool: {tool_name}")
            return

        try:
            result = handler(arguments)
            _send_response(
                req_id,
                {
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}
                    ],
                },
            )
        except Exception as e:
            _send_error(req_id, -32000, f"Tool error: {e!s}")

    else:
        _send_error(req_id, -32601, f"Unknown method: {method}")


def run_server():
    """Run the MCP server (stdio transport)."""
    import io

    reader = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

    while True:
        try:
            # Read Content-Length header
            line = reader.readline()
            if not line:
                break

            line = line.strip()
            if not line.startswith("Content-Length:"):
                continue

            content_length = int(line.split(":")[1].strip())

            # Read blank line
            reader.readline()

            # Read body
            body = reader.read(content_length)
            request = json.loads(body)

            handle_request(request)

        except (json.JSONDecodeError, ValueError, EOFError):
            break
        except KeyboardInterrupt:
            break


# ---------------------------------------------------------------------------
# CLI (for testing without MCP)
# ---------------------------------------------------------------------------
def main():
    """CLI mode for testing tools directly."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Knowledge Server")
    parser.add_argument("--serve", action="store_true", help="Run as MCP server (stdio)")
    parser.add_argument(
        "--test", type=str, help="Test a tool: search_knowledge, resolve_chunk, etc."
    )
    parser.add_argument("--query", type=str, help="Query for testing")
    parser.add_argument("--chunk-id", type=str, help="Chunk ID for resolve")
    args = parser.parse_args()

    if args.serve:
        run_server()
        return

    if args.test:
        print(f"\n{'=' * 60}")
        print("MCP KNOWLEDGE SERVER - Test Mode")
        print(f"{'=' * 60}\n")

        handler = TOOL_HANDLERS.get(args.test)
        if not handler:
            print(f"Unknown tool: {args.test}")
            print(f"Available: {', '.join(TOOL_HANDLERS.keys())}")
            sys.exit(1)

        params = {}
        if args.query:
            params["query"] = args.query
        if args.chunk_id:
            params["chunk_id"] = args.chunk_id

        result = handler(params)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n{'=' * 60}\n")
        return

    # Default: show available tools
    print(f"\n{'=' * 60}")
    print("MCP KNOWLEDGE SERVER")
    print(f"{'=' * 60}\n")
    print("Available tools:\n")
    for tool in TOOLS:
        print(f"  {tool['name']}")
        print(f"    {tool['description'][:80]}")
        print()
    print("Run with --serve to start MCP server")
    print("Run with --test <tool> --query <query> to test\n")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
