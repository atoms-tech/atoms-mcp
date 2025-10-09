#!/usr/bin/env python3
"""
Start Local Atoms MCP Server with KInfra or Deploy to Vercel

This script:
1. Allocates a persistent port using SmartInfraManager
2. Fixes server.py import errors
3. Starts the MCP server with proper configuration
4. Sets up CloudFlare tunnel to atomcp.kooshapari.com
5. Saves configuration for tests to use
6. Deploys to Vercel (preview or production)

Usage:
    python start_server.py                 # Start local server (default)
    python start_server.py --deploy-dev    # Deploy to Vercel preview (devmcp.atoms.tech)
    python start_server.py --deploy-prod   # Deploy to Vercel production (atomcp.kooshapari.com)
    python start_server.py --port PORT     # Start local server on specific port
    python start_server.py --no-tunnel     # Start local server without CloudFlare tunnel
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from kinfra import get_smart_infra_manager
from utils.logging_setup import setup_logging, get_logger

logger = get_logger(__name__)


def deploy_to_vercel(environment: str) -> int:
    """Deploy to Vercel with environment-specific configuration.

    Args:
        environment: "preview" or "production"

    Returns:
        0 on success, 1 on failure
    """
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
        logger.error(f"Invalid environment: {environment}")
        return 1

    # Verify env file exists
    env_path = Path(__file__).parent / env_file
    if not env_path.exists():
        logger.error(f"Environment file not found: {env_file}")
        print(f"\nError: {env_file} not found")
        return 1

    logger.info(f"Using environment file: {env_file}")

    # Check if vercel CLI is installed
    try:
        result = subprocess.run(
            ["vercel", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Vercel CLI version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Vercel CLI not found")
        print("\nError: Vercel CLI not installed")
        print("Install with: npm install -g vercel")
        return 1

    # Build deployment command
    if environment == "production":
        # Production deployment
        deploy_cmd = ["vercel", "--prod", "--yes"]
        logger.info("Deploying to production with --prod flag")
    else:
        # Preview deployment
        deploy_cmd = ["vercel", "--yes"]
        logger.info("Deploying to preview environment")

    print(f"\nStarting deployment to {domain}...")
    print(f"Environment: {environment}")
    print(f"Config file: {env_file}")
    print("\nThis may take a few minutes...\n")

    # Run deployment
    try:
        logger.info(f"Running command: {' '.join(deploy_cmd)}")
        result = subprocess.run(
            deploy_cmd,
            cwd=Path(__file__).parent,
            check=True,
            text=True,
            capture_output=False  # Show output in real-time
        )

        deployment_url = None
        logger.info("Deployment completed successfully")

    except subprocess.CalledProcessError as e:
        logger.error(f"Deployment failed: {e}")
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
                logger.info(f"Health check attempt {attempt + 1}/{max_retries}")
                req = urllib.request.Request(health_url)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        logger.info("Health check passed")
                        print(f"Health check passed!")
                        break
            except urllib.error.HTTPError as e:
                logger.warning(f"Health check failed with status {e.code}")
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries - 1} in {retry_delay}s...")
                    time.sleep(retry_delay)
            except Exception as e:
                logger.warning(f"Health check error: {e}")
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries - 1} in {retry_delay}s...")
                    time.sleep(retry_delay)
        else:
            logger.warning("Health check could not be verified")
            print("\nWarning: Could not verify deployment health")
            print("The deployment may still be propagating or there may be an issue")
    except ImportError:
        logger.warning("urllib not available for health check")
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


def main():
    """Main entry point for server startup or deployment.

    Modes:
    1. Local server (default): Start local server with CloudFlare tunnel
    2. Deploy to preview: Deploy to Vercel preview environment (devmcp.atoms.tech)
    3. Deploy to production: Deploy to Vercel production (atomcp.kooshapari.com)
    """
    parser = argparse.ArgumentParser(
        description="Start local Atoms MCP server or deploy to Vercel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_server.py                 # Start local server (default)
  python start_server.py --deploy-dev    # Deploy to preview (devmcp.atoms.tech)
  python start_server.py --deploy-prod   # Deploy to production (atomcp.kooshapari.com)
  python start_server.py --port 50003    # Start local on custom port
        """
    )

    # Deployment flags (mutually exclusive)
    deploy_group = parser.add_mutually_exclusive_group()
    deploy_group.add_argument(
        "--deploy-dev",
        action="store_true",
        help="Deploy to Vercel preview environment (devmcp.atoms.tech)"
    )
    deploy_group.add_argument(
        "--deploy-prod",
        action="store_true",
        help="Deploy to Vercel production (atomcp.kooshapari.com)"
    )

    # Local server options
    parser.add_argument("--port", type=int, help="Specify port for local server (default: 50002)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--no-tunnel",
        action="store_true",
        help="Disable CloudFlare tunnel for local server (WARNING: OAuth requires HTTPS)"
    )

    args = parser.parse_args()

    # Handle deployment modes
    if args.deploy_dev:
        # Setup logging for deployment
        setup_logging(level="INFO")
        return deploy_to_vercel("preview")

    if args.deploy_prod:
        # Setup logging for deployment
        setup_logging(level="INFO")
        # Confirm production deployment
        print("\n" + "!"*70)
        print("  WARNING: PRODUCTION DEPLOYMENT")
        print("!"*70)
        print("\nYou are about to deploy to PRODUCTION (atomcp.kooshapari.com)")
        print("This will affect all users immediately.")
        print("\nPlease confirm you want to proceed.")

        response = input("\nType 'yes' to continue, or anything else to cancel: ")
        if response.lower() != 'yes':
            print("\nProduction deployment cancelled.")
            return 0

        return deploy_to_vercel("production")

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)

    print("\n" + "="*70)
    print("  Atoms MCP Local Server Startup")
    print("  (CloudFlare tunnel required for OAuth)")
    print("="*70 + "\n")

    # Initialize SmartInfraManager
    logger.info("Initializing SmartInfraManager for atoms_mcp...")
    infra = get_smart_infra_manager(
        project_name="atoms_mcp",
        domain="atomcp.kooshapari.com"
    )

    # Set AUTO_TUNNEL environment variable (enabled by default)
    enable_tunnel = not args.no_tunnel
    if enable_tunnel:
        os.environ["AUTO_TUNNEL"] = "true"
        logger.info("CloudFlare tunnel enabled")

    # Allocate port - default to 50002 for atoms (50001 is used by zen)
    if args.port:
        port = args.port
        logger.info(f"Using specified port: {port}")
    else:
        # Use fixed port 50002 for atoms
        port = 50002
        logger.info(f"Using default atoms port: {port}")

    print(f"\nPort: {port}")

    # Load environment variables from .env
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            logger.info("Loaded environment variables from .env")
        except ImportError:
            logger.warning("python-dotenv not installed, skipping .env loading")

    # Set environment variables for server
    os.environ["ATOMS_FASTMCP_PORT"] = str(port)
    os.environ["ATOMS_FASTMCP_HOST"] = "127.0.0.1"
    os.environ["ATOMS_FASTMCP_TRANSPORT"] = "http"
    os.environ["ATOMS_LOCAL_PORT"] = str(port)
    os.environ["ATOMS_USE_LOCAL_SERVER"] = "true"

    # For local development, use local domain
    if args.tunnel:
        # Will be set after tunnel starts
        pass
    else:
        os.environ["FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL"] = f"http://localhost:{port}"

    # Save configuration for tests
    config_dir = Path.home() / ".atoms_mcp_test_cache"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "local_server_config.json"

    import json
    server_config = {
        "port": port,
        "host": "127.0.0.1",
        "base_url": f"http://localhost:{port}",
        "api_endpoint": f"http://localhost:{port}/api/mcp",
        "tunnel_enabled": enable_tunnel,
        "domain": "atomcp.kooshapari.com",
        "started_at": time.time(),
    }

    with open(config_file, "w") as f:
        json.dump(server_config, f, indent=2)

    logger.info(f"Server configuration saved to {config_file}")

    # Start CloudFlare tunnel (enabled by default, required for OAuth)
    enable_tunnel = not args.no_tunnel
    tunnel_url = None

    if enable_tunnel:
        logger.info("Starting CloudFlare tunnel to atomcp.kooshapari.com...")
        print("\nStarting CloudFlare tunnel...")
        print("This provides HTTPS access required for OAuth")

        tunnel_url = infra.start_cloudflare_tunnel(port, force_restart=False)
        if tunnel_url:
            print(f"\nTunnel URL: {tunnel_url}")
            print(f"MCP Endpoint: {tunnel_url}/api/mcp")

            # Update server config with tunnel URL
            server_config["tunnel_url"] = tunnel_url
            server_config["base_url"] = tunnel_url
            server_config["api_endpoint"] = f"{tunnel_url}/api/mcp"

            # Update environment for server
            os.environ["FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL"] = tunnel_url

            with open(config_file, "w") as f:
                json.dump(server_config, f, indent=2)
        else:
            logger.error("Failed to start CloudFlare tunnel")
            print("\nFailed to start tunnel. Server will only be accessible via localhost.")

    # Display server information
    print("\n" + "-"*70)
    print("  Server Configuration")
    print("-"*70)
    print(f"  Local URL:     http://localhost:{port}")
    print(f"  MCP Endpoint:  http://localhost:{port}/api/mcp")
    if tunnel_url:
        print(f"  Public URL:    {tunnel_url}")
        print(f"  Public MCP:    {tunnel_url}/api/mcp")
    print(f"  Domain:        atomcp.kooshapari.com")
    print("-"*70 + "\n")

    # Import and verify server can be loaded
    try:
        logger.info("Verifying server imports...")
        from server import create_consolidated_server
        logger.info("Server imports verified successfully")
    except ImportError as e:
        logger.error(f"Server import error: {e}")
        print(f"\nError: Failed to import server: {e}")
        print("\nTrying to fix import errors...")

        # Check if auth modules exist
        auth_dir = Path(__file__).parent / "auth"
        if not auth_dir.exists():
            logger.error("auth/ directory not found")
        else:
            logger.info("auth/ directory exists")

            # List auth modules
            auth_files = list(auth_dir.glob("*.py"))
            logger.info(f"Found auth modules: {[f.name for f in auth_files]}")

            # Check for missing modules
            required_modules = [
                "persistent_authkit_provider.py",
                "session_middleware.py",
            ]

            for module in required_modules:
                module_path = auth_dir / module
                if not module_path.exists():
                    logger.error(f"Missing auth module: {module}")
                else:
                    logger.info(f"Found auth module: {module}")

        return 1

    # Start the server
    print("Starting MCP server...")
    print("Press Ctrl+C to stop\n")

    try:
        # Run server using main() from server.py
        from server import main as server_main
        server_main()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        logger.info("Server stopped by user")

        # Cleanup
        if enable_tunnel and tunnel_url:
            logger.info("Stopping CloudFlare tunnel...")
            infra.kill_tunnel_for_port(port)

        print("\nServer stopped successfully")
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        print(f"\nServer error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
