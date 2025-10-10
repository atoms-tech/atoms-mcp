"""CLI entrypoint for local development workflows.

Wraps deploy-kit, observability-kit, filewatch-kit, and pydevkit helpers so our
local tooling is shared rather than bespoke shell scripts.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import httpx
from cli_builder.cli import CLI
from deploy_kit.local import LocalProcessConfig, LocalServiceManager, ReadyProbe
from filewatch_kit.watcher import FileEvent, FileWatcher
from observability.logging import StructuredLogger, stream_log_file
from pydevkit.correlation_id import generate_correlation_id


async def _run_subprocess(cmd):
    proc = await asyncio.create_subprocess_exec(*cmd)
    return await proc.wait()

cli = CLI(name="atoms-dev", description="Atoms MCP local development toolkit")


def _logger(service: str) -> StructuredLogger:
    correlation_id = generate_correlation_id()
    logger = StructuredLogger(
        "atoms-dev",
        service_name=service,
        environment=os.getenv("ENV", "dev"),
        version=os.getenv("ATOMS_VERSION", "local"),
    )
    logger.set_correlation_id(correlation_id)
    return logger


async def _check_http_ready(url: str, attempts: int = 30, timeout: float = 2.0) -> bool:
    async with httpx.AsyncClient(timeout=timeout) as client:
        for _ in range(attempts):
            try:
                response = await client.get(url)
                if response.status_code < 500:
                    return True
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1)
    return False


@cli.command("start", description="Start local server and optional tunnel")
async def start_command():
    logger = _logger("atoms-mcp-local")
    manager = LocalServiceManager()

    project_root = Path(__file__).resolve().parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        logger.info("loading_env", path=str(env_file))
        for line in env_file.read_text().splitlines():
            if line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

    app_env = {
        "ENV": "dev",
        "ATOMS_FASTMCP_TRANSPORT": "http",
        "ATOMS_FASTMCP_HOST": os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1"),
        "ATOMS_FASTMCP_PORT": os.getenv("ATOMS_FASTMCP_PORT", "8000"),
        "ATOMS_FASTMCP_HTTP_PATH": os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp"),
        "ATOMS_FASTMCP_HTTP_AUTH_MODE": os.getenv("ATOMS_FASTMCP_HTTP_AUTH_MODE", "optional"),
    }

    server_probe = ReadyProbe(
        lambda: _check_http_ready(
            f"http://{app_env['ATOMS_FASTMCP_HOST']}:{app_env['ATOMS_FASTMCP_PORT']}/health"
        )
    )

    configs = [
        LocalProcessConfig(
            name="atoms-server",
            command=[sys.executable, "-m", "atoms_mcp-old.server"],
            cwd=project_root,
            env=app_env,
            ready_probe=server_probe,
        )
    ]

    if _binary_exists("cloudflared"):
        configs.append(
            LocalProcessConfig(
                name="cloudflare",
                command=["cloudflared", "tunnel", "run", "atoms-mcp"],
                cwd=project_root,
            )
        )
    else:
        logger.warning("cloudflared_not_found", message="Skipping tunnel startup")

    await manager.start(configs)
    logger.info("services_started", status=manager.status())

    try:
        manager.stream_logs()
    except KeyboardInterrupt:
        logger.info("shutdown_requested")
    finally:
        await manager.stop()


def _binary_exists(name: str) -> bool:
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(path) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return True
    return False


@cli.command("verify", description="Run connectivity verification checks")
async def verify_command():
    logger = _logger("atoms-mcp-verify")
    authkit_domain = os.getenv("AUTHKIT_DOMAIN", "https://decent-hymn-17-staging.authkit.app")
    server_url = os.getenv("ATOMS_PUBLIC_ENDPOINT", "https://atomcp.kooshapari.com")

    async with httpx.AsyncClient(timeout=5.0) as client:
        await _verify_authkit_metadata(client, authkit_domain, logger)
        await _verify_protected_resource(client, server_url, logger)
        await _verify_cors(client, server_url, logger)
        await _verify_dcr(client, authkit_domain, logger)


async def _verify_authkit_metadata(client: httpx.AsyncClient, domain: str, logger: StructuredLogger) -> None:
    url = f"{domain}/.well-known/oauth-authorization-server"
    try:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info("authkit_metadata", issuer=data.get("issuer"), registration=data.get("registration_endpoint"))
    except Exception as exc:
        logger.error("authkit_metadata_failed", url=url, error=str(exc))


async def _verify_protected_resource(client: httpx.AsyncClient, server_url: str, logger: StructuredLogger) -> None:
    url = f"{server_url}/.well-known/oauth-protected-resource"
    try:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            logger.info(
                "protected_resource",
                resource=data.get("resource"),
                authorization_servers=data.get("authorization_servers"),
            )
        else:
            logger.warning("protected_resource_unavailable", status=response.status_code, body=response.text[:200])
    except Exception as exc:
        logger.warning("protected_resource_error", error=str(exc))


async def _verify_cors(client: httpx.AsyncClient, server_url: str, logger: StructuredLogger) -> None:
    url = f"{server_url}/.well-known/oauth-protected-resource"
    try:
        request = client.build_request(
            "OPTIONS",
            url,
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "mcp-protocol-version",
            },
        )
        response = await client.send(request)
        header = response.headers.get("Access-Control-Allow-Origin")
        logger.info("cors_check", allowed_origin=header)
    except Exception as exc:
        logger.warning("cors_check_failed", error=str(exc))


async def _verify_dcr(client: httpx.AsyncClient, domain: str, logger: StructuredLogger) -> None:
    url = f"{domain}/oauth2/register"
    payload = {
        "client_name": "Atoms Dev Diagnostics",
        "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
    }
    try:
        response = await client.post(url, json=payload)
        if response.status_code == 201:
            logger.info("dcr_enabled", client_id=response.json().get("client_id"))
        else:
            logger.warning("dcr_failed", status=response.status_code, body=response.text[:200])
    except Exception as exc:
        logger.error("dcr_error", error=str(exc))


@cli.command("monitor", description="Stream structured logs from the local server")
async def monitor_command(log_path: str | None = None):
    logger = _logger("atoms-mcp-monitor")
    path = Path(log_path or os.getenv("ATOMS_LOG_PATH", "/tmp/atoms_mcp.log"))

    logger.info("stream_start", path=str(path))
    try:
        async for entry in stream_log_file(path):
            logger.info("log", **entry)
    except KeyboardInterrupt:
        logger.info("stream_stop")


@cli.command("watch", description="Watch paths for file changes", args=["path"])
async def watch_command(path: str):
    logger = _logger("atoms-mcp-watch")
    watcher = FileWatcher(path, patterns=["*.py", "*.sql"], recursive=True)

    def _emit(event: FileEvent) -> None:
        logger.info(
            "file_event",
            event_type=event.type.value,
            path=event.path,
            directory=event.is_directory,
        )

    watcher.on_any(_emit)
    try:
        await watcher.start()
    except KeyboardInterrupt:
        watcher.stop()
        logger.info("watcher_stopped")


@cli.command("backfill", description="Run embedding backfill", args=["*options"])
async def backfill_command(options: list[str] | None = None):
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "backfill_embeddings.py"),
        * (options or []),
    ]
    await _run_subprocess(cmd)


@cli.command("check-embeddings", description="Check embedding status")
async def check_embeddings_command():
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "check_embedding_status.py"),
    ]
    await _run_subprocess(cmd)


@cli.command("setup-sessions", description="Provision the Supabase mcp_sessions table")
async def setup_sessions_command():
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "setup_mcp_sessions.py"),
    ]
    await _run_subprocess(cmd)


def main() -> None:
    asyncio.run(cli.run())


if __name__ == "__main__":  # pragma: no cover
    main()
