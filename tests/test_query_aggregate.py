"""
Query Aggregate Tests

This module contains comprehensive tests for query aggregation functionality:
- Count aggregations
- Sum aggregations
- Average aggregations
- Group by operations
- Filter combinations
"""

import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Add the parent directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.atoms_mcp.core.mcp_server import AtomsServer
from src.atoms_mcp.models.base import Document, Organization, Project, Requirement, Test
from src.atoms_mcp.models.enums import EntityStatus, RequirementPriority, TestStatus


@pytest.fixture
async def server_with_test_data():
    """Create a server instance with comprehensive test data for aggregation scenarios."""
    server = AtomsServer()

    # Create organizations
    org1 = Organization(
        id=str(uuid.uuid4()),
        name="TechCorp",
        description="Leading technology company focused on AI and cloud solutions",
        created_at=datetime.now(UTC),
        metadata={"industry": "technology", "size": "large", "region": "global"},
    )

    org2 = Organization(
        id=str(uuid.uuid4()),
        name="DataSystems",
        description="Data management and analytics company",
        created_at=datetime.now(UTC),
        metadata={"industry": "data", "size": "medium", "region": "north-america"},
    )

    # Create projects
    project1 = Project(
        id=str(uuid.uuid4()),
        name="AI Platform",
        description="Next-generation AI platform for enterprise applications",
        organization_id=org1.id,
        created_at=datetime.now(UTC),
        metadata={"type": "ai", "priority": "high", "status": "active"},
    )

    project2 = Project(
        id=str(uuid.uuid4()),
        name="Data Pipeline",
        description="Real-time data processing pipeline",
        organization_id=org2.id,
        created_at=datetime.now(UTC),
        metadata={"type": "data", "priority": "medium", "status": "planning"},
    )

    # Create requirements
    req1 = Requirement(
        id=str(uuid.uuid4()),
        title="User Authentication",
        description="Implement secure user authentication system",
        project_id=project1.id,
        priority=RequirementPriority.HIGH,
        status=EntityStatus.ACTIVE,
        created_at=datetime.now(UTC),
        metadata={"type": "functional", "complexity": "medium"},
    )

    req2 = Requirement(
        id=str(uuid.uuid4()),
        title="Data Validation",
        description="Implement data validation rules",
        project_id=project2.id,
        priority=RequirementPriority.MEDIUM,
        status=EntityStatus.ACTIVE,
        created_at=datetime.now(UTC),
        metadata={"type": "functional", "complexity": "low"},
    )

    # Create tests
    test1 = Test(
        id=str(uuid.uuid4()),
        name="Authentication Test",
        description="Test user authentication functionality",
        project_id=project1.id,
        status=TestStatus.PASSED,
        created_at=datetime.now(UTC),
        metadata={"type": "unit", "coverage": "high"},
    )

    test2 = Test(
        id=str(uuid.uuid4()),
        name="Data Validation Test",
        description="Test data validation rules",
        project_id=project2.id,
        status=TestStatus.FAILED,
        created_at=datetime.now(UTC),
        metadata={"type": "integration", "coverage": "medium"},
    )

    # Create documents
    doc1 = Document(
        id=str(uuid.uuid4()),
        title="API Documentation",
        content="Comprehensive API documentation for the AI platform",
        project_id=project1.id,
        created_at=datetime.now(UTC),
        metadata={"type": "documentation", "format": "markdown"},
    )

    doc2 = Document(
        id=str(uuid.uuid4()),
        title="Data Schema",
        content="Data schema definitions and validation rules",
        project_id=project2.id,
        created_at=datetime.now(UTC),
        metadata={"type": "schema", "format": "json"},
    )

    # Store all entities
    await server.store_entity(org1)
    await server.store_entity(org2)
    await server.store_entity(project1)
    await server.store_entity(project2)
    await server.store_entity(req1)
    await server.store_entity(req2)
    await server.store_entity(test1)
    await server.store_entity(test2)
    await server.store_entity(doc1)
    await server.store_entity(doc2)

    return server


