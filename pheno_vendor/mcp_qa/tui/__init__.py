"""
TUI components for MCP test dashboards.

New modular structure (RECOMMENDED):
- base/: Base classes (BaseDashboard, BaseWidget)
- factories/: Factory classes for creating components  
- components/: Generic reusable components

Usage:
    from mcp_qa.tui.base import BaseDashboard
    from mcp_qa.tui.factories import DashboardFactory, WidgetFactory
    from mcp_qa.tui.components import GenericStatusPanel
    
    class MyDashboard(BaseDashboard):
        def build_layout(self):
            return Container(
                WidgetFactory.create_status_panel("Server", ["Port", "Status"]),
                WidgetFactory.create_log_viewer("Logs", "/var/log/app.log")
            )
"""

# New modular structure (RECOMMENDED)
from .base import BaseDashboard, BaseWidget
from .factories import DashboardFactory, WidgetFactory
from .components import GenericStatusPanel

__all__ = [
    # Base classes
    'BaseDashboard',
    'BaseWidget',
    
    # Factories
    'DashboardFactory',
    'WidgetFactory',
    
    # Components
    'GenericStatusPanel',
]

__version__ = "2.0.0"

# Note: Old monolithic files (dashboard_atoms.py, widgets.py, etc.) are deprecated
# They have Textual API compatibility issues (Widget.Message is deprecated)
# Use the new modular structure above for new projects
