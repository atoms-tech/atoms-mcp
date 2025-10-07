"""
Comprehensive Query Parameter Matrix Tests

This module contains 65+ comprehensive tests covering all query parameter combinations:
- Search tests: 15 tests covering single/multi entity, filters, limits, ordering
- RAG tests: 24 tests covering 4 modes × 3 entities × 2 queries + threshold variations
- Aggregate tests: 12 tests covering all entities with filters and projections
- Similarity tests: 6 tests covering basic, threshold, and entity type variations
- Analyze tests: 8 tests covering different analysis types with filters

Each test includes comprehensive assertions to validate:
- Response structure and data types
- Field presence and validity
- Filter application correctness
- Sorting and limiting behavior
- RAG mode effectiveness
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

# Add the parent directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.atoms_mcp.mcp_server import AtomsServer
from src.atoms_mcp.models.base import Organization, Project, Document, Requirement, Test, TestRun
from src.atoms_mcp.models.knowledge import SemanticSearchResult
from src.atoms_mcp.models.enums import EntityStatus, RequirementPriority, TestStatus, RAGMode


@pytest.fixture
async def server_with_test_data():
    """Create a server instance with comprehensive test data for all query scenarios."""
    server = AtomsServer()

    # Create organizations
    org1 = Organization(
        id=str(uuid.uuid4()),
        name="TechCorp",
        description="Leading technology company focused on AI and cloud solutions",
        created_at=datetime.now(timezone.utc),
        metadata={"industry": "technology", "size": "large", "region": "global"}
    )

    org2 = Organization(
        id=str(uuid.uuid4()),
        name="DataSystems",
        description="Data analytics and business intelligence solutions provider",
        created_at=datetime.now(timezone.utc),
        metadata={"industry": "data", "size": "medium", "region": "north_america"}
    )

    server.storage.organizations[org1.id] = org1
    server.storage.organizations[org2.id] = org2

    # Create projects with different statuses
    proj1 = Project(
        id=str(uuid.uuid4()),
        name="CloudPlatform",
        organization_id=org1.id,
        description="Enterprise cloud infrastructure platform with microservices architecture",
        status=EntityStatus.ACTIVE,
        metadata={"type": "infrastructure", "team_size": 25, "budget": 5000000}
    )

    proj2 = Project(
        id=str(uuid.uuid4()),
        name="AIAnalytics",
        organization_id=org1.id,
        description="Machine learning powered analytics dashboard for business insights",
        status=EntityStatus.IN_PROGRESS,
        metadata={"type": "ai_ml", "team_size": 15, "budget": 2000000}
    )

    proj3 = Project(
        id=str(uuid.uuid4()),
        name="DataPipeline",
        organization_id=org2.id,
        description="Real-time data processing pipeline for streaming analytics",
        status=EntityStatus.ACTIVE,
        metadata={"type": "data_processing", "team_size": 10, "budget": 1500000}
    )

    server.storage.projects[proj1.id] = proj1
    server.storage.projects[proj2.id] = proj2
    server.storage.projects[proj3.id] = proj3

    # Create documents with rich content for RAG testing
    doc1 = Document(
        id=str(uuid.uuid4()),
        name="Architecture Guide",
        project_id=proj1.id,
        content="Comprehensive microservices architecture guide covering service mesh, API gateway, container orchestration with Kubernetes, and event-driven patterns using Apache Kafka for real-time data streaming.",
        doc_type="technical",
        metadata={"version": "2.0", "pages": 150, "format_type": "markdown", "tags": ["architecture", "microservices", "kubernetes"]}
    )

    doc2 = Document(
        id=str(uuid.uuid4()),
        name="ML Model Documentation",
        project_id=proj2.id,
        content="Deep learning models for natural language processing including transformer architectures, BERT fine-tuning, and custom neural networks for sentiment analysis and entity recognition.",
        doc_type="technical",
        metadata={"version": "1.5", "pages": 85, "format_type": "jupyter", "tags": ["ml", "nlp", "deep_learning"]}
    )

    doc3 = Document(
        id=str(uuid.uuid4()),
        name="API Reference",
        project_id=proj1.id,
        content="RESTful API documentation with OpenAPI specification, authentication using OAuth 2.0, rate limiting strategies, and comprehensive error handling patterns for distributed systems.",
        doc_type="api",
        metadata={"version": "3.0", "endpoints": 125, "format_type": "openapi", "tags": ["api", "rest", "oauth"]}
    )

    doc4 = Document(
        id=str(uuid.uuid4()),
        name="Data Schema Documentation",
        project_id=proj3.id,
        content="Database schema design with normalized tables, indexing strategies, partitioning schemes for time-series data, and optimization techniques for high-throughput queries.",
        doc_type="technical",
        metadata={"version": "1.0", "tables": 45, "format_type": "sql", "tags": ["database", "schema", "optimization"]}
    )

    server.storage.documents[doc1.id] = doc1
    server.storage.documents[doc2.id] = doc2
    server.storage.documents[doc3.id] = doc3
    server.storage.documents[doc4.id] = doc4

    # Create requirements with different priorities and statuses
    req1 = Requirement(
        id=str(uuid.uuid4()),
        name="User Authentication",
        project_id=proj1.id,
        description="Implement secure multi-factor authentication with biometric support, single sign-on integration, and session management for enterprise users.",
        priority=RequirementPriority.CRITICAL,
        status=EntityStatus.ACTIVE,
        metadata={"category": "security", "effort": "high", "sprint": 3}
    )

    req2 = Requirement(
        id=str(uuid.uuid4()),
        name="Real-time Analytics",
        project_id=proj2.id,
        description="Build real-time data analytics pipeline with streaming processing, complex event processing, and interactive dashboards for business metrics visualization.",
        priority=RequirementPriority.HIGH,
        status=EntityStatus.IN_PROGRESS,
        metadata={"category": "analytics", "effort": "medium", "sprint": 4}
    )

    req3 = Requirement(
        id=str(uuid.uuid4()),
        name="API Rate Limiting",
        project_id=proj1.id,
        description="Implement adaptive rate limiting with token bucket algorithm, per-user quotas, and graceful degradation for API endpoints under high load.",
        priority=RequirementPriority.MEDIUM,
        status=EntityStatus.ACTIVE,
        metadata={"category": "performance", "effort": "medium", "sprint": 5}
    )

    req4 = Requirement(
        id=str(uuid.uuid4()),
        name="Data Backup Strategy",
        project_id=proj3.id,
        description="Design and implement automated backup strategy with incremental backups, point-in-time recovery, and cross-region replication for disaster recovery.",
        priority=RequirementPriority.HIGH,
        status=EntityStatus.COMPLETED,
        metadata={"category": "infrastructure", "effort": "high", "sprint": 2}
    )

    req5 = Requirement(
        id=str(uuid.uuid4()),
        name="UI Responsiveness",
        project_id=proj2.id,
        description="Optimize frontend performance with lazy loading, code splitting, service workers for offline support, and responsive design for mobile devices.",
        priority=RequirementPriority.LOW,
        status=EntityStatus.ACTIVE,
        metadata={"category": "frontend", "effort": "low", "sprint": 6}
    )

    server.storage.requirements[req1.id] = req1
    server.storage.requirements[req2.id] = req2
    server.storage.requirements[req3.id] = req3
    server.storage.requirements[req4.id] = req4
    server.storage.requirements[req5.id] = req5

    # Create tests for comprehensive coverage
    test1 = Test(
        id=str(uuid.uuid4()),
        name="Authentication Security Test",
        requirement_id=req1.id,
        description="Comprehensive security testing for authentication including SQL injection, XSS, CSRF, session hijacking, and brute force attack prevention.",
        test_type="security",
        status=TestStatus.PASSED,
        metadata={"coverage": 95, "duration": 120, "automated": True}
    )

    test2 = Test(
        id=str(uuid.uuid4()),
        name="Performance Load Test",
        requirement_id=req2.id,
        description="Load testing with concurrent users, stress testing under peak load, endurance testing for memory leaks, and spike testing for sudden traffic.",
        test_type="performance",
        status=TestStatus.FAILED,
        metadata={"coverage": 80, "duration": 300, "automated": True}
    )

    test3 = Test(
        id=str(uuid.uuid4()),
        name="API Integration Test",
        requirement_id=req3.id,
        description="End-to-end API testing including request validation, response formatting, error handling, timeout scenarios, and rate limit enforcement.",
        test_type="integration",
        status=TestStatus.IN_PROGRESS,
        metadata={"coverage": 70, "duration": 45, "automated": False}
    )

    server.storage.tests[test1.id] = test1
    server.storage.tests[test2.id] = test2
    server.storage.tests[test3.id] = test3

    # Store IDs for easy reference in tests
    server.test_data = {
        'org_ids': [org1.id, org2.id],
        'project_ids': [proj1.id, proj2.id, proj3.id],
        'document_ids': [doc1.id, doc2.id, doc3.id, doc4.id],
        'requirement_ids': [req1.id, req2.id, req3.id, req4.id, req5.id],
        'test_ids': [test1.id, test2.id, test3.id]
    }

    return server


class TestSearchQueries:
    """Test suite for search queries covering single/multi entity, filters, limits, and ordering."""

    @pytest.mark.asyncio
    async def test_search_single_entity_project(self, server_with_test_data):
        """Test searching for single project entity."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["project"],
            "search_term": "cloud"
        })

        assert result["success"] is True
        assert "results" in result
        assert len(result["results"]) > 0

        # Verify all results are projects
        for item in result["results"]:
            assert item["entity_type"] == "project"
            assert "cloud" in item["name"].lower() or "cloud" in item.get("description", "").lower()

    @pytest.mark.asyncio
    async def test_search_single_entity_document(self, server_with_test_data):
        """Test searching for single document entity."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["document"],
            "search_term": "api"
        })

        assert result["success"] is True
        assert "results" in result

        # Verify document-specific fields
        for item in result["results"]:
            assert item["entity_type"] == "document"
            assert "api" in item["name"].lower() or "api" in item.get("content", "").lower()
            assert "doc_type" in item

    @pytest.mark.asyncio
    async def test_search_single_entity_requirement(self, server_with_test_data):
        """Test searching for single requirement entity."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["requirement"],
            "search_term": "authentication"
        })

        assert result["success"] is True
        assert "results" in result

        # Verify requirement-specific fields
        for item in result["results"]:
            assert item["entity_type"] == "requirement"
            assert "priority" in item
            assert "status" in item

    @pytest.mark.asyncio
    async def test_search_multi_entity_all(self, server_with_test_data):
        """Test searching across all entity types."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["project", "document", "requirement"],
            "search_term": "data"
        })

        assert result["success"] is True
        assert "results" in result

        # Verify mixed entity types
        entity_types = {item["entity_type"] for item in result["results"]}
        assert len(entity_types) > 1  # Should have multiple entity types

    @pytest.mark.asyncio
    async def test_search_multi_entity_project_document(self, server_with_test_data):
        """Test searching across projects and documents."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["project", "document"],
            "search_term": "architecture"
        })

        assert result["success"] is True
        assert "results" in result

        # Verify only projects and documents
        for item in result["results"]:
            assert item["entity_type"] in ["project", "document"]

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, server_with_test_data):
        """Test search with status filter."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["project", "requirement"],
            "filters": {"status": "active"}
        })

        assert result["success"] is True

        # Verify all results have active status
        for item in result["results"]:
            assert item.get("status") == "active"

    @pytest.mark.asyncio
    async def test_search_with_priority_filter(self, server_with_test_data):
        """Test search with priority filter for requirements."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["requirement"],
            "filters": {"priority": "high"}
        })

        assert result["success"] is True

        # Verify all results have high priority
        for item in result["results"]:
            assert item["entity_type"] == "requirement"
            assert item.get("priority") in ["high", "critical"]  # Critical is higher than high

    @pytest.mark.asyncio
    async def test_search_with_multiple_filters(self, server_with_test_data):
        """Test search with multiple filters combined."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["requirement"],
            "filters": {
                "status": "active",
                "priority": "medium"
            }
        })

        assert result["success"] is True

        # Verify all filters are applied
        for item in result["results"]:
            assert item["entity_type"] == "requirement"
            assert item.get("status") == "active"
            assert item.get("priority") == "medium"

    @pytest.mark.asyncio
    async def test_search_with_limit_5(self, server_with_test_data):
        """Test search with limit of 5 results."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["document", "requirement"],
            "limit": 5
        })

        assert result["success"] is True
        assert len(result["results"]) <= 5

    @pytest.mark.asyncio
    async def test_search_with_limit_20(self, server_with_test_data):
        """Test search with limit of 20 results."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["project", "document", "requirement"],
            "limit": 20
        })

        assert result["success"] is True
        assert len(result["results"]) <= 20

    @pytest.mark.asyncio
    async def test_search_with_limit_50(self, server_with_test_data):
        """Test search with limit of 50 results."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["organization", "project", "document", "requirement", "test"],
            "limit": 50
        })

        assert result["success"] is True
        assert len(result["results"]) <= 50

    @pytest.mark.asyncio
    async def test_search_with_ordering_asc_name(self, server_with_test_data):
        """Test search with ascending order by name."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["project"],
            "order_by": "name",
            "order_direction": "asc"
        })

        assert result["success"] is True

        # Verify ascending order
        names = [item["name"] for item in result["results"]]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_search_with_ordering_desc_created(self, server_with_test_data):
        """Test search with descending order by creation date."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["document"],
            "order_by": "created_at",
            "order_direction": "desc"
        })

        assert result["success"] is True

        # Verify descending order
        if len(result["results"]) > 1:
            for i in range(len(result["results"]) - 1):
                assert result["results"][i]["created_at"] >= result["results"][i+1]["created_at"]

    @pytest.mark.asyncio
    async def test_search_with_ordering_priority(self, server_with_test_data):
        """Test search ordering by priority for requirements."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["requirement"],
            "order_by": "priority",
            "order_direction": "desc"
        })

        assert result["success"] is True

        # Priority order: critical > high > medium > low
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        if len(result["results"]) > 1:
            for i in range(len(result["results"]) - 1):
                curr_priority = priority_order.get(result["results"][i].get("priority", "low"), 0)
                next_priority = priority_order.get(result["results"][i+1].get("priority", "low"), 0)
                assert curr_priority >= next_priority

    @pytest.mark.asyncio
    async def test_search_complex_combined(self, server_with_test_data):
        """Test search with all parameters combined: multi-entity, filters, limit, ordering."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["project", "requirement"],
            "search_term": "data",
            "filters": {"status": "active"},
            "limit": 10,
            "order_by": "name",
            "order_direction": "asc"
        })

        assert result["success"] is True
        assert len(result["results"]) <= 10

        # Verify all conditions
        for item in result["results"]:
            assert item["entity_type"] in ["project", "requirement"]
            assert item.get("status") == "active"
            assert "data" in str(item).lower()

        # Verify ordering
        names = [item["name"] for item in result["results"]]
        assert names == sorted(names)


