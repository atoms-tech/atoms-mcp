#!/usr/bin/env python3
"""
Example: Auth Validation with Unified Test Runner

This example demonstrates the complete auth validation flow:
1. OAuth authentication
2. Auth validation
3. Test execution (if validation passes)

The validation happens automatically between steps 1 and 3.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def example_with_atoms_runner():
    """Example using AtomsMCPTestRunner (automatic validation)."""
    from tests.framework import AtomsMCPTestRunner

    print("=" * 70)
    print("Example: Atoms Test Runner with Automatic Auth Validation")
    print("=" * 70)
    print("")

    mcp_endpoint = os.getenv("ATOMS_MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")

    async with AtomsMCPTestRunner(
        mcp_endpoint=mcp_endpoint,
        parallel=False,  # Run sequentially for demo
        verbose=True,
        enable_all_reporters=False  # Don't generate reports
    ) as runner:
        # Auth validation happens automatically during initialization

        # Check validation result
        if runner.validation_result:
            print("")
            print("📊 Validation Result:")
            print(f"   Valid: {runner.validation_result.valid}")
            print(f"   Duration: {runner.validation_result.duration_ms:.0f}ms")
            print("")

            if not runner.validation_result.valid:
                print("❌ Validation failed, aborting test execution")
                return 1

        # Run a few tests as example
        print("🧪 Running example tests...")
        print("")

        # You would normally run: summary = await runner.run_all()
        # For this example, just show that auth is validated and ready
        print("✅ Auth validated - Ready to run tests")
        print("")
        print("To run full test suite:")
        print("  summary = await runner.run_all()")

    return 0


async def example_with_manual_validation():
    """Example with manual auth validation."""
    from mcp_qa.oauth.credential_broker import UnifiedCredentialBroker
    from mcp_qa.testing.auth_validator import validate_auth

    print("=" * 70)
    print("Example: Manual Auth Validation")
    print("=" * 70)
    print("")

    mcp_endpoint = os.getenv("ATOMS_MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")

    # Step 1: Authenticate
    print("🔐 Step 1: Authentication")
    broker = UnifiedCredentialBroker(
        mcp_endpoint=mcp_endpoint,
        provider="authkit"
    )

    try:
        client, credentials = await broker.get_authenticated_client()

        # Step 2: Validate auth
        print("")
        print("🔍 Step 2: Validation")
        result = await validate_auth(
            client=client,
            credentials=credentials,
            mcp_endpoint=mcp_endpoint,
            verbose=True,
            retry_on_failure=True
        )

        # Step 3: Check result
        print("")
        print("📊 Step 3: Check Result")
        print(f"   Valid: {result.valid}")
        print(f"   Duration: {result.duration_ms:.0f}ms")
        print("")

        if result.valid:
            print("✅ Auth validated - Ready to run tests")
            return 0
        else:
            print("❌ Auth validation failed")
            print(f"   Error: {result.error}")
            print("")
            print("Checks:")
            for check_name, check_result in result.checks.items():
                status = "✓" if check_result['success'] else "✗"
                print(f"   {status} {check_name}: {check_result['message']}")
            return 1

    finally:
        await broker.close()


async def main():
    """Run examples."""
    # Run Atoms runner example (automatic validation)
    print("Running example 1: Automatic validation with AtomsMCPTestRunner")
    print("")
    result = await example_with_atoms_runner()

    print("")
    print("-" * 70)
    print("")

    # Run manual validation example
    print("Running example 2: Manual validation")
    print("")
    result = await example_with_manual_validation()

    return result


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
