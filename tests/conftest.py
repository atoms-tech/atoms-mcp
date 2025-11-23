"""Canonical pytest configuration - Unified and enhanced.

This is the single source of truth for pytest configuration.
Merges:
- Basic test configuration and markers
- Enhanced reporting (error classification, matrix views, epic views)
- Coverage integration
- Performance warnings

All test infrastructure hooks are defined here.
"""

import os
import sys
import time
import pytest
import pytest_asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env files
from dotenv import load_dotenv
load_dotenv()
load_dotenv(".env.local", override=True)


# ============================================================================
# GLOBAL AUTHKIT TOKEN COLLECTION (Runs before all tests)
# ============================================================================

def pytest_sessionstart(session):
    """Collect AuthKit token globally before any tests run.
    
    This hook runs once at the start of the test session and ensures
    an AuthKit access token is available for all tests.
    
    Checks in order:
    1. OS keychain (most secure, persistent)
    2. Environment variables (ATOMS_TEST_AUTH_TOKEN, AUTHKIT_TOKEN)
    3. Auto-collect via Playwright if credentials are available
    """
    import os
    import asyncio
    import logging
    import sys
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    # Try to get token from keychain or environment first
    try:
        # Add scripts directory to path for imports
        scripts_dir = Path(__file__).parent.parent / "scripts"
        sys.path.insert(0, str(scripts_dir))
        
        from authkit_token_cache import get_token
        
        # get_token() automatically handles expiration and refresh
        token = get_token()
        if token:
            # Cache in environment for this session
            os.environ["ATOMS_TEST_AUTH_TOKEN"] = token
            logger.info("✅ AuthKit token available (from keychain or environment, refreshed if needed)")
            print("✅ AuthKit token found and cached for test session (auto-refreshed if expired)")
            return
    except ImportError:
        # Fall back to direct environment check
        if os.getenv("ATOMS_TEST_AUTH_TOKEN") or os.getenv("AUTHKIT_TOKEN"):
            token = os.getenv("ATOMS_TEST_AUTH_TOKEN") or os.getenv("AUTHKIT_TOKEN")
            # Validate it's a real JWT
            if len(token) >= 100 and token.count(".") >= 2:
                logger.info("✅ AuthKit token already available in environment")
                return
    except Exception as e:
        logger.debug(f"Token cache check failed: {e}")
    
    # Check if we have WorkOS credentials for auto-collection
    workos_api_key = os.getenv("WORKOS_API_KEY")
    workos_client_id = os.getenv("WORKOS_CLIENT_ID")
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
    base_url = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL")
    
    if not (workos_api_key and workos_client_id and authkit_domain and base_url):
        logger.info("⚠️  WorkOS credentials not fully configured - token collection skipped")
        logger.info("   Tests will attempt to collect tokens individually if needed")
        return
    
    # Try to collect token automatically using WorkOS User Management
    logger.info("🔄 Auto-collecting AuthKit token before test session via WorkOS...")
    try:
        from tests.utils.workos_auth import authenticate_with_workos

        email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
        password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")

        # Run WorkOS authentication
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            token = loop.run_until_complete(authenticate_with_workos(email, password))
            if token:
                # Cache in environment for this session
                os.environ["ATOMS_TEST_AUTH_TOKEN"] = token
                logger.info("✅ Successfully collected AuthKit token for test session via WorkOS")
                print("✅ AuthKit token collected via WorkOS and cached for all tests")
            else:
                logger.warning("⚠️  WorkOS token collection returned None")
        finally:
            loop.close()
    except ImportError as e:
        logger.debug(f"WorkOS auth module not available: {e}")
    except Exception as e:
        logger.warning(f"Global token collection failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Register custom markers and configure pytest-asyncio."""
    # Try to configure asyncio mode early
    try:
        import pytest_asyncio
        pytest_asyncio.asyncio_mode = "auto"
    except (ImportError, AttributeError):
        pass

    # Register custom markers
    # Core test categories
    config.addinivalue_line(
        "markers", "unit: marks tests that use in-memory client (fast, deterministic)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests that call MCP via HTTP"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests that require full system setup"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that interact with database"
    )

    # Feature categories
    config.addinivalue_line(
        "markers", "entity: tests related to entity operations"
    )
    config.addinivalue_line(
        "markers", "workflow: tests related to workflow execution"
    )
    config.addinivalue_line(
        "markers", "relationship: tests related to relationship operations"
    )

    # Execution modes
    config.addinivalue_line(
        "markers", "slow: tests that take > 1 second to run"
    )
    config.addinivalue_line(
        "markers", "mock_only: tests that use mocks instead of real services"
    )

    # Service requirements
    config.addinivalue_line(
        "markers", "requires_db: tests that need database connection"
    )
    config.addinivalue_line(
        "markers", "requires_auth: tests that need authentication"
    )

    # Specialized tests
    config.addinivalue_line(
        "markers", "performance: performance and load tests"
    )
    config.addinivalue_line(
        "markers", "security: security-focused tests"
    )
    config.addinivalue_line(
        "markers", "error_handling: error condition and edge case tests"
    )

    # Register asyncio mark for pytest-asyncio
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async (pytest-asyncio)"
    )
    
    # Enhanced test infrastructure markers
    config.addinivalue_line(
        "markers", "dependency: marks test dependencies (pytest-dependency)"
    )
    config.addinivalue_line(
        "markers", "order: controls test execution order (pytest-order)"
    )


# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def check_server_running():
    """Check if MCP server is running on localhost:8000."""
    import httpx

    try:
        response = httpx.get("http://127.0.0.1:8000/health", timeout=2.0)
        if response.status_code == 200:
            return True
    except Exception:
        pass

    pytest.skip("MCP server not running on http://127.0.0.1:8000")


@pytest.fixture(scope="function")
def timing_tracker():
    """Track execution time for test reporting."""
    class TimingTracker:
        def __init__(self):
            self.start_time = 0.0
            self.timings = {}

        def start(self, name: str):
            """Start timing an operation."""
            self.start_time = time.perf_counter()
            self.current_name = name

        def stop(self) -> float:
            """Stop timing and return elapsed time in ms."""
            elapsed = time.perf_counter() - self.start_time
            if self.current_name in self.timings:
                self.timings[self.current_name].append(elapsed * 1000)
            else:
                self.timings[self.current_name] = [elapsed * 1000]
            return elapsed * 1000

        def report(self):
            """Return timing report."""
            return {
                name: {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times)
                }
                for name, times in self.timings.items()
            }

    return TimingTracker()


@pytest.fixture(scope="session")
def shared_supabase_jwt():
    """Get Supabase JWT once and reuse to avoid rate limits."""
    from supabase import create_client

    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        pytest.skip("Supabase not configured")

    client = create_client(url, key)

    try:
        auth_response = client.auth.sign_in_with_password({
            "email": "kooshapari@kooshapari.com",
            "password": "118118"
        })

        if auth_response.session:
            return auth_response.session.access_token
    except Exception as e:
        pytest.skip(f"Could not authenticate: {e}")

    pytest.skip("No session obtained")


@pytest.fixture(autouse=True)
def force_all_mock_mode(monkeypatch):
    """Force all services to use mock implementations by default."""
    monkeypatch.setenv("ATOMS_SERVICE_MODE", "mock")
    try:
        from infrastructure.mock_config import reset_service_config
        from infrastructure.factory import reset_factory
        reset_service_config()
        reset_factory()
    except ImportError:
        pass


# ============================================================================
# E2E AUTHENTICATION FIXTURES (from e2e/conftest.py)
# ============================================================================

@pytest_asyncio.fixture(scope="session")
async def authkit_auth_token():
    """Get a valid WorkOS JWT token for E2E tests with auto-refresh.

    CRITICAL: Using session scope with smart token refresh to prevent token expiry.
    The token manager automatically refreshes tokens when they're about to expire,
    ensuring all tests in the session have valid authentication.

    Strategy:
    1. Check for pre-obtained token (fastest)
    2. Use smart token manager (caches + auto-refreshes)
    3. Authenticate fresh if needed

    All environments (local, dev, prod) use real WorkOS authentication.
    The same WorkOS keys are used for all environments (from .env).

    Returns:
        Valid WorkOS JWT token for authenticated API calls

    Raises:
        pytest.skip: If no token can be obtained (tests will be skipped)
    """
    import os
    import logging
    logger_local = logging.getLogger(__name__)

    # Check for pre-obtained token first (fastest)
    pre_obtained_token = os.getenv("ATOMS_TEST_AUTH_TOKEN") or os.getenv("AUTHKIT_TOKEN")
    if pre_obtained_token:
        logger_local.info("✅ Using pre-obtained token from environment")
        return pre_obtained_token

    # Use smart token manager for auto-refresh
    from tests.utils.token_manager import get_fresh_token

    email = os.getenv("WORKOS_TEST_EMAIL")
    password = os.getenv("WORKOS_TEST_PASSWORD")

    if not email or not password:
        logger_local.warning(
            "⚠️  WORKOS_TEST_EMAIL and WORKOS_TEST_PASSWORD not set - "
            "e2e tests will be skipped"
        )
        import pytest
        pytest.skip("WorkOS credentials not configured for e2e tests")

    logger_local.info(f"🔐 Authenticating with WorkOS as {email}")
    token = await get_fresh_token(email, password)

    if token:
        logger_local.info("✅ Successfully obtained real WorkOS JWT token (session scope with auto-refresh)")
        return token
    else:
        error_msg = (
            f"❌ Failed to obtain WorkOS JWT token.\n"
            f"Ensure WORKOS_API_KEY and WORKOS_CLIENT_ID are set in .env"
        )
        logger_local.error(error_msg)
        import pytest
        pytest.skip(error_msg)


