"""
Core MCP server creation and configuration.

This module provides the main server factory function that creates and
configures the FastMCP server with all tools and authentication.

Pythonic Patterns Applied:
- Type hints throughout
- Dataclass for server configuration
- Builder pattern for server creation
- Dependency injection for rate limiter
- Context managers for resource management
"""

from __future__ import annotations

from dataclasses import dataclass

from fastmcp import FastMCP
from fastmcp.server.auth.providers.workos import AuthKitProvider

from config.settings import AppSettings, get_settings
from utils.logging_setup import get_logger

from .auth import RateLimiter
from .env import get_fastmcp_vars, load_env_files

logger = get_logger("atoms_fastmcp.core")


# Global rate limiter instance (will be set during server creation)
_rate_limiter: RateLimiter | None = None


@dataclass
class ServerConfig:
    """Configuration for MCP server.

    Attributes:
        name: Server name
        base_url: Base URL for the server
        authkit_domain: AuthKit domain for OAuth
        authkit_required_scopes: Optional OAuth scopes for AuthKit
        rate_limit_rpm: Rate limit in requests per minute
        transport: Transport type (stdio or http)
        host: Host for HTTP transport
        port: Port for HTTP transport
        http_path: Path for HTTP transport
    """
    name: str = "atoms-fastmcp-consolidated"
    base_url: str | None = None
    authkit_domain: str | None = None
    authkit_required_scopes: tuple[str, ...] = ()
    rate_limit_rpm: int = 120
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    http_path: str = "/api/mcp"

    @classmethod
    def from_env(cls) -> ServerConfig:
        """Create configuration from environment variables.

        Returns:
            ServerConfig instance

        Examples:
            >>> config = ServerConfig.from_env()
            >>> print(config.base_url)
        """
        settings = get_settings()
        return cls.from_settings(settings)

    @classmethod
    def from_settings(cls, settings: AppSettings | None = None) -> ServerConfig:
        """Create configuration from an AppSettings instance."""
        if settings is None:
            settings = get_settings()

        # Get environment variables
        fastmcp_vars = get_fastmcp_vars()

        # Create instance with settings from fastmcp config
        config = cls(
            transport=settings.fastmcp.transport,
            host=settings.fastmcp.host,
            port=settings.fastmcp.port,
            http_path=settings.fastmcp.http_path,
            base_url=settings.fastmcp.base_url,
        )

        # Override with environment variables if present
        if "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN" in fastmcp_vars:
            config.authkit_domain = fastmcp_vars["FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN"]

        return config


def _initialize_rate_limiter(config: ServerConfig) -> RateLimiter | None:
    """Initialize rate limiter for API protection.

    Args:
        config: Server configuration

    Returns:
        RateLimiter instance or None
    """
    try:
        # Try to use pheno-sdk observability instead
        from pheno.dev.rate_limiting import SlidingWindowRateLimiter

        limiter = SlidingWindowRateLimiter(
            window_seconds=60,
            max_requests=config.rate_limit_rpm
        )
        logger.info(f"✅ Rate limiter configured: {config.rate_limit_rpm} requests/minute")
        return limiter
    except ImportError:
        try:
            # Fallback to observability module if available
            from pheno.dev.rate_limiting import SlidingWindowRateLimiter

            limiter = SlidingWindowRateLimiter(
                window_seconds=60,
                max_requests=config.rate_limit_rpm
            )
            logger.info(f"✅ Rate limiter configured: {config.rate_limit_rpm} requests/minute")
            return limiter
        except ImportError as e:
            if "observability" in str(e):
                logger.info("ℹ️  Rate limiter not available (observability module not installed)")
            else:
                logger.warning(f"Rate limiter not available: {e}")
            return None


def _create_auth_provider(config: ServerConfig):
    """Create authentication provider.

    Args:
        config: Server configuration

    Returns:
        Auth provider instance

    Raises:
        ValueError: If AuthKit domain is not configured
    """
    if not config.authkit_domain:
        raise ValueError("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN required")

    auth_provider = AuthKitProvider(
        authkit_domain=config.authkit_domain,
        base_url=config.base_url,
        required_scopes=list(config.authkit_required_scopes) or None,
    )

    logger.info(f"✅ AuthKitProvider configured (remote OAuth): {config.authkit_domain}")
    print(f"✅ AuthKitProvider configured (remote OAuth): {config.authkit_domain}")

    return auth_provider


