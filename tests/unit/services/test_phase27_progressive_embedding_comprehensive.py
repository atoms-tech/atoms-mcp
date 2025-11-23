"""Phase 27: Comprehensive tests for ProgressiveEmbeddingService to reach 85%+ coverage."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List


class TestProgressiveEmbeddingService:
    """Comprehensive tests for ProgressiveEmbeddingService."""

    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client."""
        mock = MagicMock()
        mock.table.return_value.select.return_value.is_.return_value.eq.return_value.limit.return_value.order.return_value.execute.return_value.data = []
        return mock

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        mock = AsyncMock()
        mock.generate_embedding.return_value = MagicMock(embedding=[0.1] * 768)
        return mock

    @pytest.fixture
    def service(self, mock_supabase, mock_embedding_service):
        """Create ProgressiveEmbeddingService instance."""
        from services.progressive_embedding import ProgressiveEmbeddingService
        return ProgressiveEmbeddingService(mock_supabase, mock_embedding_service)

    @pytest.mark.asyncio
    async def test_ensure_embeddings_for_search_background(self, service, mock_supabase):
        """Test ensuring embeddings in background mode."""
        # Setup mock to return records without embeddings
        mock_supabase.table.return_value.select.return_value.is_.return_value.eq.return_value.limit.return_value.order.return_value.execute.return_value.data = [
            {"id": "1", "content": "test", "embedding": None},
            {"id": "2", "content": "test2", "embedding": None}
        ]
        
        results = await service.ensure_embeddings_for_search(
            ["document"], limit=10, background=True
        )
        
        assert "document" in results
        assert "Generating" in results["document"]

    @pytest.mark.asyncio
    async def test_ensure_embeddings_for_search_synchronous(self, service, mock_supabase):
        """Test ensuring embeddings in synchronous mode."""
        # Setup mock to return records without embeddings
        mock_supabase.table.return_value.select.return_value.is_.return_value.eq.return_value.limit.return_value.order.return_value.execute.return_value.data = [
            {"id": "1", "content": "test", "embedding": None}
        ]
        
        # Mock the update to succeed
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        
        results = await service.ensure_embeddings_for_search(
            ["document"], limit=10, background=False
        )
        
        assert "document" in results

    @pytest.mark.asyncio
    async def test_ensure_embeddings_for_search_all_have_embeddings(self, service, mock_supabase):
        """Test when all records already have embeddings."""
        # Setup mock to return empty list (no records without embeddings)
        mock_supabase.table.return_value.select.return_value.is_.return_value.eq.return_value.limit.return_value.order.return_value.execute.return_value.data = []
        
        results = await service.ensure_embeddings_for_search(["document"])
        
        assert "document" in results
        assert "All records have embeddings" in results["document"]

    @pytest.mark.asyncio
    async def test_ensure_embeddings_for_search_invalid_entity_type(self, service):
        """Test with invalid entity type."""
        results = await service.ensure_embeddings_for_search(["invalid_type"])
        
        assert "invalid_type" not in results or results.get("invalid_type") == "Error"

    @pytest.mark.asyncio
    async def test_ensure_embeddings_for_search_multiple_entity_types(self, service, mock_supabase):
        """Test with multiple entity types."""
        mock_supabase.table.return_value.select.return_value.is_.return_value.eq.return_value.limit.return_value.order.return_value.execute.return_value.data = []
        
        results = await service.ensure_embeddings_for_search(["document", "requirement"])
        
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_generate_embedding_on_demand_with_record_data(self, service, mock_supabase, mock_embedding_service):
        """Test generating embedding on-demand with provided record data."""
        record_data = {"id": "1", "content": "test content", "name": "test"}
        
        # Mock RPC call to succeed
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        
        result = await service.generate_embedding_on_demand("documents", "1", record_data)
        
        assert result is not None
        assert "embedding" in result
        assert "timings" in result

    @pytest.mark.asyncio
    async def test_generate_embedding_on_demand_fetch_record(self, service, mock_supabase, mock_embedding_service):
        """Test generating embedding on-demand by fetching record."""
        # Mock record fetch
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "1", "content": "test content"
        }
        
        # Mock RPC call
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        
        result = await service.generate_embedding_on_demand("documents", "1")
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_embedding_on_demand_no_content(self, service, mock_supabase):
        """Test generating embedding when record has no content."""
        # For documents table, need content/description/name - if none have text, should return None
        record_data = {"id": "1"}  # No content columns
        
        result = await service.generate_embedding_on_demand("documents", "1", record_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_on_demand_duplicate_processing(self, service, mock_supabase):
        """Test preventing duplicate processing."""
        record_data = {"id": "1", "content": "test"}
        
        # Add to processing set
        service._processing_records.add("documents:1")
        
        result = await service.generate_embedding_on_demand("documents", "1", record_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_on_demand_embedding_error(self, service, mock_supabase, mock_embedding_service):
        """Test handling embedding generation error."""
        record_data = {"id": "1", "content": "test"}
        mock_embedding_service.generate_embedding.side_effect = Exception("API error")
        
        result = await service.generate_embedding_on_demand("documents", "1", record_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_find_records_without_embeddings(self, service, mock_supabase):
        """Test finding records without embeddings."""
        mock_supabase.table.return_value.select.return_value.is_.return_value.eq.return_value.limit.return_value.order.return_value.execute.return_value.data = [
            {"id": "1", "content": "test"}
        ]
        
        records = await service._find_records_without_embeddings("documents", limit=10)
        
        assert len(records) == 1

    @pytest.mark.asyncio
    async def test_find_records_without_embeddings_error(self, service, mock_supabase):
        """Test error handling when finding records."""
        mock_supabase.table.return_value.select.return_value.is_.return_value.eq.return_value.limit.return_value.order.return_value.execute.side_effect = Exception("DB error")
        
        records = await service._find_records_without_embeddings("documents")
        
        assert records == []

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_records(self, service, mock_supabase, mock_embedding_service):
        """Test generating embeddings for batch of records."""
        records = [
            {"id": "1", "content": "test1"},
            {"id": "2", "content": "test2"}
        ]
        
        # Mock RPC call
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        
        count = await service._generate_embeddings_for_records("documents", records)
        
        assert count == 2

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_records_partial_failure(self, service, mock_supabase, mock_embedding_service):
        """Test handling partial failures in batch."""
        records = [
            {"id": "1", "content": "test1"},
            {"id": "2"}  # Missing content
        ]
        
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        
        count = await service._generate_embeddings_for_records("documents", records)
        
        assert count == 1

    @pytest.mark.asyncio
    async def test_fetch_record(self, service, mock_supabase):
        """Test fetching a record."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "1", "content": "test"
        }
        
        record = await service._fetch_record("documents", "1")
        
        assert record is not None
        assert record["id"] == "1"

    @pytest.mark.asyncio
    async def test_fetch_record_not_found(self, service, mock_supabase):
        """Test fetching non-existent record."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        
        record = await service._fetch_record("documents", "999")
        
        assert record is None

    @pytest.mark.asyncio
    async def test_fetch_record_error(self, service, mock_supabase):
        """Test error handling when fetching record."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB error")
        
        record = await service._fetch_record("documents", "1")
        
        assert record is None

    def test_extract_content_from_content_column(self, service):
        """Test extracting content from content column."""
        record = {"id": "1", "content": "test content"}
        content = service._extract_content(record, "documents")
        
        assert content == "test content"

    def test_extract_content_from_description_column(self, service):
        """Test extracting content from description column."""
        record = {"id": "1", "description": "test description"}
        content = service._extract_content(record, "documents")
        
        assert content == "test description"

    def test_extract_content_from_name_column(self, service):
        """Test extracting content from name column."""
        record = {"id": "1", "name": "test name"}
        content = service._extract_content(record, "documents")
        
        assert content == "test name"

    def test_extract_content_no_content(self, service):
        """Test when record has no extractable content."""
        record = {"id": "1"}
        content = service._extract_content(record, "documents")
        
        assert content is None

    def test_extract_content_whitespace_only(self, service):
        """Test when content is only whitespace."""
        record = {"id": "1", "content": "   "}
        content = service._extract_content(record, "documents")
        
        assert content is None

    @pytest.mark.asyncio
    async def test_update_record_embedding_rpc_success(self, service, mock_supabase):
        """Test updating record embedding via RPC."""
        record_data = {"id": "1", "created_by": "user1"}
        embedding = [0.1] * 768
        
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        
        result = await service._update_record_embedding("documents", "1", embedding, record_data)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_update_record_embedding_rpc_retry(self, service, mock_supabase):
        """Test RPC retry on connection error."""
        record_data = {"id": "1", "created_by": "user1"}
        embedding = [0.1] * 768
        
        # First call fails with connection error, second succeeds
        mock_supabase.rpc.return_value.execute.side_effect = [
            Exception("Resource temporarily unavailable"),
            MagicMock()
        ]
        
        result = await service._update_record_embedding("documents", "1", embedding, record_data)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_update_record_embedding_fallback_to_direct_update(self, service, mock_supabase):
        """Test fallback to direct update when RPC fails."""
        record_data = {"id": "1", "created_by": "user1"}
        embedding = [0.1] * 768
        
        # RPC fails with permission error
        mock_supabase.rpc.return_value.execute.side_effect = Exception("permission denied")
        
        # Direct update succeeds
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": "1"}]
        
        result = await service._update_record_embedding("documents", "1", embedding, record_data)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_update_record_embedding_both_fail(self, service, mock_supabase):
        """Test when both RPC and direct update fail."""
        record_data = {"id": "1", "created_by": "user1"}
        embedding = [0.1] * 768
        
        # Both fail
        mock_supabase.rpc.return_value.execute.side_effect = Exception("RPC error")
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Direct error")
        
        result = await service._update_record_embedding("documents", "1", embedding, record_data)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_update_record_embedding_no_rows_updated(self, service, mock_supabase):
        """Test when update returns no rows."""
        record_data = {"id": "1", "created_by": "user1"}
        embedding = [0.1] * 768
        
        # RPC fails
        mock_supabase.rpc.return_value.execute.side_effect = Exception("RPC error")
        
        # Direct update returns no data
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
        
        result = await service._update_record_embedding("documents", "1", embedding, record_data)
        
        assert result is False

    def test_get_table_name_mapping(self, service):
        """Test entity type to table name mapping."""
        assert service._get_table_name("document") == "documents"
        assert service._get_table_name("requirement") == "requirements"
        assert service._get_table_name("test") == "test_req"
        assert service._get_table_name("project") == "projects"
        assert service._get_table_name("organization") == "organizations"

    def test_get_table_name_invalid(self, service):
        """Test invalid entity type."""
        assert service._get_table_name("invalid") is None

    def test_get_processing_stats(self, service):
        """Test getting processing statistics."""
        service._processing_records.add("documents:1")
        service._processing_records.add("documents:2")
        
        stats = service.get_processing_stats()
        
        assert stats["currently_processing"] == 2
        assert len(stats["processing_records"]) == 2

    def test_get_processing_stats_empty(self, service):
        """Test processing stats when nothing is processing."""
        stats = service.get_processing_stats()
        
        assert stats["currently_processing"] == 0
        assert len(stats["processing_records"]) == 0

    @pytest.mark.asyncio
    async def test_ensure_embeddings_for_search_error_handling(self, service, mock_supabase):
        """Test error handling in ensure_embeddings_for_search."""
        # Cause an error in finding records - need to set up the chain properly
        chain = mock_supabase.table.return_value
        chain.select.return_value.is_.return_value.eq.return_value.limit.return_value.order.return_value.execute.side_effect = Exception("DB error")
        
        results = await service.ensure_embeddings_for_search(["document"])
        
        assert "document" in results
        # Error should be caught and returned as error message
        assert isinstance(results["document"], str)
