"""Adapter-Kit: Architecture patterns for clean code."""

from .di.container import Container, get_container, inject
from .factories.base import Factory, Registry
from .repositories.base import Repository, InMemoryRepository

__version__ = "0.1.0"

__all__ = [
    "Container",
    "get_container",
    "inject",
    "Factory",
    "Registry",
    "Repository",
    "InMemoryRepository",
]