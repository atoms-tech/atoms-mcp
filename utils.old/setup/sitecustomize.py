"""
Minimal site customization for Atoms MCP.

Ensures a sibling checkout of pheno-sdk is importable during local
development. Vendored package support has been removed in favour of
installing pheno-sdk directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_PHENO_SRC = PROJECT_ROOT / "pheno-sdk" / "src"

if LOCAL_PHENO_SRC.exists():
    local_path = str(LOCAL_PHENO_SRC)
    if local_path not in sys.path:
        sys.path.insert(0, local_path)
