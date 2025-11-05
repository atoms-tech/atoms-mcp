#!/usr/bin/env python3
"""
Simple test runner that bypasses hypothesis library issues.
Directly runs pytest without importing hypothesis.
"""

import subprocess
import sys
import os

# Change to project directory
os.chdir("/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod")

# Run pytest with hypothesis plugin disabled and without importing it
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "tests/unit_refactor/",
    "-v",
    "--tb=short",
    "-p", "no:hypothesis",
    "--override-ini=addopts=",  # Override default addopts that might include hypothesis
    "--cov=src/atoms_mcp",
    "--cov-report=term-missing",
], env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

sys.exit(result.returncode)
