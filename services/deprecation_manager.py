"""Deprecation Manager for Atoms MCP - Manage deprecated APIs.

Provides deprecation warnings, migration tracking, and timeline management.
"""

import logging
import warnings
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class DeprecationLevel(Enum):
    """Deprecation levels."""
    WARNING = "warning"
    CRITICAL = "critical"
    REMOVED = "removed"


class DeprecationManager:
    """Manage deprecated APIs and migration."""

    def __init__(self):
        """Initialize deprecation manager."""
        self.deprecated_apis = {}
        self._setup_deprecations()

    def _setup_deprecations(self) -> None:
        """Setup deprecated APIs."""
        # Phase 2: Deprecate query_tool
        self.deprecated_apis["query_tool"] = {
            "name": "query_tool",
            "replacement": "entity_tool",
            "level": DeprecationLevel.WARNING,
            "deprecated_date": datetime.now().isoformat(),
            "removal_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "migration_guide": "https://docs.atoms.tech/migration/query-tool",
            "reason": "Consolidated into entity_tool for unified API"
        }

    def warn_deprecated(
        self,
        api_name: str,
        replacement: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        """Warn about deprecated API usage.
        
        Args:
            api_name: Name of deprecated API
            replacement: Replacement API name
            message: Custom warning message
        """
        if api_name not in self.deprecated_apis:
            return

        deprecation = self.deprecated_apis[api_name]
        replacement = replacement or deprecation.get("replacement")

        if message is None:
            message = (
                f"'{api_name}' is deprecated and will be removed on "
                f"{deprecation['removal_date']}. "
                f"Use '{replacement}' instead. "
                f"Migration guide: {deprecation['migration_guide']}"
            )

        # Log warning
        logger.warning(f"DEPRECATION: {message}")

        # Issue Python warning
        warnings.warn(message, DeprecationWarning, stacklevel=3)

    def get_deprecation_info(self, api_name: str) -> Optional[Dict[str, Any]]:
        """Get deprecation information for API.
        
        Args:
            api_name: Name of API
            
        Returns:
            Deprecation info dict or None
        """
        return self.deprecated_apis.get(api_name)

    def is_deprecated(self, api_name: str) -> bool:
        """Check if API is deprecated.
        
        Args:
            api_name: Name of API
            
        Returns:
            True if deprecated, False otherwise
        """
        return api_name in self.deprecated_apis

    def get_all_deprecations(self) -> Dict[str, Dict[str, Any]]:
        """Get all deprecations.
        
        Returns:
            Dict of all deprecations
        """
        return self.deprecated_apis.copy()

    def add_deprecation(
        self,
        api_name: str,
        replacement: str,
        level: DeprecationLevel = DeprecationLevel.WARNING,
        removal_days: int = 90,
        migration_guide: str = "",
        reason: str = ""
    ) -> None:
        """Add new deprecation.
        
        Args:
            api_name: Name of API to deprecate
            replacement: Replacement API name
            level: Deprecation level
            removal_days: Days until removal
            migration_guide: URL to migration guide
            reason: Reason for deprecation
        """
        self.deprecated_apis[api_name] = {
            "name": api_name,
            "replacement": replacement,
            "level": level,
            "deprecated_date": datetime.now().isoformat(),
            "removal_date": (datetime.now() + timedelta(days=removal_days)).isoformat(),
            "migration_guide": migration_guide,
            "reason": reason
        }

        logger.info(f"Added deprecation for '{api_name}': {reason}")

    def get_migration_guide(self, api_name: str) -> Optional[str]:
        """Get migration guide URL for API.
        
        Args:
            api_name: Name of API
            
        Returns:
            Migration guide URL or None
        """
        deprecation = self.get_deprecation_info(api_name)
        if deprecation:
            return deprecation.get("migration_guide")
        return None

    def get_removal_date(self, api_name: str) -> Optional[str]:
        """Get removal date for API.
        
        Args:
            api_name: Name of API
            
        Returns:
            Removal date or None
        """
        deprecation = self.get_deprecation_info(api_name)
        if deprecation:
            return deprecation.get("removal_date")
        return None

    def get_replacement(self, api_name: str) -> Optional[str]:
        """Get replacement API for deprecated API.
        
        Args:
            api_name: Name of deprecated API
            
        Returns:
            Replacement API name or None
        """
        deprecation = self.get_deprecation_info(api_name)
        if deprecation:
            return deprecation.get("replacement")
        return None


# Global deprecation manager instance
_deprecation_manager = None


def get_deprecation_manager() -> DeprecationManager:
    """Get global deprecation manager instance."""
    global _deprecation_manager
    if _deprecation_manager is None:
        _deprecation_manager = DeprecationManager()
    return _deprecation_manager

