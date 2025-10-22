#!/usr/bin/env python3
"""Atoms MCP command line interface."""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# Ensure project modules are importable
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

try:  # pragma: no cover - optional structured logging
    from observability import LogLevel, StructuredLogger

    _LOGGER = StructuredLogger(
        "atoms-cli",
        service_name="atoms-mcp-cli",
        environment="local",
        level=LogLevel.INFO,
    )
    USE_STRUCTURED_LOGGING = True
except ImportError:  # pragma: no cover - fallback logging
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _LOGGER = logging.getLogger("atoms-cli")
    USE_STRUCTURED_LOGGING = False

from config import get_settings, reset_settings_cache  # noqa: E402
from config.settings import AppSettings  # noqa: E402

ENV_ALIASES: dict[str, str] = {
    "local": "local",
    "dev": "dev",
    "preview": "dev",
    "development": "dev",
    "staging": "dev",
    "prod": "production",
    "production": "production",
    "none": "production",
}

ENV_ENDPOINTS: dict[str, str] = {
    "local": "http://127.0.0.1:8000/api/mcp",
    "dev": "https://devmcp.atoms.tech/api/mcp",
    "production": "https://mcp.atoms.tech/api/mcp",
}

ENV_DISPLAY_NAMES: dict[str, str] = {
    "local": "Local (atomcp tunnel)",
    "dev": "Preview (devmcp.atoms.tech)",
    "production": "Production (mcp.atoms.tech)",
}

SUITE_PATHS: dict[str, str] = {
    "unit": "tests/unit/",
    "integration": "tests/integration/",
    "e2e": "tests/e2e/",
    "performance": "tests/performance/",
    "all": "tests/",
}


def log_info(message: str, **kwargs: Any) -> None:
    if USE_STRUCTURED_LOGGING:
        _LOGGER.info(message, **kwargs)
    else:
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        _LOGGER.info(f"{message} {extra}".strip())


def log_error(message: str, **kwargs: Any) -> None:
    if USE_STRUCTURED_LOGGING:
        _LOGGER.error(message, **kwargs)
    else:
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        _LOGGER.error(f"{message} {extra}".strip())


def canonical_environment(value: str | None, default: str) -> str:
    if value is None:
        return default
    key = value.lower()
    return ENV_ALIASES.get(key, default)


def deployment_target(env: str) -> str:
    return "preview" if env == "dev" else "production"


def environment_variables_for(env: str) -> dict[str, str]:
    canonical = env
    target = "preview" if canonical == "dev" else canonical
    env_vars: dict[str, str] = {
        "ATOMS_TARGET_ENVIRONMENT": target,
        "ATOMS_MCP_ENVIRONMENT": target,
        "ATOMS_FASTMCP_TRANSPORT": "http",
    }
    endpoint = ENV_ENDPOINTS.get(canonical)
    if endpoint:
        env_vars["MCP_ENDPOINT"] = endpoint
        env_vars["ATOMS_MCP_ENDPOINT"] = endpoint
    return env_vars


def apply_environment(env: str) -> tuple[dict[str, str], AppSettings | None]:
    env_vars = environment_variables_for(env)
    for key, value in env_vars.items():
        if value is not None:
            os.environ[key] = value

    reset_settings_cache()
    try:
        settings: AppSettings | None = get_settings()
        if settings:
            settings.apply_to_environment(override=True)
    except Exception:  # pragma: no cover - defensive fallback
        settings = None

    return env_vars, settings


def run_subprocess(command: Sequence[str], *, env: dict[str, str] | None = None) -> int:
    log_info("Executing command", command=" ".join(command))
    result = subprocess.run(command, env=env)
    return result.returncode


