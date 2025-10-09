"""
Comprehensive test suite for workflow endpoints.

This test module provides extensive testing for all workflow operations including:
- setup_project: Project initialization with various configurations
- import_requirements: Batch requirement import scenarios
- setup_test_matrix: Test matrix creation and configuration
- bulk_status_update: Batch status updates for entities
- organization_onboarding: Organization setup and initialization

Test categories cover minimal parameters, full parameters, edge cases,
performance testing, and error handling scenarios.
"""

from __future__ import annotations

import pytest
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
import time

from test_utils import (
    EntityFactory,
    EntityHierarchyBuilder,
    AssertionHelpers,
    TestDataValidator,
    PerformanceAnalyzer
)


class WorkflowDataGenerator:
    """Generate test data for workflow tests."""

    @staticmethod
    def uuid() -> str:
        """Generate a random UUID string."""
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def generate_requirements(count: int, **kwargs) -> List[Dict[str, Any]]:
        """Generate a list of requirement data.

        Args:
            count: Number of requirements to generate
            **kwargs: Override default values

        Returns:
            List of requirement dictionaries
        """
        requirements = []
        for i in range(count):
            uid = uuid.uuid4().hex[:8]
            req = {
                "name": kwargs.get("name", f"Requirement {uid}"),
                "block_id": kwargs.get("block_id", f"block_{uid}"),
                "description": kwargs.get("description", f"Generated requirement {i+1}"),
                "priority": kwargs.get("priority", ["high", "medium", "low"][i % 3]),
                "status": kwargs.get("status", "active"),
                "external_id": kwargs.get("external_id", f"EXT-{uid}"),
            }
            # Apply any specific overrides
            for key, value in kwargs.items():
                if key not in req:
                    req[key] = value
            requirements.append(req)
        return requirements

    @staticmethod
    def generate_document_names(count: int) -> List[str]:
        """Generate a list of document names.

        Args:
            count: Number of document names to generate

        Returns:
            List of document names
        """
        templates = [
            "Requirements Specification",
            "Technical Design",
            "User Manual",
            "Test Plan",
            "API Documentation",
            "Architecture Overview",
            "Security Guidelines",
            "Deployment Guide"
        ]

        if count <= len(templates):
            return templates[:count]

        # Generate additional names if needed
        names = templates.copy()
        for i in range(count - len(templates)):
            names.append(f"Document {uuid.uuid4().hex[:8]}")

        return names

    @staticmethod
    def generate_entity_ids(count: int, entity_type: str) -> List[str]:
        """Generate mock entity IDs for testing.

        Args:
            count: Number of IDs to generate
            entity_type: Type of entity

        Returns:
            List of entity IDs
        """
        prefix = {
            "requirement": "req",
            "test": "test",
            "document": "doc",
            "project": "proj",
            "organization": "org"
        }.get(entity_type, "entity")

        return [f"{prefix}_{uuid.uuid4().hex}" for _ in range(count)]


class WorkflowTestSuite:
    """Base class for workflow test suites."""

    def __init__(self, call_mcp: Callable):
        self.call_mcp = call_mcp
        self.data_generator = WorkflowDataGenerator()
        self.assertion_helpers = AssertionHelpers()
        self.performance_analyzer = PerformanceAnalyzer()
        self.created_entities = []

    async def cleanup(self):
        """Clean up created entities."""
        # Delete in reverse order to respect dependencies
        for entity in reversed(self.created_entities):
            try:
                await self.call_mcp(
                    "entity_tool",
                    {
                        "operation": "delete",
                        "entity_type": entity["type"],
                        "entity_id": entity["id"],
                        "soft_delete": True
                    }
                )
            except:
                pass  # Ignore cleanup errors

    def record_entity(self, entity_type: str, entity_id: str):
        """Record an entity for cleanup."""
        self.created_entities.append({
            "type": entity_type,
            "id": entity_id
        })


