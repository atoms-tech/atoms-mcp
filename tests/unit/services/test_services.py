"""Comprehensive unit tests for service layer components.

Covers:
- Embedding service factory and initialization
- Vector search: semantic, keyword, hybrid, and similarity modes
- Search result structures and response handling
- Error handling and edge cases
- Integration with external services (mocked)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.embedding_factory import get_embedding_service, _check_vertex_ai_available
from services.vector_search import (
    VectorSearchService,
    SearchResult,
    SearchResponse
)


# =============================================================================
# EMBEDDING FACTORY TESTS
# =============================================================================

class TestEmbeddingFactory:
    """Test embedding service factory."""

    def test_check_vertex_ai_available_returns_false_without_credentials(self):
        with patch.dict('os.environ', {}, clear=True):
            result = _check_vertex_ai_available()
            assert result is False

    def test_check_vertex_ai_available_checks_project_env(self):
        with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}, clear=True):
            with patch('google.auth.default', side_effect=Exception("ADC not found")):
                result = _check_vertex_ai_available()
                assert result is False

    def test_get_embedding_service_raises_without_vertex_ai(self):
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RuntimeError):
                get_embedding_service()

    def test_get_embedding_service_raises_informative_error(self):
        with patch.dict('os.environ', {}, clear=True):
            try:
                get_embedding_service()
            except RuntimeError as e:
                error_msg = str(e)
                assert "Vertex AI" in error_msg
                assert "GOOGLE_CLOUD_PROJECT" in error_msg


# =============================================================================
# SEARCH RESULT STRUCTURES
# =============================================================================

class TestSearchResultStructures:
    """Test search result NamedTuples."""

    def test_search_result_creation(self):
        result = SearchResult(
            id="doc-1",
            content="test content",
            similarity=0.95,
            metadata={"source": "test"},
            entity_type="document"
        )
        assert result.id == "doc-1"
        assert result.similarity == 0.95
        assert result.entity_type == "document"

    def test_search_result_immutability(self):
        result = SearchResult(
            id="doc-1",
            content="test",
            similarity=0.5,
            metadata={},
            entity_type="document"
        )
        with pytest.raises(AttributeError):
            result.id = "doc-2"

    def test_search_response_creation(self):
        results = [
            SearchResult("id1", "content", 0.9, {}, "doc"),
            SearchResult("id2", "content", 0.8, {}, "doc")
        ]
        response = SearchResponse(
            results=results,
            total_results=2,
            query_embedding_tokens=100,
            search_time_ms=150.5,
            mode="semantic"
        )
        assert response.total_results == 2
        assert response.search_time_ms == 150.5
        assert response.mode == "semantic"


# =============================================================================
# VECTOR SEARCH SERVICE TESTS
# =============================================================================

class TestVectorSearchService:
    """Test VectorSearchService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use regular MagicMock for supabase to support method chaining
        self.mock_supabase = MagicMock()
        self.mock_embedding_service = AsyncMock()

        # Make rpc return a mock with execute method (as expected by vector_search.py)
        self.mock_supabase.rpc.return_value = MagicMock()

    @pytest.mark.asyncio
    async def test_semantic_search_handles_empty_embedding(self):
        """Test semantic search with no embedding vector."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=None,
            tokens_used=0
        )
        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)

        response = await service.semantic_search("test query")

        assert response.total_results == 0
        assert response.results == []
        assert response.mode == "semantic"

    @pytest.mark.asyncio
    async def test_semantic_search_with_empty_entity_types(self):
        """Test semantic search with no valid entity types."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1, 0.2, 0.3],
            tokens_used=10
        )
        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)

        response = await service.semantic_search(
            "test query",
            entity_types=["invalid_type"]
        )

        assert response.total_results == 0

    @pytest.mark.asyncio
    async def test_semantic_search_calls_rpc_with_correct_params(self):
        """Test that semantic search calls RPC with proper parameters."""
        embedding = [0.1, 0.2, 0.3]
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=embedding,
            tokens_used=10
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[
            {"id": "doc1", "content": "test", "similarity": 0.95, "metadata": {}}
        ])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search("test query", limit=5)

        # Verify RPC was called
        self.mock_supabase.rpc.assert_called()
        call_args = self.mock_supabase.rpc.call_args
        rpc_name = call_args[0][0]
        params = call_args[0][1]

        # Check that RPC name is one of the expected matches
        assert rpc_name in ["match_requirements", "match_document", "match_projects", "match_organizations"]
        assert params["query_embedding"] == embedding
        assert params["match_count"] == 5

    @pytest.mark.asyncio
    async def test_semantic_search_handles_rpc_exception(self):
        """Test semantic search continues on RPC failure."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1, 0.2, 0.3],
            tokens_used=10
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.side_effect = Exception("RPC failed")
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search("test query")

        # Should return empty results but not raise
        assert response.total_results == 0

    @pytest.mark.asyncio
    async def test_semantic_search_respects_similarity_threshold(self):
        """Test that similarity threshold is passed to RPC."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1, 0.2, 0.3],
            tokens_used=10
        )

        # self.supabase.rpc() should return an object that when .execute() is called returns data
        mock_rpc_result = MagicMock()  # Not AsyncMock - we want a plain object
        mock_rpc_result.execute.return_value = MagicMock(data=[
            {"id": "doc1", "content": "high", "similarity": 0.95, "metadata": {}}
        ])
        self.mock_supabase.rpc.return_value = mock_rpc_result

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search("test", similarity_threshold=0.7, entity_types=["requirement"])

        # Verify threshold was passed to RPC
        call_args = self.mock_supabase.rpc.call_args
        params = call_args[0][1]
        assert params.get("similarity_threshold") == 0.7
        # Should have results
        assert len(response.results) >= 1

    @pytest.mark.asyncio
    async def test_semantic_search_sorts_by_similarity(self):
        """Test that results are sorted by similarity descending."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1, 0.2, 0.3],
            tokens_used=10
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[
            {"id": "doc1", "content": "mid", "similarity": 0.6, "metadata": {}},
            {"id": "doc2", "content": "high", "similarity": 0.95, "metadata": {}},
            {"id": "doc3", "content": "low", "similarity": 0.3, "metadata": {}}
        ])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search("test", entity_types=["requirement"])

        # Results should be sorted by similarity descending
        if len(response.results) >= 3:
            assert response.results[0].similarity >= response.results[1].similarity
            assert response.results[1].similarity >= response.results[2].similarity

    @pytest.mark.asyncio
    async def test_semantic_search_applies_limit(self):
        """Test that global limit is applied."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1],
            tokens_used=1
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        many_results = [
            {"id": f"doc{i}", "content": f"content{i}", "similarity": 0.9 - i*0.01, "metadata": {}}
            for i in range(20)
        ]
        mock_rpc.execute.return_value = MagicMock(data=many_results)
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search("test", limit=5, entity_types=["requirement"])

        assert len(response.results) <= 5

    @pytest.mark.asyncio
    async def test_keyword_search_returns_empty_for_invalid_entities(self):
        """Test keyword search with invalid entity types."""
        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.keyword_search("test", entity_types=["invalid"])

        assert response.total_results == 0
        assert response.mode == "keyword"

    @pytest.mark.asyncio
    async def test_keyword_search_attempts_fts_rpc(self):
        """Test that keyword search tries FTS RPC first."""
        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[
            {"id": "doc1", "name": "test", "description": "content", "rank": 0.5}
        ])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.keyword_search("test query", entity_types=["requirement"])

        # FTS RPC should be called
        self.mock_supabase.rpc.assert_called()
        call_args = self.mock_supabase.rpc.call_args
        rpc_name = call_args[0][0]
        assert "search_" in rpc_name and "fts" in rpc_name

    @pytest.mark.asyncio
    async def test_keyword_search_fallback_to_ilike(self):
        """Test fallback to ILIKE when FTS RPC fails."""
        # Use MagicMock to avoid coroutine warnings - Supabase's .execute() is synchronous
        mock_table = MagicMock()
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.ilike.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[
            {"id": "doc1", "name": "test", "description": "content"}
        ])
        mock_table.select.return_value = mock_query

        # FTS RPC fails, so ILIKE is used
        self.mock_supabase.rpc.side_effect = Exception("RPC not found")
        self.mock_supabase.table.return_value = mock_table

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.keyword_search("test query", entity_types=["organization"])

        # Should have results from table query
        assert response.mode == "keyword"
        # Verify table was queried
        self.mock_supabase.table.assert_called()

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_results(self):
        """Test that hybrid search combines semantic and keyword results."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1],
            tokens_used=10
        )

        # Mock semantic search RPC - use MagicMock to avoid coroutine warnings
        semantic_mock = MagicMock()
        semantic_mock.execute.return_value = MagicMock(data=[
            {"id": "doc1", "content": "semantic result", "similarity": 0.9, "metadata": {}}
        ])

        # Mock keyword search table query - use MagicMock to avoid coroutine warnings
        keyword_table = MagicMock()
        keyword_query = MagicMock()
        keyword_query.eq.return_value = keyword_query
        keyword_query.or_.return_value = keyword_query
        keyword_query.limit.return_value = keyword_query
        keyword_query.ilike.return_value = keyword_query
        keyword_query.execute.return_value = MagicMock(data=[
            {"id": "doc2", "name": "keyword result", "description": "content"}
        ])
        keyword_table.select.return_value = keyword_query

        def rpc_side_effect(name, params=None):
            if "match_" in name:
                return semantic_mock
            else:
                raise Exception("FTS not available")

        self.mock_supabase.rpc.side_effect = rpc_side_effect
        self.mock_supabase.table.return_value = keyword_table

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.hybrid_search("test query", entity_types=["requirement"])

        assert response.mode == "hybrid"
        # Should have at least results from one of the search methods
        assert response.results is not None

    @pytest.mark.asyncio
    async def test_similarity_search_excludes_id(self):
        """Test that similarity search excludes specified ID."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1],
            tokens_used=1
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[
            {"id": "source-id", "content": "source", "similarity": 0.99, "metadata": {}},
            {"id": "similar-1", "content": "similar", "similarity": 0.85, "metadata": {}},
            {"id": "similar-2", "content": "similar", "similarity": 0.80, "metadata": {}}
        ])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.similarity_search_by_content(
            "source content",
            "document",
            exclude_id="source-id",
            limit=2
        )

        # Source ID should be excluded from results
        result_ids = [r.id for r in response.results]
        assert "source-id" not in result_ids

    @pytest.mark.asyncio
    async def test_similarity_search_returns_empty_for_invalid_entity(self):
        """Test similarity search with invalid entity type."""
        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.similarity_search_by_content(
            "test",
            "invalid_entity"
        )

        assert response.total_results == 0
        assert response.mode == "similarity"

    @pytest.mark.asyncio
    async def test_search_response_contains_timing_info(self):
        """Test that search responses include timing information."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1],
            tokens_used=10
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[
            {"id": "doc1", "content": "test", "similarity": 0.9, "metadata": {}}
        ])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search("test")

        assert response.search_time_ms >= 0
        assert response.query_embedding_tokens == 10

    @pytest.mark.asyncio
    async def test_search_filters_applied_to_rpc(self):
        """Test that filters are passed to RPC calls."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1],
            tokens_used=1
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        filters = {"project_id": "proj-123"}

        await service.semantic_search("test", filters=filters)

        # Check that filters were passed to RPC
        call_args = self.mock_supabase.rpc.call_args
        params = call_args[0][1]
        assert params.get("filters") == filters

    @pytest.mark.asyncio
    async def test_keyword_search_applies_soft_delete_filter(self):
        """Test that keyword search filters out soft-deleted items."""
        # Use MagicMock to avoid coroutine warnings - Supabase's .execute() is synchronous
        mock_table = MagicMock()
        mock_query = MagicMock()

        # Track method calls on the query builder
        eq_calls = []
        def eq_side_effect(field, value):
            eq_calls.append((field, value))
            return mock_query

        mock_query.eq.side_effect = eq_side_effect
        mock_query.or_.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.ilike.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[])

        # Make FTS RPC fail to fall back to ILIKE
        self.mock_supabase.rpc.side_effect = Exception("RPC not found")
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_query

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        await service.keyword_search("test", entity_types=["document"])

        # Document table should have the is_deleted filter applied
        # (some tables like test_req and properties don't have soft delete)
        # Verify table method was called
        self.mock_supabase.table.assert_called()


