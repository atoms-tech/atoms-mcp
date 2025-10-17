"""
Session management configuration for Atoms MCP.

Creates and configures session manager using pheno-sdk authkit-client.
"""

import sys
from pathlib import Path

# Add pheno-sdk to path
_repo_root = Path(__file__).resolve().parents[2]
_authkit_path = _repo_root / "pheno-sdk" / "authkit-client"

if _authkit_path.exists():
    sys.path.insert(0, str(_authkit_path))

# Import from pheno-sdk with fallback
try:
    from authkit_client.session import DatabaseSessionStore, SessionManager  # noqa: E402
except ImportError:
    DatabaseSessionStore = None
    SessionManager = None

# Import Atoms-specific components
try:
    from supabase_client import get_supabase  # noqa: E402
except ImportError:
    get_supabase = None

try:
    from utils.logging_setup import get_logger  # noqa: E402
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# Singleton instance
_session_manager = None


def get_session_manager():
    """
    Get configured session manager.

    Uses pheno-sdk's SessionManager with DatabaseSessionStore.

    Returns:
        Configured SessionManager
    """
    global _session_manager

    if _session_manager is None:
        if SessionManager and DatabaseSessionStore and get_supabase:
            supabase = get_supabase()
            store = DatabaseSessionStore(
                db_client=supabase,
                table_name="sessions",
                logger=logger,
            )
            _session_manager = SessionManager(
                store=store,
                session_ttl_hours=24,
                logger=logger,
            )
            logger.info("Initialized SessionManager with DatabaseSessionStore (pheno-sdk)")
        else:
            raise RuntimeError("SessionManager not available - authkit-client or dependencies not installed")

    return _session_manager


def reset_session_manager():
    """
    Reset session manager singleton.

    Useful for testing or when configuration changes.

    Examples:
        >>> from config.session import reset_session_manager
        >>> reset_session_manager()
    """
    global _session_manager
    _session_manager = None

