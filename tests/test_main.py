#!/usr/bin/env python3
"""
Atoms MCP Comprehensive Test Suite

Enhanced with Zen MCP features:
- Health checks before test execution
- PlaywrightOAuthAdapter support
- Improved error handling and reporting
- Session-based OAuth with broker pattern
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from fastmcp import Client
from fastmcp.client.auth import OAuth

# Ensure shared mcp_qa library is importable before local packages
_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parents[2]
_SHARED_QA_PATHS = [
    _REPO_ROOT / "clean" / "mcp-QA",
]
for _path in _SHARED_QA_PATHS:
    if _path.exists():
        sys.path.insert(0, str(_path))

# Add project parent to path for local imports
sys.path.insert(0, str(_TESTS_DIR.parent))

# Import from local framework
from tests.framework import (
    AtomsMCPTestRunner,
    TestCache,
)
from tests.framework.test_logging_setup import (
    configure_test_logging,
    suppress_deprecation_warnings,
)

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

# Configuration
MCP_ENDPOINT = os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")


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
    parser.add_argument("--verbose", action="store_true", help="Show verbose logging (default: only errors)")
    parser.add_argument(
        "--use-shared-session",
        action="store_true",
        help="Reuse a shared OAuth session broker instead of launching Playwright",
    )

    args = parser.parse_args()

    # Configure logging based on verbose flag
    configure_test_logging(verbose=args.verbose)
    suppress_deprecation_warnings()

    # Clear caches silently
    if args.clear_cache:
        TestCache().clear()

    if args.clear_oauth:
        # Clear OAuth cache if it exists
        cache_file = Path.home() / ".atoms_mcp_test_cache" / "credentials.json"
        if cache_file.exists():
            cache_file.unlink()
            print("✅ OAuth cache cleared")

    try:
        # Use AtomsMCPTestRunner which integrates pheno-sdk's UnifiedMCPTestRunner
        # with Atoms-specific test infrastructure
        async with AtomsMCPTestRunner(
            mcp_endpoint=MCP_ENDPOINT,
            provider=os.getenv("ATOMS_OAUTH_PROVIDER", "authkit"),
            parallel=not args.sequential,
            workers=args.workers,
            cache=not args.no_cache,
            verbose=args.verbose,
            output_dir=Path(__file__).parent,
            enable_all_reporters=True,
        ) as runner:
            summary = await runner.run_all(categories=args.categories)
            return 1 if summary and summary.get("failed", 0) > 0 else 0

    except asyncio.TimeoutError:
        print("❌ Timeout - try: python tests/test_comprehensive_new.py --clear-oauth")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
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
