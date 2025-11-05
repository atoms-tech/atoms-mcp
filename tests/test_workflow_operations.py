"""
Workflow Operations Tests

This module contains comprehensive tests for workflow operations:
- import_requirements: Batch requirement import scenarios
- bulk_status_update: Batch status updates for entities
- Performance testing
- Error handling scenarios
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


class WorkflowOperationsTestSuite:
    """Base class for workflow operations test suites."""

    def __init__(self, call_mcp: Callable):
        self.call_mcp = call_mcp
        self.created_entities: list[dict[str, str]] = []

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
                        "soft_delete": True,
                    },
                )
            except Exception:
                pass  # Ignore cleanup errors

    def track_entity(self, entity_type: str, entity_id: str):
        """Track created entity for cleanup."""
        self.created_entities.append({"type": entity_type, "id": entity_id})


class TestWorkflowImportRequirements:
    """Test suite for import_requirements workflow."""

    @pytest.fixture
    def workflow_suite(self, call_mcp):
        """Create workflow test suite."""
        return WorkflowOperationsTestSuite(call_mcp)

    @pytest.mark.asyncio
    async def test_import_requirements_basic(self, workflow_suite):
        """Test import_requirements with basic requirements."""
        requirements = [
            {
                "title": "User Authentication",
                "description": "Implement secure user authentication system",
                "priority": "high",
            },
            {"title": "Data Validation", "description": "Implement data validation rules", "priority": "medium"},
        ]

        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {"operation": "import_requirements", "project_id": str(uuid.uuid4()), "requirements": requirements},
        )

        assert result["success"] is True
        assert "requirements_imported" in result
        assert result["requirements_imported"] == 2

    @pytest.mark.asyncio
    async def test_import_requirements_with_metadata(self, workflow_suite):
        """Test import_requirements with metadata."""
        requirements = [
            {
                "title": "API Integration",
                "description": "Integrate with external API",
                "priority": "high",
                "metadata": {"complexity": "medium", "estimated_hours": 40, "dependencies": ["authentication"]},
            }
        ]

        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {"operation": "import_requirements", "project_id": str(uuid.uuid4()), "requirements": requirements},
        )

        assert result["success"] is True
        assert "requirements_imported" in result
        assert result["requirements_imported"] == 1

    @pytest.mark.asyncio
    async def test_import_requirements_batch_large(self, workflow_suite):
        """Test import_requirements with large batch."""
        requirements = [
            {"title": f"Requirement {i}", "description": f"Description for requirement {i}", "priority": "medium"}
            for i in range(100)
        ]

        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {"operation": "import_requirements", "project_id": str(uuid.uuid4()), "requirements": requirements},
        )

        assert result["success"] is True
        assert "requirements_imported" in result
        assert result["requirements_imported"] == 100

    @pytest.mark.asyncio
    async def test_import_requirements_with_validation(self, workflow_suite):
        """Test import_requirements with validation rules."""
        requirements = [
            {"title": "Valid Requirement", "description": "This is a valid requirement", "priority": "high"},
            {
                "title": "",  # Invalid - empty title
                "description": "This requirement has no title",
                "priority": "medium",
            },
        ]

        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "import_requirements",
                "project_id": str(uuid.uuid4()),
                "requirements": requirements,
                "validate": True,
            },
        )

        assert result["success"] is True
        assert "requirements_imported" in result
        assert "validation_errors" in result
        assert result["requirements_imported"] == 1
        assert len(result["validation_errors"]) == 1

    @pytest.mark.asyncio
    async def test_import_requirements_invalid_project(self, workflow_suite):
        """Test import_requirements with invalid project ID."""
        requirements = [{"title": "Test Requirement", "description": "Test description", "priority": "high"}]

        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {"operation": "import_requirements", "project_id": "invalid-project-id", "requirements": requirements},
        )

        assert result["success"] is False
        assert "project" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_import_requirements_empty_list(self, workflow_suite):
        """Test import_requirements with empty requirements list."""
        result = await workflow_suite.call_mcp(
            "workflow_tool", {"operation": "import_requirements", "project_id": str(uuid.uuid4()), "requirements": []}
        )

        assert result["success"] is False
        assert "empty" in result["error"].lower()


class TestWorkflowBulkStatusUpdate:
    """Test suite for bulk_status_update workflow."""

    @pytest.fixture
    def workflow_suite(self, call_mcp):
        """Create workflow test suite."""
        return WorkflowOperationsTestSuite(call_mcp)

    @pytest.mark.asyncio
    async def test_bulk_status_update_requirements(self, workflow_suite):
        """Test bulk_status_update for requirements."""
        # First create some requirements
        project_id = str(uuid.uuid4())
        requirements = [
            {"title": f"Requirement {i}", "description": f"Description {i}", "priority": "medium"} for i in range(5)
        ]

        # Import requirements
        import_result = await workflow_suite.call_mcp(
            "workflow_tool",
            {"operation": "import_requirements", "project_id": project_id, "requirements": requirements},
        )

        assert import_result["success"] is True
        requirement_ids = import_result["created_requirement_ids"]

        # Update status
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "bulk_status_update",
                "entity_type": "requirement",
                "entity_ids": requirement_ids,
                "new_status": "in_progress",
            },
        )

        assert result["success"] is True
        assert "entities_updated" in result
        assert result["entities_updated"] == 5

    @pytest.mark.asyncio
    async def test_bulk_status_update_tests(self, workflow_suite):
        """Test bulk_status_update for tests."""
        # Create test cases
        test_cases = [{"name": f"Test {i}", "description": f"Test description {i}", "type": "unit"} for i in range(3)]

        # Setup test matrix
        setup_result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_test_matrix",
                "project_id": str(uuid.uuid4()),
                "test_types": ["unit"],
                "test_cases": test_cases,
            },
        )

        assert setup_result["success"] is True
        test_ids = setup_result["created_test_ids"]

        # Update status
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {"operation": "bulk_status_update", "entity_type": "test", "entity_ids": test_ids, "new_status": "passed"},
        )

        assert result["success"] is True
        assert "entities_updated" in result
        assert result["entities_updated"] == 3

    @pytest.mark.asyncio
    async def test_bulk_status_update_with_metadata(self, workflow_suite):
        """Test bulk_status_update with metadata update."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "bulk_status_update",
                "entity_type": "requirement",
                "entity_ids": [str(uuid.uuid4())],
                "new_status": "completed",
                "metadata_update": {"completed_by": "test_user", "completed_at": "2024-01-01T00:00:00Z"},
            },
        )

        assert result["success"] is True
        assert "metadata_updated" in result

    @pytest.mark.asyncio
    async def test_bulk_status_update_invalid_entity_type(self, workflow_suite):
        """Test bulk_status_update with invalid entity type."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "bulk_status_update",
                "entity_type": "invalid_type",
                "entity_ids": [str(uuid.uuid4())],
                "new_status": "active",
            },
        )

        assert result["success"] is False
        assert "entity type" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_bulk_status_update_empty_ids(self, workflow_suite):
        """Test bulk_status_update with empty entity IDs list."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {"operation": "bulk_status_update", "entity_type": "requirement", "entity_ids": [], "new_status": "active"},
        )

        assert result["success"] is False
        assert "empty" in result["error"].lower()


