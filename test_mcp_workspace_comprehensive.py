"""
Comprehensive test script for mcp__Atoms__workspace_tool.

This script tests ALL operations via the MCP tool interface:
1. list_workspaces
2. get_context
3. set_context
4. get_defaults

Note: Create, update, and delete operations are not supported by workspace_tool.
Those operations are handled by entity_tool with entity_type='organization'.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class MCPWorkspaceToolTester:
    """Comprehensive test harness for mcp__Atoms__workspace_tool."""

    def __init__(self):
        """Initialize tester."""
        self.results: List[Dict[str, Any]] = []
        self.test_start_time = datetime.now()

    def log_result(
        self,
        test_number: int,
        operation: str,
        input_params: Dict[str, Any],
        output_response: Any,
        status: str,
        error: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Log detailed test result."""
        result = {
            "test_number": test_number,
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "input_parameters": input_params,
            "output_response": output_response,
            "status": status,
            "error": error,
            "notes": notes,
            "response_structure": self._analyze_structure(output_response) if output_response else None
        }
        self.results.append(result)

        # Print formatted result
        print(f"\n{'='*100}")
        print(f"TEST #{test_number}: {operation}")
        print(f"{'='*100}")
        print(f"Status: {status}")
        print(f"\nInput Parameters:")
        print(json.dumps(input_params, indent=2))

        if error:
            print(f"\nError:")
            print(f"  {error}")

        if output_response:
            print(f"\nOutput Response:")
            print(json.dumps(output_response, indent=2, default=str))

            print(f"\nResponse Structure:")
            print(json.dumps(result['response_structure'], indent=2))

        if notes:
            print(f"\nNotes:")
            print(f"  {notes}")

        print(f"{'='*100}\n")

    def _analyze_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze data structure for documentation."""
        if isinstance(data, dict):
            analysis = {
                "type": "dict",
                "keys": list(data.keys()),
                "key_types": {k: type(v).__name__ for k, v in data.items()}
            }

            # Special analysis for common response patterns
            if "success" in data:
                analysis["is_standard_response"] = True
                analysis["success"] = data.get("success")

            if "data" in data and isinstance(data["data"], list):
                analysis["data_list_length"] = len(data["data"])
                if data["data"]:
                    analysis["data_item_sample_keys"] = list(data["data"][0].keys()) if isinstance(data["data"][0], dict) else None

            return analysis

        elif isinstance(data, list):
            return {
                "type": "list",
                "length": len(data),
                "item_types": list(set(type(item).__name__ for item in data)) if data else []
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data) if data is not None else None
            }

    def print_header(self, title: str):
        """Print formatted section header."""
        print(f"\n{'#'*100}")
        print(f"# {title}")
        print(f"{'#'*100}\n")

    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final test report."""
        test_end_time = datetime.now()
        duration = (test_end_time - self.test_start_time).total_seconds()

        # Calculate statistics
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r["status"] == "SUCCESS")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        not_supported = sum(1 for r in self.results if r["status"] == "NOT_SUPPORTED")

        report = {
            "test_suite": "mcp__Atoms__workspace_tool Comprehensive Tests",
            "execution_time": {
                "start": self.test_start_time.isoformat(),
                "end": test_end_time.isoformat(),
                "duration_seconds": duration
            },
            "summary": {
                "total_tests": total_tests,
                "successful": successful,
                "failed": failed,
                "errors": errors,
                "not_supported": not_supported,
                "success_rate": f"{(successful/total_tests*100):.2f}%" if total_tests > 0 else "N/A"
            },
            "test_results": self.results
        }

        # Print summary
        self.print_header("FINAL TEST REPORT")

        print(f"Test Suite: {report['test_suite']}")
        print(f"Duration: {duration:.2f} seconds")
        print()
        print("Results Summary:")
        print(f"  Total Tests:    {total_tests}")
        print(f"  Successful:     {successful}")
        print(f"  Failed:         {failed}")
        print(f"  Errors:         {errors}")
        print(f"  Not Supported:  {not_supported}")
        print(f"  Success Rate:   {report['summary']['success_rate']}")
        print()

        print("Test Details:")
        for result in self.results:
            status_icon = {
                "SUCCESS": "✓",
                "FAILED": "✗",
                "ERROR": "⚠",
                "NOT_SUPPORTED": "○"
            }.get(result["status"], "?")
            print(f"  {status_icon} Test #{result['test_number']}: {result['operation']} - {result['status']}")

        # Save to file
        report_filename = f"workspace_tool_mcp_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\nDetailed report saved to: {report_filename}")
        print(f"{'#'*100}\n")

        return report


