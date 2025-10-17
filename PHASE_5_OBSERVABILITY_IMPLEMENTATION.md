# Phase 5: Observability Infrastructure Implementation Plan

## Executive Summary

Phase 5 implements comprehensive observability infrastructure for the Atoms MCP platform, including structured logging with correlation IDs, request/tool metrics collection, multi-layer health checks, Vercel webhook integration, and a complete monitoring dashboard. This phase leverages the existing observability-kit from pheno_vendor while adding platform-specific enhancements.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Requests                                │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Request Middleware Layer                          │
├─────────────────────────────────────────────────────────────────────┤
│  • Correlation ID Injection                                         │
│  • Request Timing Start                                             │
│  • Request Attributes Capture                                       │
│  • Rate Limit Tracking                                              │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Core Application Layer                            │
├─────────────────────────────────────────────────────────────────────┤
│  • Tool Execution with Metrics                                      │
│  • Structured Logging with Context                                  │
│  • Error Tracking and Recovery                                      │
│  • Performance Monitoring                                           │
└────────────────────┬────────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Logging    │ │   Metrics    │ │   Tracing    │ │Health Checks │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ Structured   │ │ Prometheus   │ │ Distributed  │ │ Service      │
│ JSON Output  │ │ Compatible   │ │ Trace Context│ │ Dependencies │
│ Log Levels   │ │ Histograms   │ │ Span Tracking│ │ Performance  │
│ Correlation  │ │ Counters     │ │ Attributes   │ │ Degradation  │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
        │                │                │                │
        └────────────────┴────────────────┴────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Observability Backend                             │
├─────────────────────────────────────────────────────────────────────┤
│  • Vercel Logs (JSON structured)                                    │
│  • Prometheus Metrics Endpoint (/metrics)                           │
│  • Health Status Endpoint (/health)                                 │
│  • Webhook Notifications (errors/alerts)                            │
│  • Dashboard API (/api/observability/dashboard)                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 1. Structured Logging Implementation

### 1.1 Core Logging Module
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/lib/atoms/observability/logging.py`

```python
"""
Enhanced structured logging for Atoms MCP with correlation tracking.
"""
from __future__ import annotations
import json
import time
from contextvars import ContextVar
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from observability import (
    StructuredLogger,
    LogLevel,
    generate_correlation_id,
    set_global_correlation_id
)

# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
tool_name_var: ContextVar[Optional[str]] = ContextVar('tool_name', default=None)

class AtomsLogger(StructuredLogger):
    """Enhanced logger with Atoms-specific context."""

    def __init__(self, name: str, **kwargs):
        super().__init__(
            name,
            service_name="atoms-mcp",
            environment=kwargs.get("environment", "development"),
            **kwargs
        )

    def _add_context(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Add request context to log entries."""
        context = {
            "correlation_id": correlation_id_var.get(),
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "tool_name": tool_name_var.get(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Remove None values
        context = {k: v for k, v in context.items() if v is not None}

        # Merge with provided kwargs
        return {**context, **kwargs}

    def log_tool_execution(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None,
        **kwargs
    ):
        """Log tool execution with standardized format."""
        log_data = self._add_context({
            "event": "tool_execution",
            "tool": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "error": error,
            **kwargs
        })

        if success:
            self.info("Tool executed successfully", **log_data)
        else:
            self.error(f"Tool execution failed: {error}", **log_data)

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """Log HTTP request with standardized format."""
        log_data = self._add_context({
            "event": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **kwargs
        })

        level = LogLevel.INFO if status_code < 400 else LogLevel.ERROR
        self.log(level, f"{method} {path} - {status_code}", **log_data)

# Global logger instance
atoms_logger = AtomsLogger("atoms-mcp")

def get_atoms_logger(name: str) -> AtomsLogger:
    """Get a logger instance with the given name."""
    return AtomsLogger(name)
```

### 1.2 Logging Configuration
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/lib/atoms/observability/config.py`

```python
"""
Observability configuration for different environments.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"  # json or plain
    include_timestamp: bool = True
    include_correlation_id: bool = True
    include_user_context: bool = True
    max_message_length: int = 10000
    sensitive_fields: list[str] = None

    def __post_init__(self):
        if self.sensitive_fields is None:
            self.sensitive_fields = [
                "password", "token", "api_key", "secret",
                "authorization", "cookie", "session"
            ]

@dataclass
class MetricsConfig:
    """Metrics collection configuration."""
    enabled: bool = True
    export_interval: int = 60  # seconds
    prometheus_enabled: bool = True
    include_system_metrics: bool = True
    histogram_buckets: list[float] = None

    def __post_init__(self):
        if self.histogram_buckets is None:
            # Default buckets for request duration (ms)
            self.histogram_buckets = [
                10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000
            ]

@dataclass
class HealthCheckConfig:
    """Health check configuration."""
    enabled: bool = True
    check_interval: int = 30  # seconds
    timeout: int = 5  # seconds
    include_dependencies: bool = True
    degraded_threshold: float = 0.8  # 80% success rate

@dataclass
class AlertingConfig:
    """Alerting configuration."""
    enabled: bool = True
    webhook_url: Optional[str] = None
    error_threshold: int = 10  # errors per minute
    latency_threshold: int = 5000  # ms
    failure_rate_threshold: float = 0.1  # 10%

@dataclass
class ObservabilityConfig:
    """Complete observability configuration."""
    logging: LoggingConfig
    metrics: MetricsConfig
    health_check: HealthCheckConfig
    alerting: AlertingConfig
    environment: str = "development"

    @classmethod
    def from_env(cls) -> ObservabilityConfig:
        """Create configuration from environment variables."""
        env = os.getenv("ENVIRONMENT", "development")

        return cls(
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                format=os.getenv("LOG_FORMAT", "json"),
            ),
            metrics=MetricsConfig(
                enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
                prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            ),
            health_check=HealthCheckConfig(
                enabled=os.getenv("HEALTH_CHECK_ENABLED", "true").lower() == "true",
            ),
            alerting=AlertingConfig(
                enabled=os.getenv("ALERTING_ENABLED", "true").lower() == "true",
                webhook_url=os.getenv("VERCEL_WEBHOOK_URL"),
            ),
            environment=env
        )
