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
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env files
from dotenv import load_dotenv
load_dotenv()
load_dotenv(".env.local", override=True)


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
        reset_service_config()
    except ImportError:
        pass


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
        
        # Create test result
        duration = report.duration if hasattr(report, 'duration') else 0.0
        result = TestResult(
            name=item.nodeid,
            layer=layer,
            mode=mode,
            outcome=report.outcome,
            duration=duration
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
            
            # Attach to report
            report.error_category = category
            report.error_reason = reason
            report.error_icon = ErrorClassifier.get_icon(category)
            
            # Add to error report
            error_report.add_error(
                test_name=item.nodeid,
                exception=exception,
                category=category,
                reason=reason
            )
            
            matrix_collector.add_error(category.name, item.nodeid)


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
    except Exception:
        pass
    
    # 4. Architect view
    architect_view = ArchitectView(matrix_collector).render()
    terminalreporter.write("\n" + architect_view + "\n")
    
    # 5. Epic view (detailed user stories)
    epic_view_detailed = EpicView(matrix_collector).render()
    terminalreporter.write("\n" + epic_view_detailed + "\n")
    
    # Epic view (compact summary)
    epic_view_compact = EpicView(matrix_collector).render_compact()
    terminalreporter.write("\n" + epic_view_compact + "\n")
    
    # 6. PM view
    pm_view = PMView(matrix_collector).render()
    terminalreporter.write("\n" + pm_view + "\n")
    
    # Save all reports
    try:
        import os
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
            f"\n📊 Reports saved to {reports_dir}/\n"
        )
    except Exception as e:
        terminalreporter.write(f"\n⚠️  Could not save reports: {e}\n")
