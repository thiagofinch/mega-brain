#!/usr/bin/env python3
"""
MCP Server for MercadoLivre API Integration

Implements Model Context Protocol (JSON-RPC 2.0 over stdio)

Provides real-time access to:
- Commission rates by category
- Shipping costs
- Advertising policies

Uses official mcp SDK: https://github.com/modelcontextprotocol/python-sdk

Author: JARVIS
Version: 2.0.0 (MCP SDK compliant)
"""

import os
import json
import asyncio
import requests
from typing import Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class MercadoLivreMCPClient:
    """MercadoLivre API Client for MCP Server"""

    def __init__(self):
        self.client_id = os.getenv("MERCADOLIVRE_CLIENT_ID", "")
        self.client_secret = os.getenv("MERCADOLIVRE_CLIENT_SECRET", "")
        self.redirect_url = os.getenv("MERCADOLIVRE_REDIRECT_URL", "")
        self.access_token = os.getenv("MERCADOLIVRE_ACCESS_TOKEN", "")

        self.base_url = "https://api.mercadolibre.com"
        self.token_expires_at: Optional[datetime] = None
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JARVIS-MercadoLivre-MCP/2.0.0"
        })

    def _is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        return datetime.now() < self.token_expires_at

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Make HTTP request with retry logic and timeout

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base_url)
            **kwargs: Additional requests parameters

        Returns:
            JSON response or error dict
        """
        url = f"{self.base_url}{endpoint}"

        # Add auth header if token available
        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=10,
                    headers=headers,
                    **kwargs
                )

                # Handle rate limiting with backoff
                if response.status_code in [429, 503]:
                    if attempt < max_retries - 1:
                        asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                return {"error": "Request timeout (10s exceeded)", "status": "timeout"}
            except requests.exceptions.ConnectionError as e:
                return {"error": f"Connection error: {str(e)}", "status": "connection_error"}
            except requests.exceptions.HTTPError as e:
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": response.status_code
                }
            except Exception as e:
                return {"error": str(e), "status": "unknown_error"}

        return {"error": "Max retries exceeded", "status": "max_retries"}

    def get_categories(self) -> dict:
        """
        Get all MercadoLivre categories (public endpoint)

        Returns:
            Dict with category IDs and names
        """
        result = self._make_request("GET", "/sites/MLB/categories")

        if isinstance(result, list):
            # Convert list response to dict with summary
            return {
                "status": "success",
                "total_categories": len(result),
                "categories": result[:10],  # Return first 10 for preview
                "note": f"Showing 10 of {len(result)} total categories",
                "timestamp": datetime.now().isoformat()
            }

        return result

    def get_commissions(self, category_id: str) -> dict:
        """
        Get commission rates for a specific category

        Args:
            category_id: MercadoLivre category ID (e.g., "MLB1459")

        Returns:
            Commission rate and details
        """
        if not category_id:
            return {"error": "category_id is required", "status": "invalid_input"}

        result = self._make_request("GET", f"/categories/{category_id}")

        if "error" in result:
            return result

        # Extract relevant commission info
        commission_rate = result.get("commission", {})

        return {
            "status": "success",
            "category_id": category_id,
            "category_name": result.get("name", ""),
            "commission": commission_rate,
            "seller_fees": result.get("seller_fees", {}),
            "timestamp": datetime.now().isoformat()
        }

    def get_shipping_info(self, category_id: str) -> dict:
        """
        Get shipping information for a category

        Args:
            category_id: MercadoLivre category ID

        Returns:
            Shipping rules and costs
        """
        if not category_id:
            return {"error": "category_id is required", "status": "invalid_input"}

        result = self._make_request("GET", f"/categories/{category_id}")

        if "error" in result:
            return result

        return {
            "status": "success",
            "category_id": category_id,
            "category_name": result.get("name", ""),
            "shipping_info": result.get("shipping_info", {}),
            "timestamp": datetime.now().isoformat()
        }

    def get_listing_types(self, category_id: str = "MLB1459") -> dict:
        """
        Get available listing types for a category

        Args:
            category_id: MercadoLivre category ID

        Returns:
            Listing types and features
        """
        result = self._make_request("GET", f"/categories/{category_id}")

        if "error" in result:
            return result

        return {
            "status": "success",
            "category_id": category_id,
            "category_name": result.get("name", ""),
            "listing_types": result.get("listing_types", []),
            "settings": result.get("settings", {}),
            "timestamp": datetime.now().isoformat()
        }

    def get_category_attributes(self, category_id: str) -> dict:
        """
        Get required and optional attributes for a category (ficha técnica)

        Args:
            category_id: MercadoLivre category ID (e.g., "MLB1459")

        Returns:
            Required fields, optional fields, and attribute types
        """
        if not category_id:
            return {"error": "category_id is required", "status": "invalid_input"}

        result = self._make_request("GET", f"/categories/{category_id}/attributes")

        if "error" in result:
            return result

        # Filter to essential info
        return {
            "status": "success",
            "category_id": category_id,
            "attributes": result.get("attributes", []) if isinstance(result, dict) else result,
            "timestamp": datetime.now().isoformat()
        }

    def get_item_health(self, item_id: str) -> dict:
        """
        Get health score and issues for a specific listing

        Args:
            item_id: MercadoLivre item ID

        Returns:
            Health score (0-100) and list of issues/recommendations
        """
        if not item_id:
            return {"error": "item_id is required", "status": "invalid_input"}

        result = self._make_request("GET", f"/items/{item_id}/health")

        if "error" in result:
            return result

        return {
            "status": "success",
            "item_id": item_id,
            "health_score": result.get("health", result.get("score", 0)),
            "issues": result.get("issues", []),
            "recommendations": result.get("recommendations", []),
            "timestamp": datetime.now().isoformat()
        }

    def get_item_details(self, item_id: str) -> dict:
        """
        Get complete details of a listing

        Args:
            item_id: MercadoLivre item ID

        Returns:
            Full listing data including title, description, images, attributes
        """
        if not item_id:
            return {"error": "item_id is required", "status": "invalid_input"}

        result = self._make_request("GET", f"/items/{item_id}")

        if "error" in result:
            return result

        return {
            "status": "success",
            "item_id": item_id,
            "title": result.get("title", ""),
            "price": result.get("price", 0),
            "category_id": result.get("category_id", ""),
            "description": result.get("description", {}).get("plain_text", "")[:200],  # Preview
            "pictures_count": len(result.get("pictures", [])),
            "attributes": result.get("attributes", []),
            "status": result.get("status", ""),
            "timestamp": datetime.now().isoformat()
        }

    def get_seller_items(self, user_id: str) -> dict:
        """
        Get list of active items for a seller

        Args:
            user_id: MercadoLivre user ID

        Returns:
            List of item IDs and total count
        """
        if not user_id:
            return {"error": "user_id is required", "status": "invalid_input"}

        if not self.access_token:
            return {"error": "Authentication required for seller items", "status": "unauthorized"}

        result = self._make_request("GET", f"/users/{user_id}/items/search")

        if "error" in result:
            return result

        return {
            "status": "success",
            "user_id": user_id,
            "total_items": len(result.get("results", [])) if isinstance(result, dict) else 0,
            "items": result.get("results", [])[:20],  # First 20 items
            "timestamp": datetime.now().isoformat()
        }

    def search_competitive_items(self, query: str, category_id: str = None) -> dict:
        """
        Search MercadoLivre and return top competitive listings

        Args:
            query: Search query
            category_id: Optional category filter

        Returns:
            Top 10 listings with title, price, sold quantity, reviews
        """
        if not query:
            return {"error": "query is required", "status": "invalid_input"}

        endpoint = f"/sites/MLB/search?q={query}"
        if category_id:
            endpoint += f"&category={category_id}"
        endpoint += "&sort=relevance&limit=10"

        result = self._make_request("GET", endpoint)

        if "error" in result:
            return result

        results = []
        for item in result.get("results", [])[:10]:
            results.append({
                "title": item.get("title", ""),
                "price": item.get("price", 0),
                "id": item.get("id", ""),
                "seller": item.get("seller", {}).get("nickname", ""),
            })

        return {
            "status": "success",
            "query": query,
            "category_id": category_id,
            "total_found": result.get("paging", {}).get("total", 0),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }


# MCP Server initialization
server = Server("mercadolivre-mcp")
client = MercadoLivreMCPClient()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available MCP tools"""
    return [
        types.Tool(
            name="mercadolivre_get_categories",
            description="Get all MercadoLivre categories (public endpoint, no auth required)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="mercadolivre_get_commissions",
            description="Get commission rates and seller fees for a specific category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_id": {
                        "type": "string",
                        "description": "MercadoLivre category ID (e.g., MLB1459 for Clothing)"
                    }
                },
                "required": ["category_id"]
            }
        ),
        types.Tool(
            name="mercadolivre_get_shipping_info",
            description="Get shipping rules and options for a category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_id": {
                        "type": "string",
                        "description": "MercadoLivre category ID"
                    }
                },
                "required": ["category_id"]
            }
        ),
        types.Tool(
            name="mercadolivre_get_listing_types",
            description="Get available listing types and features for a category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_id": {
                        "type": "string",
                        "description": "MercadoLivre category ID",
                        "default": "MLB1459"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="mercadolivre_get_category_attributes",
            description="Get required and optional attributes (ficha técnica) for a category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_id": {
                        "type": "string",
                        "description": "MercadoLivre category ID (e.g., MLB1459)"
                    }
                },
                "required": ["category_id"]
            }
        ),
        types.Tool(
            name="mercadolivre_get_item_health",
            description="Get listing health score and issues for a specific item",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "MercadoLivre item ID (requires auth)"
                    }
                },
                "required": ["item_id"]
            }
        ),
        types.Tool(
            name="mercadolivre_get_item_details",
            description="Get complete details of a listing (title, description, images, attributes)",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "MercadoLivre item ID"
                    }
                },
                "required": ["item_id"]
            }
        ),
        types.Tool(
            name="mercadolivre_get_seller_items",
            description="Get list of active items for a seller (requires auth)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "MercadoLivre user ID"
                    }
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="mercadolivre_search_competitive_items",
            description="Search MercadoLivre and get top competitive listings for ranking analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'iphone 13')"
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Optional category filter"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    Handle MCP tool calls

    Implements JSON-RPC 2.0 protocol via stdio

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent with result
    """
    try:
        result = None

        if name == "mercadolivre_get_categories":
            result = client.get_categories()

        elif name == "mercadolivre_get_commissions":
            category_id = arguments.get("category_id", "")
            result = client.get_commissions(category_id)

        elif name == "mercadolivre_get_shipping_info":
            category_id = arguments.get("category_id", "")
            result = client.get_shipping_info(category_id)

        elif name == "mercadolivre_get_listing_types":
            category_id = arguments.get("category_id", "MLB1459")
            result = client.get_listing_types(category_id)

        elif name == "mercadolivre_get_category_attributes":
            category_id = arguments.get("category_id", "")
            result = client.get_category_attributes(category_id)

        elif name == "mercadolivre_get_item_health":
            item_id = arguments.get("item_id", "")
            result = client.get_item_health(item_id)

        elif name == "mercadolivre_get_item_details":
            item_id = arguments.get("item_id", "")
            result = client.get_item_details(item_id)

        elif name == "mercadolivre_get_seller_items":
            user_id = arguments.get("user_id", "")
            result = client.get_seller_items(user_id)

        elif name == "mercadolivre_search_competitive_items":
            query = arguments.get("query", "")
            category_id = arguments.get("category_id", None)
            result = client.search_competitive_items(query, category_id)

        else:
            result = {"error": f"Unknown tool: {name}"}

        # Return as JSON string wrapped in TextContent
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]

    except Exception as e:
        error_response = {
            "error": str(e),
            "status": "tool_execution_error"
        }
        return [types.TextContent(
            type="text",
            text=json.dumps(error_response, indent=2)
        )]


async def main():
    """
    Run MCP Server with stdio transport

    This function starts the server and waits for incoming MCP calls
    from Claude Code or other MCP clients via stdin/stdout.
    """
    print("🚀 MercadoLivre MCP Server v2.0.0 starting...", file=__import__("sys").stderr)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