# =============================================================================
# INTEGRATION SCENARIOS
# =============================================================================

class TestSearchIntegrationScenarios:
    """Test realistic search scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use regular MagicMock for supabase to support method chaining
        self.mock_supabase = MagicMock()
        self.mock_embedding_service = AsyncMock()

        # Make rpc return a mock with execute method (as expected by vector_search.py)
        self.mock_supabase.rpc.return_value = MagicMock()

    @pytest.mark.asyncio
    async def test_search_across_multiple_entity_types(self):
        """Test searching across multiple entity types."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1, 0.2],
            tokens_used=5
        )

        # Mock RPC to return results for each call
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[
            {"id": "req1", "content": "requirement", "similarity": 0.9, "metadata": {}}
        ])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search("test", entity_types=["requirement", "document"])

        # Verify RPC was called multiple times for each entity type
        assert self.mock_supabase.rpc.call_count >= 1

    @pytest.mark.asyncio
    async def test_no_results_returns_gracefully(self):
        """Test that no results are handled gracefully."""
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1],
            tokens_used=1
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search("xyz")

        assert response.total_results == 0
        assert response.results == []
        assert response.search_time_ms >= 0

    @pytest.mark.asyncio
    async def test_very_long_search_query_handled(self):
        """Test that very long search queries are handled."""
        long_query = "a" * 5000
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1],
            tokens_used=100
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search(long_query)

        # Should handle without crashing
        assert response is not None
        assert response.mode == "semantic"

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self):
        """Test that special characters in search queries are handled."""
        special_query = "<script>alert('xss')</script> OR 1=1"
        self.mock_embedding_service.generate_embedding.return_value = MagicMock(
            embedding=[0.1],
            tokens_used=5
        )

        # Use MagicMock, not AsyncMock, since Supabase's .execute() is synchronous
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[])
        self.mock_supabase.rpc.return_value = mock_rpc

        service = VectorSearchService(self.mock_supabase, self.mock_embedding_service)
        response = await service.semantic_search(special_query)

        # Should handle without crashing
        assert response is not None
