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
    
    Examples:
        Run with stdio transport:
        >>> ATOMS_FASTMCP_TRANSPORT=stdio python -m server
        
        Run with HTTP transport:
        >>> ATOMS_FASTMCP_TRANSPORT=http ATOMS_FASTMCP_PORT=8080 python -m server
    """
    # Load env files early
    load_env_files()

    # Debug environment loading
    fastmcp_vars = get_fastmcp_vars()
    print(f"🚀 MAIN DEBUG: FASTMCP environment variables: {fastmcp_vars}")
    print(f"🚀 MAIN DEBUG: Current working directory: {os.getcwd()}")
    print(f"🚀 MAIN DEBUG: .env file exists: {os.path.exists('.env')}")

    # Get configuration from environment
    config = ServerConfig.from_env()

    # Create server
    server = create_consolidated_server(config)

    # Add health check for HTTP transport
    if config.transport == "http":
        @server.custom_route("/health", methods=["GET"])  # type: ignore[attr-defined]
        async def _health(_request):  # pragma: no cover
            from starlette.responses import PlainTextResponse
            return PlainTextResponse("OK")

        logger.info(f"Starting HTTP server on {config.host}:{config.port}{config.http_path}")
        server.run(
            transport="http",
            host=config.host,
            port=config.port,
            path=config.http_path
        )
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
]

