"""Vector-Kit unified client interface."""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from utils.logging_setup import get_logger

from vector_kit.providers.factory import get_embedding_service
from vector_kit.search.enhanced import EnhancedVectorSearchService
from vector_kit.search.types import SearchResponse

logger = get_logger(__name__)


class VectorClient:
    """
    Unified client for vector search with progressive embedding.
    
    Provides a simple interface to:
    - Generate embeddings across multiple providers (Vertex AI, OpenAI, local)
    - Search across multiple backends (pgvector, Supabase, FAISS, LanceDB)
    - Progressive embedding (on-demand generation for missing records)
    - Hybrid search (semantic + keyword)
    
    Example:
        ```python
        from vector_kit import VectorClient
        
        client = VectorClient(
            provider="vertex",
            backend_dsn="postgres://...",
        )
        
        # Progressive semantic search
        results = await client.search.semantic(
            query="machine learning frameworks",
            limit=20,
            ensure_embeddings=True,  # Generate missing embeddings
        )
        ```
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        backend_dsn: Optional[str] = None,
        supabase_client=None,
        **provider_kwargs
    ):
        """
        Initialize Vector Client.
        
        Args:
            provider: Embedding provider ("vertex", "openai", "local", or None for auto-detect)
            backend_dsn: Database connection string for pgvector backend
            supabase_client: Supabase client instance (alternative to backend_dsn)
            **provider_kwargs: Additional provider-specific configuration
        """
        self.provider = provider
        self.backend_dsn = backend_dsn
        self.supabase_client = supabase_client
        self.provider_kwargs = provider_kwargs
        
        # Initialize embedding service
        if provider:
            self.embedding_service = get_embedding_service(provider_type=provider, **provider_kwargs)
        else:
            self.embedding_service = get_embedding_service()  # Auto-detect
        
        # Initialize search service
        if supabase_client:
            self.search = EnhancedVectorSearchService(
                supabase_client=supabase_client,
                embedding_service=self.embedding_service
            )
        else:
            raise NotImplementedError("pgvector backend coming soon - use supabase_client for now")
    
    async def semantic_search(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        ensure_embeddings: bool = True
    ) -> SearchResponse:
        """
        Perform semantic search with automatic embedding generation.
        
        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum results to return
            entity_types: Specific entity types to search
            filters: Additional filters to apply
            ensure_embeddings: If True, generate embeddings for missing records
            
        Returns:
            SearchResponse with ranked results
        """
        return await self.search.semantic_search(
            query=query,
            similarity_threshold=similarity_threshold,
            limit=limit,
            entity_types=entity_types,
            filters=filters,
            ensure_embeddings=ensure_embeddings
        )
    
    async def hybrid_search(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        keyword_weight: float = 0.3,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        ensure_embeddings: bool = True
    ) -> SearchResponse:
        """
        Perform hybrid search (semantic + keyword).
        
        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum results to return
            keyword_weight: Weight for keyword results (0-1, default 0.3)
            entity_types: Specific entity types to search
            filters: Additional filters to apply
            ensure_embeddings: If True, generate embeddings for missing records
            
        Returns:
            SearchResponse with ranked results
        """
        return await self.search.hybrid_search(
            query=query,
            similarity_threshold=similarity_threshold,
            limit=limit,
            keyword_weight=keyword_weight,
            entity_types=entity_types,
            filters=filters,
            ensure_embeddings=ensure_embeddings
        )
    
    async def keyword_search(
        self,
        query: str,
        limit: int = 10,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """
        Perform keyword-only search (no embeddings needed).
        
        Args:
            query: Search query text
            limit: Maximum results to return
            entity_types: Specific entity types to search
            filters: Additional filters to apply
            
        Returns:
            SearchResponse with ranked results
        """
        return await self.search.keyword_search(
            query=query,
            limit=limit,
            entity_types=entity_types,
            filters=filters
        )
    
    async def similarity_search_by_content(
        self,
        content: str,
        entity_type: str,
        similarity_threshold: float = 0.8,
        limit: int = 5,
        exclude_id: Optional[str] = None,
        ensure_embeddings: bool = True
    ) -> SearchResponse:
        """
        Find similar content by comparing embeddings.
        
        Args:
            content: Content to find similar matches for
            entity_type: Entity type to search within
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum results to return
            exclude_id: Optional ID to exclude from results
            ensure_embeddings: If True, generate missing embeddings
            
        Returns:
            SearchResponse with similar content
        """
        return await self.search.similarity_search_by_content(
            content=content,
            entity_type=entity_type,
            similarity_threshold=similarity_threshold,
            limit=limit,
            exclude_id=exclude_id,
            ensure_embeddings=ensure_embeddings
        )
    
    async def comprehensive_search(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 20,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, SearchResponse]:
        """
        Perform comprehensive search using all methods.
        
        Returns:
            Dict with results from each search method:
            {
                "semantic": SearchResponse,
                "keyword": SearchResponse,
                "hybrid": SearchResponse
            }
        """
        return await self.search.comprehensive_search(
            query=query,
            similarity_threshold=similarity_threshold,
            limit=limit,
            entity_types=entity_types,
            filters=filters
        )


class EmbeddingProvider:
    """Factory for creating embedding providers."""
    
    @staticmethod
    def vertex(project: str, location: str = "us-central1", **kwargs):
        """Create Vertex AI embedding provider."""
        from vector_kit.providers.vertex import VertexEmbeddingService
        return VertexEmbeddingService(project=project, location=location, **kwargs)
    
    @staticmethod
    def openai(api_key: Optional[str] = None, **kwargs):
        """Create OpenAI embedding provider."""
        # Implementation coming soon
        raise NotImplementedError("OpenAI provider coming soon")
    
    @staticmethod
    def local(model_name: str = "all-MiniLM-L6-v2", **kwargs):
        """Create local embedding provider using sentence-transformers."""
        # Implementation coming soon
        raise NotImplementedError("Local provider coming soon")


class IndexBackend:
    """Factory for creating index backends."""
    
    @staticmethod
    def pgvector(dsn: str, **kwargs):
        """Create pgvector backend."""
        # Implementation coming soon
        raise NotImplementedError("pgvector backend coming soon")
    
    @staticmethod
    def supabase(client, **kwargs):
        """Create Supabase backend."""
        return {"supabase_client": client, **kwargs}
    
    @staticmethod
    def faiss(index_path: Optional[str] = None, **kwargs):
        """Create FAISS backend."""
        # Implementation coming soon
        raise NotImplementedError("FAISS backend coming soon")
    
    @staticmethod
    def lancedb(uri: str, **kwargs):
        """Create LanceDB backend."""
        # Implementation coming soon
        raise NotImplementedError("LanceDB backend coming soon")
