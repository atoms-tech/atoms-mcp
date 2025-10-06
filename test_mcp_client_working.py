#!/usr/bin/env python3
"""Working test client for Atoms MCP with session-based auth.

This client properly handles Atoms' AuthKit OAuth + session flow:
1. Uses FastMCP's OAuth to complete authentication
2. Extracts the session_id from the OAuth callback/cookie
3. Uses session_id as Bearer token for subsequent requests
"""

import asyncio
import time
import webbrowser
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import json
import os

from fastmcp import Client
from fastmcp.client.auth import BearerAuth

from test_cases import TestCases
from test_report_generator import TestReportGenerator


class AtomsSessionAuth:
    """Custom auth handler that uses Atoms session_id as Bearer token."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._bearer_auth = BearerAuth(session_id)

    def __call__(self, request):
        """Add session_id as Bearer token to request."""
        return self._bearer_auth(request)


async def get_atoms_session_id() -> Optional[str]:
    """Get session_id via Atoms OAuth flow.

    This opens the browser for OAuth, then extracts the session_id
    from the cookie or local storage.

    Returns:
        session_id (UUID) or None
    """
    import webbrowser
    import http.server
    import socketserver
    import urllib.parse
    from threading import Thread
    import queue

    MCP_ENDPOINT = "https://mcp.atoms.tech/api/mcp"

    print("\n🔐 Starting Atoms OAuth flow...")
    print(f"📡 Endpoint: {MCP_ENDPOINT}")

    # Queue to receive session_id from callback server
    result_queue = queue.Queue()

    # Simple HTTP server to capture OAuth callback
    class CallbackHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            # Parse query parameters
            parsed = urllib.parse.urlparse(self.path)

            if parsed.path == "/oauth-complete":
                # Extract session_id from query or cookie
                query = urllib.parse.parse_qs(parsed.query)

                # Check if session_id is in query params
                session_id = query.get("session_id", [None])[0]

                # Or check cookie header
                if not session_id:
                    cookie_header = self.headers.get("Cookie", "")
                    for cookie in cookie_header.split(";"):
                        cookie = cookie.strip()
                        if cookie.startswith("mcp_session_id="):
                            session_id = cookie.split("=", 1)[1]
                            break

                if session_id:
                    result_queue.put(session_id)
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                        <html><body>
                        <h1>Authentication Successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                        </body></html>
                    """)
                else:
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                        <html><body>
                        <h1>Authentication Failed</h1>
                        <p>No session_id found. Please try again.</p>
                        </body></html>
                    """)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress log messages

    # Start callback server on random port
    with socketserver.TCPServer(("", 0), CallbackHandler) as httpd:
        port = httpd.server_address[1]
        callback_url = f"http://localhost:{port}/oauth-complete"

        print(f"🎧 Started callback server on port {port}")

        # Start server in background thread
        server_thread = Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        # Open browser to OAuth start
        auth_url = f"{MCP_ENDPOINT}/auth/start?redirect_uri={callback_url}"
        print(f"\n🌐 Opening browser for authentication...")
        webbrowser.open(auth_url)

        print("\n⏳ Waiting for OAuth completion...")
        print("   Please log in and authorize the application in your browser.")

        # Wait for callback (with timeout)
        try:
            session_id = result_queue.get(timeout=120)  # 2 minute timeout
            print(f"\n✅ Received session_id: {session_id[:8]}...{session_id[-4:]}")
            return session_id
        except queue.Empty:
            print("\n❌ Timeout waiting for OAuth callback")
            return None
        finally:
            httpd.shutdown()


async def manual_session_input() -> Optional[str]:
    """Fallback: manually input session_id."""
    print("\n📋 Manual session_id input")
    print("   If you have a session_id from a previous login,")
    print("   you can paste it here (or press Enter to skip):")

    session_id = input("\nSession ID: ").strip()
    return session_id if session_id else None


class MCPTestClient:
    """Test client for Atoms MCP."""

    MCP_ENDPOINT = "https://mcp.atoms.tech/api/mcp"

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.client: Optional[Client] = None
        self.report = TestReportGenerator()
        self.test_cases = TestCases()
        self.created_entities: Dict[str, str] = {}

    async def connect(self) -> bool:
        """Connect to MCP server using session_id."""
        print(f"\n📡 Connecting to {self.MCP_ENDPOINT}...")
        print(f"🔑 Using session_id: {self.session_id[:8]}...{self.session_id[-4:]}")

        try:
            # Create client with session-based auth
            auth = AtomsSessionAuth(self.session_id)
            self.client = Client(self.MCP_ENDPOINT, auth=auth)

            # Connect
            await self.client.__aenter__()

            # Verify by listing tools
            tools = await self.client.list_tools()
            print(f"✅ Connected! Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"   - {tool.name}")

            self.report.set_connection_info(self.MCP_ENDPOINT, "connected")
            self.report.set_auth_info("authenticated", user=f"session-{self.session_id[:8]}")

            return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            import traceback
            print(traceback.format_exc())
            self.report.set_connection_info(self.MCP_ENDPOINT, "failed", str(e))
            return False

    async def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool."""
        start_time = time.perf_counter()

        try:
            result = await self.client.call_tool(tool_name, arguments=params)
            duration_ms = (time.perf_counter() - start_time) * 1000

            if result.content:
                text_content = result.content[0].text if result.content else "{}"
                try:
                    parsed_result = json.loads(text_content)
                    parsed_result["_client_timing_ms"] = duration_ms
                    return parsed_result
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": f"Failed to parse response: {text_content[:100]}",
                        "_client_timing_ms": duration_ms
                    }
            else:
                return {
                    "success": False,
                    "error": "Empty response",
                    "_client_timing_ms": duration_ms
                }
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "_client_timing_ms": duration_ms
            }

    async def run_quick_tests(self):
        """Run a few quick tests to validate functionality."""
        print("\n" + "="*80)
        print("RUNNING QUICK VALIDATION TESTS")
        print("="*80)

        self.report.start_test_run()

        # Test 1: workspace_tool
        print("\n🧪 Test 1: workspace_tool (list_workspaces)")
        result = await self._call_tool("workspace_tool", {"operation": "list_workspaces"})
        if result.get("success"):
            print(f"   ✅ Passed ({result.get('_client_timing_ms', 0):.2f}ms)")
        else:
            print(f"   ❌ Failed: {result.get('error')}")

        # Test 2: entity_tool
        print("\n🧪 Test 2: entity_tool (list projects)")
        result = await self._call_tool("entity_tool", {"entity_type": "project", "operation": "list"})
        if result.get("success"):
            count = result.get("count", 0)
            print(f"   ✅ Passed - Found {count} projects ({result.get('_client_timing_ms', 0):.2f}ms)")
        else:
            print(f"   ❌ Failed: {result.get('error')}")

        # Test 3: query_tool
        print("\n🧪 Test 3: query_tool (search)")
        result = await self._call_tool("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "test"
        })
        if result.get("success"):
            print(f"   ✅ Passed ({result.get('_client_timing_ms', 0):.2f}ms)")
        else:
            print(f"   ❌ Failed: {result.get('error')}")

        self.report.end_test_run()

        print("\n" + "="*80)
        print("QUICK TESTS COMPLETE")
        print("="*80)

    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.__aexit__(None, None, None)


async def main():
    """Main entry point."""
    print("="*80)
    print("ATOMS MCP TEST CLIENT")
    print("="*80)

    # Try to get session_id via OAuth
    session_id = await get_atoms_session_id()

    # Fallback to manual input
    if not session_id:
        print("\n⚠️  OAuth flow didn't complete. Trying manual input...")
        session_id = await manual_session_input()

    if not session_id:
        print("\n❌ No session_id available. Cannot proceed.")
        return 1

    # Create and run test client
    client = MCPTestClient(session_id)

    try:
        if not await client.connect():
            print("\n❌ Failed to connect")
            return 1

        # Run quick validation tests
        await client.run_quick_tests()

        print("\n✅ Test client completed!")
        return 0

    finally:
        await client.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
