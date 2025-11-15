"""Test environment manager for auto-targeting different deployment targets.

Handles environment setup for:
- local: Local development (localhost:8000, local Supabase)
- dev: Development deployment (mcpdev.atoms.tech)
- prod: Production deployment (mcp.atoms.tech)
"""

import os
from pathlib import Path
from typing import Dict, Any
from enum import Enum


class TestEnvironment(Enum):
    """Supported test environments."""
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class TestEnvManager:
    """Manages test environment configuration and setup."""
    
    # Environment configurations
    CONFIGS = {
        TestEnvironment.LOCAL: {
            "name": "Local Development",
            "mcp_base_url": "http://127.0.0.1:8000/api/mcp",
            "health_url": "http://127.0.0.1:8000/health",
            "supabase_url": os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            "supabase_key": os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"),
            "timeout": 10,
            "retry_attempts": 3,
            "env_file": ".env",
            "description": "Local development with local Supabase"
        },
        TestEnvironment.DEV: {
            "name": "Development (mcpdev.atoms.tech)",
            "mcp_base_url": "https://mcpdev.atoms.tech/api/mcp",
            "health_url": "https://mcpdev.atoms.tech/health",
            "supabase_url": os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            "supabase_key": os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"),
            "timeout": 30,
            "retry_attempts": 5,
            "env_file": ".env.e2e",
            "description": "Development deployment (mcpdev.atoms.tech)"
        },
        TestEnvironment.PROD: {
            "name": "Production (mcp.atoms.tech)",
            "mcp_base_url": "https://mcp.atoms.tech/api/mcp",
            "health_url": "https://mcp.atoms.tech/health",
            "supabase_url": os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            "supabase_key": os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"),
            "timeout": 60,
            "retry_attempts": 5,
            "env_file": None,
            "description": "Production deployment (mcp.atoms.tech)"
        }
    }
    
    @classmethod
    def get_environment_for_scope(cls, scope: str) -> TestEnvironment:
        """Determine which environment to use based on test scope.
        
        Args:
            scope: Test scope - 'unit', 'integration', 'e2e'
            
        Returns:
            TestEnvironment to use
        """
        # Unit tests always use local (they don't need deployment)
        if scope == "unit":
            return TestEnvironment.LOCAL
        
        # Check if explicitly set via environment variable
        explicit_env = os.getenv("TEST_ENV")
        if explicit_env:
            try:
                return TestEnvironment(explicit_env.lower())
            except ValueError:
                pass
        
        # Default to dev for integration/e2e
        # (can be overridden via TEST_ENV env var)
        if scope in ["integration", "e2e"]:
            # Auto-target dev unless explicitly set to local or prod
            return TestEnvironment.DEV
        
        return TestEnvironment.LOCAL
    
    @classmethod
    def get_config(cls, environment: TestEnvironment) -> Dict[str, Any]:
        """Get configuration for an environment.
        
        Args:
            environment: TestEnvironment to get config for
            
        Returns:
            Configuration dictionary
        """
        return cls.CONFIGS[environment].copy()
    
    @classmethod
    def setup_environment(cls, environment: TestEnvironment) -> None:
        """Set up environment variables for testing.
        
        Args:
            environment: TestEnvironment to set up
        """
        config = cls.get_config(environment)
        
        # Set MCP-specific variables
        os.environ["MCP_BASE_URL"] = config["mcp_base_url"]
        os.environ["MCP_HEALTH_URL"] = config["health_url"]
        os.environ["MCP_TIMEOUT"] = str(config["timeout"])
        os.environ["MCP_RETRY_ATTEMPTS"] = str(config["retry_attempts"])
        
        # Set Supabase variables (only if they have values)
        if config["supabase_url"]:
            os.environ["NEXT_PUBLIC_SUPABASE_URL"] = config["supabase_url"]
        if config["supabase_key"]:
            os.environ["NEXT_PUBLIC_SUPABASE_ANON_KEY"] = config["supabase_key"]
        
        # Set environment-specific URLs for fixtures
        if environment == TestEnvironment.LOCAL:
            os.environ["MCP_INTEGRATION_BASE_URL"] = "http://127.0.0.1:8000/api/mcp"
            os.environ["MCP_E2E_BASE_URL"] = "http://127.0.0.1:8000/api/mcp"
        elif environment == TestEnvironment.DEV:
            os.environ["MCP_INTEGRATION_BASE_URL"] = "https://mcpdev.atoms.tech/api/mcp"
            os.environ["MCP_E2E_BASE_URL"] = "https://mcpdev.atoms.tech/api/mcp"
        elif environment == TestEnvironment.PROD:
            os.environ["MCP_INTEGRATION_BASE_URL"] = "https://mcp.atoms.tech/api/mcp"
            os.environ["MCP_E2E_BASE_URL"] = "https://mcp.atoms.tech/api/mcp"
    
    @classmethod
    def print_environment_info(cls, environment: TestEnvironment) -> None:
        """Print environment information.
        
        Args:
            environment: TestEnvironment to print info for
        """
        config = cls.get_config(environment)
        print(f"🎯 Test Environment: {config['name']}")
        print(f"📝 Description: {config['description']}")
        print(f"🔗 MCP URL: {config['mcp_base_url']}")
        print(f"⏱️  Timeout: {config['timeout']}s")
        print(f"🔄 Retries: {config['retry_attempts']}")
    
    @classmethod
    def verify_environment(cls, environment: TestEnvironment) -> bool:
        """Verify that an environment is reachable.
        
        Args:
            environment: TestEnvironment to verify
            
        Returns:
            True if environment is reachable, False otherwise
        """
        import httpx
        
        config = cls.get_config(environment)
        health_url = config["health_url"]
        
        try:
            with httpx.Client(timeout=config["timeout"]) as client:
                response = client.get(health_url)
                return response.status_code == 200
        except Exception as e:
            print(f"⚠️  Could not reach {environment.value}: {e}")
            return False