@pytest_asyncio.fixture
async def e2e_auth_token(authkit_auth_token):
    """Generate authentication token for E2E tests.

    REQUIRED: All tests must use real AuthKit access tokens - no static
    or test tokens allowed.

    Provides a valid AuthKit JWT bearer token that the MCP server will accept.
    The token MUST be a real AuthKit JWT obtained via WorkOS User Management API.

    Note: This fixture can make external service calls to AuthKit when
    authenticating with real credentials. If no AuthKit token is available,
    tests will be skipped.
    """
    import logging

    logger_local = logging.getLogger(__name__)

    # Use real AuthKit JWT from cloud authentication (REQUIRED)
    # All tests MUST use real AuthKit access tokens
    if authkit_auth_token is not None:
        logger_local.info(f"✅ Using real AuthKit JWT for E2E authentication")
        return authkit_auth_token

    # No AuthKit token available - tests REQUIRE real tokens
    error_msg = (
        "❌ No AuthKit access token available. "
        "Tests require real AuthKit JWTs - no static or test tokens allowed.\n"
    )
    logger_local.error(error_msg)
    import pytest
    pytest.skip(error_msg)





# ============================================================================
# ENHANCED TEST INFRASTRUCTURE - ERROR CLASSIFICATION & VISUALIZATION
# ============================================================================

# Import enhanced infrastructure components
try:
    from tests.framework.error_classifier import ErrorClassifier, ErrorReport
    from tests.framework.matrix_views import (
        MatrixCollector,
        ArchitectView,
        PMView,
        TestResult,
        extract_layer_from_path,
        extract_mode_from_markers,
    )
    from tests.framework.epic_view import EpicView
    from tests.framework.warning_analyzer import WarningAnalyzer

    # Global collectors
    error_report = ErrorReport()
    matrix_collector = MatrixCollector()
    warning_analyzer = WarningAnalyzer()

    ENHANCED_INFRASTRUCTURE_AVAILABLE = True

