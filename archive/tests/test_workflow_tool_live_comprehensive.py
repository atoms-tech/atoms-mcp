"""
Comprehensive Live Test Suite for Atoms MCP workflow_tool
Tests all available workflows against the actual MCP server with real authentication.

This test suite covers:
1. setup_project - Create project with initial structure
2. import_requirements - Import requirements from external source
3. setup_test_matrix - Set up test matrix for a project
4. bulk_status_update - Update status for multiple entities
5. organization_onboarding - Complete organization setup

Tests include:
- Parameter validation
- Transaction mode behavior
- Error handling
- Success scenarios
- Edge cases
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.workflow import workflow_execute
from tools.entity import entity_operation


class WorkflowTestResult:
    """Track individual workflow test results"""
    def __init__(self, workflow_name: str, scenario: str):
        self.workflow_name = workflow_name
        self.scenario = scenario
        self.status = "PENDING"
        self.duration_ms = 0
        self.transaction_mode_used = False
        self.error_message = None
        self.response = None
        self.timestamp = datetime.now().isoformat()

    def mark_success(self, duration_ms: float, response: Dict[str, Any], transaction_mode: bool):
        self.status = "PASS"
        self.duration_ms = duration_ms
        self.response = response
        self.transaction_mode_used = transaction_mode

    def mark_failure(self, error: str, duration_ms: float, transaction_mode: bool):
        self.status = "FAIL"
        self.error_message = error
        self.duration_ms = duration_ms
        self.transaction_mode_used = transaction_mode

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow": self.workflow_name,
            "scenario": self.scenario,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "transaction_mode": self.transaction_mode_used,
            "error_message": self.error_message,
            "response": self.response,
            "timestamp": self.timestamp
        }


class WorkflowTester:
    """Comprehensive workflow testing harness"""

    def __init__(self):
        self.results: List[WorkflowTestResult] = []
        self.auth_token = os.environ.get("ATOMS_AUTH_TOKEN")
        if not self.auth_token:
            raise ValueError("ATOMS_AUTH_TOKEN environment variable not set")

        # Track created entities for cleanup
        self.created_orgs = []
        self.created_projects = []
        self.created_documents = []
        self.created_requirements = []

    async def test_workflow(self, workflow_name: str, scenario: str,
                          parameters: Dict[str, Any],
                          transaction_mode: bool = True,
                          expect_failure: bool = False) -> WorkflowTestResult:
        """Test a single workflow scenario"""
        result = WorkflowTestResult(workflow_name, scenario)

        print(f"\n{'='*80}")
        print(f"Testing: {workflow_name} - {scenario}")
        print(f"Transaction Mode: {transaction_mode}")
        print(f"Parameters: {json.dumps(parameters, indent=2)}")
        print(f"{'='*80}")

        import time
        start_time = time.time()

        try:
            response = await workflow_execute(
                auth_token=self.auth_token,
                workflow=workflow_name,
                parameters=parameters,
                transaction_mode=transaction_mode,
                format_type="detailed"
            )

            duration = (time.time() - start_time) * 1000

            print(f"\nResponse: {json.dumps(response, indent=2)}")

            if expect_failure:
                if response.get("success") is False or "error" in response:
                    result.mark_success(duration, response, transaction_mode)
                    print(f"✓ Expected failure occurred: {response.get('error', 'Unknown error')}")
                else:
                    result.mark_failure("Expected failure but workflow succeeded", duration, transaction_mode)
                    print("✗ Unexpected success when failure was expected")
            else:
                if response.get("success") is not False and "error" not in response:
                    result.mark_success(duration, response, transaction_mode)
                    print(f"✓ Test passed in {duration:.2f}ms")

                    # Track created entities for cleanup
                    if "organization_id" in response:
                        self.created_orgs.append(response["organization_id"])
                    if "project_id" in response:
                        self.created_projects.append(response["project_id"])
                else:
                    error = response.get("error", "Unknown error")
                    result.mark_failure(error, duration, transaction_mode)
                    print(f"✗ Test failed: {error}")

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = str(e)

            if expect_failure:
                result.mark_success(duration, {"error": error_msg}, transaction_mode)
                print(f"✓ Expected exception occurred: {error_msg}")
            else:
                result.mark_failure(error_msg, duration, transaction_mode)
                print(f"✗ Exception occurred: {error_msg}")

        self.results.append(result)
        return result

    # ==================== ORGANIZATION_ONBOARDING TESTS ====================

    async def test_organization_onboarding_basic(self):
        """Test basic organization onboarding"""
        return await self.test_workflow(
            workflow_name="organization_onboarding",
            scenario="basic_success",
            parameters={
                "name": f"Test Org {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "Test organization for workflow testing",
                "type": "team"
            },
            transaction_mode=True
        )

    async def test_organization_onboarding_with_starter_project(self):
        """Test organization onboarding with starter project"""
        return await self.test_workflow(
            workflow_name="organization_onboarding",
            scenario="with_starter_project",
            parameters={
                "name": f"Full Org {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "Organization with starter project",
                "create_starter_project": True,
                "type": "enterprise"
            },
            transaction_mode=True
        )

    async def test_organization_onboarding_missing_name(self):
        """Test organization onboarding with missing name"""
        return await self.test_workflow(
            workflow_name="organization_onboarding",
            scenario="missing_name_error",
            parameters={
                "description": "Missing name field"
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_organization_onboarding_no_transaction(self):
        """Test organization onboarding without transaction mode"""
        return await self.test_workflow(
            workflow_name="organization_onboarding",
            scenario="no_transaction_mode",
            parameters={
                "name": f"No Trans Org {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type": "team"
            },
            transaction_mode=False
        )

    # ==================== SETUP_PROJECT TESTS ====================

    async def test_setup_project_basic(self, org_id: str):
        """Test basic project setup"""
        return await self.test_workflow(
            workflow_name="setup_project",
            scenario="basic_success",
            parameters={
                "name": f"Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "organization_id": org_id,
                "description": "Test project for workflow testing"
            },
            transaction_mode=True
        )

    async def test_setup_project_with_documents(self, org_id: str):
        """Test project setup with initial documents"""
        return await self.test_workflow(
            workflow_name="setup_project",
            scenario="with_initial_documents",
            parameters={
                "name": f"Project with Docs {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "organization_id": org_id,
                "description": "Project with multiple documents",
                "initial_documents": [
                    "Requirements Specification",
                    "Design Document",
                    "Test Plan",
                    "User Guide"
                ]
            },
            transaction_mode=True
        )

    async def test_setup_project_missing_org_id(self):
        """Test project setup with missing organization_id"""
        return await self.test_workflow(
            workflow_name="setup_project",
            scenario="missing_org_id_error",
            parameters={
                "name": "Incomplete Project"
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_setup_project_invalid_org_id(self):
        """Test project setup with invalid organization_id"""
        return await self.test_workflow(
            workflow_name="setup_project",
            scenario="invalid_org_id_error",
            parameters={
                "name": "Invalid Org Project",
                "organization_id": "00000000-0000-0000-0000-000000000000"
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_setup_project_no_transaction(self, org_id: str):
        """Test project setup without transaction mode"""
        return await self.test_workflow(
            workflow_name="setup_project",
            scenario="no_transaction_mode",
            parameters={
                "name": f"No Trans Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "organization_id": org_id
            },
            transaction_mode=False
        )

    # ==================== IMPORT_REQUIREMENTS TESTS ====================

    async def test_import_requirements_basic(self, document_id: str):
        """Test basic requirements import"""
        return await self.test_workflow(
            workflow_name="import_requirements",
            scenario="basic_success",
            parameters={
                "document_id": document_id,
                "requirements": [
                    {
                        "name": "REQ-001",
                        "description": "User authentication system",
                        "priority": "high",
                        "status": "active"
                    },
                    {
                        "name": "REQ-002",
                        "description": "Password reset functionality",
                        "priority": "medium",
                        "status": "active"
                    },
                    {
                        "name": "REQ-003",
                        "description": "User profile management",
                        "priority": "low",
                        "status": "draft"
                    }
                ]
            },
            transaction_mode=True
        )

    async def test_import_requirements_bulk(self, document_id: str):
        """Test bulk requirements import (50 requirements)"""
        requirements = [
            {
                "name": f"REQ-{i:03d}",
                "description": f"Requirement {i} for testing bulk import",
                "priority": ["high", "medium", "low"][i % 3],
                "status": "active"
            }
            for i in range(1, 51)
        ]

        return await self.test_workflow(
            workflow_name="import_requirements",
            scenario="bulk_import_50_requirements",
            parameters={
                "document_id": document_id,
                "requirements": requirements
            },
            transaction_mode=True
        )

    async def test_import_requirements_missing_document_id(self):
        """Test import with missing document_id"""
        return await self.test_workflow(
            workflow_name="import_requirements",
            scenario="missing_document_id_error",
            parameters={
                "requirements": [
                    {"name": "REQ-001", "description": "Test"}
                ]
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_import_requirements_empty_list(self, document_id: str):
        """Test import with empty requirements list"""
        return await self.test_workflow(
            workflow_name="import_requirements",
            scenario="empty_requirements_list",
            parameters={
                "document_id": document_id,
                "requirements": []
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_import_requirements_invalid_format(self, document_id: str):
        """Test import with invalid requirements format"""
        return await self.test_workflow(
            workflow_name="import_requirements",
            scenario="invalid_format_error",
            parameters={
                "document_id": document_id,
                "requirements": "not a list"
            },
            transaction_mode=True,
            expect_failure=True
        )

    # ==================== SETUP_TEST_MATRIX TESTS ====================

    async def test_setup_test_matrix_basic(self, project_id: str):
        """Test basic test matrix setup"""
        return await self.test_workflow(
            workflow_name="setup_test_matrix",
            scenario="basic_success",
            parameters={
                "project_id": project_id,
                "matrix_name": "QA Test Matrix"
            },
            transaction_mode=True
        )

    async def test_setup_test_matrix_missing_project_id(self):
        """Test test matrix with missing project_id"""
        return await self.test_workflow(
            workflow_name="setup_test_matrix",
            scenario="missing_project_id_error",
            parameters={
                "matrix_name": "Incomplete Matrix"
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_setup_test_matrix_invalid_project_id(self):
        """Test test matrix with invalid project_id"""
        return await self.test_workflow(
            workflow_name="setup_test_matrix",
            scenario="invalid_project_id_error",
            parameters={
                "project_id": "00000000-0000-0000-0000-000000000000",
                "matrix_name": "Invalid Project Matrix"
            },
            transaction_mode=True,
            expect_failure=True
        )

    # ==================== BULK_STATUS_UPDATE TESTS ====================

    async def test_bulk_status_update_basic(self, entity_type: str, entity_ids: List[str]):
        """Test basic bulk status update"""
        return await self.test_workflow(
            workflow_name="bulk_status_update",
            scenario="basic_success",
            parameters={
                "entity_type": entity_type,
                "entity_ids": entity_ids,
                "new_status": "approved"
            },
            transaction_mode=True
        )

    async def test_bulk_status_update_missing_entity_type(self, entity_ids: List[str]):
        """Test bulk update with missing entity_type"""
        return await self.test_workflow(
            workflow_name="bulk_status_update",
            scenario="missing_entity_type_error",
            parameters={
                "entity_ids": entity_ids,
                "new_status": "approved"
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_bulk_status_update_missing_entity_ids(self):
        """Test bulk update with missing entity_ids"""
        return await self.test_workflow(
            workflow_name="bulk_status_update",
            scenario="missing_entity_ids_error",
            parameters={
                "entity_type": "requirement",
                "new_status": "approved"
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_bulk_status_update_missing_new_status(self, entity_ids: List[str]):
        """Test bulk update with missing new_status"""
        return await self.test_workflow(
            workflow_name="bulk_status_update",
            scenario="missing_new_status_error",
            parameters={
                "entity_type": "requirement",
                "entity_ids": entity_ids
            },
            transaction_mode=True,
            expect_failure=True
        )

    async def test_bulk_status_update_empty_entity_ids(self):
        """Test bulk update with empty entity_ids list"""
        return await self.test_workflow(
            workflow_name="bulk_status_update",
            scenario="empty_entity_ids_list",
            parameters={
                "entity_type": "requirement",
                "entity_ids": [],
                "new_status": "approved"
            },
            transaction_mode=True,
            expect_failure=True
        )

    # ==================== INVALID WORKFLOW TESTS ====================

    async def test_invalid_workflow_name(self):
        """Test with invalid workflow name"""
        return await self.test_workflow(
            workflow_name="invalid_workflow_xyz",
            scenario="invalid_workflow_error",
            parameters={},
            transaction_mode=True,
            expect_failure=True
        )

    # ==================== TEST ORCHESTRATION ====================

    async def run_all_tests(self):
        """Run all workflow tests"""
        print("\n" + "="*100)
        print("COMPREHENSIVE WORKFLOW TOOL TEST SUITE")
        print("="*100)

        # Phase 1: Organization Onboarding Tests
        print("\n" + "="*100)
        print("PHASE 1: ORGANIZATION_ONBOARDING WORKFLOW TESTS")
        print("="*100)

        await self.test_organization_onboarding_missing_name()
        org_result = await self.test_organization_onboarding_basic()
        await self.test_organization_onboarding_with_starter_project()
        await self.test_organization_onboarding_no_transaction()

        # Get org_id from successful onboarding
        org_id = None
        if org_result.status == "PASS" and org_result.response:
            org_id = org_result.response.get("organization_id")

        if not org_id:
            print("\n✗ Failed to create organization. Cannot proceed with dependent tests.")
            return self.generate_report()

        print(f"\n✓ Using organization ID: {org_id}")

        # Phase 2: Setup Project Tests
        print("\n" + "="*100)
        print("PHASE 2: SETUP_PROJECT WORKFLOW TESTS")
        print("="*100)

        await self.test_setup_project_missing_org_id()
        await self.test_setup_project_invalid_org_id()
        project_result = await self.test_setup_project_basic(org_id)
        await self.test_setup_project_with_documents(org_id)
        await self.test_setup_project_no_transaction(org_id)

        # Get project_id and document_id
        project_id = None
        document_id = None

        if project_result.status == "PASS" and project_result.response:
            project_id = project_result.response.get("project_id")

            # Get document from results if any were created
            results = project_result.response.get("results", [])
            for result_item in results:
                if result_item.get("step", "").startswith("create_document"):
                    doc_result = result_item.get("result")
                    if doc_result and "id" in doc_result:
                        document_id = doc_result["id"]
                        break

        # If no document from project setup, create one manually
        if project_id and not document_id:
            print("\n📝 Creating document for import_requirements tests...")
            try:
                doc_response = await entity_operation(
                    auth_token=self.auth_token,
                    entity_type="document",
                    data={
                        "name": "Test Requirements Document",
                        "project_id": project_id,
                        "description": "Document for testing requirements import"
                    }
                )
                if "id" in doc_response:
                    document_id = doc_response["id"]
                    print(f"✓ Document created: {document_id}")
            except Exception as e:
                print(f"✗ Failed to create document: {e}")

        # Phase 3: Import Requirements Tests
        if document_id:
            print("\n" + "="*100)
            print("PHASE 3: IMPORT_REQUIREMENTS WORKFLOW TESTS")
            print("="*100)

            await self.test_import_requirements_missing_document_id()
            await self.test_import_requirements_invalid_format(document_id)
            await self.test_import_requirements_empty_list(document_id)
            req_result = await self.test_import_requirements_basic(document_id)
            await self.test_import_requirements_bulk(document_id)

            # Get requirement IDs for bulk update tests
            requirement_ids = []
            if req_result.status == "PASS" and req_result.response:
                results = req_result.response.get("results", [])
                for result_item in results:
                    if result_item.get("status") == "success":
                        req = result_item.get("result")
                        if req and "id" in req:
                            requirement_ids.append(req["id"])
        else:
            print("\n✗ No document available. Skipping import_requirements tests.")
            requirement_ids = []

        # Phase 4: Setup Test Matrix Tests
        if project_id:
            print("\n" + "="*100)
            print("PHASE 4: SETUP_TEST_MATRIX WORKFLOW TESTS")
            print("="*100)

            await self.test_setup_test_matrix_missing_project_id()
            await self.test_setup_test_matrix_invalid_project_id()
            await self.test_setup_test_matrix_basic(project_id)
        else:
            print("\n✗ No project available. Skipping setup_test_matrix tests.")

        # Phase 5: Bulk Status Update Tests
        if requirement_ids:
            print("\n" + "="*100)
            print("PHASE 5: BULK_STATUS_UPDATE WORKFLOW TESTS")
            print("="*100)

            await self.test_bulk_status_update_missing_entity_type(requirement_ids)
            await self.test_bulk_status_update_missing_entity_ids()
            await self.test_bulk_status_update_missing_new_status(requirement_ids)
            await self.test_bulk_status_update_empty_entity_ids()
            await self.test_bulk_status_update_basic("requirement", requirement_ids[:3])
        else:
            print("\n✗ No requirements available. Skipping bulk_status_update tests.")

        # Phase 6: Invalid Workflow Tests
        print("\n" + "="*100)
        print("PHASE 6: INVALID WORKFLOW TESTS")
        print("="*100)

        await self.test_invalid_workflow_name()

        # Generate final report
        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("\n" + "="*100)
        print("COMPREHENSIVE TEST REPORT")
        print("="*100)

        # Group by workflow
        workflows = {}
        for result in self.results:
            if result.workflow_name not in workflows:
                workflows[result.workflow_name] = []
            workflows[result.workflow_name].append(result)

        # Overall statistics
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")

        print("\nOVERALL SUMMARY:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"  Failed: {failed} ({failed/total*100:.1f}%)")

        # Per-workflow summary
        print("\nPER-WORKFLOW SUMMARY:")
        for workflow_name, results in sorted(workflows.items()):
            wf_total = len(results)
            wf_passed = sum(1 for r in results if r.status == "PASS")
            wf_failed = sum(1 for r in results if r.status == "FAIL")

            print(f"\n  {workflow_name}:")
            print(f"    Total: {wf_total}")
            print(f"    Passed: {wf_passed} ({wf_passed/wf_total*100:.1f}%)")
            print(f"    Failed: {wf_failed}")

            for result in results:
                status_icon = "✓" if result.status == "PASS" else "✗"
                print(f"      {status_icon} {result.scenario} ({result.duration_ms:.2f}ms)")
                if result.error_message:
                    print(f"        Error: {result.error_message}")

        # Performance metrics
        if self.results:
            durations = [r.duration_ms for r in self.results]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            print("\nPERFORMANCE METRICS:")
            print(f"  Average Duration: {avg_duration:.2f}ms")
            print(f"  Max Duration: {max_duration:.2f}ms")
            print(f"  Min Duration: {min_duration:.2f}ms")

        # Transaction mode usage
        transaction_tests = sum(1 for r in self.results if r.transaction_mode_used)
        print("\nTRANSACTION MODE:")
        print(f"  Tests with transaction_mode=True: {transaction_tests}/{total}")
        print(f"  Tests with transaction_mode=False: {total - transaction_tests}/{total}")

        # Build report data
        report_data = {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": (passed/total*100) if total > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "workflows": {
                workflow_name: {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.status == "PASS"),
                    "failed": sum(1 for r in results if r.status == "FAIL"),
                    "scenarios": [r.to_dict() for r in results]
                }
                for workflow_name, results in workflows.items()
            },
            "performance": {
                "avg_duration_ms": avg_duration if self.results else 0,
                "max_duration_ms": max_duration if self.results else 0,
                "min_duration_ms": min_duration if self.results else 0
            },
            "transaction_mode": {
                "with_transaction": transaction_tests,
                "without_transaction": total - transaction_tests
            },
            "created_entities": {
                "organizations": self.created_orgs,
                "projects": self.created_projects,
                "documents": self.created_documents,
                "requirements": self.created_requirements
            }
        }

        # Save to file
        report_file = "/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/workflow_test_comprehensive_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n\nDetailed report saved to: {report_file}")
        print("="*100 + "\n")

        return report_data


async def main():
    """Main test execution"""
    tester = WorkflowTester()

    try:
        report = await tester.run_all_tests()

        # Print summary
        print("\n" + "="*100)
        print("TEST EXECUTION COMPLETE")
        print("="*100)
        print(f"\nTotal Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Pass Rate: {report['summary']['pass_rate']:.1f}%")

        # List available workflows
        print("\n" + "="*100)
        print("AVAILABLE WORKFLOWS:")
        print("="*100)
        for workflow_name, workflow_data in sorted(report['workflows'].items()):
            print(f"\n  {workflow_name}:")
            print(f"    Tests: {workflow_data['total']}")
            print(f"    Passed: {workflow_data['passed']}")
            print(f"    Failed: {workflow_data['failed']}")

        return report

    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())