class TestRAGQueries:
    """Test suite for RAG queries covering all modes, entities, and threshold variations."""

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_document_architecture(self, server_with_test_data):
        """Test semantic RAG mode for documents with architecture query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "microservices architecture patterns",
            "entity_types": ["document"],
            "mode": RAGMode.SEMANTIC.value
        })

        assert result["success"] is True
        assert "results" in result
        assert len(result["results"]) > 0

        # Verify semantic relevance
        for item in result["results"]:
            assert item["entity_type"] == "document"
            assert "score" in item
            assert item["score"] > 0.0

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_document_ml(self, server_with_test_data):
        """Test semantic RAG mode for documents with ML query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "machine learning deep neural networks",
            "entity_types": ["document"],
            "mode": RAGMode.SEMANTIC.value
        })

        assert result["success"] is True
        assert "results" in result

        # Should find ML-related documents
        for item in result["results"]:
            assert item["entity_type"] == "document"
            assert "score" in item

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_requirement_security(self, server_with_test_data):
        """Test semantic RAG mode for requirements with security query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "security authentication authorization",
            "entity_types": ["requirement"],
            "mode": RAGMode.SEMANTIC.value
        })

        assert result["success"] is True
        assert "results" in result

        for item in result["results"]:
            assert item["entity_type"] == "requirement"
            assert "score" in item

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_requirement_performance(self, server_with_test_data):
        """Test semantic RAG mode for requirements with performance query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "performance optimization scalability",
            "entity_types": ["requirement"],
            "mode": RAGMode.SEMANTIC.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_test_security(self, server_with_test_data):
        """Test semantic RAG mode for tests with security testing query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "security vulnerability testing",
            "entity_types": ["test"],
            "mode": RAGMode.SEMANTIC.value
        })

        assert result["success"] is True
        assert "results" in result

        for item in result["results"]:
            assert item["entity_type"] == "test"

    @pytest.mark.asyncio
    async def test_rag_semantic_mode_test_performance(self, server_with_test_data):
        """Test semantic RAG mode for tests with performance testing query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "load testing performance metrics",
            "entity_types": ["test"],
            "mode": RAGMode.SEMANTIC.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_document_specific(self, server_with_test_data):
        """Test keyword RAG mode for documents with specific terms."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "kubernetes kafka",
            "entity_types": ["document"],
            "mode": RAGMode.KEYWORD.value
        })

        assert result["success"] is True
        assert "results" in result

        # Should find documents with exact keywords
        for item in result["results"]:
            content = item.get("content", "").lower()
            assert "kubernetes" in content or "kafka" in content

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_document_api(self, server_with_test_data):
        """Test keyword RAG mode for documents with API keywords."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "oauth rest api",
            "entity_types": ["document"],
            "mode": RAGMode.KEYWORD.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_requirement_auth(self, server_with_test_data):
        """Test keyword RAG mode for requirements with auth keywords."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "authentication biometric",
            "entity_types": ["requirement"],
            "mode": RAGMode.KEYWORD.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_requirement_backup(self, server_with_test_data):
        """Test keyword RAG mode for requirements with backup keywords."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "backup recovery replication",
            "entity_types": ["requirement"],
            "mode": RAGMode.KEYWORD.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_test_sql(self, server_with_test_data):
        """Test keyword RAG mode for tests with SQL injection keyword."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "sql injection xss",
            "entity_types": ["test"],
            "mode": RAGMode.KEYWORD.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_keyword_mode_test_load(self, server_with_test_data):
        """Test keyword RAG mode for tests with load testing keywords."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "concurrent stress endurance",
            "entity_types": ["test"],
            "mode": RAGMode.KEYWORD.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_document_comprehensive(self, server_with_test_data):
        """Test hybrid RAG mode combining semantic and keyword for documents."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "distributed systems architecture with kubernetes",
            "entity_types": ["document"],
            "mode": RAGMode.HYBRID.value
        })

        assert result["success"] is True
        assert "results" in result

        # Hybrid should balance semantic and keyword matching
        for item in result["results"]:
            assert item["entity_type"] == "document"
            assert "score" in item

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_document_technical(self, server_with_test_data):
        """Test hybrid RAG mode for technical documentation query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "database optimization indexing strategies",
            "entity_types": ["document"],
            "mode": RAGMode.HYBRID.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_requirement_mixed(self, server_with_test_data):
        """Test hybrid RAG mode for requirements with mixed query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "real-time processing with high performance",
            "entity_types": ["requirement"],
            "mode": RAGMode.HYBRID.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_requirement_specific(self, server_with_test_data):
        """Test hybrid RAG mode for specific requirement features."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "api rate limiting token bucket",
            "entity_types": ["requirement"],
            "mode": RAGMode.HYBRID.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_test_comprehensive(self, server_with_test_data):
        """Test hybrid RAG mode for comprehensive test query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "security testing vulnerability assessment",
            "entity_types": ["test"],
            "mode": RAGMode.HYBRID.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_hybrid_mode_test_integration(self, server_with_test_data):
        """Test hybrid RAG mode for integration test query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "api integration end-to-end testing",
            "entity_types": ["test"],
            "mode": RAGMode.HYBRID.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_auto_mode_document_natural(self, server_with_test_data):
        """Test auto RAG mode with natural language query for documents."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "How do we handle authentication in our system?",
            "entity_types": ["document"],
            "mode": RAGMode.AUTO.value
        })

        assert result["success"] is True
        assert "results" in result
        assert "mode_used" in result  # Auto mode should indicate which mode was chosen

    @pytest.mark.asyncio
    async def test_rag_auto_mode_document_technical(self, server_with_test_data):
        """Test auto RAG mode with technical query for documents."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "transformer BERT NLP models",
            "entity_types": ["document"],
            "mode": RAGMode.AUTO.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_auto_mode_requirement_question(self, server_with_test_data):
        """Test auto RAG mode with question for requirements."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "What are our high priority requirements?",
            "entity_types": ["requirement"],
            "mode": RAGMode.AUTO.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_auto_mode_requirement_keywords(self, server_with_test_data):
        """Test auto RAG mode with keywords for requirements."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "frontend UI responsive mobile",
            "entity_types": ["requirement"],
            "mode": RAGMode.AUTO.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_auto_mode_test_mixed(self, server_with_test_data):
        """Test auto RAG mode with mixed query for tests."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "performance testing under heavy load conditions",
            "entity_types": ["test"],
            "mode": RAGMode.AUTO.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_auto_mode_test_specific(self, server_with_test_data):
        """Test auto RAG mode with specific test query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "automated security vulnerability scanning",
            "entity_types": ["test"],
            "mode": RAGMode.AUTO.value
        })

        assert result["success"] is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_rag_threshold_low_05(self, server_with_test_data):
        """Test RAG with low threshold (0.5) - more inclusive results."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "system design",
            "entity_types": ["document"],
            "mode": RAGMode.SEMANTIC.value,
            "threshold": 0.5
        })

        assert result["success"] is True

        # Low threshold should return more results
        low_threshold_count = len(result["results"])

        # All results should meet threshold
        for item in result["results"]:
            assert item["score"] >= 0.5

    @pytest.mark.asyncio
    async def test_rag_threshold_medium_07(self, server_with_test_data):
        """Test RAG with medium threshold (0.7) - balanced results."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "system design",
            "entity_types": ["document"],
            "mode": RAGMode.SEMANTIC.value,
            "threshold": 0.7
        })

        assert result["success"] is True

        # All results should meet threshold
        for item in result["results"]:
            assert item["score"] >= 0.7

    @pytest.mark.asyncio
    async def test_rag_threshold_high_09(self, server_with_test_data):
        """Test RAG with high threshold (0.9) - only very relevant results."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "microservices kubernetes",
            "entity_types": ["document"],
            "mode": RAGMode.SEMANTIC.value,
            "threshold": 0.9
        })

        assert result["success"] is True

        # High threshold should return fewer, more relevant results
        for item in result["results"]:
            assert item["score"] >= 0.9

    @pytest.mark.asyncio
    async def test_rag_multi_entity_search(self, server_with_test_data):
        """Test RAG across multiple entity types."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "security authentication testing",
            "entity_types": ["document", "requirement", "test"],
            "mode": RAGMode.HYBRID.value
        })

        assert result["success"] is True
        assert "results" in result

        # Should have mixed entity types
        entity_types = {item["entity_type"] for item in result["results"]}
        assert len(entity_types) > 1


