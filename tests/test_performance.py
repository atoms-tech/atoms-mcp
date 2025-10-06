"""
Performance Benchmarking Tests for Atoms MCP

This test suite validates performance characteristics:
- Response time benchmarks for each tool
- Throughput testing under load
- Concurrent request handling
- Large dataset operations
- Memory usage patterns
- Database query performance

Run with: pytest tests/test_performance.py -v -s
"""

from __future__ import annotations

import os
import time
import uuid
import asyncio
import statistics
from typing import Any, Dict, List, Tuple
from datetime import datetime, timezone

import httpx
import pytest
from supabase import create_client

MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

pytestmark = [pytest.mark.asyncio, pytest.mark.performance]


# Performance thresholds (in seconds)
THRESHOLDS = {
    "entity_tool_create": 2.0,
    "entity_tool_read": 1.0,
    "entity_tool_update": 2.0,
    "entity_tool_delete": 2.0,
    "entity_tool_list": 3.0,
    "workspace_tool_get_context": 1.0,
    "workspace_tool_set_context": 2.0,
    "workspace_tool_list_workspaces": 3.0,
    "relationship_tool_link": 2.0,
    "relationship_tool_list": 2.0,
    "workflow_tool_setup_project": 10.0,
    "query_tool_search": 3.0,
    "query_tool_aggregate": 3.0,
    "query_tool_rag_search": 5.0,
}


