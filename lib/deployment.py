"""
Lightweight deployment utilities for Atoms MCP.

This module provides deployment functions that can be used by both
the atoms-mcp CLI and potentially moved to pheno-sdk/deploy-kit.

Classes and functions are designed to be framework-agnostic and
can be easily moved to pheno-sdk.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any


def deploy_to_vercel(
    environment: str,
    project_root: Optional[Path] = None,
    logger=None
) -> int:
    """Deploy to Vercel with environment-specific configuration.

    Args:
        environment: "preview" or "production"
        project_root: Root directory of the project (default: current file's parent)
        logger: Optional logger instance (uses print if None)

    Returns:
        0 on success, 1 on failure
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent

    def log_info(msg):
        if logger:
            logger.info(msg)
        else:
            print(f"INFO: {msg}")

    def log_error(msg):
        if logger:
            logger.error(msg)
        else:
            print(f"ERROR: {msg}")

    def log_warning(msg):
        if logger and hasattr(logger, 'warning'):
            logger.warning(msg)
        else:
            print(f"WARNING: {msg}")

    print("\n" + "="*70)
    print(f"  Deploying to Vercel ({environment})")
    print("="*70 + "\n")

    # Determine target domain and env file
    if environment == "preview":
        domain = "devmcp.atoms.tech"
        env_file = ".env.preview"
    elif environment == "production":
        domain = "atomcp.kooshapari.com"
        env_file = ".env.production"
    else:
        log_error(f"Invalid environment: {environment}")
        return 1

    # Verify env file exists
    env_path = project_root / env_file
    if not env_path.exists():
        log_error(f"Environment file not found: {env_file}")
        print(f"\nError: {env_file} not found")
        return 1

    log_info(f"Using environment file: {env_file}")

    # Check if vercel CLI is installed
    try:
        result = subprocess.run(
            ["vercel", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        log_info(f"Vercel CLI version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_error("Vercel CLI not found")
        print("\nError: Vercel CLI not installed")
        print("Install with: npm install -g vercel")
        return 1

    # Build deployment command
    if environment == "production":
        # Production deployment
        deploy_cmd = ["vercel", "--prod", "--yes"]
        log_info("Deploying to production with --prod flag")
    else:
        # Preview deployment
        deploy_cmd = ["vercel", "--yes"]
        log_info("Deploying to preview environment")

    print(f"\nStarting deployment to {domain}...")
    print(f"Environment: {environment}")
    print(f"Config file: {env_file}")
    print("\nThis may take a few minutes...\n")

    # Run deployment
    try:
        log_info(f"Running command: {' '.join(deploy_cmd)}")
        result = subprocess.run(
            deploy_cmd,
            cwd=project_root,
            check=True,
            text=True,
            capture_output=False  # Show output in real-time
        )

        log_info("Deployment completed successfully")

    except subprocess.CalledProcessError as e:
        log_error(f"Deployment failed: {e}")
        print(f"\nDeployment failed with exit code {e.returncode}")
        print("\nTroubleshooting:")
        print("1. Ensure you're logged in: vercel login")
        print("2. Ensure the project is linked: vercel link")
        print("3. Check environment variables in Vercel dashboard")
        return 1

    # Wait a moment for deployment to propagate
    print("\nWaiting for deployment to propagate...")
    time.sleep(3)

    # Check deployment health
    print(f"\nChecking deployment health at {domain}...")
    health_url = f"https://{domain}/health"

    try:
        import urllib.request
        import urllib.error

        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                log_info(f"Health check attempt {attempt + 1}/{max_retries}")
                req = urllib.request.Request(health_url)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        log_info("Health check passed")
                        print(f"Health check passed!")
                        break
            except urllib.error.HTTPError as e:
                log_warning(f"Health check failed with status {e.code}")
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries - 1} in {retry_delay}s...")
                    time.sleep(retry_delay)
            except Exception as e:
                log_warning(f"Health check error: {e}")
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries - 1} in {retry_delay}s...")
                    time.sleep(retry_delay)
        else:
            log_warning("Health check could not be verified")
            print("\nWarning: Could not verify deployment health")
            print("The deployment may still be propagating or there may be an issue")
    except ImportError:
        log_warning("urllib not available for health check")
        print("\nSkipping health check (urllib not available)")

    # Display deployment info
    print("\n" + "-"*70)
    print("  Deployment Summary")
    print("-"*70)
    print(f"  Environment:   {environment}")
    print(f"  Domain:        {domain}")
    print(f"  URL:           https://{domain}")
    print(f"  MCP Endpoint:  https://{domain}/api/mcp")
    print(f"  Health Check:  https://{domain}/health")
    print("-"*70)

    print("\nDeployment completed successfully!")
    print("\nNext steps:")
    print("1. Verify the deployment at the URL above")
    print("2. Test the MCP endpoint with your client")
    print("3. Monitor logs in Vercel dashboard")

    if environment == "production":
        print("\nNote: This is a PRODUCTION deployment")
        print("All users will see this version immediately")
    else:
        print("\nNote: This is a PREVIEW deployment")
        print("Use for testing before promoting to production")

    return 0


class VercelDeployer:
    """Vercel deployment manager (framework-agnostic)."""

    def __init__(self, project_root: Optional[Path] = None, logger=None):
        self.project_root = project_root or Path.cwd()
        self.logger = logger

    def log_info(self, msg: str):
        if self.logger:
            self.logger.info(msg)

    def log_error(self, msg: str):
        if self.logger:
            self.logger.error(msg)

    def log_warning(self, msg: str):
        if self.logger and hasattr(self.logger, 'warning'):
            self.logger.warning(msg)

    def check_cli_installed(self) -> bool:
        """Check if Vercel CLI is installed."""
        try:
            result = subprocess.run(
                ["vercel", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            self.log_info(f"Vercel CLI version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_error("Vercel CLI not found")
            return False

    def deploy(
        self,
        environment: str,
        production: bool = False
    ) -> int:
        """Deploy to Vercel."""
        cmd = ["vercel", "--yes"]
        if production:
            cmd.insert(1, "--prod")

        self.log_info(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                check=True,
                text=True,
                capture_output=False
            )
            self.log_info("Deployment completed successfully")
            return 0
        except subprocess.CalledProcessError as e:
            self.log_error(f"Deployment failed: {e}")
            return 1


class HealthChecker:
    """Health check utilities (framework-agnostic)."""

    @staticmethod
    def check_url(
        url: str,
        max_retries: int = 5,
        retry_delay: int = 2,
        timeout: int = 10,
        logger=None
    ) -> bool:
        """Check if URL is healthy."""
        import urllib.request
        import urllib.error

        for attempt in range(max_retries):
            try:
                if logger:
                    logger.info(f"Health check attempt {attempt + 1}/{max_retries}")

                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.status == 200:
                        if logger:
                            logger.info("Health check passed")
                        return True
            except urllib.error.HTTPError as e:
                if logger:
                    logger.warning(f"Health check failed with status {e.code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                if logger:
                    logger.warning(f"Health check error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        return False


def start_local_server(
    port: Optional[int] = None,
    verbose: bool = False,
    no_tunnel: bool = False,
    logger=None
):
    """Start local server with KInfra tunnel.

    This is a lightweight wrapper that delegates to start_server.py.

    Args:
        port: Port to run on (default: 50002)
        verbose: Enable verbose logging
        no_tunnel: Disable CloudFlare tunnel
        logger: Optional logger instance

    Returns:
        Exit code from start_server.py
    """
    import sys

    # Build command
    cmd = [sys.executable, str(Path(__file__).parent.parent / "start_server.py")]

    if port:
        cmd.extend(["--port", str(port)])
    if verbose:
        cmd.append("--verbose")
    if no_tunnel:
        cmd.append("--no-tunnel")

    # Run start_server.py
    result = subprocess.run(cmd)
    return result.returncode