def handle_start(args: argparse.Namespace) -> int:
    """Start Atoms MCP with full orchestration (byteport-style behavior)."""
    env = canonical_environment(args.environment, "local")
    env_vars, settings = apply_environment(env)

    log_info(
        "Starting Atoms MCP with orchestration",
        environment=env,
        endpoint=env_vars.get("MCP_ENDPOINT"),
        base_url=getattr(settings, "resolved_base_url", None),
    )

    # Import orchestration components
    try:
        import sys

        # Add pheno-sdk to path
        sys.path.insert(0, str(PROJECT_ROOT.parent / "pheno-sdk" / "src"))

        # Determine mode based on environment
        dev_mode = env in ["dev", "development", "preview"]
        local_mode = env == "local"

        # Set port in environment if specified
        if args.port:
            os.environ["ATOMS_MCP_PORT"] = str(args.port)

        # Set tunnel mode
        if args.no_tunnel:
            os.environ["ATOMS_NO_TUNNEL"] = "true"

        # Run the orchestration
        asyncio.run(start_atoms_orchestration(dev_mode=dev_mode, local_mode=local_mode))
        return 0

    except Exception as exc:
        log_error("Orchestration failed, falling back to simple start", error=str(exc))

        # Fallback to simple server start
        try:
            from lib.atoms import start_atoms_server
        except ImportError as exc2:
            log_error("Unable to import start_atoms_server", error=str(exc2))
            print("Error: start_atoms_server not available")
            return 1

        # Use pheno-sdk port allocation if no specific port provided
        if args.port:
            port = args.port
        else:
            # Try to use pheno-sdk port allocation
            try:
                from pheno.infra.port_allocator import SmartPortAllocator
                from pheno.infra.port_registry import PortRegistry
                from pheno.infra.process_cleanup import ProcessCleanupConfig

                # Perform process cleanup before port allocation
                ProcessCleanupConfig(
                    cleanup_related_services=True,
                    cleanup_tunnels=True,
                    grace_period=2.0,
                )
                # Note: cleanup_before_startup is async, skip for now
                print("🧹 Process cleanup skipped (sync context)")

                registry = PortRegistry()
                allocator = SmartPortAllocator(registry)
                port = allocator.allocate_port("atoms-mcp-server")
                print(f"🔧 pheno-sdk allocated port {port} for atoms-mcp-server")
            except ImportError:
                port = 8000
                print("⚠️  pheno-sdk not available, using default port 8000")
            except Exception as e:
                port = 8000
                print(f"⚠️  pheno-sdk port allocation failed: {e}, using default port 8000")

        return start_atoms_server(
            port=port,
            verbose=args.verbose,
            no_tunnel=args.no_tunnel,
            logger=_LOGGER if USE_STRUCTURED_LOGGING else None,
        )


