"""
Live Testing of ALL Atoms Workflow Tool Workflows
Tests each workflow with real authentication and proper prerequisites.

Available Workflows:
1. organization_onboarding - Complete organization setup
2. setup_project - Create project with initial structure
3. import_requirements - Import requirements from external source
4. setup_test_matrix - Set up test matrix for a project
5. bulk_status_update - Update status for multiple entities

Run with: python tests/test_all_workflows_live.py
"""

import os
import sys
import json
import time
import uuid
import asyncio
from typing import Any, Dict, List
from datetime import datetime

import httpx

# Configuration
MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

SUPABASE_URL = os.getenv("
SUPABASE_KEY = os.getenv("

class WorkflowTestRunner:
    """Comprehensive workflow testing with real MCP calls."""

    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        self.results = {
            "test_run_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "workflows_tested": [],
            "summary": {},
            "detailed_results": {}
        }
        self.created_entities = {
            "organizations": [],
            "projects": [],
            "documents": [],
            "requirements": [],
            "test_matrices": [],
        }

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result."""
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": f"tools/{tool_name}",
            "params": params,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.base_url, json=payload, headers=self.headers)

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "tool": tool_name
                    }

                body = response.json()
                if "result" in body:
                    return body["result"]

                return {
                    "success": False,
                    "error": body.get("error", "Unknown error"),
                    "tool": tool_name
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "tool": tool_name
                }

    async def test_organization_onboarding(self) -> Dict[str, Any]:
        """Test 1: Organization Onboarding Workflow"""
        print("\n" + "="*80)
        print("TEST 1: organization_onboarding")
        print("="*80)

        start_time = time.time()
        test_result = {
            "workflow": "organization_onboarding",
            "scenarios": [],
            "entities_created": [],
            "relationships_created": []
        }

        # Scenario 1: Basic onboarding
        print("\n[Scenario 1] Basic organization onboarding...")
        result1 = await self.call_tool("workflow_tool", {
            "workflow": "organization_onboarding",
            "parameters": {
                "name": f"Test Org {uuid.uuid4().hex[:8]}",
                "description": "Organization for workflow testing"
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result1, indent=2)}")

        scenario1 = {
            "name": "basic_onboarding",
            "success": result1.get("success", False),
            "result": result1,
            "transaction_mode": True
        }
        test_result["scenarios"].append(scenario1)

        if result1.get("success") and result1.get("data", {}).get("organization_id"):
            org_id = result1["data"]["organization_id"]
            self.created_entities["organizations"].append(org_id)
            test_result["entities_created"].append({"type": "organization", "id": org_id})

        # Scenario 2: Onboarding with starter project
        print("\n[Scenario 2] Onboarding with starter project...")
        result2 = await self.call_tool("workflow_tool", {
            "workflow": "organization_onboarding",
            "parameters": {
                "name": f"Full Setup Org {uuid.uuid4().hex[:8]}",
                "description": "Organization with starter project",
                "create_starter_project": True
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result2, indent=2)}")

        scenario2 = {
            "name": "onboarding_with_project",
            "success": result2.get("success", False),
            "result": result2,
            "transaction_mode": True
        }
        test_result["scenarios"].append(scenario2)

        # Scenario 3: Error handling - missing required params
        print("\n[Scenario 3] Error handling - missing name...")
        result3 = await self.call_tool("workflow_tool", {
            "workflow": "organization_onboarding",
            "parameters": {},
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result3, indent=2)}")

        scenario3 = {
            "name": "missing_required_params",
            "success": not result3.get("success", True),  # Should fail
            "result": result3,
            "transaction_mode": True,
            "expected_error": True
        }
        test_result["scenarios"].append(scenario3)

        test_result["duration_seconds"] = time.time() - start_time
        test_result["total_scenarios"] = len(test_result["scenarios"])
        test_result["passed_scenarios"] = sum(1 for s in test_result["scenarios"] if s["success"])

        return test_result

    async def test_setup_project(self) -> Dict[str, Any]:
        """Test 2: Setup Project Workflow"""
        print("\n" + "="*80)
        print("TEST 2: setup_project")
        print("="*80)

        start_time = time.time()
        test_result = {
            "workflow": "setup_project",
            "scenarios": [],
            "entities_created": [],
            "relationships_created": []
        }

        # Need an organization first
        if not self.created_entities["organizations"]:
            print("\n[Prerequisite] Creating organization...")
            org_result = await self.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "create",
                "data": {
                    "name": f"Project Test Org {uuid.uuid4().hex[:8]}",
                    "slug": f"proj-test-{uuid.uuid4().hex[:8]}",
                    "type": "team"
                }
            })

            if org_result.get("success") and org_result.get("data", {}).get("id"):
                org_id = org_result["data"]["id"]
                self.created_entities["organizations"].append(org_id)
                print(f"✓ Created organization: {org_id}")
            else:
                print(f"✗ Failed to create organization: {org_result.get('error')}")
                test_result["error"] = "Failed to create prerequisite organization"
                return test_result

        org_id = self.created_entities["organizations"][0]

        # Scenario 1: Basic project setup
        print("\n[Scenario 1] Basic project setup...")
        result1 = await self.call_tool("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": f"Test Project {uuid.uuid4().hex[:8]}",
                "organization_id": org_id,
                "description": "Basic test project"
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result1, indent=2)}")

        scenario1 = {
            "name": "basic_setup",
            "success": result1.get("success", False),
            "result": result1,
            "transaction_mode": True
        }
        test_result["scenarios"].append(scenario1)

        if result1.get("success") and result1.get("data", {}).get("project_id"):
            proj_id = result1["data"]["project_id"]
            self.created_entities["projects"].append(proj_id)
            test_result["entities_created"].append({"type": "project", "id": proj_id})

        # Scenario 2: Project with initial documents
        print("\n[Scenario 2] Project with initial documents...")
        result2 = await self.call_tool("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": f"Doc Project {uuid.uuid4().hex[:8]}",
                "organization_id": org_id,
                "initial_documents": ["Requirements", "Design", "Test Plan"]
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result2, indent=2)}")

        scenario2 = {
            "name": "with_initial_documents",
            "success": result2.get("success", False),
            "result": result2,
            "transaction_mode": True
        }
        test_result["scenarios"].append(scenario2)

        if result2.get("success") and result2.get("data", {}).get("project_id"):
            proj_id = result2["data"]["project_id"]
            self.created_entities["projects"].append(proj_id)

        # Scenario 3: Error handling - missing org_id
        print("\n[Scenario 3] Error handling - missing organization_id...")
        result3 = await self.call_tool("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Incomplete Project"
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result3, indent=2)}")

        scenario3 = {
            "name": "missing_required_params",
            "success": not result3.get("success", True),  # Should fail
            "result": result3,
            "transaction_mode": True,
            "expected_error": True
        }
        test_result["scenarios"].append(scenario3)

        test_result["duration_seconds"] = time.time() - start_time
        test_result["total_scenarios"] = len(test_result["scenarios"])
        test_result["passed_scenarios"] = sum(1 for s in test_result["scenarios"] if s["success"])

        return test_result

    async def test_import_requirements(self) -> Dict[str, Any]:
        """Test 3: Import Requirements Workflow"""
        print("\n" + "="*80)
        print("TEST 3: import_requirements")
        print("="*80)

        start_time = time.time()
        test_result = {
            "workflow": "import_requirements",
            "scenarios": [],
            "entities_created": [],
            "relationships_created": []
        }

        # Need a document first
        if not self.created_entities["projects"]:
            print("✗ No project available, skipping import_requirements test")
            test_result["skipped"] = True
            test_result["reason"] = "No project available"
            return test_result

        project_id = self.created_entities["projects"][0]

        print(f"\n[Prerequisite] Creating document in project {project_id}...")
        doc_result = await self.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "create",
            "data": {
                "name": f"Requirements Doc {uuid.uuid4().hex[:8]}",
                "project_id": project_id,
                "description": "Document for testing requirements import"
            }
        })

        if not doc_result.get("success") or not doc_result.get("data", {}).get("id"):
            print(f"✗ Failed to create document: {doc_result.get('error')}")
            test_result["error"] = "Failed to create prerequisite document"
            return test_result

        doc_id = doc_result["data"]["id"]
        self.created_entities["documents"].append(doc_id)
        print(f"✓ Created document: {doc_id}")

        # Scenario 1: Import multiple requirements
        print("\n[Scenario 1] Import multiple requirements...")
        result1 = await self.call_tool("workflow_tool", {
            "workflow": "import_requirements",
            "parameters": {
                "document_id": doc_id,
                "requirements": [
                    {"name": "REQ-001", "description": "User authentication", "priority": "high"},
                    {"name": "REQ-002", "description": "Data validation", "priority": "medium"},
                    {"name": "REQ-003", "description": "Error handling", "priority": "high"},
                    {"name": "REQ-004", "description": "Logging", "priority": "low"}
                ]
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result1, indent=2)}")

        scenario1 = {
            "name": "import_multiple_requirements",
            "success": result1.get("success", False),
            "result": result1,
            "transaction_mode": True
        }
        test_result["scenarios"].append(scenario1)

        # Scenario 2: Error handling - missing document_id
        print("\n[Scenario 2] Error handling - missing document_id...")
        result2 = await self.call_tool("workflow_tool", {
            "workflow": "import_requirements",
            "parameters": {
                "requirements": [{"name": "REQ-X", "description": "Test"}]
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result2, indent=2)}")

        scenario2 = {
            "name": "missing_required_params",
            "success": not result2.get("success", True),  # Should fail
            "result": result2,
            "transaction_mode": True,
            "expected_error": True
        }
        test_result["scenarios"].append(scenario2)

        test_result["duration_seconds"] = time.time() - start_time
        test_result["total_scenarios"] = len(test_result["scenarios"])
        test_result["passed_scenarios"] = sum(1 for s in test_result["scenarios"] if s["success"])

        return test_result

    async def test_setup_test_matrix(self) -> Dict[str, Any]:
        """Test 4: Setup Test Matrix Workflow"""
        print("\n" + "="*80)
        print("TEST 4: setup_test_matrix")
        print("="*80)

        start_time = time.time()
        test_result = {
            "workflow": "setup_test_matrix",
            "scenarios": [],
            "entities_created": [],
            "relationships_created": []
        }

        if not self.created_entities["projects"]:
            print("✗ No project available, skipping setup_test_matrix test")
            test_result["skipped"] = True
            test_result["reason"] = "No project available"
            return test_result

        project_id = self.created_entities["projects"][0]

        # Scenario 1: Basic test matrix setup
        print(f"\n[Scenario 1] Basic test matrix setup for project {project_id}...")
        result1 = await self.call_tool("workflow_tool", {
            "workflow": "setup_test_matrix",
            "parameters": {
                "project_id": project_id,
                "matrix_name": f"Test Matrix {uuid.uuid4().hex[:8]}"
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result1, indent=2)}")

        scenario1 = {
            "name": "basic_test_matrix",
            "success": result1.get("success", False),
            "result": result1,
            "transaction_mode": True
        }
        test_result["scenarios"].append(scenario1)

        # Scenario 2: Error handling - missing project_id
        print("\n[Scenario 2] Error handling - missing project_id...")
        result2 = await self.call_tool("workflow_tool", {
            "workflow": "setup_test_matrix",
            "parameters": {},
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result2, indent=2)}")

        scenario2 = {
            "name": "missing_required_params",
            "success": not result2.get("success", True),  # Should fail
            "result": result2,
            "transaction_mode": True,
            "expected_error": True
        }
        test_result["scenarios"].append(scenario2)

        test_result["duration_seconds"] = time.time() - start_time
        test_result["total_scenarios"] = len(test_result["scenarios"])
        test_result["passed_scenarios"] = sum(1 for s in test_result["scenarios"] if s["success"])

        return test_result

    async def test_bulk_status_update(self) -> Dict[str, Any]:
        """Test 5: Bulk Status Update Workflow"""
        print("\n" + "="*80)
        print("TEST 5: bulk_status_update")
        print("="*80)

        start_time = time.time()
        test_result = {
            "workflow": "bulk_status_update",
            "scenarios": [],
            "entities_created": [],
            "relationships_created": []
        }

        if not self.created_entities["documents"]:
            print("✗ No documents available, creating requirements first...")
            test_result["skipped"] = True
            test_result["reason"] = "No requirements available for bulk update"
            return test_result

        # Get requirements to update
        doc_id = self.created_entities["documents"][0]

        print(f"\n[Prerequisite] Getting requirements from document {doc_id}...")
        req_query = await self.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "list",
            "parent_type": "document",
            "parent_id": doc_id
        })

        if not req_query.get("success") or not req_query.get("data"):
            print("✗ No requirements found, creating some...")
            # Create some requirements
            for i in range(3):
                await self.call_tool("entity_tool", {
                    "entity_type": "requirement",
                    "operation": "create",
                    "data": {
                        "name": f"REQ-BULK-{i:03d}",
                        "description": f"Requirement for bulk update {i}",
                        "document_id": doc_id,
                        "status": "draft"
                    }
                })

            # Re-query
            req_query = await self.call_tool("entity_tool", {
                "entity_type": "requirement",
                "operation": "list",
                "parent_type": "document",
                "parent_id": doc_id
            })

        if not req_query.get("success") or not req_query.get("data"):
            print("✗ Still no requirements available")
            test_result["error"] = "Could not create requirements for bulk update"
            return test_result

        requirement_ids = [req["id"] for req in req_query["data"]][:3]  # Use first 3
        print(f"✓ Found {len(requirement_ids)} requirements to update")

        # Scenario 1: Bulk status update
        print(f"\n[Scenario 1] Bulk update {len(requirement_ids)} requirements to 'approved'...")
        result1 = await self.call_tool("workflow_tool", {
            "workflow": "bulk_status_update",
            "parameters": {
                "entity_type": "requirement",
                "entity_ids": requirement_ids,
                "new_status": "approved"
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result1, indent=2)}")

        scenario1 = {
            "name": "bulk_update_requirements",
            "success": result1.get("success", False),
            "result": result1,
            "transaction_mode": True
        }
        test_result["scenarios"].append(scenario1)

        # Scenario 2: Error handling - missing params
        print("\n[Scenario 2] Error handling - missing new_status...")
        result2 = await self.call_tool("workflow_tool", {
            "workflow": "bulk_status_update",
            "parameters": {
                "entity_type": "requirement",
                "entity_ids": requirement_ids
            },
            "transaction_mode": True
        })

        print(f"Result: {json.dumps(result2, indent=2)}")

        scenario2 = {
            "name": "missing_required_params",
            "success": not result2.get("success", True),  # Should fail
            "result": result2,
            "transaction_mode": True,
            "expected_error": True
        }
        test_result["scenarios"].append(scenario2)

        test_result["duration_seconds"] = time.time() - start_time
        test_result["total_scenarios"] = len(test_result["scenarios"])
        test_result["passed_scenarios"] = sum(1 for s in test_result["scenarios"] if s["success"])

        return test_result

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all workflow tests and generate comprehensive report."""
        print("\n" + "="*80)
        print("COMPREHENSIVE WORKFLOW TESTING - ALL WORKFLOWS")
        print("="*80)

        overall_start = time.time()

        # Test each workflow
        results = []

        # Test 1: Organization Onboarding
        org_result = await self.test_organization_onboarding()
        results.append(org_result)

        # Test 2: Setup Project
        project_result = await self.test_setup_project()
        results.append(project_result)

        # Test 3: Import Requirements
        import_result = await self.test_import_requirements()
        results.append(import_result)

        # Test 4: Setup Test Matrix
        matrix_result = await self.test_setup_test_matrix()
        results.append(matrix_result)

        # Test 5: Bulk Status Update
        bulk_result = await self.test_bulk_status_update()
        results.append(bulk_result)

        # Generate summary
        total_scenarios = sum(r.get("total_scenarios", 0) for r in results)
        passed_scenarios = sum(r.get("passed_scenarios", 0) for r in results)

        self.results["workflows_tested"] = [r["workflow"] for r in results]
        self.results["detailed_results"] = {r["workflow"]: r for r in results}
        self.results["summary"] = {
            "total_workflows": len(results),
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "failed_scenarios": total_scenarios - passed_scenarios,
            "pass_rate": f"{(passed_scenarios/total_scenarios*100):.1f}%" if total_scenarios > 0 else "N/A",
            "total_duration_seconds": time.time() - overall_start,
            "entities_created": self.created_entities
        }

        return self.results

async def main():
    """Main test execution."""
    print("Atoms MCP Workflow Testing")
    print("=" * 80)

    # Check environment
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ Supabase environment variables not configured")
        sys.exit(1)

    # Authenticate
    print("\n[Auth] Authenticating with Supabase...")
    try:
        client = 
        auth_response = client
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })

        if not auth_response.session or not auth_response.session.access_token:
            print("✗ No session obtained")
            sys.exit(1)

        auth_token = auth_response.session.access_token
        print(f"✓ Authenticated successfully")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        sys.exit(1)

    # Run tests
    runner = WorkflowTestRunner(auth_token)
    results = await runner.run_all_tests()

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(json.dumps(results["summary"], indent=2))

    # Save full report
    report_file = "/Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/tests/workflow_live_test_report.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Full report saved to: {report_file}")

    # Return exit code based on results
    if results["summary"]["failed_scenarios"] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