except ImportError as e:
    import warnings
    warnings.warn(f"Enhanced test infrastructure not loaded: {e}")
    ENHANCED_INFRASTRUCTURE_AVAILABLE = False


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to classify errors and collect results.
    
    Runs after each test and:
    1. Classifies failures by category (INFRA, PRODUCT, etc.)
    2. Collects results for matrix visualization
    3. Analyzes performance warnings
    4. Extracts user story information from @pytest.mark.story
    """
    outcome = yield
    report = outcome.get_result()
    
    if not ENHANCED_INFRASTRUCTURE_AVAILABLE:
        return
    
    # Only process call phase (actual test execution)
    if report.when == "call":
        # Extract layer and mode
        layer = extract_layer_from_path(item.nodeid)
        mode = extract_mode_from_markers(item.own_markers)
        
        # Extract user story from @pytest.mark.story decorator
        story = None
        for marker in item.own_markers:
            if marker.name == "story":
                # marker.args[0] contains the story string
                if marker.args:
                    story = marker.args[0]
                break
        
        # Create test result
        duration = report.duration if hasattr(report, 'duration') else 0.0
        result = TestResult(
            name=item.nodeid,
            layer=layer,
            mode=mode,
            outcome=report.outcome,
            duration=duration,
            story=story
        )
        matrix_collector.add_result(result)
        
        # Analyze for warnings
        warnings = warning_analyzer.analyze_test_result(
            item.nodeid, 
            duration, 
            report.outcome
        )
        for warning in warnings:
            warning_analyzer.add_warning(warning)
        
        # Classify errors
        if report.failed and hasattr(call, 'excinfo') and call.excinfo:
            exception = call.excinfo.value
            
            category, reason = ErrorClassifier.classify(exception)
            
            # Attach to report (ensure category is string for serialization)
            report.error_category = str(category.value) if hasattr(category, 'value') else str(category)
            report.error_reason = reason
            report.error_icon = ErrorClassifier.get_icon(category)
            
            # Add to error report
            error_report.add_error(
                test_name=item.nodeid,
                exception=exception,
                category=category,
                reason=reason
            )
            
            # Ensure category.name is string for serialization
            cat_name = category.name if hasattr(category, 'name') else str(category)
            matrix_collector.add_error(cat_name, item.nodeid)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Generate enhanced summary after all tests.
    
    Shows:
    1. Error classification report (INFRA vs PRODUCT)
    2. Warning & performance analysis (slow tests, flaky tests)
    3. Code coverage summary
    4. Architect view matrix (system health)
    5. Epic view (48 user stories across 11 epics)
    6. PM view (feature area tracking)
    
    All reports are saved to tests/reports/
    """
    if not ENHANCED_INFRASTRUCTURE_AVAILABLE:
        return
    
    # 1. Error classification report
    error_summary = error_report.generate_summary()
    terminalreporter.write(error_summary)
    
    # 2. Warning analysis
    warning_summary = warning_analyzer.generate_report()
    terminalreporter.write(warning_summary)
    
    # 3. Code coverage summary (if available)
    try:
        import json
        from pathlib import Path
        coverage_file = Path("coverage.json")
        if coverage_file.exists():
            with open(coverage_file) as f:
                cov_data = json.load(f)
                total_pct = cov_data.get("totals", {}).get("percent_covered", 0)
                
                terminalreporter.write("\n" + "="*70 + "\n")
                terminalreporter.write("📊 CODE COVERAGE SUMMARY\n")
                terminalreporter.write("="*70 + "\n")
                terminalreporter.write(f"Overall Coverage: {total_pct:.1f}%\n")
                
                if total_pct >= 80:
                    terminalreporter.write("Status: ✅ Excellent (≥80%)\n")
                elif total_pct >= 60:
                    terminalreporter.write("Status: ✓ Good (60-79%)\n")
                elif total_pct >= 40:
                    terminalreporter.write("Status: ⚠️  Fair (40-59%)\n")
                else:
                    terminalreporter.write("Status: ❌ Needs Improvement (<40%)\n")
                
                terminalreporter.write("="*70 + "\n")
                
                # Calculate coverage by layer from coverage.json
                layer_paths = {
                    "tools": "tools/",
                    "infrastructure": "infrastructure/",
                    "services": "services/",
                    "auth": "auth/",
                }
                
                for layer, path_prefix in layer_paths.items():
                    layer_files = cov_data.get("files", {})
                    layer_coverage = []
                    
                    for file_path, file_data in layer_files.items():
                        if path_prefix in file_path or f"/{path_prefix}" in file_path:
                            coverage_pct = file_data.get("summary", {}).get("percent_covered", 0)
                            layer_coverage.append(coverage_pct)
                    
                    # Calculate average coverage for layer
                    avg_coverage = (sum(layer_coverage) / len(layer_coverage)) if layer_coverage else total_pct
                    matrix_collector.set_coverage(layer, avg_coverage)
    except Exception as e:
        # Silently handle coverage errors - not critical for test reporting
        pass
    
    summary_mode = os.getenv("ATOMS_TEST_SUMMARY_MODE", "minimal").lower()
    verbose_reports = summary_mode == "full"

    # 4-6. Matrix views
    architect_view = ArchitectView(matrix_collector).render()
    epic_view_detailed = EpicView(matrix_collector).render()
    epic_view_compact = EpicView(matrix_collector).render_compact()
    pm_view = PMView(matrix_collector).render()

    if verbose_reports:
        terminalreporter.write("\n" + architect_view + "\n")
        terminalreporter.write("\n" + epic_view_detailed + "\n")
        terminalreporter.write("\n" + epic_view_compact + "\n")
        terminalreporter.write("\n" + pm_view + "\n")
    else:
        terminalreporter.write(
            "\nℹ️  Detailed matrix reports suppressed. Set ATOMS_TEST_SUMMARY_MODE=full to display them.\n"
        )
    
    # Save all reports
    try:
        reports_dir = "tests/reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        with open(f"{reports_dir}/architect_view.txt", "w") as f:
            f.write(architect_view)
        
        with open(f"{reports_dir}/epic_view.txt", "w") as f:
            f.write(epic_view_detailed)
        
        with open(f"{reports_dir}/epic_summary.txt", "w") as f:
            f.write(epic_view_compact)
        
        with open(f"{reports_dir}/pm_view.txt", "w") as f:
            f.write(pm_view)
        
        with open(f"{reports_dir}/error_classification.txt", "w") as f:
            f.write(error_summary)
        
        with open(f"{reports_dir}/warnings.txt", "w") as f:
            f.write(warning_summary)
        
        terminalreporter.write(
            f"\n📊 Reports saved to {reports_dir}/" \
            " (set ATOMS_TEST_SUMMARY_MODE=full to print).\n"
        )
    except Exception as e:
        terminalreporter.write(f"\n⚠️  Could not save reports: {e}\n")
