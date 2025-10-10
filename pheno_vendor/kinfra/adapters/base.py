"""
Base Resource Adapter - Abstract interface for resource management
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class HealthCheckStrategy(Enum):
    """Health check strategies."""
    TCP = "tcp"
    HTTP = "http"
    COMMAND = "command"
    CUSTOM = "custom"


@dataclass
class ResourceState:
    """Current state of a resource."""
    name: str
    running: bool = False
    healthy: bool = False
    pid: Optional[int] = None
    container_id: Optional[str] = None
    port: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ResourceAdapter(ABC):
    """
    Abstract base class for resource adapters.

    Adapters handle the specifics of starting, stopping, and monitoring
    different types of resources (Docker, systemd, processes, etc.).
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize adapter.

        Args:
            name: Resource name
            config: Resource-specific configuration
        """
        self.name = name
        self.config = config
        self.state = ResourceState(name=name)

    @abstractmethod
    async def start(self) -> bool:
        """
        Start the resource.

        Returns:
            True if started successfully
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the resource.

        Returns:
            True if stopped successfully
        """
        pass

    @abstractmethod
    async def is_running(self) -> bool:
        """
        Check if resource is running.

        Returns:
            True if running
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check if resource is healthy.

        Returns:
            True if healthy
        """
        pass

    async def restart(self) -> bool:
        """
        Restart the resource.

        Returns:
            True if restarted successfully
        """
        await self.stop()
        await asyncio.sleep(1.0)
        return await self.start()

    def get_state(self) -> ResourceState:
        """Get current resource state."""
        return self.state

    def update_state(self, **kwargs):
        """Update resource state fields."""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
