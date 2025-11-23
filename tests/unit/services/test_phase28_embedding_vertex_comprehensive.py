"""Phase 28: Comprehensive tests for VertexAIEmbeddingService to reach 85%+ coverage."""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch, mock_open
from typing import List


class TestVertexAIEmbeddingService:
    """Comprehensive tests for VertexAIEmbeddingService."""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up mock environment variables."""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials."""
        with patch('services.embedding_vertex.default') as mock_default, \
             patch('services.embedding_vertex.service_account') as mock_sa:
            mock_cred = MagicMock()
            mock_default.return_value = (mock_cred, "test-project")
            yield mock_cred

    @pytest.fixture
    def service(self, mock_env, mock_credentials):
        """Create VertexAIEmbeddingService instance."""
        with patch('services.embedding_vertex.VERTEX_AI_AVAILABLE', True):
            from services.embedding_vertex import VertexAIEmbeddingService
            return VertexAIEmbeddingService(cache_size=100)

    def test_init_with_service_account_json(self, monkeypatch):
        """Test initialization with service account JSON from env."""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
        monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", '{"type": "service_account"}')
        
        with patch('services.embedding_vertex.VERTEX_AI_AVAILABLE', True), \
             patch('services.embedding_vertex.service_account') as mock_sa:
            mock_sa.Credentials.from_service_account_info.return_value = MagicMock()
            
            from services.embedding_vertex import VertexAIEmbeddingService
            service = VertexAIEmbeddingService()
            
            assert service.project == "test-project"

    def test_init_missing_project(self, monkeypatch):
        """Test initialization fails without project."""
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("GCP_PROJECT", raising=False)
        monkeypatch.delenv("GOOGLE_VERTEX_PROJECT", raising=False)
        
        with patch('services.embedding_vertex.VERTEX_AI_AVAILABLE', True):
            from services.embedding_vertex import VertexAIEmbeddingService
            with pytest.raises(RuntimeError, match="GOOGLE_CLOUD_PROJECT"):
                VertexAIEmbeddingService()

    def test_init_packages_not_available(self):
        """Test initialization fails when packages not available."""
        with patch('services.embedding_vertex.VERTEX_AI_AVAILABLE', False):
            from services.embedding_vertex import VertexAIEmbeddingService
            with pytest.raises(RuntimeError, match="Required packages"):
                VertexAIEmbeddingService()

    @pytest.mark.asyncio
    async def test_generate_embedding_basic(self, service, mock_credentials):
        """Test basic embedding generation."""
        with patch('services.embedding_vertex.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "predictions": [{
                    "embeddings": {
                        "values": [0.1] * 768
                    }
                }]
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await service.generate_embedding("test content")
            
            assert result.embedding is not None
            assert len(result.embedding) == 768

    @pytest.mark.asyncio
    async def test_generate_embedding_cached(self, service):
        """Test embedding generation uses cache."""
        # First call
        with patch('services.embedding_vertex.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "predictions": [{
                    "embeddings": {
                        "values": [0.1] * 768
                    }
                }]
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result1 = await service.generate_embedding("test content")
            assert not result1.cached
        
        # Second call should use cache
        result2 = await service.generate_embedding("test content")
        assert result2.cached

    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self, service, mock_credentials):
        """Test handling API errors."""
        with patch('services.embedding_vertex.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(Exception):
                await service.generate_embedding("test content")

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self, service, mock_credentials):
        """Test batch embedding generation."""
        with patch('services.embedding_vertex.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "predictions": [
                    {"embeddings": {"values": [0.1] * 768}},
                    {"embeddings": {"values": [0.2] * 768}}
                ]
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await service.generate_batch_embeddings(["content1", "content2"])
            
            assert len(result.embeddings) == 2
            assert result.total_tokens > 0

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings_partial_cache(self, service):
        """Test batch embedding with partial cache."""
        # Cache one embedding
        with patch('services.embedding_vertex.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "predictions": [{"embeddings": {"values": [0.1] * 768}}]
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            await service.generate_embedding("cached_content")
        
        # Batch with one cached, one new
        with patch('services.embedding_vertex.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "predictions": [{"embeddings": {"values": [0.2] * 768}}]
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await service.generate_batch_embeddings(["cached_content", "new_content"])
            
            assert len(result.embeddings) == 2
            assert result.cached_count == 1

    def test_get_cache_stats(self, service):
        """Test getting cache statistics."""
        stats = service.get_cache_stats()
        
        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats

    def test_clear_cache(self, service):
        """Test clearing cache."""
        # Add something to cache first
        service._cache = {"test": [0.1] * 768}
        
        service.clear_cache()
        
        assert len(service._cache) == 0

    @pytest.mark.asyncio
    async def test_generate_embedding_with_retry(self, service, mock_credentials):
        """Test embedding generation with retry on failure."""
        with patch('services.embedding_vertex.httpx.AsyncClient') as mock_client:
            # First call fails, second succeeds
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 429
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {
                "predictions": [{"embeddings": {"values": [0.1] * 768}}]
            }
            
            mock_client.return_value.__aenter__.return_value.post.side_effect = [
                mock_response_fail,
                mock_response_success
            ]
            
            result = await service.generate_embedding("test", max_retries=2)
            
            assert result.embedding is not None

    def test_cache_key_generation(self, service):
        """Test cache key generation."""
        key1 = service._get_cache_key("test content")
        key2 = service._get_cache_key("test content")
        key3 = service._get_cache_key("different content")
        
        assert key1 == key2
        assert key1 != key3
