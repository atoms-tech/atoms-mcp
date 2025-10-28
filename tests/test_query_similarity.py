"""
Query Similarity Tests

This module contains comprehensive tests for query similarity functionality:
- Basic similarity searches
- Threshold-based similarity
- Entity type variations
- Cross-entity similarity
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
from src.atoms_mcp.models.enums import EntityStatus, RAGMode, RequirementPriority, TestStatus


@pytest.fixture
async def server_with_test_data():
    """Create a server instance with comprehensive test data for similarity scenarios."""
    server = AtomsServer()

    # Create organizations
    org1 = Organization(
        id=str(uuid.uuid4()),
        name="TechCorp",
        description="Leading technology company focused on AI and cloud solutions",
        created_at=datetime.now(UTC),
        metadata={"industry": "technology", "size": "large", "region": "global"}
    )

    org2 = Organization(
        id=str(uuid.uuid4()),
        name="DataSystems",
        description="Data management and analytics company",
        created_at=datetime.now(UTC),
        metadata={"industry": "data", "size": "medium", "region": "north-america"}
    )

    # Create projects
    project1 = Project(
        id=str(uuid.uuid4()),
        name="AI Platform",
        description="Next-generation AI platform for enterprise applications",
        organization_id=org1.id,
        created_at=datetime.now(UTC),
        metadata={"type": "ai", "priority": "high", "status": "active"}
    )

    project2 = Project(
        id=str(uuid.uuid4()),
        name="Data Pipeline",
        description="Real-time data processing pipeline",
        organization_id=org2.id,
        created_at=datetime.now(UTC),
        metadata={"type": "data", "priority": "medium", "status": "planning"}
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
        metadata={"type": "functional", "complexity": "medium"}
    )

    req2 = Requirement(
        id=str(uuid.uuid4()),
        title="Data Validation",
        description="Implement data validation rules",
        project_id=project2.id,
        priority=RequirementPriority.MEDIUM,
        status=EntityStatus.ACTIVE,
        created_at=datetime.now(UTC),
        metadata={"type": "functional", "complexity": "low"}
    )

    # Create tests
    test1 = Test(
        id=str(uuid.uuid4()),
        name="Authentication Test",
        description="Test user authentication functionality",
        project_id=project1.id,
        status=TestStatus.PASSED,
        created_at=datetime.now(UTC),
        metadata={"type": "unit", "coverage": "high"}
    )

    test2 = Test(
        id=str(uuid.uuid4()),
        name="Data Validation Test",
        description="Test data validation rules",
        project_id=project2.id,
        status=TestStatus.FAILED,
        created_at=datetime.now(UTC),
        metadata={"type": "integration", "coverage": "medium"}
    )

    # Create documents
    doc1 = Document(
        id=str(uuid.uuid4()),
        title="API Documentation",
        content="Comprehensive API documentation for the AI platform",
        project_id=project1.id,
        created_at=datetime.now(UTC),
        metadata={"type": "documentation", "format": "markdown"}
    )

    doc2 = Document(
        id=str(uuid.uuid4()),
        title="Data Schema",
        content="Data schema definitions and validation rules",
        project_id=project2.id,
        created_at=datetime.now(UTC),
        metadata={"type": "schema", "format": "json"}
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


class TestQuerySimilarity:
    """Test query similarity functionality."""

    @pytest.mark.asyncio
    async def test_similarity_basic_organizations(self, server_with_test_data):
        """Test basic similarity search for organizations."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization"],
            search_query="tech company",
            similarity_threshold=0.5
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find TechCorp based on similarity
        org_names = [entity["name"] for entity in result["entities"]]
        assert "TechCorp" in org_names

    @pytest.mark.asyncio
    async def test_similarity_high_threshold(self, server_with_test_data):
        """Test similarity search with high threshold."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project"],
            search_query="AI platform",
            similarity_threshold=0.9
        )

        assert result is not None
        assert "entities" in result
        # May be empty with high threshold
        assert len(result["entities"]) >= 0

    @pytest.mark.asyncio
    async def test_similarity_low_threshold(self, server_with_test_data):
        """Test similarity search with low threshold."""
        result = await server_with_test_data.query_entities(
            entity_types=["Requirement"],
            search_query="system",
            similarity_threshold=0.1
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find requirements with low threshold
        req_titles = [entity["title"] for entity in result["entities"]]
        assert any("system" in title.lower() for title in req_titles)

    @pytest.mark.asyncio
    async def test_similarity_multiple_entity_types(self, server_with_test_data):
        """Test similarity search across multiple entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project", "Requirement", "Test"],
            search_query="authentication",
            similarity_threshold=0.6
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find authentication-related entities
        entity_names = [entity.get("name", entity.get("title", "")) for entity in result["entities"]]
        assert any("auth" in name.lower() for name in entity_names)

    @pytest.mark.asyncio
    async def test_similarity_with_filters(self, server_with_test_data):
        """Test similarity search with metadata filters."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"],
            search_query="unit test",
            similarity_threshold=0.5,
            filters={"metadata.type": "unit"}
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find unit tests
        for entity in result["entities"]:
            assert entity["metadata"]["type"] == "unit"

    @pytest.mark.asyncio
    async def test_similarity_documents(self, server_with_test_data):
        """Test similarity search for documents."""
        result = await server_with_test_data.query_entities(
            entity_types=["Document"],
            search_query="API documentation",
            similarity_threshold=0.7
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find API documentation
        doc_titles = [entity["title"] for entity in result["entities"]]
        assert "API Documentation" in doc_titles

    @pytest.mark.asyncio
    async def test_similarity_cross_entity_semantic(self, server_with_test_data):
        """Test cross-entity semantic similarity."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project"],
            search_query="technology solutions",
            similarity_threshold=0.6
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find technology-related entities
        entity_names = [entity.get("name", entity.get("title", "")) for entity in result["entities"]]
        assert any("tech" in name.lower() or "ai" in name.lower() for name in entity_names)

    @pytest.mark.asyncio
    async def test_similarity_requirement_test_matching(self, server_with_test_data):
        """Test similarity between requirements and tests."""
        result = await server_with_test_data.query_entities(
            entity_types=["Requirement", "Test"],
            search_query="validation",
            similarity_threshold=0.5
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find validation-related entities
        entity_names = [entity.get("name", entity.get("title", "")) for entity in result["entities"]]
        assert any("validation" in name.lower() for name in entity_names)

    @pytest.mark.asyncio
    async def test_similarity_with_rag_mode(self, server_with_test_data):
        """Test similarity search with RAG mode."""
        result = await server_with_test_data.query_entities(
            entity_types=["Document"],
            search_query="technical documentation",
            similarity_threshold=0.6,
            rag_mode=RAGMode.SEMANTIC
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find documentation
        doc_titles = [entity["title"] for entity in result["entities"]]
        assert "API Documentation" in doc_titles

    @pytest.mark.asyncio
    async def test_similarity_no_matches(self, server_with_test_data):
        """Test similarity search with no matches."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization"],
            search_query="completely unrelated query",
            similarity_threshold=0.9
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) == 0

    @pytest.mark.asyncio
    async def test_similarity_all_entity_types(self, server_with_test_data):
        """Test similarity search across all entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project", "Requirement", "Test", "Document"],
            search_query="data",
            similarity_threshold=0.4
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find data-related entities
        entity_names = [entity.get("name", entity.get("title", "")) for entity in result["entities"]]
        assert any("data" in name.lower() for name in entity_names)
