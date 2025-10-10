"""
Dashboard module for real-time monitoring.

Provides:
- Real-time metric aggregation
- WebSocket streaming for live updates
- Dashboard data formatting
- Multi-tenant dashboard support
"""

from .aggregator import (
    MetricType,
    Metric,
    MetricAggregator,
    DashboardDataCollector,
    get_dashboard_collector,
)
from .formatters import (
    DashboardFormatter,
    format_dashboard_data,
    format_component_status,
)

__all__ = [
    # Types
    "MetricType",
    "Metric",
    # Aggregation
    "MetricAggregator",
    "DashboardDataCollector",
    "get_dashboard_collector",
    # Formatting
    "DashboardFormatter",
    "format_dashboard_data",
    "format_component_status",
]

# Optional WebSocket streaming support
try:
    from .streaming import (
        DashboardStreamer,
        WebSocketDashboard,
        get_dashboard_streamer,
    )

    __all__.extend([
        "DashboardStreamer",
        "WebSocketDashboard",
        "get_dashboard_streamer",
    ])
except ImportError:
    # WebSocket support not available
    pass