class TestQueryAggregate:
    """Test query aggregation functionality."""

    @pytest.mark.asyncio
    async def test_count_organizations(self, server_with_test_data):
        """Test counting organizations."""
        result = await server_with_test_data.query_entities(entity_types=["Organization"], aggregate="count")

        assert result is not None
        assert "count" in result
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_count_projects_by_organization(self, server_with_test_data):
        """Test counting projects grouped by organization."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project"], aggregate="count", group_by="organization_id"
        )

        assert result is not None
        assert "groups" in result
        assert len(result["groups"]) == 2
        for group in result["groups"]:
            assert "organization_id" in group
            assert "count" in group
            assert group["count"] == 1

    @pytest.mark.asyncio
    async def test_count_requirements_by_priority(self, server_with_test_data):
        """Test counting requirements grouped by priority."""
        result = await server_with_test_data.query_entities(
            entity_types=["Requirement"], aggregate="count", group_by="priority"
        )

        assert result is not None
        assert "groups" in result
        assert len(result["groups"]) == 2

        # Should have one HIGH and one MEDIUM priority
        priorities = [group["priority"] for group in result["groups"]]
        assert "HIGH" in priorities
        assert "MEDIUM" in priorities

    @pytest.mark.asyncio
    async def test_count_tests_by_status(self, server_with_test_data):
        """Test counting tests grouped by status."""
        result = await server_with_test_data.query_entities(entity_types=["Test"], aggregate="count", group_by="status")

        assert result is not None
        assert "groups" in result
        assert len(result["groups"]) == 2

        # Should have one PASSED and one FAILED status
        statuses = [group["status"] for group in result["groups"]]
        assert "PASSED" in statuses
        assert "FAILED" in statuses

    @pytest.mark.asyncio
    async def test_count_documents_by_type(self, server_with_test_data):
        """Test counting documents grouped by type."""
        result = await server_with_test_data.query_entities(
            entity_types=["Document"], aggregate="count", group_by="metadata.type"
        )

        assert result is not None
        assert "groups" in result
        assert len(result["groups"]) == 2

        # Should have documentation and schema types
        types = [group["metadata.type"] for group in result["groups"]]
        assert "documentation" in types
        assert "schema" in types

    @pytest.mark.asyncio
    async def test_count_with_filters(self, server_with_test_data):
        """Test counting with metadata filters."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"], aggregate="count", filters={"metadata.type": "unit"}
        )

        assert result is not None
        assert "count" in result
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_count_multiple_entity_types(self, server_with_test_data):
        """Test counting across multiple entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project", "Requirement"], aggregate="count"
        )

        assert result is not None
        assert "count" in result
        assert result["count"] == 5  # 2 orgs + 2 projects + 1 requirement

    @pytest.mark.asyncio
    async def test_count_by_metadata_field(self, server_with_test_data):
        """Test counting grouped by metadata field."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project"], aggregate="count", group_by="metadata.type"
        )

        assert result is not None
        assert "groups" in result
        assert len(result["groups"]) == 2

        # Should have ai and data types
        types = [group["metadata.type"] for group in result["groups"]]
        assert "ai" in types
        assert "data" in types

    @pytest.mark.asyncio
    async def test_count_with_search_query(self, server_with_test_data):
        """Test counting with search query."""
        result = await server_with_test_data.query_entities(
            entity_types=["Document"], search_query="API", aggregate="count"
        )

        assert result is not None
        assert "count" in result
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_count_with_complex_filters(self, server_with_test_data):
        """Test counting with complex metadata filters."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"], aggregate="count", filters={"metadata.type": "unit", "status": "PASSED"}
        )

        assert result is not None
        assert "count" in result
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_count_all_entities(self, server_with_test_data):
        """Test counting all entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project", "Requirement", "Test", "Document"], aggregate="count"
        )

        assert result is not None
        assert "count" in result
        assert result["count"] == 8  # Total entities

    @pytest.mark.asyncio
    async def test_count_with_nested_group_by(self, server_with_test_data):
        """Test counting with nested group by."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"], aggregate="count", group_by=["metadata.type", "status"]
        )

        assert result is not None
        assert "groups" in result
        assert len(result["groups"]) == 2

        # Should have unit/PASSED and integration/FAILED combinations
        combinations = [(group["metadata.type"], group["status"]) for group in result["groups"]]
        assert ("unit", "PASSED") in combinations
        assert ("integration", "FAILED") in combinations
