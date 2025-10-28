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

import asyncio
import importlib.util
import os
import socket
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from starlette.responses import JSONResponse, PlainTextResponse

from config import app_config
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

SERVICE_NAME = "atoms-mcp"
DEFAULT_PORT = 8000
DEFAULT_DOMAIN = "atomcp.kooshapari.com"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PHENO_SRC = PROJECT_ROOT.parent / "pheno-sdk" / "src"
if PHENO_SRC.exists():  # pragma: no branch - development convenience
    sys.path.insert(0, str(PHENO_SRC))

_kinfra_enabled = False

try:  # pragma: no branch - import guard
    from pheno.infra.tunneling import (  # type: ignore[import-untyped]
        AsyncTunnelManager,
        TunnelConfig,
        TunnelInfo,
        TunnelProtocol,
        TunnelStatus,
        TunnelType,
    )

    _kinfra_enabled = True
    logger.info("✅ pheno-sdk tunneling integration available")
except Exception as direct_import_exc:  # pragma: no cover - optional dependency
    try:
        tunneling_path = PHENO_SRC / "pheno" / "infra" / "tunneling.py"
        if not tunneling_path.exists():
            import pheno  # type: ignore
            tunneling_path = Path(pheno.__file__).parent / "infra" / "tunneling.py"

        spec = importlib.util.spec_from_file_location("atoms.pheno_tunneling", tunneling_path)
        if not spec or not spec.loader:  # pragma: no cover - safety check
            raise ImportError("Unable to resolve pheno.infra.tunneling module")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        AsyncTunnelManager = module.AsyncTunnelManager  # type: ignore[attr-defined]
        TunnelConfig = module.TunnelConfig  # type: ignore[attr-defined]
        TunnelInfo = module.TunnelInfo  # type: ignore[attr-defined]
        TunnelProtocol = module.TunnelProtocol  # type: ignore[attr-defined]
        TunnelStatus = module.TunnelStatus  # type: ignore[attr-defined]
        TunnelType = module.TunnelType  # type: ignore[attr-defined]

        _kinfra_enabled = True
        logger.info("✅ pheno-sdk tunneling loaded via direct module path")
    except Exception as dynamic_import_exc:  # pragma: no cover - optional dependency
        _kinfra_enabled = False
        logger.warning(
            "⚠️  pheno-sdk tunneling not available: %s",
            dynamic_import_exc if 'dynamic_import_exc' in locals() else direct_import_exc,
        )
        AsyncTunnelManager = None  # type: ignore[assignment]
        TunnelConfig = TunnelInfo = TunnelProtocol = TunnelStatus = TunnelType = None  # type: ignore[assignment]


def _find_free_port(preferred: Optional[int]) -> int:
    candidates = ([preferred] if preferred else []) + [0]
    last_error: Optional[OSError] = None
    for port in candidates:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
                sock.listen(1)
                return sock.getsockname()[1]
        except OSError as exc:
            last_error = exc
            continue
    fallback = preferred or DEFAULT_PORT
    if last_error:
        logger.debug("Falling back to port %s after bind error: %s", fallback, last_error)
    return fallback


@dataclass(slots=True)
class _ServiceState:
    port: int
    tunnel: Optional[TunnelInfo] = None


class _KinfraRuntime:
    def __init__(self, domain: str, enable_tunnel: bool) -> None:
        self.domain = domain
        self.enable_tunnel = enable_tunnel and _kinfra_enabled
        self._manager: Optional[AsyncTunnelManager] = AsyncTunnelManager() if self.enable_tunnel else None
        self._state: dict[str, _ServiceState] = {}

    def allocate_port(self, service_name: str, preferred: Optional[int]) -> int:
        if service_name in self._state:
            return self._state[service_name].port
        port = _find_free_port(preferred)
        self._state[service_name] = _ServiceState(port=port)
        logger.info("Allocated port %s for %s", port, service_name)
        return port

    def start_tunnel(self, service_name: str, port: int) -> Optional[TunnelInfo]:
        if not self.enable_tunnel or not self._manager:
            return None
        config = TunnelConfig(
            name=self.domain,
            tunnel_type=TunnelType.CLOUDFLARE,
            protocol=TunnelProtocol.HTTPS,
            local_host="127.0.0.1",
            local_port=port,
            metadata={"service": service_name},
        )
        try:
            info = asyncio.run(self._manager.create_tunnel(config))
            self._state[service_name].tunnel = info
            logger.info("Tunnel established at %s", info.public_url)
            return info
        except Exception as exc:  # pragma: no cover - tunnel failures deferred
            logger.warning("Failed to establish tunnel: %s", exc)
            return None

    def get_port(self, service_name: str) -> Optional[int]:
        state = self._state.get(service_name)
        return state.port if state else None

    def health(self, service_name: str) -> dict[str, object]:
        state = self._state.get(service_name)
        if not state:
            return {"service": service_name, "healthy": False, "status": "not_allocated"}
        tunnel_status = (
            state.tunnel.status.value if state.tunnel else TunnelStatus.CLOSED.value
        )
        return {
            "service": service_name,
            "healthy": True,
            "status": "allocated",
            "port": state.port,
            "tunnel_status": tunnel_status,
        }

    def cleanup(self, service_name: str) -> None:
        state = self._state.pop(service_name, None)
        if not state or not state.tunnel or not self._manager:
            return
        try:
            asyncio.run(self._manager.destroy_tunnel(state.tunnel.tunnel_id))
            logger.info("Tunnel %s closed", state.tunnel.public_url)
        except Exception as exc:  # pragma: no cover - cleanup best effort
            logger.warning("Tunnel cleanup failed: %s", exc)


