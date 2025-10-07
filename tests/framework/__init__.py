"""
Atoms MCP Test Framework

A robust, modular test framework for Atoms MCP server based on Zen's architecture.
Provides decorator-based test registration, smart caching, parallel execution,
and comprehensive reporting.

Components:
- decorators: @mcp_test, @require_auth, @skip_if, @timeout, @retry
- reporters: Console, JSON, Markdown, FunctionalityMatrix
- adapters: FastMCP client adapter
- cache: Smart caching based on tool code hashes
- runner: Parallel/sequential test execution with progress tracking
"""

from .adapters import AtomsMCPClientAdapter
from .cache import TestCache
from .client_pool import WorkerClientPool
from .connection_manager import ConnectionManager, ConnectionState, WaitStrategy
from .data_generators import DataGenerator
from .health_checks import HealthChecker
from .progress_display import ComprehensiveProgressDisplay
from .decorators import (
    TestRegistry,
    cache_result,
    get_test_registry,
    mcp_test,
    require_auth,
    retry,
    skip_if,
    timeout,
)
from .factories import ParameterPermutationFactory, TestFactory, TestSuiteFactory
from .file_watcher import SmartReloadManager, TestFileWatcher
from .live_runner import LiveTestRunner
from .oauth_cache import CachedOAuthClient, create_cached_client
from .parallel_clients import ParallelClientManager
from .patterns import IntegrationPattern, ToolTestPattern, UserStoryPattern
from .reporters import (
    ConsoleReporter,
    DetailedErrorReporter,
    FunctionalityMatrixReporter,
    JSONReporter,
    MarkdownReporter,
    TestReporter,
)
from .runner import TestRunner
from .tui import run_tui_dashboard
from .validators import FieldValidator, ResponseValidator

__all__ = [
    # Decorators
    "mcp_test",
    "require_auth",
    "skip_if",
    "timeout",
    "retry",
    "cache_result",
    "TestRegistry",
    "get_test_registry",
    # Reporters
    "TestReporter",
    "ConsoleReporter",
    "JSONReporter",
    "MarkdownReporter",
    "FunctionalityMatrixReporter",
    "DetailedErrorReporter",
    # Cache
    "TestCache",
    # OAuth Cache
    "CachedOAuthClient",
    "create_cached_client",
    # Adapter
    "AtomsMCPClientAdapter",
    # Runners
    "TestRunner",
    "LiveTestRunner",
    # Patterns
    "ToolTestPattern",
    "UserStoryPattern",
    "IntegrationPattern",
    # Factories
    "TestFactory",
    "TestSuiteFactory",
    "ParameterPermutationFactory",
    # Validators
    "ResponseValidator",
    "FieldValidator",
    # Data Generators
    "DataGenerator",
    # Health Checks
    "HealthChecker",
    # Connection Management
    "ConnectionManager",
    "ConnectionState",
    "WaitStrategy",
    # Client Pool
    "WorkerClientPool",
    "ParallelClientManager",
    # Progress Display
    "ComprehensiveProgressDisplay",
    # File Watching
    "TestFileWatcher",
    "SmartReloadManager",
    # TUI
    "run_tui_dashboard",
]
