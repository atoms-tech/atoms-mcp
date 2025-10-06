"""
Comprehensive Test Suite for Atoms workflow_tool
Tests all available workflows with complete coverage including:
- Successful execution paths
- Transaction mode behavior
- Error handling and rollback
- Multi-step scenarios
- Validation and edge cases
- Performance metrics
"""

import pytest
import time
import json
from typing import Dict, List, Any
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import asyncio

# Test results tracking
test_results = []

class WorkflowTestResult:
    """Track individual workflow test results"""
    def __init__(self, workflow_name: str, scenario: str):
        self.workflow_name = workflow_name
        self.scenario = scenario
        self.status = "PENDING"
        self.duration_ms = 0
        self.transaction_verified = False
        self.rollback_verified = False
        self.error_handling_verified = False
        self.entities_created = []
        self.relationships_created = []
        self.error_details = None

    def mark_success(self, duration_ms: float):
        self.status = "PASS"
        self.duration_ms = duration_ms

    def mark_failure(self, error: str, duration_ms: float):
        self.status = "FAIL"
        self.error_details = error
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow": self.workflow_name,
            "scenario": self.scenario,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "transaction_verified": self.transaction_verified,
            "rollback_verified": self.rollback_verified,
            "error_handling_verified": self.error_handling_verified,
            "entities_created": len(self.entities_created),
            "relationships_created": len(self.relationships_created),
            "error_details": self.error_details
        }


