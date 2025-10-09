"""
Atoms MCP Client Adapter

Extends pheno-sdk's BaseClientAdapter with Atoms-specific result processing
and error handling.

This is the slimmed-down version (~80 lines vs ~200 before) that leverages
shared infrastructure from pheno-sdk.
"""

import json
from typing import Any, Dict
from utils.logging_setup import get_logger

from mcp_qa.core.base import BaseClientAdapter

logger = get_logger("atoms.adapter")


class AtomsMCPClientAdapter(BaseClientAdapter):
    """
    Atoms-specific MCP client adapter.
    
    Extends BaseClientAdapter with Atoms-specific:
    - Result processing (JSON parsing, success detection)
    - Error handling (DB permissions, verbose failures)
    - Helper methods (workspace operations, etc.)
    """
    
    def __init__(self, client: Any, debug: bool = False, verbose_on_fail: bool = True):
        """
        Initialize Atoms adapter.
        
        Args:
            client: FastMCP Client instance
            debug: Enable debug logging
            verbose_on_fail: Show detailed logs on failure
        """
        super().__init__(client, verbose_on_fail=verbose_on_fail)
        self.debug = debug
        self._url = getattr(client, "_url", "unknown")
        self.endpoint = self._url  # For metadata compatibility
    
    def _process_result(self, result: Any, tool_name: str, params: Dict[str, Any]) -> Any:
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
        if not hasattr(result, 'content') or not result.content:
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
    
    def _log_error(self, error: Exception, tool_name: str, params: Dict[str, Any]) -> None:
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
    
    async def workspace_operation(self, operation: str, params: Dict[str, Any]) -> Any:
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
    
    async def entity_operation(self, entity_type: str, operation: str, data: Dict[str, Any]) -> Any:
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


__all__ = ["AtomsMCPClientAdapter"]
