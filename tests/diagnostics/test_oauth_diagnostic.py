#!/usr/bin/env python3
"""
Quick diagnostic for OAuth flow timeout issue.
"""

import asyncio
import contextlib
import sys

from fastmcp import Client
from fastmcp.client.auth import OAuth

MCP_ENDPOINT = "https://mcp.atoms.tech/api/mcp"


async def test_oauth_init():
    """Test OAuth initialization and URL capture."""
    print("🔍 Testing OAuth initialization...")

    oauth_url_captured = asyncio.Event()
    captured_url = None

    class DiagnosticOAuth(OAuth):
        """OAuth with diagnostics."""

        def __init__(self, *args, **kwargs):
            print("  ✓ OAuth.__init__ called")
            super().__init__(*args, **kwargs)
            print(f"  ✓ Redirect port: {self.redirect_port}")

        async def redirect_handler(self, authorization_url: str) -> None:
            """Called when OAuth URL is ready."""
            nonlocal captured_url
            print(f"  ✓ redirect_handler called: {authorization_url[:100]}...")
            captured_url = authorization_url
            oauth_url_captured.set()

        async def launch_browser(self, authorization_url: str) -> None:
            """Override browser launch."""
            nonlocal captured_url
            print(f"  ✓ launch_browser called: {authorization_url[:100]}...")
            captured_url = authorization_url
            oauth_url_captured.set()

    print("  Creating OAuth handler...")
    oauth = DiagnosticOAuth(mcp_url=MCP_ENDPOINT, client_name="Diagnostic")

    print("  Creating client...")
    client = Client(MCP_ENDPOINT, auth=oauth)

    print("  Starting __aenter__...")
    auth_task = asyncio.create_task(client.__aenter__())

    print("  Waiting for OAuth URL (30s timeout)...")
    try:
        await asyncio.wait_for(oauth_url_captured.wait(), timeout=30.0)
        print(f"  ✅ SUCCESS! OAuth URL captured: {captured_url[:100]}...")

        # Cancel the auth task
        auth_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await auth_task

        return True
    except TimeoutError:
        print("  ❌ TIMEOUT - OAuth URL never captured")
        print(f"  Auth task done: {auth_task.done()}")
        if auth_task.done() and not auth_task.cancelled():
            try:
                exc = auth_task.exception()
                print(f"  Auth task exception: {exc}")
            except Exception:
                pass
        return False
    finally:
        with contextlib.suppress(Exception):
            await client.__aexit__(None, None, None)


if __name__ == "__main__":
    try:
        success = asyncio.run(test_oauth_init())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
