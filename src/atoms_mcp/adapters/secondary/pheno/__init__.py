"""
Pheno SDK adapter module with graceful fallback.

This module provides optional integration with pheno-sdk. If pheno-sdk
is not available, it gracefully falls back to standard library alternatives.

Usage:
    from atoms_mcp.adapters.secondary.pheno import get_logger, PHENO_AVAILABLE

    logger = get_logger(__name__)
    if PHENO_AVAILABLE:
        tunnel = get_tunnel_provider()
"""

from __future__ import annotations

import logging
from typing import Any, Optional

# Try to import pheno-sdk
PHENO_AVAILABLE = False
_pheno_logger = None
_pheno_tunnel = None

try:
    from pheno import Pheno
    from pheno.core.logging import PhenoLogger
    from pheno.tunnel import TunnelProvider

    PHENO_AVAILABLE = True
except ImportError:
    # Pheno-SDK not available, will use fallbacks
    Pheno = None
    PhenoLogger = None
    TunnelProvider = None


def get_logger(
    name: str,
    level: Optional[str] = None,
) -> logging.Logger:
    """
    Get a logger instance.

    If pheno-sdk is available, returns a Pheno logger.
    Otherwise, returns a standard library logger.

    Args:
        name: Logger name (typically __name__)
        level: Optional log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger instance (either Pheno or stdlib)
    """
    if PHENO_AVAILABLE and PhenoLogger:
        try:
            # Try to create Pheno logger
            from atoms_mcp.adapters.secondary.pheno.logger import PhenoLoggerAdapter

            return PhenoLoggerAdapter(name, level)
        except Exception:
            # Fall back to stdlib on any error
            pass

    # Use standard library logger
    logger = logging.getLogger(name)

    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
    elif not logger.handlers:
        # Set up basic configuration if not already configured
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    return logger


def get_tunnel_provider() -> Optional[Any]:
    """
    Get a tunnel provider instance.

    If pheno-sdk is available and configured, returns a TunnelProvider.
    Otherwise, returns None.

    Returns:
        TunnelProvider instance or None
    """
    if not PHENO_AVAILABLE or not TunnelProvider:
        return None

    try:
        from atoms_mcp.adapters.secondary.pheno.tunnel import get_pheno_tunnel
        from atoms_mcp.infrastructure.config.settings import get_settings

        settings = get_settings()

        # Only create tunnel if explicitly enabled
        if settings.pheno.tunnel_enabled:
            return get_pheno_tunnel()

        return None
    except Exception:
        # Return None on any error
        return None


def is_pheno_available() -> bool:
    """
    Check if pheno-sdk is available.

    Returns:
        True if pheno-sdk is installed and importable
    """
    return PHENO_AVAILABLE


def get_pheno_instance() -> Optional[Any]:
    """
    Get the global Pheno instance if available.

    Returns:
        Pheno instance or None
    """
    if not PHENO_AVAILABLE or not Pheno:
        return None

    try:
        from atoms_mcp.infrastructure.config.settings import get_settings

        settings = get_settings()

        if not settings.pheno.enabled:
            return None

        # Initialize Pheno if not already done
        pheno = Pheno()
        return pheno
    except Exception:
        return None


# Convenience exports
__all__ = [
    "PHENO_AVAILABLE",
    "get_logger",
    "get_tunnel_provider",
    "is_pheno_available",
    "get_pheno_instance",
]