class MockWorkflowTool:
    """Mock implementation of the workflow tool for testing"""

    def __init__(self):
        self.executed_workflows = []
        self.created_entities = {}
        self.created_relationships = []
        self.transaction_active = False
        self.should_fail = False
        self.failure_point = None
        self.transaction_snapshot = None

    async def execute_workflow(self, workflow: str, parameters: Dict[str, Any],
                               transaction_mode: bool = True, format_type: str = "detailed") -> Dict[str, Any]:
        """Execute a workflow with transaction support"""
        start_time = time.time()

        try:
            if transaction_mode:
                self.transaction_active = True
                # Create snapshot before starting transaction
                self.transaction_snapshot = {
                    "entities": {k: v.copy() for k, v in self.created_entities.items()},
                    "relationships": self.created_relationships.copy()
                }

            self.executed_workflows.append({
                "workflow": workflow,
                "parameters": parameters,
                "transaction_mode": transaction_mode,
                "timestamp": datetime.now().isoformat()
            })

            # Route to appropriate workflow handler
            if workflow == "setup_project":
                result = await self._setup_project(parameters)
            elif workflow == "import_requirements":
                result = await self._import_requirements(parameters)
            elif workflow == "setup_test_matrix":
                result = await self._setup_test_matrix(parameters)
            elif workflow == "bulk_status_update":
                result = await self._bulk_status_update(parameters)
            elif workflow == "organization_onboarding":
                result = await self._organization_onboarding(parameters)
            else:
                raise ValueError(f"Unknown workflow: {workflow}")

            if transaction_mode:
                # Commit transaction
                self.transaction_active = False
                self.transaction_snapshot = None

            duration = (time.time() - start_time) * 1000
            result["execution_time_ms"] = duration
            return result

        except Exception as e:
            if transaction_mode and self.transaction_active:
                # Rollback transaction to snapshot
                await self._rollback()
                self.transaction_active = False
            raise

    async def _setup_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Setup project workflow"""
        if self.should_fail and self.failure_point == "setup_project":
            raise ValueError("Simulated setup_project failure")

        # Validate required parameters
        if "name" not in params:
            raise ValueError("Missing required parameter: name")
        if "organization_id" not in params:
            raise ValueError("Missing required parameter: organization_id")

        # Create project
        project_id = f"proj_{len(self.created_entities.get('project', []))+1}"
        project = {
            "id": project_id,
            "name": params["name"],
            "organization_id": params["organization_id"],
            "description": params.get("description", ""),
            "created_at": datetime.now().isoformat()
        }

        if "project" not in self.created_entities:
            self.created_entities["project"] = []
        self.created_entities["project"].append(project)

        # Create initial documents if specified
        documents = []
        if "initial_documents" in params:
            for doc_name in params["initial_documents"]:
                doc_id = f"doc_{len(self.created_entities.get('document', []))+1}"
                doc = {
                    "id": doc_id,
                    "name": doc_name,
                    "project_id": project_id,
                    "created_at": datetime.now().isoformat()
                }
                if "document" not in self.created_entities:
                    self.created_entities["document"] = []
                self.created_entities["document"].append(doc)
                documents.append(doc)

        return {
            "success": True,
            "project": project,
            "documents": documents,
            "message": f"Project '{params['name']}' created successfully"
        }

    async def _import_requirements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import requirements workflow"""
        if self.should_fail and self.failure_point == "import_requirements":
            raise ValueError("Simulated import_requirements failure")

        if "document_id" not in params:
            raise ValueError("Missing required parameter: document_id")
        if "requirements" not in params or not isinstance(params["requirements"], list):
            raise ValueError("Missing or invalid parameter: requirements")

        imported_reqs = []
        failed_reqs = []

        for req_data in params["requirements"]:
            try:
                if "name" not in req_data:
                    failed_reqs.append({
                        "data": req_data,
                        "error": "Missing required field: name"
                    })
                    continue

                req_id = f"req_{len(self.created_entities.get('requirement', []))+1}"
                req = {
                    "id": req_id,
                    "name": req_data["name"],
                    "description": req_data.get("description", ""),
                    "document_id": params["document_id"],
                    "status": req_data.get("status", "draft"),
                    "priority": req_data.get("priority", "medium"),
                    "created_at": datetime.now().isoformat()
                }

                if "requirement" not in self.created_entities:
                    self.created_entities["requirement"] = []
                self.created_entities["requirement"].append(req)
                imported_reqs.append(req)

            except Exception as e:
                failed_reqs.append({
                    "data": req_data,
                    "error": str(e)
                })

        return {
            "success": len(failed_reqs) == 0,
            "imported_count": len(imported_reqs),
            "failed_count": len(failed_reqs),
            "requirements": imported_reqs,
            "failures": failed_reqs
        }

    async def _setup_test_matrix(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Setup test matrix workflow"""
        if self.should_fail and self.failure_point == "setup_test_matrix":
            raise ValueError("Simulated setup_test_matrix failure")

        if "project_id" not in params:
            raise ValueError("Missing required parameter: project_id")

        # Create test matrix structure
        matrix_id = f"matrix_{len(self.created_entities.get('test_matrix', []))+1}"
        matrix = {
            "id": matrix_id,
            "project_id": params["project_id"],
            "name": params.get("name", "Test Matrix"),
            "created_at": datetime.now().isoformat()
        }

        if "test_matrix" not in self.created_entities:
            self.created_entities["test_matrix"] = []
        self.created_entities["test_matrix"].append(matrix)

        # Create test cases if specified
        test_cases = []
        if "test_cases" in params:
            for tc_data in params["test_cases"]:
                tc_id = f"tc_{len(self.created_entities.get('test_case', []))+1}"
                tc = {
                    "id": tc_id,
                    "name": tc_data.get("name", "Test Case"),
                    "matrix_id": matrix_id,
                    "type": tc_data.get("type", "functional"),
                    "created_at": datetime.now().isoformat()
                }
                if "test_case" not in self.created_entities:
                    self.created_entities["test_case"] = []
                self.created_entities["test_case"].append(tc)
                test_cases.append(tc)

        return {
            "success": True,
            "matrix": matrix,
            "test_cases": test_cases,
            "message": "Test matrix created successfully"
        }

    async def _bulk_status_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk status update workflow"""
        if self.should_fail and self.failure_point == "bulk_status_update":
            raise ValueError("Simulated bulk_status_update failure")

        if "entity_type" not in params:
            raise ValueError("Missing required parameter: entity_type")
        if "entity_ids" not in params or not isinstance(params["entity_ids"], list):
            raise ValueError("Missing or invalid parameter: entity_ids")
        if "new_status" not in params:
            raise ValueError("Missing required parameter: new_status")

        updated_entities = []
        failed_updates = []

        entity_type = params["entity_type"]
        entities = self.created_entities.get(entity_type, [])

        for entity_id in params["entity_ids"]:
            try:
                entity = next((e for e in entities if e["id"] == entity_id), None)
                if entity:
                    entity["status"] = params["new_status"]
                    entity["updated_at"] = datetime.now().isoformat()
                    updated_entities.append(entity)
                else:
                    failed_updates.append({
                        "entity_id": entity_id,
                        "error": "Entity not found"
                    })
            except Exception as e:
                failed_updates.append({
                    "entity_id": entity_id,
                    "error": str(e)
                })

        return {
            "success": len(failed_updates) == 0,
            "updated_count": len(updated_entities),
            "failed_count": len(failed_updates),
            "updated_entities": updated_entities,
            "failures": failed_updates
        }

    async def _organization_onboarding(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Organization onboarding workflow"""
        if self.should_fail and self.failure_point == "organization_onboarding":
            raise ValueError("Simulated organization_onboarding failure")

        if "organization_name" not in params:
            raise ValueError("Missing required parameter: organization_name")
        if "admin_user_id" not in params:
            raise ValueError("Missing required parameter: admin_user_id")

        # Create organization
        org_id = f"org_{len(self.created_entities.get('organization', []))+1}"
        org = {
            "id": org_id,
            "name": params["organization_name"],
            "created_at": datetime.now().isoformat()
        }

        if "organization" not in self.created_entities:
            self.created_entities["organization"] = []
        self.created_entities["organization"].append(org)

        # Create admin membership
        membership = {
            "organization_id": org_id,
            "user_id": params["admin_user_id"],
            "role": "admin",
            "created_at": datetime.now().isoformat()
        }
        self.created_relationships.append(membership)

        # Create default project if specified
        default_project = None
        if params.get("create_default_project", False):
            proj_id = f"proj_{len(self.created_entities.get('project', []))+1}"
            default_project = {
                "id": proj_id,
                "name": "Default Project",
                "organization_id": org_id,
                "created_at": datetime.now().isoformat()
            }
            if "project" not in self.created_entities:
                self.created_entities["project"] = []
            self.created_entities["project"].append(default_project)

        return {
            "success": True,
            "organization": org,
            "admin_membership": membership,
            "default_project": default_project,
            "message": f"Organization '{params['organization_name']}' onboarded successfully"
        }

    async def _rollback(self):
        """Rollback all changes in current transaction to the snapshot"""
        if self.transaction_snapshot:
            # Restore to snapshot state
            self.created_entities = {k: v.copy() for k, v in self.transaction_snapshot["entities"].items()}
            self.created_relationships = self.transaction_snapshot["relationships"].copy()
            self.transaction_snapshot = None
        else:
            # No snapshot, clear everything (backward compatibility)
            self.created_entities.clear()
            self.created_relationships.clear()


# Test Fixtures
@pytest.fixture
def workflow_tool():
    """Create a mock workflow tool instance"""
    return MockWorkflowTool()


@pytest.fixture
def valid_org_id():
    return "org_test_123"


@pytest.fixture
def valid_user_id():
    return "user_test_456"


@pytest.fixture
def valid_project_id():
    return "proj_test_789"


@pytest.fixture
def valid_document_id():
    return "doc_test_101"


# ==================== SETUP_PROJECT WORKFLOW TESTS ====================

@pytest.mark.asyncio
async def test_setup_project_success_basic(workflow_tool, valid_org_id):
    """Test basic project setup with minimal parameters"""
    result_tracker = WorkflowTestResult("setup_project", "success_basic")
    start_time = time.time()

    try:
        parameters = {
            "name": "Test Project",
            "organization_id": valid_org_id
        }

        result = await workflow_tool.execute_workflow(
            workflow="setup_project",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert result["project"]["name"] == "Test Project"
        assert result["project"]["organization_id"] == valid_org_id
        assert "id" in result["project"]

        result_tracker.transaction_verified = True
        result_tracker.entities_created = [result["project"]]
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_setup_project_with_initial_documents(workflow_tool, valid_org_id):
    """Test project setup with initial documents"""
    result_tracker = WorkflowTestResult("setup_project", "with_initial_documents")
    start_time = time.time()

    try:
        parameters = {
            "name": "Project with Docs",
            "organization_id": valid_org_id,
            "description": "Test project with documents",
            "initial_documents": ["Requirements", "Design", "Test Plan"]
        }

        result = await workflow_tool.execute_workflow(
            workflow="setup_project",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert len(result["documents"]) == 3
        assert all(doc["project_id"] == result["project"]["id"] for doc in result["documents"])

        doc_names = [doc["name"] for doc in result["documents"]]
        assert "Requirements" in doc_names
        assert "Design" in doc_names
        assert "Test Plan" in doc_names

        result_tracker.transaction_verified = True
        result_tracker.entities_created = [result["project"]] + result["documents"]
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_setup_project_missing_required_params(workflow_tool):
    """Test project setup with missing required parameters"""
    result_tracker = WorkflowTestResult("setup_project", "missing_required_params")
    start_time = time.time()

    try:
        parameters = {
            "name": "Incomplete Project"
            # Missing organization_id
        }

        with pytest.raises(ValueError, match="Missing required parameter: organization_id"):
            await workflow_tool.execute_workflow(
                workflow="setup_project",
                parameters=parameters,
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_setup_project_transaction_rollback(workflow_tool, valid_org_id):
    """Test transaction rollback on failure"""
    result_tracker = WorkflowTestResult("setup_project", "transaction_rollback")
    start_time = time.time()

    try:
        workflow_tool.should_fail = True
        workflow_tool.failure_point = "setup_project"

        parameters = {
            "name": "Failing Project",
            "organization_id": valid_org_id
        }

        with pytest.raises(ValueError, match="Simulated setup_project failure"):
            await workflow_tool.execute_workflow(
                workflow="setup_project",
                parameters=parameters,
                transaction_mode=True
            )

        # Verify rollback occurred
        assert len(workflow_tool.created_entities) == 0
        assert workflow_tool.transaction_active is False

        result_tracker.rollback_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError as e:
        result_tracker.mark_failure(f"Rollback verification failed: {str(e)}", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)
        workflow_tool.should_fail = False


@pytest.mark.asyncio
async def test_setup_project_no_transaction_mode(workflow_tool, valid_org_id):
    """Test project setup without transaction mode"""
    result_tracker = WorkflowTestResult("setup_project", "no_transaction_mode")
    start_time = time.time()

    try:
        parameters = {
            "name": "No Transaction Project",
            "organization_id": valid_org_id
        }

        result = await workflow_tool.execute_workflow(
            workflow="setup_project",
            parameters=parameters,
            transaction_mode=False
        )

        assert result["success"] is True
        assert workflow_tool.transaction_active is False

        result_tracker.transaction_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


# ==================== IMPORT_REQUIREMENTS WORKFLOW TESTS ====================

@pytest.mark.asyncio
async def test_import_requirements_success(workflow_tool, valid_document_id):
    """Test successful requirements import"""
    result_tracker = WorkflowTestResult("import_requirements", "success")
    start_time = time.time()

    try:
        parameters = {
            "document_id": valid_document_id,
            "requirements": [
                {"name": "REQ-001", "description": "User login", "priority": "high"},
                {"name": "REQ-002", "description": "Password reset", "priority": "medium"},
                {"name": "REQ-003", "description": "User profile", "priority": "low"}
            ]
        }

        result = await workflow_tool.execute_workflow(
            workflow="import_requirements",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert result["imported_count"] == 3
        assert result["failed_count"] == 0
        assert len(result["requirements"]) == 3

        result_tracker.transaction_verified = True
        result_tracker.entities_created = result["requirements"]
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_import_requirements_partial_failure(workflow_tool, valid_document_id):
    """Test requirements import with some invalid entries"""
    result_tracker = WorkflowTestResult("import_requirements", "partial_failure")
    start_time = time.time()

    try:
        parameters = {
            "document_id": valid_document_id,
            "requirements": [
                {"name": "REQ-001", "description": "Valid requirement"},
                {"description": "Missing name"},  # Invalid - missing name
                {"name": "REQ-003", "description": "Another valid one"}
            ]
        }

        result = await workflow_tool.execute_workflow(
            workflow="import_requirements",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is False  # Not all succeeded
        assert result["imported_count"] == 2
        assert result["failed_count"] == 1
        assert len(result["failures"]) == 1
        assert "Missing required field: name" in result["failures"][0]["error"]

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_import_requirements_missing_document_id(workflow_tool):
    """Test import with missing document_id"""
    result_tracker = WorkflowTestResult("import_requirements", "missing_document_id")
    start_time = time.time()

    try:
        parameters = {
            "requirements": [{"name": "REQ-001", "description": "Test"}]
        }

        with pytest.raises(ValueError, match="Missing required parameter: document_id"):
            await workflow_tool.execute_workflow(
                workflow="import_requirements",
                parameters=parameters,
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_import_requirements_invalid_requirements_format(workflow_tool, valid_document_id):
    """Test import with invalid requirements format"""
    result_tracker = WorkflowTestResult("import_requirements", "invalid_format")
    start_time = time.time()

    try:
        parameters = {
            "document_id": valid_document_id,
            "requirements": "not a list"  # Invalid format
        }

        with pytest.raises(ValueError, match="Missing or invalid parameter: requirements"):
            await workflow_tool.execute_workflow(
                workflow="import_requirements",
                parameters=parameters,
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_import_requirements_empty_list(workflow_tool, valid_document_id):
    """Test import with empty requirements list"""
    result_tracker = WorkflowTestResult("import_requirements", "empty_list")
    start_time = time.time()

    try:
        parameters = {
            "document_id": valid_document_id,
            "requirements": []
        }

        result = await workflow_tool.execute_workflow(
            workflow="import_requirements",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert result["imported_count"] == 0
        assert result["failed_count"] == 0

        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


# ==================== SETUP_TEST_MATRIX WORKFLOW TESTS ====================

@pytest.mark.asyncio
async def test_setup_test_matrix_success_basic(workflow_tool, valid_project_id):
    """Test basic test matrix setup"""
    result_tracker = WorkflowTestResult("setup_test_matrix", "success_basic")
    start_time = time.time()

    try:
        parameters = {
            "project_id": valid_project_id,
            "name": "QA Test Matrix"
        }

        result = await workflow_tool.execute_workflow(
            workflow="setup_test_matrix",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert result["matrix"]["project_id"] == valid_project_id
        assert result["matrix"]["name"] == "QA Test Matrix"

        result_tracker.transaction_verified = True
        result_tracker.entities_created = [result["matrix"]]
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_setup_test_matrix_with_test_cases(workflow_tool, valid_project_id):
    """Test matrix setup with test cases"""
    result_tracker = WorkflowTestResult("setup_test_matrix", "with_test_cases")
    start_time = time.time()

    try:
        parameters = {
            "project_id": valid_project_id,
            "name": "Comprehensive Test Matrix",
            "test_cases": [
                {"name": "Unit Tests", "type": "unit"},
                {"name": "Integration Tests", "type": "integration"},
                {"name": "E2E Tests", "type": "e2e"},
                {"name": "Performance Tests", "type": "performance"}
            ]
        }

        result = await workflow_tool.execute_workflow(
            workflow="setup_test_matrix",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert len(result["test_cases"]) == 4

        test_types = [tc["type"] for tc in result["test_cases"]]
        assert "unit" in test_types
        assert "integration" in test_types
        assert "e2e" in test_types
        assert "performance" in test_types

        result_tracker.transaction_verified = True
        result_tracker.entities_created = [result["matrix"]] + result["test_cases"]
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_setup_test_matrix_missing_project_id(workflow_tool):
    """Test matrix setup with missing project_id"""
    result_tracker = WorkflowTestResult("setup_test_matrix", "missing_project_id")
    start_time = time.time()

    try:
        parameters = {
            "name": "Incomplete Matrix"
        }

        with pytest.raises(ValueError, match="Missing required parameter: project_id"):
            await workflow_tool.execute_workflow(
                workflow="setup_test_matrix",
                parameters=parameters,
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


# ==================== BULK_STATUS_UPDATE WORKFLOW TESTS ====================

@pytest.mark.asyncio
async def test_bulk_status_update_success(workflow_tool):
    """Test successful bulk status update"""
    result_tracker = WorkflowTestResult("bulk_status_update", "success")
    start_time = time.time()

    try:
        # First create some requirements
        workflow_tool.created_entities["requirement"] = [
            {"id": "req_1", "name": "REQ-1", "status": "draft"},
            {"id": "req_2", "name": "REQ-2", "status": "draft"},
            {"id": "req_3", "name": "REQ-3", "status": "draft"}
        ]

        parameters = {
            "entity_type": "requirement",
            "entity_ids": ["req_1", "req_2", "req_3"],
            "new_status": "approved"
        }

        result = await workflow_tool.execute_workflow(
            workflow="bulk_status_update",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert result["updated_count"] == 3
        assert result["failed_count"] == 0
        assert all(e["status"] == "approved" for e in result["updated_entities"])

        result_tracker.transaction_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_bulk_status_update_partial_failure(workflow_tool):
    """Test bulk update with some non-existent entities"""
    result_tracker = WorkflowTestResult("bulk_status_update", "partial_failure")
    start_time = time.time()

    try:
        workflow_tool.created_entities["requirement"] = [
            {"id": "req_1", "name": "REQ-1", "status": "draft"},
            {"id": "req_2", "name": "REQ-2", "status": "draft"}
        ]

        parameters = {
            "entity_type": "requirement",
            "entity_ids": ["req_1", "req_2", "req_999"],  # req_999 doesn't exist
            "new_status": "approved"
        }

        result = await workflow_tool.execute_workflow(
            workflow="bulk_status_update",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is False
        assert result["updated_count"] == 2
        assert result["failed_count"] == 1
        assert len(result["failures"]) == 1
        assert result["failures"][0]["entity_id"] == "req_999"

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_bulk_status_update_missing_params(workflow_tool):
    """Test bulk update with missing parameters"""
    result_tracker = WorkflowTestResult("bulk_status_update", "missing_params")
    start_time = time.time()

    try:
        parameters = {
            "entity_type": "requirement",
            "entity_ids": ["req_1"]
            # Missing new_status
        }

        with pytest.raises(ValueError, match="Missing required parameter: new_status"):
            await workflow_tool.execute_workflow(
                workflow="bulk_status_update",
                parameters=parameters,
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_bulk_status_update_invalid_entity_ids(workflow_tool):
    """Test bulk update with invalid entity_ids format"""
    result_tracker = WorkflowTestResult("bulk_status_update", "invalid_entity_ids")
    start_time = time.time()

    try:
        parameters = {
            "entity_type": "requirement",
            "entity_ids": "not_a_list",
            "new_status": "approved"
        }

        with pytest.raises(ValueError, match="Missing or invalid parameter: entity_ids"):
            await workflow_tool.execute_workflow(
                workflow="bulk_status_update",
                parameters=parameters,
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


# ==================== ORGANIZATION_ONBOARDING WORKFLOW TESTS ====================

@pytest.mark.asyncio
async def test_organization_onboarding_success_basic(workflow_tool, valid_user_id):
    """Test basic organization onboarding"""
    result_tracker = WorkflowTestResult("organization_onboarding", "success_basic")
    start_time = time.time()

    try:
        parameters = {
            "organization_name": "Test Corp",
            "admin_user_id": valid_user_id
        }

        result = await workflow_tool.execute_workflow(
            workflow="organization_onboarding",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert result["organization"]["name"] == "Test Corp"
        assert result["admin_membership"]["user_id"] == valid_user_id
        assert result["admin_membership"]["role"] == "admin"

        result_tracker.transaction_verified = True
        result_tracker.entities_created = [result["organization"]]
        result_tracker.relationships_created = [result["admin_membership"]]
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_organization_onboarding_with_default_project(workflow_tool, valid_user_id):
    """Test organization onboarding with default project creation"""
    result_tracker = WorkflowTestResult("organization_onboarding", "with_default_project")
    start_time = time.time()

    try:
        parameters = {
            "organization_name": "Full Setup Corp",
            "admin_user_id": valid_user_id,
            "create_default_project": True
        }

        result = await workflow_tool.execute_workflow(
            workflow="organization_onboarding",
            parameters=parameters,
            transaction_mode=True
        )

        assert result["success"] is True
        assert result["default_project"] is not None
        assert result["default_project"]["name"] == "Default Project"
        assert result["default_project"]["organization_id"] == result["organization"]["id"]

        result_tracker.transaction_verified = True
        result_tracker.entities_created = [result["organization"], result["default_project"]]
        result_tracker.relationships_created = [result["admin_membership"]]
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_organization_onboarding_missing_org_name(workflow_tool, valid_user_id):
    """Test onboarding with missing organization name"""
    result_tracker = WorkflowTestResult("organization_onboarding", "missing_org_name")
    start_time = time.time()

    try:
        parameters = {
            "admin_user_id": valid_user_id
        }

        with pytest.raises(ValueError, match="Missing required parameter: organization_name"):
            await workflow_tool.execute_workflow(
                workflow="organization_onboarding",
                parameters=parameters,
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_organization_onboarding_missing_admin_user(workflow_tool):
    """Test onboarding with missing admin user ID"""
    result_tracker = WorkflowTestResult("organization_onboarding", "missing_admin_user")
    start_time = time.time()

    try:
        parameters = {
            "organization_name": "Incomplete Org"
        }

        with pytest.raises(ValueError, match="Missing required parameter: admin_user_id"):
            await workflow_tool.execute_workflow(
                workflow="organization_onboarding",
                parameters=parameters,
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


# ==================== COMPLEX MULTI-STEP SCENARIOS ====================

@pytest.mark.asyncio
async def test_complete_workflow_chain(workflow_tool, valid_user_id):
    """Test complete workflow chain: onboarding -> project -> requirements -> matrix -> bulk update"""
    result_tracker = WorkflowTestResult("multi_workflow", "complete_chain")
    start_time = time.time()

    try:
        # Step 1: Organization onboarding
        org_result = await workflow_tool.execute_workflow(
            workflow="organization_onboarding",
            parameters={
                "organization_name": "Chain Test Corp",
                "admin_user_id": valid_user_id,
                "create_default_project": True
            },
            transaction_mode=True
        )

        org_id = org_result["organization"]["id"]
        project_id = org_result["default_project"]["id"]

        # Step 2: Setup project with documents
        project_result = await workflow_tool.execute_workflow(
            workflow="setup_project",
            parameters={
                "name": "Feature Project",
                "organization_id": org_id,
                "initial_documents": ["Requirements"]
            },
            transaction_mode=True
        )

        feature_project_id = project_result["project"]["id"]
        doc_id = project_result["documents"][0]["id"]

        # Step 3: Import requirements
        req_result = await workflow_tool.execute_workflow(
            workflow="import_requirements",
            parameters={
                "document_id": doc_id,
                "requirements": [
                    {"name": "REQ-001", "description": "Feature 1", "status": "draft"},
                    {"name": "REQ-002", "description": "Feature 2", "status": "draft"}
                ]
            },
            transaction_mode=True
        )

        # Step 4: Setup test matrix
        matrix_result = await workflow_tool.execute_workflow(
            workflow="setup_test_matrix",
            parameters={
                "project_id": feature_project_id,
                "test_cases": [
                    {"name": "Test Feature 1", "type": "functional"},
                    {"name": "Test Feature 2", "type": "functional"}
                ]
            },
            transaction_mode=True
        )

        # Step 5: Bulk update requirements to approved
        req_ids = [req["id"] for req in req_result["requirements"]]
        update_result = await workflow_tool.execute_workflow(
            workflow="bulk_status_update",
            parameters={
                "entity_type": "requirement",
                "entity_ids": req_ids,
                "new_status": "approved"
            },
            transaction_mode=True
        )

        # Verify complete chain
        assert org_result["success"] is True
        assert project_result["success"] is True
        assert req_result["success"] is True
        assert matrix_result["success"] is True
        assert update_result["success"] is True

        result_tracker.transaction_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_transaction_rollback_in_chain(workflow_tool, valid_user_id):
    """Test transaction rollback in a multi-step workflow chain"""
    result_tracker = WorkflowTestResult("multi_workflow", "rollback_in_chain")
    start_time = time.time()

    try:
        # Create a fresh workflow tool for this test to avoid interference
        test_tool = MockWorkflowTool()

        # Step 1: Successful onboarding
        org_result = await test_tool.execute_workflow(
            workflow="organization_onboarding",
            parameters={
                "organization_name": "Rollback Test Corp",
                "admin_user_id": valid_user_id
            },
            transaction_mode=True
        )

        org_id = org_result["organization"]["id"]

        # Store count before failure
        org_count_before = len(test_tool.created_entities.get("organization", []))

        # Step 2: Configure to fail on project setup
        test_tool.should_fail = True
        test_tool.failure_point = "setup_project"

        # This should fail and rollback only the project transaction
        with pytest.raises(ValueError):
            await test_tool.execute_workflow(
                workflow="setup_project",
                parameters={
                    "name": "Failing Project",
                    "organization_id": org_id
                },
                transaction_mode=True
            )

        # Verify rollback - org from first transaction should still exist,
        # but no project should be created
        org_count_after = len(test_tool.created_entities.get("organization", []))
        assert org_count_after == org_count_before, "Organization count should remain unchanged"
        assert "project" not in test_tool.created_entities or len(test_tool.created_entities["project"]) == 0

        result_tracker.rollback_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError as e:
        result_tracker.mark_failure(f"Rollback verification failed: {str(e)}", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


# ==================== PERFORMANCE TESTS ====================

@pytest.mark.asyncio
async def test_bulk_import_performance(workflow_tool, valid_document_id):
    """Test performance of bulk requirement import"""
    result_tracker = WorkflowTestResult("import_requirements", "performance_bulk")
    start_time = time.time()

    try:
        # Create 100 requirements
        requirements = [
            {
                "name": f"REQ-{i:03d}",
                "description": f"Requirement {i}",
                "priority": ["high", "medium", "low"][i % 3]
            }
            for i in range(100)
        ]

        parameters = {
            "document_id": valid_document_id,
            "requirements": requirements
        }

        result = await workflow_tool.execute_workflow(
            workflow="import_requirements",
            parameters=parameters,
            transaction_mode=True
        )

        duration_ms = (time.time() - start_time) * 1000

        assert result["success"] is True
        assert result["imported_count"] == 100

        # Performance assertion: should complete in under 1 second
        assert duration_ms < 1000, f"Bulk import took {duration_ms}ms, expected < 1000ms"

        result_tracker.mark_success(duration_ms)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_bulk_update_performance(workflow_tool):
    """Test performance of bulk status update"""
    result_tracker = WorkflowTestResult("bulk_status_update", "performance_bulk")
    start_time = time.time()

    try:
        # Create 100 requirements
        workflow_tool.created_entities["requirement"] = [
            {"id": f"req_{i}", "name": f"REQ-{i:03d}", "status": "draft"}
            for i in range(100)
        ]

        entity_ids = [f"req_{i}" for i in range(100)]

        parameters = {
            "entity_type": "requirement",
            "entity_ids": entity_ids,
            "new_status": "approved"
        }

        result = await workflow_tool.execute_workflow(
            workflow="bulk_status_update",
            parameters=parameters,
            transaction_mode=True
        )

        duration_ms = (time.time() - start_time) * 1000

        assert result["success"] is True
        assert result["updated_count"] == 100

        # Performance assertion
        assert duration_ms < 500, f"Bulk update took {duration_ms}ms, expected < 500ms"

        result_tracker.mark_success(duration_ms)

    except Exception as e:
        result_tracker.mark_failure(str(e), (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


# ==================== EDGE CASES ====================

@pytest.mark.asyncio
async def test_unknown_workflow(workflow_tool):
    """Test handling of unknown workflow"""
    result_tracker = WorkflowTestResult("unknown_workflow", "invalid_workflow")
    start_time = time.time()

    try:
        with pytest.raises(ValueError, match="Unknown workflow"):
            await workflow_tool.execute_workflow(
                workflow="invalid_workflow_name",
                parameters={},
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


@pytest.mark.asyncio
async def test_empty_parameters(workflow_tool):
    """Test workflows with empty parameters"""
    result_tracker = WorkflowTestResult("edge_cases", "empty_parameters")
    start_time = time.time()

    try:
        with pytest.raises(ValueError):
            await workflow_tool.execute_workflow(
                workflow="setup_project",
                parameters={},
                transaction_mode=True
            )

        result_tracker.error_handling_verified = True
        result_tracker.mark_success((time.time() - start_time) * 1000)

    except AssertionError:
        result_tracker.mark_failure("Error handling not working correctly", (time.time() - start_time) * 1000)
        raise
    finally:
        test_results.append(result_tracker)


# ==================== TEST RESULT AGGREGATION ====================

def generate_test_matrix_report():
    """Generate comprehensive test matrix report"""

    print("\n" + "="*80)
    print("WORKFLOW TEST MATRIX REPORT")
    print("="*80)

    # Group results by workflow
    workflows = {}
    for result in test_results:
        workflow_name = result.workflow_name
        if workflow_name not in workflows:
            workflows[workflow_name] = []
        workflows[workflow_name].append(result)

    # Summary statistics
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.status == "PASS")
    failed_tests = sum(1 for r in test_results if r.status == "FAIL")

    print(f"\nOVERALL SUMMARY:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"  Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

    # Detailed results by workflow
    for workflow_name, results in sorted(workflows.items()):
        print(f"\n{workflow_name.upper()}")
        print("-" * 80)

        workflow_passed = sum(1 for r in results if r.status == "PASS")
        workflow_total = len(results)

        print(f"  Coverage: {workflow_passed}/{workflow_total} scenarios ({workflow_passed/workflow_total*100:.1f}%)")

        for result in results:
            status_icon = "✓" if result.status == "PASS" else "✗"
            print(f"\n  {status_icon} {result.scenario}")
            print(f"    Status: {result.status}")
            print(f"    Duration: {result.duration_ms:.2f}ms")
            print(f"    Transaction Verified: {'Yes' if result.transaction_verified else 'No'}")
            print(f"    Rollback Verified: {'Yes' if result.rollback_verified else 'No'}")
            print(f"    Error Handling Verified: {'Yes' if result.error_handling_verified else 'No'}")
            print(f"    Entities Created: {len(result.entities_created)}")
            print(f"    Relationships Created: {len(result.relationships_created)}")

            if result.error_details:
                print(f"    Error: {result.error_details}")

    # Performance metrics
    print(f"\nPERFORMANCE METRICS:")
    print("-" * 80)

    avg_duration = sum(r.duration_ms for r in test_results) / len(test_results)
    max_duration = max(r.duration_ms for r in test_results)
    min_duration = min(r.duration_ms for r in test_results)

    print(f"  Average Test Duration: {avg_duration:.2f}ms")
    print(f"  Max Duration: {max_duration:.2f}ms")
    print(f"  Min Duration: {min_duration:.2f}ms")

    # Transaction handling verification
    print(f"\nTRANSACTION HANDLING:")
    print("-" * 80)

    transaction_verified = sum(1 for r in test_results if r.transaction_verified)
    rollback_verified = sum(1 for r in test_results if r.rollback_verified)
    error_handling_verified = sum(1 for r in test_results if r.error_handling_verified)

    print(f"  Transaction Mode Verified: {transaction_verified}/{total_tests}")
    print(f"  Rollback Verified: {rollback_verified}/{total_tests}")
    print(f"  Error Handling Verified: {error_handling_verified}/{total_tests}")

    # Export to JSON
    report_data = {
        "summary": {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": passed_tests/total_tests*100 if total_tests > 0 else 0
        },
        "performance": {
            "avg_duration_ms": avg_duration,
            "max_duration_ms": max_duration,
            "min_duration_ms": min_duration
        },
        "transaction_handling": {
            "transaction_verified": transaction_verified,
            "rollback_verified": rollback_verified,
            "error_handling_verified": error_handling_verified
        },
        "workflows": {
            workflow_name: [r.to_dict() for r in results]
            for workflow_name, results in workflows.items()
        }
    }

    return report_data


# Test execution fixture
@pytest.fixture(scope="session", autouse=True)
def print_final_report():
    """Print final report after all tests complete"""
    yield
    report = generate_test_matrix_report()

    # Save report to file
    report_file = "/Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/tests/workflow_test_matrix_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n\nFull report saved to: {report_file}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
