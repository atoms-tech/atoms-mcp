"""
Query Analyze Tests

This module contains comprehensive tests for query analysis functionality:
- Different analysis types
- Filter combinations
- Entity type variations
- Analysis result validation
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
    """Create a server instance with comprehensive test data for analysis scenarios."""
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


class TestQueryAnalyze:
    """Test query analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_organizations_by_industry(self, server_with_test_data):
        """Test analyzing organizations by industry."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization"], analysis_type="industry_distribution"
        )

        assert result is not None
        assert "analysis" in result
        assert "industry_distribution" in result["analysis"]

        # Should have technology and data industries
        industries = result["analysis"]["industry_distribution"]
        assert "technology" in industries
        assert "data" in industries

    @pytest.mark.asyncio
    async def test_analyze_projects_by_priority(self, server_with_test_data):
        """Test analyzing projects by priority."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project"], analysis_type="priority_distribution"
        )

        assert result is not None
        assert "analysis" in result
        assert "priority_distribution" in result["analysis"]

        # Should have high and medium priorities
        priorities = result["analysis"]["priority_distribution"]
        assert "high" in priorities
        assert "medium" in priorities

    @pytest.mark.asyncio
    async def test_analyze_requirements_by_complexity(self, server_with_test_data):
        """Test analyzing requirements by complexity."""
        result = await server_with_test_data.query_entities(
            entity_types=["Requirement"], analysis_type="complexity_analysis"
        )

        assert result is not None
        assert "analysis" in result
        assert "complexity_analysis" in result["analysis"]

        # Should have medium and low complexity
        complexities = result["analysis"]["complexity_analysis"]
        assert "medium" in complexities
        assert "low" in complexities

    @pytest.mark.asyncio
    async def test_analyze_tests_by_status(self, server_with_test_data):
        """Test analyzing tests by status."""
        result = await server_with_test_data.query_entities(entity_types=["Test"], analysis_type="status_analysis")

        assert result is not None
        assert "analysis" in result
        assert "status_analysis" in result["analysis"]

        # Should have passed and failed statuses
        statuses = result["analysis"]["status_analysis"]
        assert "PASSED" in statuses
        assert "FAILED" in statuses

    @pytest.mark.asyncio
    async def test_analyze_documents_by_type(self, server_with_test_data):
        """Test analyzing documents by type."""
        result = await server_with_test_data.query_entities(
            entity_types=["Document"], analysis_type="type_distribution"
        )

        assert result is not None
        assert "analysis" in result
        assert "type_distribution" in result["analysis"]

        # Should have documentation and schema types
        types = result["analysis"]["type_distribution"]
        assert "documentation" in types
        assert "schema" in types

    @pytest.mark.asyncio
    async def test_analyze_with_filters(self, server_with_test_data):
        """Test analysis with metadata filters."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"], analysis_type="coverage_analysis", filters={"metadata.type": "unit"}
        )

        assert result is not None
        assert "analysis" in result
        assert "coverage_analysis" in result["analysis"]

        # Should only analyze unit tests
        coverage = result["analysis"]["coverage_analysis"]
        assert "high" in coverage

    @pytest.mark.asyncio
    async def test_analyze_multiple_entity_types(self, server_with_test_data):
        """Test analysis across multiple entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project", "Requirement"], analysis_type="cross_entity_analysis"
        )

        assert result is not None
        assert "analysis" in result
        assert "cross_entity_analysis" in result["analysis"]

        # Should analyze relationships between projects and requirements
        analysis = result["analysis"]["cross_entity_analysis"]
        assert "project_requirement_mapping" in analysis

    @pytest.mark.asyncio
    async def test_analyze_temporal_trends(self, server_with_test_data):
        """Test analyzing temporal trends."""
        result = await server_with_test_data.query_entities(
            entity_types=["Project", "Requirement", "Test"], analysis_type="temporal_analysis"
        )

        assert result is not None
        assert "analysis" in result
        assert "temporal_analysis" in result["analysis"]

        # Should analyze creation patterns over time
        temporal = result["analysis"]["temporal_analysis"]
        assert "creation_trends" in temporal

    @pytest.mark.asyncio
    async def test_analyze_metadata_patterns(self, server_with_test_data):
        """Test analyzing metadata patterns."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project"], analysis_type="metadata_pattern_analysis"
        )

        assert result is not None
        assert "analysis" in result
        assert "metadata_pattern_analysis" in result["analysis"]

        # Should analyze common metadata patterns
        patterns = result["analysis"]["metadata_pattern_analysis"]
        assert "common_fields" in patterns

    @pytest.mark.asyncio
    async def test_analyze_entity_relationships(self, server_with_test_data):
        """Test analyzing entity relationships."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project", "Requirement"], analysis_type="relationship_analysis"
        )

        assert result is not None
        assert "analysis" in result
        assert "relationship_analysis" in result["analysis"]

        # Should analyze how entities are connected
        relationships = result["analysis"]["relationship_analysis"]
        assert "organization_project_links" in relationships
        assert "project_requirement_links" in relationships

    @pytest.mark.asyncio
    async def test_analyze_with_search_query(self, server_with_test_data):
        """Test analysis with search query."""
        result = await server_with_test_data.query_entities(
            entity_types=["Test"], search_query="authentication", analysis_type="query_based_analysis"
        )

        assert result is not None
        assert "analysis" in result
        assert "query_based_analysis" in result["analysis"]

        # Should analyze only authentication-related tests
        analysis = result["analysis"]["query_based_analysis"]
        assert "matching_entities" in analysis

    @pytest.mark.asyncio
    async def test_analyze_all_entity_types(self, server_with_test_data):
        """Test analysis across all entity types."""
        result = await server_with_test_data.query_entities(
            entity_types=["Organization", "Project", "Requirement", "Test", "Document"],
            analysis_type="comprehensive_analysis",
        )

        assert result is not None
        assert "analysis" in result
        assert "comprehensive_analysis" in result["analysis"]

        # Should provide comprehensive analysis
        analysis = result["analysis"]["comprehensive_analysis"]
        assert "entity_type_distribution" in analysis
        assert "cross_entity_insights" in analysis
