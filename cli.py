"""Atoms MCP CLI - Enhanced command-line interface with npm-like commands.

This module provides comprehensive CLI commands for development, testing, and deployment.

Commands (like npm scripts):
  atoms run          - Start the MCP server
  atoms dev          - Start in development mode with hot reload
  atoms test         - Run test suite
  atoms test:unit    - Run unit tests only
  atoms test:int     - Run integration tests
  atoms test:e2e     - Run end-to-end tests
  atoms test:cov     - Run tests with coverage report
  atoms test:rls     - Run Row-Level Security tests
  atoms test:story   - Run tests by user story mapping
  atoms test:comprehensive - Run comprehensive integration & e2e tests (100% coverage)
  atoms test:integration-full - Run all 61 integration tests
  atoms test:e2e-full - Run all 61 e2e tests
  atoms test:live    - Run live service tests with your credentials
  atoms lint         - Check code with ruff
  atoms format       - Auto-format code with black
  atoms type-check   - Check types with mypy
  atoms health       - Check server health
  atoms build        - Build for production
  atoms update       - Update dependencies interactively
  atoms version      - Show version info
  atoms clean        - Clean cache and build artifacts
  atoms deps         - Analyze dependencies
  atoms docs         - Generate/view documentation
  atoms logs         - Tail server logs
  atoms db:regen-types - Regenerate Supabase type definitions
"""

import sys
import typer
import subprocess
from typing import Optional
from pathlib import Path

app = typer.Typer(
    name="atoms",
    help="Atoms MCP Server - Development CLI",
    pretty_exceptions_show_locals=False,
)


# ============================================================================
# Server Commands
# ============================================================================

@app.command()
def run(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to run on"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
    http: bool = typer.Option(False, help="Use HTTP transport instead of stdio"),
) -> None:
    """Start the Atoms MCP Server.
    
    Example:
        atoms run --port 8001 --debug
        atoms run --http  # Start with HTTP transport for E2E testing
    """
    import os
    if debug:
        os.environ["DEBUG"] = "true"
    
    if http:
        os.environ["ATOMS_FASTMCP_TRANSPORT"] = "http"
        os.environ["ATOMS_FASTMCP_HOST"] = host
        os.environ["ATOMS_FASTMCP_PORT"] = str(port)
        os.environ["ATOMS_FASTMCP_HTTP_PATH"] = "/api/mcp"
        print(f"🚀 Starting Atoms MCP Server (HTTP) on {host}:{port}/api/mcp")
    else:
        print(f"🚀 Starting Atoms MCP Server (stdio) on {host}:{port}")
    
    if debug:
        print("🔧 Debug mode enabled")
    
    from server import main
    main()


