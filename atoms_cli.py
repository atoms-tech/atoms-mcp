#!/usr/bin/env python3
"""Atoms MCP command line interface."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

# Ensure project modules are importable
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "pheno_vendor"))

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


def apply_environment(env: str) -> tuple[dict[str, str], Any]:
    env_vars = environment_variables_for(env)
    for key, value in env_vars.items():
        if value is not None:
            os.environ[key] = value

    reset_settings_cache()
    try:
        settings = get_settings()
        settings.apply_to_environment(override=True)
    except Exception:  # pragma: no cover - defensive fallback
        settings = None

    return env_vars, settings


def run_subprocess(command: Sequence[str], *, env: dict[str, str] | None = None) -> int:
    log_info("Executing command", command=" ".join(command))
    result = subprocess.run(command, env=env)
    return result.returncode


def handle_start(args: argparse.Namespace) -> int:
    env = canonical_environment(args.environment, "local")
    env_vars, settings = apply_environment(env)

    log_info(
        "Starting server",
        environment=env,
        endpoint=env_vars.get("MCP_ENDPOINT"),
        base_url=getattr(settings, "resolved_base_url", None),
    )

    try:
        from lib.atoms import start_atoms_server
    except ImportError as exc:  # pragma: no cover - module missing
        log_error("Unable to import start_atoms_server", error=str(exc))
        print("Error: start_atoms_server not available")
        return 1

    port = args.port or 8000
    return start_atoms_server(
        port=port,
        verbose=args.verbose,
        no_tunnel=args.no_tunnel,
        logger=_LOGGER if USE_STRUCTURED_LOGGING else None,
    )


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

    markers = list(tokens)
    if args.markers:
        markers.extend(args.markers)

    env_vars, settings = apply_environment(env)
    suite_path = SUITE_PATHS.get(suite, suite)

    pytest_cmd = ["pytest", suite_path]
    pytest_cmd.append("-vv" if args.verbose else "-v")

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


def handle_config(args: argparse.Namespace) -> int:
    env = canonical_environment(args.environment, "production")
    env_vars, settings = apply_environment(env)

    if args.action == "show":
        data = settings.model_dump() if settings else {}
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