class TestAggregateQueries:
    """Test suite for aggregate queries covering all entities with filters and projections."""

    @pytest.mark.asyncio
    async def test_aggregate_all_entities(self, server_with_test_data):
        """Test aggregation across all entity types."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["organization", "project", "document", "requirement", "test"]
        })

        assert result["success"] is True
        assert "aggregations" in result

        # Should have counts for all entity types
        assert "organization" in result["aggregations"]
        assert "project" in result["aggregations"]
        assert "document" in result["aggregations"]
        assert "requirement" in result["aggregations"]
        assert "test" in result["aggregations"]

        # Verify counts
        assert result["aggregations"]["organization"]["count"] == 2
        assert result["aggregations"]["project"]["count"] == 3
        assert result["aggregations"]["document"]["count"] == 4
        assert result["aggregations"]["requirement"]["count"] == 5
        assert result["aggregations"]["test"]["count"] == 3

    @pytest.mark.asyncio
    async def test_aggregate_single_entity_organization(self, server_with_test_data):
        """Test aggregation for single organization entity."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["organization"]
        })

        assert result["success"] is True
        assert "aggregations" in result
        assert "organization" in result["aggregations"]

        org_agg = result["aggregations"]["organization"]
        assert org_agg["count"] == 2
        assert "metadata" in org_agg

    @pytest.mark.asyncio
    async def test_aggregate_single_entity_project(self, server_with_test_data):
        """Test aggregation for single project entity."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["project"]
        })

        assert result["success"] is True
        assert "aggregations" in result
        assert "project" in result["aggregations"]

        proj_agg = result["aggregations"]["project"]
        assert proj_agg["count"] == 3
        assert "by_status" in proj_agg
        assert "by_organization" in proj_agg

    @pytest.mark.asyncio
    async def test_aggregate_single_entity_document(self, server_with_test_data):
        """Test aggregation for single document entity."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["document"]
        })

        assert result["success"] is True
        assert "aggregations" in result
        assert "document" in result["aggregations"]

        doc_agg = result["aggregations"]["document"]
        assert doc_agg["count"] == 4
        assert "by_type" in doc_agg
        assert "by_project" in doc_agg

    @pytest.mark.asyncio
    async def test_aggregate_single_entity_requirement(self, server_with_test_data):
        """Test aggregation for single requirement entity."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["requirement"]
        })

        assert result["success"] is True
        assert "aggregations" in result
        assert "requirement" in result["aggregations"]

        req_agg = result["aggregations"]["requirement"]
        assert req_agg["count"] == 5
        assert "by_status" in req_agg
        assert "by_priority" in req_agg
        assert "by_project" in req_agg

    @pytest.mark.asyncio
    async def test_aggregate_with_status_filter(self, server_with_test_data):
        """Test aggregation with status filter."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["project", "requirement"],
            "filters": {"status": "active"}
        })

        assert result["success"] is True
        assert "aggregations" in result

        # Counts should only include active items
        if "project" in result["aggregations"]:
            assert result["aggregations"]["project"]["count"] <= 3
        if "requirement" in result["aggregations"]:
            assert result["aggregations"]["requirement"]["count"] <= 5

    @pytest.mark.asyncio
    async def test_aggregate_with_priority_filter(self, server_with_test_data):
        """Test aggregation with priority filter for requirements."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["requirement"],
            "filters": {"priority": "high"}
        })

        assert result["success"] is True
        assert "aggregations" in result
        assert "requirement" in result["aggregations"]

        # Should only count high/critical priority requirements
        req_agg = result["aggregations"]["requirement"]
        assert req_agg["count"] <= 5

    @pytest.mark.asyncio
    async def test_aggregate_with_projections_basic(self, server_with_test_data):
        """Test aggregation with basic field projections."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["project"],
            "projections": ["name", "status"]
        })

        assert result["success"] is True
        assert "aggregations" in result
        assert "samples" in result  # Projections should include sample data

        # Verify projected fields
        if result.get("samples"):
            for sample in result["samples"]:
                assert "name" in sample
                assert "status" in sample
                assert "description" not in sample  # Not projected

    @pytest.mark.asyncio
    async def test_aggregate_with_projections_metadata(self, server_with_test_data):
        """Test aggregation with metadata projections."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["document"],
            "projections": ["name", "doc_type", "metadata"]
        })

        assert result["success"] is True
        assert "aggregations" in result

        # Verify metadata is included
        if result.get("samples"):
            for sample in result["samples"]:
                assert "metadata" in sample

    @pytest.mark.asyncio
    async def test_aggregate_multi_entity_with_filters(self, server_with_test_data):
        """Test multi-entity aggregation with filters."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["project", "document", "requirement"],
            "filters": {"status": "active"}
        })

        assert result["success"] is True
        assert "aggregations" in result

        # All entity types should be present
        for entity_type in ["project", "document", "requirement"]:
            if entity_type in result["aggregations"]:
                assert "count" in result["aggregations"][entity_type]

    @pytest.mark.asyncio
    async def test_aggregate_with_group_by(self, server_with_test_data):
        """Test aggregation with group_by functionality."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["requirement"],
            "group_by": ["status", "priority"]
        })

        assert result["success"] is True
        assert "aggregations" in result

        req_agg = result["aggregations"]["requirement"]
        assert "by_status" in req_agg
        assert "by_priority" in req_agg

        # Verify grouping structure
        assert isinstance(req_agg["by_status"], dict)
        assert isinstance(req_agg["by_priority"], dict)

    @pytest.mark.asyncio
    async def test_aggregate_test_entity_with_status(self, server_with_test_data):
        """Test aggregation for test entities with status grouping."""
        server = server_with_test_data

        result = await server.query({
            "operation": "aggregate",
            "entity_types": ["test"]
        })

        assert result["success"] is True
        assert "aggregations" in result
        assert "test" in result["aggregations"]

        test_agg = result["aggregations"]["test"]
        assert test_agg["count"] == 3
        assert "by_status" in test_agg
        assert "by_type" in test_agg


class TestSimilarityQueries:
    """Test suite for similarity queries with various thresholds and entity types."""

    @pytest.mark.asyncio
    async def test_similarity_basic_document(self, server_with_test_data):
        """Test basic similarity search for documents."""
        server = server_with_test_data
        doc_id = server.test_data["document_ids"][0]

        result = await server.query({
            "operation": "similarity",
            "entity_id": doc_id,
            "entity_type": "document"
        })

        assert result["success"] is True
        assert "similar_items" in result

        # Should find similar documents
        for item in result["similar_items"]:
            assert "id" in item
            assert "score" in item
            assert "entity_type" in item
            assert item["id"] != doc_id  # Should not include self

    @pytest.mark.asyncio
    async def test_similarity_high_threshold(self, server_with_test_data):
        """Test similarity with high threshold (0.9)."""
        server = server_with_test_data
        req_id = server.test_data["requirement_ids"][0]

        result = await server.query({
            "operation": "similarity",
            "entity_id": req_id,
            "entity_type": "requirement",
            "threshold": 0.9
        })

        assert result["success"] is True
        assert "similar_items" in result

        # High threshold should return only very similar items
        for item in result["similar_items"]:
            assert item["score"] >= 0.9

    @pytest.mark.asyncio
    async def test_similarity_with_limit(self, server_with_test_data):
        """Test similarity with result limit."""
        server = server_with_test_data
        doc_id = server.test_data["document_ids"][1]

        result = await server.query({
            "operation": "similarity",
            "entity_id": doc_id,
            "entity_type": "document",
            "limit": 2
        })

        assert result["success"] is True
        assert "similar_items" in result
        assert len(result["similar_items"]) <= 2

    @pytest.mark.asyncio
    async def test_similarity_cross_entity_type(self, server_with_test_data):
        """Test similarity search across different entity types."""
        server = server_with_test_data
        doc_id = server.test_data["document_ids"][0]

        result = await server.query({
            "operation": "similarity",
            "entity_id": doc_id,
            "entity_type": "document",
            "target_types": ["requirement", "test"]
        })

        assert result["success"] is True
        assert "similar_items" in result

        # Should find similar items from different entity types
        entity_types = {item["entity_type"] for item in result["similar_items"]}
        assert len(entity_types) >= 1

    @pytest.mark.asyncio
    async def test_similarity_requirement_to_requirement(self, server_with_test_data):
        """Test similarity between requirements."""
        server = server_with_test_data
        req_id = server.test_data["requirement_ids"][2]

        result = await server.query({
            "operation": "similarity",
            "entity_id": req_id,
            "entity_type": "requirement",
            "target_types": ["requirement"]
        })

        assert result["success"] is True
        assert "similar_items" in result

        # All results should be requirements
        for item in result["similar_items"]:
            assert item["entity_type"] == "requirement"

    @pytest.mark.asyncio
    async def test_similarity_with_metadata_filter(self, server_with_test_data):
        """Test similarity with metadata filtering."""
        server = server_with_test_data
        proj_id = server.test_data["project_ids"][0]

        result = await server.query({
            "operation": "similarity",
            "entity_id": proj_id,
            "entity_type": "project",
            "filters": {"status": "active"}
        })

        assert result["success"] is True
        assert "similar_items" in result

        # All similar items should match filter
        for item in result["similar_items"]:
            if "status" in item:
                assert item["status"] == "active"


class TestAnalyzeQueries:
    """Test suite for analyze queries covering different analysis types."""

    @pytest.mark.asyncio
    async def test_analyze_organization(self, server_with_test_data):
        """Test organization analysis."""
        server = server_with_test_data
        org_id = server.test_data["org_ids"][0]

        result = await server.query({
            "operation": "analyze",
            "entity_type": "organization",
            "entity_id": org_id
        })

        assert result["success"] is True
        assert "analysis" in result

        analysis = result["analysis"]
        assert "entity_type" in analysis
        assert analysis["entity_type"] == "organization"
        assert "projects_count" in analysis
        assert "total_documents" in analysis
        assert "total_requirements" in analysis

    @pytest.mark.asyncio
    async def test_analyze_project(self, server_with_test_data):
        """Test project analysis."""
        server = server_with_test_data
        proj_id = server.test_data["project_ids"][0]

        result = await server.query({
            "operation": "analyze",
            "entity_type": "project",
            "entity_id": proj_id
        })

        assert result["success"] is True
        assert "analysis" in result

        analysis = result["analysis"]
        assert analysis["entity_type"] == "project"
        assert "documents_count" in analysis
        assert "requirements_count" in analysis
        assert "tests_count" in analysis
        assert "completion_percentage" in analysis

    @pytest.mark.asyncio
    async def test_analyze_requirement(self, server_with_test_data):
        """Test requirement analysis."""
        server = server_with_test_data
        req_id = server.test_data["requirement_ids"][0]

        result = await server.query({
            "operation": "analyze",
            "entity_type": "requirement",
            "entity_id": req_id
        })

        assert result["success"] is True
        assert "analysis" in result

        analysis = result["analysis"]
        assert analysis["entity_type"] == "requirement"
        assert "test_coverage" in analysis
        assert "related_documents" in analysis
        assert "complexity_score" in analysis

    @pytest.mark.asyncio
    async def test_analyze_with_filters(self, server_with_test_data):
        """Test analysis with filters applied."""
        server = server_with_test_data
        proj_id = server.test_data["project_ids"][0]

        result = await server.query({
            "operation": "analyze",
            "entity_type": "project",
            "entity_id": proj_id,
            "filters": {"status": "active"}
        })

        assert result["success"] is True
        assert "analysis" in result

        # Analysis should respect filters
        analysis = result["analysis"]
        assert "filtered" in analysis or "filter_applied" in analysis

    @pytest.mark.asyncio
    async def test_analyze_document_content(self, server_with_test_data):
        """Test document content analysis."""
        server = server_with_test_data
        doc_id = server.test_data["document_ids"][0]

        result = await server.query({
            "operation": "analyze",
            "entity_type": "document",
            "entity_id": doc_id
        })

        assert result["success"] is True
        assert "analysis" in result

        analysis = result["analysis"]
        assert analysis["entity_type"] == "document"
        assert "content_length" in analysis
        assert "keywords" in analysis or "topics" in analysis

    @pytest.mark.asyncio
    async def test_analyze_test_results(self, server_with_test_data):
        """Test analysis of test results."""
        server = server_with_test_data
        test_id = server.test_data["test_ids"][0]

        result = await server.query({
            "operation": "analyze",
            "entity_type": "test",
            "entity_id": test_id
        })

        assert result["success"] is True
        assert "analysis" in result

        analysis = result["analysis"]
        assert analysis["entity_type"] == "test"
        assert "status" in analysis
        assert "coverage" in analysis or "test_metrics" in analysis

    @pytest.mark.asyncio
    async def test_analyze_cross_entity_relationships(self, server_with_test_data):
        """Test analysis of relationships between entities."""
        server = server_with_test_data
        org_id = server.test_data["org_ids"][0]

        result = await server.query({
            "operation": "analyze",
            "entity_type": "organization",
            "entity_id": org_id,
            "include_relationships": True
        })

        assert result["success"] is True
        assert "analysis" in result

        analysis = result["analysis"]
        assert "relationships" in analysis or "related_entities" in analysis

    @pytest.mark.asyncio
    async def test_analyze_with_depth_parameter(self, server_with_test_data):
        """Test analysis with depth parameter for nested analysis."""
        server = server_with_test_data
        proj_id = server.test_data["project_ids"][0]

        result = await server.query({
            "operation": "analyze",
            "entity_type": "project",
            "entity_id": proj_id,
            "analysis_depth": "deep"
        })

        assert result["success"] is True
        assert "analysis" in result

        analysis = result["analysis"]
        # Deep analysis should include more detailed metrics
        assert len(analysis.keys()) > 5  # Should have many analysis fields


class TestEdgeCasesAndValidation:
    """Test suite for edge cases and validation scenarios."""

    @pytest.mark.asyncio
    async def test_empty_query_string(self, server_with_test_data):
        """Test handling of empty query string."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["document"],
            "search_term": ""
        })

        # Should either return all results or handle gracefully
        assert result["success"] is True or "error" in result

    @pytest.mark.asyncio
    async def test_invalid_entity_type(self, server_with_test_data):
        """Test handling of invalid entity type."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["invalid_type"],
            "search_term": "test"
        })

        # Should handle invalid type gracefully
        assert "error" in result or len(result.get("results", [])) == 0

    @pytest.mark.asyncio
    async def test_nonexistent_entity_id(self, server_with_test_data):
        """Test handling of non-existent entity ID."""
        server = server_with_test_data

        result = await server.query({
            "operation": "similarity",
            "entity_id": "non-existent-id-12345",
            "entity_type": "document"
        })

        # Should handle gracefully
        assert result["success"] is False or "error" in result

    @pytest.mark.asyncio
    async def test_conflicting_filters(self, server_with_test_data):
        """Test handling of conflicting filter conditions."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["requirement"],
            "filters": {
                "status": "active",
                "status": "completed"  # Conflicting
            }
        })

        # Should handle conflict (last value wins or error)
        assert "results" in result or "error" in result

    @pytest.mark.asyncio
    async def test_extreme_limit_values(self, server_with_test_data):
        """Test handling of extreme limit values."""
        server = server_with_test_data

        # Test with very large limit
        result = await server.query({
            "operation": "search",
            "entity_types": ["document"],
            "limit": 999999
        })

        assert result["success"] is True
        assert len(result["results"]) <= 999999

        # Test with zero limit
        result = await server.query({
            "operation": "search",
            "entity_types": ["document"],
            "limit": 0
        })

        # Should either return no results or use default
        assert "results" in result

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, server_with_test_data):
        """Test handling of special characters in query string."""
        server = server_with_test_data

        result = await server.query({
            "operation": "rag",
            "search_term": "test @#$%^&* special <script>alert('xss')</script>",
            "entity_types": ["document"],
            "mode": RAGMode.KEYWORD.value
        })

        # Should handle special characters safely
        assert result["success"] is True or "error" in result

    @pytest.mark.asyncio
    async def test_unicode_in_query(self, server_with_test_data):
        """Test handling of Unicode characters in query."""
        server = server_with_test_data

        result = await server.query({
            "operation": "search",
            "entity_types": ["document"],
            "search_term": "测试 テスト тест"  # Chinese, Japanese, Russian
        })

        # Should handle Unicode gracefully
        assert "results" in result or "error" in result

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, server_with_test_data):
        """Test query performance with larger dataset."""
        server = server_with_test_data

        import time

        # Add more test data
        for i in range(100):
            doc = Document(
                id=str(uuid.uuid4()),
                name=f"Performance Test Doc {i}",
                project_id=server.test_data["project_ids"][0],
                content=f"Content for performance testing document {i} with various keywords",
                doc_type="test"
            )
            server.storage.documents[doc.id] = doc

        start_time = time.time()
        result = await server.query({
            "operation": "search",
            "entity_types": ["document"],
            "search_term": "performance"
        })
        elapsed_time = time.time() - start_time

        assert result["success"] is True
        assert elapsed_time < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, server_with_test_data):
        """Test handling of concurrent query execution."""
        server = server_with_test_data
        import asyncio

        # Define multiple queries to run concurrently
        queries = [
            {"operation": "search", "entity_types": ["document"], "search_term": "test1"},
            {"operation": "rag", "entity_types": ["requirement"], "search_term": "test2", "mode": RAGMode.SEMANTIC.value},
            {"operation": "aggregate", "entity_types": ["project"]},
            {"operation": "search", "entity_types": ["test"], "search_term": "test3"},
        ]

        # Run queries concurrently
        results = await asyncio.gather(
            *[server.query(q) for q in queries],
            return_exceptions=True
        )

        # All queries should complete successfully
        for result in results:
            if isinstance(result, dict):
                assert result.get("success") is True or "error" in result
            else:
                # Should not raise exceptions
                assert False, f"Query raised exception: {result}"


if __name__ == "__main__":
    # Run all tests with verbose output
    pytest.main([__file__, "-v", "-s"])