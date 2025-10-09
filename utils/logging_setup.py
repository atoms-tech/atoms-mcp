"""
Atoms MCP Logging Setup

Backward-compatible wrapper for new mcp_qa.utils.logging_utils.
Migrated to use consolidated utilities from pheno-SDK.

Usage:
    from utils.logging_setup import setup_logging, get_logger
    
    # In main/server startup:
    setup_logging()
    
    # In modules:
    logger = get_logger(__name__)
    logger.info("Starting server")
    logger.error("Failed to connect", exc_info=True)

Note: This is now a thin wrapper around mcp_qa.utils.logging_utils.
      New code should import directly from mcp_qa.utils.
"""

import sys
import logging
from pathlib import Path

# Add pheno-sdk/mcp-QA to path  
_repo_root = Path(__file__).resolve().parents[2]
_mcp_qa_path = _repo_root / "pheno-sdk" / "mcp-QA"
if _mcp_qa_path.exists():
    sys.path.insert(0, str(_mcp_qa_path))

try:
    from mcp_qa.utils import configure_logging as _configure_logging, get_logger as _get_logger
    HAS_NEW_UTILS = True
except ImportError:
    HAS_NEW_UTILS = False


def setup_logging(level: str = "INFO", use_color: bool = True, use_timestamps: bool = True):
    """
    Configure logging for Atoms MCP.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        use_color: Enable colored output (ignored, for backward compatibility)
        use_timestamps: Show timestamps in logs (ignored, for backward compatibility)
    
    Note: Now uses mcp_qa.utils.configure_logging with standard format.
    """
    if HAS_NEW_UTILS:
        # Map string level to logging constant
        log_level = getattr(logging, level.upper(), logging.INFO)
        _configure_logging(level=log_level)
    else:
        # Fallback to basic logging if mcp-QA not available
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        )


def get_logger(name: str):
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance with standard logging methods
    
    Example:
        logger = get_logger(__name__)
        logger.info("Entity created")
        logger.error("Failed", exc_info=True)
    """
    if HAS_NEW_UTILS:
        return _get_logger(name)
    else:
        # Fallback to standard logger
        return logging.getLogger(name)


# Export for convenience
__all__ = ["setup_logging", "get_logger"]