def create_consolidated_server(config: ServerConfig | None = None) -> FastMCP:
    """Create the FastMCP server with consolidated tools.

    This server provides 5 smart, agent-optimized tools:
    - workspace_operation: Context management
    - entity_operation: Unified CRUD for all entities
    - relationship_operation: Manage entity relationships
    - workflow_execute: Complex multi-step operations
    - data_query: Data exploration and analysis with RAG

    Args:
        config: Optional server configuration

    Returns:
        Configured FastMCP server instance

    Examples:
        >>> server = create_consolidated_server()
        >>> server.run(transport="stdio")
    """
    # Load environment files early
    load_env_files()

    # Debug environment loading
    fastmcp_vars = get_fastmcp_vars()
    print(f"🔍 DEBUG: FASTMCP environment variables: {fastmcp_vars}")
    logger.info(f"🔍 DEBUG: FASTMCP environment variables: {fastmcp_vars}")

    # Create configuration
    if config is None:
        config = ServerConfig.from_env()

    logger.info(f"Resolved base URL: {config.base_url}")
    print(f"🌐 AUTH BASE URL -> {config.base_url}")

    # Initialize rate limiter
    global _rate_limiter
    _rate_limiter = _initialize_rate_limiter(config)

    # Create auth provider
    auth_provider = _create_auth_provider(config)

    # Create FastMCP server
    mcp = FastMCP(
        name=config.name,
        instructions=(
            "Atoms MCP server with consolidated, agent-optimized tools. "
            "Authenticate via OAuth (AuthKit). "
            "Use workspace_tool to manage context, entity_tool for CRUD, "
            "relationship_tool for associations, workflow_tool for complex tasks, "
            "and query_tool for data exploration including RAG search."
        ),
        auth=auth_provider,
    )

    # Register tools (imported from tools module)
    _register_tools(mcp)

    # Add OAuth discovery endpoints
    _add_oauth_endpoints(mcp, config)

    logger.info("✅ Server created - AuthKit remote OAuth is fully stateless")

    return mcp


def _register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools.

    Args:
        mcp: FastMCP server instance
    """
    # Import tool operations using importlib to avoid conflicts with pheno-sdk/adapter-kit/tools
    import importlib.util
    import sys
    from pathlib import Path

    # Get the path to the local tools package
    atoms_mcp_root = Path(__file__).parent.parent
    tools_init_path = atoms_mcp_root / "tools" / "__init__.py"

    # Load the tools module from the specific file path
    spec = importlib.util.spec_from_file_location("atoms_tools", tools_init_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load tools module from {tools_init_path}")

    atoms_tools = importlib.util.module_from_spec(spec)
    sys.modules["atoms_tools"] = atoms_tools
    spec.loader.exec_module(atoms_tools)

    # Extract the tool operations from the loaded module
    workspace_operation = atoms_tools.workspace_operation
    entity_operation = atoms_tools.entity_operation
    relationship_operation = atoms_tools.relationship_operation
    workflow_execute = atoms_tools.workflow_execute
    data_query = atoms_tools.data_query

    # Import tool registration functions
    from .tools import (
        register_entity_tool,
        register_query_tool,
        register_relationship_tool,
        register_workflow_tool,
        register_workspace_tool,
    )

    # Register each tool
    register_workspace_tool(mcp, workspace_operation, _rate_limiter)
    register_entity_tool(mcp, entity_operation, _rate_limiter)
    register_relationship_tool(mcp, relationship_operation, _rate_limiter)
    register_workflow_tool(mcp, workflow_execute, _rate_limiter)
    register_query_tool(mcp, data_query, _rate_limiter)

    logger.info("✅ All tools registered")


def _add_oauth_endpoints(mcp: FastMCP, config: ServerConfig) -> None:
    """Add OAuth discovery endpoints for MCP client compatibility.

    Args:
        mcp: FastMCP server instance
        config: Server configuration
    """
    async def _oauth_protected_resource_handler(request):
        from starlette.responses import JSONResponse

        # Determine resource URL from request headers
        scheme = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("x-forwarded-host") or request.headers.get("host")

        if host:
            resource = f"{scheme}://{host}"
        else:
            resource = config.base_url or "http://localhost:8000"

        return JSONResponse({
            "resource": resource,
            "authorization_servers": [config.authkit_domain] if config.authkit_domain else [],
            "bearer_methods_supported": ["header"],
        })

    async def _oauth_authorization_server_handler(request):
        import httpx
        from starlette.responses import JSONResponse

        if not config.authkit_domain:
            return JSONResponse({"error": "AuthKit not configured"}, status_code=404)

        # Proxy to AuthKit
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{config.authkit_domain}/.well-known/oauth-authorization-server"
            )
            return JSONResponse(resp.json())

    mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])(
        _oauth_protected_resource_handler
    )
    mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])(
        _oauth_authorization_server_handler
    )

    logger.info("✅ OAuth discovery endpoints added")


__all__ = [
    "ServerConfig",
    "create_consolidated_server",
]
