"""Health Checks for Test Framework

Validates backend connectivity before running tests to enable graceful skipping
when infrastructure is unavailable.

Now uses the registry-based system from mcp-QA.
"""

import sys
from pathlib import Path

# Import from shared mcp-QA library
_repo_root = Path(__file__).resolve().parents[3]
_mcp_qa_path = _repo_root / "pheno-sdk" / "mcp-QA"
if _mcp_qa_path.exists():
    sys.path.insert(0, str(_mcp_qa_path))

try:
    from mcp_qa.core.health_registry import HealthCheckRegistry
    HAS_REGISTRY = True
except ImportError:
    HAS_REGISTRY = False


class HealthChecker:
    """
    Health checker for Atoms MCP test framework.
    
    Uses registry-based system to only check services that are configured.
    No hardcoded NATS or other checks that don't apply to this project.
    """

    @staticmethod
    async def check_all() -> dict:
        """
        Run all configured health checks.
        
        Only registers checks for services that are actually used/configured.
        Atoms MCP uses Supabase, so no NATS/Redis/pgvector checks needed.
        """
        if not HAS_REGISTRY:
            # Silently skip if registry not available
            return {}
        
        registry = HealthCheckRegistry()
        
        # Atoms MCP uses Supabase which is checked via HTTP API calls
        # No explicit backend health checks needed since MCP server does that
        
        # If you want to add project-specific checks, register them here:
        # registry.register("supabase_api", check_supabase_func, critical=False)
        
        return await registry.run_all()
    
    @staticmethod
    def print_health_status(results: dict):
        """Print health check results."""
        if not results:
            # Silently skip - no checks configured
            return
        
        if HAS_REGISTRY:
            registry = HealthCheckRegistry()
            registry.print_results(results)