@pytest.mark.asyncio
class TestSetupProjectWorkflow(WorkflowTestSuite):
    """Test suite for setup_project workflow."""

    async def test_minimal_params(self, call_mcp):
        """Test setup_project with minimal required parameters."""
        # First create an organization
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        assert org_result.get("success"), "Failed to create organization"
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        # Execute workflow with minimal params
        start_time = time.time()
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Minimal Test Project",
                    "organization_id": org_id
                }
            }
        )
        duration_ms = (time.time() - start_time) * 1000
        self.performance_analyzer.record_metric(
            "workflow", "setup_project", duration_ms, workflow_variant="minimal"
        )

        # Assertions
        assert result.get("success") is not False, f"Workflow failed: {result.get('error')}"
        assert result.get("project_id"), "No project_id in response"
        assert result.get("steps_completed") >= 2, "Should complete at least 2 steps"
        self.record_entity("project", result["project_id"])

    async def test_with_description(self, call_mcp):
        """Test setup_project with description parameter."""
        # Create organization
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        # Execute workflow with description
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Described Project",
                    "organization_id": org_id,
                    "description": "This is a comprehensive project description for testing purposes."
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("project_id")
        self.record_entity("project", result["project_id"])

        # Verify description was set
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "project",
                "entity_id": result["project_id"]
            }
        )
        assert project_result["data"]["description"] == "This is a comprehensive project description for testing purposes."

    async def test_add_creator_as_admin_true(self, call_mcp):
        """Test setup_project with add_creator_as_admin=True."""
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Admin Project",
                    "organization_id": org_id,
                    "add_creator_as_admin": True
                }
            }
        )

        assert result.get("success") is not False
        assert any(
            step.get("step") == "add_creator_member" and step.get("status") == "success"
            for step in result.get("results", [])
        ), "Creator should be added as admin"
        self.record_entity("project", result["project_id"])

    async def test_add_creator_as_admin_false(self, call_mcp):
        """Test setup_project with add_creator_as_admin=False."""
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "No Admin Project",
                    "organization_id": org_id,
                    "add_creator_as_admin": False
                }
            }
        )

        assert result.get("success") is not False
        # Check that add_creator_member step was not executed
        add_creator_steps = [
            step for step in result.get("results", [])
            if step.get("step") == "add_creator_member"
        ]
        assert len(add_creator_steps) == 0, "Creator should not be added when flag is False"
        self.record_entity("project", result["project_id"])

    async def test_with_one_initial_document(self, call_mcp):
        """Test setup_project with 1 initial document."""
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        doc_names = self.data_generator.generate_document_names(1)
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Project with 1 Doc",
                    "organization_id": org_id,
                    "initial_documents": doc_names
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("project_id")

        # Check that document was created
        doc_steps = [
            step for step in result.get("results", [])
            if step.get("step").startswith("create_document_")
        ]
        assert len(doc_steps) == 1, "Should create 1 document"
        self.record_entity("project", result["project_id"])

    async def test_with_three_initial_documents(self, call_mcp):
        """Test setup_project with 3 initial documents."""
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        doc_names = self.data_generator.generate_document_names(3)
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Project with 3 Docs",
                    "organization_id": org_id,
                    "initial_documents": doc_names
                }
            }
        )

        assert result.get("success") is not False
        doc_steps = [
            step for step in result.get("results", [])
            if step.get("step").startswith("create_document_")
        ]
        assert len(doc_steps) == 3, "Should create 3 documents"
        self.record_entity("project", result["project_id"])

    async def test_with_five_initial_documents(self, call_mcp):
        """Test setup_project with 5 initial documents."""
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        doc_names = self.data_generator.generate_document_names(5)
        start_time = time.time()
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Project with 5 Docs",
                    "organization_id": org_id,
                    "initial_documents": doc_names
                }
            }
        )
        duration_ms = (time.time() - start_time) * 1000
        self.performance_analyzer.record_metric(
            "workflow", "setup_project", duration_ms,
            workflow_variant="5_documents", document_count=5
        )

        assert result.get("success") is not False
        doc_steps = [
            step for step in result.get("results", [])
            if step.get("step").startswith("create_document_")
        ]
        assert len(doc_steps) == 5, "Should create 5 documents"
        self.record_entity("project", result["project_id"])

    async def test_all_parameters_complete(self, call_mcp):
        """Test setup_project with all available parameters."""
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        doc_names = self.data_generator.generate_document_names(3)
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Complete Project",
                    "organization_id": org_id,
                    "description": "A fully configured project with all parameters",
                    "add_creator_as_admin": True,
                    "initial_documents": doc_names
                },
                "transaction_mode": True,
                "format_type": "detailed"
            }
        )

        assert result.get("success") is not False
        assert result.get("project_id")
        assert result.get("steps_successful") >= 5, "Should complete multiple steps"
        self.record_entity("project", result["project_id"])

    async def test_invalid_organization_id(self, call_mcp):
        """Test setup_project with invalid organization ID."""
        # Use a properly formatted UUID that doesn't exist
        invalid_org_id = str(uuid.uuid4())

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Invalid Org Project",
                    "organization_id": invalid_org_id
                }
            }
        )

        assert result.get("success") is False, "Should fail with invalid org ID"
        assert "error" in result, f"Expected 'error' in result, got keys: {list(result.keys())}"

    async def test_missing_required_params(self, call_mcp):
        """Test setup_project with missing required parameters."""
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Missing Org ID Project"
                    # Missing organization_id
                }
            }
        )

        assert result.get("success") is False, "Should fail with missing params"
        assert "error" in result, f"Expected 'error' in result, got keys: {list(result.keys())}"
        assert "required" in result["error"].lower()


