"""
Server Management Module

Reusable server startup and configuration management.
Can be moved to pheno-sdk/server-kit or similar.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any


class ServerConfig:
    """Server configuration management."""
    
    def __init__(
        self,
        port: int,
        host: str = "127.0.0.1",
        domain: Optional[str] = None,
        tunnel_enabled: bool = True,
        tunnel_url: Optional[str] = None
    ):
        self.port = port
        self.host = host
        self.domain = domain
        self.tunnel_enabled = tunnel_enabled
        self.tunnel_url = tunnel_url
        self.started_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "port": self.port,
            "host": self.host,
            "base_url": self.tunnel_url or f"http://{self.host}:{self.port}",
            "api_endpoint": f"{self.tunnel_url or f'http://{self.host}:{self.port}'}/api/mcp",
            "tunnel_enabled": self.tunnel_enabled,
            "tunnel_url": self.tunnel_url,
            "domain": self.domain,
            "started_at": self.started_at,
        }
    
    def save(self, config_file: Path):
        """Save configuration to file."""
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, config_file: Path) -> Optional["ServerConfig"]:
        """Load configuration from file."""
        if not config_file.exists():
            return None
        
        with open(config_file) as f:
            data = json.load(f)
        
        return cls(
            port=data["port"],
            host=data.get("host", "127.0.0.1"),
            domain=data.get("domain"),
            tunnel_enabled=data.get("tunnel_enabled", True),
            tunnel_url=data.get("tunnel_url")
        )


class EnvironmentManager:
    """Environment variable management for server."""
    
    @staticmethod
    def load_env_file(env_file: Path, logger=None) -> bool:
        """Load environment variables from .env file."""
        if not env_file.exists():
            return False
        
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            if logger:
                logger.info(f"Loaded environment variables from {env_file}")
            return True
        except ImportError:
            if logger:
                logger.warning("python-dotenv not installed, skipping .env loading")
            return False
    
    @staticmethod
    def setup_server_env(
        port: int,
        host: str = "127.0.0.1",
        tunnel_url: Optional[str] = None
    ):
        """Setup environment variables for server."""
        # Port configuration
        os.environ["PORT"] = str(port)
        os.environ["ATOMS_FASTMCP_PORT"] = str(port)
        os.environ["ATOMS_LOCAL_PORT"] = str(port)
        
        # Host configuration
        os.environ["ATOMS_FASTMCP_HOST"] = host
        
        # Transport configuration
        os.environ["ATOMS_FASTMCP_TRANSPORT"] = "http"
        os.environ["ATOMS_USE_LOCAL_SERVER"] = "true"
        
        # Auth base URL
        base_url = tunnel_url or f"http://{host}:{port}"
        os.environ["FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL"] = base_url
    
    @staticmethod
    def enable_tunnel():
        """Enable CloudFlare tunnel."""
        os.environ["AUTO_TUNNEL"] = "true"
    
    @staticmethod
    def disable_tunnel():
        """Disable CloudFlare tunnel."""
        os.environ.pop("AUTO_TUNNEL", None)


class ServerManager:
    """High-level server management."""
    
    def __init__(
        self,
        project_name: str,
        domain: str,
        port: int = 50002,
        enable_tunnel: bool = True,
        logger=None
    ):
        self.project_name = project_name
        self.domain = domain
        self.port = port
        self.enable_tunnel = enable_tunnel
        self.logger = logger
        self.config: Optional[ServerConfig] = None
        self.infra = None
    
    def log_info(self, msg: str):
        """Log info message."""
        if self.logger:
            self.logger.info(msg)
        else:
            print(f"INFO: {msg}")
    
    def log_error(self, msg: str):
        """Log error message."""
        if self.logger:
            self.logger.error(msg)
        else:
            print(f"ERROR: {msg}")
    
    def log_warning(self, msg: str):
        """Log warning message."""
        if self.logger:
            self.logger.warning(msg)
        else:
            print(f"WARNING: {msg}")
    
    def initialize_infra(self):
        """Initialize infrastructure manager."""
        try:
            from kinfra import get_smart_infra_manager
            self.log_info(f"Initializing SmartInfraManager for {self.project_name}...")
            self.infra = get_smart_infra_manager(
                project_name=self.project_name,
                domain=self.domain
            )
            return True
        except ImportError as e:
            self.log_error(f"Failed to import kinfra: {e}")
            return False
    
    def start_tunnel(self) -> Optional[str]:
        """Start CloudFlare tunnel."""
        if not self.enable_tunnel:
            return None
        
        if not self.infra:
            self.log_error("Infrastructure manager not initialized")
            return None
        
        self.log_info(f"Starting CloudFlare tunnel to {self.domain}...")
        print("\nStarting CloudFlare tunnel...")
        print("This provides HTTPS access required for OAuth")
        
        tunnel_url = self.infra.start_cloudflare_tunnel(self.port, force_restart=False)
        
        if tunnel_url:
            print(f"\nTunnel URL: {tunnel_url}")
            print(f"MCP Endpoint: {tunnel_url}/api/mcp")
            return tunnel_url
        else:
            self.log_error("Failed to start CloudFlare tunnel")
            print("\nFailed to start tunnel. Server will only be accessible via localhost.")
            return None
    
    def stop_tunnel(self):
        """Stop CloudFlare tunnel."""
        if self.infra and self.enable_tunnel:
            self.log_info("Stopping CloudFlare tunnel...")
            self.infra.kill_tunnel_for_port(self.port)
    
    def setup_environment(self, env_file: Optional[Path] = None):
        """Setup environment for server."""
        # Load .env file if provided
        if env_file:
            EnvironmentManager.load_env_file(env_file, self.logger)
        
        # Setup server environment
        EnvironmentManager.setup_server_env(
            port=self.port,
            host="127.0.0.1",
            tunnel_url=self.config.tunnel_url if self.config else None
        )
        
        # Enable/disable tunnel
        if self.enable_tunnel:
            EnvironmentManager.enable_tunnel()
        else:
            EnvironmentManager.disable_tunnel()
    
    def save_config(self, config_dir: Optional[Path] = None):
        """Save server configuration."""
        if config_dir is None:
            config_dir = Path.home() / f".{self.project_name}_test_cache"
        
        config_file = config_dir / "local_server_config.json"
        
        if self.config:
            self.config.save(config_file)
            self.log_info(f"Server configuration saved to {config_file}")
    
    def display_info(self):
        """Display server information."""
        if not self.config:
            return
        
        print("\n" + "-"*70)
        print("  Server Configuration")
        print("-"*70)
        print(f"  Local URL:     http://localhost:{self.port}")
        print(f"  MCP Endpoint:  http://localhost:{self.port}/api/mcp")
        
        if self.config.tunnel_url:
            print(f"  Public URL:    {self.config.tunnel_url}")
            print(f"  Public MCP:    {self.config.tunnel_url}/api/mcp")
        
        print(f"  Domain:        {self.domain}")
        print("-"*70 + "\n")
    
    def verify_server_imports(self, server_module: str = "server") -> bool:
        """Verify server can be imported."""
        try:
            self.log_info("Verifying server imports...")
            __import__(server_module)
            self.log_info("Server imports verified successfully")
            return True
        except ImportError as e:
            self.log_error(f"Server import error: {e}")
            print(f"\nError: Failed to import {server_module}: {e}")
            return False
    
    def start(self, env_file: Optional[Path] = None) -> int:
        """Start server with full setup."""
        print("\n" + "="*70)
        print(f"  {self.project_name.upper()} Local Server Startup")
        print("  (CloudFlare tunnel required for OAuth)")
        print("="*70 + "\n")
        
        # Initialize infrastructure
        if not self.initialize_infra():
            return 1
        
        print(f"\nPort: {self.port}")
        
        # Setup environment
        self.setup_environment(env_file)
        
        # Create initial config
        self.config = ServerConfig(
            port=self.port,
            host="127.0.0.1",
            domain=self.domain,
            tunnel_enabled=self.enable_tunnel
        )
        
        # Start tunnel if enabled
        if self.enable_tunnel:
            tunnel_url = self.start_tunnel()
            if tunnel_url:
                self.config.tunnel_url = tunnel_url
                # Update environment with tunnel URL
                EnvironmentManager.setup_server_env(
                    port=self.port,
                    tunnel_url=tunnel_url
                )
        
        # Save configuration
        self.save_config()
        
        # Display server info
        self.display_info()
        
        # Verify server can be imported
        if not self.verify_server_imports():
            return 1
        
        return 0

