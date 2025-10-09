"""
Test Reporters for Result Output

Provides reporters for:
- Console output (human-readable)
- JSON export (machine-readable)
- Markdown documentation
- Functionality Matrix (comprehensive feature coverage)
- Detailed error reporting with pytest-like output
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class TestReporter:
    """Base class for test reporters."""

    def report(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
        """Generate report from test results."""
        raise NotImplementedError


class ConsoleReporter(TestReporter):
    """Console reporter with formatted output."""

    def __init__(self, verbose: bool = False, show_running: bool = False):
        """
        Initialize console reporter.

        Args:
            verbose: Show detailed output during test execution
            show_running: Show currently running tests (useful for parallel execution)
        """
        self.verbose = verbose
        self.show_running = show_running

    def report(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
        """Print formatted report to console."""
        print("\n" + "=" * 80)
        print("ATOMS MCP TEST REPORT")
        print("=" * 80)

        # Connection info
        if "endpoint" in metadata:
            print(f"\n📡 ENDPOINT: {metadata['endpoint']}")
        if "auth_status" in metadata:
            print(f"🔐 AUTH: {metadata['auth_status']}")

        # Summary stats
        total = len(results)
        passed = sum(1 for r in results if r.get("success", False) and not r.get("skipped", False))
        failed = sum(1 for r in results if not r.get("success", False) and not r.get("skipped", False))
        skipped = sum(1 for r in results if r.get("skipped", False))
        cached = sum(1 for r in results if r.get("cached", False))

        pass_rate = (passed / (total - skipped)) * 100 if (total - skipped) > 0 else 0

        print(f"\n📊 SUMMARY")
        print(f"   Total: {total} | ✅ {passed} | ❌ {failed} | ⏭️  {skipped} | 💾 {cached}")
        print(f"   Pass Rate: {pass_rate:.1f}%")

        if "duration_seconds" in metadata:
            print(f"   Total Time: {metadata['duration_seconds']:.2f}s")

        # Group by tool
        by_tool: Dict[str, List] = {}
        for result in results:
            tool = result.get("tool_name", "unknown")
            by_tool.setdefault(tool, []).append(result)

        print(f"\n🔧 RESULTS BY TOOL:")
        for tool, tool_results in sorted(by_tool.items()):
            print(f"\n   {tool}:")
            for r in tool_results:
                icon = "💾" if r.get("cached") else ("⏭️ " if r.get("skipped") else ("✅" if r.get("success") else "❌"))
                name = r.get("test_name", "unknown")
                duration = r.get("duration_ms", 0)
                print(f"     {icon} {name} ({duration:.2f}ms)")

                if r.get("error") and not r.get("success"):
                    error_preview = str(r["error"])[:80]
                    print(f"        {error_preview}")

        print("\n" + "=" * 80)


class JSONReporter(TestReporter):
    """JSON reporter for machine-readable output."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)

    def report(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
        """Export report as JSON."""
        # Sanitize results to remove non-JSON-serializable objects
        sanitized_results = []
        for result in results:
            sanitized = {}
            for key, value in result.items():
                # Skip functions and non-serializable types
                if callable(value):
                    continue
                try:
                    json.dumps(value)
                    sanitized[key] = value
                except (TypeError, ValueError):
                    sanitized[key] = str(value)

            sanitized_results.append(sanitized)

        report = {
            "generated_at": datetime.now().isoformat(),
            "metadata": metadata,
            "summary": self._calculate_summary(results),
            "results": sanitized_results,
        }

        self.output_path.write_text(json.dumps(report, indent=2))
        print(f"📄 JSON Report: {self.output_path}")

    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total = len(results)
        passed = sum(1 for r in results if r.get("success", False) and not r.get("skipped", False))
        failed = sum(1 for r in results if not r.get("success", False) and not r.get("skipped", False))
        skipped = sum(1 for r in results if r.get("skipped", False))
        cached = sum(1 for r in results if r.get("cached", False))

        total_duration = sum(r.get("duration_ms", 0) for r in results if not r.get("skipped", False))
        avg_duration = total_duration / (total - skipped) if (total - skipped) > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "cached": cached,
            "pass_rate": (passed / (total - skipped) * 100) if (total - skipped) > 0 else 0,
            "avg_duration_ms": avg_duration,
        }