@pytest.mark.asyncio
class TestImportRequirementsWorkflow(WorkflowTestSuite):
    """Test suite for import_requirements workflow."""

    async def setup_document(self, call_mcp) -> tuple[str, str, str]:
        """Create organization, project and document for testing.

        Returns:
            Tuple of (organization_id, project_id, document_id)
        """
        # Create organization
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        # Create project
        project_data = EntityFactory.project(org_id)
        project_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "project", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        self.record_entity("project", project_id)

        # Create document
        doc_data = EntityFactory.document(project_id)
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "document", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]
        self.record_entity("document", doc_id)

        return org_id, project_id, doc_id

    async def test_small_batch_3_requirements(self, call_mcp):
        """Test import_requirements with 3 requirements."""
        _, _, doc_id = await self.setup_document(call_mcp)

        requirements = self.data_generator.generate_requirements(3)

        start_time = time.time()
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "import_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "requirements": requirements
                }
            }
        )
        duration_ms = (time.time() - start_time) * 1000
        self.performance_analyzer.record_metric(
            "workflow", "import_requirements", duration_ms,
            requirement_count=3, batch_size="small"
        )

        assert result.get("success") is not False
        assert result.get("imported_count") == 3
        assert result.get("failed_count") == 0

    async def test_medium_batch_10_requirements(self, call_mcp):
        """Test import_requirements with 10 requirements."""
        _, _, doc_id = await self.setup_document(call_mcp)

        requirements = self.data_generator.generate_requirements(10)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "import_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "requirements": requirements
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("imported_count") == 10
        assert result.get("total_requirements") == 10

    async def test_large_batch_25_requirements(self, call_mcp):
        """Test import_requirements with 25 requirements."""
        _, _, doc_id = await self.setup_document(call_mcp)

        requirements = self.data_generator.generate_requirements(25)

        start_time = time.time()
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "import_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "requirements": requirements
                }
            }
        )
        duration_ms = (time.time() - start_time) * 1000
        self.performance_analyzer.record_metric(
            "workflow", "import_requirements", duration_ms,
            requirement_count=25, batch_size="large"
        )

        assert result.get("success") is not False
        assert result.get("imported_count") == 25

    async def test_with_full_metadata(self, call_mcp):
        """Test import_requirements with complete metadata."""
        _, _, doc_id = await self.setup_document(call_mcp)

        requirements = [
            {
                "name": "Full Metadata Req 1",
                "block_id": "block_full_1",
                "description": "Complete requirement with all metadata",
                "status": "active",
                "priority": "high",
                "external_id": "EXT-001",
                "tags": ["critical", "security"],
                "version": "1.0.0"
            },
            {
                "name": "Full Metadata Req 2",
                "block_id": "block_full_2",
                "description": "Another complete requirement",
                "status": "approved",
                "priority": "medium",
                "external_id": "EXT-002",
                "tags": ["performance"],
                "version": "1.0.0"
            }
        ]

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "import_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "requirements": requirements
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("imported_count") == 2

        # Verify metadata was preserved
        for step in result.get("results", []):
            if step.get("status") == "success" and "result" in step:
                req = step["result"]
                assert req.get("status") in ["active", "approved"]
                assert req.get("priority") in ["high", "medium"]

    async def test_minimal_metadata(self, call_mcp):
        """Test import_requirements with minimal metadata (name only)."""
        _, _, doc_id = await self.setup_document(call_mcp)

        requirements = [
            {
                "name": "Minimal Req 1",
                "block_id": "block_min_1"
            },
            {
                "name": "Minimal Req 2",
                "block_id": "block_min_2"
            }
        ]

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "import_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "requirements": requirements
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("imported_count") == 2

        # Check defaults were applied
        for step in result.get("results", []):
            if step.get("status") == "success" and "result" in step:
                req = step["result"]
                assert req.get("status") == "active", "Default status should be active"
                assert req.get("priority") == "medium", "Default priority should be medium"

    async def test_mixed_priorities(self, call_mcp):
        """Test import_requirements with mixed priority levels."""
        _, _, doc_id = await self.setup_document(call_mcp)

        requirements = [
            {"name": "High Priority", "block_id": "block_h", "priority": "high"},
            {"name": "Medium Priority", "block_id": "block_m", "priority": "medium"},
            {"name": "Low Priority", "block_id": "block_l", "priority": "low"},
            {"name": "Critical Priority", "block_id": "block_c", "priority": "critical"},
        ]

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "import_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "requirements": requirements
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("imported_count") == 4

        # Verify all priorities were set correctly
        priorities = set()
        for step in result.get("results", []):
            if step.get("status") == "success" and "result" in step:
                priorities.add(step["result"].get("priority"))

        assert "high" in priorities
        assert "medium" in priorities
        assert "low" in priorities

    async def test_invalid_document_id(self, call_mcp):
        """Test import_requirements with invalid document ID."""
        requirements = self.data_generator.generate_requirements(3)
        # Use a properly formatted UUID that doesn't exist
        invalid_doc_id = str(uuid.uuid4())

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "import_requirements",
                "parameters": {
                    "document_id": invalid_doc_id,
                    "requirements": requirements
                }
            }
        )

        assert result.get("success") is False
        assert "error" in result, f"Expected 'error' in result, got keys: {list(result.keys())}"

    async def test_empty_requirements_list(self, call_mcp):
        """Test import_requirements with empty requirements list."""
        _, _, doc_id = await self.setup_document(call_mcp)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "import_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "requirements": []
                }
            }
        )

        assert result.get("success") is False
        assert "error" in result, f"Expected 'error' in result, got keys: {list(result.keys())}"
        assert "empty" in result["error"].lower() or "non-empty" in result["error"].lower()


