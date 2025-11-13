"""Health Check System

Provides comprehensive health checks for all system components.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
import asyncio

logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive system health checker"""

    def __init__(self):
        self.last_check = None
        self.last_result = None
        self.check_interval = 60  # seconds

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from supabase_client import get_supabase

            start = datetime.now(timezone.utc)

            # Try a simple query
            client = get_supabase()
            _ = client.table('organizations').select('id').limit(1).execute()  # Test query connectivity

            end = datetime.now(timezone.utc)
            latency = (end - start).total_seconds() * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "responsive": True
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "responsive": False
            }

    async def check_authentication(self) -> Dict[str, Any]:
        """Check authentication service"""
        try:
            # Verify auth infrastructure is accessible
            from infrastructure.adapters import get_auth_adapter

            # Just verify the module loads and adapter exists
            get_auth_adapter()  # Verify it can be imported and instantiated

            return {
                "status": "healthy",
                "service": "operational"
            }
        except Exception as e:
            logger.error(f"Authentication health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_cache(self) -> Dict[str, Any]:
        """Check cache status"""
        try:
            from infrastructure.supabase_db import SupabaseDatabaseAdapter

            # Get cache stats
            adapter = SupabaseDatabaseAdapter()
            cache_size = len(adapter._query_cache) if hasattr(adapter, '_query_cache') else 0

            return {
                "status": "healthy",
                "size": cache_size,
                "max_size": 1000
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "degraded",
                "error": str(e)
            }

    async def check_performance(self) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            from infrastructure.monitoring import get_performance_monitor

            monitor = get_performance_monitor()
            stats = monitor.get_stats()

            # Calculate health based on stats
            total_queries = stats.get('total_queries', 0)
            slow_queries = sum(
                s.get('slow_queries', 0)
                for s in stats.get('query_breakdown', {}).values()
            )

            slow_query_percentage = (slow_queries / total_queries * 100) if total_queries > 0 else 0

            return {
                "status": "healthy" if slow_query_percentage < 10 else "degraded",
                "total_queries": total_queries,
                "slow_queries": slow_queries,
                "slow_query_percentage": round(slow_query_percentage, 2)
            }
        except Exception as e:
            logger.error(f"Performance health check failed: {e}")
            return {
                "status": "unknown",
                "error": str(e)
            }

    async def check_errors(self) -> Dict[str, Any]:
        """Get error statistics"""
        try:
            from infrastructure.monitoring import get_error_tracker

            tracker = get_error_tracker()
            summary = tracker.get_error_summary()

            total_errors = summary.get('total_errors', 0)

            return {
                "status": "healthy" if total_errors < 100 else "degraded",
                "total_errors": total_errors,
                "unique_errors": summary.get('unique_errors', 0)
            }
        except Exception as e:
            logger.error(f"Error health check failed: {e}")
            return {
                "status": "unknown",
                "error": str(e)
            }

    async def check_rate_limiter(self) -> Dict[str, Any]:
        """Check rate limiter status"""
        try:
            from infrastructure.security import get_rate_limiter

            limiter = get_rate_limiter()

            # Count active tracked users
            active_users = len(limiter.user_requests)

            return {
                "status": "active",
                "tracked_users": active_users
            }
        except Exception as e:
            logger.error(f"Rate limiter health check failed: {e}")
            return {
                "status": "unknown",
                "error": str(e)
            }

    async def comprehensive_check(self) -> Dict[str, Any]:
        """Run all health checks"""
        timestamp = datetime.now(timezone.utc)

        # Run all checks in parallel
        results = await asyncio.gather(
            self.check_database(),
            self.check_authentication(),
            self.check_cache(),
            self.check_performance(),
            self.check_errors(),
            self.check_rate_limiter(),
            return_exceptions=True
        )

        # Unpack results
        db_check, auth_check, cache_check, perf_check, error_check, rate_check = results

        # Determine overall status
        components = {
            "database": db_check if not isinstance(db_check, Exception) else {"status": "error", "error": str(db_check)},
            "authentication": auth_check if not isinstance(auth_check, Exception) else {"status": "error", "error": str(auth_check)},
            "cache": cache_check if not isinstance(cache_check, Exception) else {"status": "error", "error": str(cache_check)},
            "performance": perf_check if not isinstance(perf_check, Exception) else {"status": "error", "error": str(perf_check)},
            "errors": error_check if not isinstance(error_check, Exception) else {"status": "error", "error": str(error_check)},
            "rate_limiter": rate_check if not isinstance(rate_check, Exception) else {"status": "error", "error": str(rate_check)}
        }

        # Calculate overall status
        statuses = [c.get('status', 'unknown') for c in components.values()]
        if any(s == 'unhealthy' or s == 'error' for s in statuses):
            overall_status = 'unhealthy'
        elif any(s == 'degraded' for s in statuses):
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'

        result = {
            "status": overall_status,
            "timestamp": timestamp.isoformat(),
            "components": components,
            "uptime_seconds": self._calculate_uptime()
        }

        self.last_check = timestamp
        self.last_result = result

        return result

    def _calculate_uptime(self) -> float:
        """Calculate system uptime (simplified)"""
        # In production, this would track actual server start time
        if self.last_check:
            return (datetime.utcnow() - self.last_check).total_seconds()
        return 0.0

    def get_last_check(self) -> Optional[Dict[str, Any]]:
        """Get last health check result"""
        return self.last_result


# Global instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
        logger.info("Health checker initialized")
    return _health_checker
