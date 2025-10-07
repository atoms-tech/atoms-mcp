"""
Client Adapters for Atoms MCP Test Framework

Provides abstraction layer over FastMCP client for testing with detailed logging.
"""

import json
import logging
import time
from typing import Any, Dict

from fastmcp import Client

# Configure detailed logging for debugging
logger = logging.getLogger("atoms.adapter")


class AtomsMCPClientAdapter:
    """
    Adapter for FastMCP Client.

    Provides unified interface for calling MCP tools with timing, error handling,
    and comprehensive debug logging for troubleshooting.
    """

    def __init__(self, client: Client, debug: bool = False, verbose_on_fail: bool = True):
        """
        Initialize adapter with FastMCP client.

        Args:
            client: FastMCP Client instance (already authenticated)
            debug: Enable verbose debug logging
            verbose_on_fail: Only show detailed logs when tests fail (default: True)
        """
        self.client = client
        self._url = getattr(client, "_url", "unknown")
        self.debug = debug
        self.verbose_on_fail = verbose_on_fail
        self._call_count = 0
        self._last_call_log = []  # Store logs for last call

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool and return parsed result with timing.

        Detailed logging only shown when test fails (verbose_on_fail=True).

        Args:
            tool_name: Name of the tool to call
            params: Tool parameters

        Returns:
            Dict with structure:
            {
                "success": bool,
                "error": str | None,
                "duration_ms": float,
                "response": Any (parsed response if success)
            }
        """
        self._call_count += 1
        self._last_call_log = []  # Reset log buffer
        start = time.perf_counter()

        # Capture logs in buffer (ONLY print on failure, never on success)
        def log(msg: str):
            self._last_call_log.append(msg)
            # Never print here - only via _print_logs_on_error()

        log(f"[CLIENT-{self._call_count}] Calling tool={tool_name} with args={params!r}"[:200])

        try:
            result = await self.client.call_tool(tool_name, arguments=params)
            duration_ms = (time.perf_counter() - start) * 1000

            # Capture logs (print only on failure)
            log(f"[CLIENT-{self._call_count}] Got result type={type(result)}")

            if result is None:
                log(f"[CLIENT-{self._call_count}] ⚠️  Tool returned None")
                self._print_logs_on_error()
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

                    # Check if tool call succeeded
                    tool_success = parsed.get("success", True)

                    if not tool_success:
                        # Tool failed - print full logs
                        log(f"[CLIENT-{self._call_count}] ❌ Tool returned success=false")
                        log(f"[CLIENT-{self._call_count}] Response: {json.dumps(parsed, indent=2)}")
                        self._print_logs_on_error()
                    # else: Success - don't print logs (quiet mode)

                    parsed["_duration_ms"] = duration_ms
                    return {
                        "success": tool_success,
                        "error": parsed.get("error") if not tool_success else None,
                        "duration_ms": duration_ms,
                        "response": parsed,
                        "request_params": params if not tool_success else None,
                    }

                except json.JSONDecodeError as e:
                    log(f"[CLIENT-{self._call_count}] ⚠️  JSON parse failed: {e}")
                    self._print_logs_on_error()
                    return {
                        "success": True,
                        "error": None,
                        "duration_ms": duration_ms,
                        "response": {"text": text},
                    }

            # No content
            log(f"[CLIENT-{self._call_count}] ❌ Empty response")
            self._print_logs_on_error()
            return {
                "success": False,
                "error": "Empty response",
                "duration_ms": duration_ms,
                "response": None,
            }

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            log(f"[CLIENT-{self._call_count}] ❌ Exception: {type(e).__name__}: {str(e)[:100]}")
            self._print_logs_on_error()

            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms,
                "response": None,
                "request_params": params,
            }

    def _print_logs_on_error(self):
        """Print buffered logs IMMEDIATELY when error occurs (live fail verbosity)."""
        if self._last_call_log:  # ALWAYS show on failure
            print("\n" + "═" * 80)
            print("❌ FAILED TEST - LIVE DETAILED OUTPUT:")
            print("═" * 80)
            for log_line in self._last_call_log:
                print(log_line)
            print("═" * 80 + "\n")

    async def list_tools(self):
        """
        List available tools.

        Returns:
            List of tool metadata
        """
        return await self.client.list_tools()

    async def get_tool(self, tool_name: str):
        """
        Get tool metadata.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool metadata
        """
        tools = await self.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

    @property
    def endpoint(self) -> str:
        """Get the MCP endpoint URL."""
        return self._url

    def enable_debug(self):
        """Enable verbose debug logging."""
        self.debug = True
        logger.setLevel(logging.DEBUG)
        print("[CLIENT] 🐛 Debug logging enabled")

    def disable_debug(self):
        """Disable debug logging."""
        self.debug = False
        logger.setLevel(logging.INFO)

    def get_stats(self) -> Dict[str, int]:
        """Get adapter statistics."""
        return {
            "total_calls": self._call_count,
            "endpoint": self._url,
        }