@pytest.mark.asyncio
class TestSetupTestMatrixWorkflow(WorkflowTestSuite):
    """Test suite for setup_test_matrix workflow."""

    async def setup_project_with_requirements(
        self, call_mcp, requirement_count: int = 5
    ) -> tuple[str, str, List[str]]:
        """Create project with requirements for testing.

        Returns:
            Tuple of (project_id, document_id, requirement_ids)
        """
        # Create organization
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        # Create project
        project_data = EntityFactory.project(org_id)
        project_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "project", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        self.record_entity("project", project_id)

        # Create document
        doc_data = EntityFactory.document(project_id)
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "document", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]
        self.record_entity("document", doc_id)

        # Create requirements
        req_ids = []
        for i in range(requirement_count):
            req_data = EntityFactory.requirement(
                doc_id,
                f"block_{i}",
                priority=["high", "medium", "low"][i % 3]
            )
            req_result, _ = await call_mcp(
                "entity_tool",
                {"operation": "create", "entity_type": "requirement", "data": req_data}
            )
            req_ids.append(req_result["data"]["id"])
            self.record_entity("requirement", req_result["data"]["id"])

        return project_id, doc_id, req_ids

    async def test_default_matrix_name(self, call_mcp):
        """Test setup_test_matrix with default matrix name."""
        project_id, _, _ = await self.setup_project_with_requirements(call_mcp, 5)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_test_matrix",
                "parameters": {
                    "project_id": project_id
                    # matrix_name not provided, should use default
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("matrix_view_id")
        assert result.get("requirements_found") == 5
        self.record_entity("test_matrix_view", result["matrix_view_id"])

    async def test_custom_matrix_name(self, call_mcp):
        """Test setup_test_matrix with custom matrix name."""
        project_id, _, _ = await self.setup_project_with_requirements(call_mcp, 3)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_test_matrix",
                "parameters": {
                    "project_id": project_id,
                    "matrix_name": "Custom Test Coverage Matrix"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("matrix_view_id")
        self.record_entity("test_matrix_view", result["matrix_view_id"])

        # Verify matrix name
        for step in result.get("results", []):
            if step.get("step") == "create_matrix_view" and "result" in step:
                assert step["result"].get("name") == "Custom Test Coverage Matrix"
                break

    async def test_empty_project(self, call_mcp):
        """Test setup_test_matrix with empty project (no requirements)."""
        # Create project without requirements
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        project_data = EntityFactory.project(org_id)
        project_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "project", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        self.record_entity("project", project_id)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_test_matrix",
                "parameters": {
                    "project_id": project_id
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("requirements_found") == 0
        assert result.get("test_cases_created") == 0
        self.record_entity("test_matrix_view", result["matrix_view_id"])

    async def test_large_project(self, call_mcp):
        """Test setup_test_matrix with large project (50+ requirements)."""
        # This test is simplified for performance - creates 10 requirements
        # In production, you would test with 50+
        project_id, _, _ = await self.setup_project_with_requirements(call_mcp, 10)

        start_time = time.time()
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_test_matrix",
                "parameters": {
                    "project_id": project_id
                }
            }
        )
        duration_ms = (time.time() - start_time) * 1000
        self.performance_analyzer.record_metric(
            "workflow", "setup_test_matrix", duration_ms,
            requirement_count=10, variant="large_project"
        )

        assert result.get("success") is not False
        assert result.get("requirements_found") == 10
        self.record_entity("test_matrix_view", result["matrix_view_id"])

    async def test_only_high_priority_requirements(self, call_mcp):
        """Test setup_test_matrix creates tests only for high priority requirements."""
        # Create project with mixed priority requirements
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        project_data = EntityFactory.project(org_id)
        project_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "project", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        self.record_entity("project", project_id)

        doc_data = EntityFactory.document(project_id)
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "document", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]
        self.record_entity("document", doc_id)

        # Create requirements with specific priorities
        high_count = 0
        for i, priority in enumerate(["high", "high", "medium", "low", "high"]):
            req_data = EntityFactory.requirement(
                doc_id, f"block_{i}", priority=priority
            )
            req_result, _ = await call_mcp(
                "entity_tool",
                {"operation": "create", "entity_type": "requirement", "data": req_data}
            )
            self.record_entity("requirement", req_result["data"]["id"])
            if priority == "high":
                high_count += 1

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_test_matrix",
                "parameters": {
                    "project_id": project_id
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("test_cases_created") == high_count
        self.record_entity("test_matrix_view", result["matrix_view_id"])

    async def test_invalid_project_id(self, call_mcp):
        """Test setup_test_matrix with invalid project ID."""
        # Use a properly formatted UUID that doesn't exist
        invalid_project_id = str(uuid.uuid4())

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "setup_test_matrix",
                "parameters": {
                    "project_id": invalid_project_id
                }
            }
        )

        # The workflow might not fail but should find 0 requirements
        if result.get("success") is not False:
            assert result.get("requirements_found") == 0


