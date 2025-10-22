#!/usr/bin/env python3
"""
Atoms MCP Entry Point - Orchestration Launcher
==============================================

Unified launcher for Atoms MCP services with full orchestration support.

Features:
- MCP server startup with HTTP/stdio transport
- Port allocation using pheno-sdk
- Process cleanup and resource management
- Cloudflare tunnel support
- CLI monitoring and management
- Development and production modes

Usage:
    ./atoms orchestrate              # Start MCP server
    ./atoms orchestrate --dev        # Vercel preview mode
    ./atoms orchestrate --local      # Local mode with tunnels
    ./atoms orchestrate --stop       # Stop all services
    ./atoms orchestrate --status     # Show service status
    ./atoms orchestrate --help       # Show help
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "pheno-sdk" / "src"))

# Make project_root available globally
PROJECT_ROOT = project_root

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
            # Note: cleanup_before_startup is async, but we're in a sync context
            # For now, skip cleanup to avoid asyncio issues
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
            from pheno.infra.tunneling import TunnelConfig, TunnelManager, TunnelProtocol, TunnelType

            tunnel_config = TunnelConfig(
                name="atoms-mcp-tunnel",
                local_host=DEFAULT_HOST,
                local_port=local_port,
                tunnel_type=TunnelType.CLOUDFLARE,
                protocol=TunnelProtocol.HTTPS,
            )

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
            logger.info(f"   Mode: {'LOCAL (with tunnels)' if local_mode else 'DEV (Vercel preview)' if dev_mode else 'PRODUCTION (Vercel prod)'}")

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


async def start_services(dev_mode: bool = False, local_mode: bool = False) -> None:
    """Start all Atoms MCP services."""
    logger.info("=" * 60)
    logger.info("🎯 Atoms MCP Orchestrator Starting...")
    logger.info(f"   Mode: {'LOCAL (with tunnels)' if local_mode else 'DEV (Vercel preview)' if dev_mode else 'PRODUCTION (Vercel prod)'}")
    logger.info("=" * 60)

    orchestrator = AtomsOrchestrator()

    # Allocate port
    orchestrator.allocated_port = orchestrator.allocate_port()

    # Setup tunnel for local mode (local has tunnels, just not in production)
    if local_mode:
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


async def stop_services() -> None:
    """Stop all running Atoms MCP services."""
    logger.info("🛑 Stopping all Atoms MCP services...")

    # Try to find and stop existing processes
    try:
        result = subprocess.run(
            ["pkill", "-f", "atoms.*server"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("✅ Stopped existing Atoms MCP processes")
        else:
            logger.info("ℹ️  No existing processes found")
    except Exception as e:
        logger.warning(f"⚠️  Error stopping processes: {e}")


def show_status() -> None:
    """Show status of running Atoms MCP services."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "atoms.*server"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ Atoms MCP processes running: {', '.join(pids)}")
        else:
            print("❌ No Atoms MCP processes found")
    except Exception as e:
        print(f"❌ Error checking status: {e}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Atoms MCP Orchestration Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in Vercel preview mode"
    )

    parser.add_argument(
        "--local",
        action="store_true",
        help="Run in local mode with tunnels"
    )

    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop all running Atoms MCP services"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status of running services"
    )

    args = parser.parse_args()

    try:
        if args.stop:
            asyncio.run(stop_services())
        elif args.status:
            show_status()
        else:
            asyncio.run(start_services(dev_mode=args.dev, local_mode=args.local))
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as exc:
        logger.error(f"Fatal error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
