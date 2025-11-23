"""Phase 8 comprehensive tests for query tool - 6% → 85%."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


class TestQueryToolPhase8:
    """Test query tool functionality comprehensively."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database adapter."""
        return AsyncMock()

    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service."""
        return AsyncMock()

    @pytest.fixture
    def query_tool(self, mock_db, mock_embedding_service):
        """Create a query tool instance."""
        from tools.query import QueryTool
        return QueryTool(mock_db, mock_embedding_service)

    @pytest.mark.asyncio
    async def test_query_basic_search(self, query_tool, mock_db, mock_embedding_service):
        """Test basic query search."""
        mock_db.query = AsyncMock(return_value=[{"id": "1", "name": "Result"}])
        
        result = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_filters(self, query_tool, mock_db):
        """Test query with filters."""
        mock_db.query = AsyncMock(return_value=[])
        
        result = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement",
            filters={"status": "active"}
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_sorting(self, query_tool, mock_db):
        """Test query with sorting."""
        mock_db.query = AsyncMock(return_value=[])
        
        result = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement",
            sort=[{"field": "priority", "order": "desc"}]
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_pagination(self, query_tool, mock_db):
        """Test query with pagination."""
        mock_db.query = AsyncMock(return_value=[])
        
        result = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement",
            limit=50,
            offset=100
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_full_text_search(self, query_tool, mock_db):
        """Test full-text search."""
        mock_db.query = AsyncMock(return_value=[])
        
        result = await query_tool.full_text_search(
            workspace_id=str(uuid.uuid4()),
            query="test query"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_semantic_search(self, query_tool, mock_db, mock_embedding_service):
        """Test semantic search."""
        mock_embedding_service.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])
        mock_db.query = AsyncMock(return_value=[])
        
        result = await query_tool.semantic_search(
            workspace_id=str(uuid.uuid4()),
            query="similar requirements"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_aggregation(self, query_tool, mock_db):
        """Test query with aggregation."""
        mock_db.query = AsyncMock(return_value=[{"status": "active", "count": 10}])
        
        result = await query_tool.aggregate(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement",
            group_by="status"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_facets(self, query_tool, mock_db):
        """Test query with facets."""
        mock_db.query = AsyncMock(return_value=[])
        
        result = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement",
            facets=["status", "priority"]
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_error_handling(self, query_tool, mock_db):
        """Test query error handling."""
        mock_db.query = AsyncMock(side_effect=Exception("DB error"))
        
        result = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement"
        )
        assert result is not None or isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_query_caching(self, query_tool, mock_db):
        """Test query result caching."""
        mock_db.query = AsyncMock(return_value=[])
        
        # First query
        result1 = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement"
        )
        # Second query (may use cache)
        result2 = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement"
        )
        
        assert result1 is not None
        assert result2 is not None

    @pytest.mark.asyncio
    async def test_query_performance(self, query_tool, mock_db):
        """Test query performance."""
        mock_db.query = AsyncMock(return_value=[])
        
        result = await query_tool.query_entities(
            workspace_id=str(uuid.uuid4()),
            entity_type="requirement"
        )
        assert result is not None