@pytest.mark.asyncio
class TestBulkStatusUpdateWorkflow(WorkflowTestSuite):
    """Test suite for bulk_status_update workflow."""

    async def create_test_entities(
        self, call_mcp, entity_type: str, count: int
    ) -> List[str]:
        """Create test entities for bulk update testing.

        Returns:
            List of entity IDs
        """
        entity_ids = []

        if entity_type == "requirement":
            # Need document first
            org_data = EntityFactory.organization()
            org_result, _ = await call_mcp(
                "entity_tool",
                {"operation": "create", "entity_type": "organization", "data": org_data}
            )
            org_id = org_result["data"]["id"]
            self.record_entity("organization", org_id)

            project_data = EntityFactory.project(org_id)
            project_result, _ = await call_mcp(
                "entity_tool",
                {"operation": "create", "entity_type": "project", "data": project_data}
            )
            project_id = project_result["data"]["id"]
            self.record_entity("project", project_id)

            doc_data = EntityFactory.document(project_id)
            doc_result, _ = await call_mcp(
                "entity_tool",
                {"operation": "create", "entity_type": "document", "data": doc_data}
            )
            doc_id = doc_result["data"]["id"]
            self.record_entity("document", doc_id)

            for i in range(count):
                req_data = EntityFactory.requirement(doc_id, f"block_{i}")
                req_result, _ = await call_mcp(
                    "entity_tool",
                    {"operation": "create", "entity_type": "requirement", "data": req_data}
                )
                entity_ids.append(req_result["data"]["id"])
                self.record_entity("requirement", req_result["data"]["id"])

        elif entity_type == "test":
            # Need project first
            org_data = EntityFactory.organization()
            org_result, _ = await call_mcp(
                "entity_tool",
                {"operation": "create", "entity_type": "organization", "data": org_data}
            )
            org_id = org_result["data"]["id"]
            self.record_entity("organization", org_id)

            project_data = EntityFactory.project(org_id)
            project_result, _ = await call_mcp(
                "entity_tool",
                {"operation": "create", "entity_type": "project", "data": project_data}
            )
            project_id = project_result["data"]["id"]
            self.record_entity("project", project_id)

            for i in range(count):
                test_data = EntityFactory.test_entity(project_id)
                test_result, _ = await call_mcp(
                    "entity_tool",
                    {"operation": "create", "entity_type": "test", "data": test_data}
                )
                entity_ids.append(test_result["data"]["id"])
                self.record_entity("test", test_result["data"]["id"])

        return entity_ids

    async def test_single_entity(self, call_mcp):
        """Test bulk_status_update with single entity."""
        entity_ids = await self.create_test_entities(call_mcp, "requirement", 1)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": entity_ids,
                    "new_status": "approved"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("success_count") == 1
        assert result.get("total_entities") == 1
        assert result.get("new_status") == "approved"

    async def test_small_batch_5_entities(self, call_mcp):
        """Test bulk_status_update with 5 entities."""
        entity_ids = await self.create_test_entities(call_mcp, "requirement", 5)

        start_time = time.time()
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": entity_ids,
                    "new_status": "active"
                }
            }
        )
        duration_ms = (time.time() - start_time) * 1000
        self.performance_analyzer.record_metric(
            "workflow", "bulk_status_update", duration_ms,
            entity_count=5, batch_size="small"
        )

        assert result.get("success") is not False
        assert result.get("success_count") == 5

    async def test_large_batch_20_entities(self, call_mcp):
        """Test bulk_status_update with 20 entities (simulating 50)."""
        # Using 20 for performance reasons, but logic is same for 50
        entity_ids = await self.create_test_entities(call_mcp, "requirement", 20)

        start_time = time.time()
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": entity_ids,
                    "new_status": "rejected"
                }
            }
        )
        duration_ms = (time.time() - start_time) * 1000
        self.performance_analyzer.record_metric(
            "workflow", "bulk_status_update", duration_ms,
            entity_count=20, batch_size="large"
        )

        assert result.get("success") is not False
        assert result.get("success_count") == 20

    async def test_status_active(self, call_mcp):
        """Test bulk_status_update with 'active' status."""
        entity_ids = await self.create_test_entities(call_mcp, "requirement", 3)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": entity_ids,
                    "new_status": "active"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("new_status") == "active"

    async def test_status_approved(self, call_mcp):
        """Test bulk_status_update with 'approved' status."""
        entity_ids = await self.create_test_entities(call_mcp, "requirement", 3)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": entity_ids,
                    "new_status": "approved"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("new_status") == "approved"

    async def test_status_rejected(self, call_mcp):
        """Test bulk_status_update with 'rejected' status."""
        entity_ids = await self.create_test_entities(call_mcp, "requirement", 3)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": entity_ids,
                    "new_status": "rejected"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("new_status") == "rejected"

    async def test_entity_type_requirement(self, call_mcp):
        """Test bulk_status_update with requirement entities."""
        entity_ids = await self.create_test_entities(call_mcp, "requirement", 3)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": entity_ids,
                    "new_status": "active"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("entity_type") == "requirement"

    async def test_entity_type_test(self, call_mcp):
        """Test bulk_status_update with test entities."""
        entity_ids = await self.create_test_entities(call_mcp, "test", 3)

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "test",
                    "entity_ids": entity_ids,
                    "new_status": "passed"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("entity_type") == "test"

    async def test_entity_type_document(self, call_mcp):
        """Test bulk_status_update with document entities."""
        # Create documents
        org_data = EntityFactory.organization()
        org_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "organization", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        self.record_entity("organization", org_id)

        project_data = EntityFactory.project(org_id)
        project_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": "project", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        self.record_entity("project", project_id)

        doc_ids = []
        for i in range(3):
            doc_data = EntityFactory.document(project_id)
            doc_result, _ = await call_mcp(
                "entity_tool",
                {"operation": "create", "entity_type": "document", "data": doc_data}
            )
            doc_ids.append(doc_result["data"]["id"])
            self.record_entity("document", doc_result["data"]["id"])

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "document",
                    "entity_ids": doc_ids,
                    "new_status": "published"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("entity_type") == "document"

    async def test_partial_failure(self, call_mcp):
        """Test bulk_status_update with some invalid IDs."""
        valid_ids = await self.create_test_entities(call_mcp, "requirement", 3)
        # Use properly formatted UUIDs that don't exist
        invalid_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        all_ids = valid_ids + invalid_ids

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": all_ids,
                    "new_status": "active"
                }
            }
        )

        # Should still be successful but with partial results
        assert result.get("success") is not False
        assert result.get("success_count") == 3
        assert result.get("total_entities") == 5

        # Check for errors in results
        error_count = sum(
            1 for r in result.get("results", [])
            if "error" in r
        )
        assert error_count == 2

    async def test_all_invalid_ids(self, call_mcp):
        """Test bulk_status_update with all invalid IDs."""
        # Use properly formatted UUIDs that don't exist
        invalid_ids = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]

        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": invalid_ids,
                    "new_status": "active"
                }
            }
        )

        # Should complete but with 0 successes
        assert result.get("success") is not False
        assert result.get("success_count") == 0
        assert result.get("total_entities") == 3


