"""
Atoms MCP Server with Hexagonal Architecture

Clean separation of concerns using hexagonal architecture pattern.
Implements Domain-Driven Design with dependency inversion.
"""

__version__ = "2.0.0"

# Optional: export key classes for convenience
try:
    from .domain.models import Entity, Workspace
    from .domain.services import EntityService
    from .application.commands import CreateEntityCommand
    from .infrastructure.config import get_settings

    __all__ = [
        "__version__",
        "Entity",
        "Workspace",
        "EntityService",
        "CreateEntityCommand",
        "get_settings",
    ]
except ImportError:
    # If imports fail, just provide version
    __all__ = ["__version__"]
