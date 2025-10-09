"""
Session management configuration for Atoms MCP.

Creates and configures session manager using pheno-sdk authkit-client.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add pheno-sdk to path
_repo_root = Path(__file__).resolve().parents[2]
_authkit_path = _repo_root / "pheno-sdk" / "authkit-client"

if _authkit_path.exists():
    sys.path.insert(0, str(_authkit_path))

# Import from pheno-sdk
from authkit_client.session import SessionManager, DatabaseSessionStore

# Import Atoms-specific components
from supabase_client import get_supabase
from utils.logging_setup import get_logger

logger = get_logger(__name__)


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get configured session manager.

    Uses pheno-sdk's SessionManager with DatabaseSessionStore.

    Returns:
        Configured SessionManager
    """
    global _session_manager

    if _session_manager is None:
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

