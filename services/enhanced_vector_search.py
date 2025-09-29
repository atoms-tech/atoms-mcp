"""Enhanced vector search service with automatic on-demand embedding generation."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any, NamedTuple
from datetime import datetime

from supabase import Client

from .embedding_factory import get_embedding_service
from .progressive_embedding import ProgressiveEmbeddingService
from .vector_search import SearchResult, SearchResponse

logger = logging.getLogger(__name__)


class EnhancedVectorSearchService:
    """
    Enhanced vector search service that automatically generates embeddings on-demand.
    
    This service wraps the existing VectorSearchService and adds progressive embedding
    capabilities, ensuring that search operations automatically include records that
    don't have embeddings yet.
    """
    
    def __init__(self, supabase_client: Client, embedding_service=None):
        self.supabase = supabase_client
        self.embedding_service = embedding_service or get_embedding_service()
        self.progressive_service = ProgressiveEmbeddingService(supabase_client, self.embedding_service)
        
        # Import the original search service
        from .vector_search import VectorSearchService
        self.vector_search = VectorSearchService(supabase_client, self.embedding_service)
    
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
            SearchResponse with ranked results (may include newly embedded content)
        """
        search_entities = entity_types or list(self.vector_search.searchable_entities.keys())
        
        # Step 1: Ensure embeddings exist for searchable records (background)
        if ensure_embeddings:
            embedding_stats = await self.progressive_service.ensure_embeddings_for_search(
                search_entities, 
                limit=limit * 2,  # Generate a bit more than we need
                background=True  # Non-blocking
            )
            logger.debug(f"Embedding generation initiated: {embedding_stats}")
        
        # Step 2: Perform search with existing embeddings
        primary_results = await self.vector_search.semantic_search(
            query, similarity_threshold, limit, entity_types, filters
        )
        
        # Step 3: If we got fewer results than expected, try harder to fill gaps
        if len(primary_results.results) < min(limit, 5) and ensure_embeddings:
            # Generate embeddings synchronously for a small batch
            additional_stats = await self.progressive_service.ensure_embeddings_for_search(
                search_entities,
                limit=10,  # Small batch for immediate results
                background=False  # Blocking
            )
            logger.debug(f"Additional embeddings generated: {additional_stats}")
            
            # Re-run search to include newly embedded content
            enhanced_results = await self.vector_search.semantic_search(
                query, similarity_threshold, limit, entity_types, filters
            )
            
            # Use the better result set
            if len(enhanced_results.results) > len(primary_results.results):
                return enhanced_results
        
        return primary_results
    
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
        Perform hybrid search with automatic embedding generation.
        
        This combines semantic search (with embedding generation) and keyword search
        for the best coverage of both embedded and non-embedded content.
        """
        search_entities = entity_types or list(self.vector_search.searchable_entities.keys())
        
        # Ensure embeddings for better semantic results
        if ensure_embeddings:
            await self.progressive_service.ensure_embeddings_for_search(
                search_entities,
                limit=limit * 2,
                background=True
            )
        
        # Perform hybrid search (this internally handles both semantic and keyword)
        return await self.vector_search.hybrid_search(
            query, similarity_threshold, limit, keyword_weight, entity_types, filters
        )
    
    async def keyword_search(
        self,
        query: str,
        limit: int = 10,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """
        Perform keyword search (no embedding generation needed).
        
        Keyword search works on all records regardless of embedding status.
        """
        return await self.vector_search.keyword_search(query, limit, entity_types, filters)
    
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
        Find similar content with automatic embedding generation.
        """
        # Ensure embeddings exist for the target entity type
        if ensure_embeddings:
            await self.progressive_service.ensure_embeddings_for_search(
                [entity_type],
                limit=limit * 3,
                background=True
            )
        
        return await self.vector_search.similarity_search_by_content(
            content, entity_type, similarity_threshold, limit, exclude_id
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
        Perform a comprehensive search using all available methods.
        
        This ensures maximum coverage by using:
        1. Semantic search (with embedding generation)
        2. Keyword search (covers all records)
        3. Combines results for comprehensive coverage
        
        Returns:
            Dict with results from each search method
        """
        search_entities = entity_types or list(self.vector_search.searchable_entities.keys())
        
        # Ensure embeddings for semantic search
        await self.progressive_service.ensure_embeddings_for_search(
            search_entities,
            limit=limit,
            background=True
        )
        
        # Run multiple search strategies concurrently
        import asyncio
        
        semantic_task = self.semantic_search(
            query, similarity_threshold, limit//2, entity_types, filters, ensure_embeddings=False
        )
        keyword_task = self.keyword_search(
            query, limit//2, entity_types, filters
        )
        
        semantic_results, keyword_results = await asyncio.gather(
            semantic_task, keyword_task, return_exceptions=True
        )
        
        results = {}
        
        if not isinstance(semantic_results, Exception):
            results['semantic'] = semantic_results
        else:
            logger.error(f"Semantic search failed: {semantic_results}")
            results['semantic'] = SearchResponse([], 0, 0, 0.0, "semantic_failed")
        
        if not isinstance(keyword_results, Exception):
            results['keyword'] = keyword_results
        else:
            logger.error(f"Keyword search failed: {keyword_results}")
            results['keyword'] = SearchResponse([], 0, 0, 0.0, "keyword_failed")
        
        return results
    
    async def get_embedding_coverage(self, entity_types: Optional[List[str]] = None) -> Dict[str, Dict[str, int]]:
        """
        Get embedding coverage statistics for entity types.
        
        Returns:
            Dict with embedding coverage stats per entity type
        """
        search_entities = entity_types or list(self.vector_search.searchable_entities.keys())
        coverage = {}
        
        for entity_type in search_entities:
            table_name = self.progressive_service._get_table_name(entity_type)
            if not table_name:
                continue
            
            try:
                # Count total records
                total_query = self.supabase.table(table_name).select('id', count='exact', head=True)
                total_query = total_query.eq('is_deleted', False)
                total_result = total_query.execute()
                total_count = getattr(total_result, 'count', 0) or 0
                
                # Count records with embeddings
                embedded_query = self.supabase.table(table_name).select('id', count='exact', head=True)
                embedded_query = embedded_query.eq('is_deleted', False)
                embedded_query = embedded_query.not_.is_('embedding', 'null')
                embedded_result = embedded_query.execute()
                embedded_count = getattr(embedded_result, 'count', 0) or 0
                
                coverage_pct = (embedded_count / total_count * 100) if total_count > 0 else 0
                
                coverage[entity_type] = {
                    'total_records': total_count,
                    'embedded_records': embedded_count,
                    'missing_embeddings': total_count - embedded_count,
                    'coverage_percentage': round(coverage_pct, 2)
                }
                
            except Exception as e:
                logger.error(f"Error getting coverage for {entity_type}: {e}")
                coverage[entity_type] = {'error': str(e)}
        
        return coverage
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current background processing statistics."""
        return self.progressive_service.get_processing_stats()