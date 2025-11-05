"""
Helper functions for Atoms CLI operations.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

import httpx

from atoms_cli_enhanced import CICheckError, DeploymentError, GitStateError, HealthCheckError


async def run_command(
    command: str, cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """
    Run a shell command asynchronously.

    Args:
        command: Command to run
        cwd: Working directory
        env: Environment variables

    Returns:
        CompletedProcess with result
    """
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd, env=env
    )

    stdout, stderr = await process.communicate()

    returncode = process.returncode
    if returncode is None:
        returncode = 0  # Default to 0 if None

    return subprocess.CompletedProcess(
        args=command, returncode=returncode, stdout=stdout.decode(), stderr=stderr.decode()
    )


async def run_ci_checks(checks: list[dict[str, Any]], cwd: Path) -> bool:
    """
    Run all CI/CD checks.

    Args:
        checks: List of check configurations
        cwd: Working directory

    Returns:
        True if all checks pass

    Raises:
        CICheckError: If any required check fails
    """

    for check in checks:
        name = check.get("name", "unknown")
        command = check.get("command", "")
        required = check.get("required", True)

        print(f"  Running {name}...")
        result = await run_command(command, cwd=cwd)

        if result.returncode != 0:
            if required:
                raise CICheckError(f"{name} failed:\n{result.stderr}")
            print(f"  Warning: {name} failed (non-required)")
        else:
            print(f"  ✓ {name} passed")

    return True


async def validate_git_state(cwd: Path) -> bool:
    """
    Validate that git state is clean and pushed.

    Args:
        cwd: Working directory

    Returns:
        True if git state is valid

    Raises:
        GitStateError: If git state is invalid
    """

    # Check for uncommitted changes
    result = await run_command("git status --porcelain", cwd=cwd)
    if result.stdout.strip():
        raise GitStateError("Uncommitted changes detected. Please commit all changes before deploying to production.")

    # Check for unpushed commits
    result = await run_command("git log @{u}..", cwd=cwd)
    if result.stdout.strip():
        raise GitStateError("Unpushed commits detected. Please push all commits before deploying to production.")

    return True


async def build_application(cwd: Path) -> bool:
    """
    Build the application.

    Args:
        cwd: Working directory

    Returns:
        True if build succeeds

    Raises:
        DeploymentError: If build fails
    """

    # Run build command
    result = await run_command("python -m build", cwd=cwd)

    if result.returncode != 0:
        raise DeploymentError(f"Build failed:\n{result.stderr}")

    return True


async def deploy_to_vercel(env: str, domain: str, cwd: Path, vercel_token: str | None = None) -> dict[str, str]:
    """
    Deploy to Vercel using CLI.

    Args:
        env: Environment (preview/production)
        domain: Domain name
        cwd: Working directory
        vercel_token: Vercel API token

    Returns:
        Deployment result with URL

    Raises:
        DeploymentError: If deployment fails
    """

    # Prepare command
    command = "vercel --prod" if env == "production" else "vercel"

    # Add token if provided
    env_vars = {}
    if vercel_token:
        env_vars["VERCEL_TOKEN"] = vercel_token

    # Run deployment
    result = await run_command(command, cwd=cwd, env=env_vars)

    if result.returncode != 0:
        raise DeploymentError(f"Vercel deployment failed:\n{result.stderr}")

    # Extract URL from output
    url = f"https://{domain}"

    return {"url": url, "environment": env, "domain": domain}


async def health_check(url: str, timeout: int = 30, retries: int = 3) -> bool:
    """
    Perform health check on deployed service.

    Args:
        url: URL to check
        timeout: Timeout in seconds
        retries: Number of retries

    Returns:
        True if health check passes

    Raises:
        HealthCheckError: If health check fails
    """

    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                response = await client.get(url, timeout=timeout)
                if response.status_code == 200:
                    return True
                print(f"  Health check attempt {attempt + 1}/{retries} failed: {response.status_code}")
            except Exception as e:
                print(f"  Health check attempt {attempt + 1}/{retries} failed: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(5)

        raise HealthCheckError(f"Health check failed after {retries} attempts")


async def run_smoke_tests(url: str, tests: list[dict[str, Any]]) -> bool:
    """
    Run smoke tests against deployed service.

    Args:
        url: Base URL of service
        tests: List of test configurations

    Returns:
        True if all tests pass

    Raises:
        HealthCheckError: If any test fails
    """

    async with httpx.AsyncClient() as client:
        for test in tests:
            name = test.get("name", "unknown")
            endpoint = test.get("endpoint", "/")
            expected_status = test.get("expected_status", 200)

            print(f"  Running smoke test: {name}...")

            try:
                response = await client.get(f"{url}{endpoint}", timeout=10)
                if response.status_code == expected_status:
                    print(f"  ✓ {name} passed")
                else:
                    raise HealthCheckError(
                        f"Smoke test '{name}' failed: expected {expected_status}, got {response.status_code}"
                    )
            except httpx.RequestError as e:
                raise HealthCheckError(f"Smoke test '{name}' failed: {e}") from e

    return True


async def cleanup_stale_processes(port: int):
    """
    Cleanup stale processes on a port.

    Args:
        port: Port number
    """
    try:
        # Find process using port
        result = await run_command(f"lsof -ti :{port}")
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                print(f"  Killing process {pid} on port {port}")
                await run_command(f"kill -9 {pid}")
    except Exception as e:
        print(f"  Warning: Failed to cleanup port {port}: {e}")


async def cleanup_stale_tunnels():
    """Cleanup stale Cloudflare tunnels."""
    try:
        result = await run_command("cloudflared tunnel cleanup")
        if result.returncode == 0:
            print("  ✓ Cleaned up stale tunnels")
    except Exception as e:
        print(f"  Warning: Failed to cleanup tunnels: {e}")


def confirm_deployment(environment: str) -> bool:
    """
    Prompt user to confirm deployment.

    Args:
        environment: Environment name

    Returns:
        True if user confirms
    """
    response = input(f"\n⚠️  Deploy to {environment}? This will update the live service. [y/N]: ")
    return response.lower() in ["y", "yes"]


async def start_server_process(
    port: int, workers: int, env_vars: dict[str, str], cwd: Path
) -> asyncio.subprocess.Process:
    """
    Start the server process.

    Args:
        port: Port to bind to
        workers: Number of worker processes
        env_vars: Environment variables
        cwd: Working directory

    Returns:
        Process object
    """
    # Prepare environment
    env = {**os.environ, **env_vars}
    env["PORT"] = str(port)
    env["WORKERS"] = str(workers)

    # Start process
    process = await asyncio.create_subprocess_exec(
        "python",
        "-m",
        "atoms_mcp.server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
    )

    # Wait a bit for startup
    await asyncio.sleep(2)

    return process


async def launch_tui_dashboard(services: list[dict], tunnel_info, refresh_interval: float = 1.0):
    """
    Launch TUI dashboard for monitoring.

    Args:
        services: List of service information
        tunnel_info: Tunnel information
        refresh_interval: Refresh interval in seconds
    """
    # This will be implemented using Rich Live display
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table

    console = Console()

    def generate_table():
        """Generate status table."""
        table = Table(title="Atoms MCP Server Status")
        table.add_column("Service", style="cyan")
        table.add_column("PID", style="magenta")
        table.add_column("Port", style="green")
        table.add_column("Status", style="yellow")

        for service in services:
            table.add_row(
                service.get("name", "unknown"),
                str(service.get("pid", "N/A")),
                str(service.get("port", "N/A")),
                service.get("status", "unknown"),
            )

        return table

    # Display dashboard
    with Live(generate_table(), refresh_per_second=1 / refresh_interval, console=console):
        try:
            # Keep running until interrupted
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
