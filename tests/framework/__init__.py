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
        # Decorators & Registry
        TestRegistry,
        get_test_registry,
        mcp_test,
        require_auth,
        retry,
        skip_if,
        timeout,
        cache_result,
        # Reporters
        ConsoleReporter,
        DetailedErrorReporter,
        FunctionalityMatrixReporter,
        JSONReporter,
        MarkdownReporter,
        TestReporter,
        # Cache
        TestCache,
        # Data & Validators
        DataGenerator,
        # Progress
        ComprehensiveProgressDisplay,
        # Parallel Execution
        WorkerClientPool,
        ParallelClientManager,
        ConnectionManager,
        ConnectionState,
        WaitStrategy,
        # Health
        HealthChecker,
    )
    
    # Base patterns (NEW!)
    from mcp_qa.core.base import (
        BaseClientAdapter,
        BaseTestRunner,
    )
    
    # Optimizations (NEW - with fixed PooledMCPClient!)
    from mcp_qa.core.optimizations import (
        PooledMCPClient,
        ResponseCacheLayer,
        OptimizationFlags,
    )
    
    HAS_MCP_QA = True
    
except ImportError as e:
    print(f"⚠️  Warning: Could not import from mcp-qa: {e}")
    print("   Falling back to local implementations")

    # Fallback to local imports if mcp-QA not installed
    from .cache import TestCache
    from .client_pool import WorkerClientPool
    from .connection_manager import ConnectionManager, ConnectionState, WaitStrategy
    from .data_generators import DataGenerator
    from .health_checks import HealthChecker

    # These have been consolidated to mcp_qa - no local fallback
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
from .patterns import IntegrationPattern, ToolTestPattern, UserStoryPattern
from .validators import FieldValidator, ResponseValidator

# Optional components (may not exist in all installations)
try:
    from .factories import ParameterPermutationFactory, TestFactory, TestSuiteFactory
except ImportError:
    ParameterPermutationFactory = None
    TestFactory = None
    TestSuiteFactory = None

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
