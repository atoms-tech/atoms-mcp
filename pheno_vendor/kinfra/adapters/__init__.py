"""
Resource Adapters - Generic patterns for managing any system resource

Provides adapter-based architecture for extensible resource management.
"""

from .base import ResourceAdapter, HealthCheckStrategy
from .docker import DockerAdapter
from .daemon import SystemDaemonAdapter
from .command import CommandAdapter
from .api import APIAdapter
from .factory import ResourceFactory, resource_from_dict

__all__ = [
    'ResourceAdapter',
    'HealthCheckStrategy',
    'DockerAdapter',
    'SystemDaemonAdapter',
    'CommandAdapter',
    'APIAdapter',
    'ResourceFactory',
    'resource_from_dict',
]
