"""
Comprehensive Test Evolution Runner - Main orchestrator for hot/cold/dry test execution.

This module contains:
- ComprehensiveTestEvolutionRunner: Main orchestrator class
- Performance scoring and coverage analysis
- Rich UI result display
"""

import asyncio
from typing import Any

from test_definitions import ALL_TESTS, TestResult
from test_runners import ColdTestRunner, DryTestRunner, HotTestRunner


class ComprehensiveTestEvolutionRunner:
    """Comprehensive test evolution runner with hot/cold/dry modes covering all features."""

    def __init__(self):
        self.hot_runner = HotTestRunner()
        self.cold_runner = ColdTestRunner()
        self.dry_runner = DryTestRunner()

    async def execute_matrix(
        self,
        modes: list[str],
        environment: str,
        parallel: bool = True,
        coverage: bool = True
    ) -> dict[str, TestResult]:
        """Execute comprehensive test matrix with specified modes."""

        print(f"\n🧪 Comprehensive Test Evolution Matrix - Environment: {environment.upper()}")
        print(f"📋 Modes: {', '.join([m.upper() for m in modes])}")
        print(f"⚡ Parallel: {parallel}")
        print(f"📊 Coverage: {coverage}")
        print("=" * 60)

        results = {}

        # Handle comma-separated modes
        mode_list = []
        for mode_str in modes:
            mode_list.extend([m.strip() for m in mode_str.split(",") if m.strip()])

        for mode in mode_list:
            print(f"\n🧪 Running {mode.upper()} tests...")

            if mode.upper() == "HOT":
                results[mode.upper()] = await self.hot_runner.run_hot_tests(environment)
            elif mode.upper() == "COLD":
                results[mode.upper()] = await self.cold_runner.run_cold_tests(environment)
            elif mode.upper() == "DRY":
                results[mode.upper()] = await self.dry_runner.run_dry_tests(environment)

        if coverage:
            results["coverage"] = await self.generate_coverage_report(results)

        return results

    async def generate_coverage_report(self, results: dict[str, TestResult]) -> dict[str, Any]:
        """Generate comprehensive coverage report from test results."""

        total_tests = sum(r.total_tests for r in results.values() if hasattr(r, "total_tests"))
        total_passed = sum(r.passed_tests for r in results.values() if hasattr(r, "passed_tests"))
        total_failed = sum(r.failed_tests for r in results.values() if hasattr(r, "failed_tests"))

        avg_duration = sum(r.duration_seconds for r in results.values() if hasattr(r, "duration_seconds")) / max(1, len(results))

        # Tool coverage analysis
        tool_coverage = {}
        for mode, result in results.items():
            if not hasattr(result, "details") or "categories" not in result.details:
                continue

            categories = result.details["categories"]
            for category, stats in categories.items():
                if category not in tool_coverage:
                    tool_coverage[category] = {"total": 0, "passed": 0, "modes": set()}
                tool_coverage[category]["total"] += stats["total"]
                tool_coverage[category]["passed"] += stats["passed"]
                tool_coverage[category]["modes"].add(mode)

        return {
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "pass_rate": (total_passed / max(1, total_tests)) * 100,
            "average_duration": avg_duration,
            "performance_score": self._calculate_performance_score(results),
            "tool_coverage": tool_coverage,
            "test_categories": list(ALL_TESTS.keys()),
            "total_features_tested": sum(len(tests) for tests in ALL_TESTS.values())
        }

    def _calculate_performance_score(self, results: dict[str, TestResult]) -> float:
        """Calculate performance score based on duration targets."""
        scores = []

        for mode, result in results.items():
            if not hasattr(result, "duration_seconds") or mode == "coverage":
                continue

            # Performance targets: HOT<30s, COLD<2s, DRY<1s
            if mode == "HOT":
                target_duration = 30.0
            elif mode == "COLD":
                target_duration = 2.0
            elif mode == "DRY":
                target_duration = 1.0
            else:
                target_duration = 5.0

            # Score: 100 for meeting target, reduced for overshoot
            if result.duration_seconds <= target_duration:
                score = 100
            else:
                # Penalty for exceeding target (10% per 2x target)
                ratio = result.duration_seconds / target_duration
                penalty = (ratio - 1) * 50  # 50% penalty for 2x target
                score = max(0, 100 - penalty)

            scores.append(score)

        return sum(scores) / max(1, len(scores))

    def display_test_results(self, results: dict[str, TestResult]):
        """Display comprehensive test results using Rich UI."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            console = Console()
        except ImportError:
            print("Rich not available for result display")
            return

        # Display results table
        results_table = Table(title="Comprehensive Test Evolution Results")
        results_table.add_column("Mode", style="bold blue")
        results_table.add_column("Tests", style="dim")
        results_table.add_column("Passed", style="bold green")
        results_table.add_column("Failed", style="bold red")
        results_table.add_column("Duration", style="bold yellow")
        results_table.add_column("Performance", style="bold cyan")

        for mode, result in results.items():
            if mode == "coverage":
                continue  # Handle separately

            if not hasattr(result, "total_tests"):
                continue

            # Calculate performance score
            if mode == "HOT":
                target_duration = 30.0
            elif mode == "COLD":
                target_duration = 2.0
            elif mode == "DRY":
                target_duration = 1.0
            else:
                target_duration = 5.0

            score = 100
            if result.duration_seconds > target_duration:
                ratio = result.duration_seconds / target_duration
                penalty = (ratio - 1) * 50
                score = max(0, 100 - penalty)

            perf_indicator = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"

            results_table.add_row(
                mode.upper(),
                str(result.total_tests),
                str(result.passed_tests),
                str(result.failed_tests),
                f"{result.duration_seconds:.2f}s",
                f"{perf_indicator} {score:.0f}%"
            )

        console.print(results_table)

        # Display category breakdown if available
        if any(hasattr(r, "details") and "categories" in r.details for r in results.values()):
            category_table = Table(title="Test Coverage by Category")
            category_table.add_column("Category", style="bold blue")
            category_table.add_column("Total Tests", style="dim")
            category_table.add_column("Passed", style="bold green")
            category_table.add_column("Pass Rate", style="bold cyan")

            # Aggregate category results across modes
            category_totals = {}
            for result in results.values():
                if not hasattr(result, "details") or "categories" not in result.details:
                    continue

                for category, stats in result.details["categories"].items():
                    if category not in category_totals:
                        category_totals[category] = {"total": 0, "passed": 0}
                    category_totals[category]["total"] += stats["total"]
                    category_totals[category]["passed"] += stats["passed"]

            for category, totals in category_totals.items():
                pass_rate = (totals["passed"] / max(1, totals["total"])) * 100
                category_table.add_row(
                    category.title(),
                    str(totals["total"]),
                    str(totals["passed"]),
                    f"{pass_rate:.1f}%"
                )

            console.print(category_table)

        # Display coverage if available
        if "coverage" in results:
            coverage = results["coverage"]
            console.print("\n[bold]📊 Comprehensive Coverage Summary:[/bold]")
            console.print(f"Total Tests: {coverage['total_tests']}")
            console.print(f"Passed: {coverage['passed_tests']} ({coverage['pass_rate']:.1f}%)")
            console.print(f"Failed: {coverage['failed_tests']}")
            console.print(f"Avg Duration: {coverage['average_duration']:.2f}s")
            console.print(f"Performance Score: {coverage['performance_score']:.1f}%")
            console.print(f"Features Tested: {coverage['total_features_tested']}")
            console.print(f"Test Categories: {', '.join(coverage['test_categories'])}")

            # Display tool coverage panel
            if coverage.get("tool_coverage"):
                coverage_text = "\n".join([
                    f"{cat}: {stats['passed']}/{stats['total']} tests across {', '.join(stats['modes'])} modes"
                    for cat, stats in coverage["tool_coverage"].items()
                ])
                console.print(Panel(
                    coverage_text,
                    title="[bold blue]Tool Coverage Details[/bold blue]",
                    border_style="blue"
                ))

        console.print("\n[bold green]✅ Comprehensive test evolution complete[/bold green]")


# Main execution function
async def main():
    """Main execution function for comprehensive test evolution."""
    runner = ComprehensiveTestEvolutionRunner()

    # Example execution
    results = await runner.execute_matrix(
        modes=["HOT", "COLD", "DRY"],
        environment="development",
        parallel=True,
        coverage=True
    )

    runner.display_test_results(results)

    return results


if __name__ == "__main__":
    asyncio.run(main())
