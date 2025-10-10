"""
Dashboard data formatting utilities.

Provides formatters for converting raw metrics and health data
into dashboard-ready formats.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DashboardFormatter:
    """
    Formats data for dashboard display.

    Provides consistent formatting for:
    - Component status
    - Metrics data
    - Health reports
    - Time series data
    """

    @staticmethod
    def format_component_status(
        component_name: str,
        status: str,
        message: str = "",
        response_time_ms: float = 0.0,
        last_check: Optional[datetime] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format component status for dashboard.

        Args:
            component_name: Name of the component
            status: Status string (healthy, warning, critical, etc.)
            message: Optional status message
            response_time_ms: Response time in milliseconds
            last_check: Last check timestamp
            details: Additional details

        Returns:
            Formatted component status dict
        """
        return {
            "name": component_name,
            "status": status,
            "message": message,
            "response_time_ms": round(response_time_ms, 2),
            "last_check": last_check.isoformat() if last_check else None,
            "details": details or {},
        }

    @staticmethod
    def format_metric_series(
        metrics: List[Any],
        value_key: str = "value",
        timestamp_key: str = "timestamp",
        bucket_minutes: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Format metrics into time series buckets.

        Args:
            metrics: List of metric objects or dicts
            value_key: Key/attr for metric value
            timestamp_key: Key/attr for timestamp
            bucket_minutes: Minutes per bucket for aggregation

        Returns:
            List of time series data points
        """
        if not metrics:
            return []

        # Group metrics into time buckets
        buckets: Dict[datetime, List[float]] = {}

        for metric in metrics:
            # Get value and timestamp
            if isinstance(metric, dict):
                value = metric.get(value_key, 0)
                timestamp = metric.get(timestamp_key)
            else:
                value = getattr(metric, value_key, 0)
                timestamp = getattr(metric, timestamp_key, None)

            if timestamp is None:
                continue

            # Convert to datetime if needed
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            # Round to bucket
            bucket_time = timestamp.replace(
                minute=(timestamp.minute // bucket_minutes) * bucket_minutes,
                second=0,
                microsecond=0,
            )

            if bucket_time not in buckets:
                buckets[bucket_time] = []
            buckets[bucket_time].append(float(value))

        # Format as series
        series = []
        for bucket_time in sorted(buckets.keys()):
            values = buckets[bucket_time]
            series.append({
                "timestamp": bucket_time.isoformat(),
                "value": sum(values) / len(values),  # Average
                "count": len(values),
                "min": min(values),
                "max": max(values),
            })

        return series

    @staticmethod
    def format_health_report(
        overall_status: str,
        components: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None,
        alerts: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Format health report for dashboard.

        Args:
            overall_status: Overall system status
            components: Component status dict
            metrics: Optional metrics summary
            alerts: Optional active alerts
            timestamp: Report timestamp

        Returns:
            Formatted health report
        """
        return {
            "overall_status": overall_status,
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "components": components,
            "metrics": metrics or {},
            "active_alerts": alerts or [],
            "component_count": len(components),
            "healthy_count": sum(
                1 for c in components.values()
                if c.get("status") == "healthy"
            ),
            "critical_count": sum(
                1 for c in components.values()
                if c.get("status") == "critical"
            ),
        }

    @staticmethod
    def format_alert(
        alert_id: str,
        name: str,
        description: str,
        severity: str,
        triggered_at: Optional[datetime] = None,
        resolved_at: Optional[datetime] = None,
        is_active: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format alert for dashboard display.

        Args:
            alert_id: Alert ID
            name: Alert name
            description: Alert description
            severity: Severity level
            triggered_at: When alert was triggered
            resolved_at: When alert was resolved
            is_active: Whether alert is currently active
            metadata: Additional metadata

        Returns:
            Formatted alert dict
        """
        duration = None
        if triggered_at:
            end_time = resolved_at or datetime.now(timezone.utc)
            duration = (end_time - triggered_at).total_seconds()

        return {
            "id": alert_id,
            "name": name,
            "description": description,
            "severity": severity,
            "is_active": is_active,
            "triggered_at": triggered_at.isoformat() if triggered_at else None,
            "resolved_at": resolved_at.isoformat() if resolved_at else None,
            "duration_seconds": duration,
            "metadata": metadata or {},
        }

    @staticmethod
    def format_task_metrics(
        total_created: int = 0,
        total_completed: int = 0,
        total_failed: int = 0,
        avg_execution_time: float = 0.0,
        success_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Format task metrics for dashboard.

        Args:
            total_created: Total tasks created
            total_completed: Total tasks completed
            total_failed: Total tasks failed
            avg_execution_time: Average execution time
            success_rate: Optional success rate (calculated if None)

        Returns:
            Formatted task metrics
        """
        if success_rate is None:
            total = total_completed + total_failed
            success_rate = (total_completed / total * 100) if total > 0 else 100.0

        return {
            "total_created": total_created,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "total_processed": total_completed + total_failed,
            "success_rate": round(success_rate, 2),
            "failure_rate": round(100 - success_rate, 2),
            "avg_execution_time": round(avg_execution_time, 3),
        }

    @staticmethod
    def format_system_info(
        uptime_seconds: float = 0.0,
        connected_clients: int = 0,
        memory_usage_mb: float = 0.0,
        cpu_percent: float = 0.0,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format system information for dashboard.

        Args:
            uptime_seconds: System uptime in seconds
            connected_clients: Number of connected clients
            memory_usage_mb: Memory usage in MB
            cpu_percent: CPU usage percentage
            additional_info: Additional system info

        Returns:
            Formatted system info
        """
        # Format uptime
        uptime_delta = timedelta(seconds=int(uptime_seconds))
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

        return {
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": uptime_str,
            "connected_clients": connected_clients,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "cpu_percent": round(cpu_percent, 2),
            **(additional_info or {}),
        }


def format_dashboard_data(
    health_report: Optional[Dict[str, Any]] = None,
    task_metrics: Optional[Dict[str, Any]] = None,
    active_alerts: Optional[List[Dict[str, Any]]] = None,
    system_info: Optional[Dict[str, Any]] = None,
    time_series_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    """
    Format complete dashboard data.

    Args:
        health_report: Health report data
        task_metrics: Task metrics data
        active_alerts: Active alerts list
        system_info: System information
        time_series_data: Time series metrics

    Returns:
        Complete formatted dashboard data
    """
    return {
        "health": health_report or {},
        "task_metrics": task_metrics or {},
        "active_alerts": active_alerts or [],
        "system_info": system_info or {},
        "time_series": time_series_data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def format_component_status(
    component_name: str,
    status: str,
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function for formatting component status.

    Args:
        component_name: Component name
        status: Status string
        **kwargs: Additional formatting arguments

    Returns:
        Formatted component status
    """
    return DashboardFormatter.format_component_status(
        component_name,
        status,
        **kwargs,
    )
