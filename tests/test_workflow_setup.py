"""
Workflow Setup Tests

This module contains comprehensive tests for workflow setup operations:
- setup_project: Project initialization with various configurations
- setup_test_matrix: Test matrix creation and configuration
- organization_onboarding: Organization setup and initialization
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


class WorkflowSetupTestSuite:
    """Base class for workflow setup test suites."""

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
                        "soft_delete": True
                    }
                )
            except Exception:
                pass  # Ignore cleanup errors

    def track_entity(self, entity_type: str, entity_id: str):
        """Track created entity for cleanup."""
        self.created_entities.append({"type": entity_type, "id": entity_id})


class TestWorkflowSetupProject:
    """Test suite for setup_project workflow."""

    @pytest.fixture
    def workflow_suite(self, call_mcp):
        """Create workflow test suite."""
        return WorkflowSetupTestSuite(call_mcp)
        # Cleanup is handled by the suite

    @pytest.mark.asyncio
    async def test_setup_project_minimal(self, workflow_suite):
        """Test setup_project with minimal parameters."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_project",
                "project_name": "Test Project",
                "organization_id": str(uuid.uuid4())
            }
        )

        assert result["success"] is True
        assert "project_id" in result
        workflow_suite.track_entity("project", result["project_id"])

    @pytest.mark.asyncio
    async def test_setup_project_full_parameters(self, workflow_suite):
        """Test setup_project with full parameters."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_project",
                "project_name": "Full Test Project",
                "organization_id": str(uuid.uuid4()),
                "description": "A comprehensive test project",
                "metadata": {
                    "priority": "high",
                    "type": "development",
                    "status": "active"
                },
                "settings": {
                    "auto_approve": True,
                    "notifications": True,
                    "version_control": "git"
                }
            }
        )

        assert result["success"] is True
        assert "project_id" in result
        assert result["project_name"] == "Full Test Project"
        workflow_suite.track_entity("project", result["project_id"])

    @pytest.mark.asyncio
    async def test_setup_project_with_requirements(self, workflow_suite):
        """Test setup_project with initial requirements."""
        requirements = [
            {
                "title": "User Authentication",
                "description": "Implement secure user authentication",
                "priority": "high"
            },
            {
                "title": "Data Validation",
                "description": "Implement data validation rules",
                "priority": "medium"
            }
        ]

        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_project",
                "project_name": "Project with Requirements",
                "organization_id": str(uuid.uuid4()),
                "requirements": requirements
            }
        )

        assert result["success"] is True
        assert "project_id" in result
        assert "requirements_created" in result
        assert result["requirements_created"] == 2
        workflow_suite.track_entity("project", result["project_id"])

    @pytest.mark.asyncio
    async def test_setup_project_with_tests(self, workflow_suite):
        """Test setup_project with initial test cases."""
        test_cases = [
            {
                "name": "Authentication Test",
                "description": "Test user authentication functionality",
                "type": "unit"
            },
            {
                "name": "Data Validation Test",
                "description": "Test data validation rules",
                "type": "integration"
            }
        ]

        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_project",
                "project_name": "Project with Tests",
                "organization_id": str(uuid.uuid4()),
                "test_cases": test_cases
            }
        )

        assert result["success"] is True
        assert "project_id" in result
        assert "tests_created" in result
        assert result["tests_created"] == 2
        workflow_suite.track_entity("project", result["project_id"])

    @pytest.mark.asyncio
    async def test_setup_project_duplicate_name(self, workflow_suite):
        """Test setup_project with duplicate project name."""
        project_name = "Duplicate Test Project"
        organization_id = str(uuid.uuid4())

        # Create first project
        result1 = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_project",
                "project_name": project_name,
                "organization_id": organization_id
            }
        )

        assert result1["success"] is True
        workflow_suite.track_entity("project", result1["project_id"])

        # Try to create duplicate
        result2 = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_project",
                "project_name": project_name,
                "organization_id": organization_id
            }
        )

        assert result2["success"] is False
        assert "already exists" in result2["error"].lower()

    @pytest.mark.asyncio
    async def test_setup_project_invalid_organization(self, workflow_suite):
        """Test setup_project with invalid organization ID."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_project",
                "project_name": "Test Project",
                "organization_id": "invalid-id"
            }
        )

        assert result["success"] is False
        assert "organization" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_setup_project_missing_required_fields(self, workflow_suite):
        """Test setup_project with missing required fields."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_project",
                "project_name": "Test Project"
                # Missing organization_id
            }
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestWorkflowSetupTestMatrix:
    """Test suite for setup_test_matrix workflow."""

    @pytest.fixture
    def workflow_suite(self, call_mcp):
        """Create workflow test suite."""
        return WorkflowSetupTestSuite(call_mcp)

    @pytest.mark.asyncio
    async def test_setup_test_matrix_basic(self, workflow_suite):
        """Test setup_test_matrix with basic configuration."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_test_matrix",
                "project_id": str(uuid.uuid4()),
                "test_types": ["unit", "integration", "e2e"]
            }
        )

        assert result["success"] is True
        assert "test_matrix_id" in result
        assert "test_cases_created" in result

    @pytest.mark.asyncio
    async def test_setup_test_matrix_with_requirements(self, workflow_suite):
        """Test setup_test_matrix with requirements mapping."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_test_matrix",
                "project_id": str(uuid.uuid4()),
                "test_types": ["unit", "integration"],
                "requirements_mapping": {
                    "unit": ["functional", "performance"],
                    "integration": ["api", "database"]
                }
            }
        )

        assert result["success"] is True
        assert "test_matrix_id" in result
        assert "mappings_created" in result

    @pytest.mark.asyncio
    async def test_setup_test_matrix_with_metadata(self, workflow_suite):
        """Test setup_test_matrix with metadata configuration."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "setup_test_matrix",
                "project_id": str(uuid.uuid4()),
                "test_types": ["unit", "integration", "e2e"],
                "metadata": {
                    "coverage_target": 80,
                    "automation_level": "high",
                    "priority": "critical"
                }
            }
        )

        assert result["success"] is True
        assert "test_matrix_id" in result
        assert "metadata_applied" in result