async def start_atoms_orchestration(dev_mode: bool = False, local_mode: bool = False) -> None:
    """Start Atoms MCP with full orchestration (byteport-style behavior)."""
    import logging
    import os
    import subprocess
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger("atoms-orchestrator")

    # Default configuration
    DEFAULT_PORT = 8000
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_HTTP_PATH = "/api/mcp"
    PUBLIC_DOMAIN = "atoms.kooshapari.com"

    class AtomsOrchestrator:
        """Orchestrator for Atoms MCP services."""

        def __init__(self):
            self.process: subprocess.Popen | None = None
            self.allocated_port: int | None = None
            self.tunnel_info: dict | None = None

        def allocate_port(self, service_name: str = "atoms-mcp-server") -> int:
            """Allocate a port using pheno-sdk's smart port allocator."""
            try:
                from pheno.infra.port_allocator import SmartPortAllocator
                from pheno.infra.port_registry import PortRegistry
                from pheno.infra.process_cleanup import ProcessCleanupConfig

                # Perform process cleanup before port allocation
                ProcessCleanupConfig(
                    cleanup_related_services=True,
                    cleanup_tunnels=True,
                    grace_period=2.0,
                )
                # Note: cleanup_before_startup is async, skip for now
                logger.info("🧹 Process cleanup skipped (sync context)")

                # Create port allocator and registry
                registry = PortRegistry()
                allocator = SmartPortAllocator(registry)

                # Allocate port for the service
                port = allocator.allocate_port(service_name)
                logger.info(f"🔧 pheno-sdk allocated port {port} for service '{service_name}'")
                return port

            except ImportError:
                logger.warning("⚠️  pheno-sdk not available, using default port")
                return DEFAULT_PORT
            except Exception as e:
                logger.warning(f"⚠️  pheno-sdk port allocation failed: {e}, using default port")
                return DEFAULT_PORT

        def setup_tunnel(self, local_port: int, domain: str = PUBLIC_DOMAIN) -> dict | None:
            """Setup Cloudflare tunnel for the service."""
            try:
                from pheno.infra.tunneling import TunnelManager, TunnelProtocol, TunnelType

                tunnel_config = {
                    "domain": domain,
                    "local_host": DEFAULT_HOST,
                    "local_port": local_port,
                    "tunnel_type": TunnelType.CLOUDFLARE.value,
                    "protocol": TunnelProtocol.HTTPS.value,
                }

                manager = TunnelManager(tunnel_config)
                tunnel_info = asyncio.run(manager.establish())

                logger.info(f"🌐 Tunnel established: {tunnel_info.public_url}")
                return {
                    "tunnel_id": tunnel_info.tunnel_id,
                    "public_url": tunnel_info.public_url,
                    "local_port": local_port,
                    "manager": manager
                }

            except ImportError:
                logger.warning("⚠️  pheno-sdk tunneling not available")
                return None
            except Exception as e:
                logger.warning(f"⚠️  Tunnel setup failed: {e}")
                return None

        async def start_mcp_server(self, port: int, dev_mode: bool = False, local_mode: bool = False) -> bool:
            """Start the MCP server process."""
            try:
                # Set environment variables
                env = os.environ.copy()
                env.update({
                    "ATOMS_FASTMCP_TRANSPORT": "http",
                    "ATOMS_FASTMCP_HOST": DEFAULT_HOST,
                    "ATOMS_FASTMCP_PORT": str(port),
                    "ATOMS_FASTMCP_HTTP_PATH": DEFAULT_HTTP_PATH,
                    "ENABLE_KINFRA": "true",
                    "LOG_LEVEL": "INFO",
                    "ENVIRONMENT": "development" if dev_mode else "production",
                    "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN": "http://localhost:3000",
                })

                if local_mode:
                    env["ATOMS_NO_TUNNEL"] = "true"

                # Build command - use conda python
                cmd = ["python", "-m", "server"]
                if dev_mode:
                    cmd.append("--reload")

                logger.info(f"🚀 Starting MCP server on {DEFAULT_HOST}:{port}")
                logger.info(f"   Command: {' '.join(cmd)}")
                logger.info(f"   Mode: {'LOCAL' if local_mode else 'DEV' if dev_mode else 'PRODUCTION'}")

                # Start the process
                self.process = subprocess.Popen(
                    cmd,
                    cwd=PROJECT_ROOT,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )

                # Wait a moment for startup
                await asyncio.sleep(2)

                # Check if process is still running
                if self.process.poll() is not None:
                    logger.error("❌ MCP server failed to start")
                    return False

                logger.info(f"✅ MCP server started with PID {self.process.pid}")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to start MCP server: {e}")
                return False

        async def stop_services(self) -> None:
            """Stop all running services."""
            logger.info("🛑 Stopping Atoms MCP services...")

            if self.process:
                try:
                    self.process.terminate()
                    await asyncio.sleep(1)
                    if self.process.poll() is None:
                        self.process.kill()
                    logger.info("✅ MCP server stopped")
                except Exception as e:
                    logger.error(f"❌ Error stopping MCP server: {e}")

            if self.tunnel_info and "manager" in self.tunnel_info:
                try:
                    await self.tunnel_info["manager"].teardown()
                    logger.info("✅ Tunnel closed")
                except Exception as e:
                    logger.error(f"❌ Error closing tunnel: {e}")

        def show_status(self) -> None:
            """Show status of running services."""
            print("\n" + "=" * 60)
            print("📊 Atoms MCP Service Status")
            print("=" * 60)

            if self.process and self.process.poll() is None:
                print(f"✅ MCP Server: Running (PID: {self.process.pid})")
                print(f"   URL: http://{DEFAULT_HOST}:{self.allocated_port}{DEFAULT_HTTP_PATH}")
                print(f"   Health: http://{DEFAULT_HOST}:{self.allocated_port}/health")
            else:
                print("❌ MCP Server: Not running")

            if self.tunnel_info:
                print("🌐 Tunnel: Active")
                print(f"   Public URL: {self.tunnel_info['public_url']}")
            else:
                print("🌐 Tunnel: Not active")

            print("=" * 60)

    # Start orchestration
    logger.info("=" * 60)
    logger.info("🎯 Atoms MCP Orchestrator Starting...")
    logger.info(f"   Mode: {'LOCAL' if local_mode else 'DEV' if dev_mode else 'PRODUCTION'}")
    logger.info("=" * 60)

    orchestrator = AtomsOrchestrator()

    # Allocate port
    orchestrator.allocated_port = orchestrator.allocate_port()

    # Setup tunnel if not in local mode
    if not local_mode:
        orchestrator.tunnel_info = orchestrator.setup_tunnel(orchestrator.allocated_port)

    # Start MCP server
    success = await orchestrator.start_mcp_server(
        port=orchestrator.allocated_port,
        dev_mode=dev_mode,
        local_mode=local_mode
    )

    if not success:
        logger.error("❌ Failed to start Atoms MCP services")
        await orchestrator.stop_services()
        sys.exit(1)

    # Show status
    orchestrator.show_status()

    try:
        # Monitor the process
        while True:
            if orchestrator.process and orchestrator.process.poll() is not None:
                logger.error("❌ MCP server process died unexpectedly")
                break
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down...")
        await orchestrator.stop_services()
        logger.info("✅ Shutdown complete")