_kinfra_runtime: Optional[_KinfraRuntime] = None
_cleanup_registered = False


def _init_kinfra(kinfra_settings, preferred_port: Optional[int]) -> Optional[int]:
    global _kinfra_runtime, _cleanup_registered

    domain = getattr(kinfra_settings, "domain", DEFAULT_DOMAIN)
    enable_tunnel = getattr(kinfra_settings, "enable_tunnel", True)
    runtime = _KinfraRuntime(domain, enable_tunnel)
    port = runtime.allocate_port(SERVICE_NAME, preferred_port)
    runtime.start_tunnel(SERVICE_NAME, port)
    _kinfra_runtime = runtime

    if not _cleanup_registered and threading.current_thread() is threading.main_thread():
        atexit.register(cleanup_kinfra)
        signal.signal(signal.SIGTERM, _cleanup_on_signal)  # type: ignore[arg-type]
        signal.signal(signal.SIGINT, _cleanup_on_signal)  # type: ignore[arg-type]
        _cleanup_registered = True

    return port


def get_allocated_port(service_name: str = SERVICE_NAME) -> Optional[int]:
    if not _kinfra_runtime:
        return None
    return _kinfra_runtime.get_port(service_name)


def health_check(service_name: str = SERVICE_NAME) -> dict[str, object]:
    if not _kinfra_runtime:
        return {"service": service_name, "healthy": False, "status": "not_initialised"}
    return _kinfra_runtime.health(service_name)


def cleanup_kinfra(service_name: str = SERVICE_NAME) -> None:
    if _kinfra_runtime:
        _kinfra_runtime.cleanup(service_name)


def _cleanup_on_signal(_signum, _frame) -> None:  # pragma: no cover - signal path
    cleanup_kinfra()


def main() -> None:
    """CLI runner for the consolidated server.

    This is the main entry point for running the server from the command line.
    It loads environment configuration and starts the server with the desired
    transport (stdio or HTTP).
    """

    # Load env files early
    load_env_files()

    # Debug environment loading
    fastmcp_vars = get_fastmcp_vars()
    settings = app_config
    print(f"🚀 MAIN DEBUG: FASTMCP environment variables: {fastmcp_vars}")
    print(f"🚀 MAIN DEBUG: Resolved base URL: {settings.fastmcp.base_url}")
    print(f"🚀 MAIN DEBUG: Transport: {settings.fastmcp.transport}, HTTP path: {settings.fastmcp.http_path}")

    # Get configuration from environment
    config = ServerConfig.from_settings(settings)

    # Initialize KINFRA if enabled
    kinfra_settings = getattr(settings, "kinfra", None)
    allocated_port = None

    if (
        _kinfra_enabled
        and kinfra_settings
        and getattr(kinfra_settings, "enabled", True)
        and config.transport == "http"
    ):
        try:
            logger.info("🚀 Initializing pheno-sdk infrastructure...")
            allocated_port = _init_kinfra(kinfra_settings, config.port)
            if allocated_port:
                logger.info(f"✅ Infrastructure allocated port: {allocated_port}")
                config.port = allocated_port
            else:
                logger.warning("⚠️  Infrastructure port allocation returned None, using config port")
        except Exception:
            logger.exception("❌ Infrastructure initialization failed")
            logger.info("⏩ Continuing without KINFRA...")

    # Create server
    server = create_consolidated_server(config)

    # Add health check for HTTP transport
    if config.transport == "http":
        @server.custom_route("/health", methods=["GET"])  # type: ignore[attr-defined]
        async def _health(_request):  # pragma: no cover
            if _kinfra_enabled and _kinfra_runtime:
                kinfra_health = health_check(SERVICE_NAME)
                return JSONResponse(
                    {
                        "status": "healthy",
                        "service": SERVICE_NAME,
                        "port": allocated_port or config.port,
                        "kinfra": kinfra_health,
                    }
                )
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
            if _kinfra_enabled and _kinfra_runtime:
                logger.info("🧹 Cleaning up KINFRA...")
                cleanup_kinfra()
    else:
        logger.info("Starting stdio server")
        server.run(transport="stdio")


__all__ = [
    # Auth
    "BearerToken",
    "EnvConfig",
    "EnvLoadError",
    "RateLimitExceeded",
    "RateLimiter",
    "Serializable",
    "SerializerConfig",
    # Configuration
    "ServerConfig",
    "apply_rate_limit_if_configured",
    "check_rate_limit",
    "cleanup_kinfra",
    # Main functions
    "create_consolidated_server",
    "extract_bearer_token",
    "get_allocated_port",
    "get_env_var",
    "get_fastmcp_vars",
    "get_token_string",
    "health_check",
    # Environment
    "load_env_files",
    "main",
    "markdown_serializer",
    "parse_env_file",
    "rate_limited_operation",
    # Serialization
    "serialize_to_markdown",
    "temporary_env",
]
