#!/usr/bin/env python3
"""Generate comprehensive test report for query_tool."""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

import httpx
from supabase import create_client

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Configuration
MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")


class QueryToolTester:
    """Comprehensive query tool testing and reporting."""

    def __init__(self, base_url: str, mcp_path: str, auth_token: str):
        self.base_url = f"{base_url.rstrip('/')}{mcp_path}"
        self.auth_token = auth_token
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "query_types": {},
            "rag_modes": {},
            "performance": {},
            "errors": [],
            "summary": {}
        }

    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make MCP tool call."""
        payload = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "tools/query_tool",
            "params": params
        }

        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            start = time.time()
            response = await client.post(self.base_url, json=payload, headers=headers)
            elapsed = (time.time() - start) * 1000

            if response.status_code == 200:
                body = response.json()
                result = body.get("result", {})
                return {**result, "_response_time_ms": elapsed}
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "_response_time_ms": elapsed
                }

    async def test_query_type(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific query type."""
        print(f"  Testing {query_type}...", end=" ")

        result = await self.call_tool({
            "query_type": query_type,
            **params
        })

        success = result.get("success", False)
        response_time = result.get("_response_time_ms", 0)

        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} ({response_time:.0f}ms)")

        return {
            "success": success,
            "response_time_ms": response_time,
            "has_data": "data" in result,
            "error": result.get("error"),
            "result_preview": str(result.get("data", ""))[:100]
        }

    async def test_rag_mode(self, mode: str, query: str) -> Dict[str, Any]:
        """Test a specific RAG mode."""
        print(f"  Testing RAG mode '{mode}'...", end=" ")

        result = await self.call_tool({
            "query_type": "rag_search",
            "entities": ["requirement", "document"],
            "search_term": query,
            "rag_mode": mode,
            "limit": 5
        })

        success = result.get("success", False)
        response_time = result.get("_response_time_ms", 0)
        data = result.get("data", {})
        result_count = len(data.get("results", []))
        mode_used = data.get("mode", "unknown")

        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {result_count} results, mode={mode_used} ({response_time:.0f}ms)")

        return {
            "success": success,
            "response_time_ms": response_time,
            "mode_used": mode_used,
            "result_count": result_count,
            "search_time_ms": data.get("search_time_ms", 0),
            "error": result.get("error")
        }

    async def run_all_tests(self):
        """Run all comprehensive tests."""
        print("\n" + "="*80)
        print("QUERY TOOL COMPREHENSIVE TEST REPORT")
        print("="*80)
        print(f"\nTimestamp: {self.results['timestamp']}")
        print(f"Server: {self.base_url}")

        # Test all query types
        print("\n[1/3] Testing Query Types")
        print("-" * 40)

        query_type_tests = [
            ("search", {
                "entities": ["organization", "project"],
                "search_term": "test"
            }),
            ("aggregate", {
                "entities": ["organization", "project", "requirement"]
            }),
            ("analyze", {
                "entities": ["organization", "project", "requirement"]
            }),
            ("relationships", {
                "entities": ["organization", "project"]
            }),
            ("rag_search", {
                "entities": ["requirement"],
                "search_term": "authentication security",
                "rag_mode": "auto"
            }),
            ("similarity", {
                "entities": ["requirement"],
                "content": "user authentication and security"
            })
        ]

        for query_type, params in query_type_tests:
            self.results["query_types"][query_type] = await self.test_query_type(
                query_type, params
            )

        # Test RAG modes
        print("\n[2/3] Testing RAG Modes")
        print("-" * 40)

        rag_modes = ["auto", "semantic", "keyword", "hybrid"]
        test_query = "secure user authentication and data encryption"

        for mode in rag_modes:
            self.results["rag_modes"][mode] = await self.test_rag_mode(mode, test_query)

        # Performance benchmarks
        print("\n[3/3] Performance Benchmarks")
        print("-" * 40)

        performance_tests = [
            ("Search Performance", "search", {
                "entities": ["organization", "project", "document"],
                "search_term": "test",
                "limit": 20
            }),
            ("RAG Search Performance", "rag_search", {
                "entities": ["requirement", "document"],
                "search_term": "authentication security performance",
                "rag_mode": "semantic",
                "limit": 10
            }),
            ("Aggregate Performance", "aggregate", {
                "entities": ["organization", "project", "requirement"]
            })
        ]

        for test_name, query_type, params in performance_tests:
            print(f"  {test_name}...", end=" ")
            result = await self.call_tool({"query_type": query_type, **params})
            response_time = result.get("_response_time_ms", 0)
            success = result.get("success", False)

            status = "✓" if success else "✗"
            print(f"{status} {response_time:.0f}ms")

            self.results["performance"][test_name] = {
                "success": success,
                "response_time_ms": response_time
            }

        # Generate summary
        self.generate_summary()

        # Print report
        self.print_report()

        # Save to file
        self.save_report()

    def generate_summary(self):
        """Generate test summary."""
        total_query_types = len(self.results["query_types"])
        passed_query_types = sum(
            1 for r in self.results["query_types"].values() if r["success"]
        )

        total_rag_modes = len(self.results["rag_modes"])
        passed_rag_modes = sum(
            1 for r in self.results["rag_modes"].values() if r["success"]
        )

        total_performance = len(self.results["performance"])
        passed_performance = sum(
            1 for r in self.results["performance"].values() if r["success"]
        )

        total_tests = total_query_types + total_rag_modes + total_performance
        passed_tests = passed_query_types + passed_rag_modes + passed_performance

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "pass_rate": f"{(passed_tests/total_tests*100):.2f}%" if total_tests > 0 else "0%",
            "query_types": {
                "total": total_query_types,
                "passed": passed_query_types
            },
            "rag_modes": {
                "total": total_rag_modes,
                "passed": passed_rag_modes
            },
            "performance": {
                "total": total_performance,
                "passed": passed_performance
            }
        }

    def print_report(self):
        """Print formatted report."""
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)

        summary = self.results["summary"]
        print(f"\nOverall Results:")
        print(f"  Total Tests:    {summary['total_tests']}")
        print(f"  Passed:         {summary['passed_tests']} ({summary['pass_rate']})")
        print(f"  Failed:         {summary['failed_tests']}")

        print(f"\nQuery Type Results ({summary['query_types']['passed']}/{summary['query_types']['total']}):")
        for qtype, data in self.results["query_types"].items():
            status = "✓ PASS" if data["success"] else "✗ FAIL"
            print(f"  {qtype:15} {status:8} ({data['response_time_ms']:.0f}ms)")

        print(f"\nRAG Mode Results ({summary['rag_modes']['passed']}/{summary['rag_modes']['total']}):")
        for mode, data in self.results["rag_modes"].items():
            status = "✓ PASS" if data["success"] else "✗ FAIL"
            print(f"  {mode:10} {status:8} - {data['result_count']} results, "
                  f"mode={data['mode_used']} ({data['response_time_ms']:.0f}ms)")

        print(f"\nPerformance Benchmarks ({summary['performance']['passed']}/{summary['performance']['total']}):")
        for test_name, data in self.results["performance"].items():
            status = "✓ PASS" if data["success"] else "✗ FAIL"
            print(f"  {test_name:25} {status:8} ({data['response_time_ms']:.0f}ms)")

        # RAG Mode Comparison
        print("\n" + "-"*80)
        print("RAG MODE COMPARISON")
        print("-"*80)
        print(f"\n{'Mode':<10} {'Results':<10} {'Response Time':<15} {'Search Time':<15} {'Mode Used':<15}")
        print("-"*80)
        for mode, data in self.results["rag_modes"].items():
            if data["success"]:
                print(f"{mode:<10} {data['result_count']:<10} "
                      f"{data['response_time_ms']:.0f}ms{'':<10} "
                      f"{data['search_time_ms']:.0f}ms{'':<10} "
                      f"{data['mode_used']:<15}")

        print("\n" + "="*80)

        # Determine overall status
        if summary["failed_tests"] == 0:
            print("✓ ALL TESTS PASSED")
        else:
            print(f"✗ {summary['failed_tests']} TEST(S) FAILED")

        print("="*80 + "\n")

    def save_report(self):
        """Save report to JSON file."""
        filename = f"query_tool_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"Report saved to: {filepath}")


async def main():
    """Main test runner."""
    # Authenticate
    print("Authenticating with Supabase...")
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("Error: Supabase environment variables not set")
        sys.exit(1)

    client = create_client(supabase_url, supabase_key)
    auth_response = client.auth.sign_in_with_password({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })

    if not auth_response.session or not auth_response.session.access_token:
        print("Error: Could not authenticate")
        sys.exit(1)

    auth_token = auth_response.session.access_token
    print("✓ Authentication successful")

    # Check server
    print("Checking MCP server...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            response = await http_client.get(f"{MCP_BASE_URL}/health")
            if response.status_code != 200:
                print(f"Error: Server returned {response.status_code}")
                sys.exit(1)
        print("✓ Server is running")
    except Exception as e:
        print(f"Error: Could not connect to server - {e}")
        sys.exit(1)

    # Run tests
    tester = QueryToolTester(MCP_BASE_URL, MCP_PATH, auth_token)
    await tester.run_all_tests()

    # Exit with appropriate code
    if tester.results["summary"]["failed_tests"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
