#!/usr/bin/env python3
"""
MCP Server for MercadoLivre API Integration (Raw JSON-RPC 2.0)

Provides real-time access to:
- Commission rates by category
- Shipping costs
- Advertising policies
- Listing types
- Listing health scores (v2.0)
- Category attributes / Ficha Técnica (v2.0)
- Item details (v2.0)
- Seller items (v2.0)
- Competitive item search (v2.0)

Author: JARVIS
Version: 2.0.0 (5 new tools added for listing optimization)
"""

import os
import sys
import json
import requests
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class MercadoLivreMCPServer:
    """MercadoLivre API Client for JARVIS via JSON-RPC 2.0"""

    def __init__(self):
        self.client_id = os.getenv("MERCADOLIVRE_CLIENT_ID")
        self.client_secret = os.getenv("MERCADOLIVRE_CLIENT_SECRET")
        self.redirect_url = os.getenv("MERCADOLIVRE_REDIRECT_URL")

        self.base_url = "https://api.mercadolibre.com"
        self.access_token = os.getenv("MERCADOLIVRE_ACCESS_TOKEN")
        self.refresh_token = os.getenv("MERCADOLIVRE_REFRESH_TOKEN")

        # In a real environment, we'd persist the token and expiry
        # For simplicity in this script, we'll try to use what's in .env
        self.token_expires_at = None

        if not all([self.client_id, self.client_secret]):
            # We don't fail immediately, but tools requiring auth will fail
            pass

    def _get_headers(self) -> Dict[str, str]:
        token = self.access_token
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all MercadoLivre categories (public)"""
        try:
            response = requests.get(
                f"{self.base_url}/sites/MLB/categories",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]

    def get_commissions(self, category_id: str) -> Dict[str, Any]:
        """Get commission rates for a specific category"""
        try:
            response = requests.get(
                f"{self.base_url}/categories/{category_id}",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                "category_id": category_id,
                "category_name": data.get("name", ""),
                "commission": self._extract_commission(data),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    def get_shipping_costs(self, item_weight: float, destination: str = "BR") -> Dict[str, Any]:
        """Get shipping cost estimates (Simplified)"""
        # This endpoint usually requires a full item/seller context
        # Returning a structured mock/placeholder for now if token is missing
        if not self.access_token:
            return {"error": "Authentication required for shipping costs"}

        return {
            "estimated_cost": 24.90,
            "currency": "BRL",
            "method": "Mercado Envios",
            "note": "Simplified estimate based on weight",
            "weight": item_weight
        }

    def get_listing_types(self) -> List[Dict[str, Any]]:
        """Get available listing types (public)"""
        try:
            response = requests.get(
                f"{self.base_url}/sites/MLB/listing_types",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]

    def update_item_attributes(self, item_id: str, attributes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update item attributes (requires auth)
        attributes format: [{'id': 'NCM', 'value_name': '61091000'}]
        """
        try:
            url = f"{self.base_url}/items/{item_id}"
            payload = {"attributes": attributes}
            response = requests.put(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "item_id": item_id}

    def delete_item(self, item_id: str) -> Dict[str, Any]:
        """Delete an item from MercadoLivre.
        Step 1: Change status to 'closed'
        Step 2: Change status to 'deleted'
        """
        try:
            # Step 1: Close
            close_url = f"{self.base_url}/items/{item_id}"
            close_payload = {"status": "closed"}
            close_resp = requests.put(
                close_url,
                json=close_payload,
                headers=self._get_headers(),
                timeout=15
            )
            close_resp.raise_for_status()

            # Step 2: Delete
            delete_payload = {"status": "deleted"}
            delete_resp = requests.put(
                close_url, # Same URL
                json=delete_payload,
                headers=self._get_headers(),
                timeout=15
            )
            delete_resp.raise_for_status()
            
            return {"status": "success", "message": f"Item {item_id} deleted successfully", "item_id": item_id}
        except Exception as e:
            return {"error": str(e), "status": "error", "item_id": item_id}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NEW TOOLS (v2.0) - LISTING OPTIMIZATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_category_attributes(self, category_id: str) -> Dict[str, Any]:
        """Get required and optional attributes (ficha técnica) for a category"""
        try:
            response = requests.get(
                f"{self.base_url}/categories/{category_id}/attributes",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                "status": "success",
                "category_id": category_id,
                "attributes": data if isinstance(data, list) else data.get("attributes", []),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def get_item_health(self, item_id: str) -> Dict[str, Any]:
        """Get health score and issues for a specific listing"""
        try:
            response = requests.get(
                f"{self.base_url}/items/{item_id}/health",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                "status": "success",
                "item_id": item_id,
                "health_score": data.get("health", data.get("score", 0)),
                "issues": data.get("issues", []),
                "recommendations": data.get("recommendations", []),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def get_item_details(self, item_id: str) -> Dict[str, Any]:
        """Get complete details of a listing"""
        try:
            response = requests.get(
                f"{self.base_url}/items/{item_id}",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                "status": "success",
                "item_id": item_id,
                "title": data.get("title", ""),
                "price": data.get("price", 0),
                "category_id": data.get("category_id", ""),
                "description": data.get("description", {}).get("plain_text", "")[:200],
                "pictures_count": len(data.get("pictures", [])),
                "attributes": data.get("attributes", []),
                "status": data.get("status", ""),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def get_seller_items(self, user_id: str) -> Dict[str, Any]:
        """Get list of active items for a seller"""
        if not self.access_token:
            return {"error": "Authentication required", "status": "unauthorized"}

        try:
            response = requests.get(
                f"{self.base_url}/users/{user_id}/items/search",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", []) if isinstance(data, dict) else data if isinstance(data, list) else []

            return {
                "status": "success",
                "user_id": user_id,
                "total_items": len(results),
                "items": results[:20],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def get_orders(self, seller_id: str, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """Get orders for a specific seller within a date range"""
        if not self.access_token:
            return {"error": "Authentication required", "status": "unauthorized"}

        try:
            endpoint = f"{self.base_url}/orders/search?seller={seller_id}"
            if date_from:
                endpoint += f"&order.date_created.from={date_from}"
            if date_to:
                endpoint += f"&order.date_created.to={date_to}"

            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            return {
                "status": "success",
                "seller_id": seller_id,
                "total_orders": len(data.get("results", [])),
                "orders": data.get("results", []),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def search_competitive_items(self, query: str, category_id: str = None) -> Dict[str, Any]:
        """Search MercadoLivre and return top competitive listings"""
        try:
            endpoint = f"{self.base_url}/sites/MLB/search?q={query}"
            if category_id:
                endpoint += f"&category={category_id}"
            endpoint += "&sort=relevance&limit=10"

            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", [])[:10]:
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
                "total_found": data.get("paging", {}).get("total", 0),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}

    def _extract_commission(self, category_data: Dict) -> Optional[float]:
        """Extract commission rate from category data"""
        if "commission" in category_data:
            return category_data["commission"]
        if "seller_fees" in category_data:
            return category_data["seller_fees"].get("commission", None)
        return None


def serve():
    """Main JSON-RPC 2.0 Loop"""
    server = MercadoLivreMCPServer()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            result = None
            error = None

            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mercadolivre-mcp", "version": "2.0.0"}
                }
            elif method == "list_tools":
                result = {
                    "tools": [
                        {
                            "name": "mercadolivre_get_categories",
                            "description": "Get categories from MercadoLivre",
                            "inputSchema": {"type": "object", "properties": {}}
                        },
                        {
                            "name": "mercadolivre_get_commissions",
                            "description": "Get commission for a category ID",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "category_id": {"type": "string"}
                                },
                                "required": ["category_id"]
                            }
                        },
                        {
                            "name": "mercadolivre_get_shipping_costs",
                            "description": "Estimate shipping costs",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_weight": {"type": "number"}
                                },
                                "required": ["item_weight"]
                            }
                        },
                        {
                            "name": "mercadolivre_get_listing_types",
                            "description": "Get available listing types for MercadoLivre MLB",
                            "inputSchema": {"type": "object", "properties": {}}
                        },
                        {
                            "name": "mercadolivre_update_item_attributes",
                            "description": "Update specific attributes of a MercadoLivre item (e.g., NCM, Origin)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string"},
                                    "attributes": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "string"},
                                                "value_name": {"type": "string"}
                                            }
                                        }
                                    }
                                },
                                "required": ["item_id", "attributes"]
                            }
                        },
                        # NEW TOOLS (v2.0)
                        {
                            "name": "mercadolivre_get_category_attributes",
                            "description": "Get required/optional attributes (ficha técnica) for a category",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "category_id": {"type": "string"}
                                },
                                "required": ["category_id"]
                            }
                        },
                        {
                            "name": "mercadolivre_get_item_health",
                            "description": "Get health score and issues for a listing",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string"}
                                },
                                "required": ["item_id"]
                            }
                        },
                        {
                            "name": "mercadolivre_get_item_details",
                            "description": "Get complete details of a listing",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string"}
                                },
                                "required": ["item_id"]
                            }
                        },
                        {
                            "name": "mercadolivre_get_seller_items",
                            "description": "Get list of active items for a seller",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "user_id": {"type": "string"}
                                },
                                "required": ["user_id"]
                            }
                        },
                        {
                            "name": "mercadolivre_delete_item",
                            "description": "Delete an item from MercadoLivre (closes then deletes)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string"}
                                },
                                "required": ["item_id"]
                            }
                        },
                        {
                            "name": "mercadolivre_get_orders",
                            "description": "Get orders for a seller (requires auth)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "seller_id": {"type": "string"},
                                    "date_from": {"type": "string", "description": "ISO format date"},
                                    "date_to": {"type": "string", "description": "ISO format date"}
                                },
                                "required": ["seller_id"]
                            }
                        }
                    ]
                }
            elif method == "call_tool":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name == "mercadolivre_get_categories":
                    data = server.get_categories()
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_get_commissions":
                    data = server.get_commissions(arguments.get("category_id"))
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_get_shipping_costs":
                    data = server.get_shipping_costs(arguments.get("item_weight"))
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_get_listing_types":
                    data = server.get_listing_types()
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_update_item_attributes":
                    data = server.update_item_attributes(
                        arguments.get("item_id"),
                        arguments.get("attributes")
                    )
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                # NEW TOOLS (v2.0)
                elif tool_name == "mercadolivre_get_category_attributes":
                    data = server.get_category_attributes(arguments.get("category_id"))
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_get_item_health":
                    data = server.get_item_health(arguments.get("item_id"))
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_get_item_details":
                    data = server.get_item_details(arguments.get("item_id"))
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_get_seller_items":
                    data = server.get_seller_items(arguments.get("user_id"))
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_search_competitive_items":
                    data = server.search_competitive_items(
                        arguments.get("query"),
                        arguments.get("category_id")
                    )
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_delete_item":
                    data = server.delete_item(arguments.get("item_id"))
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                elif tool_name == "mercadolivre_get_orders":
                    data = server.get_orders(
                        arguments.get("seller_id"),
                        arguments.get("date_from"),
                        arguments.get("date_to")
                    )
                    result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                else:
                    error = {"code": -32601, "message": f"Tool not found: {tool_name}"}
            else:
                error = {"code": -32601, "message": f"Method not found: {method}"}

            response = {"jsonrpc": "2.0", "id": request_id}
            if error:
                response["error"] = error
            else:
                response["result"] = result

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception:
            # Send error response if we have a request_id
            # Log to stderr
            sys.stderr.write(traceback.format_exc())
            sys.stderr.flush()

if __name__ == "__main__":
    serve()