class PerformanceMetrics:
    """Collect and analyze performance metrics."""

    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}

    def record(self, operation: str, duration: float):
        """Record a performance measurement."""
        if operation not in self.measurements:
            self.measurements[operation] = []
        self.measurements[operation].append(duration)

    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for an operation."""
        if operation not in self.measurements:
            return {}

        durations = self.measurements[operation]
        return {
            "count": len(durations),
            "min": min(durations),
            "max": max(durations),
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
            "stdev": statistics.stdev(durations) if len(durations) > 1 else 0,
            "p95": statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
            "p99": statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        report = {
            "summary": {
                "total_operations": sum(len(m) for m in self.measurements.values()),
                "operation_types": len(self.measurements),
            },
            "operations": {},
            "threshold_violations": []
        }

        for operation, durations in self.measurements.items():
            stats = self.get_stats(operation)
            report["operations"][operation] = stats

            # Check threshold violations
            threshold = THRESHOLDS.get(operation)
            if threshold and stats.get("p95", 0) > threshold:
                report["threshold_violations"].append({
                    "operation": operation,
                    "threshold": threshold,
                    "p95": stats["p95"],
                    "violation": stats["p95"] - threshold
                })

        return report


@pytest.fixture(scope="module")
def perf_metrics():
    """Provide shared performance metrics instance."""
    return PerformanceMetrics()


@pytest.fixture(scope="module")
def mcp_client(check_server_running, shared_supabase_jwt, perf_metrics):
    """Return MCP client with performance tracking."""
    base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
    headers = {
        "Authorization": f"Bearer {shared_supabase_jwt}",
        "Content-Type": "application/json",
    }

    async def call_tool(tool_name: str, params: Dict[str, Any], track_perf: bool = True) -> Tuple[Dict[str, Any], float]:
        """Call MCP tool and track performance."""
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": f"tools/{tool_name}",
            "params": params,
        }

        start_time = time.time()

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(base_url, json=payload, headers=headers)
                duration = time.time() - start_time

                if track_perf:
                    operation_key = f"{tool_name}_{params.get('operation', params.get('workflow', params.get('query_type', 'call')))}"
                    perf_metrics.record(operation_key, duration)

                if response.status_code != 200:
                    return {"success": False, "error": f"HTTP {response.status_code}"}, duration

                body = response.json()
                if "result" in body:
                    return body["result"], duration

                return {"success": False, "error": "No result"}, duration

            except Exception as e:
                duration = time.time() - start_time
                return {"success": False, "error": str(e)}, duration

    return call_tool


# ============================================================================
# Individual Tool Performance Tests
# ============================================================================

class TestEntityToolPerformance:
    """Test entity_tool performance."""

    @pytest.mark.asyncio
    async def test_entity_crud_performance(self, mcp_client, perf_metrics):
        """Benchmark entity CRUD operations."""
        print("\n=== Entity CRUD Performance ===")

        # Create
        org_slug = f"perf-test-{uuid.uuid4().hex[:8]}"
        result, duration = await mcp_client("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "Performance Test Org",
                "slug": org_slug,
                "type": "team"
            }
        })

        assert result.get("success") is True
        org_id = result["data"]["id"]
        print(f"  Create: {duration:.3f}s")

        # Read
        result, duration = await mcp_client("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": org_id
        })

        assert result.get("success") is True
        print(f"  Read:   {duration:.3f}s")

        # Update
        result, duration = await mcp_client("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": org_id,
            "data": {"description": "Updated for performance test"}
        })

        assert result.get("success") is True
        print(f"  Update: {duration:.3f}s")

        # List
        result, duration = await mcp_client("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "limit": 50
        })

        assert result.get("success") is True
        print(f"  List:   {duration:.3f}s")

        # Delete
        result, duration = await mcp_client("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": org_id
        })

        assert result.get("success") is True
        print(f"  Delete: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_batch_create_performance(self, mcp_client):
        """Test performance of creating multiple entities."""
        print("\n=== Batch Create Performance ===")

        # Create org first
        org_result, _ = await mcp_client("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "Batch Test Org",
                "slug": f"batch-{uuid.uuid4().hex[:8]}"
            }
        })

        org_id = org_result["data"]["id"]

        # Create 10 projects sequentially
        start_time = time.time()
        project_ids = []

        for i in range(10):
            result, _ = await mcp_client("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Batch Project {i}",
                    "organization_id": org_id
                }
            }, track_perf=False)

            if result.get("success"):
                project_ids.append(result["data"]["id"])

        sequential_duration = time.time() - start_time
        print(f"  Sequential (10 projects): {sequential_duration:.3f}s ({sequential_duration/10:.3f}s avg)")

        # Create 10 projects concurrently
        async def create_project(index: int):
            result, _ = await mcp_client("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Concurrent Project {index}",
                    "organization_id": org_id
                }
            }, track_perf=False)
            return result

        start_time = time.time()
        results = await asyncio.gather(*[create_project(i) for i in range(10)])
        concurrent_duration = time.time() - start_time

        print(f"  Concurrent (10 projects): {concurrent_duration:.3f}s ({concurrent_duration/10:.3f}s avg)")
        print(f"  Speedup: {sequential_duration/concurrent_duration:.1f}x")


class TestWorkspaceToolPerformance:
    """Test workspace_tool performance."""

    @pytest.mark.asyncio
    async def test_workspace_operations_performance(self, mcp_client):
        """Benchmark workspace operations."""
        print("\n=== Workspace Operations Performance ===")

        # Get context
        result, duration = await mcp_client("workspace_tool", {
            "operation": "get_context"
        })

        print(f"  Get Context:     {duration:.3f}s")

        # List workspaces
        result, duration = await mcp_client("workspace_tool", {
            "operation": "list_workspaces",
            "limit": 100
        })

        print(f"  List Workspaces: {duration:.3f}s")

        # Get defaults
        result, duration = await mcp_client("workspace_tool", {
            "operation": "get_defaults"
        })

        print(f"  Get Defaults:    {duration:.3f}s")


class TestQueryToolPerformance:
    """Test query_tool performance."""

    @pytest.mark.asyncio
    async def test_search_performance(self, mcp_client):
        """Benchmark search operations."""
        print("\n=== Search Performance ===")

        # Simple search
        result, duration = await mcp_client("query_tool", {
            "query_type": "search",
            "entities": ["organization", "project"],
            "search_term": "test",
            "limit": 20
        })

        print(f"  Keyword Search: {duration:.3f}s")

        # Aggregate query
        result, duration = await mcp_client("query_tool", {
            "query_type": "aggregate",
            "entities": ["organization", "project"]
        })

        print(f"  Aggregate:      {duration:.3f}s")

        # RAG search (if available)
        result, duration = await mcp_client("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "authentication security",
            "rag_mode": "auto",
            "limit": 10
        })

        print(f"  RAG Search:     {duration:.3f}s")


class TestWorkflowPerformance:
    """Test workflow_tool performance."""

    @pytest.mark.asyncio
    async def test_workflow_performance(self, mcp_client):
        """Benchmark workflow execution."""
        print("\n=== Workflow Performance ===")

        # Create org for workflow
        org_result, _ = await mcp_client("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "Workflow Perf Test",
                "slug": f"wf-perf-{uuid.uuid4().hex[:8]}"
            }
        })

        org_id = org_result["data"]["id"]

        # Setup project workflow
        result, duration = await mcp_client("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Performance Test Project",
                "organization_id": org_id,
                "initial_documents": ["Requirements", "Design", "Test Plan"]
            }
        })

        print(f"  Setup Project: {duration:.3f}s")

        if result.get("success"):
            steps = result.get("data", {}).get("steps", [])
            print(f"    Steps completed: {len(steps)}")
            for step in steps:
                if step.get("duration"):
                    print(f"    - {step['step']}: {step.get('duration', 'N/A')}")


# ============================================================================
# Load and Stress Tests
# ============================================================================

class TestLoadPerformance:
    """Test performance under load."""

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, mcp_client):
        """Test concurrent read performance."""
        print("\n=== Concurrent Read Performance ===")

        # Create test org
        org_result, _ = await mcp_client("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "Concurrent Read Test",
                "slug": f"concurrent-{uuid.uuid4().hex[:8]}"
            }
        })

        org_id = org_result["data"]["id"]

        # Perform 50 concurrent reads
        async def read_org():
            result, duration = await mcp_client("entity_tool", {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": org_id
            }, track_perf=False)
            return duration

        start_time = time.time()
        durations = await asyncio.gather(*[read_org() for _ in range(50)])
        total_duration = time.time() - start_time

        print(f"  50 concurrent reads:")
        print(f"    Total time:   {total_duration:.3f}s")
        print(f"    Avg per read: {statistics.mean(durations):.3f}s")
        print(f"    Min:          {min(durations):.3f}s")
        print(f"    Max:          {max(durations):.3f}s")
        print(f"    Throughput:   {50/total_duration:.1f} req/s")

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, mcp_client):
        """Test concurrent write performance."""
        print("\n=== Concurrent Write Performance ===")

        # Create test org
        org_result, _ = await mcp_client("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "Concurrent Write Test",
                "slug": f"concurrent-write-{uuid.uuid4().hex[:8]}"
            }
        })

        org_id = org_result["data"]["id"]

        # Perform 20 concurrent project creations
        async def create_project(index: int):
            result, duration = await mcp_client("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Concurrent Project {index}",
                    "organization_id": org_id
                }
            }, track_perf=False)
            return duration, result.get("success")

        start_time = time.time()
        results = await asyncio.gather(*[create_project(i) for i in range(20)])
        total_duration = time.time() - start_time

        durations = [r[0] for r in results]
        successes = sum(1 for r in results if r[1])

        print(f"  20 concurrent creates:")
        print(f"    Total time:    {total_duration:.3f}s")
        print(f"    Successes:     {successes}/20")
        print(f"    Avg per create: {statistics.mean(durations):.3f}s")
        print(f"    Throughput:    {20/total_duration:.1f} req/s")

    @pytest.mark.asyncio
    async def test_pagination_performance(self, mcp_client):
        """Test pagination performance with large datasets."""
        print("\n=== Pagination Performance ===")

        # Test different page sizes
        page_sizes = [10, 50, 100, 500]

        for page_size in page_sizes:
            result, duration = await mcp_client("entity_tool", {
                "operation": "list",
                "entity_type": "organization",
                "limit": page_size,
                "offset": 0
            }, track_perf=False)

            count = len(result.get("data", []))
            print(f"  Page size {page_size:3d}: {duration:.3f}s ({count} results)")


# ============================================================================
# Report Generation
# ============================================================================

class TestPerformanceReport:
    """Generate performance test report."""

    @pytest.mark.asyncio
    async def test_generate_performance_report(self, perf_metrics):
        """Generate and display performance report."""
        print("\n" + "="*80)
        print("PERFORMANCE TEST REPORT")
        print("="*80)

        report = perf_metrics.generate_report()

        # Summary
        print(f"\n{'SUMMARY':^80}")
        print("-"*80)
        print(f"Total Operations:  {report['summary']['total_operations']}")
        print(f"Operation Types:   {report['summary']['operation_types']}")

        # Operations
        print(f"\n{'OPERATION PERFORMANCE':^80}")
        print("-"*80)
        print(f"{'Operation':<40} {'Count':>6} {'Mean':>8} {'P95':>8} {'P99':>8}")
        print("-"*80)

        for operation, stats in sorted(report['operations'].items()):
            threshold = THRESHOLDS.get(operation, float('inf'))
            p95_status = "❌" if stats.get('p95', 0) > threshold else "✅"

            print(f"{operation:<40} {stats['count']:>6} {stats['mean']:>7.3f}s {stats['p95']:>7.3f}s {stats['p99']:>7.3f}s {p95_status}")

        # Threshold Violations
        if report['threshold_violations']:
            print(f"\n{'THRESHOLD VIOLATIONS':^80}")
            print("-"*80)
            for violation in report['threshold_violations']:
                print(f"❌ {violation['operation']}")
                print(f"   Threshold: {violation['threshold']:.3f}s")
                print(f"   P95:       {violation['p95']:.3f}s")
                print(f"   Violation: +{violation['violation']:.3f}s")
        else:
            print(f"\n{'THRESHOLD VIOLATIONS':^80}")
            print("-"*80)
            print("✅ No threshold violations detected")

        print("\n" + "="*80)
        print("END OF PERFORMANCE REPORT")
        print("="*80 + "\n")

        # Save report
        import json
        report_path = "/Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/tests/performance_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📊 Detailed report saved to: {report_path}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
