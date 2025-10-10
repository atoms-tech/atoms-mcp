"""
Atoms MCP Unified Test Runner

Extends pheno-sdk's UnifiedMCPTestRunner to integrate with
Atoms MCP's local TestRunner infrastructure.

This provides:
- OAuth authentication via UnifiedCredentialBroker
- Parallel client pooling
- Session caching
- Integration with Atoms-specific reporters and test registry
"""

import os
from pathlib import Path
from typing import Any

from mcp_qa.testing.unified_runner import UnifiedMCPTestRunner

from .adapters import AtomsMCPClientAdapter
from .reporters import (
    ConsoleReporter,
    FunctionalityMatrixReporter,
    JSONReporter,
    MarkdownReporter,
)
from .runner import AtomsTestRunner


class AtomsMCPTestRunner(UnifiedMCPTestRunner):
    """
    Atoms MCP Test Runner integrated with pheno-sdk's UnifiedMCPTestRunner.
    
    Handles OAuth, parallel execution, and session caching via pheno-sdk,
    while using Atoms-specific test infrastructure for execution and reporting.
    
    Usage:
        async with AtomsMCPTestRunner(
            mcp_endpoint="https://mcp.atoms.tech/api/mcp",
            parallel=True,
            workers=16
        ) as runner:
            summary = await runner.run_all()
    """

    def __init__(
        self,
        mcp_endpoint: str,
        provider: str = "authkit",
        parallel: bool = True,
        workers: int = None,
        cache: bool = True,
        verbose: bool = False,
        output_dir: Path | None = None,
        enable_all_reporters: bool = True,
        show_running: bool = True,
    ):
        """
        Initialize Atoms MCP test runner.
        
        Args:
            mcp_endpoint: MCP server endpoint URL
            provider: OAuth provider (default: authkit)
            parallel: Enable parallel execution (default: True)
            workers: Number of parallel workers (default: auto-detect CPU cores)
            cache: Enable test result caching (default: True)
            verbose: Verbose output (default: False)
            output_dir: Directory for test reports (default: tests/)
            enable_all_reporters: Enable JSON, Markdown, and Matrix reporters (default: True)
            show_running: Show currently running tests (default: True for parallel)
        """
        # Initialize pheno-sdk's UnifiedMCPTestRunner
        super().__init__(
            mcp_endpoint=mcp_endpoint,
            provider=provider,
            parallel=parallel,
            workers=workers,
            cache=cache,
            verbose=verbose,
        )

        # Atoms-specific configuration
        self.output_dir = output_dir
        self.enable_all_reporters = enable_all_reporters
        self.show_running = show_running
        self._test_runner: AtomsTestRunner | None = None

    async def run_all(self, categories: list[str] | None = None) -> dict[str, Any]:
        """
        Run all tests with automatic OAuth and parallel execution.
        
        Args:
            categories: Optional list of test categories to run
            
        Returns:
            Test summary dict with results
        """
        # Ensure initialization (handles OAuth + parallel client pool + auth validation)
        await self.initialize()

        if self.verbose:
            # Show validation results if available
            if self._validation_result:
                print("")
                print("📊 Auth Validation Summary:")
                for check_name, check_result in self._validation_result.checks.items():
                    status = "✓" if check_result["success"] else "✗"
                    print(f"   {status} {check_name}: {check_result['message']}")
                print("")

            print("🚀 Running Atoms MCP tests...")
            print(f"   Endpoint: {self.mcp_endpoint}")
            print(f"   Parallel: {self.parallel} ({self.workers} workers)")
            print(f"   Cache: {self.cache}")

        # Capture OAuth token from the broker for HTTP mode
        access_token = None
        if hasattr(self, "credentials") and self.credentials:
            access_token = self.credentials.access_token

        # Create Atoms MCP client adapter with HTTP mode
        adapter = AtomsMCPClientAdapter(
            client=self.client,
            mcp_endpoint=self.mcp_endpoint,
            access_token=access_token,
            use_direct_http=True,  # Use JSON-RPC 2.0 over HTTP POST (correct MCP protocol)
            verbose_on_fail=True
        )

        # Run health checks if available
        try:
            from .health_checks import HealthChecker
            health_results = await HealthChecker.check_all()
            adapter.health_results = health_results
            if self.verbose:
                print("✅ Health checks completed")
        except ImportError:
            if self.verbose:
                print("⚠️  Health checks not available")

        # Setup reporters
        reporters = [
            ConsoleReporter(
                verbose=self.verbose,
                show_running=self.show_running and self.parallel
            )
        ]

        if self.enable_all_reporters:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_dir or Path(__file__).parent.parent

            reporters.extend([
                JSONReporter(str(output_dir / f"test_report_{timestamp}.json")),
                MarkdownReporter(str(output_dir / f"test_report_{timestamp}.md")),
                FunctionalityMatrixReporter(
                    str(output_dir / f"functionality_matrix_{timestamp}.md")
                ),
            ])

        # Create Atoms TestRunner with parallel client manager if available
        self._test_runner = AtomsTestRunner(
            client_adapter=adapter,
            cache=self.cache,
            parallel=self.parallel,
            parallel_workers=self.workers,
            reporters=reporters,
            use_optimizations=True,  # Enable connection pooling
            verbose=self.verbose,
        )

        # Attach parallel client manager from pheno-sdk (if available)
        if self._client_manager:
            self._test_runner.client_manager = self._client_manager
            if self.verbose:
                print("✅ Using pheno-sdk parallel client manager")

        # Run tests
        summary = await self._test_runner.run_all(categories=categories)

        return summary


async def run_atoms_tests(
    mcp_endpoint: str = None,
    provider: str = "authkit",
    parallel: bool = True,
    workers: int = None,
    categories: list[str] | None = None,
    cache: bool = True,
    verbose: bool = False,
    **kwargs
) -> dict[str, Any]:
    """
    Quick helper to run Atoms MCP tests with automatic OAuth and parallel execution.
    
    Args:
        mcp_endpoint: MCP server endpoint URL (default: from env ATOMS_MCP_ENDPOINT)
        provider: OAuth provider (default: authkit)
        parallel: Enable parallel execution (default: True)
        workers: Number of parallel workers (default: auto-detect)
        categories: Optional list of test categories
        cache: Enable test result caching (default: True)
        verbose: Verbose output
        **kwargs: Additional arguments for AtomsMCPTestRunner
        
    Returns:
        Test summary dict
        
    Example:
        summary = await run_atoms_tests(
            mcp_endpoint="https://mcp.atoms.tech/api/mcp",
            parallel=True,
            workers=16,
            verbose=True
        )
    """
    mcp_endpoint = mcp_endpoint or os.getenv(
        "ATOMS_MCP_ENDPOINT",
        "https://mcp.atoms.tech/api/mcp"
    )

    async with AtomsMCPTestRunner(
        mcp_endpoint=mcp_endpoint,
        provider=provider,
        parallel=parallel,
        workers=workers,
        cache=cache,
        verbose=verbose,
        **kwargs
    ) as runner:
        summary = await runner.run_all(categories=categories)
        return summary