def handle_deploy(args: argparse.Namespace) -> int:
    env = canonical_environment(args.environment, "production")

    if env == "local":
        start_args = argparse.Namespace(
            environment="local",
            port=args.port or 8000,
            verbose=args.verbose,
            no_tunnel=args.no_tunnel,
        )
        return handle_start(start_args)

    target = deployment_target(env)
    env_vars, settings = apply_environment(env)

    log_info(
        "Preparing deployment",
        environment=target,
        endpoint=env_vars.get("MCP_ENDPOINT"),
        base_url=getattr(settings, "resolved_base_url", None),
    )

    if target == "production" and not args.yes and not args.dry_run:
        print("\n" + "!" * 70)
        print("  WARNING: PRODUCTION DEPLOYMENT")
        print("!" * 70)
        prompt = input("Type 'deploy' to continue: ").strip().lower()
        if prompt != "deploy":
            print("Production deployment cancelled.")
            return 0

    if args.dry_run:
        log_info("Dry-run deployment", environment=target)
        print(f"[dry-run] Would deploy to {ENV_DISPLAY_NAMES.get(env, env)}")
        return 0

    try:
        from lib.atoms import deploy_atoms_to_vercel
    except ImportError as exc:  # pragma: no cover
        log_error("Unable to import deploy_atoms_to_vercel", error=str(exc))
        print("Error: Vercel deployment helper not available")
        return 1

    log_info("Deploying", environment=target)
    return deploy_atoms_to_vercel(
        environment=target,
        project_root=PROJECT_ROOT,
        logger=_LOGGER if USE_STRUCTURED_LOGGING else None,
    )


def handle_test(args: argparse.Namespace) -> int:
    tokens = list(args.tokens)

    env = "dev"
    if tokens and tokens[0].lower() in ENV_ALIASES:
        env = canonical_environment(tokens.pop(0), "dev")

    suite = args.suite or "unit"
    if tokens and tokens[0] in SUITE_PATHS:
        suite = tokens.pop(0)

    # Check if the next token is a test mode
    mode = args.mode  # Default from argument
    if tokens and tokens[0] in ["hot", "cold", "dry", "all"]:
        mode = tokens.pop(0)

    markers = list(tokens)
    if args.markers:
        markers.extend(args.markers)

    env_vars, settings = apply_environment(env)
    suite_path = SUITE_PATHS.get(suite, suite)

    pytest_cmd = ["pytest", suite_path]
    pytest_cmd.append("-vv" if args.verbose else "-v")

    # Add test mode
    pytest_cmd.extend(["--mode", mode])

    if args.workers:
        pytest_cmd.extend(["-n", str(args.workers)])
    if args.k:
        pytest_cmd.extend(["-k", args.k])
    if markers:
        marker_expr = " and ".join(markers)
        pytest_cmd.extend(["-m", marker_expr])

    env_copy = os.environ.copy()
    env_copy.update(env_vars)

    print("\n" + "=" * 70)
    print("  Running Tests")
    print("=" * 70)
    print(f" Environment: {ENV_DISPLAY_NAMES.get(env, env)}")
    if env_vars.get("MCP_ENDPOINT"):
        print(f" Endpoint:   {env_vars['MCP_ENDPOINT']}")
    if settings and getattr(settings, "resolved_base_url", None):
        print(f" Base URL:   {settings.resolved_base_url}")
    if markers:
        print(f" Markers:    {' '.join(markers)}")
    print("=" * 70 + "\n")

    return run_subprocess(pytest_cmd, env=env_copy)


