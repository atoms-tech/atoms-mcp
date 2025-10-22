"""
Atoms MCP Server - Modular FastMCP server implementation.

This package provides a modular, well-structured MCP server with:
- Markdown serialization for LLM-friendly responses
- OAuth authentication via AuthKit
- Rate limiting for API protection
- Environment configuration management
- Consolidated tool registration

Pythonic Patterns Applied:
- Package structure for modularity
- Type hints throughout
- Dataclasses for configuration
- Context managers for resources
- Protocols for extensibility

Usage:
    >>> from server import create_consolidated_server, main
    >>> server = create_consolidated_server()
    >>> server.run(transport="stdio")

    Or use the CLI:
    >>> main()
"""

from __future__ import annotations

import os
from typing import Optional

from config import get_settings
from utils.logging_setup import get_logger

from .auth import (
    BearerToken,
    RateLimiter,
    RateLimitExceeded,
    apply_rate_limit_if_configured,
    check_rate_limit,
    extract_bearer_token,
    get_token_string,
    rate_limited_operation,
)
from .core import ServerConfig, create_consolidated_server
from .env import (
    EnvConfig,
    EnvLoadError,
    get_env_var,
    get_fastmcp_vars,
    load_env_files,
    parse_env_file,
    temporary_env,
)
from .serializers import (
    Serializable,
    SerializerConfig,
    markdown_serializer,
    serialize_to_markdown,
)

logger = get_logger("atoms_fastmcp")

# KINFRA Integration
_kinfra_enabled = False
_kinfra_instance = None
_service_manager = None

try:
    from kinfra_setup import cleanup_kinfra, get_allocated_port, health_check, setup_kinfra
    _kinfra_enabled = True
    logger.info("✅ KINFRA integration available")
except ImportError as e:
    logger.warning(f"⚠️  KINFRA integration not available: {e}")
    # Define stub functions for when KINFRA is not available
    def setup_kinfra(*args, **kwargs):
        return None, None
    def cleanup_kinfra(*args, **kwargs):
        pass
    def get_allocated_port(*args, **kwargs):
        return None
    def health_check(*args, **kwargs):
        return {"status": "kinfra_not_available"}


def main() -> None:
    """CLI runner for the consolidated server.

    This is the main entry point for running the server from the command line.
    It loads environment configuration and starts the server with the
    appropriate transport (stdio or HTTP).

    Environment Variables:
        ATOMS_FASTMCP_TRANSPORT: Transport type (stdio or http)
        ATOMS_FASTMCP_HOST: Host for HTTP transport (default: 127.0.0.1)
        ATOMS_FASTMCP_PORT: Port for HTTP transport (default: 8000)
        ATOMS_FASTMCP_HTTP_PATH: Path for HTTP transport (default: /api/mcp)
        ENABLE_KINFRA: Enable KINFRA integration (default: true)

    Examples:
        Run with stdio transport:
        >>> ATOMS_FASTMCP_TRANSPORT=stdio python -m server

        Run with HTTP transport:
        >>> ATOMS_FASTMCP_TRANSPORT=http ATOMS_FASTMCP_PORT=8080 python -m server

        Run with KINFRA port allocation:
        >>> ENABLE_KINFRA=true ATOMS_FASTMCP_TRANSPORT=http python -m server
    """
    global _kinfra_instance, _service_manager

    # Load env files early
    load_env_files()

    # Debug environment loading
    fastmcp_vars = get_fastmcp_vars()
    settings = get_settings()
    print(f"🚀 MAIN DEBUG: FASTMCP environment variables: {fastmcp_vars}")
    print(f"🚀 MAIN DEBUG: Resolved base URL: {settings.fastmcp.base_url}")
    print(f"🚀 MAIN DEBUG: Transport: {settings.fastmcp.transport}, HTTP path: {settings.fastmcp.http_path}")

    # Get configuration from environment
    config = ServerConfig.from_settings(settings)

    # Initialize KINFRA if enabled
    enable_kinfra = os.getenv("ENABLE_KINFRA", "true").lower() in ("true", "1", "yes")
    allocated_port = None

    if _kinfra_enabled and enable_kinfra and config.transport == "http":
        try:
            logger.info("🚀 Initializing KINFRA...")
            _kinfra_instance, _service_manager = setup_kinfra(
                project_name="atoms-mcp",
                preferred_port=config.port,
                enable_tunnel=False,  # Local only
                enable_fallback=False,  # No fallback for MCP server
            )
            allocated_port = get_allocated_port("atoms-mcp")
            if allocated_port:
                logger.info(f"✅ KINFRA allocated port: {allocated_port}")
                config.port = allocated_port  # Override config port with KINFRA allocation
            else:
                logger.warning("⚠️  KINFRA port allocation returned None, using config port")
        except Exception as e:
            logger.error(f"❌ KINFRA initialization failed: {e}")
            logger.info("⏩ Continuing without KINFRA...")

    # Create server
    server = create_consolidated_server(config)

    # Add health check for HTTP transport
    if config.transport == "http":
        @server.custom_route("/health", methods=["GET"])  # type: ignore[attr-defined]
        async def _health(_request):  # pragma: no cover
            from starlette.responses import JSONResponse, PlainTextResponse

            # Include KINFRA health status if available
            if _kinfra_enabled and _kinfra_instance:
                kinfra_health = health_check("atoms-mcp")
                return JSONResponse({
                    "status": "healthy",
                    "service": "atoms-mcp",
                    "port": allocated_port or config.port,
                    "kinfra": kinfra_health
                })
            return PlainTextResponse("OK")

        logger.info(f"Starting HTTP server on {config.host}:{config.port}{config.http_path}")
        print(f"\n{'='*60}")
        print("🚀 Atoms MCP Server Starting")
        print(f"{'='*60}")
        print(f"   Host: {config.host}")
        print(f"   Port: {config.port}")
        print(f"   Path: {config.http_path}")
        if allocated_port:
            print(f"   KINFRA: Enabled (port {allocated_port})")
        print(f"{'='*60}\n")

        try:
            server.run(
                transport="http",
                host=config.host,
                port=config.port,
                path=config.http_path
            )
        finally:
            # Cleanup KINFRA on server shutdown
            if _kinfra_enabled and _kinfra_instance:
                logger.info("🧹 Cleaning up KINFRA...")
                cleanup_kinfra(_kinfra_instance, _service_manager)
    else:
        logger.info("Starting stdio server")
        server.run(transport="stdio")


__all__ = [
    # Main functions
    "create_consolidated_server",
    "main",

    # Configuration
    "ServerConfig",
    "EnvConfig",
    "SerializerConfig",

    # Auth
    "BearerToken",
    "RateLimiter",
    "RateLimitExceeded",
    "extract_bearer_token",
    "check_rate_limit",
    "apply_rate_limit_if_configured",
    "rate_limited_operation",
    "get_token_string",

    # Environment
    "load_env_files",
    "parse_env_file",
    "temporary_env",
    "get_env_var",
    "get_fastmcp_vars",
    "EnvLoadError",

    # Serialization
    "serialize_to_markdown",
    "markdown_serializer",
    "Serializable",

    # KINFRA Integration (available if kinfra_setup is installed)
    "setup_kinfra",
    "cleanup_kinfra",
    "get_allocated_port",
    "health_check",
]
