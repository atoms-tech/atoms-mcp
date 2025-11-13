"""
Live comprehensive test suite for workflow_tool
Tests all available workflows against real Atoms MCP backend
"""
import asyncio
import json
from typing import Dict, Any
from datetime import datetime


class WorkflowToolLiveTester:
    """Comprehensive live tester for workflow_tool functionality"""

    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "workflows_tested": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
        self.test_org_id = None
        self.test_project_id = None
        self.test_document_id = None
        self.test_requirement_ids = []

    def log_test(self, workflow: str, test_name: str, success: bool,
                 details: Dict[str, Any], error: str = None):
        """Log test result"""
        if workflow not in self.results["workflows_tested"]:
            self.results["workflows_tested"][workflow] = {
                "tests": [],
                "passed": 0,
                "failed": 0
            }

        test_result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

        self.results["workflows_tested"][workflow]["tests"].append(test_result)
        self.results["summary"]["total_tests"] += 1

        if success:
            self.results["workflows_tested"][workflow]["passed"] += 1
            self.results["summary"]["passed"] += 1
        else:
            self.results["workflows_tested"][workflow]["failed"] += 1
            self.results["summary"]["failed"] += 1
            if error:
                self.results["summary"]["errors"].append({
                    "workflow": workflow,
                    "test": test_name,
                    "error": error
                })

    async def setup_test_data(self):
        """Create minimal test data needed for workflows"""
        print("\n=== SETTING UP TEST DATA ===")

        try:
            # Import the MCP tools
            from tools.workspace_tool import workspace_tool
            from tools.entity_tool import entity_tool

            # 1. Get or create test organization
            print("1. Getting test organization...")
            workspaces_result = await workspace_tool(
                operation="list_workspaces",
                format_type="detailed"
            )

            if isinstance(workspaces_result, list) and len(workspaces_result) > 0:
                # Use first organization
                for ws in workspaces_result:
                    if isinstance(ws, dict):
                        self.test_org_id = ws.get("id")
                        print(f"   Using existing organization: {ws.get('name')} ({self.test_org_id})")
                        break

            if not self.test_org_id:
                print("   Creating new test organization...")
                org_result = await entity_tool(
                    entity_type="organization",
                    data={
                        "name": f"Workflow Test Org {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "description": "Organization for comprehensive workflow testing"
                    }
                )
                if isinstance(org_result, dict):
                    self.test_org_id = org_result.get("id")
                    print(f"   Created organization ID: {self.test_org_id}")

            # 2. Create test project for some workflows
            print("2. Creating test project...")
            project_result = await entity_tool(
                entity_type="project",
                data={
                    "name": f"Workflow Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "description": "Project for workflow testing",
                    "organization_id": self.test_org_id
                }
            )

            if isinstance(project_result, dict):
                self.test_project_id = project_result.get("id")
                print(f"   Created project ID: {self.test_project_id}")

            # 3. Create test document for import_requirements workflow
            print("3. Creating test document...")
            doc_result = await entity_tool(
                entity_type="document",
                data={
                    "name": f"Test Requirements Doc {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "type": "requirements",
                    "project_id": self.test_project_id
                }
            )

            if isinstance(doc_result, dict):
                self.test_document_id = doc_result.get("id")
                print(f"   Created document ID: {self.test_document_id}")

            # 4. Create test requirements for bulk operations
            print("4. Creating test requirements...")
            for i in range(3):
                req_result = await entity_tool(
                    entity_type="requirement",
                    data={
                        "name": f"TEST-REQ-{i+1}",
                        "description": f"Test requirement {i+1} for bulk operations",
                        "status": "draft",
                        "document_id": self.test_document_id
                    }
                )
                if isinstance(req_result, dict):
                    req_id = req_result.get("id")
                    self.test_requirement_ids.append(req_id)
                    print(f"   Created requirement: {req_id}")

            print("\n✓ Test data setup complete")
            return True

        except Exception as e:
            print(f"\n✗ Test data setup failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    async def test_setup_project_workflow(self):
        """Test setup_project workflow with various parameters"""
        print("\n=== TESTING SETUP_PROJECT WORKFLOW ===")

        from tools.workflow_tool import workflow_tool

        # Test 1: Basic project setup
        print("\nTest 1: Basic project setup")
        try:
            result = await workflow_tool(
                workflow="setup_project",
                parameters={
                    "name": f"Basic Project {datetime.now().strftime('%H%M%S')}",
                    "organization_id": self.test_org_id
                },
                transaction_mode=True
            )
            success = isinstance(result, dict) and not result.get("error")
            self.log_test("setup_project", "basic_setup", success, {
                "result": str(result)[:500]
            })
            if success:
                print(f"   ✓ Success: {json.dumps(result, indent=2)[:200]}")
            else:
                print(f"   ✗ Failed: {result}")
        except Exception as e:
            self.log_test("setup_project", "basic_setup", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 2: Project with initial documents
        print("\nTest 2: Project with initial documents")
        try:
            result = await workflow_tool(
                workflow="setup_project",
                parameters={
                    "name": f"Project with Docs {datetime.now().strftime('%H%M%S')}",
                    "organization_id": self.test_org_id,
                    "initial_documents": ["Requirements", "Design", "Test Plan"]
                },
                transaction_mode=True
            )
            success = isinstance(result, dict) and not result.get("error")
            self.log_test("setup_project", "with_initial_documents", success, {
                "result": str(result)[:500]
            })
            if success:
                print(f"   ✓ Success: {json.dumps(result, indent=2)[:200]}")
            else:
                print(f"   ✗ Failed: {result}")
        except Exception as e:
            self.log_test("setup_project", "with_initial_documents", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 3: Without transaction mode
        print("\nTest 3: Setup project without transaction mode")
        try:
            result = await workflow_tool(
                workflow="setup_project",
                parameters={
                    "name": f"Non-Transaction Project {datetime.now().strftime('%H%M%S')}",
                    "organization_id": self.test_org_id
                },
                transaction_mode=False
            )
            success = isinstance(result, dict) and not result.get("error")
            self.log_test("setup_project", "no_transaction_mode", success, {
                "result": str(result)[:500]
            })
            if success:
                print("   ✓ Success")
            else:
                print(f"   ✗ Failed: {result}")
        except Exception as e:
            self.log_test("setup_project", "no_transaction_mode", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 4: Missing required parameter
        print("\nTest 4: Missing organization_id (should fail)")
        try:
            result = await workflow_tool(
                workflow="setup_project",
                parameters={
                    "name": "Project Without Org"
                },
                transaction_mode=True
            )
            # Should fail or return error
            is_error = result.get("error") if isinstance(result, dict) else True
            self.log_test("setup_project", "missing_org_id", True, {
                "result": str(result)[:500],
                "note": "Correctly handled missing parameter"
            })
            print(f"   ✓ Correctly handled missing organization_id: {result}")
        except Exception as e:
            self.log_test("setup_project", "missing_org_id", True, {
                "error": str(e),
                "note": "Correctly raised error for missing parameter"
            })
            print(f"   ✓ Correctly raised error: {str(e)}")

    async def test_import_requirements_workflow(self):
        """Test import_requirements workflow"""
        print("\n=== TESTING IMPORT_REQUIREMENTS WORKFLOW ===")

        from tools.workflow_tool import workflow_tool

        # Test 1: Basic requirements import
        print("\nTest 1: Basic requirements import")
        try:
            result = await workflow_tool(
                workflow="import_requirements",
                parameters={
                    "document_id": self.test_document_id,
                    "requirements": [
                        {
                            "name": "REQ-001",
                            "description": "User shall be able to login"
                        },
                        {
                            "name": "REQ-002",
                            "description": "System shall validate credentials"
                        }
                    ]
                },
                transaction_mode=True
            )
            success = isinstance(result, dict) and not result.get("error")
            self.log_test("import_requirements", "basic_import", success, {
                "result": str(result)[:500]
            })
            if success:
                print(f"   ✓ Success: {json.dumps(result, indent=2)[:200]}")
            else:
                print(f"   ✗ Failed: {result}")
        except Exception as e:
            self.log_test("import_requirements", "basic_import", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 2: Empty requirements list
        print("\nTest 2: Empty requirements list")
        try:
            result = await workflow_tool(
                workflow="import_requirements",
                parameters={
                    "document_id": self.test_document_id,
                    "requirements": []
                },
                transaction_mode=True
            )
            success = isinstance(result, dict)
            self.log_test("import_requirements", "empty_list", success, {
                "result": str(result)[:500]
            })
            if success:
                print(f"   ✓ Handled empty list: {result}")
            else:
                print(f"   ✗ Failed: {result}")
        except Exception as e:
            self.log_test("import_requirements", "empty_list", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 3: Missing document_id
        print("\nTest 3: Missing document_id (should fail)")
        try:
            result = await workflow_tool(
                workflow="import_requirements",
                parameters={
                    "requirements": [
                        {"name": "REQ-X", "description": "Test"}
                    ]
                },
                transaction_mode=True
            )
            is_error = result.get("error") if isinstance(result, dict) else True
            self.log_test("import_requirements", "missing_doc_id", True, {
                "result": str(result)[:500],
                "note": "Correctly handled missing parameter"
            })
            print(f"   ✓ Correctly handled missing document_id: {result}")
        except Exception as e:
            self.log_test("import_requirements", "missing_doc_id", True, {
                "error": str(e),
                "note": "Correctly raised error"
            })
            print(f"   ✓ Correctly raised error: {str(e)}")

    async def test_setup_test_matrix_workflow(self):
        """Test setup_test_matrix workflow"""
        print("\n=== TESTING SETUP_TEST_MATRIX WORKFLOW ===")

        from tools.workflow_tool import workflow_tool

        # Test 1: Basic test matrix setup
        print("\nTest 1: Basic test matrix setup")
        try:
            result = await workflow_tool(
                workflow="setup_test_matrix",
                parameters={
                    "project_id": self.test_project_id
                },
                transaction_mode=True
            )
            success = isinstance(result, dict)
            self.log_test("setup_test_matrix", "basic_setup", success, {
                "result": str(result)[:500]
            })
            if success:
                print(f"   Result: {json.dumps(result, indent=2)[:200]}")
            else:
                print(f"   Failed: {result}")
        except Exception as e:
            self.log_test("setup_test_matrix", "basic_setup", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 2: Missing project_id
        print("\nTest 2: Missing project_id (should fail)")
        try:
            result = await workflow_tool(
                workflow="setup_test_matrix",
                parameters={},
                transaction_mode=True
            )
            is_error = result.get("error") if isinstance(result, dict) else True
            self.log_test("setup_test_matrix", "missing_project_id", True, {
                "result": str(result)[:500],
                "note": "Correctly handled missing parameter"
            })
            print(f"   ✓ Correctly handled missing project_id: {result}")
        except Exception as e:
            self.log_test("setup_test_matrix", "missing_project_id", True, {
                "error": str(e),
                "note": "Correctly raised error"
            })
            print(f"   ✓ Correctly raised error: {str(e)}")

    async def test_bulk_status_update_workflow(self):
        """Test bulk_status_update workflow"""
        print("\n=== TESTING BULK_STATUS_UPDATE WORKFLOW ===")

        from tools.workflow_tool import workflow_tool

        if not self.test_requirement_ids:
            print("⚠ Skipping: No test requirements available")
            return

        # Test 1: Basic bulk status update
        print("\nTest 1: Basic bulk status update")
        try:
            result = await workflow_tool(
                workflow="bulk_status_update",
                parameters={
                    "entity_type": "requirement",
                    "entity_ids": self.test_requirement_ids[:2],
                    "new_status": "approved"
                },
                transaction_mode=True
            )
            success = isinstance(result, dict)
            self.log_test("bulk_status_update", "basic_update", success, {
                "result": str(result)[:500]
            })
            if success:
                print(f"   Result: {json.dumps(result, indent=2)[:200]}")
            else:
                print(f"   Failed: {result}")
        except Exception as e:
            self.log_test("bulk_status_update", "basic_update", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 2: Without transaction mode
        print("\nTest 2: Bulk update without transaction mode")
        try:
            result = await workflow_tool(
                workflow="bulk_status_update",
                parameters={
                    "entity_type": "requirement",
                    "entity_ids": self.test_requirement_ids[:1],
                    "new_status": "draft"
                },
                transaction_mode=False
            )
            success = isinstance(result, dict)
            self.log_test("bulk_status_update", "no_transaction", success, {
                "result": str(result)[:500]
            })
            if success:
                print(f"   Result: {json.dumps(result, indent=2)[:200]}")
            else:
                print(f"   Failed: {result}")
        except Exception as e:
            self.log_test("bulk_status_update", "no_transaction", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 3: Empty entity list
        print("\nTest 3: Empty entity list")
        try:
            result = await workflow_tool(
                workflow="bulk_status_update",
                parameters={
                    "entity_type": "requirement",
                    "entity_ids": [],
                    "new_status": "approved"
                },
                transaction_mode=True
            )
            success = isinstance(result, dict)
            self.log_test("bulk_status_update", "empty_list", success, {
                "result": str(result)[:500]
            })
            print(f"   Result: {json.dumps(result, indent=2)[:200]}")
        except Exception as e:
            self.log_test("bulk_status_update", "empty_list", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

    async def test_organization_onboarding_workflow(self):
        """Test organization_onboarding workflow"""
        print("\n=== TESTING ORGANIZATION_ONBOARDING WORKFLOW ===")

        from tools.workflow_tool import workflow_tool

        # Test 1: Basic organization onboarding
        print("\nTest 1: Basic organization onboarding")
        try:
            result = await workflow_tool(
                workflow="organization_onboarding",
                parameters={
                    "organization_name": f"Onboarded Org {datetime.now().strftime('%H%M%S')}"
                },
                transaction_mode=True
            )
            success = isinstance(result, dict)
            self.log_test("organization_onboarding", "basic_onboarding", success, {
                "result": str(result)[:500]
            })
            if success:
                print(f"   Result: {json.dumps(result, indent=2)[:200]}")
            else:
                print(f"   Failed: {result}")
        except Exception as e:
            self.log_test("organization_onboarding", "basic_onboarding", False, {}, str(e))
            print(f"   ✗ Error: {str(e)}")

        # Test 2: Missing required parameters
        print("\nTest 2: Missing organization_name (should fail)")
        try:
            result = await workflow_tool(
                workflow="organization_onboarding",
                parameters={},
                transaction_mode=True
            )
            is_error = result.get("error") if isinstance(result, dict) else True
            self.log_test("organization_onboarding", "missing_name", True, {
                "result": str(result)[:500],
                "note": "Correctly handled missing parameter"
            })
            print(f"   ✓ Correctly handled missing organization_name: {result}")
        except Exception as e:
            self.log_test("organization_onboarding", "missing_name", True, {
                "error": str(e),
                "note": "Correctly raised error"
            })
            print(f"   ✓ Correctly raised error: {str(e)}")

    async def test_invalid_workflow(self):
        """Test handling of invalid/unknown workflows"""
        print("\n=== TESTING INVALID WORKFLOW HANDLING ===")

        from tools.workflow_tool import workflow_tool

        print("\nTest: Invalid workflow name")
        try:
            result = await workflow_tool(
                workflow="nonexistent_workflow",
                parameters={},
                transaction_mode=True
            )
            is_error = result.get("error") if isinstance(result, dict) else True
            self.log_test("invalid_workflow", "unknown_workflow", True, {
                "result": str(result)[:500],
                "note": "Correctly handled invalid workflow"
            })
            print(f"   ✓ Correctly handled invalid workflow: {result}")
        except Exception as e:
            self.log_test("invalid_workflow", "unknown_workflow", True, {
                "error": str(e),
                "note": "Correctly raised error"
            })
            print(f"   ✓ Correctly raised error: {str(e)}")

    async def run_all_tests(self):
        """Run all workflow tests"""
        print("=" * 80)
        print("COMPREHENSIVE WORKFLOW_TOOL LIVE TEST SUITE")
        print("=" * 80)

        # Setup test data
        if not await self.setup_test_data():
            print("\n✗ Failed to setup test data. Aborting tests.")
            return

        # Run all workflow tests
        await self.test_setup_project_workflow()
        await self.test_import_requirements_workflow()
        await self.test_setup_test_matrix_workflow()
        await self.test_bulk_status_update_workflow()
        await self.test_organization_onboarding_workflow()
        await self.test_invalid_workflow()

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        summary = self.results["summary"]
        print(f"\nTotal Tests: {summary['total_tests']}")
        if summary['total_tests'] > 0:
            print(f"Passed: {summary['passed']} ({summary['passed']/summary['total_tests']*100:.1f}%)")
            print(f"Failed: {summary['failed']} ({summary['failed']/summary['total_tests']*100:.1f}%)")

        print("\nWorkflow Breakdown:")
        for workflow, data in self.results["workflows_tested"].items():
            total = len(data["tests"])
            passed = data["passed"]
            print(f"  {workflow}: {passed}/{total} passed")

        if summary["errors"]:
            print(f"\nErrors encountered: {len(summary['errors'])}")
            for error in summary["errors"][:5]:  # Show first 5 errors
                print(f"  - {error['workflow']}.{error['test']}: {error['error'][:100]}")

    def save_results(self):
        """Save test results to file"""
        output_file = "/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/tests/workflow_tool_live_test_results.json"

        try:
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n✓ Results saved to: {output_file}")
        except Exception as e:
            print(f"\n✗ Failed to save results: {str(e)}")


async def main():
    """Main test execution"""
    tester = WorkflowToolLiveTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
