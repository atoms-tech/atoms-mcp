"""
Rich Display Module for Test Results

Provides beautiful terminal UI for test evolution results using Rich library.
"""

from typing import Any

# Import Rich components
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Set flag for evolution module availability
EVOLUTION_AVAILABLE = True
try:
    from . import evolution
except ImportError:
    EVOLUTION_AVAILABLE = False


class TestDisplayManager:
    """Manages Rich display for test evolution."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    def display_test_results(self, results: dict[str, Any]):
        """Display test results using Rich UI."""

        if not RICH_AVAILABLE:
            self._display_simple_results(results)
            return

        if not EVOLUTION_AVAILABLE:
            self._display_error("Test evolution module not available")
            return

        # Display header
        self.console.print(Panel.fit("[bold blue]🧪 Test Evolution Results[/bold blue]", border_style="blue"))

        # Results table
        table = Table(title="Test Matrix Results")
        table.add_column("Mode", style="bold blue", width=8)
        table.add_column("Tests", style="dim", width=6)
        table.add_column("Passed", style="bold green", width=7)
        table.add_column("Failed", style="bold red", width=7)
        table.add_column("Duration", style="bold yellow", width=10)
        table.add_column("Performance", style="bold cyan", width=11)

        for mode, result in results.items():
            if mode.lower() == "coverage":
                continue  # Handle separately

            # Extract result fields safely
            total_tests = getattr(result, "total_tests", 0)
            passed_tests = getattr(result, "passed_tests", 0)
            failed_tests = getattr(result, "failed_tests", 0)
            duration = getattr(result, "duration_seconds", 0.0)

            # Calculate performance score
            score = self._calculate_performance_score(mode, duration)
            perf_indicator = self._get_performance_indicator(score)

            table.add_row(
                mode.upper(),
                str(total_tests),
                str(passed_tests),
                str(failed_tests),
                f"{duration:.2f}s",
                f"{perf_indicator} {score:.0f}%",
            )

        self.console.print(table)

        # Display coverage if available
        if "coverage" in results:
            self._display_coverage_summary(results["coverage"])

    def display_test_progress(self, mode: str, message: str):
        """Display test progress with spinner."""
        if not RICH_AVAILABLE:
            print(f"{mode.upper()}: {message}")
            return

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console
        ) as progress:
            task = progress.add_task(f"{mode.upper()}", total=1)
            progress.update(task, description=message)
            # Short delay to show spinner
            import time

            time.sleep(0.5)

    def display_auth_flow(self, mode: str, method: str):
        """Display authentication flow information."""
        if not RICH_AVAILABLE:
            print(f"{mode.upper()} Authentication: {method}")
            return

        auth_methods = {
            "playwright": "🔐 Browser automation",
            "authkit": "🔑 Programmatic API",
            "mock": "🎭 Fully simulated",
        }

        method_desc = auth_methods.get(method, f"📋 {method}")
        self.console.print(f"[blue]Auth Method: {method_desc}[/blue]")

    def display_client_type(self, mode: str, client_type: str):
        """Display MCP client type information."""
        if not RICH_AVAILABLE:
            print(f"{mode.upper()} Client: {client_type}")
            return

        client_types = {
            "real_http": "🌐 Real HTTP client",
            "in_memory": "💾 In-memory client",
            "simulated": "🎯 Fully simulated",
        }

        client_desc = client_types.get(client_type, f"📋 {client_type}")
        self.console.print(f"[cyan]Client Type: {client_desc}[/cyan]")

    def _display_simple_results(self, results: dict[str, Any]):
        """Fallback simple display without Rich."""
        print("\n=== Test Evolution Results ===")
        for mode, result in results.items():
            if mode.lower() == "coverage":
                continue
            print(f"{mode.upper()}: {result}")
        print("\nTest evolution complete")

    def _display_coverage_summary(self, coverage: dict[str, Any]):
        """Display coverage summary."""
        if not RICH_AVAILABLE:
            print(f"\nCoverage: {coverage}")
            return

        coverage_table = Table(title="Coverage Summary")
        coverage_table.add_column("Metric", style="bold blue", width=12)
        coverage_table.add_column("Value", style="bold green", width=15)

        coverage_table.add_row("Total Tests", str(coverage.get("total_tests", 0)))
        coverage_table.add_row("Passed Tests", str(coverage.get("passed_tests", 0)))
        coverage_table.add_row("Pass Rate", f"{coverage.get('pass_rate', 0):.1f}%")
        coverage_table.add_row("Avg Duration", f"{coverage.get('average_duration', 0):.2f}s")
        coverage_table.add_row("Performance", f"{coverage.get('performance_score', 0):.1f}%")

        self.console.print(coverage_table)

    def _calculate_performance_score(self, mode: str, duration: float) -> float:
        """Calculate performance score based on mode and duration."""
        # Performance targets: HOT<30s, COLD<2s, DRY<1s
        targets = {"HOT": 30.0, "COLD": 2.0, "DRY": 1.0}

        target = targets.get(mode.upper(), 5.0)

        # Score: 100 for meeting target, reduced for overshoot
        if duration <= target:
            return 100.0

        # Penalty for exceeding target (10% per 2x target)
        ratio = duration / target
        if ratio <= 2.0:
            penalty = (ratio - 1) * 50  # 50% penalty for 2x target
        else:
            penalty = 75  # 75% penalty for >2x target

        return max(0, 100 - penalty)

    def _get_performance_indicator(self, score: float) -> str:
        """Get performance indicator emoji based on score."""
        if score >= 80:
            return "🟢"  # Green circle
        if score >= 60:
            return "🟡"  # Yellow circle
        return "🔴"  # Red circle

    def _display_error(self, error: str):
        """Display error message."""
        if RICH_AVAILABLE:
            self.console.print(f"[bold red]Error: {error}[/bold red]")
        else:
            print(f"Error: {error}")


# Create global display manager
display_manager = TestDisplayManager()
