"""
Atoms MCP Configuration

Project-specific configuration that uses pheno-sdk generic components.

This module provides factory functions for all infrastructure components:
- Database, Storage, Realtime (from pheno-sdk/db-kit)
- Auth (Atoms-specific)
- Rate Limiting (from pheno-sdk/observability-kit)
- Session Management (from pheno-sdk/authkit-client)
- Vector Search & Embeddings (from pheno-sdk/vector-kit)
"""

from .infrastructure import (
    get_auth_adapter,
    get_database_adapter,
    get_rate_limiter,
    get_realtime_adapter,
    get_storage_adapter,
)
from .session import get_session_manager
from .settings import AppSettings, get_settings, reset_settings_cache
from .vector import (
    get_embedding_service,
    get_enhanced_vector_search_service,
    get_progressive_embedding_service,
    get_vector_search_service,
)

__all__ = [
    # Infrastructure
    "get_database_adapter",
    "get_auth_adapter",
    "get_storage_adapter",
    "get_realtime_adapter",
    "get_rate_limiter",

    # Session
    "get_session_manager",

    # Vector & Embeddings
    "get_embedding_service",
    "get_vector_search_service",
    "get_enhanced_vector_search_service",
    "get_progressive_embedding_service",
    # Settings
    "AppSettings",
    "get_settings",
    "reset_settings_cache",
]