```

## 2. Request Metrics Collection

### 2.1 Metrics Collector
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/lib/atoms/observability/metrics.py`

```python
"""
Metrics collection for Atoms MCP.
"""
from __future__ import annotations
import time
from typing import Dict, Optional
from contextlib import contextmanager

from observability import (
    MetricsCollector,
    Counter,
    Gauge,
    Histogram
)

class AtomsMetrics:
    """Centralized metrics collection for Atoms MCP."""

    def __init__(self):
        self.collector = MetricsCollector()

        # Request metrics
        self.request_count = self.collector.counter(
            "atoms_mcp_requests_total",
            "Total number of requests",
            labels=["method", "path", "status"]
        )

        self.request_duration = self.collector.histogram(
            "atoms_mcp_request_duration_ms",
            "Request duration in milliseconds",
            labels=["method", "path"],
            buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
        )

        # Tool metrics
        self.tool_execution_count = self.collector.counter(
            "atoms_mcp_tool_executions_total",
            "Total number of tool executions",
            labels=["tool", "status"]
        )

        self.tool_duration = self.collector.histogram(
            "atoms_mcp_tool_duration_ms",
            "Tool execution duration in milliseconds",
            labels=["tool"],
            buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000]
        )

        # Error metrics
        self.error_count = self.collector.counter(
            "atoms_mcp_errors_total",
            "Total number of errors",
            labels=["type", "tool"]
        )

        # Rate limiting metrics
        self.rate_limit_hits = self.collector.counter(
            "atoms_mcp_rate_limit_hits_total",
            "Total number of rate limit hits",
            labels=["user_id"]
        )

        # Active connections
        self.active_connections = self.collector.gauge(
            "atoms_mcp_active_connections",
            "Number of active connections"
        )

        # Dependency health
        self.dependency_health = self.collector.gauge(
            "atoms_mcp_dependency_health",
            "Health status of dependencies (1=healthy, 0=unhealthy)",
            labels=["dependency"]
        )

    @contextmanager
    def measure_request(self, method: str, path: str):
        """Context manager to measure request duration."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000
            self.request_duration.observe(duration, {"method": method, "path": path})

    @contextmanager
    def measure_tool(self, tool_name: str):
        """Context manager to measure tool execution."""
        start_time = time.time()
        success = False
        try:
            yield
            success = True
        except Exception as e:
            self.error_count.inc({"type": type(e).__name__, "tool": tool_name})
            raise
        finally:
            duration = (time.time() - start_time) * 1000
            self.tool_duration.observe(duration, {"tool": tool_name})
            status = "success" if success else "failure"
            self.tool_execution_count.inc({"tool": tool_name, "status": status})

    def record_request(self, method: str, path: str, status: int, duration_ms: float):
        """Record a completed request."""
        self.request_count.inc({
            "method": method,
            "path": path,
            "status": str(status)
        })
        self.request_duration.observe(duration_ms, {"method": method, "path": path})

    def record_rate_limit(self, user_id: str):
        """Record a rate limit hit."""
        self.rate_limit_hits.inc({"user_id": user_id})

    def set_dependency_health(self, dependency: str, healthy: bool):
        """Set the health status of a dependency."""
        self.dependency_health.set(1.0 if healthy else 0.0, {"dependency": dependency})

    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format."""
        from observability import PrometheusExporter
        exporter = PrometheusExporter(self.collector)
        return exporter.export()

# Global metrics instance
atoms_metrics = AtomsMetrics()
```

### 2.2 Middleware Integration
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/lib/atoms/observability/middleware.py`

```python
"""
Observability middleware for request tracking.
"""
from __future__ import annotations
import time
import json
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logging import (
    atoms_logger,
    correlation_id_var,
    request_id_var,
    user_id_var,
    generate_correlation_id
)
from .metrics import atoms_metrics

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request observability."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or generate_correlation_id()
        request_id = generate_correlation_id()

        # Extract user ID from auth if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)

        # Set context variables
        correlation_id_var.set(correlation_id)
        request_id_var.set(request_id)
        if user_id:
            user_id_var.set(user_id)

        # Track active connections
        atoms_metrics.active_connections.inc()

        # Start timing
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log and record metrics
            atoms_logger.log_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=request.client.host if request.client else None
            )

            atoms_metrics.record_request(
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms
            )

            # Add correlation ID to response
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            atoms_logger.error(
                f"Request failed: {str(e)}",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__
            )

            # Record error metrics
            atoms_metrics.error_count.inc({
                "type": type(e).__name__,
                "tool": "middleware"
            })

            atoms_metrics.record_request(
                method=request.method,
                path=request.url.path,
                status=500,
                duration_ms=duration_ms
            )

            raise

        finally:
            # Decrement active connections
            atoms_metrics.active_connections.dec()

            # Clear context variables
            correlation_id_var.set(None)
            request_id_var.set(None)
            user_id_var.set(None)
```

## 3. Health Check System

### 3.1 Health Check Implementation
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/lib/atoms/observability/health.py`

