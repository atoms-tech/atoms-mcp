"""Factory helpers for Atoms MCP infrastructure adapters.

All adapters are sourced from pheno-sdk implementations with
minimal project-specific customization (Supabase auth).
"""

from __future__ import annotations

from typing import Any, Dict

from config.infrastructure import (
    get_auth_adapter,
    get_database_adapter,
    get_rate_limiter,
    get_realtime_adapter,
    get_storage_adapter,
)


def get_adapters() -> Dict[str, Any]:
    """Return shared infrastructure adapters."""
    return {
        "database": get_database_adapter(),
        "auth": get_auth_adapter(),
        "storage": get_storage_adapter(),
        "realtime": get_realtime_adapter(),
        "rate_limiter": get_rate_limiter(),
    }


__all__ = ["get_adapters"]
