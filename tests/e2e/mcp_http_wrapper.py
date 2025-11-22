"""Authenticated MCP HTTP client wrapper for E2E tests.

This wrapper provides an authenticated httpx-based MCP client that:
- Sends Bearer token authentication headers
- Calls MCP tools via HTTP transport
- Handles FastMCP stateless HTTP protocol
- Provides same interface as FastMCP Client for test compatibility
"""

import httpx
from typing import Dict, Any, Optional


class AuthenticatedMcpClient:
    """MCP client wrapper that authenticates requests with Bearer token.
    
    This client wraps httpx to make authenticated MCP tool calls via HTTP,
    compatible with FastMCP's stateless_http mode deployed on Vercel.
    
    Attributes:
        base_url: Full MCP endpoint URL (e.g., "https://mcpdev.atoms.tech/api/mcp")
        http_client: Authenticated httpx.AsyncClient with Bearer token headers
        auth_token: JWT access token from Supabase authentication
    
    Usage:
        async with httpx.AsyncClient(...) as http_client:
            mcp = AuthenticatedMcpClient(
                base_url="https://mcpdev.atoms.tech/api/mcp",
                http_client=http_client,
                auth_token="<jwt>"
            )
            result = await mcp.call_tool("entity_tool", {...})
            assert result.get("success")
    """
    
    def __init__(
        self,
        base_url: str,
        http_client: httpx.AsyncClient,
        auth_token: str
    ):
        """Initialize authenticated MCP client.
        
        Args:
            base_url: Full MCP endpoint URL
            http_client: httpx AsyncClient with auth headers configured
            auth_token: JWT access token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.http_client = http_client
        self.auth_token = auth_token
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call MCP tool with authentication.
        
        Sends authenticated HTTP POST to MCP endpoint following FastMCP's
        stateless HTTP protocol.
        
        Args:
            tool_name: Name of MCP tool to call
            arguments: Tool arguments as dictionary
            **kwargs: Additional parameters (ignored, for API compatibility)
        
        Returns:
            Tool result dictionary with structure:
            {
                "success": bool,
                "data": {...},  # if success
                "error": str    # if failure
            }
        
        Raises:
            httpx.HTTPStatusError: If HTTP request fails
        """
        if arguments is None:
            arguments = {}
        
        # Construct MCP call payload following FastMCP protocol
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Send authenticated request
        try:
            response = await self.http_client.post(
                f"{self.base_url}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json",
                }
            )
            
            # Raise for HTTP errors (401, 403, 500, etc.)
            response.raise_for_status()
            
            # Parse JSON-RPC response
            result = response.json()
            
            # Handle JSON-RPC error responses
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"].get("message", "Unknown error")
                }
            
            # Extract tool result from JSON-RPC response
            if "result" in result:
                tool_result = result["result"]
                
                # If tool_result is already structured with success/data/error, return as-is
                if isinstance(tool_result, dict) and "success" in tool_result:
                    return tool_result
                
                # Otherwise, wrap in success structure
                return {
                    "success": True,
                    "data": tool_result
                }
            
            # Unexpected response format
            return {
                "success": False,
                "error": "Unexpected response format from MCP server"
            }
        
        except httpx.HTTPStatusError as e:
            # HTTP error (401, 403, 500, etc.)
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        
        except httpx.RequestError as e:
            # Network error (timeout, connection refused, etc.)
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        
        except Exception as e:
            # Unexpected error
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools.
        
        Returns:
            Dictionary with tools list
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        try:
            response = await self.http_client.post(
                f"{self.base_url}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json",
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "result" in result:
                return {"success": True, "tools": result["result"].get("tools", [])}
            
            return {"success": False, "error": "No tools list in response"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health.

        Returns:
            Health status dictionary
        """
        try:
            # Try health endpoint first
            base = self.base_url.rsplit('/api/mcp', 1)[0]
            response = await self.http_client.get(
                f"{base}/health",
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                }
            )

            if response.status_code == 200:
                return {"success": True, "status": "healthy"}

            return {"success": False, "error": f"Health check returned {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # Convenience methods for common operations

    async def entity_create(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an entity."""
        return await self.call_tool("entity_tool", {
            "entity_type": entity_type,
            "operation": "create",
            "data": data
        })

    async def entity_get(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Get an entity by ID."""
        return await self.call_tool("entity_tool", {
            "entity_type": entity_type,
            "operation": "get",
            "entity_id": entity_id
        })

    async def entity_list(self, entity_type: str, **kwargs) -> Dict[str, Any]:
        """List entities."""
        args = {
            "entity_type": entity_type,
            "operation": "list"
        }
        args.update(kwargs)
        return await self.call_tool("entity_tool", args)

    async def entity_update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an entity."""
        return await self.call_tool("entity_tool", {
            "entity_type": entity_type,
            "operation": "update",
            "entity_id": entity_id,
            "data": data
        })

    async def entity_delete(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Delete an entity."""
        return await self.call_tool("entity_tool", {
            "entity_type": entity_type,
            "operation": "delete",
            "entity_id": entity_id
        })

    async def workflow_execute(self, workflow_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a workflow."""
        return await self.call_tool("workflow_execute", {
            "workflow_name": workflow_name,
            "parameters": kwargs
        })

    async def query_search(self, search_term: str, entities: list, **kwargs) -> Dict[str, Any]:
        """Search for entities."""
        args = {
            "query_type": "search",
            "search_term": search_term,
            "entities": entities
        }
        args.update(kwargs)
        return await self.call_tool("query_tool", args)

    async def query_aggregate(self, entities: list, **kwargs) -> Dict[str, Any]:
        """Aggregate entities."""
        args = {
            "query_type": "aggregate",
            "entities": entities
        }
        args.update(kwargs)
        return await self.call_tool("query_tool", args)

    async def permission_check(self, operation: str, entity_type: str, **kwargs) -> Dict[str, Any]:
        """Check permissions."""
        args = {
            "operation": operation,
            "entity_type": entity_type
        }
        args.update(kwargs)
        return await self.call_tool("permission_tool", args)

    async def workspace_get_context(self, **kwargs) -> Dict[str, Any]:
        """Get workspace context."""
        return await self.call_tool("workspace_tool", {
            "operation": "get_context",
            **kwargs
        })

    async def workspace_switch_context(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Switch workspace context."""
        return await self.call_tool("workspace_tool", {
            "operation": "switch_context",
            "entity_type": entity_type,
            "entity_id": entity_id
        })

    async def workspace_list(self, **kwargs) -> Dict[str, Any]:
        """List workspaces."""
        return await self.call_tool("workspace_tool", {
            "operation": "list",
            **kwargs
        })
