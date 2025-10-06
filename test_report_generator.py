#!/usr/bin/env python3
"""Test report generator for Atoms MCP headless testing.

Generates comprehensive test reports in multiple formats:
- Console output (pretty printed)
- Markdown report
- JSON report for CI/CD integration
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path


class TestReportGenerator:
    """Generate comprehensive test reports."""

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.connection_info: Dict[str, Any] = {}
        self.auth_info: Dict[str, Any] = {}

    def set_connection_info(self, url: str, status: str, error: str | None = None):
        """Set connection information."""
        self.connection_info = {
            "url": url,
            "status": status,
            "error": error
        }

    def set_auth_info(self, status: str, user: str | None = None, error: str | None = None):
        """Set authentication information."""
        self.auth_info = {
            "status": status,
            "user": user,
            "error": error
        }

    def start_test_run(self):
        """Mark the start of a test run."""
        self.start_time = datetime.now()

    def end_test_run(self):
        """Mark the end of a test run."""
        self.end_time = datetime.now()

    def add_test_result(
        self,
        test_name: str,
        tool: str,
        params: Dict[str, Any],
        success: bool,
        duration_ms: float,
        response: Any = None,
        error: str | None = None,
        known_issue: bool = False,
        skipped: bool = False,
        skip_reason: str | None = None
    ):
        """Add a test result."""
        result = {
            "test_name": test_name,
            "tool": tool,
            "params": params,
            "success": success,
            "duration_ms": round(duration_ms, 2),
            "response": response,
            "error": error,
            "known_issue": known_issue,
            "skipped": skipped,
            "skip_reason": skip_reason,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total = len(self.test_results)
        if total == 0:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "known_issues": 0,
                "pass_rate": 0.0,
                "avg_duration_ms": 0.0
            }

        passed = sum(1 for r in self.test_results if r["success"] and not r["skipped"])
        failed = sum(1 for r in self.test_results if not r["success"] and not r["skipped"])
        skipped = sum(1 for r in self.test_results if r["skipped"])
        known_issues = sum(1 for r in self.test_results if r.get("known_issue", False))

        total_duration = sum(r["duration_ms"] for r in self.test_results if not r["skipped"])
        avg_duration = total_duration / (total - skipped) if (total - skipped) > 0 else 0.0

        pass_rate = (passed / (total - skipped)) * 100 if (total - skipped) > 0 else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "known_issues": known_issues,
            "pass_rate": round(pass_rate, 1),
            "avg_duration_ms": round(avg_duration, 2)
        }

    def print_console_report(self):
        """Print formatted report to console."""
        print("\n" + "=" * 80)
        print("ATOMS MCP HEADLESS TEST REPORT")
        print("=" * 80)

        # Connection info
        print(f"\n📡 CONNECTION")
        status_icon = "✅" if self.connection_info.get("status") == "connected" else "❌"
        print(f"   {status_icon} URL: {self.connection_info.get('url')}")
        if self.connection_info.get("error"):
            print(f"   ❌ Error: {self.connection_info['error']}")

        # Auth info
        print(f"\n🔐 AUTHENTICATION")
        auth_status = self.auth_info.get("status")
        status_icon = "✅" if auth_status == "authenticated" else "❌"
        print(f"   {status_icon} Status: {auth_status}")
        if self.auth_info.get("user"):
            print(f"   👤 User: {self.auth_info['user']}")
        if self.auth_info.get("error"):
            print(f"   ❌ Error: {self.auth_info['error']}")

        # Summary stats
        stats = self.get_summary_stats()
        print(f"\n📊 SUMMARY")
        print(f"   Total Tests: {stats['total']}")
        print(f"   ✅ Passed: {stats['passed']}")
        print(f"   ❌ Failed: {stats['failed']}")
        print(f"   ⏭️  Skipped: {stats['skipped']}")
        print(f"   ⚠️  Known Issues: {stats['known_issues']}")
        print(f"   📈 Pass Rate: {stats['pass_rate']}%")
        print(f"   ⏱️  Avg Duration: {stats['avg_duration_ms']}ms")

        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"   🕐 Total Time: {duration:.2f}s")

        # Group results by tool
        by_tool: Dict[str, List[Dict[str, Any]]] = {}
        for result in self.test_results:
            tool = result["tool"]
            if tool not in by_tool:
                by_tool[tool] = []
            by_tool[tool].append(result)

        # Print results by tool
        print(f"\n🔧 DETAILED RESULTS")
        for tool, results in by_tool.items():
            print(f"\n   {tool}:")
            for result in results:
                if result["skipped"]:
                    icon = "⏭️ "
                    status = f"SKIPPED: {result['skip_reason']}"
                elif result["known_issue"]:
                    icon = "⚠️ "
                    status = f"KNOWN ISSUE: {result['error'][:50] if result['error'] else 'N/A'}"
                elif result["success"]:
                    icon = "✅"
                    status = f"{result['duration_ms']}ms"
                else:
                    icon = "❌"
                    status = f"{result['error'][:50] if result['error'] else 'Failed'}"

                print(f"     {icon} {result['test_name']}")
                print(f"        {status}")

        print("\n" + "=" * 80)

    def generate_markdown_report(self, output_path: str | None = None) -> str:
        """Generate markdown report."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"test_report_{timestamp}.md"

        stats = self.get_summary_stats()

        lines = [
            "# Atoms MCP Headless Test Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Connection",
            "",
            f"- **URL:** `{self.connection_info.get('url')}`",
            f"- **Status:** {'✅ Connected' if self.connection_info.get('status') == 'connected' else '❌ Failed'}",
        ]

        if self.connection_info.get("error"):
            lines.append(f"- **Error:** `{self.connection_info['error']}`")

        lines.extend([
            "",
            "## Authentication",
            "",
            f"- **Status:** {'✅ Authenticated' if self.auth_info.get('status') == 'authenticated' else '❌ Failed'}",
        ])

        if self.auth_info.get("user"):
            lines.append(f"- **User:** `{self.auth_info['user']}`")
        if self.auth_info.get("error"):
            lines.append(f"- **Error:** `{self.auth_info['error']}`")

        lines.extend([
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Tests | {stats['total']} |",
            f"| ✅ Passed | {stats['passed']} |",
            f"| ❌ Failed | {stats['failed']} |",
            f"| ⏭️ Skipped | {stats['skipped']} |",
            f"| ⚠️ Known Issues | {stats['known_issues']} |",
            f"| 📈 Pass Rate | {stats['pass_rate']}% |",
            f"| ⏱️ Avg Duration | {stats['avg_duration_ms']}ms |",
        ])

        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            lines.append(f"| 🕐 Total Time | {duration:.2f}s |")

        # Group by tool
        by_tool: Dict[str, List[Dict[str, Any]]] = {}
        for result in self.test_results:
            tool = result["tool"]
            if tool not in by_tool:
                by_tool[tool] = []
            by_tool[tool].append(result)

        lines.extend([
            "",
            "## Test Results by Tool",
            ""
        ])

        for tool, results in by_tool.items():
            lines.append(f"### {tool}")
            lines.append("")
            lines.append("| Test | Status | Duration | Details |")
            lines.append("|------|--------|----------|---------|")

            for result in results:
                if result["skipped"]:
                    status = "⏭️ SKIPPED"
                    details = result["skip_reason"]
                elif result["known_issue"]:
                    status = "⚠️ KNOWN ISSUE"
                    details = result["error"][:50] if result["error"] else "N/A"
                elif result["success"]:
                    status = "✅ PASS"
                    details = "Success"
                else:
                    status = "❌ FAIL"
                    details = result["error"][:50] if result["error"] else "Failed"

                duration = f"{result['duration_ms']}ms" if not result["skipped"] else "-"
                lines.append(f"| {result['test_name']} | {status} | {duration} | {details} |")

            lines.append("")

        markdown = "\n".join(lines)

        # Write to file
        Path(output_path).write_text(markdown)
        print(f"\n📝 Markdown report saved to: {output_path}")

        return markdown

    def generate_json_report(self, output_path: str | None = None) -> Dict[str, Any]:
        """Generate JSON report for CI/CD integration."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"test_report_{timestamp}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "connection": self.connection_info,
            "auth": self.auth_info,
            "summary": self.get_summary_stats(),
            "test_results": self.test_results
        }

        if self.start_time and self.end_time:
            report["duration_seconds"] = (self.end_time - self.start_time).total_seconds()

        # Write to file
        Path(output_path).write_text(json.dumps(report, indent=2))
        print(f"📊 JSON report saved to: {output_path}")

        return report
