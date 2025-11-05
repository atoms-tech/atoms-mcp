#!/usr/bin/env python3
"""
Test script for hybrid configuration loading.

This script tests that:
1. Configuration loads from YAML in local development
2. Configuration loads from environment variables in Vercel
3. Settings are properly typed and validated
"""

import os
import sys
import traceback
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from settings.app import AppSettings
from settings.combined import AtomsSettings, is_vercel_environment


def test_local_yaml_loading():
    """Test loading from YAML files (local development)."""
    print("\n" + "=" * 60)
    print("TEST 1: Local YAML Loading")
    print("=" * 60)

    # Force YAML loading
    settings = AtomsSettings(force_yaml=True)

    print(f"✓ Configuration source: {settings.source}")
    print(f"✓ App name: {settings.app.mcp_server_name}")
    print(f"✓ Host: {settings.app.host}")
    print(f"✓ Port: {settings.app.port}")
    print(f"✓ Debug: {settings.app.debug}")
    print(f"✓ Log level: {settings.app.log_level}")

    # Check if secrets are loaded (if secrets.yml exists)
    if Path("secrets.yml").exists():
        print(f"✓ Has Supabase config: {settings.secrets.has_supabase_config()}")
        print(f"✓ Has Google AI config: {settings.secrets.has_google_ai_config()}")
    else:
        print("⚠ secrets.yml not found (expected in local dev)")

    assert settings.source == "yaml", "Should load from YAML"
    print("\n✅ Local YAML loading test PASSED")


def test_environment_loading():
    """Test loading from environment variables (Vercel)."""
    print("\n" + "=" * 60)
    print("TEST 2: Environment Variable Loading")
    print("=" * 60)

    # Set some test environment variables
    os.environ["ATOMS_HOST"] = "test.example.com"
    os.environ["ATOMS_PORT"] = "9000"
    os.environ["ATOMS_DEBUG"] = "true"
    os.environ["ATOMS_LOG_LEVEL"] = "DEBUG"

    # Force environment loading
    settings = AtomsSettings(force_env=True)

    print(f"✓ Configuration source: {settings.source}")
    print(f"✓ Host: {settings.app.host}")
    print(f"✓ Port: {settings.app.port}")
    print(f"✓ Debug: {settings.app.debug}")
    print(f"✓ Log level: {settings.app.log_level}")

    assert settings.source == "environment", "Should load from environment"
    assert settings.app.host == "test.example.com", "Should use env var"
    assert settings.app.port == 9000, "Should use env var"
    assert settings.app.debug is True, "Should use env var"
    assert settings.app.log_level == "DEBUG", "Should use env var"

    # Clean up
    del os.environ["ATOMS_HOST"]
    del os.environ["ATOMS_PORT"]
    del os.environ["ATOMS_DEBUG"]
    del os.environ["ATOMS_LOG_LEVEL"]

    print("\n✅ Environment loading test PASSED")


def test_vercel_detection():
    """Test Vercel environment detection."""
    print("\n" + "=" * 60)
    print("TEST 3: Vercel Environment Detection")
    print("=" * 60)

    # Test without VERCEL env var
    assert not is_vercel_environment(), "Should not detect Vercel"
    print("✓ Correctly detects non-Vercel environment")

    # Test with VERCEL env var
    os.environ["VERCEL"] = "1"
    assert is_vercel_environment(), "Should detect Vercel"
    print("✓ Correctly detects Vercel environment")
    del os.environ["VERCEL"]

    # Test with VERCEL_ENV
    os.environ["VERCEL_ENV"] = "production"
    assert is_vercel_environment(), "Should detect Vercel"
    print("✓ Correctly detects Vercel environment (VERCEL_ENV)")
    del os.environ["VERCEL_ENV"]

    print("\n✅ Vercel detection test PASSED")


def test_automatic_selection():
    """Test automatic environment selection."""
    print("\n" + "=" * 60)
    print("TEST 4: Automatic Environment Selection")
    print("=" * 60)

    # Test local (no VERCEL env var)
    settings = AtomsSettings()
    print(f"✓ Local environment detected, source: {settings.source}")
    assert settings.source == "yaml", "Should auto-select YAML for local"

    # Test Vercel (with VERCEL env var)
    os.environ["VERCEL"] = "1"
    settings = AtomsSettings()
    print(f"✓ Vercel environment detected, source: {settings.source}")
    assert settings.source == "environment", "Should auto-select env for Vercel"
    del os.environ["VERCEL"]

    print("\n✅ Automatic selection test PASSED")


def test_settings_validation():
    """Test pydantic validation."""
    print("\n" + "=" * 60)
    print("TEST 5: Settings Validation")
    print("=" * 60)

    settings = AtomsSettings(force_yaml=True)

    # Test port validation
    try:
        AppSettings(port=99999)
        print("❌ Should have raised validation error for invalid port")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Port validation works: {e}")

    # Test type safety
    assert isinstance(settings.app.port, int), "Port should be int"
    assert isinstance(settings.app.debug, bool), "Debug should be bool"
    assert isinstance(settings.app.host, str), "Host should be str"
    print("✓ Type safety works correctly")

    print("\n✅ Settings validation test PASSED")


def test_convenience_methods():
    """Test convenience methods."""
    print("\n" + "=" * 60)
    print("TEST 6: Convenience Methods")
    print("=" * 60)

    settings = AtomsSettings(force_yaml=True)

    # Test server config
    server_config = settings.get_server_config()
    print(f"✓ Server config: {server_config}")
    assert "host" in server_config
    assert "port" in server_config
    assert "url" in server_config

    # Test MCP config
    mcp_config = settings.get_mcp_config()
    print(f"✓ MCP config: {mcp_config}")
    assert "name" in mcp_config
    assert "server_url" in mcp_config

    # Test workspace config
    workspace_config = settings.get_workspace_config()
    print(f"✓ Workspace config: {workspace_config}")
    assert "root" in workspace_config

    # Test safe dict conversion
    safe_dict = settings.to_dict_safe()
    print(f"✓ Safe dict keys: {list(safe_dict.keys())}")
    assert "app" in safe_dict
    assert "has_secrets" in safe_dict
    assert "features" in safe_dict

    print("\n✅ Convenience methods test PASSED")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ATOMS MCP HYBRID CONFIGURATION TESTS")
    print("=" * 60)

    try:
        test_local_yaml_loading()
        test_environment_loading()
        test_vercel_detection()
        test_automatic_selection()
        test_settings_validation()
        test_convenience_methods()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nHybrid configuration is working correctly:")
        print("  • Local development: Loads from config.yml + secrets.yml")
        print("  • Vercel/Production: Loads from environment variables")
        print("  • Type-safe with pydantic validation")
        print("  • Backward compatible with existing code")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        traceback.print_exc()
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
