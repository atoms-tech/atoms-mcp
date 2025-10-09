"""
Atoms MCP Client Adapter with Enhanced Logging

Project-specific adapter that uses pheno-sdk's enhanced logging capabilities.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import Client

# Add pheno-sdk to path
_repo_root = Path(__file__).resolve().parents[2]
_mcp_qa_path = _repo_root / "pheno-sdk" / "mcp-QA"
if _mcp_qa_path.exists():
    sys.path.insert(0, str(_mcp_qa_path))

try:
    from mcp_qa.core import EnhancedMCPAdapter, create_enhanced_adapter
    from mcp_qa.logging import create_mcp_logger, ToolCallContext
    HAS_ENHANCED_LOGGING = True
except ImportError:
    HAS_ENHANCED_LOGGING = False
    # Fallback imports
    import json
    import logging
    import time


def create_atoms_adapter(
    client: Client,
    *,
    verbose_on_fail: bool = True,
    use_color: bool = True,
    use_emoji: bool = True,
    logger_name: str = "atoms.mcp",
) -> "EnhancedMCPAdapter | LegacyAdapter":
    """
    Create an Atoms MCP client adapter with enhanced logging.
    
    Args:
        client: FastMCP Client instance
        verbose_on_fail: Show detailed logs only on failures
        use_color: Enable colored output
        use_emoji: Enable emoji indicators
        logger_name: Name for the logger
    
    Returns:
        EnhancedMCPAdapter if available, otherwise LegacyAdapter
    
    Example:
        from utils.mcp_adapter import create_atoms_adapter
        
        client = Client("http://localhost:8000/api/mcp")
        adapter = create_atoms_adapter(client, verbose_on_fail=True)
        
        result = await adapter.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project"
        })
    """
    if HAS_ENHANCED_LOGGING:
        return create_enhanced_adapter(
            client,
            verbose_on_fail=verbose_on_fail,
            use_color=use_color,
            use_emoji=use_emoji,
        )
    else:
        # Fallback to legacy adapter
        return LegacyAdapter(client, verbose_on_fail=verbose_on_fail)


class LegacyAdapter:
    """
    Legacy adapter for when pheno-sdk enhanced logging is not available.
    
    This provides basic functionality with simple print-based logging.
    """
    
    def __init__(self, client: Client, verbose_on_fail: bool = True):
        """Initialize legacy adapter."""
        self.client = client
        self._url = getattr(client, "_url", "unknown")
        self.verbose_on_fail = verbose_on_fail
        self._call_count = 0
        self._log_buffer = []
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool with basic logging."""
        import json
        import time
        
        self._call_count += 1
        self._log_buffer = []
        start = time.perf_counter()
        
        def log(msg: str):
            self._log_buffer.append(msg)
        
        log(f"[CLIENT-{self._call_count}] Calling tool={tool_name} with args={params!r}"[:200])
        
        try:
            result = await self.client.call_tool(tool_name, arguments=params)
            duration_ms = (time.perf_counter() - start) * 1000
            
            log(f"[CLIENT-{self._call_count}] Got result type={type(result)}")
            
            if result is None:
                log(f"[CLIENT-{self._call_count}] ⚠️  Tool returned None")
                self._print_logs()
                return {
                    "success": False,
                    "error": "Tool returned None",
                    "duration_ms": duration_ms,
                    "response": None,
                }
            
            if result.content:
                text = result.content[0].text
                log(f"[CLIENT-{self._call_count}] Response length: {len(text)} chars")
                
                try:
                    parsed = json.loads(text)
                    tool_success = parsed.get("success", True)
                    
                    if not tool_success:
                        log(f"[CLIENT-{self._call_count}] ❌ Tool returned success=false")
                        log(f"[CLIENT-{self._call_count}] Response: {json.dumps(parsed, indent=2)}")
                        self._print_logs()
                    
                    return {
                        "success": tool_success,
                        "error": parsed.get("error") if not tool_success else None,
                        "duration_ms": duration_ms,
                        "response": parsed,
                        "request_params": params if not tool_success else None,
                    }
                
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "error": None,
                        "duration_ms": duration_ms,
                        "response": {"text": text},
                    }
            
            log(f"[CLIENT-{self._call_count}] ❌ Empty response")
            self._print_logs()
            return {
                "success": False,
                "error": "Empty response",
                "duration_ms": duration_ms,
                "response": None,
            }
        
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            log(f"[CLIENT-{self._call_count}] ❌ Exception: {type(e).__name__}: {str(e)[:100]}")
            self._print_logs()
            
            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms,
                "response": None,
                "request_params": params,
            }
    
    def _print_logs(self):
        """Print buffered logs."""
        if self._log_buffer:
            print("\n" + "═" * 80)
            print("❌ FAILED TEST - LIVE DETAILED OUTPUT:")
            print("═" * 80)
            for log_line in self._log_buffer:
                print(log_line)
            print("═" * 80 + "\n")
    
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
    
    @property
    def endpoint(self) -> str:
        """Get the MCP endpoint URL."""
        return self._url
    
    def enable_verbose(self):
        """Enable verbose logging."""
        self.verbose_on_fail = False
    
    def disable_verbose(self):
        """Disable verbose logging."""
        self.verbose_on_fail = True
    
    def get_stats(self) -> Dict[str, int]:
        """Get adapter statistics."""
        return {
            "total_calls": self._call_count,
            "endpoint": self._url,
        }


__all__ = ["create_atoms_adapter", "LegacyAdapter"]