async def get_auth_token():
    """Get authentication token from Supabase."""
    try:
        from supabase import create_client

        url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

        if not url or not key:
            print("ERROR: Supabase configuration not found in environment.")
            print("Required: NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY")
            return None

        client = create_client(url, key)

        # Authenticate
        auth_response = client.auth.sign_in_with_password({
            "email": "kooshapari@kooshapari.com",
            "password": "118118"
        })

        if auth_response.session:
            print(f"✓ Authentication successful!")
            print(f"  Token: {auth_response.session.access_token[:30]}...")
            return auth_response.session.access_token

        print("ERROR: No session obtained from Supabase")
        return None

    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        return None


async def run_comprehensive_tests():
    """Run all comprehensive tests for mcp__Atoms__workspace_tool."""

    tester = MCPWorkspaceToolTester()
    tester.print_header("MCP WORKSPACE_TOOL COMPREHENSIVE TEST SUITE")

    print("This test suite will execute all available operations on the workspace_tool:")
    print("1. list_workspaces - List all available workspaces")
    print("2. get_context - Get current workspace context")
    print("3. set_context - Set active workspace context")
    print("4. get_defaults - Get smart default values")
    print()
    print("Note: Create/Update/Delete operations are not supported by workspace_tool.")
    print("      Those operations use entity_tool with entity_type='organization'.")
    print()

    # Get authentication token
    auth_token = await get_auth_token()
    if not auth_token:
        print("\nFATAL: Cannot proceed without authentication token.")
        tester.log_result(
            0,
            "authentication",
            {},
            None,
            "ERROR",
            "Failed to obtain authentication token",
            "All tests require authentication"
        )
        return tester.generate_final_report()

    # Store data between tests
    test_data = {}

    # Import the workspace operation function
    try:
        from tools.workspace import workspace_operation
    except ImportError:
        from workspace import workspace_operation

    # TEST 1: List Workspaces
    tester.print_header("TEST 1: List Workspaces")
    test_1_params = {
        "operation": "list_workspaces",
        "format_type": "detailed"
    }

    try:
        response_1 = await workspace_operation(auth_token=auth_token, **test_1_params)

        status = "SUCCESS" if response_1.get("success") is not False else "FAILED"
        tester.log_result(
            1,
            "list_workspaces",
            test_1_params,
            response_1,
            status,
            None if status == "SUCCESS" else response_1.get("error"),
            f"Retrieved workspaces list"
        )

        # Store organizations for later tests
        if response_1.get("organizations"):
            test_data["organizations"] = response_1["organizations"]
            test_data["first_org_id"] = response_1["organizations"][0].get("id")

    except Exception as e:
        tester.log_result(
            1,
            "list_workspaces",
            test_1_params,
            None,
            "ERROR",
            str(e),
            "Exception occurred during list_workspaces operation"
        )

    # TEST 2: Get Context
    tester.print_header("TEST 2: Get Current Context")
    test_2_params = {
        "operation": "get_context",
        "format_type": "detailed"
    }

    try:
        if auth_token:
            response_2 = await workspace_operation(auth_token=auth_token, **test_2_params)

            status = "SUCCESS" if response_2.get("success") is not False else "FAILED"
            tester.log_result(
                2,
                "get_context",
                test_2_params,
                response_2,
                status,
                None if status == "SUCCESS" else response_2.get("error"),
                "Retrieved current workspace context"
            )

    except Exception as e:
        tester.log_result(
            2,
            "get_context",
            test_2_params,
            None,
            "ERROR",
            str(e),
            "Exception occurred during get_context operation"
        )

    # TEST 3: Set Context (if we have an organization)
    if test_data.get("first_org_id"):
        tester.print_header("TEST 3: Set Context")
        test_3_params = {
            "operation": "set_context",
            "context_type": "organization",
            "entity_id": test_data["first_org_id"],
            "format_type": "detailed"
        }

        try:
            if auth_token:
                response_3 = await workspace_operation(auth_token=auth_token, **test_3_params)

                status = "SUCCESS" if response_3.get("success") is not False else "FAILED"
                tester.log_result(
                    3,
                    "set_context",
                    test_3_params,
                    response_3,
                    status,
                    None if status == "SUCCESS" else response_3.get("error"),
                    f"Set context to organization: {test_data['first_org_id']}"
                )

        except Exception as e:
            tester.log_result(
                3,
                "set_context",
                test_3_params,
                None,
                "ERROR",
                str(e),
                "Exception occurred during set_context operation"
            )
    else:
        tester.log_result(
            3,
            "set_context",
            {"note": "Skipped - no organizations available"},
            None,
            "FAILED",
            "No organizations available to set context",
            "Test requires at least one organization to exist"
        )

    # TEST 4: Get Defaults
    tester.print_header("TEST 4: Get Smart Defaults")
    test_4_params = {
        "operation": "get_defaults",
        "format_type": "detailed"
    }

    try:
        if auth_token:
            response_4 = await workspace_operation(auth_token=auth_token, **test_4_params)

            status = "SUCCESS" if response_4.get("success") is not False else "FAILED"
            tester.log_result(
                4,
                "get_defaults",
                test_4_params,
                response_4,
                status,
                None if status == "SUCCESS" else response_4.get("error"),
                "Retrieved smart default values based on current context"
            )

    except Exception as e:
        tester.log_result(
            4,
            "get_defaults",
            test_4_params,
            None,
            "ERROR",
            str(e),
            "Exception occurred during get_defaults operation"
        )

    # TEST 5: Create Workspace (NOT SUPPORTED - Document this)
    tester.print_header("TEST 5: Create Workspace (Not Supported)")
    test_5_params = {
        "note": "workspace_tool does not support create operation",
        "workaround": "Use entity_tool instead",
        "example": {
            "tool": "entity_tool",
            "parameters": {
                "entity_type": "organization",
                "operation": "create",
                "data": {
                    "name": "New Workspace",
                    "type": "team"
                }
            }
        }
    }

    tester.log_result(
        5,
        "create_workspace",
        test_5_params,
        None,
        "NOT_SUPPORTED",
        "Operation not available in workspace_tool",
        "Use entity_tool with entity_type='organization' to create workspaces"
    )

    # TEST 6: Update Workspace (NOT SUPPORTED - Document this)
    tester.print_header("TEST 6: Update Workspace (Not Supported)")
    test_6_params = {
        "note": "workspace_tool does not support update operation",
        "workaround": "Use entity_tool instead",
        "example": {
            "tool": "entity_tool",
            "parameters": {
                "entity_type": "organization",
                "operation": "update",
                "entity_id": "org_xxx",
                "data": {
                    "name": "Updated Name"
                }
            }
        }
    }

    tester.log_result(
        6,
        "update_workspace",
        test_6_params,
        None,
        "NOT_SUPPORTED",
        "Operation not available in workspace_tool",
        "Use entity_tool with entity_type='organization' to update workspaces"
    )

    # TEST 7: Delete Workspace (NOT SUPPORTED - Document this)
    tester.print_header("TEST 7: Delete Workspace (Not Supported)")
    test_7_params = {
        "note": "workspace_tool does not support delete operation",
        "workaround": "Use entity_tool instead",
        "example": {
            "tool": "entity_tool",
            "parameters": {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": "org_xxx",
                "soft_delete": True
            }
        }
    }

    tester.log_result(
        7,
        "delete_workspace",
        test_7_params,
        None,
        "NOT_SUPPORTED",
        "Operation not available in workspace_tool",
        "Use entity_tool with entity_type='organization' to delete workspaces"
    )

    # Generate and return final report
    return tester.generate_final_report()


def main():
    """Main entry point."""
    print("\nStarting comprehensive mcp__Atoms__workspace_tool tests...\n")

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        load_dotenv(".env.local", override=True)
        print("✓ Environment variables loaded\n")
    except ImportError:
        print("⚠ python-dotenv not installed, using system environment\n")

    # Run tests
    report = asyncio.run(run_comprehensive_tests())

    print("\nAll tests completed!")
    return report


if __name__ == "__main__":
    main()
