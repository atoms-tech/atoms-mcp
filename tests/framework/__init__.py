"""
Atoms MCP Test Framework

A robust, modular test framework for Atoms MCP server.
Most components are now imported from pheno.testing.mcp_qa.core for consistency.

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
    from pheno.mcp.qa.core import (
        # Available components
        BaseClientAdapter,
        BaseTestRunner,
        MCPClientAdapter,
        TestRegistry,
        TestRunner,
        get_test_registry,
        mcp_test,
    )
    
    # Set missing components to None for now
    ComprehensiveProgressDisplay = None
    ConnectionManager = None
    ConnectionState = None
    ConsoleReporter = None
    DataGenerator = None
    DetailedErrorReporter = None
    FunctionalityMatrixReporter = None
    HealthChecker = None
    JSONReporter = None
    MarkdownReporter = None
    ParallelClientManager = None
    TestCache = None
    TestReporter = None
    WaitStrategy = None
    WorkerClientPool = None
    cache_result = None
    require_auth = None
    retry = None
    skip_if = None
    timeout = None

    # Base patterns (NEW!) - already imported above
    # BaseClientAdapter and BaseTestRunner are already imported

    # Optimizations (NEW - with fixed PooledMCPClient!)
    # Set to None for now as these modules may not exist
    OptimizationFlags = None
    PooledMCPClient = None
    ResponseCacheLayer = None

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
    # Try to import from pheno.mcp.qa.core
    from pheno.mcp.qa.core import (
        ParameterPermutationFactory, 
        TestFactory, 
        TestSuiteFactory,
        IntegrationPattern, 
        ToolTestPattern, 
        UserStoryPattern,
        FieldValidator, 
        ResponseValidator
    )
except ImportError:
    # Fallback to local implementations
    print("⚠️  Warning: pheno.mcp.qa.core not available, using local implementations")
    from .validators import FieldValidator, ResponseValidator
    IntegrationPattern = None
    ToolTestPattern = None
    UserStoryPattern = None
    ParameterPermutationFactory = None
    TestFactory = None
    TestSuiteFactory = None

# Import Atoms-specific helpers
from .atoms_helpers import AtomsTestHelpers  # noqa: E402

# ============================================================================
# Phase 2 Test Infrastructure (NEW!)
# ============================================================================

# @harmful decorator for automatic test state tracking
try:
    from .harmful import (
        CleanupStrategy,
        Entity,
        EntityType,
        HarmfulStateTracker,
        TestDataTracker,
        TestHarmfulState,
        create_and_track,
        harmful,
        harmful_context,
    )
except ImportError:
    # Set to None to avoid redefinition errors
    Entity = None  # type: ignore
    EntityType = None  # type: ignore
    HarmfulStateTracker = None  # type: ignore
    TestDataTracker = None  # type: ignore
    TestHarmfulState = None
    # CleanupStrategy is imported from harmful module, don't override
    create_and_track = None
    harmful = None
    harmful_context = None

# Test modes framework
try:
    from .test_modes import (
        ConditionalFixture,
        TestMode,
        TestModeConfig,
        TestModeDetector,
        TestModeManager,
        TestModeValidator,
        get_mode_manager,
        get_test_mode,
        get_test_mode_config,
        set_test_mode,
    )
except ImportError:
    ConditionalFixture = None
    TestMode = None
    TestModeConfig = None
    TestModeDetector = None
    TestModeManager = None
    TestModeValidator = None
    get_mode_manager = None
    get_test_mode = None
    get_test_mode_config = None
    set_test_mode = None

# Test mode conditional fixtures
try:
    from .fixtures import (
        conditional_auth_manager,
        conditional_database,
        conditional_event_loop,
        conditional_http_client,
        conditional_mcp_client,
        conditional_temp_directory,
        create_mock_mcp_client,
        create_real_mcp_client,
        create_simulated_mcp_client,
    )
except ImportError:
    conditional_auth_manager = None
    conditional_database = None
    conditional_event_loop = None
    conditional_http_client = None
    conditional_mcp_client = None
    conditional_temp_directory = None
    create_mock_mcp_client = None
    create_real_mcp_client = None
    create_simulated_mcp_client = None

# Cascade flow patterns for test dependency ordering
try:
    from .dependencies import (
        FlowPattern,
        FlowTestGenerator,
        FlowVisualizer,
        TestResult,
        TestResultRegistry,
        cascade_flow,
        depends_on,
        flow_stage,
        get_result_registry,
        store_result,
        test_results,
    )
except ImportError:
    FlowPattern = None
    FlowTestGenerator = None
    FlowVisualizer = None
    TestResult = None
    TestResultRegistry = None
    cascade_flow = None
    depends_on = None
    flow_stage = None
    get_result_registry = None
    store_result = None
    test_results = None

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
    AtomsMCPTestRunner = None  # type: ignore
    run_atoms_tests = None  # type: ignore

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

    # ========== Phase 2 Test Infrastructure (NEW!) ==========
    # @harmful decorator for automatic test state tracking
    "harmful",
    "harmful_context",
    "create_and_track",
    "HarmfulStateTracker",
    "TestHarmfulState",
    "Entity",
    "EntityType",
    "CleanupStrategy",
    "TestDataTracker",

    # Test modes framework
    "TestMode",
    "TestModeConfig",
    "TestModeDetector",
    "TestModeValidator",
    "TestModeManager",
    "ConditionalFixture",
    "get_mode_manager",
    "set_test_mode",
    "get_test_mode",
    "get_test_mode_config",

    # Test mode conditional fixtures
    "conditional_mcp_client",
    "conditional_http_client",
    "conditional_database",
    "conditional_auth_manager",
    "conditional_temp_directory",
    "conditional_event_loop",
    "create_real_mcp_client",
    "create_mock_mcp_client",
    "create_simulated_mcp_client",

    # Cascade flow patterns for test dependency ordering
    "FlowPattern",
    "TestResult",
    "TestResultRegistry",
    "depends_on",
    "flow_stage",
    "cascade_flow",
    "FlowVisualizer",
    "FlowTestGenerator",
    "get_result_registry",
    "test_results",
    "store_result",
]