@pytest.mark.asyncio
class TestOrganizationOnboardingWorkflow(WorkflowTestSuite):
    """Test suite for organization_onboarding workflow."""

    async def test_minimal_name_only(self, call_mcp):
        """Test organization_onboarding with minimal parameters (name only)."""
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Minimal Test Organization"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("organization_id")
        assert result.get("steps_completed") >= 3
        self.record_entity("organization", result["organization_id"])

    async def test_with_slug(self, call_mcp):
        """Test organization_onboarding with custom slug."""
        custom_slug = f"custom-slug-{uuid.uuid4().hex[:8]}"
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Organization with Custom Slug",
                    "slug": custom_slug
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("organization_id")
        self.record_entity("organization", result["organization_id"])

        # Verify slug was set
        for step in result.get("results", []):
            if step.get("step") == "create_organization" and "result" in step:
                assert step["result"].get("slug") == custom_slug
                break

    async def test_with_type_enterprise(self, call_mcp):
        """Test organization_onboarding with type='enterprise'."""
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Enterprise Organization",
                    "type": "enterprise"
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("organization_id")
        self.record_entity("organization", result["organization_id"])

        # Verify type was set
        for step in result.get("results", []):
            if step.get("step") == "create_organization" and "result" in step:
                assert step["result"].get("type") == "enterprise"
                break

    async def test_with_description(self, call_mcp):
        """Test organization_onboarding with description."""
        description = "This is a comprehensive organization description for onboarding."
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Described Organization",
                    "description": description
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("organization_id")
        self.record_entity("organization", result["organization_id"])

        # Verify description was set
        for step in result.get("results", []):
            if step.get("step") == "create_organization" and "result" in step:
                assert step["result"].get("description") == description
                break

    async def test_create_starter_project_true(self, call_mcp):
        """Test organization_onboarding with create_starter_project=True."""
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Org with Starter Project",
                    "create_starter_project": True
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("organization_id")
        self.record_entity("organization", result["organization_id"])

        # Check that starter project was created
        project_steps = [
            step for step in result.get("results", [])
            if step.get("step") == "create_starter_project"
        ]
        assert len(project_steps) == 1, f"Expected len(project_steps) == 1, got {len(project_steps)}"
        assert project_steps[0].get("status") == "success"

    async def test_create_starter_project_false(self, call_mcp):
        """Test organization_onboarding with create_starter_project=False."""
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Org without Starter Project",
                    "create_starter_project": False
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("organization_id")
        self.record_entity("organization", result["organization_id"])

        # Check that starter project was NOT created
        project_steps = [
            step for step in result.get("results", [])
            if step.get("step") == "create_starter_project"
        ]
        assert len(project_steps) == 0, f"Expected len(project_steps) == 0, got {len(project_steps)}"

    async def test_all_parameters(self, call_mcp):
        """Test organization_onboarding with all available parameters."""
        custom_slug = f"complete-org-{uuid.uuid4().hex[:8]}"

        start_time = time.time()
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Complete Organization",
                    "slug": custom_slug,
                    "type": "enterprise",
                    "description": "A fully configured organization with all parameters",
                    "create_starter_project": True
                },
                "transaction_mode": True,
                "format_type": "detailed"
            }
        )
        duration_ms = (time.time() - start_time) * 1000
        self.performance_analyzer.record_metric(
            "workflow", "organization_onboarding", duration_ms,
            variant="all_parameters"
        )

        assert result.get("success") is not False
        assert result.get("organization_id")
        assert result.get("steps_successful") >= 4
        self.record_entity("organization", result["organization_id"])

        # Verify all parameters were applied
        for step in result.get("results", []):
            if step.get("step") == "create_organization" and "result" in step:
                org = step["result"]
                assert org.get("name") == "Complete Organization"
                assert org.get("slug") == custom_slug
                assert org.get("type") == "enterprise"
                assert org.get("description") == "A fully configured organization with all parameters"
                break

    async def test_auto_slug_generation(self, call_mcp):
        """Test organization_onboarding with automatic slug generation."""
        org_name = f"Test Org {uuid.uuid4().hex[:4]}"
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": org_name
                    # slug not provided, should be auto-generated
                }
            }
        )

        assert result.get("success") is not False
        assert result.get("organization_id")
        self.record_entity("organization", result["organization_id"])

        # Verify slug was auto-generated from name
        for step in result.get("results", []):
            if step.get("step") == "create_organization" and "result" in step:
                generated_slug = step["result"].get("slug")
                assert generated_slug
                # Should be lowercase and hyphenated version of name
                assert "-" in generated_slug or generated_slug.islower()
                break

    async def test_missing_required_name(self, call_mcp):
        """Test organization_onboarding without required name parameter."""
        result, _ = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "type": "team"
                    # name is missing
                }
            }
        )

        assert result.get("success") is False
        assert "error" in result, f"Expected 'error' in result, got keys: {list(result.keys())}"
        assert "name" in result["error"].lower()


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])