class TestWorkflowPerformance:
    """Test suite for workflow performance scenarios."""

    @pytest.fixture
    def workflow_suite(self, call_mcp):
        """Create workflow test suite."""
        return WorkflowOperationsTestSuite(call_mcp)

    @pytest.mark.asyncio
    async def test_import_requirements_performance(self, workflow_suite):
        """Test import_requirements performance with large dataset."""
        requirements = [
            {
                "title": f"Performance Test Requirement {i}",
                "description": f"Description for requirement {i}",
                "priority": "medium",
            }
            for i in range(1000)
        ]

        start_time = time.time()
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {"operation": "import_requirements", "project_id": str(uuid.uuid4()), "requirements": requirements},
        )
        end_time = time.time()

        assert result["success"] is True
        assert result["requirements_imported"] == 1000

        # Should complete within reasonable time (adjust threshold as needed)
        execution_time = end_time - start_time
        assert execution_time < 30.0  # 30 seconds max

    @pytest.mark.asyncio
    async def test_bulk_status_update_performance(self, workflow_suite):
        """Test bulk_status_update performance with large dataset."""
        entity_ids = [str(uuid.uuid4()) for _ in range(500)]

        start_time = time.time()
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "bulk_status_update",
                "entity_type": "requirement",
                "entity_ids": entity_ids,
                "new_status": "in_progress",
            },
        )
        end_time = time.time()

        assert result["success"] is True
        assert result["entities_updated"] == 500

        # Should complete within reasonable time
        execution_time = end_time - start_time
        assert execution_time < 10.0  # 10 seconds max