@app.command()
def dev(
    port: int = typer.Option(8000, help="Port to run on"),
) -> None:
    """Start in development mode using Vercel dev server.
    
    Features:
    - Uses Vercel dev server for local development
    - Auto-reloads on file changes
    - Shows detailed error messages
    - Enables all debug logging
    
    Example:
        atoms dev --port 8001
    """
    import os
    import subprocess
    import sys
    
    os.environ["DEBUG"] = "true"
    
    print("⚙️  Starting in development mode with Vercel...")
    print(f"🔄 Vercel dev server will handle auto-reload")
    print("📝 Watching for file changes...")
    
    # Check if vercel is installed
    try:
        result = subprocess.run(
            ["vercel", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Vercel CLI found: {result.stdout.strip()}")
        
        # Run vercel dev
        print("🚀 Starting Vercel dev server...")
        print(f"🌐 Server will be available at http://localhost:{port}")
        # Vercel dev uses --listen flag with port only (not host:port)
        subprocess.run(
            ["vercel", "dev", "--listen", str(port)],
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Vercel CLI not found. Install with: npm i -g vercel")
        print("   Falling back to uvicorn...")
        try:
            import uvicorn
            uvicorn.run(
                "app:app",
                host="0.0.0.0",
                port=port,
                reload=True,
                log_level="debug"
            )
        except ImportError:
            print("❌ uvicorn not installed. Using standard server...")
            from server import main
            main()


@app.command()
def health() -> None:
    """Check if the server is running and healthy."""
    try:
        import httpx
        client = httpx.Client(timeout=5.0)
        response = client.get("http://localhost:8000/health", timeout=5.0)
        
        if response.status_code == 200:
            print("✅ Server is healthy")
            sys.exit(0)
        else:
            print(f"⚠️  Server returned: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Server is not responding: {e}")
        sys.exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    print("Atoms MCP Server v0.1.0")
    print("FastMCP-based consolidated MCP server")


# ============================================================================
# Testing Commands
# ============================================================================

@app.command()
def test(
    scope: Optional[str] = typer.Option(None, "--scope", help="Test scope: unit, integration, or e2e (if omitted, runs all tests)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
    coverage: bool = typer.Option(False, "--cov", help="Generate coverage report"),
    marker: Optional[str] = typer.Option(None, "-m", "--marker", help="Run specific marker (e.g., 'unit', 'story')"),
    keyword: Optional[str] = typer.Option(None, "-k", "--keyword", help="Run tests matching keyword"),
    env: Optional[str] = typer.Option(None, "--env", help="Environment: local, dev, or prod (auto-detected if not specified)"),
    parallel: bool = typer.Option(False, "--parallel", help="Run dependency-ordered stages with pytest-xdist"),
    max_workers: Optional[int] = typer.Option(None, "--max-workers", help="Override pytest-xdist worker count (default: auto)"),
) -> None:
    """Run the test suite with automatic environment targeting.
    
    The CLI automatically targets the correct environment:
    - no scope → all tests (local)
    - --scope unit → unit tests (local, no deployment needed)
    - --scope integration → integration tests (dev by default, or local)
    - --scope e2e → e2e tests (dev by default, or prod)
    
    Examples:
        atoms test                          # Run all tests (local)
        atoms test --scope unit             # Unit tests only (local)
        atoms test --scope integration      # Integration tests (dev: mcpdev.atoms.tech)
        atoms test --scope e2e              # E2E tests (dev: mcpdev.atoms.tech)
        atoms test --scope e2e --env prod   # E2E tests against production
        atoms test --scope unit -v          # Verbose unit tests
        atoms test --scope integration --env local  # Integration against local server
        atoms test -v --cov                 # All tests with coverage and verbose
    """
    from cli_modules.test_env_manager import TestEnvManager, TestEnvironment
    
    # Determine environment
    if env:
        try:
            environment = TestEnvironment(env.lower())
        except ValueError:
            print(f"❌ Invalid environment: {env}. Use: local, dev, or prod")
            sys.exit(1)
    else:
        # Auto-detect based on scope (if provided)
        # If no scope, default to local for all tests
        if scope:
            environment = TestEnvManager.get_environment_for_scope(scope)
        else:
            environment = TestEnvironment.LOCAL
    
    # Set up environment variables
    TestEnvManager.setup_environment(environment)
    
    # Print environment info
    TestEnvManager.print_environment_info(environment)
    
    if parallel:
        if scope:
            print("⚠️ --parallel runs the full suite. Remove --scope to continue.")
            sys.exit(1)
        if max_workers is not None and max_workers < 1:
            print("⚠️ --max-workers must be >= 1")
            sys.exit(1)

        from cli_modules.test_orchestrator import TestOrchestrator

        orchestrator = TestOrchestrator(
            verbose=verbose,
            marker=marker,
            keyword=keyword,
            parallel=True,
            max_workers=max_workers,
            coverage=coverage,
        )
        summary = orchestrator.run()
        sys.exit(0 if summary.success else 1)

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])

    # Add marker based on explicit scope or marker option (not default)
    if marker:
        cmd.extend(["-m", marker])
    elif scope and scope in ["unit", "integration", "e2e"]:
        # Only add marker if scope was explicitly provided
        cmd.extend(["-m", scope])

    if keyword:
        cmd.extend(["-k", keyword])

    # Add test path
    cmd.append("tests/")

    print(f"\n🧪 Running tests: {' '.join(cmd[3:])}\n")
    result = subprocess.run(cmd)

    # Exit with test result code
    sys.exit(result.returncode)


@app.command("test:unit")
def test_unit(
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Run unit tests only (fast, no external services).
    
    Always uses local environment (no deployment needed).
    
    Example:
        atoms test:unit -v
    """
    from cli_modules.test_env_manager import TestEnvManager, TestEnvironment
    
    # Unit tests always use local
    environment = TestEnvironment.LOCAL
    TestEnvManager.setup_environment(environment)
    
    cmd = ["python", "-m", "pytest", "-m", "unit", "tests/"]
    if verbose:
        cmd.insert(-1, "-v")
    
    print("🧪 Running unit tests (local)...")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@app.command("test:int")
def test_integration(
    verbose: bool = typer.Option(False, "-v", "--verbose"),
    env: Optional[str] = typer.Option(None, "--env", help="Environment: local, dev, or prod"),
) -> None:
    """Run integration tests (requires services).
    
    Automatically targets dev deployment (mcpdev.atoms.tech) by default.
    Override with --env local to use local server or --env prod for production.
    
    Examples:
        atoms test:int                  # Integration tests on dev
        atoms test:int -v               # Verbose
        atoms test:int --env local      # Against local server
        atoms test:int --env prod       # Against production
    """
    from cli_modules.test_env_manager import TestEnvManager, TestEnvironment
    
    # Determine environment
    if env:
        try:
            environment = TestEnvironment(env.lower())
        except ValueError:
            print(f"❌ Invalid environment: {env}. Use: local, dev, or prod")
            sys.exit(1)
    else:
        # Default to dev for integration tests
        environment = TestEnvironment.DEV
    
    TestEnvManager.setup_environment(environment)
    TestEnvManager.print_environment_info(environment)
    
    cmd = ["python", "-m", "pytest", "-m", "integration", "tests/"]
    if verbose:
        cmd.insert(-1, "-v")
    
    print()
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@app.command("test:e2e")
def test_e2e(
    verbose: bool = typer.Option(False, "-v", "--verbose"),
    env: Optional[str] = typer.Option(None, "--env", help="Environment: local, dev, or prod"),
) -> None:
    """Run end-to-end tests (full system).
    
    Automatically targets dev deployment (mcpdev.atoms.tech) by default.
    Override with --env local to use local server or --env prod for production.
    
    Examples:
        atoms test:e2e                  # E2E tests on dev
        atoms test:e2e -v               # Verbose
        atoms test:e2e --env local      # Against local server
        atoms test:e2e --env prod       # Against production
    """
    from cli_modules.test_env_manager import TestEnvManager, TestEnvironment
    
    # Determine environment
    if env:
        try:
            environment = TestEnvironment(env.lower())
        except ValueError:
            print(f"❌ Invalid environment: {env}. Use: local, dev, or prod")
            sys.exit(1)
    else:
        # Default to dev for e2e tests
        environment = TestEnvironment.DEV
    
    TestEnvManager.setup_environment(environment)
    TestEnvManager.print_environment_info(environment)
    
    cmd = ["python", "-m", "pytest", "-m", "e2e", "tests/"]
    if verbose:
        cmd.insert(-1, "-v")
    
    print()
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@app.command("test:cov")
def test_coverage() -> None:
    """Run unit tests with coverage report (HTML + terminal).
    
    Always uses local environment (coverage only for unit tests).
    
    Output:
        htmlcov/index.html - Interactive coverage report
    """
    from cli_modules.test_env_manager import TestEnvManager, TestEnvironment
    
    # Coverage always uses local + unit tests
    environment = TestEnvironment.LOCAL
    TestEnvManager.setup_environment(environment)
    
    print("🧪 Running unit tests with coverage...")
    result = subprocess.run([
        "python", "-m", "pytest",
        "-m", "unit",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "tests/"
    ])
    print("\n📊 Coverage report: htmlcov/index.html")
    sys.exit(result.returncode)


@app.command("test:rls")
def test_rls(
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Run Row-Level Security (RLS) tests.
    
    Tests RLS enforcement across unit, integration, and e2e test suites.
    
    Examples:
        atoms test:rls              # Run all RLS tests
        atoms test:rls -v           # Verbose output
    """
    cmd = [
        "python", "-m", "pytest",
        "tests/unit/security/test_rls_protection.py",
        "tests/integration/test_auth_integration.py::TestRLSEnforcement",
        "tests/e2e/test_security.py",
        "-v" if verbose else "-q",
    ]
    
    print("🔒 Running Row-Level Security (RLS) tests...")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@app.command("test:story")
def test_story(
    epic: Optional[str] = typer.Option(None, "-e", "--epic", help="Filter by epic name"),
) -> None:
    """Run tests by user story mapping.

    Examples:
        atoms test:story                    # All story tests
        atoms test:story -e "Security"      # Security epic tests
        atoms test:story -e "Organization"  # Organization epic tests
    """
    cmd = ["python", "-m", "pytest", "-m", "story"]

    if epic:
        cmd.extend(["-k", epic])

    cmd.append("tests/")

    print(f"🧪 Running story tests: {epic or 'all epics'}")
    subprocess.run(cmd)


@app.command("test:comprehensive")
def test_comprehensive(
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
    service_mode: str = typer.Option("mock", "--mode", help="Service mode: mock or live"),
    email: Optional[str] = typer.Option(None, "--email", help="Test account email (for live mode)"),
    password: Optional[str] = typer.Option(None, "--password", help="Test account password (for live mode)"),
) -> None:
    """Run comprehensive integration and e2e tests (100% coverage).

    Tests both mock and live services with full coverage:
    - 61 integration tests (database, cache, auth, search, relationships)
    - 61 e2e tests (entity, relationship, auth, search workflows)
    - 9 live service tests (with your account credentials)

    Examples:
        atoms test:comprehensive                    # Mock mode (fast, default)
        atoms test:comprehensive -v                 # Verbose output
        atoms test:comprehensive --mode live        # Live mode with credentials
        atoms test:comprehensive --mode live \\
          --email kooshapari@kooshapari.com \\
          --password ASD3on54_Pax90
    """
    import os

    # Set service mode
    os.environ["SERVICE_MODE"] = service_mode

    # Set credentials for live mode
    if service_mode == "live":
        if email:
            os.environ["ATOMS_TEST_EMAIL"] = email
        if password:
            os.environ["ATOMS_TEST_PASSWORD"] = password

        # Use defaults if not provided
        if "ATOMS_TEST_EMAIL" not in os.environ:
            os.environ["ATOMS_TEST_EMAIL"] = "kooshapari@kooshapari.com"
        if "ATOMS_TEST_PASSWORD" not in os.environ:
            os.environ["ATOMS_TEST_PASSWORD"] = "ASD3on54_Pax90"

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Add test files
    cmd.extend([
        "tests/integration/test_comprehensive_coverage.py",
        "tests/e2e/test_comprehensive_e2e.py",
    ])

    # Add live service tests if in live mode
    if service_mode == "live":
        cmd.append("tests/e2e/test_live_services_with_credentials.py")

    # Add coverage if verbose
    if verbose:
        cmd.extend(["--tb=short"])

    print(f"🧪 Running comprehensive tests ({service_mode} mode)...")
    if service_mode == "live":
        print(f"   Email: {os.environ.get('ATOMS_TEST_EMAIL')}")
        print()

    result = subprocess.run(cmd, env=os.environ.copy())
    sys.exit(result.returncode)


@app.command("test:integration-full")
def test_integration_full(
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
) -> None:
    """Run all integration tests (61 tests).

    Comprehensive integration test suite covering:
    - Database operations (10 tests)
    - Cache operations (8 tests)
    - Auth operations (5 tests)
    - Search operations (5 tests)
    - Relationship operations (4 tests)
    - Error handling (4 tests)
    - Integration workflows (3 tests)
    - Relationship operations (4 tests)
    - Error handling (4 tests)
    - Integration workflows (3 tests)

    Examples:
        atoms test:integration-full         # Run all integration tests
        atoms test:integration-full -v      # Verbose output
    """
    import os
    os.environ["SERVICE_MODE"] = "mock"

    cmd = ["python", "-m", "pytest", "tests/integration/test_comprehensive_coverage.py"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    print("🧪 Running all integration tests (61 tests)...")
    result = subprocess.run(cmd, env=os.environ.copy())
    sys.exit(result.returncode)


@app.command("test:e2e-full")
def test_e2e_full(
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
) -> None:
    """Run all e2e tests (61 tests).

    Comprehensive end-to-end test suite covering:
    - Entity management (4 tests)
    - Relationship management (3 tests)
    - Authentication flow (3 tests)
    - Search workflow (3 tests)
    - Error recovery (3 tests)
    - Concurrency (3 tests)
    - Performance (3 tests)

    Examples:
        atoms test:e2e-full         # Run all e2e tests
        atoms test:e2e-full -v      # Verbose output
    """
    import os
    os.environ["SERVICE_MODE"] = "mock"

    cmd = ["python", "-m", "pytest", "tests/e2e/test_comprehensive_e2e.py"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    print("🧪 Running all e2e tests (61 tests)...")
    result = subprocess.run(cmd, env=os.environ.copy())
    sys.exit(result.returncode)


@app.command("test:live")
def test_live(
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
    email: Optional[str] = typer.Option(None, "--email", help="Test account email"),
    password: Optional[str] = typer.Option(None, "--password", help="Test account password"),
) -> None:
    """Run live service tests with your account credentials (9 tests).

    Tests real MCP API endpoints using your account:
    - Authentication (1 test)
    - Entity operations (3 tests)
    - Relationship operations (1 test)
    - User profile (1 test)
    - Workspace management (1 test)
    - Error handling (2 tests)

    Default credentials: kooshapari@kooshapari.com / ASD3on54_Pax90

    Examples:
        atoms test:live                                  # Use default credentials
        atoms test:live -v                               # Verbose output
        atoms test:live --email user@example.com \\
          --password mypassword
    """
    import os

    os.environ["SERVICE_MODE"] = "live"

    # Set credentials
    if email:
        os.environ["ATOMS_TEST_EMAIL"] = email
    else:
        os.environ["ATOMS_TEST_EMAIL"] = "kooshapari@kooshapari.com"

    if password:
        os.environ["ATOMS_TEST_PASSWORD"] = password
    else:
        os.environ["ATOMS_TEST_PASSWORD"] = "ASD3on54_Pax90"

    cmd = ["python", "-m", "pytest", "tests/e2e/test_live_services_with_credentials.py"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    print("🧪 Running live service tests...")
    print(f"   Email: {os.environ['ATOMS_TEST_EMAIL']}")
    print()

    result = subprocess.run(cmd, env=os.environ.copy())
    sys.exit(result.returncode)


# ============================================================================
# Code Quality Commands
# ============================================================================

@app.command()
def lint() -> None:
    """Check code with ruff linter.
    
    Checks for:
    - Syntax errors
    - Unused imports
    - Naming conventions
    - Code complexity
    """
    print("🔍 Linting code with ruff...")
    result = subprocess.run(["ruff", "check", "."])
    if result.returncode == 0:
        print("✅ Linting passed")
    else:
        print("⚠️  Linting found issues")
        sys.exit(1)


@app.command()
def format() -> None:
    """Auto-format code with black.
    
    Formats:
    - Line length to 100 chars
    - Imports with isort
    - Code style to Black standard
    """
    print("🎨 Formatting code with black...")
    
    # Format with black
    subprocess.run(["black", ".", "--line-length=100"])
    
    # Sort imports
    try:
        subprocess.run(["isort", ".", "--line-length=100"])
    except FileNotFoundError:
        pass
    
    print("✅ Code formatted")


@app.command("type-check")
def type_check() -> None:
    """Check types with mypy.
    
    Validates:
    - Type annotations
    - Type consistency
    - Missing return types
    """
    print("📝 Checking types with mypy...")
    result = subprocess.run(["mypy", ".", "--ignore-missing-imports"])
    if result.returncode == 0:
        print("✅ Type checking passed")
    else:
        print("⚠️  Type issues found")
        sys.exit(1)


@app.command("check")
def check_all() -> None:
    """Run all checks: lint, format, type-check.
    
    Runs in order:
    1. Format code
    2. Lint for issues
    3. Type check
    4. Run quick tests
    """
    print("🔍 Running all checks...")
    
    # Format first
    print("\n📝 Formatting...")
    subprocess.run(["black", ".", "--line-length=100"])
    
    # Lint
    print("\n🔍 Linting...")
    lint_result = subprocess.run(["ruff", "check", "."])
    
    # Type check
    print("\n📝 Type checking...")
    type_result = subprocess.run(["mypy", ".", "--ignore-missing-imports"])
    
    if lint_result.returncode == 0 and type_result.returncode == 0:
        print("\n✅ All checks passed!")
    else:
        print("\n⚠️  Some checks failed")
        sys.exit(1)


# ============================================================================
# Dependency Commands
# ============================================================================

@app.command()
def update(
    all: bool = typer.Option(False, "--all", help="Update all dependencies"),
    deps: bool = typer.Option(False, "--deps", help="Production deps only"),
    dev: bool = typer.Option(False, "--dev", help="Dev deps only"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without applying"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
) -> None:
    """Update dependencies (like npm update).
    
    Examples:
        atoms update --all              # Update all deps
        atoms update --deps             # Production only
        atoms update --dev              # Dev only
        atoms update --all --dry-run    # Preview changes
    """
    from cli_update import (
        print_header,
        print_dependency_summary,
        execute_update_with_visualization,
        DependencyAnalyzer,
    )
    
    print_header()
    
    analyzer = DependencyAnalyzer()
    if not analyzer.load_dependencies():
        print("❌ Failed to load dependencies")
        sys.exit(1)
    
    print_dependency_summary(analyzer)
    
    update_deps = []
    if all or (not deps and not dev):
        update_deps = analyzer.prod_deps + analyzer.dev_deps
    elif deps:
        update_deps = analyzer.prod_deps
    elif dev:
        update_deps = analyzer.dev_deps
    
    if not update_deps:
        print("ℹ️  No dependencies to update")
        return
    
    execute_update_with_visualization(update_deps, dry_run=dry_run, verbose=verbose)


@app.command()
def deps() -> None:
    """Analyze project dependencies.
    
    Shows:
    - Dependency count
    - Production vs dev split
    - Lock file status
    - Total size
    """
    from cli_update import DependencyAnalyzer, print_ascii_diagram
    
    print("📦 Analyzing dependencies...\n")
    print_ascii_diagram()
    
    analyzer = DependencyAnalyzer()
    analyzer.load_dependencies()
    
    print(f"\n📊 Dependency Summary:")
    print(f"  Production: {len(analyzer.prod_deps)} packages")
    print(f"  Development: {len(analyzer.dev_deps)} packages")
    print(f"  Total: {len(analyzer.prod_deps) + len(analyzer.dev_deps)} packages")
    
    lock_stats = analyzer.get_lock_file_stats()
    if lock_stats.get("exists"):
        print(f"\n🔒 Lock File:")
        print(f"  Lines: {lock_stats['lines']}")
        print(f"  Size: {lock_stats['size_mb']}MB")


# ============================================================================
# Build & Deployment Commands
# ============================================================================

@app.command()
def build() -> None:
    """Build for production.
    
    Steps:
    1. Run all checks
    2. Run full test suite
    3. Build distribution
    4. Generate documentation
    """
    print("🏗️  Building for production...\n")
    
    # Run checks
    print("1. Running checks...")
    subprocess.run(["black", ".", "--line-length=100"], capture_output=True)
    subprocess.run(["ruff", "check", "."], capture_output=True)
    
    # Run tests
    print("2. Running tests...")
    test_result = subprocess.run(["python", "-m", "pytest", "tests/", "-q"])
    
    if test_result.returncode != 0:
        print("❌ Tests failed")
        sys.exit(1)
    
    # Build distribution
    print("3. Building distribution...")
    subprocess.run(["python", "-m", "build"])
    
    print("\n✅ Build complete!")
    print("📦 Distribution: dist/")


@app.command()
def clean() -> None:
    """Clean cache and build artifacts.
    
    Removes:
    - __pycache__ directories
    - .pyc files
    - .coverage files
    - build/ and dist/
    - htmlcov/
    """
    import shutil
    
    print("🧹 Cleaning up...")
    
    patterns = [
        "__pycache__",
        "*.pyc",
        ".coverage",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        "htmlcov",
        "*.egg-info"
    ]
    
    for pattern in patterns:
        if "*" in pattern:
            # Handle glob patterns
            from pathlib import Path
            import glob
            for path in glob.glob(f"**/{pattern}", recursive=True):
                try:
                    if Path(path).is_dir():
                        shutil.rmtree(path)
                    else:
                        Path(path).unlink()
                except Exception as e:
                    print(f"⚠️  Could not remove {path}: {e}")
        else:
            # Handle directories
            if Path(pattern).exists():
                try:
                    shutil.rmtree(pattern)
                except Exception as e:
                    print(f"⚠️  Could not remove {pattern}: {e}")
    
    print("✅ Cleaned up")


# ============================================================================
# Documentation Commands
# ============================================================================

@app.command()
def docs() -> None:
    """Generate and view documentation.
    
    Generates:
    - API documentation
    - User story mapping
    - CLI reference
    """
    print("📚 Documentation:")
    print("\n📖 Available Docs:")
    print("  • USER_STORY_TEST_MAPPING.md - All 48 user stories mapped")
    print("  • CLI_FEATURES.md - Complete CLI guide")
    print("  • SECURITY_ACCESS_IMPLEMENTATION_COMPLETE.md - Security tests")
    
    docs_path = Path("docs")
    if docs_path.exists():
        print("\n📂 Generated docs in docs/")
        for doc in docs_path.glob("**/*.md"):
            print(f"  • {doc.relative_to('.')}")


# ============================================================================
# Database Commands
# ============================================================================

@app.command("db:regen-types")
def db_regen_types(
    method: Optional[str] = typer.Option(
        "auto",
        "--method",
        help="Generation method: 'auto' (try pydantic first), 'pydantic', or 'simple'"
    ),
) -> None:
    """Regenerate Supabase type definitions from database schema.
    
    Generates Pydantic models from the Supabase database schema and writes
    them to schemas/generated/models.py.
    
    Methods:
    - auto: Try supabase-pydantic first, fall back to simple introspection
    - pydantic: Use supabase-pydantic (recommended, requires supabase-pydantic)
    - simple: Use simple introspection (no extra dependencies)
    
    Environment variables required:
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_SERVICE_KEY: Service role key (for schema introspection)
    
    Examples:
        atoms db:regen-types                    # Auto-detect best method
        atoms db:regen-types --method pydantic  # Force pydantic method
        atoms db:regen-types --method simple    # Force simple method
    """
    import os
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        print("❌ Error: SUPABASE_URL environment variable not set")
        print("   Set it with: export SUPABASE_URL='your-project-url'")
        sys.exit(1)
    
    if not supabase_key:
        print("❌ Error: SUPABASE_SERVICE_KEY or SUPABASE_KEY environment variable not set")
        print("   Set it with: export SUPABASE_SERVICE_KEY='your-service-key'")
        sys.exit(1)
    
    print("🔄 Regenerating Supabase type definitions...")
    print(f"📍 Supabase URL: {supabase_url}")
    print(f"🔑 Using service key: {'*' * 20}...{supabase_key[-4:] if len(supabase_key) > 4 else '****'}")
    print()
    
    # Determine which method to use
    use_pydantic = False
    use_simple = False
    
    if method == "pydantic":
        use_pydantic = True
    elif method == "simple":
        use_simple = True
    else:  # auto
        # Try pydantic first
        try:
            import supabase_pydantic
            use_pydantic = True
            print("✅ Found supabase-pydantic, using recommended method")
        except ImportError:
            print("⚠️  supabase-pydantic not found, using simple introspection")
            use_simple = True
    
    # Run the appropriate script
    script_path = None
    if use_pydantic:
        script_path = Path("scripts/generate_schemas.py")
        if not script_path.exists():
            print(f"❌ Error: {script_path} not found")
            sys.exit(1)
    else:
        script_path = Path("scripts/generate_schemas_simple.py")
        if not script_path.exists():
            print(f"❌ Error: {script_path} not found")
            sys.exit(1)
    
    print(f"📜 Running: {script_path.name}")
    print()
    
    # Execute the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        env=os.environ.copy(),
    )
    
    if result.returncode == 0:
        print()
        print("✅ Successfully regenerated Supabase types")
        print("📄 Output: schemas/generated/models.py")
        print("📄 Exports: schemas/generated/__init__.py")
    else:
        print()
        print("❌ Failed to regenerate types")
        if use_pydantic:
            print("💡 Tip: Try --method simple if supabase-pydantic is causing issues")
        sys.exit(result.returncode)


# ============================================================================
# Utility Commands
# ============================================================================

@app.command()
def logs(
    lines: int = typer.Option(50, "-n", "--lines", help="Number of lines to show"),
    follow: bool = typer.Option(False, "-f", "--follow", help="Follow log output"),
) -> None:
    """Tail server logs.
    
    Examples:
        atoms logs              # Last 50 lines
        atoms logs -n 100       # Last 100 lines
        atoms logs -f           # Follow in real-time
    """
    import subprocess
    
    log_file = Path(".logs/server.log")
    
    if not log_file.exists():
        print("❌ No log file found")
        print("📝 Start server with: atoms run")
        sys.exit(1)
    
    if follow:
        print(f"📖 Following {log_file}...")
        subprocess.run(["tail", "-f", str(log_file)])
    else:
        print(f"📖 Last {lines} lines of {log_file}:")
        subprocess.run(["tail", "-n", str(lines), str(log_file)])


@app.command()
def info() -> None:
    """Show project information and setup status.
    
    Displays:
    - Project name and version
    - Python version
    - Dependencies summary
    - Test status
    - Git branch
    """
    print("ℹ️  Project Information:")
    print("\n📦 Project:")
    print("  Name: Atoms MCP")
    print("  Version: 0.1.0")
    
    # Python version
    import platform
    print(f"\n🐍 Python: {platform.python_version()}")
    
    # Dependencies
    from cli_update import DependencyAnalyzer
    analyzer = DependencyAnalyzer()
    analyzer.load_dependencies()
    print(f"\n📚 Dependencies:")
    print(f"  Production: {len(analyzer.prod_deps)}")
    print(f"  Development: {len(analyzer.dev_deps)}")
    
    # Git info
    try:
        import subprocess
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True
        ).strip()
        print(f"\n🌿 Git: {branch}")
    except Exception:
        pass


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