def handle_schema(args: argparse.Namespace) -> int:
    env = canonical_environment(args.environment, "dev")
    apply_environment(env)

    script = PROJECT_ROOT / "scripts" / "sync_schema.py"
    action = args.action
    command = [sys.executable, str(script)]
    if action == "check":
        command.append("--check")
    elif action == "sync":
        command.append("--update")
    elif action == "diff":
        command.append("--diff")
    else:  # status/report
        command.append("--report")

    return run_subprocess(command)


def handle_embeddings(args: argparse.Namespace) -> int:
    env = canonical_environment(args.environment, "dev")
    apply_environment(env)

    if args.action == "backfill":
        script = PROJECT_ROOT / "scripts" / "backfill_embeddings.py"
        command = [sys.executable, str(script)]
        if args.batch_size:
            command.extend(["--batch-size", str(args.batch_size)])
        if args.verbose:
            command.append("--verbose")
        return run_subprocess(command)

    script = PROJECT_ROOT / "scripts" / "check_embedding_status.py"
    command = [sys.executable, str(script)]
    return run_subprocess(command)


def handle_vendor(args: argparse.Namespace) -> int:
    from lib.vendor_manager import VendorManager

    manager = VendorManager()

    if args.action == "setup":
        return 0 if manager.vendor_all(clean=args.clean) else 1
    if args.action == "verify":
        if not manager.check_prerequisites():
            return 1
        success_count, error_count = manager.verify_vendored_packages()
        print(f"\nVerified {success_count} packages with {error_count} error(s)")
        return 0 if error_count == 0 else 1
    if args.action == "clean":
        manager.clean_vendor()
        return 0
    print("Unknown vendor action")
    return 1


def handle_sync(args: argparse.Namespace) -> int:
    """Sync dependencies with local pheno-sdk."""
    import subprocess
    from pathlib import Path

    if args.verbose:
        print("🔄 Syncing dependencies with pheno-sdk...")

    # Check if pheno-sdk exists (for local option)
    if args.local:
        pheno_sdk_path = Path("../pheno-sdk").resolve()
        if not pheno_sdk_path.exists():
            log_error(f"pheno-sdk not found at {pheno_sdk_path}")
            return 1
        if args.verbose:
            print(f"Using local pheno-sdk at {pheno_sdk_path}")

    # Build uv sync command
    cmd = ["uv", "sync"]

    if args.dev:
        cmd.append("--dev")

    if args.verbose:
        cmd.append("--verbose")

    try:
        if args.verbose:
            print(f"Running: {' '.join(cmd)}")

        subprocess.run(cmd, check=True, capture_output=not args.verbose, text=True)

        if args.verbose:
            print("✅ Dependencies synced successfully")
        else:
            print("✅ Dependencies synced successfully")

        return 0
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to sync dependencies: {e}")
        if not args.verbose and e.stderr:
            print(f"Error: {e.stderr}")
        return 1
    except FileNotFoundError:
        log_error("uv not found. Please install uv first: pip install uv")
        return 1


def handle_config(args: argparse.Namespace) -> int:
    env = canonical_environment(args.environment, "production")
    env_vars, settings = apply_environment(env)

    if args.action == "show":
        data: dict[str, Any] = settings.model_dump() if settings else {}
        for key, value in sorted(data.items()):
            print(f"{key}: {value}")
        return 0

    if args.action == "dump":
        import json

        data = settings.model_dump() if settings else {}
        print(json.dumps(data, indent=2, default=str))
        return 0

    if args.action == "env":
        for key in sorted(env_vars):
            print(f"{key}={env_vars[key]}")
        return 0

    return handle_validate(args)


def handle_validate(args: argparse.Namespace) -> int:
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "archive" / "old_entry_points"))
        from test_config import main as validate_config  # type: ignore import
    except ImportError as exc:  # pragma: no cover
        log_error("Configuration validator not available", error=str(exc))
        return 1
    return validate_config()


def handle_verify(args: argparse.Namespace) -> int:
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "archive" / "old_entry_points"))
        from verify_setup import main as verify_setup  # type: ignore import
    except ImportError as exc:  # pragma: no cover
        log_error("Setup verifier not available", error=str(exc))
        return 1
    return verify_setup()


