"""Configuration for selecting live vs mock variants of services."""

from __future__ import annotations

import os
from typing import Dict, Any
from enum import Enum


class ServiceMode(str, Enum):
    """Service operation mode."""
    LIVE = "live"
    MOCK = "mock"
    LOCAL = "local"


class ServiceConfig:
    """Configuration for service modes and endpoints."""
    
    def __init__(self):
        # Global service mode fallback
        self.default_mode = os.getenv("ATOMS_SERVICE_MODE", ServiceMode.LIVE)
        
        # Service-specific mode overrides
        self.service_modes = {
            "mcp_client": os.getenv("ATOMS_MCP_CLIENT_MODE", self.default_mode),
            "supabase": os.getenv("ATOMS_SUPABASE_MODE", self.default_mode),
            "authkit": os.getenv("ATOMS_AUTHKIT_MODE", self.default_mode),
        }
        
        # MCP Client configuration
        self.mcp_client = {
            "live_endpoint": os.getenv("ATOMS_MCP_LIVE_ENDPOINT", "https://mcp.atoms.tech"),
            "dev_endpoint": os.getenv("ATOMS_MCP_DEV_ENDPOINT", "https://mcpdev.atoms.tech"),
            "local_port": int(os.getenv("ATOMS_MCP_LOCAL_PORT", "8001")),
        }
        
        # Supabase configuration
        self.supabase = {
            "live_url": os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            "live_key": os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"),
            "mock_data_file": os.getenv("ATOMS_SUPABASE_MOCK_DATA", "tests/fixtures/supabase_mock_data.json"),
        }
        
        # AuthKit configuration
        self.authkit = {
            "live_domain": os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN"),
            "live_key": os.getenv("WORKOS_API_KEY"),
            "live_client_id": os.getenv("WORKOS_CLIENT_ID"),
            "mock_user_id": os.getenv("ATOMS_AUTHKIT_MOCK_USER_ID", "mock-user-123"),
            "mock_email": os.getenv("ATOMS_AUTHKIT_MOCK_EMAIL", "mock@example.com"),
        }
    
    def get_service_mode(self, service_name: str) -> ServiceMode:
        """Get the mode for a specific service."""
        mode = self.service_modes.get(service_name, self.default_mode)
        return ServiceMode(mode)
    
    def is_service_mock(self, service_name: str) -> bool:
        """Check if a service should use mock implementation."""
        return self.get_service_mode(service_name) == ServiceMode.MOCK
    
    def is_service_local(self, service_name: str) -> bool:
        """Check if a service should use local implementation."""
        return self.get_service_mode(service_name) == ServiceMode.LOCAL
    
    def is_service_live(self, service_name: str) -> bool:
        """Check if a service should use live implementation."""
        return self.get_service_mode(service_name) == ServiceMode.LIVE
    
    def get_mcp_endpoint(self) -> str:
        """Get the MCP endpoint based on configuration."""
        mode = self.get_service_mode("mcp_client")
        if mode == ServiceMode.LIVE:
            return self.mcp_client["live_endpoint"]
        elif mode == ServiceMode.LOCAL:
            # For local HTTP client
            return f"http://localhost:{self.mcp_client['local_port']}"
        else:  # MOCK
            # In-memory mock, no endpoint needed
            return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for debugging."""
        return {
            "default_mode": self.default_mode,
            "service_modes": self.service_modes,
            "mcp_client": self.mcp_client,
            "supabase": {
                "has_live_config": bool(self.supabase["live_url"] and self.supabase["live_key"]),
                "mock_data_file": self.supabase["mock_data_file"],
            },
            "authkit": {
                "has_live_config": bool(self.authkit["live_domain"] and self.authkit["live_key"]),
                "mock_user_id": self.authkit["mock_user_id"],
                "mock_email": self.authkit["mock_email"],
            }
        }


# Global configuration instance
_config = None


def get_service_config() -> ServiceConfig:
    """Get the global service configuration instance."""
    global _config
    if _config is None:
        _config = ServiceConfig()
    return _config


def reset_service_config():
    """Reset the global service configuration (useful for testing)."""
    global _config
    _config = None