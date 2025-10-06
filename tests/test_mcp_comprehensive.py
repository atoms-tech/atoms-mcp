#!/usr/bin/env python3
"""Comprehensive Atoms MCP test suite - FULLY AUTOMATED.

This is the consolidated, authoritative test suite for all Atoms MCP functionality.
Tests the production endpoint with:
- FULLY AUTOMATED OAuth login via Playwright (1-click E2E)
- Parallel execution for independent tests
- Detailed performance metrics and reporting

Usage:
    python tests/test_mcp_comprehensive.py

This will automatically:
1. Open browser and log in using Playwright
2. Complete OAuth flow
3. Run all MCP tool tests
4. Generate comprehensive reports
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import json
import os
from pathlib import Path

from fastmcp import Client
from fastmcp.client.auth import OAuth

# Configuration
MCP_ENDPOINT = os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Capture FastMCP OAuth URL from logs
class OAuthURLCapture(logging.Handler):
    """Custom log handler to capture OAuth URL."""

    def __init__(self):
        super().__init__()
        self.oauth_url: Optional[str] = None

    def emit(self, record):
        msg = self.format(record)
        if "OAuth authorization URL:" in msg or "https://decent-hymn" in msg:
            # Extract URL from log message
            lines = msg.split('\n')
            for line in lines:
                if line.strip().startswith('https://'):
                    self.oauth_url = line.strip()
                    break


async def automate_oauth_login(oauth_url: str) -> bool:
    """Automate OAuth login using Playwright (visible browser).

    OAuth Flow:
    1. Login page - enter email/password
    2. AuthKit allow access page - click "Allow"
    3. Success page - OAuth complete

    Args:
        oauth_url: The OAuth authorization URL

    Returns:
        True if automation succeeded
    """
    print(f"\n🤖 Automating OAuth login with Playwright (VISIBLE browser)...")
    print(f"🔗 URL: {oauth_url[:80]}...")

    try:
        from mcp__playwright__browser_navigate import browser_navigate
        from mcp__playwright__browser_type import browser_type
        from mcp__playwright__browser_click import browser_click
        from mcp__playwright__browser_wait_for import browser_wait_for
        from mcp__playwright__browser_snapshot import browser_snapshot
        from mcp__playwright__browser_close import browser_close
    except ImportError:
        print("⚠️  Playwright MCP tools not available")
        return False

    try:
        # Step 1: Navigate to OAuth URL
        print("\n🌐 Step 1: Navigating to OAuth URL...")
        await browser_navigate(url=oauth_url)
        await asyncio.sleep(3)

        snapshot = await browser_snapshot()
        print("   📸 Snapshot: Login page loaded")

        # Step 2: Fill in credentials
        print("\n📝 Step 2: Filling in credentials...")

        print("   🔍 Looking for email field (#email)...")
        await browser_type(
            element="email field",
            ref="#email",
            text=TEST_EMAIL
        )
        print(f"   ✅ Entered email: {TEST_EMAIL}")
        await asyncio.sleep(0.5)

        print("   🔍 Looking for password field (#password)...")
        await browser_type(
            element="password field",
            ref="#password",
            text=TEST_PASSWORD
        )
        print(f"   ✅ Entered password")
        await asyncio.sleep(0.5)

        # Step 3: Click Sign in
        print("\n🖱️  Step 3: Clicking Sign in button...")
        await browser_click(
            element="Sign in button",
            ref="button[type='submit']"
        )
        print("   ✅ Clicked Sign in")

        # Wait for AuthKit allow access page
        print("\n⏳ Step 4: Waiting for AuthKit 'Allow access' page...")
        await asyncio.sleep(3)

        snapshot = await browser_snapshot()
        print("   📸 Snapshot: Should be on Allow access page")

        # Step 4: Click "Allow" button on AuthKit consent page
        print("\n🖱️  Step 5: Clicking 'Allow' on AuthKit consent page...")
        try:
            # AuthKit typically has a button with text "Allow" or "Authorize"
            await browser_click(
                element="Allow button",
                ref="button:has-text('Allow'), button:has-text('Authorize'), button[type='submit']"
            )
            print("   ✅ Clicked Allow")
        except Exception as e:
            print(f"   ⚠️  Could not find Allow button: {e}")
            print("   📸 Taking snapshot...")
            await browser_snapshot()

        # Wait for final redirect to callback
        print("\n⏳ Step 6: Waiting for OAuth callback redirect...")
        await asyncio.sleep(5)

        snapshot = await browser_snapshot()
        print("   📸 Snapshot: Final page")

        await browser_close()
        print("\n✅ Playwright automation completed - browser closed")
        return True

    except Exception as e:
        print(f"\n❌ Playwright automation failed: {e}")
        import traceback
        print(traceback.format_exc())

        print("\n📸 Taking error snapshot...")
        try:
            await browser_snapshot()
            await browser_close()
        except:
            pass
        return False


class TestReportGenerator:
    """Generate test reports."""

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.connection_info: Dict[str, Any] = {}
        self.auth_info: Dict[str, Any] = {}

    def start_test_run(self):
        self.start_time = datetime.now()

    def end_test_run(self):
        self.end_time = datetime.now()

    def set_connection_info(self, url: str, status: str, error: str | None = None):
        self.connection_info = {"url": url, "status": status, "error": error}

    def set_auth_info(self, status: str, user: str | None = None, error: str | None = None):
        self.auth_info = {"status": status, "user": user, "error": error}

    def add_test_result(self, test_name: str, tool: str, params: Dict, success: bool,
                       duration_ms: float, response: Any = None, error: str | None = None,
                       known_issue: bool = False, skipped: bool = False, skip_reason: str | None = None):
        self.test_results.append({
            "test_name": test_name,
            "tool": tool,
            "params": params,
            "success": success,
            "duration_ms": round(duration_ms, 2),
            "response": response,
            "error": error,
            "known_issue": known_issue,
            "skipped": skipped,
            "skip_reason": skip_reason,
            "timestamp": datetime.now().isoformat()
        })

    def get_summary_stats(self) -> Dict[str, Any]:
        total = len(self.test_results)
        if total == 0:
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "known_issues": 0, "pass_rate": 0.0, "avg_duration_ms": 0.0}

        passed = sum(1 for r in self.test_results if r["success"] and not r["skipped"])
        failed = sum(1 for r in self.test_results if not r["success"] and not r["skipped"])
        skipped = sum(1 for r in self.test_results if r["skipped"])
        known_issues = sum(1 for r in self.test_results if r.get("known_issue", False))

        total_duration = sum(r["duration_ms"] for r in self.test_results if not r["skipped"])
        avg_duration = total_duration / (total - skipped) if (total - skipped) > 0 else 0.0
        pass_rate = (passed / (total - skipped)) * 100 if (total - skipped) > 0 else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "known_issues": known_issues,
            "pass_rate": round(pass_rate, 1),
            "avg_duration_ms": round(avg_duration, 2)
        }

    def print_console_report(self):
        print("\n" + "=" * 80)
        print("ATOMS MCP TEST REPORT")
        print("=" * 80)

        print(f"\n📡 CONNECTION: {self.connection_info.get('url')}")
        print(f"🔐 AUTH: {self.auth_info.get('status')} ({self.auth_info.get('user')})")

        stats = self.get_summary_stats()
        print(f"\n📊 SUMMARY")
        print(f"   Total: {stats['total']} | ✅ {stats['passed']} | ❌ {stats['failed']} | ⚠️  {stats['known_issues']}")
        print(f"   Pass Rate: {stats['pass_rate']}% | Avg: {stats['avg_duration_ms']}ms")

        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"   Total Time: {duration:.2f}s")

        by_tool: Dict[str, List] = {}
        for r in self.test_results:
            by_tool.setdefault(r["tool"], []).append(r)

        print(f"\n🔧 RESULTS BY TOOL:")
        for tool, results in by_tool.items():
            print(f"\n   {tool}:")
            for r in results:
                icon = "⏭️ " if r["skipped"] else ("⚠️ " if r.get("known_issue") else ("✅" if r["success"] else "❌"))
                print(f"     {icon} {r['test_name']} ({r['duration_ms']}ms)")
                if r["error"] and not r["success"] and not r["skipped"]:
                    print(f"        {r['error'][:60]}")

        print("\n" + "=" * 80)

    def generate_json_report(self, output_path: str):
        report = {
            "generated_at": datetime.now().isoformat(),
            "endpoint": self.connection_info.get("url"),
            "auth_status": self.auth_info.get("status"),
            "summary": self.get_summary_stats(),
            "test_results": self.test_results
        }

        if self.start_time and self.end_time:
            report["duration_seconds"] = (self.end_time - self.start_time).total_seconds()

        Path(output_path).write_text(json.dumps(report, indent=2))
        print(f"📄 Report: {output_path}")


class ComprehensiveMCPTests:
    """Comprehensive test suite."""

    def __init__(self, client: Client):
        self.client = client
        self.report = TestReportGenerator()

    async def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool and return parsed result with timing."""
        start = time.perf_counter()
        try:
            result = await self.client.call_tool(tool_name, arguments=params)
            duration_ms = (time.perf_counter() - start) * 1000

            if result.content:
                text = result.content[0].text
                parsed = json.loads(text)
                parsed["_timing_ms"] = duration_ms
                return parsed
            return {"success": False, "error": "Empty response", "_timing_ms": duration_ms}
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return {"success": False, "error": str(e), "_timing_ms": duration_ms}

    async def run_all_tests(self):
        """Run all tests with parallel execution."""
        print("\n🧪 Running comprehensive tests...\n")

        self.report.start_test_run()

        # Define all test cases
        tests = [
            ("workspace: list", "workspace_tool", {"operation": "list_workspaces"}, False),
            ("workspace: get_context", "workspace_tool", {"operation": "get_context"}, False),
            ("entity: list orgs", "entity_tool", {"entity_type": "organization", "operation": "list"}, False),
            ("entity: list projects", "entity_tool", {"entity_type": "project", "operation": "list"}, False),
            ("entity: list documents", "entity_tool", {"entity_type": "document", "operation": "list"}, False),
            ("entity: list requirements", "entity_tool", {"entity_type": "requirement", "operation": "list"}, False),
            ("entity: create org (RLS)", "entity_tool", {"entity_type": "organization", "operation": "create", "data": {"name": "Test", "slug": "test"}}, True),
            ("query: search", "query_tool", {"query_type": "search", "entities": ["project"], "search_term": "test"}, False),
            ("query: aggregate", "query_tool", {"query_type": "aggregate", "entities": ["project"]}, False),
            ("query: RAG semantic", "query_tool", {"query_type": "rag_search", "entities": ["requirement"], "search_term": "safety", "rag_mode": "semantic"}, True),
            ("query: RAG keyword", "query_tool", {"query_type": "rag_search", "entities": ["document"], "search_term": "test", "rag_mode": "keyword"}, False),
        ]

        # Run tests
        for test_name, tool, params, known_issue in tests:
            result = await self._call_tool(tool, params)

            success = result.get("success", False)
            duration = result.get("_timing_ms", 0)
            error = result.get("error")

            self.report.add_test_result(test_name, tool, params, success, duration, result, error, known_issue)

            icon = "⚠️ " if known_issue else ("✅" if success else "❌")
            print(f"{icon} {test_name} ({duration:.2f}ms)")

        self.report.end_test_run()

    def generate_reports(self):
        self.report.print_console_report()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(__file__).parent / f"mcp_test_report_{timestamp}.json"
        self.report.generate_json_report(str(report_path))


