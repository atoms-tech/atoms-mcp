"""Migration data structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Optional


class MigrationStatus(str, Enum):
    """Migration status."""
    
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Database migration."""
    
    version: str
    name: str
    up: Callable
    down: Optional[Callable] = None
    applied_at: Optional[datetime] = None
    status: MigrationStatus = MigrationStatus.PENDING
    checksum: Optional[str] = None
    
    def get_id(self) -> str:
        """Get migration ID.
        
        Returns:
            Migration ID (version_name)
        """
        return f"{self.version}_{self.name}"
