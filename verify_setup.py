#!/usr/bin/env python3
"""
Verify KInfra Local Infrastructure Setup

This script verifies that all components are correctly configured:
1. SmartInfraManager is available
2. Server imports work correctly
3. Environment variables are configured
4. Auth modules are available
5. Test configuration is accessible
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_component(name: str, check_func) -> bool:
    """Verify a component and print the result."""
    try:
        check_func()
        print(f"✓ {name}")
        return True
    except Exception as e:
        print(f"✗ {name}: {e}")
        return False


def check_smart_infra():
    """Check SmartInfraManager."""
    from kinfra import get_smart_infra_manager
    infra = get_smart_infra_manager(project_name="atoms_mcp", domain="atomcp.kooshapari.com")
    assert infra.project_name == "atoms_mcp"
    assert infra.domain == "atomcp.kooshapari.com"


def check_server_imports():
    """Check server imports."""
    from server import create_consolidated_server
    assert create_consolidated_server is not None


def check_auth_modules():
    """Check auth modules."""
    from auth.persistent_authkit_provider import PersistentAuthKitProvider
    from auth.session_middleware import SessionMiddleware
    assert PersistentAuthKitProvider is not None
    assert SessionMiddleware is not None


def check_env_config():
    """Check environment configuration."""
    import os
    from dotenv import load_dotenv

    # Load .env
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    # Check key variables
    port = os.getenv("ATOMS_LOCAL_PORT")
    domain = os.getenv("ATOMS_LOCAL_DOMAIN")

    assert port is not None, "ATOMS_LOCAL_PORT not set"
    assert domain == "atomcp.kooshapari.com", f"ATOMS_LOCAL_DOMAIN is {domain}, expected atomcp.kooshapari.com"


def check_startup_script():
    """Check start_server.py exists and is executable."""
    script = Path(__file__).parent / "start_server.py"
    assert script.exists(), "start_server.py not found"
    assert script.stat().st_mode & 0o111, "start_server.py not executable"


def check_workos_setup():
    """Check WORKOS_SETUP.md exists."""
    doc = Path(__file__).parent / "WORKOS_SETUP.md"
    assert doc.exists(), "WORKOS_SETUP.md not found"


def check_test_main():
    """Check test_main.py has local flag and server detection."""
    test_file = Path(__file__).parent / "tests" / "test_main.py"
    assert test_file.exists(), "tests/test_main.py not found"

    content = test_file.read_text()
    assert "--local" in content, "--local flag not found in test_main.py"
    assert "_check_local_server_running" in content, "_check_local_server_running function not found"
    # Production is the default, so --production flag is optional


def main():
    """Run all verification checks."""
    print("\n" + "="*70)
    print("  KInfra Local Infrastructure Setup Verification")
    print("="*70 + "\n")

    checks = [
        ("SmartInfraManager", check_smart_infra),
        ("Server imports", check_server_imports),
        ("Auth modules", check_auth_modules),
        ("Environment config", check_env_config),
        ("Startup script", check_startup_script),
        ("WorkOS setup guide", check_workos_setup),
        ("Test main flags", check_test_main),
    ]

    results = []
    for name, check_func in checks:
        results.append(verify_component(name, check_func))

    print("\n" + "-"*70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} checks passed")
    print("-"*70 + "\n")

    if passed == total:
        print("✓ All checks passed! KInfra setup is complete.\n")
        print("Next steps:")
        print("  1. Start local server:")
        print("     python start_server.py --tunnel")
        print()
        print("  2. Run tests against local server:")
        print("     python tests/test_main.py --local")
        print()
        print("  3. Configure WorkOS redirect URLs (see WORKOS_SETUP.md):")
        print("     - https://atomcp.kooshapari.com/callback")
        print("     - http://localhost:50002/callback")
        print()
        return 0
    else:
        print("✗ Some checks failed. Please fix the errors above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
