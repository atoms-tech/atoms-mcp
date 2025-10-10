"""
Health checking and monitoring for system components.

Provides:
- Component health checks
- System-wide health monitoring
- Service dependency checks
- Performance threshold monitoring
- Automated health reporting

Ported from zen-mcp-server to be provider-agnostic.
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    # Basic info
    component: str
    status: HealthStatus
    timestamp: datetime = field(default_factory=datetime.now)

    # Performance metrics
    response_time_ms: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0

    # Details
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    # Dependencies
    dependencies: Dict[str, HealthStatus] = field(default_factory=dict)


@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""

    # Overall status
    overall_status: HealthStatus
    timestamp: datetime = field(default_factory=datetime.now)

    # Component health
    components: Dict[str, HealthCheckResult] = field(default_factory=dict)

    # Performance summary
    avg_response_time_ms: float = 0.0
    system_success_rate: float = 1.0
    total_errors: int = 0

    # Resource utilization
    memory_usage_mb: float = 0.0
    memory_health: str = "unknown"

    # Recommendations
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class HealthMonitor:
    """
    Health monitor for system components.
    
    Example:
        monitor = HealthMonitor()
        
        # Register a health check
        @monitor.register_check("database")
        async def check_database():
            # Check database connection
            return HealthCheckResult(
                component="database",
                status=HealthStatus.HEALTHY,
                message="Database is responsive"
            )
        
        # Run all checks
        report = await monitor.check_all()
        print(f"System status: {report.overall_status}")
    """

    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._lock = threading.RLock()
        self._last_check_time: Optional[datetime] = None
        self._cached_report: Optional[SystemHealthReport] = None
        self._cache_ttl_seconds = 30.0

    def register_check(self, component_name: str):
        """
        Decorator to register a health check function.
        
        Args:
            component_name: Name of the component to check
        
        Example:
            @monitor.register_check("api")
            async def check_api():
                return HealthCheckResult(...)
        """
        def decorator(func: Callable):
            self.health_checks[component_name] = func
            logger.info(f"Registered health check for: {component_name}")
            return func
        return decorator

    def add_check(self, component_name: str, check_func: Callable):
        """
        Programmatically add a health check.
        
        Args:
            component_name: Name of the component
            check_func: Async function that returns HealthCheckResult
        """
        self.health_checks[component_name] = check_func
        logger.info(f"Added health check for: {component_name}")

    async def check_component(
        self,
        component_name: str,
        timeout_seconds: float = 30.0
    ) -> HealthCheckResult:
        """
        Check health of a specific component.
        
        Args:
            component_name: Name of the component to check
            timeout_seconds: Timeout for the health check
        
        Returns:
            Health check result
        """
        if component_name not in self.health_checks:
            return HealthCheckResult(
                component=component_name,
                status=HealthStatus.UNKNOWN,
                message=f"No health check registered for {component_name}"
            )

        start_time = time.time()
        
        try:
            check_func = self.health_checks[component_name]
            
            # Run with timeout
            result = await asyncio.wait_for(
                check_func(),
                timeout=timeout_seconds
            )
            
            # Record response time
            result.response_time_ms = (time.time() - start_time) * 1000
            
            # Store in history
            with self._lock:
                self.health_history[component_name].append(result)
            
            return result
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component=component_name,
                status=HealthStatus.CRITICAL,
                message=f"Health check timed out after {timeout_seconds}s",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Health check failed for {component_name}: {e}")
            return HealthCheckResult(
                component=component_name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)},
                response_time_ms=(time.time() - start_time) * 1000
            )

    async def check_all(
        self,
        use_cache: bool = True,
        timeout_seconds: float = 30.0
    ) -> SystemHealthReport:
        """
        Run all registered health checks.
        
        Args:
            use_cache: Use cached results if available and fresh
            timeout_seconds: Timeout for each individual check
        
        Returns:
            System health report
        """
        # Check cache
        if use_cache and self._cached_report and self._last_check_time:
            age = (datetime.now() - self._last_check_time).total_seconds()
            if age < self._cache_ttl_seconds:
                logger.debug(f"Using cached health report (age: {age:.1f}s)")
                return self._cached_report

        # Run all checks concurrently
        tasks = {
            name: self.check_component(name, timeout_seconds)
            for name in self.health_checks.keys()
        }
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Build component results
        components = {}
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                components[name] = HealthCheckResult(
                    component=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Check failed: {str(result)}"
                )
            else:
                components[name] = result

        # Calculate overall status
        overall_status = self._calculate_overall_status(components)
        
        # Calculate statistics
        response_times = [r.response_time_ms for r in components.values()]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        total_errors = sum(r.error_count for r in components.values())
        
        # Collect issues and recommendations
        critical_issues = []
        warnings = []
        recommendations = []
        
        for result in components.values():
            if result.status == HealthStatus.CRITICAL:
                critical_issues.append(f"{result.component}: {result.message}")
            elif result.status == HealthStatus.WARNING:
                warnings.append(f"{result.component}: {result.message}")
            
            recommendations.extend(result.recommendations)

        # Build report
        report = SystemHealthReport(
            overall_status=overall_status,
            components=components,
            avg_response_time_ms=avg_response_time,
            total_errors=total_errors,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations,
        )

        # Cache the report
        self._cached_report = report
        self._last_check_time = datetime.now()

        return report

    def _calculate_overall_status(
        self,
        components: Dict[str, HealthCheckResult]
    ) -> HealthStatus:
        """Calculate overall system status from component statuses."""
        if not components:
            return HealthStatus.UNKNOWN

        statuses = [r.status for r in components.values()]

        # If any critical, system is critical
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL

        # If any warning, system has warnings
        if HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING

        # If any unavailable, system is degraded
        if HealthStatus.UNAVAILABLE in statuses:
            return HealthStatus.WARNING

        # If all healthy, system is healthy
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    def get_component_history(
        self,
        component_name: str,
        limit: int = 100
    ) -> List[HealthCheckResult]:
        """Get health check history for a component."""
        with self._lock:
            history = list(self.health_history.get(component_name, []))
            return history[-limit:]

    def clear_cache(self):
        """Clear the cached health report."""
        self._cached_report = None
        self._last_check_time = None


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor

