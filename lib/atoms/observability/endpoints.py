"""
Production-ready observability API endpoints.

This module provides FastAPI endpoints for:
- /metrics - Prometheus-formatted metrics
- /health - Health check with dependency status
- /api/observability/dashboard - Observability dashboard data

Author: Atoms MCP Platform
Version: 1.0.0
"""

import time
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from .health import HealthStatus, check_health
from .logging import get_logger
from .metrics import get_prometheus_metrics, registry

logger = get_logger(__name__)

# Create router for observability endpoints
router = APIRouter(tags=["observability"])


# Pydantic models for API responses

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Timestamp of health check")
    uptime_seconds: float | None = Field(None, description="System uptime in seconds")
    version: str | None = Field(None, description="Application version")
    components: list[dict[str, Any]] = Field(..., description="Component health details")


class MetricValueModel(BaseModel):
    """Single metric value model."""
    labels: dict[str, str] = Field(default_factory=dict)
    value: float


class MetricModel(BaseModel):
    """Metric model."""
    name: str
    type: str
    description: str
    values: list[Any]


class MetricsSnapshotResponse(BaseModel):
    """Metrics snapshot response model."""
    timestamp: str
    metrics: dict[str, Any]


class DashboardMetric(BaseModel):
    """Dashboard metric summary."""
    name: str
    value: float
    unit: str
    change_percent: float | None = None


class DashboardResponse(BaseModel):
    """Observability dashboard response."""
    health: HealthCheckResponse
    key_metrics: list[DashboardMetric]
    recent_errors: list[dict[str, Any]]
    performance_summary: dict[str, Any]


# Endpoints

@router.get(
    "/metrics",
    response_class=Response,
    summary="Prometheus Metrics",
    description="Get all metrics in Prometheus exposition format"
)
async def get_metrics() -> Response:
    """
    Return metrics in Prometheus exposition format.

    This endpoint is designed to be scraped by Prometheus or compatible
    monitoring systems.

    Returns:
        Plain text response with Prometheus-formatted metrics
    """
    try:
        metrics_text = get_prometheus_metrics()

        return Response(
            content=metrics_text,
            media_type="text/plain; version=0.0.4"
        )

    except Exception as e:
        logger.error(
            "Failed to generate Prometheus metrics",
            extra_fields={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate metrics"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Get system health status including all dependencies"
)
async def get_health() -> HealthCheckResponse:
    """
    Perform comprehensive health check.

    Checks:
    - Database connectivity
    - External service availability
    - System resources
    - Component health

    Returns:
        Health check response with component details
    """
    try:
        system_health = await check_health()

        return HealthCheckResponse(
            status=system_health.status.value,
            timestamp=system_health.timestamp.isoformat(),
            uptime_seconds=system_health.uptime_seconds,
            version=system_health.version,
            components=[c.to_dict() for c in system_health.components]
        )

    except Exception as e:
        logger.error(
            "Health check failed",
            extra_fields={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )

        # Return unhealthy status
        return HealthCheckResponse(
            status=HealthStatus.UNHEALTHY.value,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            uptime_seconds=None,
            version=None,
            components=[{
                "component_name": "system",
                "component_type": "internal_service",
                "status": "unhealthy",
                "message": f"Health check error: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }]
        )


@router.get(
    "/health/live",
    summary="Liveness Probe",
    description="Simple liveness check for Kubernetes/container orchestration"
)
async def liveness_probe() -> dict[str, str]:
    """
    Liveness probe endpoint.

    Used by container orchestration systems to determine if the
    application is alive and should continue running.

    Returns:
        Simple status response
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness Probe",
    description="Readiness check for Kubernetes/container orchestration"
)
async def readiness_probe() -> dict[str, str]:
    """
    Readiness probe endpoint.

    Used by container orchestration systems to determine if the
    application is ready to receive traffic.

    Returns:
        Status response based on critical components
    """
    try:
        system_health = await check_health()

        # Check if any critical components are unhealthy
        critical_unhealthy = any(
            c.status == HealthStatus.UNHEALTHY
            for c in system_health.components
        )

        if critical_unhealthy or system_health.status == HealthStatus.UNHEALTHY:
            raise HTTPException(
                status_code=503,
                detail="System not ready"
            )

        return {"status": "ready"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Readiness check failed",
            extra_fields={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=503,
            detail="System not ready"
        )


@router.get(
    "/api/observability/metrics/snapshot",
    response_model=MetricsSnapshotResponse,
    summary="Metrics Snapshot",
    description="Get current snapshot of all metrics in JSON format"
)
async def get_metrics_snapshot() -> MetricsSnapshotResponse:
    """
    Get current metrics snapshot.

    Returns all metrics in structured JSON format, useful for
    custom dashboards and monitoring tools.

    Returns:
        JSON response with all metrics
    """
    try:
        metrics = registry.collect_all()

        return MetricsSnapshotResponse(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            metrics=metrics
        )

    except Exception as e:
        logger.error(
            "Failed to generate metrics snapshot",
            extra_fields={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate metrics snapshot"
        )


@router.get(
    "/api/observability/dashboard",
    response_model=DashboardResponse,
    summary="Observability Dashboard",
    description="Get comprehensive observability dashboard data"
)
async def get_dashboard() -> DashboardResponse:
    """
    Get observability dashboard data.

    Provides a comprehensive view of system health, metrics, errors,
    and performance for building custom dashboards.

    Returns:
        Dashboard data including health, metrics, errors, and performance
    """
    try:
        # Get health status
        system_health = await check_health()

        health_response = HealthCheckResponse(
            status=system_health.status.value,
            timestamp=system_health.timestamp.isoformat(),
            uptime_seconds=system_health.uptime_seconds,
            version=system_health.version,
            components=[c.to_dict() for c in system_health.components]
        )

        # Get key metrics
        key_metrics = await _get_key_metrics()

        # Get recent errors (simulated - in production, would query error log)
        recent_errors: list[dict[str, Any]] = []

        # Get performance summary
        performance_summary = await _get_performance_summary()

        return DashboardResponse(
            health=health_response,
            key_metrics=key_metrics,
            recent_errors=recent_errors,
            performance_summary=performance_summary
        )

    except Exception as e:
        logger.error(
            "Failed to generate dashboard data",
            extra_fields={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate dashboard data"
        )


async def _get_key_metrics() -> list[DashboardMetric]:
    """Extract key metrics for dashboard."""
    metrics = registry.collect_all()
    key_metrics = []

    # HTTP requests
    if "http_requests_total" in metrics:
        total_requests = sum(
            value for _, value in metrics["http_requests_total"]["values"]
        )
        key_metrics.append(
            DashboardMetric(
                name="Total HTTP Requests",
                value=total_requests,
                unit="requests"
            )
        )

    # Tool executions
    if "tool_executions_total" in metrics:
        total_executions = sum(
            value for _, value in metrics["tool_executions_total"]["values"]
        )
        key_metrics.append(
            DashboardMetric(
                name="Total Tool Executions",
                value=total_executions,
                unit="executions"
            )
        )

    # Errors
    if "errors_total" in metrics:
        total_errors = sum(
            value for _, value in metrics["errors_total"]["values"]
        )
        key_metrics.append(
            DashboardMetric(
                name="Total Errors",
                value=total_errors,
                unit="errors"
            )
        )

    # Active connections
    if "active_connections" in metrics:
        active_conns = sum(
            value for _, value in metrics["active_connections"]["values"]
        )
        key_metrics.append(
            DashboardMetric(
                name="Active Connections",
                value=active_conns,
                unit="connections"
            )
        )

    return key_metrics


async def _get_performance_summary() -> dict[str, Any]:
    """Get performance summary statistics."""
    metrics = registry.collect_all()
    summary: dict[str, Any] = {
        "http_requests": {},
        "tool_executions": {},
        "database_queries": {}
    }

    # HTTP request performance
    if "http_request_duration_seconds" in metrics:
        histogram_data = metrics["http_request_duration_seconds"]["values"]
        if histogram_data:
            # Calculate average from histogram data
            total_sum = 0
            total_count = 0
            for _, buckets, sum_value, count in histogram_data:
                total_sum += sum_value
                total_count += count

            if total_count > 0:
                avg_duration_ms = (total_sum / total_count) * 1000
                summary["http_requests"] = {
                    "average_duration_ms": round(avg_duration_ms, 2),
                    "total_requests": total_count
                }

    # Tool execution performance
    if "tool_execution_duration_seconds" in metrics:
        histogram_data = metrics["tool_execution_duration_seconds"]["values"]
        if histogram_data:
            total_sum = 0
            total_count = 0
            for _, buckets, sum_value, count in histogram_data:
                total_sum += sum_value
                total_count += count

            if total_count > 0:
                avg_duration_ms = (total_sum / total_count) * 1000
                summary["tool_executions"] = {
                    "average_duration_ms": round(avg_duration_ms, 2),
                    "total_executions": total_count
                }

    # Database query performance
    if "database_query_duration_seconds" in metrics:
        histogram_data = metrics["database_query_duration_seconds"]["values"]
        if histogram_data:
            total_sum = 0
            total_count = 0
            for _, buckets, sum_value, count in histogram_data:
                total_sum += sum_value
                total_count += count

            if total_count > 0:
                avg_duration_ms = (total_sum / total_count) * 1000
                summary["database_queries"] = {
                    "average_duration_ms": round(avg_duration_ms, 2),
                    "total_queries": total_count
                }

    return summary


@router.get(
    "/api/observability/metrics/{metric_name}",
    summary="Get Specific Metric",
    description="Get detailed information about a specific metric"
)
async def get_specific_metric(metric_name: str) -> dict[str, Any]:
    """
    Get detailed information about a specific metric.

    Args:
        metric_name: Name of the metric to retrieve

    Returns:
        Metric details including type, description, and current values
    """
    try:
        metrics = registry.collect_all()

        if metric_name not in metrics:
            raise HTTPException(
                status_code=404,
                detail=f"Metric '{metric_name}' not found"
            )

        return {
            "name": metric_name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            **metrics[metric_name]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get metric: {metric_name}",
            extra_fields={
                "metric_name": metric_name,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metric: {metric_name}"
        )


# Export router for integration with main FastAPI app
__all__ = ["router", "get_metrics", "get_health", "get_dashboard"]
