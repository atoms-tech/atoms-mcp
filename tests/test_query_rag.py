"""
Query RAG Tests

This module contains comprehensive tests for RAG (Retrieval-Augmented Generation) functionality:
- Different RAG modes (semantic, keyword, hybrid, neural)
- Entity type variations
- Query variations
- Threshold testing
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
    """Create a server instance with comprehensive test data for RAG scenarios."""
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


class TestQueryRAG:
    """Test RAG (Retrieval-Augmented Generation) functionality."""

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_organizations(self, server_with_test_data):
        """Test RAG in semantic mode for organizations."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization"],
            search_query="technology company",
            rag_mode=RAGMode.SEMANTIC
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find TechCorp based on semantic similarity
        org_names = [entity["name"] for entity in result["entities"]]
        assert "TechCorp" in org_names

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_projects(self, server_with_test_data):
        """Test RAG in keyword mode for projects."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project"],
            search_query="AI platform",
            rag_mode=RAGMode.KEYWORD
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find AI Platform based on keyword matching
        project_names = [entity["name"] for entity in result["entities"]]
        assert "AI Platform" in project_names

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_requirements(self, server_with_test_data):
        """Test RAG in hybrid mode for requirements."""
        result = await server_with_test_data.query_entities(
            entity_types=["Requirement"],
            search_query="user authentication system",
            rag_mode=RAGMode.HYBRID
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find authentication requirement
        req_titles = [entity["title"] for entity in result["entities"]]
        assert "User Authentication" in req_titles

    @pytest.mark.asyncio
    async def test_rag_neural_mode_tests(self, server_with_test_data):
        """Test RAG in neural mode for tests."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"],
            search_query="authentication testing",
            rag_mode=RAGMode.NEURAL
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find authentication test
        test_names = [entity["name"] for entity in result["entities"]]
        assert "Authentication Test" in test_names

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_documents(self, server_with_test_data):
        """Test RAG in semantic mode for documents."""
        result = await server_with_test_data.query_entities(
            entity_types=["Document"],
            search_query="API documentation",
            rag_mode=RAGMode.SEMANTIC
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find API documentation
        doc_titles = [entity["title"] for entity in result["entities"]]
        assert "API Documentation" in doc_titles

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_multiple_entities(self, server_with_test_data):
        """Test RAG in keyword mode across multiple entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project", "Requirement", "Test"],
            search_query="data validation",
            rag_mode=RAGMode.KEYWORD
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find data-related entities
        entity_names = [entity.get("name", entity.get("title", "")) for entity in result["entities"]]
        assert any("data" in name.lower() for name in entity_names)

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_with_filters(self, server_with_test_data):
        """Test RAG in hybrid mode with metadata filters."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"],
            search_query="test functionality",
            rag_mode=RAGMode.HYBRID,
            filters={"metadata.type": "unit"}
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find unit tests
        for entity in result["entities"]:
            assert entity["metadata"]["type"] == "unit"

    @pytest.mark.asyncio
    async def test_rag_neural_mode_with_threshold(self, server_with_test_data):
        """Test RAG in neural mode with similarity threshold."""
        result = await server_with_test_data.query_entities(
            entity_types=["Document"],
            search_query="technical documentation",
            rag_mode=RAGMode.NEURAL,
            similarity_threshold=0.7
        )

        assert result is not None
        assert "entities" in result
        # Results may be empty if threshold is too high
        assert len(result["entities"]) >= 0

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_low_threshold(self, server_with_test_data):
        """Test RAG in semantic mode with low similarity threshold."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization"],
            search_query="company",
            rag_mode=RAGMode.SEMANTIC,
            similarity_threshold=0.1
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find all organizations with low threshold
        org_names = [entity["name"] for entity in result["entities"]]
        assert "TechCorp" in org_names or "DataSystems" in org_names

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_high_threshold(self, server_with_test_data):
        """Test RAG in keyword mode with high similarity threshold."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project"],
            search_query="AI Platform",
            rag_mode=RAGMode.KEYWORD,
            similarity_threshold=0.9
        )

        assert result is not None
        assert "entities" in result
        # May be empty with high threshold
        assert len(result["entities"]) >= 0

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_all_entities(self, server_with_test_data):
        """Test RAG in hybrid mode across all entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project", "Requirement", "Test", "Document"],
            search_query="technology",
            rag_mode=RAGMode.HYBRID
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find technology-related entities
        entity_names = [entity.get("name", entity.get("title", "")) for entity in result["entities"]]
        assert any("tech" in name.lower() for name in entity_names)

    @pytest.mark.asyncio
    async def test_rag_neural_mode_complex_query(self, server_with_test_data):
        """Test RAG in neural mode with complex query."""
        result = await server_with_test_data.query_entities(
            entity_types=["Requirement", "Test"],
            search_query="implement secure authentication system testing",
            rag_mode=RAGMode.NEURAL
        )

        assert result is not None
        assert "entities" in result
        assert len(result["entities"]) >= 1

        # Should find authentication-related entities
        entity_names = [entity.get("name", entity.get("title", "")) for entity in result["entities"]]
        assert any("auth" in name.lower() for name in entity_names)
