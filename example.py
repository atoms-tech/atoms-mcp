#!/usr/bin/env python3
"""
BytePort Orchestration Launcher
================================

Unified launcher for all BytePort services using KInfra.

Features:
- Dynamic port allocation using KInfra PortRegistry
- Cloudflare tunnel management on byte.kooshapari.com
- Automatic process lifecycle management
- Environment variable cascade (root + service-specific)
- Live reload support for development
- Automatic cleanup of stale processes/tunnels

Usage:
    python byteport.py                  # Production mode
    python byteport.py --dev            # Development mode with live reload
    python byteport.py --local          # Local development (localhost ports)
    python byteport.py --stop           # Stop all services
    python byteport.py --status         # Show service status
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

# Add KInfra to path
KINFRA_PATH = Path.home() / "KInfra" / "libraries" / "python"
if KINFRA_PATH.exists():
    sys.path.insert(0, str(KINFRA_PATH))


def _discover_pheno_sdk_path() -> Path | None:
    """Locate the pheno-sdk repository for shared orchestration utilities."""
    candidates: list[Path] = []

    env_path = os.environ.get("PHENO_SDK_PATH")
    if env_path:
        candidates.append(Path(env_path).expanduser())

    byteport_root = Path(__file__).resolve().parent
    temp_root = byteport_root.parents[2]
    if temp_root.exists():
        candidates.extend(p for p in temp_root.glob("*/kush/pheno-sdk"))

    home_root = Path.home()
    candidates.extend(
        [
            home_root / "kush" / "pheno-sdk",
            home_root / "pheno-sdk",
        ]
    )

    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_dir():
            return resolved

    return None


PHENO_SDK_PATH = _discover_pheno_sdk_path()
if PHENO_SDK_PATH:
    sys.path.insert(0, str(PHENO_SDK_PATH))

try:
    from pheno.infra.orchestration import ServiceLauncher
    from pheno.infra.orchestrator import OrchestratorConfig
    from pheno.infra.service_manager import ServiceConfig
except ImportError as e:
    print(f"⚠️  Required libraries not found: {e}")
    print(f"   KInfra path: {KINFRA_PATH}")
    if PHENO_SDK_PATH:
        print(f"   pheno-sdk path: {PHENO_SDK_PATH}")
    else:
        print("   Set PHENO_SDK_PATH to the pheno-sdk repository root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("byteport")

# BytePort root directory
BYTEPORT_ROOT = Path(__file__).resolve().parent

DEFAULT_API_PORT = 8080
DEFAULT_FRONTEND_PORT = 3000
PUBLIC_DOMAIN = "byte.kooshapari.com"


def _collect_env_files(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if path.exists()]


def get_byteport_services(
    *,
    root_dir: Path,
    dev_mode: bool = False,
    local_mode: bool = False,
    api_port: int = DEFAULT_API_PORT,
    frontend_port: int = DEFAULT_FRONTEND_PORT,
) -> list[ServiceConfig]:
    """Assemble service configurations for BytePort."""
    root_dir / "backend" / "api"
    root_dir / "frontend" / "web-next"

    # Example code - commented out as classes are not defined
    # go_options = GoServiceOptions(
    #     name="api",
    #     project_root=root_dir,
    #     module_dir=api_dir,
    #     port=api_port,
    #     env_files=_collect_env_files([root_dir / "backend" / ".env"]),
    #     health_check_url=(f"http://localhost:{api_port}/api/v1/health" if local_mode else None),
    #     path_prefix="/api/v1",
    #     enable_tunnel=not local_mode,
    #     tunnel_domain=PUBLIC_DOMAIN,
    # )
    # api_service = build_go_service(options=go_options)
    api_service = None  # Placeholder

    frontend_extra_env = {}
    if local_mode:
        frontend_extra_env.update(
            {
                "NEXT_PUBLIC_USE_LOCAL": "true",
                "NEXT_PUBLIC_API_URL": f"http://localhost:{api_port}/api/v1",
                "NEXT_PUBLIC_WORKOS_REDIRECT_URI": f"http://localhost:{frontend_port}/auth/callback",
                "NEXT_PUBLIC_AUTHKIT_REDIRECT_URI": f"http://localhost:{frontend_port}/auth/callback",
            }
        )
    else:
        frontend_extra_env.update(
            {
                "NEXT_PUBLIC_API_URL": f"https://{PUBLIC_DOMAIN}/api/v1",
                "NEXT_PUBLIC_WORKOS_REDIRECT_URI": f"https://{PUBLIC_DOMAIN}/auth/callback",
                "NEXT_PUBLIC_AUTHKIT_REDIRECT_URI": f"https://{PUBLIC_DOMAIN}/auth/callback",
            }
        )

    # Example code - commented out as classes are not defined
    # nextjs_options = NextJSServiceOptions(
    #     name="frontend",
    #     project_root=root_dir,
    #     app_dir=frontend_dir,
    #     port=frontend_port,
    #     dev_mode=dev_mode,
    #     local_mode=local_mode,
    #     env_files=_collect_env_files(
    #         [
    #             frontend_dir / ".env.local",
    #             frontend_dir / ".env",
    #         ]
    #     ),
    #     extra_env=frontend_extra_env,
    #     enable_tunnel=not local_mode,
    #     tunnel_domain=PUBLIC_DOMAIN,
    # )
    # frontend_service = build_nextjs_service(options=nextjs_options)
    frontend_service = None  # Placeholder

    return [api_service, frontend_service] if api_service and frontend_service else []


def _create_launcher() -> ServiceLauncher:
    """Create a configured service launcher for BytePort."""
    def service_factory(**service_kwargs) -> list[ServiceConfig]:
        return get_byteport_services(root_dir=BYTEPORT_ROOT, **service_kwargs)

    return ServiceLauncher(
        project_name="byteport",
        service_factory=service_factory,
        dependencies={"frontend": ["api"]},
        kinfra_domain=PUBLIC_DOMAIN,
        logger=logger,
        startup_config=OrchestratorConfig(
            project_name="byteport",
            parallel_startup=False,
            auto_restart=True,
            save_state=True,
        ),
    )


async def start_services(dev_mode: bool = False, local_mode: bool = False) -> None:
    """Start all BytePort services using the reusable launcher."""
    logger.info("=" * 60)
    logger.info("🎯 BytePort Orchestrator Starting...")
    logger.info(f"   Mode: {'LOCAL' if local_mode else 'DEV' if dev_mode else 'PRODUCTION'}")
    logger.info("=" * 60)

    launcher = _create_launcher()
    success = await launcher.start(
        monitor=True,
        dev_mode=dev_mode or local_mode,
        local_mode=local_mode,
        api_port=DEFAULT_API_PORT,
        frontend_port=DEFAULT_FRONTEND_PORT,
    )

    if not success:
        logger.error("Failed to start BytePort services")
        sys.exit(1)


async def stop_services() -> None:
    """Stop all running BytePort services."""
    logger.info("🛑 Stopping all BytePort services...")

    launcher = _create_launcher()
    await launcher.stop(
        dev_mode=False,
        local_mode=False,
        api_port=DEFAULT_API_PORT,
        frontend_port=DEFAULT_FRONTEND_PORT,
    )


def show_status() -> None:
    """Show status of running BytePort services."""
    _create_launcher().show_status()


def run_tests(test_type: str = "all") -> None:
    """Run BytePort test suites via test_runner.py."""
    test_runner_path = BYTEPORT_ROOT / "scripts" / "test_runner.py"

    if not test_runner_path.exists():
        logger.error(f"Test runner not found: {test_runner_path}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info(f"🧪 Running {test_type.upper()} Tests")
    logger.info("=" * 60)

    cmd = [sys.executable, str(test_runner_path)]

    if test_type == "all":
        cmd.append("--all")
    elif test_type == "unit":
        cmd.extend(["--backend", "--frontend"])
    elif test_type == "e2e":
        cmd.append("--e2e")
    else:
        logger.error(f"Unknown test type: {test_type}")
        sys.exit(1)

    try:
        result = subprocess.run(cmd, cwd=BYTEPORT_ROOT)
        sys.exit(result.returncode)
    except Exception as e:
        logger.error(f"Failed to run tests: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BytePort Orchestration Launcher (KInfra-powered)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode with live reload"
    )

    parser.add_argument(
        "--local",
        action="store_true",
        help="Run in local mode (uses localhost ports and disables tunnels)"
    )

    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop all running BytePort services"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status of running services"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run all tests (backend, frontend, E2E)"
    )

    parser.add_argument(
        "--test-unit",
        action="store_true",
        help="Run unit tests only (backend Go tests + frontend Vitest)"
    )

    parser.add_argument(
        "--test-e2e",
        action="store_true",
        help="Run E2E tests only (Playwright)"
    )

    args = parser.parse_args()
    dev_mode = args.dev or args.local

    try:
        if args.stop:
            asyncio.run(stop_services())
        elif args.status:
            show_status()
        elif args.test:
            run_tests("all")
        elif args.test_unit:
            run_tests("unit")
        elif args.test_e2e:
            run_tests("e2e")
        else:
            asyncio.run(start_services(dev_mode=dev_mode, local_mode=args.local))
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as exc:
        logger.error(f"Fatal error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
