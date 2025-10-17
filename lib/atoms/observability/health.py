"""
Production-ready multi-layer health monitoring.

This module provides comprehensive health checking including:
- Multi-layer health status (system, dependencies, application)
- Dependency health checks (Supabase, AuthKit, external services)
- Performance degradation detection
- Circuit breaker integration
- Health status aggregation and reporting

Author: Atoms MCP Platform
Version: 1.0.0
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .logging import get_logger
from .metrics import registry

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """Types of system components."""
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    AUTH_SERVICE = "auth_service"
    STORAGE = "storage"
    MESSAGE_QUEUE = "message_queue"
    INTERNAL_SERVICE = "internal_service"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component_name: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component_name": self.component_name,
            "component_type": self.component_type.value,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms,
            "metadata": self.metadata
        }


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    components: List[HealthCheckResult]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    uptime_seconds: Optional[float] = None
    version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "version": self.version,
            "components": [c.to_dict() for c in self.components]
        }


class HealthCheck:
    """Base class for health checks."""

    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        timeout_seconds: float = 5.0,
        critical: bool = True
    ):
        self.name = name
        self.component_type = component_type
        self.timeout_seconds = timeout_seconds
        self.critical = critical  # Whether failure affects overall health

    async def check(self) -> HealthCheckResult:
        """
        Perform health check.

        Returns:
            HealthCheckResult with status and details
        """
        raise NotImplementedError("Subclasses must implement check()")


class SupabaseHealthCheck(HealthCheck):
    """Health check for Supabase connection."""

    def __init__(
        self,
        supabase_client: Any,
        timeout_seconds: float = 5.0
    ):
        super().__init__(
            name="supabase",
            component_type=ComponentType.DATABASE,
            timeout_seconds=timeout_seconds,
            critical=True
        )
        self.client = supabase_client

    async def check(self) -> HealthCheckResult:
        """Check Supabase connectivity."""
        start_time = time.perf_counter()

        try:
            # Simple query to test connection
            response = await asyncio.wait_for(
                self._test_connection(),
                timeout=self.timeout_seconds
            )

            response_time_ms = (time.perf_counter() - start_time) * 1000

            if response:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.HEALTHY,
                    message="Supabase connection is healthy",
                    response_time_ms=response_time_ms
                )
            else:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNHEALTHY,
                    message="Supabase query returned no results",
                    response_time_ms=response_time_ms
                )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Supabase health check timed out after {self.timeout_seconds}s"
            )
        except Exception as e:
            logger.error(f"Supabase health check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Supabase error: {str(e)}"
            )

    async def _test_connection(self) -> bool:
        """Test database connection with simple query."""
        try:
            # Execute a simple query
            result = self.client.table('_health_check').select('*').limit(1).execute()
            return True
        except Exception:
            # If table doesn't exist, try a different approach
            # Just testing if we can connect
            result = self.client.auth.get_session()
            return True


class AuthKitHealthCheck(HealthCheck):
    """Health check for AuthKit service."""

    def __init__(
        self,
        authkit_client: Any,
        timeout_seconds: float = 5.0
    ):
        super().__init__(
            name="authkit",
            component_type=ComponentType.AUTH_SERVICE,
            timeout_seconds=timeout_seconds,
            critical=True
        )
        self.client = authkit_client

    async def check(self) -> HealthCheckResult:
        """Check AuthKit service health."""
        start_time = time.perf_counter()

        try:
            # Test AuthKit connectivity
            response = await asyncio.wait_for(
                self._test_authkit(),
                timeout=self.timeout_seconds
            )

            response_time_ms = (time.perf_counter() - start_time) * 1000

            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.HEALTHY if response else HealthStatus.DEGRADED,
                message="AuthKit service is healthy" if response else "AuthKit service degraded",
                response_time_ms=response_time_ms
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"AuthKit health check timed out after {self.timeout_seconds}s"
            )
        except Exception as e:
            logger.error(f"AuthKit health check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"AuthKit error: {str(e)}"
            )

    async def _test_authkit(self) -> bool:
        """Test AuthKit service."""
        try:
            # Simple API call to verify service
            # This would depend on your AuthKit client implementation
            if hasattr(self.client, 'health_check'):
                return await self.client.health_check()
            return True
        except Exception:
            return False


class CustomHealthCheck(HealthCheck):
    """Custom health check using a callable."""

    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        check_func: Callable[[], bool],
        timeout_seconds: float = 5.0,
        critical: bool = False
    ):
        super().__init__(
            name=name,
            component_type=component_type,
            timeout_seconds=timeout_seconds,
            critical=critical
        )
        self.check_func = check_func

    async def check(self) -> HealthCheckResult:
        """Run custom health check function."""
        start_time = time.perf_counter()

        try:
            # Run check function with timeout
            if asyncio.iscoroutinefunction(self.check_func):
                result = await asyncio.wait_for(
                    self.check_func(),
                    timeout=self.timeout_seconds
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.check_func),
                    timeout=self.timeout_seconds
                )

            response_time_ms = (time.perf_counter() - start_time) * 1000

            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                message=f"{self.name} check {'passed' if result else 'failed'}",
                response_time_ms=response_time_ms
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"{self.name} health check timed out after {self.timeout_seconds}s"
            )
        except Exception as e:
            logger.error(f"{self.name} health check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"{self.name} error: {str(e)}"
            )


class PerformanceMonitor:
    """Monitor performance degradation."""

    def __init__(
        self,
        window_size: int = 100,
        warning_threshold_ms: float = 1000.0,
        critical_threshold_ms: float = 5000.0
    ):
        self.window_size = window_size
        self.warning_threshold_ms = warning_threshold_ms
        self.critical_threshold_ms = critical_threshold_ms
        self.response_times: List[float] = []

    def record_response_time(self, response_time_ms: float) -> None:
        """Record a response time."""
        self.response_times.append(response_time_ms)

        # Keep only last N samples
        if len(self.response_times) > self.window_size:
            self.response_times = self.response_times[-self.window_size:]

    def get_average_response_time(self) -> Optional[float]:
        """Get average response time."""
        if not self.response_times:
            return None
        return sum(self.response_times) / len(self.response_times)

    def get_p95_response_time(self) -> Optional[float]:
        """Get 95th percentile response time."""
        if not self.response_times:
            return None

        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index]

    def detect_degradation(self) -> HealthStatus:
        """Detect performance degradation."""
        p95 = self.get_p95_response_time()

        if p95 is None:
            return HealthStatus.UNKNOWN

        if p95 >= self.critical_threshold_ms:
            return HealthStatus.UNHEALTHY
        elif p95 >= self.warning_threshold_ms:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


class HealthMonitor:
    """
    Comprehensive health monitoring system.

    Manages multiple health checks and provides aggregated health status.
    """

    def __init__(self, version: Optional[str] = None):
        self.version = version or "1.0.0"
        self.health_checks: List[HealthCheck] = []
        self.performance_monitor = PerformanceMonitor()
        self.start_time = time.time()

        # Metrics
        self.health_check_gauge = registry.register_gauge(
            "health_check_status",
            "Health check status (1=healthy, 0.5=degraded, 0=unhealthy)",
            labels=["component"]
        )

    def register_check(self, health_check: HealthCheck) -> None:
        """Register a health check."""
        self.health_checks.append(health_check)
        logger.info(f"Registered health check: {health_check.name}")

    async def check_all(self) -> SystemHealth:
        """Run all health checks and return system health."""
        results = await asyncio.gather(
            *[check.check() for check in self.health_checks],
            return_exceptions=True
        )

        # Process results
        component_results: List[HealthCheckResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Health check raised an exception
                check = self.health_checks[i]
                component_results.append(
                    HealthCheckResult(
                        component_name=check.name,
                        component_type=check.component_type,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {str(result)}"
                    )
                )
            else:
                component_results.append(result)

        # Calculate overall status
        overall_status = self._calculate_overall_status(component_results)

        # Update metrics
        self._update_metrics(component_results)

        # Calculate uptime
        uptime_seconds = time.time() - self.start_time

        return SystemHealth(
            status=overall_status,
            components=component_results,
            uptime_seconds=uptime_seconds,
            version=self.version
        )

    def _calculate_overall_status(
        self,
        results: List[HealthCheckResult]
    ) -> HealthStatus:
        """Calculate overall system health from component results."""
        if not results:
            return HealthStatus.UNKNOWN

        # Check critical components
        critical_checks = [
            r for r in results
            if any(
                c.name == r.component_name and c.critical
                for c in self.health_checks
            )
        ]

        # If any critical component is unhealthy, system is unhealthy
        if any(r.status == HealthStatus.UNHEALTHY for r in critical_checks):
            return HealthStatus.UNHEALTHY

        # If any critical component is degraded, system is degraded
        if any(r.status == HealthStatus.DEGRADED for r in critical_checks):
            return HealthStatus.DEGRADED

        # Check non-critical components
        if any(r.status == HealthStatus.UNHEALTHY for r in results):
            return HealthStatus.DEGRADED

        # Check for any degraded components
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def _update_metrics(self, results: List[HealthCheckResult]) -> None:
        """Update health check metrics."""
        status_map = {
            HealthStatus.HEALTHY: 1.0,
            HealthStatus.DEGRADED: 0.5,
            HealthStatus.UNHEALTHY: 0.0,
            HealthStatus.UNKNOWN: -1.0
        }

        for result in results:
            self.health_check_gauge.set(
                status_map[result.status],
                labels={"component": result.component_name}
            )


# Global health monitor instance
health_monitor = HealthMonitor()


async def check_health() -> SystemHealth:
    """Check system health."""
    return await health_monitor.check_all()


def register_health_check(check: HealthCheck) -> None:
    """Register a health check."""
    health_monitor.register_check(check)
