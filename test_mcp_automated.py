#!/usr/bin/env python3
"""Fully automated MCP test client with Playwright OAuth.

This client:
1. Uses Playwright to automate OAuth login
2. Captures the OAuth token/session
3. Runs comprehensive MCP tool tests
4. Generates detailed reports

Usage:
    python test_mcp_automated.py
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import json
import os

from fastmcp import Client
from fastmcp.client.auth import BearerAuth

from test_cases import TestCases
from test_report_generator import TestReportGenerator


# Credentials from environment or hardcoded
EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")
MCP_ENDPOINT = "https://mcp.atoms.tech/api/mcp"


async def get_oauth_token_via_playwright() -> Optional[str]:
    """Automate OAuth login using Playwright MCP tools.

    Returns:
        OAuth access token or None
    """
    from mcp__playwright__browser_navigate import browser_navigate
    from mcp__playwright__browser_snapshot import browser_snapshot
    from mcp__playwright__browser_type import browser_type
    from mcp__playwright__browser_close import browser_close

    print("\n🤖 Starting automated OAuth login...")
    print(f"📧 Email: {EMAIL}")

    try:
        # Navigate to OAuth start
        oauth_url = f"{MCP_ENDPOINT}/auth/start"
        print(f"🌐 Navigating to: {oauth_url}")

        await browser_navigate(url=oauth_url)
        await asyncio.sleep(3)  # Wait for page load and redirects

        # Take snapshot
        snapshot = await browser_snapshot()
        print(f"📸 Page loaded, looking for login form...")

        # Find and fill email field
        # The exact selectors depend on AuthKit's form structure
        try:
            await browser_type(
                element="email input",
                ref="input[type='email']",
                text=EMAIL
            )
            print(f"✅ Entered email")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️  Could not find email field (might be different page): {e}")
            # Take snapshot to see what page we're on
            await browser_snapshot()

        # Find and fill password field
        try:
            await browser_type(
                element="password input",
                ref="input[type='password']",
                text=PASSWORD,
                submit=True
            )
            print(f"✅ Entered password and submitted")
            await asyncio.sleep(3)  # Wait for auth to complete
        except Exception as e:
            print(f"⚠️  Could not find password field: {e}")
            await browser_snapshot()

        # After successful login, AuthKit should redirect with token
        # Check current URL for token or session_id
        import re
        snapshot = await browser_snapshot()

        # Try to extract token from URL or page content
        # AuthKit typically redirects to callback URL with code or token
        print(f"📸 Final page snapshot captured")

        # For now, we'll extract from FastMCP's OAuth cache after it completes
        # The token gets stored in ~/.fastmcp/oauth-mcp-client-cache/

        await browser_close()

        # Check FastMCP's token cache
        cache_dir = os.path.expanduser("~/.fastmcp/oauth-mcp-client-cache")
        if os.path.exists(cache_dir):
            import glob
            cache_files = glob.glob(f"{cache_dir}/*.json")
            if cache_files:
                # Read the most recent cache file
                latest_cache = max(cache_files, key=os.path.getmtime)
                with open(latest_cache, 'r') as f:
                    cache_data = json.load(f)
                    token = cache_data.get("access_token")
                    if token:
                        print(f"✅ Found token in cache: {token[:20]}...")
                        return token

        print(f"⚠️  Could not extract token from browser or cache")
        return None

    except Exception as e:
        print(f"❌ Playwright automation failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            await browser_close()
        except:
            pass
        return None


class MCPTestClient:
    """Test client using automated OAuth."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.client: Optional[Client] = None
        self.report = TestReportGenerator()
        self.test_cases = TestCases()
        self.created_entities: Dict[str, str] = {}

    async def connect(self) -> bool:
        """Connect to MCP server."""
        print(f"\n📡 Connecting to {MCP_ENDPOINT}...")

        try:
            # Create client with bearer auth
            auth = BearerAuth(self.access_token)
            self.client = Client(MCP_ENDPOINT, auth=auth)

            await self.client.__aenter__()

            # List tools to verify connection
            tools = await self.client.list_tools()
            print(f"✅ Connected! Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"   - {tool.name}")

            self.report.set_connection_info(MCP_ENDPOINT, "connected")
            self.report.set_auth_info("authenticated", user=EMAIL)

            return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run_all_tests(self):
        """Run comprehensive tests with parallel execution."""
        print("\n" + "="*80)
        print("ATOMS MCP AUTOMATED TEST RUN")
        print("="*80)

        self.report.start_test_run()

        # Run tests in phases (as defined in original client)
        all_cases = self.test_cases.all_test_cases()

        for i, test_case in enumerate(all_cases, 1):
            print(f"\n[{i}/{len(all_cases)}] {test_case['name']}")

            # Call tool
            tool_name = test_case["tool"]
            params = test_case["params"]

            start = time.perf_counter()
            try:
                result = await self.client.call_tool(tool_name, arguments=params)
                duration_ms = (time.perf_counter() - start) * 1000

                # Parse result
                if result.content:
                    text = result.content[0].text
                    parsed = json.loads(text)

                    success = parsed.get("success", True)
                    error = parsed.get("error")

                    if success:
                        print(f"   ✅ Passed ({duration_ms:.2f}ms)")
                    else:
                        print(f"   ❌ Failed: {error}")

                    self.report.add_test_result(
                        test_name=test_case["name"],
                        tool=tool_name,
                        params=params,
                        success=success,
                        duration_ms=duration_ms,
                        response=parsed,
                        error=error,
                        known_issue=test_case.get("known_issue", False)
                    )
                else:
                    print(f"   ❌ Empty response")

            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                print(f"   ❌ Exception: {e}")

                self.report.add_test_result(
                    test_name=test_case["name"],
                    tool=tool_name,
                    params=params,
                    success=False,
                    duration_ms=duration_ms,
                    error=str(e),
                    known_issue=test_case.get("known_issue", False)
                )

        self.report.end_test_run()

    def generate_reports(self):
        """Generate all reports."""
        print("\n📊 Generating reports...")

        self.report.print_console_report()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report.generate_markdown_report(f"test_report_automated_{timestamp}.md")
        self.report.generate_json_report(f"test_report_automated_{timestamp}.json")

    async def cleanup(self):
        """Cleanup."""
        if self.client:
            await self.client.__aexit__(None, None, None)


async def main():
    """Main entry point."""
    print("="*80)
    print("ATOMS MCP AUTOMATED TEST CLIENT")
    print("="*80)

    # Option 1: Use Playwright automation
    # token = await get_oauth_token_via_playwright()

    # Option 2: Use FastMCP's OAuth (simpler, standard)
    # Just let FastMCP handle it - it will open browser and cache tokens
    print("\n🔐 Using FastMCP OAuth (will open browser for first-time login)...")

    try:
        # Use FastMCP's OAuth - it will open browser if no cached token
        from fastmcp.client.auth import OAuth

        oauth = OAuth(mcp_url=MCP_ENDPOINT, client_name="Atoms MCP Test Client")
        client_instance = Client(MCP_ENDPOINT, auth=oauth)

        async with client_instance as client:
            print(f"✅ OAuth completed!")

            # List tools
            tools = await client.list_tools()
            print(f"📋 Found {len(tools.tools)} tools")

            # Run tests
            test_client = MCPTestClient(access_token="oauth-managed")
            test_client.client = client  # Reuse the authenticated client

            test_client.report.set_connection_info(MCP_ENDPOINT, "connected")
            test_client.report.set_auth_info("authenticated", user=EMAIL)

            await test_client.run_all_tests()
            test_client.generate_reports()

            return 0

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(130)
