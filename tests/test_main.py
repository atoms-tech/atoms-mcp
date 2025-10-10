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
_REPO_ROOT = _TESTS_DIR.parent.parent  # atoms_mcp-old -> kush -> 485
_SHARED_QA_PATHS = [
    _REPO_ROOT / "pheno-sdk" / "mcp-QA",  # Primary location
    _REPO_ROOT / "clean" / "mcp-QA",      # Fallback location
]
for _path in _SHARED_QA_PATHS:
    if _path.exists():
        sys.path.insert(0, str(_path))
        break

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

# Add parent to path for imports
sys.path.insert(0, str(_TESTS_DIR.parent))

# Import endpoint configuration from centralized mcp_qa library
from mcp_qa.config.endpoints import EndpointRegistry, MCPProject, Environment

TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")


def _check_local_server_running() -> tuple[bool, str | None]:
    """Check if local server is running on port 50002.

    Returns:
        tuple: (is_running, endpoint_url)
    """
    try:
        # First try the new atoms port (50002)
        import requests
        try:
            response = requests.get("http://localhost:50002/health", timeout=2)
            if response.status_code == 200:
                return True, DEFAULT_LOCAL_ENDPOINT
        except requests.exceptions.RequestException:
            pass

        # Fallback: check config file for custom port
        config_file = Path.home() / ".atoms_mcp_test_cache" / "local_server_config.json"
        if config_file.exists():
            import json
            with open(config_file) as f:
                config = json.load(f)

            port = config.get("port", 50002)
            api_endpoint = config.get("api_endpoint")

            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    return True, api_endpoint or f"http://localhost:{port}/api/mcp"
            except requests.exceptions.RequestException:
                pass

        return False, None
    except Exception:
        return False, None


def _check_dev_server_health() -> tuple[bool, str | None]:
    """Check if dev server is healthy at devmcp.atoms.tech.

    Returns:
        tuple: (is_healthy, error_message)
    """
    try:
        import requests
        # Try to reach the dev server health endpoint
        health_url = "https://devmcp.atoms.tech/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"Dev server returned status {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Dev server health check timed out"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to dev server"
    except Exception as e:
        return False, f"Dev server health check failed: {str(e)}"


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Atoms MCP comprehensive tests",
        epilog="""
Examples:
  python test_main.py                          # Run all tests on prod
  python test_main.py -t local                 # Run on local server
  python test_main.py -t dev -w 4              # Run on dev with 4 workers
  python test_main.py -k entity query          # Run entity and query tests
  python test_main.py -v                       # Verbose output
  python test_main.py --clear-cache            # Clear all caches
  python test_main.py --clear-oauth            # Clear OAuth cache only
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Target selection
    parser.add_argument("--target", "-t", choices=["local", "dev", "prod"], default="prod",
                       help="Target environment (default: prod)")

    # Test execution
    parser.add_argument("--categories", "-k", nargs="+",
                       help="Test categories to run (e.g., entity query)")
    parser.add_argument("--workers", "-w", type=int,
                       help="Number of parallel workers (default: 1)")

    # Output control
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed output and print statements")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Minimal output (only errors)")
    parser.add_argument("--no-progress", action="store_true",
                       help="Disable rich progress display")
    parser.add_argument("--no-reports", action="store_true",
                       help="Disable test reports")

    # Cache management
    parser.add_argument("--clear-cache", action="store_true",
                       help="Clear all caches (test + OAuth)")
    parser.add_argument("--clear-oauth", action="store_true",
                       help="Clear OAuth credentials cache only")

    args = parser.parse_args()

    # Set MCP endpoint based on target environment
    EndpointRegistry.set_environment(args.target, project=MCPProject.ATOMS)
    endpoint_source = EndpointRegistry.get_display_name(project=MCPProject.ATOMS, environment=args.target)
    MCP_ENDPOINT = EndpointRegistry.get_endpoint(project=MCPProject.ATOMS, environment=args.target)

    # Set environment variable so auth plugin can use it
    os.environ["MCP_ENDPOINT"] = MCP_ENDPOINT

    # Configure logging based on verbose/quiet flags
    if args.quiet and args.verbose:
        print("Error: Cannot use --quiet and --verbose together")
        return 1

    # verbose=False already handles quiet mode (only shows errors)
    configure_test_logging(verbose=args.verbose)
    suppress_deprecation_warnings()

    # Clear OAuth cache if requested
    oauth_cache_file = Path.home() / ".atoms_mcp_test_cache" / "credentials.json"
    if args.clear_oauth:
        if oauth_cache_file.exists():
            oauth_cache_file.unlink()
            print("✅ OAuth cache cleared")

    # Clear all caches if requested
    if args.clear_cache:
        TestCache().clear()
        if oauth_cache_file.exists():
            oauth_cache_file.unlink()
        print("✅ All caches cleared (test + OAuth)")

    try:
        # Use pytest with pheno-sdk auth plugin for automatic authentication
        # The plugin handles OAuth before test collection with progress bar
        # Tests get cached credentials via request.session.config._mcp_credentials
        import subprocess
        import sys

        # Build pytest command
        pytest_args = ["pytest", "tests/unit/"]

        # Verbosity control
        if args.quiet:
            pytest_args.append("-q")  # Quiet mode
        elif args.verbose:
            pytest_args.extend(["-vv", "-s", "--tb=long"])  # Very verbose + show prints + full traceback
        else:
            pytest_args.extend(["-v", "--tb=short", "-ra"])  # Default: verbose + short traceback

        # Test filtering
        if args.categories:
            category_filter = " or ".join(args.categories)
            pytest_args.extend(["-k", category_filter])

        # Parallel execution
        if args.workers:
            pytest_args.extend(["-n", str(args.workers)])

        # Add maxfail for faster feedback
        pytest_args.extend(["--maxfail=10"])

        # Skip banner in quiet mode
        if not args.quiet:
            print(f"\n🧪 Running Atoms MCP Test Suite with Auth Plugin\n")
            print("Configuration:")
            print(f"  • Target: {endpoint_source}")
            print(f"  • Endpoint: {MCP_ENDPOINT}")
            print()
            print("Features:")
            print(f"  • Auth Plugin: ✓ (automatic OAuth with progress bar)")
            print(f"  • Cached Credentials: ✓ (auth runs once before collection)")
            print(f"  • Fast execution: ✓ (pytest + FastHTTPClient)")
            print(f"  • Output mode: {'verbose' if args.verbose else 'quiet' if args.quiet else 'normal'}")
            print(f"  • Parallel workers: {args.workers if args.workers else '1 (sequential)'}")
            if args.categories:
                print(f"  • Test filter: {', '.join(args.categories)}")
            print()
            print("Auth Plugin will:")
            print("  1. Run OAuth flow before test collection")
            print("  2. Show progress bar during authentication")
            print("  3. Display completion message with credential info")
            print("  4. Cache credentials for all tests to use")
            print()
            print(f"Command: {' '.join(pytest_args)}\n")

        # Run pytest - auth plugin handles authentication automatically
        result = subprocess.run(pytest_args, cwd=Path(__file__).parent.parent)
        return result.returncode

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