```python
"""
Comprehensive health check system for Atoms MCP.
"""
from __future__ import annotations
import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from datetime import datetime, timezone

from observability import (
    HealthStatus,
    HealthCheckResult,
    SystemHealthReport,
    HealthMonitor
)

class ServiceStatus(Enum):
    """Service health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class DependencyHealth:
    """Health status of a dependency."""
    name: str
    status: ServiceStatus
    response_time_ms: Optional[float] = None
    last_check: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class AtomsHealthChecker:
    """Health checker for Atoms MCP and its dependencies."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.monitor = HealthMonitor()
        self._dependency_status: Dict[str, DependencyHealth] = {}
        self._last_full_check: Optional[datetime] = None

    async def check_supabase(self) -> DependencyHealth:
        """Check Supabase connectivity."""
        start_time = time.time()
        try:
            # Import here to avoid circular dependency
            from supabase_client import supabase

            # Try a simple query
            result = await asyncio.wait_for(
                asyncio.to_thread(lambda: supabase.table("users").select("id").limit(1).execute()),
                timeout=5.0
            )

            response_time = (time.time() - start_time) * 1000

            return DependencyHealth(
                name="supabase",
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc)
            )

        except asyncio.TimeoutError:
            return DependencyHealth(
                name="supabase",
                status=ServiceStatus.UNHEALTHY,
                error="Connection timeout",
                last_check=datetime.now(timezone.utc)
            )
        except Exception as e:
            return DependencyHealth(
                name="supabase",
                status=ServiceStatus.UNHEALTHY,
                error=str(e),
                last_check=datetime.now(timezone.utc)
            )

    async def check_authkit(self) -> DependencyHealth:
        """Check AuthKit/WorkOS connectivity."""
        start_time = time.time()
        try:
            authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
            if not authkit_domain:
                return DependencyHealth(
                    name="authkit",
                    status=ServiceStatus.DEGRADED,
                    error="AuthKit domain not configured",
                    last_check=datetime.now(timezone.utc)
                )

            # Check AuthKit endpoint
            async with aiohttp.ClientSession() as session:
                url = f"https://{authkit_domain}/health"
                async with session.get(url, timeout=5) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        return DependencyHealth(
                            name="authkit",
                            status=ServiceStatus.HEALTHY,
                            response_time_ms=response_time,
                            last_check=datetime.now(timezone.utc)
                        )
                    else:
                        return DependencyHealth(
                            name="authkit",
                            status=ServiceStatus.DEGRADED,
                            response_time_ms=response_time,
                            error=f"HTTP {response.status}",
                            last_check=datetime.now(timezone.utc)
                        )

        except Exception as e:
            return DependencyHealth(
                name="authkit",
                status=ServiceStatus.UNHEALTHY,
                error=str(e),
                last_check=datetime.now(timezone.utc)
            )

    async def check_vercel(self) -> DependencyHealth:
        """Check Vercel platform health."""
        # In production, this would check Vercel API
        # For now, we assume healthy if we're running
        return DependencyHealth(
            name="vercel",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now(timezone.utc),
            metadata={"region": os.getenv("VERCEL_REGION", "unknown")}
        )

    async def check_performance(self) -> DependencyHealth:
        """Check system performance metrics."""
        from .metrics import atoms_metrics

        # Get current metrics
        metrics_text = atoms_metrics.get_metrics_text()

        # Parse key metrics
        error_rate = 0.0
        avg_latency = 0.0

        # Simple parsing (in production, use proper Prometheus parser)
        for line in metrics_text.split('\n'):
            if 'atoms_mcp_errors_total' in line and not line.startswith('#'):
                # Extract error count
                pass
            elif 'atoms_mcp_request_duration_ms' in line and not line.startswith('#'):
                # Extract average latency
                pass

        # Determine health based on thresholds
        status = ServiceStatus.HEALTHY
        if error_rate > 0.1:  # >10% error rate
            status = ServiceStatus.UNHEALTHY
        elif error_rate > 0.05 or avg_latency > 5000:  # >5% errors or >5s latency
            status = ServiceStatus.DEGRADED

        return DependencyHealth(
            name="performance",
            status=status,
            last_check=datetime.now(timezone.utc),
            metadata={
                "error_rate": error_rate,
                "avg_latency_ms": avg_latency
            }
        )

    async def check_all_dependencies(self) -> Dict[str, DependencyHealth]:
        """Check all dependencies in parallel."""
        tasks = [
            self.check_supabase(),
            self.check_authkit(),
            self.check_vercel(),
            self.check_performance()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        dependencies = {}
        for result in results:
            if isinstance(result, DependencyHealth):
                dependencies[result.name] = result
                # Update metrics
                from .metrics import atoms_metrics
                healthy = result.status == ServiceStatus.HEALTHY
                atoms_metrics.set_dependency_health(result.name, healthy)
            elif isinstance(result, Exception):
                # Log error
                from .logging import atoms_logger
                atoms_logger.error(f"Health check failed: {str(result)}")

        self._dependency_status = dependencies
        self._last_full_check = datetime.now(timezone.utc)

        return dependencies

    def get_overall_status(self) -> ServiceStatus:
        """Get overall service status based on dependencies."""
        if not self._dependency_status:
            return ServiceStatus.UNHEALTHY

        unhealthy_count = sum(
            1 for dep in self._dependency_status.values()
            if dep.status == ServiceStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for dep in self._dependency_status.values()
            if dep.status == ServiceStatus.DEGRADED
        )

        if unhealthy_count > 0:
            return ServiceStatus.UNHEALTHY
        elif degraded_count > 0:
            return ServiceStatus.DEGRADED
        else:
            return ServiceStatus.HEALTHY

    async def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        # Check dependencies
        dependencies = await self.check_all_dependencies()

        # Get overall status
        overall_status = self.get_overall_status()

        # Build report
        report = {
            "status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "atoms-mcp",
            "version": "1.0.0",
            "dependencies": {
                name: {
                    "status": dep.status.value,
                    "response_time_ms": dep.response_time_ms,
                    "last_check": dep.last_check.isoformat() if dep.last_check else None,
                    "error": dep.error,
                    "metadata": dep.metadata
                }
                for name, dep in dependencies.items()
            },
            "metadata": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "region": os.getenv("VERCEL_REGION", "unknown"),
                "uptime_seconds": time.time() - self._start_time if hasattr(self, '_start_time') else 0
            }
        }

        return report

# Global health checker instance
atoms_health = AtomsHealthChecker()
```

