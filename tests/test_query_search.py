"""
Query Search Tests

This module contains comprehensive tests for query search functionality:
- Single entity search tests
- Multi-entity search tests
- Filter application tests
- Limit and ordering tests
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
    """Create a server instance with comprehensive test data for all query scenarios."""
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


class TestQuerySearch:
    """Test query search functionality."""

    @pytest.mark.asyncio
    async def test_search_single_entity(self, server_with_test_data):
        """Test searching for a single entity type."""
        result = await server_with_test_data.query_entities(entity_types=["Organization"], search_query="TechCorp")

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) == 1
        assert result["entities"][0]["name"] == "TechCorp"

    @pytest.mark.asyncio
    async def test_search_multiple_entities(self, server_with_test_data):
        """Test searching across multiple entity types."""
        result = await server_with_test_data.query_entities(entity_types=["Organization", "Project"], search_query="AI")

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find the AI Platform project
        project_names = [entity["name"] for entity in result["entities"]]
        assert "AI Platform" in project_names

    @pytest.mark.asyncio
    async def test_search_with_filters(self, server_with_test_data):
        """Test searching with metadata filters."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project"], search_query="platform", filters={"metadata.type": "ai"}
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) == 1
        assert result["entities"][0]["name"] == "AI Platform"
        assert result["entities"][0]["metadata"]["type"] == "ai"

    @pytest.mark.asyncio
    async def test_search_with_limit(self, server_with_test_data):
        """Test searching with result limit."""
        result = await server_with_test_data.query_entities(
            entity_types=["Document"], search_query="documentation", limit=1
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) <= 1

    @pytest.mark.asyncio
    async def test_search_with_ordering(self, server_with_test_data):
        """Test searching with ordering."""
        result = await server_with_test_data.query_entities(
            entity_types=["Requirement"], search_query="implement", order_by="priority", order_direction="desc"
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should be ordered by priority (HIGH comes before MEDIUM)
        priorities = [entity["priority"] for entity in result["entities"]]
        assert priorities[0] == "HIGH"

    @pytest.mark.asyncio
    async def test_search_no_results(self, server_with_test_data):
        """Test searching with no matching results."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization"], search_query="NonExistentCompany"
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) == 0

    @pytest.mark.asyncio
    async def test_search_all_entity_types(self, server_with_test_data):
        """Test searching across all entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project", "Requirement", "Test", "Document"], search_query="data"
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find entities with "data" in their content
        entity_names = [entity.get("name", entity.get("title", "")) for entity in result["entities"]]
        assert any("data" in name.lower() for name in entity_names)

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, server_with_test_data):
        """Test that search is case insensitive."""
        result = await server_with_test_data.query_entities(entity_types=["Organization"], search_query="techcorp")

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) == 1
        assert result["entities"][0]["name"] == "TechCorp"

    @pytest.mark.asyncio
    async def test_search_partial_match(self, server_with_test_data):
        """Test searching with partial matches."""
        result = await server_with_test_data.query_entities(entity_types=["Project"], search_query="platform")

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) == 1
        assert "platform" in result["entities"][0]["name"].lower()

    @pytest.mark.asyncio
    async def test_search_with_complex_filters(self, server_with_test_data):
        """Test searching with complex metadata filters."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"], search_query="test", filters={"metadata.type": "unit", "status": "PASSED"}
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) == 1
        assert result["entities"][0]["name"] == "Authentication Test"
        assert result["entities"][0]["metadata"]["type"] == "unit"
        assert result["entities"][0]["status"] == "PASSED"
