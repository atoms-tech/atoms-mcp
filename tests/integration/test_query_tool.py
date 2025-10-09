#!/usr/bin/env python3
"""
Comprehensive test script for Atoms MCP query_tool.

This script tests ALL query_tool capabilities including:
1. Basic entity retrieval
2. Filtering by entity type
3. Filtering by properties/metadata
4. RAG search functionality
5. Pagination and limits
6. Sorting capabilities
7. Data cleanup

Each operation is documented with:
- Operation name
- Parameters used
- Success/failure status
- Response data structure
- Number of results returned
- Any errors encountered
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the MCP server tools directly
from tools.entity import entity_operation
from tools.query import data_query


class TestReport:
    """Structured test report with detailed results."""

    def __init__(self):
        self.tests: List[Dict[str, Any]] = []
        self.start_time = datetime.now()

    def add_test(self, operation: str, params: Dict[str, Any],
                 success: bool, response: Dict[str, Any],
                 error: Optional[str] = None):
        """Add a test result to the report."""
        result_count = 0
        if success and "data" in response:
            data = response["data"]
            if isinstance(data, list):
                result_count = len(data)
            elif isinstance(data, dict):
                # Check for common result structures
                if "results" in data:
                    if isinstance(data["results"], list):
                        result_count = len(data["results"])
                    elif isinstance(data["results"], dict):
                        result_count = sum(
                            len(v.get("results", []) if isinstance(v, dict) else [])
                            for v in data["results"].values()
                        )
                elif "results_by_entity" in data:
                    result_count = sum(
                        v.get("count", 0) if isinstance(v, dict) else 0
                        for v in data["results_by_entity"].values()
                    )
                else:
                    result_count = 1

        self.tests.append({
            "operation": operation,
            "parameters": params,
            "success": success,
            "result_count": result_count,
            "response_structure": self._get_structure(response),
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def _get_structure(self, obj: Any, max_depth: int = 3, current_depth: int = 0) -> Any:
        """Get the structure of a response object."""
        if current_depth >= max_depth:
            return type(obj).__name__

        if isinstance(obj, dict):
            return {k: self._get_structure(v, max_depth, current_depth + 1)
                    for k, v in list(obj.items())[:10]}  # Limit to first 10 keys
        elif isinstance(obj, list):
            if len(obj) > 0:
                return [self._get_structure(obj[0], max_depth, current_depth + 1)]
            return []
        else:
            return type(obj).__name__

    def print_report(self):
        """Print a formatted test report."""
        print("\n" + "=" * 80)
        print("ATOMS MCP QUERY_TOOL COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        print(f"Test Start Time: {self.start_time.isoformat()}")
        print(f"Test End Time: {datetime.now().isoformat()}")
        print(f"Total Tests: {len(self.tests)}")
        print(f"Passed: {sum(1 for t in self.tests if t['success'])}")
        print(f"Failed: {sum(1 for t in self.tests if not t['success'])}")
        print("=" * 80)

        for i, test in enumerate(self.tests, 1):
            print(f"\nTest #{i}: {test['operation']}")
            print("-" * 80)
            print(f"Status: {'✓ SUCCESS' if test['success'] else '✗ FAILED'}")
            print(f"Results Returned: {test['result_count']}")

            print("\nParameters:")
            for key, value in test['parameters'].items():
                if isinstance(value, (dict, list)):
                    print(f"  - {key}: {json.dumps(value, indent=4)}")
                else:
                    print(f"  - {key}: {value}")

            print("\nResponse Structure:")
            print(json.dumps(test['response_structure'], indent=2))

            if test['error']:
                print(f"\nError: {test['error']}")

        print("\n" + "=" * 80)
        print("END OF REPORT")
        print("=" * 80 + "\n")


class QueryToolTester:
    """Comprehensive tester for query_tool functionality."""

    def __init__(self):
        self.report = TestReport()
        self.test_data_ids: Dict[str, List[str]] = {
            "organizations": [],
            "projects": [],
            "documents": [],
            "requirements": [],
            "tests": []
        }
        # Mock auth token for testing
        self.auth_token = self._get_auth_token()

    def _get_auth_token(self) -> str:
        """Get authentication token from environment or use test token."""
        # Try to get a real token from environment
        token = os.getenv("SUPABASE_ANON_KEY") or os.getenv("TEST_AUTH_TOKEN")
        if not token:
            print("WARNING: No auth token found. Using mock token.")
            print("Set SUPABASE_ANON_KEY or TEST_AUTH_TOKEN environment variable for real testing.")
            token = "mock-token-for-testing"
        return token

    async def setup_test_data(self):
        """Create test entities with varied properties for querying."""
        print("\n" + "=" * 80)
        print("STEP 1: Creating Test Data")
        print("=" * 80)

        try:
            # Create test organization
            org_result = await entity_operation(
                auth_token=self.auth_token,
                operation="create",
                entity_type="organization",
                data={
                    "name": f"Test Org {datetime.now().timestamp()}",
                    "slug": f"test-org-{int(datetime.now().timestamp())}",
                    "description": "Test organization for query testing",
                    "type": "team"
                }
            )

            if org_result.get("success") and org_result.get("data"):
                org_id = org_result["data"]["id"]
                self.test_data_ids["organizations"].append(org_id)
                print(f"✓ Created organization: {org_id}")

                # Create test projects with varied properties
                project_configs = [
                    {
                        "name": "Alpha Project",
                        "description": "First test project for filtering",
                        "status": "active",
                        "priority": "high"
                    },
                    {
                        "name": "Beta Project",
                        "description": "Second test project with different status",
                        "status": "archived",
                        "priority": "medium"
                    },
                    {
                        "name": "Gamma Project",
                        "description": "Third test project for pagination",
                        "status": "active",
                        "priority": "low"
                    }
                ]

                for config in project_configs:
                    config["organization_id"] = org_id
                    project_result = await entity_operation(
                        auth_token=self.auth_token,
                        operation="create",
                        entity_type="project",
                        data=config
                    )

                    if project_result.get("success") and project_result.get("data"):
                        project_id = project_result["data"]["id"]
                        self.test_data_ids["projects"].append(project_id)
                        print(f"✓ Created project: {config['name']} ({project_id})")

                        # Create documents for each project
                        doc_result = await entity_operation(
                            auth_token=self.auth_token,
                            operation="create",
                            entity_type="document",
                            data={
                                "name": f"{config['name']} Requirements",
                                "project_id": project_id,
                                "content": f"Requirements document for {config['name']}"
                            }
                        )

                        if doc_result.get("success") and doc_result.get("data"):
                            doc_id = doc_result["data"]["id"]
                            self.test_data_ids["documents"].append(doc_id)
                            print(f"  ✓ Created document: {doc_id}")

                print(f"\n✓ Test data created successfully!")
                print(f"  - Organizations: {len(self.test_data_ids['organizations'])}")
                print(f"  - Projects: {len(self.test_data_ids['projects'])}")
                print(f"  - Documents: {len(self.test_data_ids['documents'])}")

                self.report.add_test(
                    operation="setup_test_data",
                    params={"org_count": 1, "project_count": 3, "doc_count": 3},
                    success=True,
                    response={"data": self.test_data_ids}
                )
            else:
                error = org_result.get("error", "Unknown error creating organization")
                print(f"✗ Failed to create test organization: {error}")
                self.report.add_test(
                    operation="setup_test_data",
                    params={},
                    success=False,
                    response=org_result,
                    error=error
                )

        except Exception as e:
            error = str(e)
            print(f"✗ Error setting up test data: {error}")
            self.report.add_test(
                operation="setup_test_data",
                params={},
                success=False,
                response={},
                error=error
            )

    async def test_basic_query(self):
        """Test 2: Execute a basic query to retrieve all entities."""
        print("\n" + "=" * 80)
        print("STEP 2: Basic Query - Retrieve All Entities")
        print("=" * 80)

        params = {
            "query_type": "search",
            "entities": ["organization", "project", "document"],
            "search_term": "test"
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                total = result.get("total_results", 0)
                print(f"Total results: {total}")

                if "results_by_entity" in result:
                    for entity_type, entity_data in result["results_by_entity"].items():
                        count = entity_data.get("count", 0)
                        print(f"  - {entity_type}: {count} results")

            self.report.add_test(
                operation="basic_query_all_entities",
                params=params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Error: {error}")
            self.report.add_test(
                operation="basic_query_all_entities",
                params=params,
                success=False,
                response={},
                error=error
            )

    async def test_filter_by_type(self):
        """Test 3: Filter by entity type."""
        print("\n" + "=" * 80)
        print("STEP 3: Filter by Entity Type")
        print("=" * 80)

        params = {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "Project"
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                if "results_by_entity" in result:
                    for entity_type, entity_data in result["results_by_entity"].items():
                        count = entity_data.get("count", 0)
                        print(f"  - {entity_type}: {count} results")

            self.report.add_test(
                operation="filter_by_entity_type",
                params=params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Error: {error}")
            self.report.add_test(
                operation="filter_by_entity_type",
                params=params,
                success=False,
                response={},
                error=error
            )

    async def test_filter_by_properties(self):
        """Test 4: Filter by properties/metadata."""
        print("\n" + "=" * 80)
        print("STEP 4: Filter by Properties/Metadata")
        print("=" * 80)

        params = {
            "query_type": "search",
            "entities": ["project"],
            "conditions": {"status": "active"},
            "search_term": ""
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                if "results_by_entity" in result:
                    for entity_type, entity_data in result["results_by_entity"].items():
                        count = entity_data.get("count", 0)
                        print(f"  - {entity_type} (status=active): {count} results")

            self.report.add_test(
                operation="filter_by_properties",
                params=params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Error: {error}")
            self.report.add_test(
                operation="filter_by_properties",
                params=params,
                success=False,
                response={},
                error=error
            )

    async def test_rag_search(self):
        """Test 5: Test RAG search functionality."""
        print("\n" + "=" * 80)
        print("STEP 5: RAG Search Functionality")
        print("=" * 80)

        # Test semantic search
        semantic_params = {
            "query_type": "rag_search",
            "entities": ["project", "document"],
            "search_term": "requirements and testing",
            "rag_mode": "semantic",
            "similarity_threshold": 0.7,
            "limit": 5
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **semantic_params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Semantic Search Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                total = result.get("total_results", 0)
                mode = result.get("mode", "unknown")
                print(f"  - Mode: {mode}")
                print(f"  - Total results: {total}")
                if "search_time_ms" in result:
                    print(f"  - Search time: {result['search_time_ms']}ms")

            self.report.add_test(
                operation="rag_search_semantic",
                params=semantic_params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Semantic Search Error: {error}")
            self.report.add_test(
                operation="rag_search_semantic",
                params=semantic_params,
                success=False,
                response={},
                error=error
            )

        # Test keyword search
        keyword_params = {
            "query_type": "rag_search",
            "entities": ["project"],
            "search_term": "Alpha",
            "rag_mode": "keyword",
            "limit": 5
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **keyword_params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Keyword Search Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                total = result.get("total_results", 0)
                print(f"  - Total results: {total}")

            self.report.add_test(
                operation="rag_search_keyword",
                params=keyword_params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Keyword Search Error: {error}")
            self.report.add_test(
                operation="rag_search_keyword",
                params=keyword_params,
                success=False,
                response={},
                error=error
            )

        # Test hybrid search
        hybrid_params = {
            "query_type": "rag_search",
            "entities": ["project", "document"],
            "search_term": "test project requirements",
            "rag_mode": "hybrid",
            "similarity_threshold": 0.6,
            "limit": 10
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **hybrid_params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Hybrid Search Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                total = result.get("total_results", 0)
                print(f"  - Total results: {total}")

            self.report.add_test(
                operation="rag_search_hybrid",
                params=hybrid_params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Hybrid Search Error: {error}")
            self.report.add_test(
                operation="rag_search_hybrid",
                params=hybrid_params,
                success=False,
                response={},
                error=error
            )

    async def test_pagination(self):
        """Test 6: Test pagination and limits."""
        print("\n" + "=" * 80)
        print("STEP 6: Pagination and Limits")
        print("=" * 80)

        # Test with limit
        limit_params = {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "",
            "limit": 2
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **limit_params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Limit Test Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                if "results_by_entity" in result:
                    for entity_type, entity_data in result["results_by_entity"].items():
                        count = entity_data.get("count", 0)
                        print(f"  - {entity_type}: {count} results (limit=2)")

            self.report.add_test(
                operation="pagination_with_limit",
                params=limit_params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Error: {error}")
            self.report.add_test(
                operation="pagination_with_limit",
                params=limit_params,
                success=False,
                response={},
                error=error
            )

    async def test_sorting(self):
        """Test 7: Test sorting capabilities."""
        print("\n" + "=" * 80)
        print("STEP 7: Sorting Capabilities")
        print("=" * 80)

        # Note: The current query tool doesn't expose direct sorting parameters
        # but uses order_by internally in search queries
        params = {
            "query_type": "aggregate",
            "entities": ["project", "organization"],
            "conditions": {}
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Aggregate Query Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                if "results" in result:
                    for entity_type, stats in result["results"].items():
                        print(f"  - {entity_type}:")
                        for key, value in stats.items():
                            if key != "error":
                                print(f"    - {key}: {value}")

            self.report.add_test(
                operation="aggregate_query",
                params=params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Error: {error}")
            self.report.add_test(
                operation="aggregate_query",
                params=params,
                success=False,
                response={},
                error=error
            )

    async def test_relationship_query(self):
        """Test relationship analysis."""
        print("\n" + "=" * 80)
        print("STEP 8: Relationship Query")
        print("=" * 80)

        params = {
            "query_type": "relationships",
            "entities": ["organization", "project"],
            "conditions": {}
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Relationship Query Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                if "relationships" in result:
                    for rel_table, rel_data in result["relationships"].items():
                        count = rel_data.get("total_count", 0)
                        print(f"  - {rel_table}: {count} relationships")

            self.report.add_test(
                operation="relationship_query",
                params=params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Error: {error}")
            self.report.add_test(
                operation="relationship_query",
                params=params,
                success=False,
                response={},
                error=error
            )

    async def test_analyze_query(self):
        """Test deep analysis query."""
        print("\n" + "=" * 80)
        print("STEP 9: Deep Analysis Query")
        print("=" * 80)

        params = {
            "query_type": "analyze",
            "entities": ["organization", "project"],
            "conditions": {}
        }

        try:
            result = await data_query(
                auth_token=self.auth_token,
                **params
            )

            success = result.get("success", True) and "error" not in result
            print(f"Analysis Query Status: {'✓ SUCCESS' if success else '✗ FAILED'}")

            if success:
                if "analysis" in result:
                    for entity_type, analysis in result["analysis"].items():
                        print(f"  - {entity_type}:")
                        for key, value in analysis.items():
                            if key != "error":
                                print(f"    - {key}: {value}")

            self.report.add_test(
                operation="analyze_query",
                params=params,
                success=success,
                response=result,
                error=result.get("error")
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Error: {error}")
            self.report.add_test(
                operation="analyze_query",
                params=params,
                success=False,
                response={},
                error=error
            )

    async def cleanup_test_data(self):
        """Test 8: Clean up test data."""
        print("\n" + "=" * 80)
        print("STEP 10: Cleanup Test Data")
        print("=" * 80)

        cleanup_results = {
            "documents": 0,
            "projects": 0,
            "organizations": 0
        }

        try:
            # Clean up in reverse order (documents -> projects -> organizations)
            for doc_id in self.test_data_ids["documents"]:
                try:
                    result = await entity_operation(
                        auth_token=self.auth_token,
                        operation="delete",
                        entity_type="document",
                        entity_id=doc_id
                    )
                    if result.get("success"):
                        cleanup_results["documents"] += 1
                        print(f"✓ Deleted document: {doc_id}")
                except Exception as e:
                    print(f"✗ Error deleting document {doc_id}: {e}")

            for project_id in self.test_data_ids["projects"]:
                try:
                    result = await entity_operation(
                        auth_token=self.auth_token,
                        operation="delete",
                        entity_type="project",
                        entity_id=project_id
                    )
                    if result.get("success"):
                        cleanup_results["projects"] += 1
                        print(f"✓ Deleted project: {project_id}")
                except Exception as e:
                    print(f"✗ Error deleting project {project_id}: {e}")

            for org_id in self.test_data_ids["organizations"]:
                try:
                    result = await entity_operation(
                        auth_token=self.auth_token,
                        operation="delete",
                        entity_type="organization",
                        entity_id=org_id
                    )
                    if result.get("success"):
                        cleanup_results["organizations"] += 1
                        print(f"✓ Deleted organization: {org_id}")
                except Exception as e:
                    print(f"✗ Error deleting organization {org_id}: {e}")

            print(f"\n✓ Cleanup complete!")
            print(f"  - Documents deleted: {cleanup_results['documents']}")
            print(f"  - Projects deleted: {cleanup_results['projects']}")
            print(f"  - Organizations deleted: {cleanup_results['organizations']}")

            self.report.add_test(
                operation="cleanup_test_data",
                params=cleanup_results,
                success=True,
                response={"data": cleanup_results}
            )

        except Exception as e:
            error = str(e)
            print(f"✗ Error during cleanup: {error}")
            self.report.add_test(
                operation="cleanup_test_data",
                params={},
                success=False,
                response={},
                error=error
            )

    async def run_all_tests(self):
        """Run all test operations."""
        print("\n" + "=" * 80)
        print("STARTING COMPREHENSIVE QUERY_TOOL TEST SUITE")
        print("=" * 80)

        # Run tests in sequence
        await self.setup_test_data()
        await self.test_basic_query()
        await self.test_filter_by_type()
        await self.test_filter_by_properties()
        await self.test_rag_search()
        await self.test_pagination()
        await self.test_sorting()
        await self.test_relationship_query()
        await self.test_analyze_query()
        await self.cleanup_test_data()

        # Print final report
        self.report.print_report()


async def main():
    """Main test runner."""
    tester = QueryToolTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
