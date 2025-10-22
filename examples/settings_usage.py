"""
Example usage of Atoms MCP Production settings with Pydantic and YAML configuration.
"""
from config.settings import settings


def main():
    """Example usage of Atoms MCP Production settings."""
    print("=== Atoms MCP Production Settings Example ===")

    # Access configuration values
    print(f"Environment: {settings.server.environment}")
    print(f"Log Level: {settings.server.log_level}")
    print(f"Debug Mode: {settings.server.debug}")
    print(f"KINFRA Managed: {settings.kinfra.managed}")
    print(f"KINFRA Tunnel: {settings.kinfra.tunnel}")
    print(f"FastMCP Host: {settings.fastmcp.host}")
    print(f"FastMCP Port: {settings.fastmcp.port}")
    print(f"FastMCP Base URL: {settings.fastmcp.base_url}")
    print(f"AuthKit Domain: {settings.auth.authkit_provider.authkit_domain}")
    print(f"Required Scopes: {settings.auth.authkit_provider.authkit_required_scopes}")
    print(f"Database URL: {settings.database.url}")
    print(f"Supabase URL: {settings.database.supabase.url}")
    print(f"Caching Enabled: {settings.features.enable_caching}")
    print(f"Streaming Enabled: {settings.features.enable_streaming}")
    print(f"Tool Use Enabled: {settings.features.enable_tool_use}")
    print(f"Tool Timeout: {settings.tools.timeout}")
    print(f"Max Retries: {settings.tools.max_retries}")
    print(f"Profiling Enabled: {settings.observability.enable_profiling}")
    print(f"Tracing Enabled: {settings.observability.enable_tracing}")

    # Example of using settings in application code
    if settings.features.enable_caching:
        print("Caching is enabled")

    if settings.features.enable_streaming:
        print("Streaming is enabled")

    if settings.features.enable_tool_use:
        print("Tool use is enabled")

    # Example of conditional logic based on settings
    if settings.server.debug:
        print("Running in debug mode - additional logging enabled")

    # Example of using KINFRA configuration
    if settings.kinfra.managed:
        print("KINFRA management is enabled")
        if settings.kinfra.tunnel:
            print("CloudFlare tunnel is enabled")
        if settings.kinfra.fallback:
            print("Fallback pages are enabled")
        if settings.kinfra.restart:
            print("Auto-restart on failure is enabled")

    # Example of using FastMCP configuration
    print(f"FastMCP server running on {settings.fastmcp.host}:{settings.fastmcp.port}")
    print(f"FastMCP base URL: {settings.fastmcp.base_url}")
    print(f"FastMCP HTTP path: {settings.fastmcp.http_path}")

    # Example of using observability configuration
    if settings.observability.enable_profiling:
        print("Profiling is enabled")
    if settings.observability.enable_tracing:
        print("Tracing is enabled")
    if settings.observability.telemetry_enabled:
        print("Telemetry is enabled")


if __name__ == "__main__":
    main()
