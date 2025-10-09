"""Canonical integration tests for Atoms MCP.

These tests exercise the production HTTP surface area using real Supabase
credentials and an AuthKit-configured MCP server.
Run with: pytest tests/test_end_to_end.py -v -s
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict

import httpx
import pytest

MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

pytestmark = [pytest.mark.asyncio, pytest.mark.http]

# Supabase JWT fixture removed - using AuthKit OAuth only