def handle_check(args: argparse.Namespace) -> int:
    env = canonical_environment(args.environment, "production")
    apply_environment(env)

    from lib.deployment_checker import (
        DeploymentChecker,
        create_vercel_deployment_checks,
    )

    checker = DeploymentChecker()
    checks = create_vercel_deployment_checks()
    errors, warnings = checker.run_all(checks)

    if errors == 0 and warnings == 0:
        print("✅ All deployment checks passed.")
        return 0
    if errors == 0:
        print(f"⚠️  Deployment checks completed with {warnings} warning(s).")
        return 0
    print(f"❌ Deployment checks found {errors} error(s) and {warnings} warning(s).")
    return 1


def handle_stats(args: argparse.Namespace) -> int:
    tool = args.tool
    if tool == "cloc":
        if shutil.which("cloc") is None:
            log_error("cloc executable not found. Install cloc to use this command.")
            return 1
        command = ["cloc", "--exclude-from=.clocignore", "."]
        if args.json:
            command.append("--json")
        return run_subprocess(command)

    command = [
        "uv",
        "run",
        "vulture",
        ".",
        "--config",
        "pyproject.toml",
    ]
    if args.min_confidence is not None:
        command.extend(["--min-confidence", str(args.min_confidence)])
    if shutil.which("uv") is None:
        log_error("uv executable not found. Install uv to run vulture checks.")
        return 1
    return run_subprocess(command)


