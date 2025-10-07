"""
Health Checks for Atoms MCP Test Framework

Validates backend connectivity before running tests to enable graceful skipping
when infrastructure is unavailable.
"""

import asyncio
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)


class HealthChecker:
    """Check health of various backends before running tests."""

    @staticmethod
    async def check_supabase() -> Dict[str, any]:
        """Check Supabase connection availability."""
        try:
            from supabase import create_client

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or not key:
                return {"available": False, "service": "Supabase", "error": "Missing credentials"}

            client = create_client(url, key)

            # Try a simple query
            response = await asyncio.wait_for(
                asyncio.to_thread(lambda: client.table("organizations").select("id").limit(1).execute()),
                timeout=3.0
            )

            return {"available": True, "service": "Supabase", "url": url[:30] + "..."}

        except asyncio.TimeoutError:
            logger.warning("Supabase health check timed out (3s)")
            return {"available": False, "service": "Supabase", "error": "Timeout"}
        except Exception as e:
            logger.warning(f"Supabase health check failed: {e}")
            return {"available": False, "service": "Supabase", "error": str(e)[:50]}

    @staticmethod
    async def check_mcp_server(endpoint: str) -> Dict[str, any]:
        """Check MCP server availability."""
        try:
            import httpx

            # Simple GET to check if server is up
            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.get(endpoint.replace("/api/mcp", "/")),
                    timeout=3.0
                )

                return {
                    "available": response.status_code < 500,
                    "service": "MCP Server",
                    "status_code": response.status_code,
                    "endpoint": endpoint[:40] + "..."
                }

        except asyncio.TimeoutError:
            return {"available": False, "service": "MCP Server", "error": "Timeout"}
        except Exception as e:
            logger.warning(f"MCP server health check failed: {e}")
            return {"available": False, "service": "MCP Server", "error": str(e)[:50]}

    @staticmethod
    async def check_oauth_provider() -> Dict[str, any]:
        """Check OAuth provider (AuthKit) availability."""
        try:
            import httpx

            authkit_url = "https://api.workos.com/status"

            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.get(authkit_url),
                    timeout=3.0
                )

                return {
                    "available": response.status_code == 200,
                    "service": "AuthKit OAuth",
                    "status": "operational" if response.status_code == 200 else "degraded"
                }

        except Exception as e:
            logger.warning(f"OAuth provider health check failed: {e}")
            return {"available": False, "service": "AuthKit OAuth", "error": str(e)[:50]}

    @staticmethod
    async def check_all(mcp_endpoint: str = None) -> Dict[str, Dict]:
        """Run all health checks and return results."""
        results = {}

        # Supabase (async)
        supabase_result = await HealthChecker.check_supabase()
        results["supabase"] = supabase_result

        # MCP Server (async)
        if mcp_endpoint:
            mcp_result = await HealthChecker.check_mcp_server(mcp_endpoint)
            results["mcp_server"] = mcp_result

        # OAuth provider (async)
        oauth_result = await HealthChecker.check_oauth_provider()
        results["oauth"] = oauth_result

        return results

    @staticmethod
    def print_health_status(results: Dict[str, Dict]):
        """Print health check results in a nice format."""
        print("\n🏥 Backend Health Check:")
        print("=" * 60)

        for service, result in results.items():
            status = "✅" if result.get("available") else "❌"
            service_name = result.get("service", service)
            print(f"{status} {service_name:20s}", end="")

            if not result.get("available"):
                error = result.get("error", "Unknown error")
                print(f" - {error}")
            else:
                note = result.get("note", result.get("status", ""))
                if note:
                    print(f" - {note}")
                else:
                    print(" - OK")

        print("=" * 60)

        # Count available services
        available = sum(1 for r in results.values() if r.get("available"))
        total = len(results)
        print(f"Available: {available}/{total} services\n")

        if available < total:
            print("⚠️  Some backends unavailable - related tests may be skipped\n")
