"""
MCP QA Core - Unified Testing Framework Components

Provides shared testing infrastructure for MCP servers:
- Test registration and discovery
- Test execution (parallel/sequential)
- Live event-driven execution
- Client adapters
- Result caching
- Health checks
"""

# Test Registry
from .test_registry import (
    TestRegistry,
    get_test_registry,
    mcp_test,
    require_auth,
    skip_if,
    timeout,
    retry,
)

# Decorators
from .decorators import cache_result

# Adapters
from .adapters import MCPClientAdapter
from .enhanced_adapter import EnhancedMCPAdapter, create_enhanced_adapter

# Cache
from .cache import TestCache

# Test Runners
from .base.test_runner import BaseTestRunner as TestRunner
from .live_runner import LiveTestRunner

# Health Checks
from .health_checks import HealthChecker

# Reporters (re-exported from reporters package for backward compatibility)
from mcp_qa.reporters import (
    TestReporter,
    ConsoleReporter,
    JSONReporter,
    MarkdownReporter,
    FunctionalityMatrixReporter,
    DetailedErrorReporter,
)

# Progress Display
from .progress_display import ComprehensiveProgressDisplay

# Data Generators
from .data_generators import DataGenerator

# Parallel Execution
from .client_pool import WorkerClientPool
from .parallel_clients import ParallelClientManager
from .connection_manager import ConnectionManager, ConnectionState, WaitStrategy

# Streaming
try:
    from .streaming import (
        TestResult,
        ParallelStreamCollector,
        SmartBatchingBuffer,
        InstantFeedbackMode,
        StreamingResultDisplay,
    )
    HAS_STREAMING = True
except ImportError:
    HAS_STREAMING = False

__all__ = [
    # Registry
    "TestRegistry",
    "get_test_registry",
    "mcp_test",
    "require_auth",
    "skip_if",
    "timeout",
    "retry",
    "cache_result",
    # Adapters
    "MCPClientAdapter",
    "EnhancedMCPAdapter",
    "create_enhanced_adapter",
    # Cache
    "TestCache",
    # Runners
    "TestRunner",
    "LiveTestRunner",
    # Health
    "HealthChecker",
    # Reporters
    "TestReporter",
    "ConsoleReporter",
    "JSONReporter",
    "MarkdownReporter",
    "FunctionalityMatrixReporter",
    "DetailedErrorReporter",
    # Progress
    "ComprehensiveProgressDisplay",
    # Data
    "DataGenerator",
    # Parallel
    "WorkerClientPool",
    "ParallelClientManager",
    "ConnectionManager",
    "ConnectionState",
    "WaitStrategy",
    # Streaming
    "TestResult",
    "ParallelStreamCollector",
    "SmartBatchingBuffer",
    "InstantFeedbackMode",
    "StreamingResultDisplay",
]

if HAS_STREAMING:
    __all__.extend([
        "TestResult",
        "ParallelStreamCollector",
        "SmartBatchingBuffer",
        "InstantFeedbackMode",
        "StreamingResultDisplay",
    ])


__version__ = "0.1.0"
