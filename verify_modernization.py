#!/usr/bin/env python3
"""
Verification script for Atoms MCP modernization.

This script validates that all modernization changes are working correctly.
"""

import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} MISSING: {filepath}")
        return False


def check_yaml_valid(filepath: str, description: str) -> bool:
    """Check if a YAML file is valid."""
    import yaml

    try:
        with open(filepath) as f:
            yaml.safe_load(f)
        print(f"✅ {description} is valid")
        return True
    except Exception as e:
        print(f"❌ {description} is invalid: {e}")
        return False


def check_toml_valid(filepath: str, description: str) -> bool:
    """Check if a TOML file is valid."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    try:
        with open(filepath, "rb") as f:
            tomllib.load(f)
        print(f"✅ {description} is valid")
        return True
    except Exception as e:
        print(f"❌ {description} is invalid: {e}")
        return False


def check_settings_load() -> bool:
    """Check if settings can be loaded."""
    try:
        from config.settings import get_settings

        settings = get_settings()
        print(f"✅ Settings loaded successfully")
        print(f"   - Server port: {settings.server.port}")
        print(f"   - KINFRA enabled: {settings.kinfra.enabled}")
        print(f"   - Features RAG: {settings.features.enable_rag}")
        return True
    except Exception as e:
        print(f"❌ Settings loading failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("="*60)
    print("Atoms MCP Modernization Verification")
    print("="*60)
    print()

    results = []

    # 1. Check configuration files
    print("1. Configuration Files")
    print("-" * 60)
    results.append(check_file_exists("config/schema.yaml", "Settings schema"))
    results.append(check_file_exists("config/config.yaml", "Default config"))
    results.append(check_file_exists("config/settings.py", "Settings module"))
    results.append(check_yaml_valid("config/schema.yaml", "schema.yaml"))
    results.append(check_yaml_valid("config/config.yaml", "config.yaml"))
    print()

    # 2. Check pyproject.toml
    print("2. pyproject.toml")
    print("-" * 60)
    results.append(check_file_exists("pyproject.toml", "pyproject.toml"))
    results.append(check_toml_valid("pyproject.toml", "pyproject.toml"))
    print()

    # 3. Check ignore files
    print("3. Ignore Files")
    print("-" * 60)
    results.append(check_file_exists(".gitignore", "Git ignore"))
    results.append(check_file_exists(".dockerignore", "Docker ignore"))
    results.append(check_file_exists(".clocignore", "CLOC ignore"))
    results.append(check_file_exists(".vultureignore", "Vulture ignore"))
    results.append(check_file_exists(".pylintignore", "Pylint ignore"))
    print()

    # 4. Check toolchain files
    print("4. Toolchain Configuration")
    print("-" * 60)
    results.append(check_file_exists(".pre-commit-config.yaml", "Pre-commit config"))
    results.append(check_file_exists("tox.ini", "Tox config"))
    results.append(check_yaml_valid(".pre-commit-config.yaml", "pre-commit-config.yaml"))
    print()

    # 5. Check settings loading
    print("5. Settings Loading")
    print("-" * 60)
    results.append(check_settings_load())
    print()

    # Summary
    print("="*60)
    print("Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All verification checks passed!")
        return 0
    else:
        print(f"❌ {total - passed} checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
