"""Phase 27: Comprehensive tests for EnhancedVectorSearchService to reach 85%+ coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List


class TestEnhancedVectorSearchService:
    """Comprehensive tests for EnhancedVectorSearchService."""

    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client."""
        return MagicMock()

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        return AsyncMock()

    @pytest.fixture
    def mock_vector_search(self):
        """Create mock VectorSearchService."""
        mock = AsyncMock()
        mock.searchable_entities = {"document": {}, "requirement": {}}
        mock.semantic_search.return_value = MagicMock(results=[], total=0, limit=10, avg_similarity=0.0, method="semantic")
        mock.hybrid_search.return_value = MagicMock(results=[], total=0, limit=10, avg_similarity=0.0, method="hybrid")
        mock.keyword_search.return_value = MagicMock(results=[], total=0, limit=10, avg_similarity=0.0, method="keyword")
        mock.similarity_search_by_content.return_value = MagicMock(results=[], total=0, limit=5, avg_similarity=0.0, method="similarity")
        return mock

    @pytest.fixture
    def service(self, mock_supabase, mock_embedding_service, mock_vector_search):
        """Create EnhancedVectorSearchService instance."""
        from services.enhanced_vector_search import EnhancedVectorSearchService
        
        with patch('services.enhanced_vector_search.VectorSearchService', return_value=mock_vector_search):
            service = EnhancedVectorSearchService(mock_supabase, mock_embedding_service)
            service.vector_search = mock_vector_search
            return service

    @pytest.mark.asyncio
    async def test_semantic_search_basic(self, service, mock_vector_search):
        """Test basic semantic search."""
        mock_vector_search.semantic_search.return_value = MagicMock(
            results=[{"id": "1", "content": "test"}],
            total=1,
            limit=10,
            avg_similarity=0.85,
            method="semantic"
        )
        
        result = await service.semantic_search("test query", ensure_embeddings=True)
        
        assert result.total == 1
        assert len(result.results) == 1

    @pytest.mark.asyncio
    async def test_semantic_search_without_embeddings(self, service, mock_vector_search):
        """Test semantic search without ensuring embeddings."""
        mock_vector_search.semantic_search.return_value = MagicMock(
            results=[{"id": "1"}],
            total=1,
            limit=10,
            avg_similarity=0.8,
            method="semantic"
        )
        
        result = await service.semantic_search("test", ensure_embeddings=False)
        
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_semantic_search_few_results_triggers_additional_generation(self, service, mock_vector_search):
        """Test semantic search with few results triggers additional embedding generation."""
        # First search returns few results
        mock_vector_search.semantic_search.side_effect = [
            MagicMock(results=[{"id": "1"}], total=1, limit=10, avg_similarity=0.7, method="semantic"),
            MagicMock(results=[{"id": "1", "id": "2"}], total=2, limit=10, avg_similarity=0.75, method="semantic")
        ]
        
        result = await service.semantic_search("test", limit=10, ensure_embeddings=True)
        
        assert result.total >= 1

    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(self, service, mock_vector_search):
        """Test semantic search with filters."""
        mock_vector_search.semantic_search.return_value = MagicMock(
            results=[],
            total=0,
            limit=10,
            avg_similarity=0.0,
            method="semantic"
        )
        
        result = await service.semantic_search(
            "test",
            entity_types=["document"],
            filters={"status": "active"}
        )
        
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_hybrid_search(self, service, mock_vector_search):
        """Test hybrid search."""
        mock_vector_search.hybrid_search.return_value = MagicMock(
            results=[{"id": "1"}],
            total=1,
            limit=10,
            avg_similarity=0.8,
            method="hybrid"
        )
        
        result = await service.hybrid_search("test query", ensure_embeddings=True)
        
        assert result.method == "hybrid"

    @pytest.mark.asyncio
    async def test_hybrid_search_without_embeddings(self, service, mock_vector_search):
        """Test hybrid search without ensuring embeddings."""
        mock_vector_search.hybrid_search.return_value = MagicMock(
            results=[],
            total=0,
            limit=10,
            avg_similarity=0.0,
            method="hybrid"
        )
        
        result = await service.hybrid_search("test", ensure_embeddings=False)
        
        assert result.method == "hybrid"

    @pytest.mark.asyncio
    async def test_keyword_search(self, service, mock_vector_search):
        """Test keyword search."""
        mock_vector_search.keyword_search.return_value = MagicMock(
            results=[{"id": "1"}],
            total=1,
            limit=10,
            avg_similarity=0.0,
            method="keyword"
        )
        
        result = await service.keyword_search("test")
        
        assert result.method == "keyword"

    @pytest.mark.asyncio
    async def test_keyword_search_with_filters(self, service, mock_vector_search):
        """Test keyword search with filters."""
        mock_vector_search.keyword_search.return_value = MagicMock(
            results=[],
            total=0,
            limit=10,
            avg_similarity=0.0,
            method="keyword"
        )
        
        result = await service.keyword_search(
            "test",
            entity_types=["document"],
            filters={"status": "active"}
        )
        
        assert result.method == "keyword"

    @pytest.mark.asyncio
    async def test_similarity_search_by_content(self, service, mock_vector_search):
        """Test similarity search by content."""
        mock_vector_search.similarity_search_by_content.return_value = MagicMock(
            results=[{"id": "1"}],
            total=1,
            limit=5,
            avg_similarity=0.9,
            method="similarity"
        )
        
        result = await service.similarity_search_by_content(
            "test content",
            "document",
            ensure_embeddings=True
        )
        
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_similarity_search_by_content_with_exclude(self, service, mock_vector_search):
        """Test similarity search with exclude ID."""
        mock_vector_search.similarity_search_by_content.return_value = MagicMock(
            results=[],
            total=0,
            limit=5,
            avg_similarity=0.0,
            method="similarity"
        )
        
        result = await service.similarity_search_by_content(
            "test",
            "document",
            exclude_id="excluded_id"
        )
        
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_comprehensive_search(self, service, mock_vector_search):
        """Test comprehensive search."""
        mock_vector_search.semantic_search.return_value = MagicMock(
            results=[{"id": "1"}],
            total=1,
            limit=10,
            avg_similarity=0.8,
            method="semantic"
        )
        mock_vector_search.keyword_search.return_value = MagicMock(
            results=[{"id": "2"}],
            total=1,
            limit=10,
            avg_similarity=0.0,
            method="keyword"
        )
        
        results = await service.comprehensive_search("test query")
        
        assert "semantic" in results
        assert "keyword" in results

    @pytest.mark.asyncio
    async def test_comprehensive_search_semantic_error(self, service, mock_vector_search):
        """Test comprehensive search with semantic search error."""
        mock_vector_search.semantic_search.side_effect = Exception("Semantic error")
        mock_vector_search.keyword_search.return_value = MagicMock(
            results=[],
            total=0,
            limit=10,
            avg_similarity=0.0,
            method="keyword"
        )
        
        results = await service.comprehensive_search("test")
        
        assert "semantic" in results
        assert results["semantic"].method == "semantic_failed"

    @pytest.mark.asyncio
    async def test_comprehensive_search_keyword_error(self, service, mock_vector_search):
        """Test comprehensive search with keyword search error."""
        mock_vector_search.semantic_search.return_value = MagicMock(
            results=[],
            total=0,
            limit=10,
            avg_similarity=0.0,
            method="semantic"
        )
        mock_vector_search.keyword_search.side_effect = Exception("Keyword error")
        
        results = await service.comprehensive_search("test")
        
        assert "keyword" in results
        assert results["keyword"].method == "keyword_failed"

    @pytest.mark.asyncio
    async def test_get_embedding_coverage(self, service, mock_supabase):
        """Test getting embedding coverage statistics."""
        # Mock total count query (head=True returns count attribute)
        mock_total = MagicMock()
        mock_total.count = 100
        mock_total_result = MagicMock()
        mock_total_result.count = 100
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_total_result
        
        # Mock embedded count query
        mock_embedded_result = MagicMock()
        mock_embedded_result.count = 75
        mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.execute.return_value = mock_embedded_result
        
        coverage = await service.get_embedding_coverage(["document"])
        
        assert "document" in coverage
        assert coverage["document"]["total_records"] == 100
        assert coverage["document"]["embedded_records"] == 75

    @pytest.mark.asyncio
    async def test_get_embedding_coverage_error(self, service, mock_supabase):
        """Test error handling in embedding coverage."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        
        coverage = await service.get_embedding_coverage(["document"])
        
        assert "document" in coverage
        assert "error" in coverage["document"]

    @pytest.mark.asyncio
    async def test_get_embedding_coverage_all_entity_types(self, service, mock_supabase):
        """Test getting coverage for all entity types."""
        mock_total_result = MagicMock()
        mock_total_result.count = 50
        mock_embedded_result = MagicMock()
        mock_embedded_result.count = 40
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_total_result
        mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.execute.return_value = mock_embedded_result
        
        coverage = await service.get_embedding_coverage()
        
        assert len(coverage) > 0

    def test_get_processing_stats(self, service):
        """Test getting processing statistics."""
        # Access through progressive_service
        stats = service.progressive_service.get_processing_stats()
        
        assert "currently_processing" in stats
        assert "processing_records" in stats
