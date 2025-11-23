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
    
    def _parse_mcp_response(self, response_text: str) -> Dict[str, Any] | None:
        """Parse MCP HTTP response in SSE or plain JSON-RPC format.
        
        FastMCP returns responses as Server-Sent Events (SSE), where the JSON-RPC
        message is wrapped in SSE event format:
            event: message
            data: {"jsonrpc":"2.0",...}
        
        This method extracts and parses the JSON-RPC message from either format.
        
        Args:
            response_text: Raw response body from HTTP request
        
        Returns:
            Parsed JSON-RPC message dict, or None if parsing fails
        """
        if not response_text or response_text.strip() == "":
            return None
        
        import json
        
        # Try SSE format first
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('data: '):
                try:
                    return json.loads(line[6:])  # Skip 'data: ' prefix
                except json.JSONDecodeError:
                    continue
        
        # Fall back to plain JSON-RPC
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return None
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call MCP tool with authentication and auto-token-refresh on 401.
        
        Sends authenticated HTTP POST to MCP endpoint following FastMCP's
        stateless HTTP protocol. If a 401 (authentication failed) error occurs,
        automatically refreshes the token and retries once.
        
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
            httpx.HTTPStatusError: If HTTP request fails after retry
        """
        if arguments is None:
            arguments = {}
        
        # Try to call tool, with automatic token refresh on 401
        result = await self._call_tool_internal(tool_name, arguments)
        
        # If we got a 401 error, try to refresh token and retry
        if (isinstance(result, dict) and 
            not result.get("success") and 
            "401" in result.get("error", "")):
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔄 Token expired (401), attempting refresh...")
            
            # Attempt token refresh
            fresh_token = await self._refresh_token()
            if fresh_token:
                logger.info("✅ Token refreshed, retrying call_tool...")
                self.auth_token = fresh_token
                # Update header in http_client
                self.http_client.headers.update({
                    "Authorization": f"Bearer {fresh_token}"
                })
                # Retry with fresh token
                result = await self._call_tool_internal(tool_name, arguments)
        
        return result
    
    async def _call_tool_internal(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Internal tool call without retry logic.
        
        Args:
            tool_name: Name of MCP tool to call
            arguments: Tool arguments as dictionary
        
        Returns:
            Tool result dictionary
        """
        
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
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"📤 Calling tool: {tool_name} at {self.base_url} with token (first 20 chars: {self.auth_token[:20]}...)")
            
            response = await self.http_client.post(
                f"{self.base_url}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                }
            )
            
            logger.debug(f"📥 Response status: {response.status_code}")
            
            # Raise for HTTP errors (401, 403, 500, etc.)
            response.raise_for_status()
            
            # Parse response - could be SSE or plain JSON-RPC
            result = self._parse_mcp_response(response.text)
            if not result:
                return {
                    "success": False,
                    "error": "Failed to parse MCP server response"
                }
            
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
                    "Accept": "application/json, text/event-stream",
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
    
    async def _refresh_token(self) -> Optional[str]:
        """Refresh authentication token when it expires (on 401 error).
        
        Uses the smart token manager to get a fresh token, which will:
        1. Check cache for valid token
        2. If cached token expiring soon, refresh proactively
        3. Otherwise authenticate fresh
        
        Returns:
            Fresh JWT token or None if refresh fails
        """
        try:
            from tests.utils.token_manager import get_fresh_token
            
            import logging
            logger = logging.getLogger(__name__)
            
            # Get fresh token from token manager
            # This uses smart logic: cache if valid, refresh if expiring soon, 
            # or authenticate fresh if needed
            fresh_token = await get_fresh_token()
            
            if fresh_token:
                logger.debug(f"✅ Token refreshed (first 20 chars: {fresh_token[:20]}...)")
                return fresh_token
            else:
                logger.error("❌ Failed to refresh token - get_fresh_token returned None")
                return None
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Token refresh failed: {e}")
            return None