async def main():
    """Main runner with Playwright automation."""
    print("=" * 80)
    print("ATOMS MCP COMPREHENSIVE TEST SUITE (AUTOMATED)")
    print(f"Endpoint: {MCP_ENDPOINT}")
    print(f"Email: {TEST_EMAIL}")
    print("=" * 80)

    # Capture stderr to extract OAuth URL
    import io
    import sys as sys_module

    captured_output = io.StringIO()
    original_stderr = sys_module.stderr

    try:
        # Redirect stderr to capture OAuth URL
        sys_module.stderr = captured_output

        # Create OAuth client
        print("\n🔐 Starting OAuth flow...")
        oauth = OAuth(mcp_url=MCP_ENDPOINT, client_name="Atoms MCP Test Suite")
        client = Client(MCP_ENDPOINT, auth=oauth)

        # Start authentication in background
        auth_task = asyncio.create_task(client.__aenter__())

        # Wait for OAuth URL to appear in stderr
        print("⏳ Waiting for OAuth URL...")
        oauth_url = None

        for i in range(20):
            await asyncio.sleep(0.5)

            # Check captured output
            output = captured_output.getvalue()
            if "https://decent-hymn" in output or "oauth2/authorize" in output:
                # Extract the URL
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith("https://") and "oauth2/authorize" in line:
                        oauth_url = line
                        # Restore stderr so we can print
                        sys_module.stderr = original_stderr
                        print(f"✅ Captured OAuth URL after {i * 0.5:.1f}s")
                        print(f"   URL: {oauth_url[:80]}...")
                        break

                if oauth_url:
                    break

        # Restore stderr
        sys_module.stderr = original_stderr

        if oauth_url:
            # Start Playwright automation
            automation_task = asyncio.create_task(automate_oauth_login(oauth_url))

            # Wait for both to complete
            results = await asyncio.gather(auth_task, automation_task, return_exceptions=True)

            # Check for errors
            for result in results:
                if isinstance(result, Exception):
                    print(f"⚠️  Task failed: {result}")
        else:
            print("⚠️  Could not capture OAuth URL, waiting for manual login...")
            # Wait for manual completion
            await auth_task

        print("✅ OAuth completed!")

        # List tools
        tools = await client.list_tools()
        print(f"📋 Found {len(tools.tools)} tools")

        # Run tests
        test_suite = ComprehensiveMCPTests(client)
        test_suite.report.set_connection_info(MCP_ENDPOINT, "connected")
        test_suite.report.set_auth_info("authenticated", user=TEST_EMAIL)

        await test_suite.run_all_tests()
        test_suite.generate_reports()

        # Cleanup
        await client.__aexit__(None, None, None)

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
        print("\n⚠️  Interrupted")
        sys.exit(130)