def handle_orchestrate(args: argparse.Namespace) -> int:
    """Handle orchestration launcher commands."""
    try:
        import sys

        from atoms_entry import main as orchestrate_main

        # Convert args to sys.argv format for the orchestration launcher
        orchestrate_args = ["atoms_entry.py"]

        if args.dev:
            orchestrate_args.append("--dev")
        if args.local:
            orchestrate_args.append("--local")
        if args.stop:
            orchestrate_args.append("--stop")
        if args.status:
            orchestrate_args.append("--status")
        if args.test:
            orchestrate_args.append("--test")
        if args.test_unit:
            orchestrate_args.append("--test-unit")
        if args.test_e2e:
            orchestrate_args.append("--test-e2e")

        # Temporarily replace sys.argv
        original_argv = sys.argv
        sys.argv = orchestrate_args

        try:
            orchestrate_main()
            return 0
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    except ImportError as exc:
        log_error("Unable to import orchestration launcher", error=str(exc))
        print("Error: Orchestration launcher not available")
        return 1
    except Exception as exc:
        log_error("Orchestration launcher failed", error=str(exc))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atoms",
        description="Unified interface for Atoms MCP operations.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # start
    start_parser = subparsers.add_parser("start", help="Start the MCP server locally.")
    start_parser.add_argument("environment", nargs="?", help="Environment (default: local).")
    start_parser.add_argument("--port", type=int, help="Port to bind (default: 8000).")
    start_parser.add_argument(
        "--no-tunnel",
        action="store_true",
        help="Disable Cloudflare tunnel.",
    )
    start_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output.")
    start_parser.set_defaults(func=handle_start)

    # deploy
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to Vercel or start locally.")
    deploy_parser.add_argument("environment", nargs="?", help="Environment (default: production).")
    deploy_parser.add_argument("--port", type=int, help="Port for local deployments.")
    deploy_parser.add_argument("--no-tunnel", action="store_true", help="Disable tunnel for local.")
    deploy_parser.add_argument("--verbose", action="store_true", help="Verbose local deploy output.")
    deploy_parser.add_argument("--dry-run", action="store_true", help="Print actions without executing.")
    deploy_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts.")
    deploy_parser.set_defaults(func=handle_deploy)

    # test
    test_parser = subparsers.add_parser("test", help="Run test suites.")
    test_parser.add_argument("tokens", nargs="*", help="Environment, suite, and markers.")
    test_parser.add_argument("--suite", help="Explicit suite (unit, integration, e2e, performance).")
    test_parser.add_argument("--mode", choices=["hot", "cold", "dry", "all"], default="hot", help="Test execution mode (default: hot).")
    test_parser.add_argument("-k", help="Pytest expression.")
    test_parser.add_argument("-m", "--markers", nargs="*", help="Additional pytest markers.")
    test_parser.add_argument("-w", "--workers", type=int, help="Number of parallel workers.")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose pytest output.")
    test_parser.set_defaults(func=handle_test)

    # schema
    schema_parser = subparsers.add_parser("schema", help="Manage schema synchronization.")
    schema_parser.add_argument(
        "action",
        choices=("check", "sync", "diff", "status"),
        help="Schema action to perform.",
    )
    schema_parser.add_argument("environment", nargs="?", help="Environment to target (default: dev).")
    schema_parser.set_defaults(func=handle_schema)

    # embeddings
    embeddings_parser = subparsers.add_parser("embeddings", help="Vector embedding workflows.")
    embeddings_parser.add_argument(
        "action",
        choices=("backfill", "status"),
        help="Embedding operation.",
    )
    embeddings_parser.add_argument("environment", nargs="?", help="Environment (default: dev).")
    embeddings_parser.add_argument("--batch-size", type=int, help="Batch size for backfill.")
    embeddings_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output.")
    embeddings_parser.set_defaults(func=handle_embeddings)

    # vendor
    vendor_parser = subparsers.add_parser("vendor", help="Manage vendored SDK packages.")
    vendor_parser.add_argument(
        "action",
        choices=("setup", "verify", "clean"),
        help="Vendor operation.",
    )
    vendor_parser.add_argument("--clean", action="store_true", help="Clean before setup.")
    vendor_parser.set_defaults(func=handle_vendor)

    # sync
    sync_parser = subparsers.add_parser("sync", help="Sync dependencies with local pheno-sdk.")
    sync_parser.add_argument(
        "--local",
        action="store_true",
        help="Use local pheno-sdk from ../pheno-sdk",
    )
    sync_parser.add_argument("--dev", action="store_true", help="Include dev dependencies.")
    sync_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output.")
    sync_parser.set_defaults(func=handle_sync)

    # config
    config_parser = subparsers.add_parser("config", help="Inspect configuration.")
    config_parser.add_argument(
        "action",
        choices=("show", "dump", "env", "validate"),
        help="Configuration action.",
    )
    config_parser.add_argument("environment", nargs="?", help="Environment (default: production).")
    config_parser.set_defaults(func=handle_config)

    # validate
    validate_parser = subparsers.add_parser("validate", help="Run configuration validation.")
    validate_parser.set_defaults(func=handle_validate)

    # verify
    verify_parser = subparsers.add_parser("verify", help="Verify system setup and dependencies.")
    verify_parser.set_defaults(func=handle_verify)

    # check
    check_parser = subparsers.add_parser("check", help="Run deployment readiness checks.")
    check_parser.add_argument("environment", nargs="?", help="Environment (default: production).")
    check_parser.set_defaults(func=handle_check)

    # stats
    stats_parser = subparsers.add_parser("stats", help="Code statistics utilities.")
    stats_parser.add_argument("tool", choices=("cloc", "vulture"), help="Tool to execute.")
    stats_parser.add_argument("--json", action="store_true", help="Emit JSON output (cloc only).")
    stats_parser.add_argument(
        "--min-confidence",
        type=int,
        help="Minimum confidence for vulture findings.",
    )
    stats_parser.set_defaults(func=handle_stats)

    # orchestrate - new command for using the orchestration launcher
    orchestrate_parser = subparsers.add_parser("orchestrate", help="Use KINFRA orchestration launcher.")
    orchestrate_parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode with live reload"
    )
    orchestrate_parser.add_argument(
        "--local",
        action="store_true",
        help="Run in local mode (uses localhost ports and disables tunnels)"
    )
    orchestrate_parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop all running Atoms MCP services"
    )
    orchestrate_parser.add_argument(
        "--status",
        action="store_true",
        help="Show status of running services"
    )
    orchestrate_parser.add_argument(
        "--test",
        action="store_true",
        help="Run all tests"
    )
    orchestrate_parser.add_argument(
        "--test-unit",
        action="store_true",
        help="Run unit tests only"
    )
    orchestrate_parser.add_argument(
        "--test-e2e",
        action="store_true",
        help="Run E2E tests only"
    )
    orchestrate_parser.set_defaults(func=handle_orchestrate)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    try:
        return args.func(args) or 0
    except KeyboardInterrupt:  # pragma: no cover - user interruption
        log_error("Command interrupted by user")
        return 130


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
