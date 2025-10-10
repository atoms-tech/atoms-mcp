"""
Atoms MCP Test Framework

A robust, modular test framework for Atoms MCP server.
Most components are now imported from mcp_qa.core for consistency.

Local Components (Atoms-specific):
- adapters: AtomsMCPClientAdapter (wraps FastMCP client)
- runner: TestRunner (with Atoms-specific enhancements)
- oauth_automation: OAuth flow automation
- file_watcher: Development file watching
- tui: Terminal UI dashboard

Shared Components (from mcp-QA):
- decorators, reporters, cache, validators, patterns, data generators
- parallel execution, progress display, health checks
"""

# ============================================================================
# Import from pheno-sdk/mcp-qa (shared infrastructure)
# ============================================================================

try:
    # Core shared components
    from mcp_qa.core import (
        # Progress
        ComprehensiveProgressDisplay,
        ConnectionManager,
        ConnectionState,
        # Reporters
        ConsoleReporter,
        # Data & Validators
        DataGenerator,
        DetailedErrorReporter,
        FunctionalityMatrixReporter,
        # Health
        HealthChecker,
        JSONReporter,
        MarkdownReporter,
        ParallelClientManager,
        # Cache
        TestCache,
        # Decorators & Registry
        TestRegistry,
        TestReporter,
        WaitStrategy,
        # Parallel Execution
        WorkerClientPool,
        cache_result,
        get_test_registry,
        mcp_test,
        require_auth,
        retry,
        skip_if,
        timeout,
    )

    # Base patterns (NEW!)
    from mcp_qa.core.base import (
        BaseClientAdapter,
        BaseTestRunner,
    )

    # Optimizations (NEW - with fixed PooledMCPClient!)
    from mcp_qa.core.optimizations import (
        OptimizationFlags,
        PooledMCPClient,
        ResponseCacheLayer,
    )

    HAS_MCP_QA = True

except ImportError as e:
    print(f"⚠️  Warning: Could not import from mcp-qa: {e}")
    print("   Falling back to local implementations")

    # Fallback to local imports if mcp-QA not installed
    from .cache import TestCache

    # These have been consolidated to mcp_qa - no local fallback available
    # (deleted in Phase 1 & 2 consolidation)
    WorkerClientPool = None
    ConnectionManager = None
    ConnectionState = None
    WaitStrategy = None
    DataGenerator = None
    HealthChecker = None
    ComprehensiveProgressDisplay = None
    ParallelClientManager = None
    TestRegistry = None
    get_test_registry = None
    mcp_test = None
    require_auth = None
    retry = None
    skip_if = None
    timeout = None
    cache_result = None
    ConsoleReporter = None
    DetailedErrorReporter = None
    FunctionalityMatrixReporter = None
    JSONReporter = None
    MarkdownReporter = None
    TestReporter = None

    # Base patterns not available in fallback mode
    BaseClientAdapter = None
    BaseTestRunner = None
    PooledMCPClient = None
    ResponseCacheLayer = None
    OptimizationFlags = None

    HAS_MCP_QA = False

# ============================================================================
# Local Atoms-specific implementations
# ============================================================================

# ============================================================================
# Local Atoms-specific implementations
# ============================================================================

# Adapters (extends BaseClientAdapter)
from .adapters import AtomsMCPClientAdapter

# Runners (extends BaseTestRunner)
from .runner import AtomsTestRunner

# Backward compatibility alias
TestRunner = AtomsTestRunner

# Other Atoms-specific components (core - must exist)
# Note: cache_result decorator is now in mcp_qa.core.decorators

# Import patterns, validators, and factories from mcp_qa
try:
    from mcp_qa.core.factories import ParameterPermutationFactory, TestFactory, TestSuiteFactory
    from mcp_qa.core.patterns import IntegrationPattern, ToolTestPattern, UserStoryPattern
    from mcp_qa.core.validators import FieldValidator, ResponseValidator
except ImportError:
    # Fallback to archived versions if mcp_qa not available
    print("⚠️  Warning: mcp_qa.core not available, some features may be limited")
    IntegrationPattern = None
    ToolTestPattern = None
    UserStoryPattern = None
    FieldValidator = None
    ResponseValidator = None
    ParameterPermutationFactory = None
    TestFactory = None
    TestSuiteFactory = None

# Import Atoms-specific helpers
from .atoms_helpers import AtomsTestHelpers

try:
    from .file_watcher import SmartReloadManager, TestFileWatcher
except ImportError:
    SmartReloadManager = None
    TestFileWatcher = None

