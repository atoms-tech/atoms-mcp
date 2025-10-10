"""Atoms MCP client adapter helper.

Thin wrapper around pheno-sdk/mcp-QA enhanced adapter utilities.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastmcp import Client

# Ensure pheno-sdk/mcp-QA is on path when running in isolation
_repo_root = Path(__file__).resolve().parents[2]
_mcp_qa_path = _repo_root / "pheno-sdk" / "mcp-QA"
if _mcp_qa_path.exists():
    sys.path.insert(0, str(_mcp_qa_path))

from mcp_qa.core import create_enhanced_adapter


def create_atoms_adapter(
    client: Client,
    *,
    verbose_on_fail: bool = True,
    use_color: bool = True,
    use_emoji: bool = True,
) -> Client:
    """Return the shared enhanced adapter used across projects."""
    return create_enhanced_adapter(
        client,
        verbose_on_fail=verbose_on_fail,
        use_color=use_color,
        use_emoji=use_emoji,
    )


__all__ = ["create_atoms_adapter"]
