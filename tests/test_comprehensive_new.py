#!/usr/bin/env python3
"""
Atoms MCP Comprehensive Test Suite
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Keep FastMCP INFO logging for rich output
logging.getLogger("mcp").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("fastmcp").setLevel(logging.INFO)

from fastmcp import Client
from fastmcp.client.auth import OAuth

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test modules to register tests
# Basic tests (19 tests - tested and working)
from tests import test_workspace, test_entity, test_query, test_relationship, test_workflow  # noqa: F401

# User stories (12 integration tests - working)
from tests import test_user_stories  # noqa: F401

# Comprehensive tests (FIXED - parameters corrected)
try:
    from tests import test_workspace_comprehensive  # noqa: F401
    from tests import test_entity_comprehensive  # noqa: F401
    from tests import test_query_comprehensive  # noqa: F401
    # Relationship and workflow still need real UUIDs - skip for now
    COMPREHENSIVE_AVAILABLE = True
except ImportError:
    COMPREHENSIVE_AVAILABLE = False
from tests.auth_helper import automate_oauth_login_with_retry
from tests.framework import (
    AtomsMCPClientAdapter,
    CachedOAuthClient,
    ConsoleReporter,
    FunctionalityMatrixReporter,
    JSONReporter,
    MarkdownReporter,
    TestCache,
    TestRunner,
    create_cached_client,
)

# Configuration
MCP_ENDPOINT = os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")


class OAuthURLCapture(logging.Handler):
    """Custom log handler to capture OAuth URL from FastMCP logs."""

    def __init__(self):
        super().__init__()
        self.oauth_url: str | None = None

    def emit(self, record):
        msg = self.format(record)
        if "OAuth authorization URL:" in msg or "https://decent-hymn" in msg:
            lines = msg.split("\n")
            for line in lines:
                if line.strip().startswith("https://"):
                    self.oauth_url = line.strip()
                    break


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Atoms MCP comprehensive tests")
    parser.add_argument("--categories", nargs="+", help="Test categories to run (e.g., core entity query)")
    parser.add_argument("--coverage-level", choices=["minimal", "standard", "comprehensive"], default="standard",
                       help="Test coverage level")
    parser.add_argument("--no-cache", action="store_true", help="Disable test caching")
    parser.add_argument("--clear-cache", action="store_true", help="Clear test cache")
    parser.add_argument("--clear-oauth", action="store_true", help="Clear OAuth token cache")
    parser.add_argument("--sequential", action="store_true", help="Run tests sequentially")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel workers")
    parser.add_argument("--priority", type=int, help="Only run tests with priority >= N")
    parser.add_argument("--verbose", action="store_true", help="Show startup info")

    args = parser.parse_args()

    # Clear caches silently
    if args.clear_cache:
        TestCache().clear()

    if args.clear_oauth:
        CachedOAuthClient(MCP_ENDPOINT).clear_cache()

    client = None
    try:
        # OAuth (FastMCP handles logging)
        cached_oauth = CachedOAuthClient(
            mcp_url=MCP_ENDPOINT,
            client_name="Atoms MCP Test Suite",
            playwright_oauth_handler=automate_oauth_login_with_retry,
        )

        client = await asyncio.wait_for(cached_oauth.create_client(), timeout=60.0)

        # Create adapter (verbose only on failure)
        adapter = AtomsMCPClientAdapter(client, verbose_on_fail=True)

        # List tools (FastMCP logs this)
        tools = await client.list_tools()

        # Setup reporters
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent

        reporters = [
            ConsoleReporter(),
            JSONReporter(str(output_dir / f"test_report_{timestamp}.json")),
            MarkdownReporter(str(output_dir / f"test_report_{timestamp}.md")),
            FunctionalityMatrixReporter(str(output_dir / f"functionality_matrix_{timestamp}.md")),
        ]

        # Create runner
        runner = TestRunner(
            client_adapter=adapter,
            cache=not args.no_cache,
            parallel=False,
            reporters=reporters,
        )

        summary = await runner.run_all(categories=args.categories)

        return 1 if summary and summary.get("failed", 0) > 0 else 0

    except asyncio.TimeoutError:
        print("❌ Timeout - try: python tests/test_comprehensive_new.py --clear-oauth")
        return 1
    finally:
        if client:
            await client.__aexit__(None, None, None)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)
