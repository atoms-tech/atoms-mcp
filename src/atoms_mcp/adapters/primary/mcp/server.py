"""
FastMCP server for Atoms MCP.

This module provides the MCP server implementation using FastMCP SDK.
It registers all tools and handles MCP protocol communication.
"""

import logging
import os
import sys
from typing import Any, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import RequestError, ToolError

from ....application.commands import (
    EntityCommandHandler,
    RelationshipCommandHandler,
    WorkflowCommandHandler,
)
from ....application.queries import (
    AnalyticsQueryHandler,
    EntityQueryHandler,
    RelationshipQueryHandler,
)
from ....domain.models.entity import Entity
from ....domain.models.relationship import Relationship
from ....infrastructure.adapters.cache_adapter import InMemoryCache
from ....infrastructure.adapters.logger_adapter import PythonLogger
from ....infrastructure.adapters.repository_adapter import SupabaseRepository
from .tools import entity_tools, query_tools, relationship_tools, workflow_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


class AtomsServer:
    """
    Atoms MCP Server.

    This class encapsulates the FastMCP server and all dependencies.
    It provides methods for initialization, tool registration, and server lifecycle.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        use_cache: bool = True,
        log_level: str = "INFO",
    ):
        """
        Initialize Atoms MCP server.

        Args:
            supabase_url: Supabase URL (defaults to SUPABASE_URL env var)
            supabase_key: Supabase key (defaults to SUPABASE_KEY env var)
            use_cache: Whether to enable caching
            log_level: Logging level
        """
        # Setup environment
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            logger.warning(
                "Supabase credentials not provided. Using in-memory repositories."
            )

        # Setup logging
        logging.getLogger().setLevel(getattr(logging, log_level.upper()))
        self.logger = PythonLogger("atoms-mcp")

        # Setup cache
        self.cache = InMemoryCache() if use_cache else None

        # Initialize repositories
        self._init_repositories()

        # Initialize command and query handlers
        self._init_handlers()

        # Initialize FastMCP server
        self.mcp = FastMCP(
            "Atoms MCP Server",
            version="0.1.0",
            dependencies=["fastmcp>=2.13.0.1"],
        )

        # Register tools
        self._register_tools()

        logger.info("Atoms MCP Server initialized successfully")

    def _init_repositories(self) -> None:
        """Initialize repositories for entities and relationships."""
        if self.supabase_url and self.supabase_key:
            # Use Supabase repositories
            self.entity_repository = SupabaseRepository[Entity](
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key,
                table_name="entities",
                logger=self.logger,
            )
            self.relationship_repository = SupabaseRepository[Relationship](
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key,
                table_name="relationships",
                logger=self.logger,
            )
        else:
            # Use in-memory repositories for development
            from ....infrastructure.adapters.repository_adapter import (
                InMemoryRepository,
            )

            self.entity_repository = InMemoryRepository[Entity](logger=self.logger)
            self.relationship_repository = InMemoryRepository[Relationship](
                logger=self.logger
            )

    def _init_handlers(self) -> None:
        """Initialize command and query handlers."""
        # Command handlers
        self.entity_command_handler = EntityCommandHandler(
            repository=self.entity_repository,
            logger=self.logger,
            cache=self.cache,
        )
        self.relationship_command_handler = RelationshipCommandHandler(
            repository=self.relationship_repository,
            logger=self.logger,
            cache=self.cache,
        )
        self.workflow_command_handler = WorkflowCommandHandler(
            entity_repository=self.entity_repository,
            relationship_repository=self.relationship_repository,
            logger=self.logger,
        )

        # Query handlers
        self.entity_query_handler = EntityQueryHandler(
            repository=self.entity_repository,
            logger=self.logger,
            cache=self.cache,
        )
        self.relationship_query_handler = RelationshipQueryHandler(
            repository=self.relationship_repository,
            logger=self.logger,
            cache=self.cache,
        )
        self.analytics_query_handler = AnalyticsQueryHandler(
            entity_repository=self.entity_repository,
            relationship_repository=self.relationship_repository,
            logger=self.logger,
            cache=self.cache,
        )

    def _register_tools(self) -> None:
        """Register all MCP tools with the server."""
        logger.info("Registering MCP tools...")

        # Register entity tools
        entity_tools.register_entity_tools(self.mcp, self)

        # Register relationship tools
        relationship_tools.register_relationship_tools(self.mcp, self)

        # Register query tools
        query_tools.register_query_tools(self.mcp, self)

        # Register workflow tools
        workflow_tools.register_workflow_tools(self.mcp, self)

        logger.info(
            f"Registered {len(self.mcp.list_tools())} tools successfully"
        )

    def run(self, transport: str = "stdio") -> None:
        """
        Run the MCP server.

        Args:
            transport: Transport type ('stdio' or 'sse')
        """
        logger.info(f"Starting Atoms MCP Server with {transport} transport")

        if transport == "stdio":
            self.mcp.run()
        elif transport == "sse":
            # SSE transport for web-based clients
            import uvicorn

            app = self.mcp.get_asgi_app()
            uvicorn.run(app, host="0.0.0.0", port=8000)
        else:
            raise ValueError(f"Unknown transport: {transport}")

    def handle_error(self, error: Exception) -> dict[str, Any]:
        """
        Handle and format errors for MCP responses.

        Args:
            error: Exception to handle

        Returns:
            Error response dictionary
        """
        if isinstance(error, ToolError):
            return {
                "error": "tool_error",
                "message": str(error),
                "details": getattr(error, "details", {}),
            }
        elif isinstance(error, RequestError):
            return {
                "error": "request_error",
                "message": str(error),
                "code": getattr(error, "code", "unknown"),
            }
        else:
            logger.exception("Unexpected error in MCP server")
            return {
                "error": "internal_error",
                "message": "An internal error occurred",
                "details": str(error),
            }


def create_server(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    use_cache: bool = True,
    log_level: str = "INFO",
) -> AtomsServer:
    """
    Factory function to create Atoms MCP server.

    Args:
        supabase_url: Supabase URL
        supabase_key: Supabase key
        use_cache: Whether to enable caching
        log_level: Logging level

    Returns:
        Configured AtomsServer instance
    """
    return AtomsServer(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        use_cache=use_cache,
        log_level=log_level,
    )


def main() -> None:
    """Main entry point for the MCP server."""
    # Get configuration from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    use_cache = os.getenv("USE_CACHE", "true").lower() == "true"

    # Create and run server
    try:
        server = create_server(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            use_cache=use_cache,
            log_level=log_level,
        )
        server.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Server failed to start")
        sys.exit(1)


if __name__ == "__main__":
    main()


__all__ = ["AtomsServer", "create_server", "main"]
