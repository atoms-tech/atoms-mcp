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

import importlib
import importlib.util
import json
import shlex
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

# Ensure project root is on sys.path when loaded via fastmcp FileSystemSource
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import httpx
from fastmcp import FastMCP
from fastmcp.server.auth.providers.workos import AuthKitProvider
from starlette.responses import JSONResponse

from config import get_settings
from config.settings import AppConfig, app_config
from server.env import get_fastmcp_vars, load_env_files
from server.tools import (
    register_entity_tool,
    register_query_tool,
    register_relationship_tool,
    register_workflow_tool,
    register_workspace_tool,
)
from utils.logging_setup import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from server.auth import RateLimiter

logger = get_logger("atoms_fastmcp.core")


@asynccontextmanager
async def _server_lifespan(app: FastMCP) -> AsyncIterator[None]:
    """Server lifespan for FastMCP v2.13.0.1.

    This function provides initialization and cleanup hooks that run
    once per server instance instead of per client session.

    Yields:
        None: Control is passed to FastMCP server
    """
    _ = app  # Lifespan handlers receive the server instance; not used yet.

    logger.info("🚀 Starting Atoms FastMCP server lifespan")

    # Initialization phase - runs once per server startup
    try:
        # Initialize global resources here
        # (e.g., database connections, background tasks, etc.)
        logger.info("✅ Server initialization complete")
    except Exception:
        logger.exception("❌ Server initialization failed")
        raise

    yield  # FastMCP server runs here

    # Cleanup phase - runs once per server shutdown
    try:
        # Cleanup global resources here
        logger.info("✅ Server cleanup complete")
    except Exception:
        logger.exception("❌ Server cleanup failed")
        raise

    logger.info("🛑 Server lifespan complete")


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
    def from_settings(cls, settings: AppConfig | None = None) -> ServerConfig:
        """Create configuration from an AppConfig instance."""
        if settings is None:
            settings = app_config

        # Get environment variables
        fastmcp_vars = get_fastmcp_vars()

        # Create instance with settings from fastmcp config
        config = cls(
            transport=settings.fastmcp.transport,
            host=settings.fastmcp.host,
            port=settings.fastmcp.port or 8000,  # Default to 8000 if None
            http_path=settings.fastmcp.http_path,
            base_url=settings.fastmcp.base_url,
            authkit_domain=settings.fastmcp.authkit_domain,
            authkit_required_scopes=tuple(
                scope.strip() for scope in (settings.fastmcp.authkit_required_scopes or []) if scope and scope.strip()
            ),
        )

        # Override with environment variables if present
        domain = fastmcp_vars.get("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
        if domain:
            config.authkit_domain = domain

        base_url = fastmcp_vars.get("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL")
        if base_url:
            config.base_url = base_url

        scopes = fastmcp_vars.get("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES")
        if scopes is not None:
            config.authkit_required_scopes = _parse_scopes(scopes)

        return config


def _initialize_rate_limiter(config: ServerConfig) -> RateLimiter | None:
    """Initialize rate limiter for API protection.

    Args:
        config: Server configuration

    Returns:
        RateLimiter instance or None
    """
    module_candidates = (
        "pheno.dev.rate_limiting",
        "pheno.observability.rate_limiting",
    )

    for module_path in module_candidates:
        try:
            rate_module = importlib.import_module(module_path)
        except ImportError as exc:
            if module_path == module_candidates[-1]:
                message = "Rate limiter not available"
                if "observability" in str(exc):
                    logger.info("Rate limiter not available (observability module not installed)")
                else:
                    logger.warning(f"{message}: {exc}")
            continue

        limiter = rate_module.SlidingWindowRateLimiter(  # type: ignore[attr-defined]
            window_seconds=60,
            max_requests=config.rate_limit_rpm,
        )
        logger.info("Rate limiter configured: %s requests/minute", config.rate_limit_rpm)
        return limiter

    logger.info("Rate limiter not configured; continuing without rate limiting")
    return None


def _parse_scopes(value: str | None) -> tuple[str, ...]:
    """Parse OAuth scopes from configuration."""
    if not value:
        return ()

    candidate = value.strip()
    if not candidate:
        return ()

    # Attempt JSON parsing first
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        return tuple(str(scope).strip() for scope in parsed if str(scope).strip())
    if isinstance(parsed, str):
        parsed = parsed.strip()
        return (parsed,) if parsed else ()

    # Handle comma-separated values
    if "," in candidate:
        parts = [part.strip() for part in candidate.split(",")]
        return tuple(part for part in parts if part)

    # Fall back to whitespace-separated using shlex for quoted values
    try:
        tokens = shlex.split(candidate)
    except ValueError:
        tokens = candidate.split()

    return tuple(token.strip() for token in tokens if token.strip())


def _create_auth_provider(config: ServerConfig):
    """Create authentication provider.

    Args:
        config: Server configuration

    Returns:
        Auth provider instance

    Raises:
        ValueError: If AuthKit domain is not configured
    """
    # Return None if auth not configured
    if not config.authkit_domain:
        return None

    auth_provider = AuthKitProvider(
        authkit_domain=config.authkit_domain,
        base_url=config.base_url if config.base_url is not None else ...,  # Use Ellipsis if None (AuthKitProvider accepts EllipsisType)
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
    rate_limiter = _initialize_rate_limiter(config)

    # Create auth provider
    auth_provider = _create_auth_provider(config)

    # Create FastMCP server with v2.13.0.1 features
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
        # Enable Pydantic input validation for better type safety
        # strict_input_validation=True,  # Not supported in this FastMCP version
        # Add server icon for richer UX
        # icons=[
        #     {"url": "https://atoms.ai/icon.png", "media_type": "image/png"}
        # ],  # Not supported in this FastMCP version
        # Server lifespan for proper initialization/cleanup
        lifespan=_server_lifespan,
    )

    # Register tools (imported from tools module)
    _register_tools(mcp, rate_limiter)

    # Add OAuth discovery endpoints
    _add_oauth_endpoints(mcp, config)

    logger.info("✅ Server created - AuthKit remote OAuth is fully stateless")

    return mcp


def _register_tools(mcp: FastMCP, rate_limiter: RateLimiter | None) -> None:
    """Register all MCP tools.

    Args:
        mcp: FastMCP server instance
    """
    # Import tool operations using importlib to avoid conflicts with pheno-sdk/adapter-kit/tools
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

    # Register each tool
    register_workspace_tool(mcp, workspace_operation, rate_limiter)
    register_entity_tool(mcp, entity_operation, rate_limiter)
    register_relationship_tool(mcp, relationship_operation, rate_limiter)
    register_workflow_tool(mcp, workflow_execute, rate_limiter)
    register_query_tool(mcp, data_query, rate_limiter)

    logger.info("✅ All tools registered")


def _add_oauth_endpoints(mcp: FastMCP, config: ServerConfig) -> None:
    """Add OAuth discovery endpoints for MCP client compatibility.

    Args:
        mcp: FastMCP server instance
        config: Server configuration
    """

    async def _oauth_protected_resource_handler(request):
        # Determine resource URL from request headers
        scheme = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("x-forwarded-host") or request.headers.get("host")

        resource = f"{scheme}://{host}" if host else config.base_url or "http://localhost:8000"

        return JSONResponse(
            {
                "resource": resource,
                "authorization_servers": [config.authkit_domain] if config.authkit_domain else [],
                "bearer_methods_supported": ["header"],
            }
        )

    async def _oauth_authorization_server_handler(_request):
        if not config.authkit_domain:
            return JSONResponse({"error": "AuthKit not configured"}, status_code=404)

        # Proxy to AuthKit
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{config.authkit_domain}/.well-known/oauth-authorization-server")
            return JSONResponse(resp.json())

    mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])(_oauth_protected_resource_handler)
    mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])(_oauth_authorization_server_handler)

    logger.info("✅ OAuth discovery endpoints added")


__all__ = [
    "ServerConfig",
    "create_consolidated_server",
]
