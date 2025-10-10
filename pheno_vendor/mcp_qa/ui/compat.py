"""
Backward Compatibility for mcp_qa.ui module

Provides aliases to tui-kit implementations for seamless migration.
"""

from ..tui.compat import (
    UnifiedProgressWidget,
    ComprehensiveProgressDisplay,
    TestProgressTracker,
    Task,
    TaskStatus,
    TaskPriority,
    TaskMetrics,
    CategoryStats,
    StreamCapture,
    CapturedLine,
    LogLevel,
    OutputFormatter,
    capture_output,
)

# Re-export everything
__all__ = [
    "UnifiedProgressWidget",
    "ComprehensiveProgressDisplay",
    "TestProgressTracker",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskMetrics",
    "CategoryStats",
    "StreamCapture",
    "CapturedLine",
    "LogLevel",
    "OutputFormatter",
    "capture_output",
]
