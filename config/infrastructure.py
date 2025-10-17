"""
Infrastructure configuration for Atoms MCP.

Creates and configures infrastructure components using pheno-sdk libraries.

This module provides factory functions for creating infrastructure components:
- Database: Supabase adapter with RLS and caching (from pheno-sdk/db-kit)
- Storage: Supabase storage adapter (from pheno-sdk/db-kit)
- Realtime: Supabase realtime subscriptions (from pheno-sdk/db-kit)
- Auth: Supabase auth adapter (from pheno-sdk/authkit-client)
- Rate Limiting: Token bucket rate limiter (from pheno-sdk/observability-kit)
"""

import sys
from pathlib import Path

# Add pheno-sdk to path
_repo_root = Path(__file__).resolve().parents[2]
_adapter_kit_path = _repo_root / "pheno-sdk" / "adapter-kit"
_observability_kit_path = _repo_root / "pheno-sdk" / "observability-kit"
_db_kit_path = _repo_root / "pheno-sdk" / "db-kit"
_authkit_client_path = _repo_root / "pheno-sdk" / "authkit-client"

if _adapter_kit_path.exists():
    sys.path.insert(0, str(_adapter_kit_path))
if _observability_kit_path.exists():
    sys.path.insert(0, str(_observability_kit_path))
if _db_kit_path.exists():
    sys.path.insert(0, str(_db_kit_path))
if _authkit_client_path.exists():
    sys.path.insert(0, str(_authkit_client_path))

# Import from pheno-sdk
try:
    from db_kit import SupabaseAdapter, SupabaseRealtimeAdapter, SupabaseStorageAdapter  # noqa: E402
except ImportError:
    try:
        from adapters import DatabaseAdapter, RealtimeAdapter, StorageAdapter  # noqa: E402
    except ImportError:
        # Fallback: define minimal adapters
        DatabaseAdapter = None
        RealtimeAdapter = None
        StorageAdapter = None

# Import Atoms-specific auth implementation (not in pheno-sdk)
try:
    from authkit_client import SupabaseAuthAdapter  # noqa: E402
except ImportError:
    SupabaseAuthAdapter = None

try:
    from observability.rate_limiting import TokenBucketRateLimiter  # noqa: E402
except ImportError:
    TokenBucketRateLimiter = None

from .settings import get_settings

# Singleton instances
_database_adapter = None
_auth_adapter = None
_storage_adapter = None
_realtime_adapter = None
_rate_limiter = None


def get_database_adapter():
    """
    Get configured database adapter.

    Uses pheno-sdk's SupabaseAdapter with caching and RLS support.

    Returns:
        SupabaseAdapter configured for Atoms MCP

    Examples:
        >>> from config import get_database_adapter
        >>> db = get_database_adapter()
        >>> result = await db.query("organizations", filters={"id": "org-123"})
    """
    global _database_adapter

    if _database_adapter is None:
        if SupabaseAdapter:
            _database_adapter = SupabaseAdapter(cache_ttl=30)
        else:
            raise RuntimeError("SupabaseAdapter not available - db_kit not installed")

    return _database_adapter


def get_auth_adapter():
    """
    Get configured auth adapter.

    Note: Auth adapter is Atoms-specific and not from pheno-sdk.

    Returns:
        SupabaseAuthAdapter configured for Atoms MCP

    Examples:
        >>> from config import get_auth_adapter
        >>> auth = get_auth_adapter()
        >>> user = await auth.get_user(access_token)
    """
    global _auth_adapter

    if _auth_adapter is None:
        if SupabaseAuthAdapter:
            _auth_adapter = SupabaseAuthAdapter()
        else:
            raise RuntimeError("SupabaseAuthAdapter not available - authkit-client not installed")

    return _auth_adapter


def get_storage_adapter():
    """
    Get configured storage adapter.

    Uses pheno-sdk's SupabaseStorageAdapter.

    Returns:
        SupabaseStorageAdapter configured for Atoms MCP

    Examples:
        >>> from config import get_storage_adapter
        >>> storage = get_storage_adapter()
        >>> url = await storage.upload("bucket", "file.txt", data)
    """
    global _storage_adapter

    if _storage_adapter is None:
        if SupabaseStorageAdapter:
            _storage_adapter = SupabaseStorageAdapter()
        else:
            raise RuntimeError("SupabaseStorageAdapter not available - db_kit not installed")

    return _storage_adapter


def get_realtime_adapter():
    """
    Get configured realtime adapter.

    Uses pheno-sdk's SupabaseRealtimeAdapter for real-time subscriptions.

    Returns:
        SupabaseRealtimeAdapter configured for Atoms MCP

    Examples:
        >>> from config import get_realtime_adapter
        >>> realtime = get_realtime_adapter()
        >>> sub_id = await realtime.subscribe("organizations", callback)
    """
    global _realtime_adapter

    if _realtime_adapter is None:
        if SupabaseRealtimeAdapter:
            _realtime_adapter = SupabaseRealtimeAdapter()
        else:
            raise RuntimeError("SupabaseRealtimeAdapter not available - db_kit not installed")

    return _realtime_adapter


def get_rate_limiter(requests_per_minute=None, burst_size=None):
    """
    Get configured rate limiter.

    Uses pheno-sdk's TokenBucketRateLimiter.

    Args:
        requests_per_minute: Sustained rate limit (defaults to settings value)
        burst_size: Maximum burst size (defaults to 2x sustained rate)

    Returns:
        Configured rate limiter

    Examples:
        >>> from config import get_rate_limiter
        >>> limiter = get_rate_limiter(requests_per_minute=100)
        >>> if await limiter.acquire("user123"):
        ...     # Process request
        ...     pass
    """
    global _rate_limiter

    if _rate_limiter is None:
        if TokenBucketRateLimiter:
            if requests_per_minute is None:
                requests_per_minute = get_settings().rate_limit_rpm
            _rate_limiter = TokenBucketRateLimiter(
                requests_per_minute=requests_per_minute,
                burst_size=burst_size
            )
        else:
            raise RuntimeError("TokenBucketRateLimiter not available - observability-kit not installed")

    return _rate_limiter


def reset_infrastructure():
    """
    Reset all infrastructure singletons.

    Useful for testing or when configuration changes.

    Examples:
        >>> from config.infrastructure import reset_infrastructure
        >>> reset_infrastructure()
    """
    global _database_adapter, _auth_adapter, _storage_adapter, _realtime_adapter, _rate_limiter

    _database_adapter = None
    _auth_adapter = None
    _storage_adapter = None
    _realtime_adapter = None
    _rate_limiter = None