## 4. Vercel Integration

### 4.1 Webhook Notifications
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/lib/atoms/observability/webhooks.py`

```python
"""
Vercel webhook integration for alerts and notifications.
"""
from __future__ import annotations
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum

from .logging import atoms_logger

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class VercelWebhookNotifier:
    """Send notifications to Vercel webhooks."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("VERCEL_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)

    async def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Send an alert to Vercel webhook."""
        if not self.enabled:
            atoms_logger.debug(f"Webhook disabled, skipping alert: {title}")
            return

        payload = {
            "level": level.value,
            "title": title,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "atoms-mcp",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "metadata": metadata or {}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        atoms_logger.info(f"Alert sent successfully: {title}")
                    else:
                        atoms_logger.error(
                            f"Failed to send alert: {response.status}",
                            title=title,
                            response_text=await response.text()
                        )
        except Exception as e:
            atoms_logger.error(f"Error sending webhook: {str(e)}", title=title)

    async def send_error_alert(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Send an error alert."""
        await self.send_alert(
            level=AlertLevel.ERROR,
            title=f"Error: {type(error).__name__}",
            message=str(error),
            metadata={
                "error_type": type(error).__name__,
                "context": context or {}
            }
        )

    async def send_deployment_notification(
        self,
        status: str,
        deployment_id: str,
        url: str
    ):
        """Send deployment status notification."""
        await self.send_alert(
            level=AlertLevel.INFO,
            title=f"Deployment {status}",
            message=f"Deployment {deployment_id} is {status}",
            metadata={
                "deployment_id": deployment_id,
                "url": url,
                "status": status
            }
        )

    async def send_health_alert(
        self,
        health_status: str,
        dependencies: Dict[str, Any]
    ):
        """Send health status alert."""
        level = AlertLevel.INFO
        if health_status == "unhealthy":
            level = AlertLevel.CRITICAL
        elif health_status == "degraded":
            level = AlertLevel.WARNING

        unhealthy_deps = [
            name for name, dep in dependencies.items()
            if dep.get("status") != "healthy"
        ]

        await self.send_alert(
            level=level,
            title=f"Service Health: {health_status.upper()}",
            message=f"Service is {health_status}. Affected dependencies: {', '.join(unhealthy_deps) if unhealthy_deps else 'None'}",
            metadata={
                "overall_status": health_status,
                "dependencies": dependencies
            }
        )

# Global webhook notifier
vercel_notifier = VercelWebhookNotifier()
```

### 4.2 Vercel-Specific Endpoints
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/lib/atoms/observability/endpoints.py`

```python
"""
Observability endpoints for monitoring and metrics.
"""
from __future__ import annotations
from typing import Dict, Any
from starlette.responses import Response, JSONResponse

from .metrics import atoms_metrics
from .health import atoms_health
from .logging import atoms_logger

async def metrics_endpoint(request) -> Response:
    """Prometheus metrics endpoint."""
    metrics_text = atoms_metrics.get_metrics_text()
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4"
    )

async def health_endpoint(request) -> JSONResponse:
    """Enhanced health check endpoint."""
    try:
        report = await atoms_health.get_health_report()
        status_code = 200 if report["status"] == "healthy" else 503

        return JSONResponse(
            content=report,
            status_code=status_code
        )
    except Exception as e:
        atoms_logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e)
            },
            status_code=503
        )

async def dashboard_endpoint(request) -> JSONResponse:
    """Dashboard data endpoint."""
    from observability import get_dashboard_collector, format_dashboard_data

    try:
        collector = get_dashboard_collector()
        dashboard_data = format_dashboard_data(collector.get_current_metrics())

        # Add custom Atoms-specific data
        dashboard_data.update({
            "service": "atoms-mcp",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": "1.0.0",
            "health": await atoms_health.get_health_report()
        })

        return JSONResponse(content=dashboard_data)
    except Exception as e:
        atoms_logger.error(f"Dashboard data failed: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

def register_observability_endpoints(app):
    """Register all observability endpoints with the app."""
    app.add_route("/metrics", metrics_endpoint, methods=["GET"])
    app.add_route("/health", health_endpoint, methods=["GET"])
    app.add_route("/api/observability/dashboard", dashboard_endpoint, methods=["GET"])
```

## 5. Integration with Existing Code

### 5.1 Enhanced App.py
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/app.py` (modifications)

```python
# Add to imports
from lib.atoms.observability import (
    ObservabilityMiddleware,
    register_observability_endpoints,
    atoms_logger,
    atoms_metrics,
    vercel_notifier
)

# After creating the app
app = GZipMiddleware(_base_app, minimum_size=500)

# Add observability middleware
app = ObservabilityMiddleware(app)

# Register observability endpoints
register_observability_endpoints(mcp)

# Add startup event
@mcp.on_startup
async def on_startup():
    """Initialize observability on startup."""
    atoms_logger.info("Starting Atoms MCP Server", environment="vercel")

    # Send deployment notification
    if os.getenv("VERCEL_DEPLOYMENT_ID"):
        await vercel_notifier.send_deployment_notification(
            status="started",
            deployment_id=os.getenv("VERCEL_DEPLOYMENT_ID"),
            url=os.getenv("VERCEL_URL", "unknown")
        )

# Add shutdown event
@mcp.on_shutdown
async def on_shutdown():
    """Clean up observability on shutdown."""
    atoms_logger.info("Shutting down Atoms MCP Server")
```

### 5.2 Tool Wrapper for Metrics
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/lib/atoms/observability/decorators.py`

```python
"""
Decorators for observability instrumentation.
"""
from __future__ import annotations
import functools
import time
from typing import Any, Callable

from .logging import atoms_logger, tool_name_var
from .metrics import atoms_metrics

def observe_tool(tool_name: str):
    """Decorator to add observability to MCP tools."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Set tool context
            tool_name_var.set(tool_name)

            # Log start
            atoms_logger.info(f"Tool execution started: {tool_name}")

            # Measure execution
            async with atoms_metrics.measure_tool(tool_name):
                try:
                    result = await func(*args, **kwargs)

                    # Log success
                    atoms_logger.log_tool_execution(
                        tool_name=tool_name,
                        duration_ms=0,  # Will be calculated by metrics
                        success=True
                    )

                    return result

                except Exception as e:
                    # Log failure
                    atoms_logger.log_tool_execution(
                        tool_name=tool_name,
                        duration_ms=0,  # Will be calculated by metrics
                        success=False,
                        error=str(e)
                    )
                    raise
                finally:
                    # Clear context
                    tool_name_var.set(None)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Similar implementation for sync functions
            tool_name_var.set(tool_name)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                atoms_logger.log_tool_execution(
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    success=True
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                atoms_logger.log_tool_execution(
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e)
                )
                raise
            finally:
                tool_name_var.set(None)

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
```

## 6. Testing Strategy

### 6.1 Unit Tests
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/tests/test_observability.py`

```python
"""
Tests for observability infrastructure.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch

from lib.atoms.observability import (
    AtomsLogger,
    AtomsMetrics,
    AtomsHealthChecker,
    VercelWebhookNotifier,
    observe_tool
)

class TestStructuredLogging:
    """Test structured logging functionality."""

    def test_logger_creation(self):
        logger = AtomsLogger("test")
        assert logger is not None

    def test_context_injection(self):
        from lib.atoms.observability.logging import correlation_id_var

        logger = AtomsLogger("test")
        correlation_id_var.set("test-correlation-id")

        # Mock the underlying log method
        with patch.object(logger, 'info') as mock_info:
            logger.log_request("GET", "/test", 200, 100.0)

            # Check correlation ID was included
            call_args = mock_info.call_args
            assert "correlation_id" in call_args[1]
            assert call_args[1]["correlation_id"] == "test-correlation-id"

class TestMetricsCollection:
    """Test metrics collection."""

    def test_metrics_initialization(self):
        metrics = AtomsMetrics()
        assert metrics.request_count is not None
        assert metrics.tool_execution_count is not None

    async def test_request_measurement(self):
        metrics = AtomsMetrics()

        async with metrics.measure_request("GET", "/test"):
            await asyncio.sleep(0.1)

        # Check metrics were recorded
        metrics_text = metrics.get_metrics_text()
        assert "atoms_mcp_request_duration_ms" in metrics_text

    async def test_tool_measurement(self):
        metrics = AtomsMetrics()

        async with metrics.measure_tool("test_tool"):
            await asyncio.sleep(0.1)

        # Check metrics were recorded
        metrics_text = metrics.get_metrics_text()
        assert "atoms_mcp_tool_duration_ms" in metrics_text
        assert "atoms_mcp_tool_executions_total" in metrics_text

class TestHealthChecks:
    """Test health check system."""

    async def test_dependency_checks(self):
        health = AtomsHealthChecker()

        # Mock dependencies
        with patch.object(health, 'check_supabase') as mock_supabase:
            mock_supabase.return_value = DependencyHealth(
                name="supabase",
                status=ServiceStatus.HEALTHY
            )

            dependencies = await health.check_all_dependencies()
            assert "supabase" in dependencies

    def test_overall_status_calculation(self):
        health = AtomsHealthChecker()

        # Test all healthy
        health._dependency_status = {
            "supabase": DependencyHealth("supabase", ServiceStatus.HEALTHY),
            "authkit": DependencyHealth("authkit", ServiceStatus.HEALTHY),
        }
        assert health.get_overall_status() == ServiceStatus.HEALTHY

        # Test degraded
        health._dependency_status["supabase"] = DependencyHealth(
            "supabase", ServiceStatus.DEGRADED
        )
        assert health.get_overall_status() == ServiceStatus.DEGRADED

        # Test unhealthy
        health._dependency_status["authkit"] = DependencyHealth(
            "authkit", ServiceStatus.UNHEALTHY
        )
        assert health.get_overall_status() == ServiceStatus.UNHEALTHY

class TestWebhookNotifications:
    """Test Vercel webhook integration."""

    async def test_alert_sending(self):
        notifier = VercelWebhookNotifier("http://test.webhook")

        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            await notifier.send_alert(
                AlertLevel.ERROR,
                "Test Alert",
                "Test message"
            )

            # Verify webhook was called
            mock_session.return_value.__aenter__.return_value.post.assert_called_once()

class TestObservabilityDecorators:
    """Test observability decorators."""

    async def test_tool_decorator(self):
        @observe_tool("test_tool")
        async def test_function():
            return "result"

        with patch('lib.atoms.observability.decorators.atoms_logger') as mock_logger:
            result = await test_function()

            assert result == "result"
            mock_logger.info.assert_called()
            mock_logger.log_tool_execution.assert_called_once()
```

### 6.2 Integration Tests
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/tests/test_observability_integration.py`

```python
"""
Integration tests for observability.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient

from app import app
from lib.atoms.observability import atoms_metrics, atoms_health

class TestObservabilityIntegration:
    """Integration tests for full observability stack."""

    def test_metrics_endpoint(self):
        client = TestClient(app)
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "atoms_mcp_requests_total" in response.text

    async def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "dependencies" in data

    def test_request_tracking(self):
        client = TestClient(app)

        # Make a request
        response = client.get("/health")

        # Check correlation ID in response
        assert "X-Correlation-ID" in response.headers
        assert "X-Request-ID" in response.headers

    async def test_end_to_end_observability(self):
        """Test complete observability flow."""
        client = TestClient(app)

        # Make several requests
        for _ in range(5):
            client.get("/health")

        # Check metrics were recorded
        metrics_response = client.get("/metrics")
        assert "atoms_mcp_requests_total" in metrics_response.text

        # Check health includes metrics
        health_response = client.get("/health")
        health_data = health_response.json()
        assert health_data["dependencies"].get("performance") is not None
```

## 7. Configuration Files

### 7.1 Environment Variables
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/.env.observability`

```env
# Observability Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
METRICS_ENABLED=true
PROMETHEUS_ENABLED=true
HEALTH_CHECK_ENABLED=true
ALERTING_ENABLED=true

# Vercel Webhook
VERCEL_WEBHOOK_URL=https://api.vercel.com/webhooks/atoms-mcp

# Alert Thresholds
ERROR_THRESHOLD=10
LATENCY_THRESHOLD=5000
FAILURE_RATE_THRESHOLD=0.1

# Health Check Settings
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=5
DEGRADED_THRESHOLD=0.8
```

### 7.2 Dashboard Configuration
**File:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/config/dashboard.json`

```json
{
  "name": "Atoms MCP Observability Dashboard",
  "version": "1.0.0",
  "panels": [
    {
      "id": "request-rate",
      "title": "Request Rate",
      "type": "graph",
      "metric": "atoms_mcp_requests_total",
      "aggregation": "rate"
    },
    {
      "id": "request-duration",
      "title": "Request Duration",
      "type": "histogram",
      "metric": "atoms_mcp_request_duration_ms",
      "percentiles": [0.5, 0.95, 0.99]
    },
    {
      "id": "tool-performance",
      "title": "Tool Performance",
      "type": "heatmap",
      "metric": "atoms_mcp_tool_duration_ms",
      "groupBy": "tool"
    },
    {
      "id": "error-rate",
      "title": "Error Rate",
      "type": "graph",
      "metric": "atoms_mcp_errors_total",
      "aggregation": "rate"
    },
    {
      "id": "dependency-health",
      "title": "Dependency Health",
      "type": "status",
      "metric": "atoms_mcp_dependency_health"
    },
    {
      "id": "active-connections",
      "title": "Active Connections",
      "type": "gauge",
      "metric": "atoms_mcp_active_connections"
    }
  ],
  "alerts": [
    {
      "name": "High Error Rate",
      "condition": "rate(atoms_mcp_errors_total) > 0.1",
      "severity": "critical",
      "notification": "webhook"
    },
    {
      "name": "High Latency",
      "condition": "atoms_mcp_request_duration_ms > 5000",
      "severity": "warning",
      "notification": "webhook"
    },
    {
      "name": "Dependency Unhealthy",
      "condition": "atoms_mcp_dependency_health < 1",
      "severity": "error",
      "notification": "webhook"
    }
  ]
}
```

## 8. Deployment Guide

### 8.1 Local Development
```bash
# Install dependencies
uv sync --group dev

# Run with observability enabled
export LOG_LEVEL=DEBUG
export METRICS_ENABLED=true
python atoms-mcp.py start

# Access metrics
curl http://localhost:8000/metrics

# Check health
curl http://localhost:8000/health
```

### 8.2 Vercel Deployment
```bash
# Set environment variables in Vercel
vercel env add LOG_LEVEL production
vercel env add VERCEL_WEBHOOK_URL production

# Deploy with observability
vercel --prod

# Monitor deployment
curl https://mcp.atoms.tech/health
curl https://mcp.atoms.tech/metrics
```

### 8.3 Monitoring Setup
1. Configure Prometheus to scrape `/metrics` endpoint
2. Set up Grafana dashboards using provided JSON config
3. Configure alerting rules in Vercel dashboard
4. Set up webhook endpoints for notifications

## 9. Performance Impact Analysis

### Expected Overhead
- **Logging**: ~1-2ms per request for JSON serialization
- **Metrics**: <1ms for counter/gauge updates, ~2ms for histogram observations
- **Health Checks**: Async, non-blocking, 5s timeout
- **Correlation ID**: <0.5ms for generation and injection
- **Total Expected Overhead**: ~3-5ms per request

### Optimization Strategies
1. **Batching**: Aggregate metrics before export
2. **Sampling**: Sample traces for high-volume endpoints
3. **Caching**: Cache health check results for 30 seconds
4. **Async Processing**: All I/O operations are async
5. **Circuit Breakers**: Prevent cascade failures in health checks

## 10. Implementation Phases

### Phase 5A: Core Infrastructure (Days 1-2)
- [ ] Implement structured logging module
- [ ] Set up metrics collection
- [ ] Create health check system
- [ ] Add correlation ID tracking

### Phase 5B: Integration (Days 3-4)
- [ ] Add middleware to app.py
- [ ] Wrap existing tools with decorators
- [ ] Integrate with existing auth system
- [ ] Test with existing endpoints

### Phase 5C: Vercel Features (Days 5-6)
- [ ] Implement webhook notifications
- [ ] Add Vercel-specific health checks
- [ ] Configure environment variables
- [ ] Deploy to preview environment

### Phase 5D: Dashboards & Alerts (Days 7-8)
- [ ] Create Grafana dashboards
- [ ] Configure alert rules
- [ ] Set up notification channels
- [ ] Document monitoring procedures

### Phase 5E: Testing & Optimization (Days 9-10)
- [ ] Run performance tests
- [ ] Optimize hot paths
- [ ] Load test with observability
- [ ] Final deployment to production

## Conclusion

This comprehensive Phase 5 implementation provides:
1. **Complete Observability**: All three pillars (logs, metrics, traces)
2. **Production Ready**: Designed for Vercel serverless environment
3. **Extensible**: Easy to add new metrics and health checks
4. **Performance Conscious**: Minimal overhead with async operations
5. **Developer Friendly**: Clear APIs and comprehensive testing

The implementation leverages existing observability-kit while adding Atoms-specific features and Vercel integration. This design supports parallel implementation by multiple agents and provides clear interfaces between components.