class MarkdownReporter(TestReporter):
    """Markdown reporter for documentation."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)

    def report(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
        """Export report as Markdown."""
        lines = []

        lines.append("# Atoms MCP Test Report\n")
        lines.append(f"**Generated**: {datetime.now().isoformat()}\n")
        lines.append(f"**Endpoint**: {metadata.get('endpoint', 'N/A')}\n")
        lines.append(f"**Auth**: {metadata.get('auth_status', 'N/A')}\n")

        # Summary
        summary = self._calculate_summary(results)
        lines.append("\n## Summary\n")
        lines.append(f"- Total: {summary['total']}")
        lines.append(f"- Passed: ✅ {summary['passed']}")
        lines.append(f"- Failed: ❌ {summary['failed']}")
        lines.append(f"- Skipped: ⏭️  {summary['skipped']}")
        lines.append(f"- Cached: 💾 {summary['cached']}")
        lines.append(f"- Pass Rate: {summary['pass_rate']:.1f}%\n")

        # Results table
        lines.append("\n## Results\n")
        lines.append("| Tool | Test | Status | Duration |")
        lines.append("|------|------|--------|----------|")

        for r in results:
            tool = r.get("tool_name", "unknown")
            name = r.get("test_name", "unknown")
            if r.get("cached"):
                status = "💾 Cached"
            elif r.get("skipped"):
                status = "⏭️ Skipped"
            else:
                status = "✅ Pass" if r.get("success") else "❌ Fail"
            duration = f"{r.get('duration_ms', 0):.2f}ms"
            lines.append(f"| {tool} | {name} | {status} | {duration} |")

        self.output_path.write_text("\n".join(lines))
        print(f"📄 Markdown Report: {self.output_path}")

    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total = len(results)
        passed = sum(1 for r in results if r.get("success", False) and not r.get("skipped", False))
        failed = sum(1 for r in results if not r.get("success", False) and not r.get("skipped", False))
        skipped = sum(1 for r in results if r.get("skipped", False))
        cached = sum(1 for r in results if r.get("cached", False))

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "cached": cached,
            "pass_rate": (passed / (total - skipped) * 100) if (total - skipped) > 0 else 0,
        }


class FunctionalityMatrixReporter(TestReporter):
    """
    Functionality Matrix Reporter - Comprehensive Feature Coverage

    Maps test results to:
    - Tool capabilities
    - User stories
    - Data items validated
    - Assertions checked
    """

    TOOL_CAPABILITIES = {
        "workspace_tool": {
            "description": "Workspace context management for organizing work",
            "operations": {
                "list_workspaces": {
                    "feature": "List all accessible workspaces",
                    "user_story": "As a user, I want to see all my workspaces",
                    "data_items": ["organizations", "projects", "documents"],
                    "assertions": ["Returns organization list", "Includes context"],
                },
                "get_context": {
                    "feature": "Get current workspace context",
                    "user_story": "As a user, I want to know my current context",
                    "data_items": ["active_organization", "active_project"],
                    "assertions": ["Returns current context"],
                },
                "set_context": {
                    "feature": "Set workspace context",
                    "user_story": "As a user, I want to switch workspaces",
                    "data_items": ["organization_id", "project_id"],
                    "assertions": ["Sets active context"],
                },
                "get_defaults": {
                    "feature": "Get workspace defaults",
                    "user_story": "As a user, I want to see default settings",
                    "data_items": ["defaults", "preferences"],
                    "assertions": ["Returns default configuration"],
                },
            },
        },
        "entity_tool": {
            "description": "CRUD operations for all Atoms entities",
            "operations": {
                "list_organizations": {
                    "feature": "List organizations",
                    "user_story": "As a user, I want to see all my organizations",
                    "data_items": ["id", "name", "slug", "created_by"],
                    "assertions": ["Returns org list", "Respects RLS"],
                },
                "list_projects": {
                    "feature": "List projects",
                    "user_story": "As a user, I want to see all my projects",
                    "data_items": ["id", "name", "organization_id", "status"],
                    "assertions": ["Returns project list", "Filtered by org"],
                },
                "list_documents": {
                    "feature": "List documents",
                    "user_story": "As a user, I want to browse documents",
                    "data_items": ["id", "name", "project_id", "type"],
                    "assertions": ["Returns document list"],
                },
                "list_requirements": {
                    "feature": "List requirements",
                    "user_story": "As a user, I want to see all requirements",
                    "data_items": ["id", "name", "document_id", "status"],
                    "assertions": ["Returns requirement list"],
                },
                "create_organization": {
                    "feature": "Create organization",
                    "user_story": "As a user, I want to create organizations",
                    "data_items": ["name", "slug", "description"],
                    "assertions": ["Creates org", "Sets owner"],
                    "known_issue": "RLS policy constraint on updated_by",
                },
                "read_by_id": {
                    "feature": "Read entity by ID",
                    "user_story": "As a user, I want to view entity details",
                    "data_items": ["entity data", "metadata", "relationships"],
                    "assertions": ["Returns entity", "Includes relations"],
                },
                "update": {
                    "feature": "Update entity",
                    "user_story": "As a user, I want to modify entities",
                    "data_items": ["entity_id", "update_data"],
                    "assertions": ["Updates entity", "Validates data"],
                },
                "fuzzy_match": {
                    "feature": "Fuzzy search",
                    "user_story": "As a user, I want flexible search",
                    "data_items": ["search_term", "matches", "scores"],
                    "assertions": ["Returns ranked matches"],
                },
            },
        },
        "query_tool": {
            "description": "Search and analytics across all entities",
            "operations": {
                "search_projects": {
                    "feature": "Search projects",
                    "user_story": "As a user, I want to find projects",
                    "data_items": ["search_term", "results", "count"],
                    "assertions": ["Returns ranked results"],
                },
                "search_documents": {
                    "feature": "Search documents",
                    "user_story": "As a user, I want to find documents",
                    "data_items": ["search_term", "results", "count"],
                    "assertions": ["Returns ranked results"],
                },
                "search_multi": {
                    "feature": "Multi-entity search",
                    "user_story": "As a user, I want to search everything",
                    "data_items": ["entities", "results", "by_type"],
                    "assertions": ["Searches multiple types"],
                },
                "aggregate": {
                    "feature": "Aggregate statistics",
                    "user_story": "As a user, I want summary stats",
                    "data_items": ["aggregates", "counts", "summaries"],
                    "assertions": ["Returns aggregated data"],
                },
                "rag_search_semantic": {
                    "feature": "Semantic RAG search",
                    "user_story": "As a user, I want intelligent search",
                    "data_items": ["query", "results", "similarity_scores"],
                    "assertions": ["Uses vector similarity"],
                    "known_issue": "Embedding calculation errors",
                },
                "rag_search_keyword": {
                    "feature": "Keyword RAG search",
                    "user_story": "As a user, I want enhanced keyword search",
                    "data_items": ["query", "results", "context"],
                    "assertions": ["Returns with context"],
                },
                "rag_search_hybrid": {
                    "feature": "Hybrid RAG search",
                    "user_story": "As a user, I want best of both searches",
                    "data_items": ["query", "results", "scores"],
                    "assertions": ["Combines semantic + keyword"],
                },
            },
        },
        "relationship_tool": {
            "description": "Manage relationships between entities",
            "operations": {
                "list_relationships": {
                    "feature": "List entity relationships",
                    "user_story": "As a user, I want to see connections",
                    "data_items": ["relationship_type", "source", "target"],
                    "assertions": ["Returns relationship list"],
                },
                "link": {
                    "feature": "Link entities",
                    "user_story": "As a user, I want to connect entities",
                    "data_items": ["source", "target", "type", "metadata"],
                    "assertions": ["Creates relationship"],
                },
                "unlink": {
                    "feature": "Unlink entities",
                    "user_story": "As a user, I want to remove connections",
                    "data_items": ["relationship_id"],
                    "assertions": ["Removes relationship"],
                },
                "check": {
                    "feature": "Check relationship exists",
                    "user_story": "As a user, I want to verify connections",
                    "data_items": ["source", "target", "exists"],
                    "assertions": ["Returns existence status"],
                },
                "update": {
                    "feature": "Update relationship",
                    "user_story": "As a user, I want to modify connections",
                    "data_items": ["relationship_id", "metadata"],
                    "assertions": ["Updates relationship"],
                },
            },
        },
        "workflow_tool": {
            "description": "Automated workflows and bulk operations",
            "operations": {
                "setup_project": {
                    "feature": "Automated project setup",
                    "user_story": "As a user, I want quick project creation",
                    "data_items": ["organization_id", "project_name", "template"],
                    "assertions": ["Creates project", "Sets up structure"],
                },
                "import_requirements": {
                    "feature": "Import requirements",
                    "user_story": "As a user, I want to bulk import requirements",
                    "data_items": ["project_id", "source", "data"],
                    "assertions": ["Imports requirements", "Validates format"],
                },
                "setup_test_matrix": {
                    "feature": "Setup test matrix",
                    "user_story": "As a user, I want automated test setup",
                    "data_items": ["project_id", "matrix"],
                    "assertions": ["Creates test matrix"],
                },
                "bulk_status_update": {
                    "feature": "Bulk status update",
                    "user_story": "As a user, I want to update multiple items",
                    "data_items": ["entity_ids", "status"],
                    "assertions": ["Updates multiple entities"],
                },
                "organization_onboarding": {
                    "feature": "Organization onboarding",
                    "user_story": "As a user, I want guided org setup",
                    "data_items": ["organization_id", "template"],
                    "assertions": ["Completes onboarding steps"],
                },
            },
        },
    }

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)

    def report(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
        """Generate comprehensive functionality matrix."""
        lines = [
            "# ATOMS MCP FUNCTIONALITY MATRIX",
            "",
            "## Overview",
            "",
            "Complete validation of all Atoms MCP tools covering:",
            "- **Functionality**: What the tool does",
            "- **User Stories**: Why users need it",
            "- **Data Coverage**: All data items returned",
            "- **Test Results**: Pass/fail status with performance",
            "",
            "---",
            "",
        ]

        # Create results lookup
        results_by_test = {r["test_name"]: r for r in results}

        for tool_name, tool_info in self.TOOL_CAPABILITIES.items():
            lines.append(f"## {tool_name}")
            lines.append(f"**{tool_info['description']}**")
            lines.append("")

            # Operations table
            lines.append("| Operation | Status | Time (ms) | User Story |")
            lines.append("|-----------|--------|-----------|------------|")

            for op_name, op_info in tool_info["operations"].items():
                # Find test result
                test_result = None
                for test_name, result in results_by_test.items():
                    if tool_name in test_name.lower() and op_name in test_name.lower():
                        test_result = result
                        break

                if test_result:
                    if op_info.get("known_issue"):
                        status = "⚠️ Known Issue"
                    elif test_result.get("cached"):
                        status = "💾 Cached"
                    elif test_result["success"]:
                        status = "✅ Pass"
                    else:
                        status = "❌ Fail"
                    duration = f"{test_result['duration_ms']:.0f}"
                else:
                    status = "⏭️ Not Tested"
                    duration = "-"

                user_story = op_info.get("user_story", "").replace("As a user, I want to ", "")
                lines.append(f"| {op_name} | {status} | {duration} | {user_story[:60]} |")

            lines.append("")

        self.output_path.write_text("\n".join(lines))
        print(f"📊 Functionality Matrix: {self.output_path}")


# DetailedErrorReporter has been moved to mcp-QA package
# Import from mcp_qa.reporters.DetailedErrorReporter instead
# Keeping this comment for backward compatibility documentation