class TestWorkflowOrganizationOnboarding:
    """Test suite for organization_onboarding workflow."""

    @pytest.fixture
    def workflow_suite(self, call_mcp):
        """Create workflow test suite."""
        return WorkflowSetupTestSuite(call_mcp)

    @pytest.mark.asyncio
    async def test_organization_onboarding_basic(self, workflow_suite):
        """Test organization_onboarding with basic configuration."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "organization_onboarding",
                "organization_name": "Test Organization",
                "admin_email": "admin@test.com"
            }
        )

        assert result["success"] is True
        assert "organization_id" in result
        assert "admin_user_id" in result
        workflow_suite.track_entity("organization", result["organization_id"])

    @pytest.mark.asyncio
    async def test_organization_onboarding_full(self, workflow_suite):
        """Test organization_onboarding with full configuration."""
        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "organization_onboarding",
                "organization_name": "Full Test Organization",
                "admin_email": "admin@fulltest.com",
                "organization_metadata": {
                    "industry": "technology",
                    "size": "medium",
                    "region": "north-america"
                },
                "settings": {
                    "auto_approve_projects": True,
                    "require_approval": False,
                    "notification_preferences": "email"
                }
            }
        )

        assert result["success"] is True
        assert "organization_id" in result
        assert "admin_user_id" in result
        assert "settings_applied" in result
        workflow_suite.track_entity("organization", result["organization_id"])

    @pytest.mark.asyncio
    async def test_organization_onboarding_with_initial_projects(self, workflow_suite):
        """Test organization_onboarding with initial projects."""
        initial_projects = [
            {
                "name": "Initial Project 1",
                "description": "First project for the organization"
            },
            {
                "name": "Initial Project 2",
                "description": "Second project for the organization"
            }
        ]

        result = await workflow_suite.call_mcp(
            "workflow_tool",
            {
                "operation": "organization_onboarding",
                "organization_name": "Organization with Projects",
                "admin_email": "admin@projecttest.com",
                "initial_projects": initial_projects
            }
        )

        assert result["success"] is True
        assert "organization_id" in result
        assert "projects_created" in result
        assert result["projects_created"] == 2
        workflow_suite.track_entity("organization", result["organization_id"])
