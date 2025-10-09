"""
Comprehensive test script for the workspace_tool via Atoms MCP server.

This script tests all workspace_tool operations and documents results.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List

# Import the workspace operation function
try:
    from tools.workspace import workspace_operation
except ImportError:
    from workspace import workspace_operation


class WorkspaceToolTester:
    """Test harness for workspace_tool operations."""

    def __init__(self, auth_token: str = None):
        """Initialize tester with optional auth token."""
        self.auth_token = auth_token or os.getenv("TEST_AUTH_TOKEN")
        self.results: List[Dict[str, Any]] = []

    def log_result(self, operation: str, params: Dict[str, Any],
                   status: str, response: Any, error: str = None):
        """Log test result."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "parameters": params,
            "status": status,
            "response_structure": self._analyze_structure(response),
            "response_data": response,
            "error": error
        }
        self.results.append(result)

        # Print result
        print(f"\n{'='*80}")
        print(f"Operation: {operation}")
        print(f"Status: {status}")
        print(f"Parameters: {json.dumps(params, indent=2)}")
        if error:
            print(f"Error: {error}")
        else:
            print(f"Response Structure: {json.dumps(result['response_structure'], indent=2)}")
            print(f"Response Data: {json.dumps(response, indent=2, default=str)}")
        print(f"{'='*80}\n")

    def _analyze_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze data structure."""
        if isinstance(data, dict):
            return {
                "type": "dict",
                "keys": list(data.keys()),
                "nested_types": {k: type(v).__name__ for k, v in data.items()}
            }
        elif isinstance(data, list):
            return {
                "type": "list",
                "length": len(data),
                "item_types": list(set(type(item).__name__ for item in data))
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)
            }

    async def test_operation_1_list_workspaces(self):
        """Test 1: List all workspaces."""
        operation = "list_workspaces"
        params = {
            "operation": operation,
            "limit": 100,
            "offset": 0,
            "format_type": "detailed"
        }

        try:
            response = await workspace_operation(
                auth_token=self.auth_token,
                **params
            )

            status = "SUCCESS" if response.get("success") is not False else "FAILED"
            self.log_result(operation, params, status, response)
            return response

        except Exception as e:
            self.log_result(operation, params, "ERROR", None, str(e))
            return None

    async def test_operation_2_get_context(self):
        """Test 2: Get current workspace context."""
        operation = "get_context"
        params = {
            "operation": operation,
            "format_type": "detailed"
        }

        try:
            response = await workspace_operation(
                auth_token=self.auth_token,
                **params
            )

            status = "SUCCESS" if response.get("success") is not False else "FAILED"
            self.log_result(operation, params, status, response)
            return response

        except Exception as e:
            self.log_result(operation, params, "ERROR", None, str(e))
            return None

    async def test_operation_3_create_workspace(self, timestamp: str):
        """Test 3: Create a new test workspace.

        Note: This operation is not directly supported by workspace_tool.
        Workspaces are created via entity_tool with entity_type='organization'.
        """
        operation = "create_workspace_via_entity_tool"
        params = {
            "note": "workspace_tool does not support create operation",
            "workaround": "use entity_tool with entity_type='organization'",
            "example_params": {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"MCP_Test_Workspace_{timestamp}",
                    "type": "team"
                }
            }
        }

        self.log_result(
            operation,
            params,
            "NOT_SUPPORTED",
            {"message": "workspace_tool does not have a create operation"},
            "Operation not available in workspace_tool"
        )

        return None

    async def test_operation_4_set_context(self, organization_id: str):
        """Test 4: Set active workspace context."""
        operation = "set_context"
        params = {
            "operation": operation,
            "context_type": "organization",
            "entity_id": organization_id,
            "format_type": "detailed"
        }

        try:
            response = await workspace_operation(
                auth_token=self.auth_token,
                **params
            )

            status = "SUCCESS" if response.get("success") is not False else "FAILED"
            self.log_result(operation, params, status, response)
            return response

        except Exception as e:
            self.log_result(operation, params, "ERROR", None, str(e))
            return None

    async def test_operation_5_get_defaults(self):
        """Test 5: Get smart defaults based on context."""
        operation = "get_defaults"
        params = {
            "operation": operation,
            "format_type": "detailed"
        }

        try:
            response = await workspace_operation(
                auth_token=self.auth_token,
                **params
            )

            status = "SUCCESS" if response.get("success") is not False else "FAILED"
            self.log_result(operation, params, status, response)
            return response

        except Exception as e:
            self.log_result(operation, params, "ERROR", None, str(e))
            return None

    async def test_operation_6_update_workspace(self):
        """Test 6: Update workspace metadata.

        Note: This operation is not directly supported by workspace_tool.
        Workspace updates are done via entity_tool with entity_type='organization'.
        """
        operation = "update_workspace_via_entity_tool"
        params = {
            "note": "workspace_tool does not support update operation",
            "workaround": "use entity_tool with entity_type='organization'",
            "example_params": {
                "operation": "update",
                "entity_type": "organization",
                "entity_id": "org_xxx",
                "data": {
                    "name": "Updated Name"
                }
            }
        }

        self.log_result(
            operation,
            params,
            "NOT_SUPPORTED",
            {"message": "workspace_tool does not have an update operation"},
            "Operation not available in workspace_tool"
        )

        return None

    async def test_operation_7_delete_workspace(self):
        """Test 7: Delete workspace.

        Note: This operation is not directly supported by workspace_tool.
        Workspace deletion is done via entity_tool with entity_type='organization'.
        """
        operation = "delete_workspace_via_entity_tool"
        params = {
            "note": "workspace_tool does not support delete operation",
            "workaround": "use entity_tool with entity_type='organization'",
            "example_params": {
                "operation": "delete",
                "entity_type": "organization",
                "entity_id": "org_xxx",
                "soft_delete": True
            }
        }

        self.log_result(
            operation,
            params,
            "NOT_SUPPORTED",
            {"message": "workspace_tool does not have a delete operation"},
            "Operation not available in workspace_tool"
        )

        return None

    async def run_all_tests(self):
        """Run all workspace_tool tests."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("\n" + "="*80)
        print("WORKSPACE_TOOL COMPREHENSIVE TEST SUITE")
        print(f"Timestamp: {timestamp}")
        print(f"Auth Token Present: {bool(self.auth_token)}")
        print("="*80 + "\n")

        # Test 1: List workspaces
        workspaces_response = await self.test_operation_1_list_workspaces()

        # Test 2: Get current context
        context_response = await self.test_operation_2_get_context()

        # Test 3: Create workspace (not supported - documented)
        await self.test_operation_3_create_workspace(timestamp)

        # Test 4: Set context (if we have workspaces)
        if workspaces_response and workspaces_response.get("organizations"):
            first_org = workspaces_response["organizations"][0]
            org_id = first_org.get("id")
            if org_id:
                await self.test_operation_4_set_context(org_id)

        # Test 5: Get smart defaults
        await self.test_operation_5_get_defaults()

        # Test 6: Update workspace (not supported - documented)
        await self.test_operation_6_update_workspace()

        # Test 7: Delete workspace (not supported - documented)
        await self.test_operation_7_delete_workspace()

        # Generate final report
        self.generate_report()

    def generate_report(self):
        """Generate final test report."""
        print("\n" + "="*80)
        print("FINAL TEST REPORT")
        print("="*80 + "\n")

        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r["status"] == "SUCCESS")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        not_supported = sum(1 for r in self.results if r["status"] == "NOT_SUPPORTED")

        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Not Supported: {not_supported}")
        print()

        print("Summary by Operation:")
        for result in self.results:
            print(f"  - {result['operation']}: {result['status']}")

        # Save detailed report to file
        report_file = f"workspace_tool_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "successful": successful,
                    "failed": failed,
                    "errors": errors,
                    "not_supported": not_supported
                },
                "results": self.results
            }, f, indent=2, default=str)

        print(f"\nDetailed report saved to: {report_file}")
        print("="*80 + "\n")


async def main():
    """Main test execution."""
    # Check for auth token
    auth_token = os.getenv("TEST_AUTH_TOKEN")

    if not auth_token:
        print("WARNING: No TEST_AUTH_TOKEN found in environment.")
        print("Tests will run but may fail authentication.")
        print("Set TEST_AUTH_TOKEN environment variable with a valid Supabase JWT token.")
        print()

    # Run tests
    tester = WorkspaceToolTester(auth_token)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
