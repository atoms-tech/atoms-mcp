#!/usr/bin/env python3
"""Headless MCP client for comprehensive Atoms MCP testing.

This client:
1. Connects to production MCP endpoint (mcp.atoms.tech/api/mcp)
2. Handles OAuth authentication flow (opens browser for user login)
3. Executes all test cases with async parallel execution where possible
4. Uses PERT-style dependency flow for dependent tests
5. Collects detailed performance metrics
6. Generates comprehensive test reports

Usage:
    python test_mcp_client_headless.py
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import json
import os

from fastmcp import Client
from fastmcp.client.auth import OAuth

from test_cases import TestCases
from test_report_generator import TestReportGenerator


class MCPTestClient:
    """Headless MCP test client with OAuth and parallel execution."""

    MCP_ENDPOINT = "https://mcp.atoms.tech/api/mcp"

    def __init__(self):
        self.client: Optional[Client] = None
        self.oauth: Optional[OAuth] = None
        self.user_info: Optional[Dict[str, Any]] = None
        self.report = TestReportGenerator()
        self.test_cases = TestCases()

        # Track created entities for dependency chain
        self.created_entities: Dict[str, str] = {}

    async def connect_and_authenticate(self) -> bool:
        """Connect to MCP server and handle OAuth authentication."""
        print(f"\n📡 Connecting to {self.MCP_ENDPOINT}...")
        print("🔐 Initiating OAuth authentication flow...")
        print("\n⏳ This will open your browser for authentication.")
        print("   Please log in and grant access when prompted.\n")

        try:
            # Create OAuth helper with configuration
            # AuthKit doesn't use traditional scopes - pass empty or None
            self.oauth = OAuth(
                mcp_url=self.MCP_ENDPOINT,
                client_name="Atoms MCP Test Client"
                # No scopes - AuthKit handles permissions differently
            )

            # Create FastMCP client with OAuth
            self.client = Client(self.MCP_ENDPOINT, auth=self.oauth)

            # Initialize connection - this triggers OAuth flow if needed
            print("🌐 Opening browser for authentication...")
            await self.client.__aenter__()

            print("✅ Authentication successful!")
            self.report.set_connection_info(self.MCP_ENDPOINT, "connected")
            self.report.set_auth_info("authenticated", user="authenticated_user")

            # Verify connection by listing tools
            tools = await self.client.list_tools()
            print(f"📋 Available tools: {len(tools.tools)} found")
            for tool in tools.tools:
                print(f"   - {tool.name}")

            return True

        except Exception as e:
            print(f"❌ Connection/Authentication failed: {e}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            self.report.set_connection_info(self.MCP_ENDPOINT, "failed", str(e))
            self.report.set_auth_info("failed", error=str(e))
            return False

    async def _call_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an MCP tool using FastMCP client.

        Args:
            tool_name: Name of the tool to call
            params: Tool parameters

        Returns:
            Tool response with timing metadata
        """
        start_time = time.perf_counter()

        try:
            # Call tool using FastMCP client
            result = await self.client.call_tool(tool_name, arguments=params)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Parse the result
            if result.content:
                # Extract text content from result
                text_content = result.content[0].text if result.content else "{}"

                try:
                    parsed_result = json.loads(text_content)
                    parsed_result["_client_timing_ms"] = duration_ms
                    return parsed_result
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": f"Failed to parse tool response: {text_content[:100]}",
                        "_client_timing_ms": duration_ms,
                        "_raw_response": text_content
                    }
            else:
                return {
                    "success": False,
                    "error": "Empty response from tool",
                    "_client_timing_ms": duration_ms
                }

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "_client_timing_ms": duration_ms
            }

    async def run_test_case(
        self,
        test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single test case.

        Args:
            test_case: Test case definition

        Returns:
            Test result with timing and validation
        """
        test_name = test_case["name"]
        tool = test_case["tool"]
        params = test_case["params"].copy()
        expected = test_case.get("expected", {})
        known_issue = test_case.get("known_issue", False)
        skip_if_no_org = test_case.get("skip_if_no_org", False)

        print(f"\n🧪 Running: {test_name}")
        print(f"   Tool: {tool}")

        # Check skip conditions
        if skip_if_no_org and not self.created_entities.get("organization_id"):
            print(f"   ⏭️  Skipped: No organization created")
            self.report.add_test_result(
                test_name=test_name,
                tool=tool,
                params=params,
                success=False,
                duration_ms=0.0,
                skipped=True,
                skip_reason="No organization available"
            )
            return {"skipped": True}

        # Replace placeholder IDs with actual created entity IDs
        params = self._inject_entity_ids(params)

        # Call the tool
        start_time = time.perf_counter()
        response = await self._call_tool(tool, params)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Validate response
        success = self._validate_response(response, expected)
        error = response.get("error") if not success else None

        # Print result
        if known_issue:
            print(f"   ⚠️  Known Issue: {error}")
        elif success:
            print(f"   ✅ Passed ({duration_ms:.2f}ms)")
        else:
            print(f"   ❌ Failed: {error}")

        # Record result
        self.report.add_test_result(
            test_name=test_name,
            tool=tool,
            params=params,
            success=success,
            duration_ms=duration_ms,
            response=response,
            error=error,
            known_issue=known_issue
        )

        # Store created entity IDs for dependency chain
        if success and "create" in test_name.lower():
            self._extract_created_ids(response)

        return {
            "success": success,
            "duration_ms": duration_ms,
            "response": response
        }

    def _inject_entity_ids(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Inject created entity IDs into test parameters."""
        params_str = str(params)

        for key, value in self.created_entities.items():
            params_str = params_str.replace(f"test-{key}", value)

        # This is a simple string replacement approach
        # In production, you'd use proper dict traversal
        try:
            import ast
            return ast.literal_eval(params_str)
        except:
            return params

    def _extract_created_ids(self, response: Dict[str, Any]):
        """Extract entity IDs from create responses."""
        if not response.get("success"):
            return

        data = response.get("data", {})

        # Extract organization ID
        if data.get("id") and "organization" in str(response).lower():
            self.created_entities["organization_id"] = data["id"]
            print(f"   📝 Stored organization_id: {data['id']}")

        # Extract project ID
        if data.get("id") and "project" in str(response).lower():
            self.created_entities["project_id"] = data["id"]
            print(f"   📝 Stored project_id: {data['id']}")

    def _validate_response(
        self,
        response: Dict[str, Any],
        expected: Dict[str, Any]
    ) -> bool:
        """Validate response against expected values.

        Args:
            response: Actual response from tool
            expected: Expected response characteristics

        Returns:
            True if response matches expectations
        """
        # Check success expectation
        if "success" in expected:
            if response.get("success") != expected["success"]:
                return False

        # Check if expected to have data
        if expected.get("has_data") is True:
            if not response.get("data"):
                return False

        # Check for expected error content
        if "error_contains" in expected:
            error = str(response.get("error", "")).lower()
            if expected["error_contains"].lower() not in error:
                return False

        # Default: success if no error
        return response.get("success", True) and not response.get("error")

    async def run_test_group_parallel(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run multiple independent test cases in parallel.

        Args:
            test_cases: List of test cases to run in parallel

        Returns:
            List of test results
        """
        tasks = [self.run_test_case(tc) for tc in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"   ❌ Exception in test: {test_cases[i]['name']}: {result}")
                processed_results.append({
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        return processed_results

    async def run_all_tests(self):
        """Run all test cases with PERT-style dependency management.

        Execution strategy:
        1. Sequential: Authentication and connection tests
        2. Parallel: Independent read operations (list, get, search)
        3. Sequential: Create operations (establish dependency chain)
        4. Parallel: Tests depending on created entities
        5. Parallel: Cleanup operations
        """
        print("\n" + "="*80)
        print("ATOMS MCP COMPREHENSIVE TEST RUN")
        print("="*80)

        self.report.start_test_run()

        # Phase 1: Workspace tool tests (can run in parallel)
        print("\n📋 Phase 1: Workspace Operations (parallel)")
        workspace_cases = self.test_cases.workspace_tool_cases()
        await self.run_test_group_parallel(workspace_cases)

        # Phase 2: Entity list operations (can run in parallel)
        print("\n📋 Phase 2: Entity List Operations (parallel)")
        list_cases = [
            tc for tc in self.test_cases.entity_tool_cases()
            if "List" in tc["name"]
        ]
        await self.run_test_group_parallel(list_cases)

        # Phase 3: Query operations (can run in parallel)
        print("\n📋 Phase 3: Query Operations (parallel)")
        query_cases = self.test_cases.query_tool_cases()
        await self.run_test_group_parallel(query_cases)

        # Phase 4: Create operations (sequential - establishes dependencies)
        print("\n📋 Phase 4: Create Operations (sequential)")
        create_cases = [
            tc for tc in self.test_cases.entity_tool_cases()
            if "Create" in tc["name"] or "create" in tc["name"]
        ]
        for test_case in create_cases:
            await self.run_test_case(test_case)

        # Phase 5: Relationship and workflow tests (parallel where possible)
        print("\n📋 Phase 5: Relationship and Workflow Tests")
        relationship_cases = self.test_cases.relationship_tool_cases()
        workflow_cases = self.test_cases.workflow_tool_cases()

        # Filter out tests that require org (they'll skip if no org)
        remaining_cases = relationship_cases + workflow_cases
        await self.run_test_group_parallel(remaining_cases)

        self.report.end_test_run()

        print("\n" + "="*80)
        print("TEST RUN COMPLETE")
        print("="*80)

    def generate_reports(self):
        """Generate all test reports."""
        print("\n📊 Generating reports...")

        # Console report
        self.report.print_console_report()

        # Markdown report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report.generate_markdown_report(f"test_report_headless_{timestamp}.md")

        # JSON report
        self.report.generate_json_report(f"test_report_headless_{timestamp}.json")

    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.__aexit__(None, None, None)


async def main():
    """Main entry point."""
    client = MCPTestClient()

    try:
        # Connect and authenticate
        if not await client.connect_and_authenticate():
            print("❌ Failed to connect/authenticate")
            return 1

        # Run all tests
        await client.run_all_tests()

        # Generate reports
        client.generate_reports()

        return 0

    finally:
        # Cleanup
        await client.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
