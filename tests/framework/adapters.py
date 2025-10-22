"""
Atoms MCP Client Adapter

Extends pheno-sdk's BaseClientAdapter with Atoms-specific result processing
and error handling.

This is the slimmed-down version (~80 lines vs ~200 before) that leverages
shared infrastructure from pheno-sdk.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

import httpx
from mcp_qa.core.base import BaseClientAdapter

from utils.logging_setup import get_logger

logger = get_logger("atoms.adapter")


class AtomsMCPClientAdapter(BaseClientAdapter):
    """
    Atoms-specific MCP client adapter.

    Extends BaseClientAdapter with Atoms-specific:
    - Result processing (JSON parsing, success detection)
    - Error handling (DB permissions, verbose failures)
    - Helper methods (workspace operations, etc.)
    - Direct HTTP calls using captured OAuth token (no MCP client connection needed)
    """

    # Logging thresholds
    SLOW_CALL_THRESHOLD = 5.0  # seconds - log if call takes longer than this
    HTTP_TIMEOUT = 30.0  # seconds - timeout for individual HTTP calls

    def __init__(
        self,
        client: Any = None,
        debug: bool = False,
        verbose_on_fail: bool = True,
        mcp_endpoint: str | None = None,
        access_token: str | None = None,
        use_direct_http: bool = True
    ):
        """
        Initialize Atoms adapter.

        Args:
            client: FastMCP Client instance (required - kept alive for auth)
            debug: Enable debug logging
            verbose_on_fail: Show detailed logs on failure
            mcp_endpoint: MCP endpoint URL for direct HTTP calls
            access_token: OAuth access token for direct HTTP calls
            use_direct_http: Use direct HTTP JSON-RPC 2.0 instead of MCP client protocol (default: True)
                Note: Falls back to MCP client protocol automatically if HTTP fails.
                Direct HTTP is faster and uses proper JSON-RPC 2.0 over HTTP POST.
        """
        super().__init__(client, verbose_on_fail=verbose_on_fail)
        self.debug = debug
        self._url = getattr(client, "_url", "unknown") if client else mcp_endpoint
        self.endpoint = self._url  # For metadata compatibility

        # Direct HTTP support
        self.use_direct_http = use_direct_http
        self.mcp_endpoint = mcp_endpoint
        self.access_token = access_token
        self._http_client: httpx.AsyncClient | None = None
        self._auth_handler: Any | None = None  # Extracted from MCP client transport

    async def call_tool(self, name: str, params: dict[str, Any]) -> Any:
        """
        Call a tool using direct HTTP JSON-RPC 2.0 or MCP client protocol.

        Default (use_direct_http=True):
        - Makes direct HTTP POST to MCP endpoint using JSON-RPC 2.0
        - Faster than SSE-based MCP client protocol
        - Proper JSON-RPC 2.0 format with unique request IDs
        - Extracts auth from MCP client's transport or uses Bearer token
        - Falls back to MCP client protocol automatically on failure

        Alternative (use_direct_http=False):
        - Uses MCP client protocol (SSE) through authenticated client
        - Reuses existing OAuth session from client
        - Compatible with servers that don't support JSON-RPC HTTP
        - Client connection stays alive for reuse

        Args:
            name: Tool name
            params: Tool parameters

        Returns:
            Processed result from tool call

        Raises:
            asyncio.TimeoutError: If call exceeds HTTP_TIMEOUT
            Exception: If tool call fails
        """
        self._call_count += 1
        call_start = datetime.now()

        # Compact params for logging (hide sensitive data, truncate large values)
        params_preview = self._format_params_for_log(params)

        # Log call initiation
        if self.debug or self.verbose_on_fail:
            method = "HTTP" if self.use_direct_http else "MCP"
            logger.info(f"→ Calling {name} via {method} with params: {params_preview}")

        try:
            # Choose call method
            if self.use_direct_http:
                result = await self._call_tool_http(name, params)
            else:
                result = await self._call_tool_mcp(name, params)

            # Process result
            logger.debug(f"→ [BEFORE PROCESSING] Processing result from {name}")
            processed_result = self._process_result(result, name, params)
            logger.debug(f"← [AFTER PROCESSING] Result processed for {name}")

            # Log success with timing
            duration = (datetime.now() - call_start).total_seconds()
            success = processed_result.get("success", True) if isinstance(processed_result, dict) else True

            # Always log if call was slow or if in debug/verbose mode
            if duration >= self.SLOW_CALL_THRESHOLD or self.debug or self.verbose_on_fail:
                status_emoji = "✓" if success else "✗"
                logger.info(
                    f"{status_emoji} Call to {name} completed in {duration:.2f}s "
                    f"(success={success})"
                )

            # Track successful call
            self._call_history.append({
                "tool": name,
                "params": params,
                "success": True,
                "duration": duration,
                "timestamp": call_start.isoformat()
            })

            return processed_result

        except Exception as e:
            self._error_count += 1
            self._last_error = e

            duration = (datetime.now() - call_start).total_seconds()

            # Track failed call
            self._call_history.append({
                "tool": name,
                "params": params,
                "success": False,
                "error": str(e),
                "duration": duration,
                "timestamp": call_start.isoformat()
            })

            # Log where the failure occurred
            error_type = type(e).__name__
            logger.error(
                f"❌ [ERROR] {name} failed after {duration:.2f}s\n"
                f"   Error type: {error_type}\n"
                f"   Error: {str(e)[:200]}\n"
                f"   Params: {params_preview}"
            )

            if self.verbose_on_fail:
                self._log_error(e, name, params)

            raise

    def _extract_auth_from_client(self) -> Any | None:
        """
        Extract the auth handler from the MCP client's transport.

        The FastMCP Client uses an httpx Auth handler internally for OAuth.
        We extract this to use for our direct HTTP calls.

        Returns:
            httpx.Auth handler or None if not available
        """
        if not self.client:
            return None

        try:
            # FastMCP Client stores transport in .transport attribute
            transport = getattr(self.client, "transport", None)
            if not transport:
                logger.debug("No transport found on MCP client")
                return None

            # HTTP transport stores auth in .auth attribute
            auth = getattr(transport, "auth", None)
            if auth:
                logger.debug(f"Extracted auth handler from transport: {type(auth).__name__}")
                return auth
            logger.debug("No auth handler found on transport")
            return None

        except Exception as e:
            logger.warning(f"Failed to extract auth from MCP client: {e}")
            return None

    async def _call_tool_http(self, name: str, params: dict[str, Any]) -> Any:
        """
        Make direct HTTP call to MCP tool endpoint using proper MCP HTTP protocol.

        Uses JSON-RPC 2.0 format (the official MCP HTTP protocol) to call tools.
        Extracts authentication from the MCP client's transport to ensure
        we have the same session/cookies/tokens.

        Args:
            name: Tool name
            params: Tool parameters

        Returns:
            Raw response (will be processed by _process_result)

        Raises:
            ValueError: If client or endpoint not configured
            httpx.HTTPStatusError: If HTTP request fails
        """
        if not self.client:
            raise ValueError(
                "MCP client required for direct HTTP calls. "
                "Provide a client instance or set use_direct_http=False."
            )

        # Extract endpoint from client if not provided
        if not self.mcp_endpoint:
            self.mcp_endpoint = getattr(self.client.transport, "url", None)
            if not self.mcp_endpoint:
                raise ValueError("Could not determine MCP endpoint from client")

        logger.debug(f"→ [BEFORE HTTP] Sending direct HTTP request for {name}")

        # Extract auth from MCP client on first use
        if self._auth_handler is None and self._http_client is None:
            self._auth_handler = self._extract_auth_from_client()

        # Create HTTP client if needed, using MCP client's auth
        if self._http_client is None:
            client_kwargs = {
                "timeout": httpx.Timeout(connect=self.HTTP_TIMEOUT, read=self.HTTP_TIMEOUT, write=self.HTTP_TIMEOUT, pool=self.HTTP_TIMEOUT)
            }

            # Use auth from MCP client if available
            if self._auth_handler:
                client_kwargs["auth"] = self._auth_handler
                logger.debug("Using auth handler from MCP client")
            # Fallback to access token if provided
            elif self.access_token:
                # Don't set headers here - set them per-request below
                pass
            else:
                logger.warning("No authentication available - requests may fail")

            self._http_client = httpx.AsyncClient(**client_kwargs)

        try:
            # Make JSON-RPC 2.0 call to MCP endpoint
            # Use unique ID for each request (required by JSON-RPC 2.0)
            self._call_count_for_id = getattr(self, "_call_count_for_id", 0) + 1

            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": params
                },
                "id": self._call_count_for_id
            }

            # Build headers for this specific request
            request_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"  # MCP requires both
            }

            # Add Bearer token if we have one (and no auth handler)
            if self.access_token and not self._auth_handler:
                request_headers["Authorization"] = f"Bearer {self.access_token}"
                logger.debug("Using Bearer token authentication")

            logger.debug(f"→ [HTTP REQUEST] POST {self.mcp_endpoint}")
            logger.debug(f"   Headers: {request_headers}")
            logger.debug(f"   Payload: {json.dumps(payload)}")

            response = await asyncio.wait_for(
                self._http_client.post(
                    self.mcp_endpoint,
                    json=payload,
                    headers=request_headers
                ),
                timeout=self.HTTP_TIMEOUT
            )

            logger.debug(f"← [AFTER HTTP] Received response from {name} (status: {response.status_code})")

            # Log response details for debugging
            if response.status_code != 200:
                logger.debug(f"   Response headers: {dict(response.headers)}")
                logger.debug(f"   Response body: {response.text[:500]}")

            response.raise_for_status()

            # Parse JSON-RPC response
            rpc_response = response.json()

            # Check for JSON-RPC error
            if "error" in rpc_response:
                error_data = rpc_response["error"]
                error_msg = error_data if isinstance(error_data, str) else json.dumps(error_data)
                raise Exception(f"JSON-RPC Error: {error_msg}")

            # Extract result - simulate FastMCP result structure
            result_data = rpc_response.get("result", {})

            # Create a simple object that mimics FastMCP result structure
            class FakeMCPResult:
                def __init__(self, data):
                    self.content = [type("obj", (object,), {"text": json.dumps(data)})]

            return FakeMCPResult(result_data)

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning(
                f"⚠️  [HTTP FAILED] Direct HTTP call to {name} failed: {e}\n"
                f"   Status: {getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'}\n"
                f"   Falling back to MCP client protocol..."
            )
            # Fall back to MCP client protocol
            return await self._call_tool_mcp(name, params)

        except TimeoutError:
            logger.error(
                f"⏱️  [TIMEOUT] Direct HTTP call to {name} exceeded {self.HTTP_TIMEOUT}s timeout\n"
                f"   Falling back to MCP client protocol..."
            )
            # Fall back to MCP client protocol
            return await self._call_tool_mcp(name, params)

    async def _call_tool_mcp(self, name: str, params: dict[str, Any]) -> Any:
        """
        Make traditional MCP client call.

        Args:
            name: Tool name
            params: Tool parameters

        Returns:
            Raw MCP result

        Raises:
            ValueError: If client not configured
        """
        if not self.client:
            raise ValueError(
                "MCP client not configured. "
                "Set use_direct_http=True or provide client instance."
            )

        logger.debug(f"→ [BEFORE MCP] Sending request to MCP server for {name}")

        result = await asyncio.wait_for(
            self.client.call_tool(name, params),
            timeout=self.HTTP_TIMEOUT
        )

        logger.debug(f"← [AFTER MCP] Received response from {name}")

        return result

    def _format_params_for_log(self, params: dict[str, Any]) -> str:
        """
        Format parameters for logging (compact, safe).

        Args:
            params: Tool parameters

        Returns:
            Formatted string representation
        """
        try:
            # Create a copy to avoid modifying original
            safe_params = params.copy()

            # Truncate long values
            for key, value in safe_params.items():
                if isinstance(value, str) and len(value) > 100:
                    safe_params[key] = value[:100] + "..."
                elif isinstance(value, dict):
                    # Recursively truncate nested dicts
                    safe_params[key] = {k: (v[:50] + "..." if isinstance(v, str) and len(v) > 50 else v)
                                       for k, v in list(value.items())[:5]}
                    if len(value) > 5:
                        safe_params[key]["..."] = f"({len(value) - 5} more fields)"

            return json.dumps(safe_params, default=str)
        except Exception:
            return str(params)[:200]

    def _process_result(self, result: Any, tool_name: str, params: dict[str, Any]) -> Any:
        """
        Process Atoms MCP result format.

        Handles:
        - FastMCP result.content extraction
        - JSON parsing
        - Success/error detection
        - DB permission error formatting
        """
        if result is None:
            return {
                "success": False,
                "error": "Tool returned None",
                "response": None,
            }

        # Extract content from FastMCP result
        if not hasattr(result, "content") or not result.content:
            return {
                "success": False,
                "error": "Empty response",
                "response": None,
            }

        text = result.content[0].text

        try:
            parsed = json.loads(text)

            # Check tool success
            tool_success = parsed.get("success", True)

            return {
                "success": tool_success,
                "error": parsed.get("error") if not tool_success else None,
                "response": parsed,
                "request_params": params if not tool_success else None,
            }

        except json.JSONDecodeError:
            # Non-JSON response (text response)
            return {
                "success": True,
                "error": None,
                "response": {"text": text},
            }

    def _log_error(self, error: Exception, tool_name: str, params: dict[str, Any]) -> None:
        """
        Log error with Atoms-specific formatting.

        Provides concise output for DB permission errors,
        detailed output for other errors.
        """
        error_msg = str(error)

        # Check for DB permission errors
        is_db_error = any([
            "TABLE_ACCESS_RESTRICTED" in error_msg,
            "RLS policy" in error_msg,
            "missing GRANT" in error_msg,
            "permission denied" in error_msg.lower(),
        ])

        print("\n" + "=" * 80)
        if is_db_error:
            print("🔒 DATABASE PERMISSION ERROR")
            entity_type = params.get("entity_type", "unknown")
            operation = params.get("operation", "unknown")
            print(f"   Entity: {entity_type}")
            print(f"   Action: {operation}")
            print(f"   Error: {error_msg}")
        else:
            print(f"❌ TOOL CALL FAILED: {tool_name}")
            print(f"   Params: {json.dumps(params, indent=2, default=str)}")
            print(f"   Error: {error_msg}")
        print("=" * 80 + "\n")

    # ============================================================================
    # Atoms-specific helper methods
    # ============================================================================

    async def workspace_operation(self, operation: str, params: dict[str, Any]) -> Any:
        """
        Atoms-specific workspace operation helper.

        Args:
            operation: Operation name (create, update, delete, etc.)
            params: Operation parameters

        Returns:
            Processed result
        """
        return await self.call_tool("workspace_operation", {
            "operation": operation,
            **params
        })

    async def entity_operation(self, entity_type: str, operation: str, data: dict[str, Any]) -> Any:
        """
        Atoms-specific entity operation helper.

        Args:
            entity_type: Entity type name
            operation: Operation name (create, read, update, delete)
            data: Entity data

        Returns:
            Processed result
        """
        return await self.call_tool("entity_operation", {
            "entity_type": entity_type,
            "operation": operation,
            "data": data
        })

    async def list_tools(self):
        """List available tools."""
        return await self.client.list_tools()

    async def get_tool(self, tool_name: str):
        """Get tool metadata."""
        tools = await self.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

    async def close(self):
        """
        Close HTTP client and release resources.

        Note: We do NOT close the MCP client here because it's managed
        by the session broker and may be shared across multiple adapters.
        We only close our own HTTP client.
        """
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
        # Don't close self.client - it's managed externally

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


__all__ = ["AtomsMCPClientAdapter"]