try:
    from .live_runner import LiveTestRunner
except ImportError:
    LiveTestRunner = None

try:
    from .workflow_manager import TestWorkflowManager
except ImportError:
    TestWorkflowManager = None

try:
    from .collaboration import (
        CollaborationBroadcaster,
        CollaborationFactory,
        CollaborationSubscriber,
    )
    from .collaboration import (
        TestEvent as CollaborationEvent,
    )
except ImportError:
    CollaborationBroadcaster = None
    CollaborationFactory = None
    CollaborationSubscriber = None
    CollaborationEvent = None

try:
    from .oauth_cache import CachedOAuthClient, create_cached_client
except ImportError:
    CachedOAuthClient = None
    create_cached_client = None

try:
    from .oauth_automation import (
        FlowResult,
        FlowStep,
        OAuthAutomator,
        OAuthFlowConfig,
        create_default_automator,
        flow_config_from_dict,
        load_flow_config_from_yaml,
    )
except ImportError:
    FlowResult = None
    FlowStep = None
    OAuthAutomator = None
    OAuthFlowConfig = None
    create_default_automator = None
    flow_config_from_dict = None
    load_flow_config_from_yaml = None

try:
    from .oauth_session import OAuthSessionBroker
except ImportError:
    OAuthSessionBroker = None

try:
    from .tui import run_tui_dashboard
except ImportError:
    run_tui_dashboard = None

# Unified runner (integrates with pheno-sdk UnifiedMCPTestRunner)
try:
    from .atoms_unified_runner import AtomsMCPTestRunner, run_atoms_tests
    HAS_UNIFIED_RUNNER = True
except ImportError:
    HAS_UNIFIED_RUNNER = False
    AtomsMCPTestRunner = None
    run_atoms_tests = None

__all__ = [
    # ========== pheno-sdk Base Classes (NEW!) ==========
    "BaseClientAdapter",
    "BaseTestRunner",

    # ========== pheno-sdk Optimizations (NEW!) ==========
    "PooledMCPClient",
    "ResponseCacheLayer",
    "OptimizationFlags",

    # ========== Decorators ==========
    "mcp_test",
    "require_auth",
    "skip_if",
    "timeout",
    "retry",
    "cache_result",
    "TestRegistry",
    "get_test_registry",

    # ========== Reporters ==========
    "TestReporter",
    "ConsoleReporter",
    "JSONReporter",
    "MarkdownReporter",
    "FunctionalityMatrixReporter",
    "DetailedErrorReporter",

    # ========== Cache ==========
    "TestCache",

    # ========== OAuth ==========
    "CachedOAuthClient",
    "create_cached_client",
    "OAuthSessionBroker",
    "OAuthAutomator",
    "create_default_automator",
    "OAuthFlowConfig",
    "FlowStep",
    "FlowResult",
    "flow_config_from_dict",
    "load_flow_config_from_yaml",

    # ========== Adapters (Atoms-specific) ==========
    "AtomsMCPClientAdapter",

    # ========== Runners (Atoms-specific + Unified) ==========
    "AtomsTestRunner",  # NEW: Extends BaseTestRunner
    "TestRunner",       # Alias for backward compatibility
    "LiveTestRunner",
    "AtomsMCPTestRunner",  # Unified runner
    "run_atoms_tests",

    # ========== Patterns ==========
    "ToolTestPattern",
    "UserStoryPattern",
    "IntegrationPattern",

    # ========== Factories ==========
    "TestFactory",
    "TestSuiteFactory",
    "ParameterPermutationFactory",

    # ========== Validators ==========
    "ResponseValidator",
    "FieldValidator",
    "AtomsTestHelpers",  # Atoms-specific helpers

    # ========== Data Generators ==========
    "DataGenerator",

    # ========== Health Checks ==========
    "HealthChecker",

    # ========== Connection Management ==========
    "ConnectionManager",
    "ConnectionState",
    "WaitStrategy",

    # ========== Client Pool ==========
    "WorkerClientPool",
    "ParallelClientManager",

    # ========== Progress Display ==========
    "ComprehensiveProgressDisplay",

    # ========== File Watching ==========
    "TestFileWatcher",
    "SmartReloadManager",

    # ========== Collaboration ==========
    "CollaborationFactory",
    "CollaborationBroadcaster",
    "CollaborationSubscriber",
    "CollaborationEvent",

    # ========== Workflow Manager ==========
    "TestWorkflowManager",

    # ========== TUI ==========
    "run_tui_dashboard",
]
