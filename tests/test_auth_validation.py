#!/usr/bin/env python3
"""
Test Auth Validation

Quick test to verify auth validation is working correctly.
This should be run before the full test suite to ensure auth is valid.

Usage:
    python tests/test_auth_validation.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pheno.testing.mcp_qa.oauth.credential_broker import UnifiedCredentialBroker
from pheno.testing.mcp_qa.testing.auth_validator import validate_auth


async def main():
    """Test auth validation."""
    print("=" * 60)
    print("Auth Validation Test")
    print("=" * 60)
    print("")

    # Get MCP endpoint
    mcp_endpoint = os.getenv("ATOMS_MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")
    print(f"MCP Endpoint: {mcp_endpoint}")
    print("")

    # Authenticate
    print("🔐 Authenticating...")
    broker = UnifiedCredentialBroker(
        mcp_endpoint=mcp_endpoint,
        provider="authkit"
    )

    try:
        client, credentials = await broker.get_authenticated_client()
        print("")

        # Validate auth
        result = await validate_auth(
            client=client,
            credentials=credentials,
            mcp_endpoint=mcp_endpoint,
            verbose=True,
            retry_on_failure=True
        )

        print("")
        print("=" * 60)
        print("Validation Result:")
        print("=" * 60)
        print(f"Valid: {result.valid}")
        print(f"Duration: {result.duration_ms:.0f}ms")
        print("")

        if result.valid:
            print("✅ Auth validation passed - Ready for test execution")
            return 0
        print("❌ Auth validation failed:")
        print(f"   {result.error}")
        print("")
        print("Checks:")
        for check_name, check_result in result.checks.items():
            status = "✓" if check_result["success"] else "✗"
            print(f"   {status} {check_name}: {check_result['message']}")
        return 1

    except Exception as e:
        print("")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await broker.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
