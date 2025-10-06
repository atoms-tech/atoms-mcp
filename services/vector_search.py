"""Vector similarity search service using Supabase pgvector via RPC.

This implementation assumes your Supabase Postgres has pgvector enabled and
exposes per-entity RPC functions that perform similarity search server-side.

Expected RPC signatures (examples):
  match_documents(query_embedding vector, match_count int, similarity_threshold float,
                  filters jsonb default null)
  RETURNS TABLE (id text, content text, metadata jsonb, similarity float);

See infrastructure/sql/vector_rpcs.sql for templates.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, NamedTuple
from datetime import datetime

from supabase import Client

from .embedding_factory import get_embedding_service


class SearchResult(NamedTuple):
    """Single search result with similarity score."""
    id: str
    content: str
    similarity: float
    metadata: Dict[str, Any]
    entity_type: str


class SearchResponse(NamedTuple):
    """Complete search response with results and metadata."""
    results: List[SearchResult]
    total_results: int
    query_embedding_tokens: int
    search_time_ms: float
    mode: str


class VectorSearchService:
    """Service for performing vector similarity search on embedded content."""
    
    def __init__(self, supabase_client: Client, embedding_service=None):
        self.supabase = supabase_client
        self.embedding_service = embedding_service or get_embedding_service()
        
        # Entity type to table mappings for search
        self.searchable_entities = {
            "requirement": "requirements",
            "document": "documents",
            # "test": "tests",  # Disabled due to permission issues with test_req table
            "project": "projects",
            "organization": "organizations",
        }

        # Entity type to RPC function name mappings
        # Provide an RPC per entity that returns rows with
        # (id, content, metadata, similarity)
        self.rpc_functions = {
            "requirement": "match_requirements",
            "document": "match_documents",
            # "test": "match_tests",  # Disabled due to permission issues
            "project": "match_projects",
            "organization": "match_organizations",
        }
    
    async def semantic_search(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Perform semantic search using vector similarity.
        
        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum results to return
            entity_types: Specific entity types to search
            filters: Additional filters to apply
            
        Returns:
            SearchResponse with ranked results
        """
        start_time = datetime.now()
        
        # Generate query embedding
        embedding_result = await self.embedding_service.generate_embedding(query)
        query_vector = embedding_result.embedding
        
        # Determine which entity types to search
        search_entities = entity_types if entity_types else list(self.searchable_entities.keys())
        search_entities = [e for e in search_entities if e in self.searchable_entities]
        
        if not search_entities:
            return SearchResponse([], 0, embedding_result.tokens_used, 0.0, "semantic")
        
        all_results = []
        
        # Search each entity type via RPC
        for entity_type in search_entities:
            rpc_name = self.rpc_functions.get(entity_type)
            if not rpc_name:
                continue

            try:
                params: Dict[str, Any] = {
                    "query_embedding": query_vector,
                    "match_count": limit,
                    "similarity_threshold": similarity_threshold,
                }
                # Optional dynamic filters passed as JSONB to the RPC
                if filters:
                    params["filters"] = filters

                response = self.supabase.rpc(rpc_name, params).execute()

                for row in getattr(response, "data", []) or []:
                    similarity = row.get("similarity")
                    if similarity is None:
                        similarity = 0.0
                    result = SearchResult(
                        id=row.get("id"),
                        content=row.get("content", ""),
                        similarity=float(similarity),
                        metadata=row.get("metadata", {}) or {},
                        entity_type=entity_type,
                    )
                    all_results.append(result)

            except Exception as e:
                # Log error but continue with other entity types
                print(f"Error searching {entity_type}: {str(e)}")
                continue
        
        # Sort all results by similarity score (highest first)
        all_results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Apply global limit
        final_results = all_results[:limit]
        
        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=final_results,
            total_results=len(final_results),
            query_embedding_tokens=embedding_result.tokens_used,
            search_time_ms=search_time,
            mode="semantic"
        )
    
    async def keyword_search(
        self,
        query: str,
        limit: int = 10,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Perform keyword-based search using PostgreSQL full-text search.
        
        Args:
            query: Search query text
            limit: Maximum results to return
            entity_types: Specific entity types to search
            filters: Additional filters to apply
            
        Returns:
            SearchResponse with ranked results
        """
        start_time = datetime.now()
        
        # Determine which entity types to search
        search_entities = entity_types if entity_types else list(self.searchable_entities.keys())
        search_entities = [e for e in search_entities if e in self.searchable_entities]
        
        if not search_entities:
            return SearchResponse([], 0, 0, 0.0, "keyword")
        
        all_results = []
        
        # Search each entity type
        for entity_type in search_entities:
            table_name = self.searchable_entities[entity_type]
            
            try:
                # Build query with filters first, then apply text search
                # Select common columns (not all tables have metadata)
                query_builder = self.supabase.table(table_name).select(
                    "id, name, description"
                )
                
                # Apply default filters (skip for tables without is_deleted)
                tables_without_soft_delete = {'test_req', 'properties'}
                if table_name not in tables_without_soft_delete:
                    query_builder = query_builder.eq("is_deleted", False)

                # Apply additional filters
                if filters:
                    for key, value in filters.items():
                        query_builder = query_builder.eq(key, value)

                # Use ilike for keyword matching on name and description
                response = query_builder.or_(f"name.ilike.%{query}%,description.ilike.%{query}%").limit(limit).execute()

                # Process results
                for row in (response.data or []):
                    # Combine name and description as content
                    name = row.get("name", "")
                    description = row.get("description", "")
                    content = f"{name}: {description}" if name and description else (name or description or "")
                    
                    result = SearchResult(
                        id=row["id"],
                        content=content,
                        similarity=1.0,  # Default score for keyword matches
                        metadata={},  # No metadata for keyword search
                        entity_type=entity_type
                    )
                    all_results.append(result)
                    
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"❌ Keyword search failed for {entity_type}: {e}")
                print(f"❌ Keyword search error [{entity_type}]: {e}")
                import traceback
                print(traceback.format_exc())
                # Continue to search other entity types
                continue
        
        # Apply global limit
        final_results = all_results[:limit]

        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000

        # Debug logging
        print(f"🔍 Keyword search complete: query='{query}', entities={search_entities}, results={len(final_results)}")
        if not final_results:
            print(f"⚠️ No keyword search results found for query '{query}' across {search_entities}")

        return SearchResponse(
            results=final_results,
            total_results=len(final_results),
            query_embedding_tokens=0,  # No embeddings used
            search_time_ms=search_time,
            mode="keyword"
        )
    
    async def hybrid_search(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        keyword_weight: float = 0.3,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query text
            similarity_threshold: Minimum similarity score for semantic search
            limit: Maximum results to return
            keyword_weight: Weight for keyword results (0-1, remainder goes to semantic)
            entity_types: Specific entity types to search
            filters: Additional filters to apply
            
        Returns:
            SearchResponse with combined and ranked results
        """
        start_time = datetime.now()
        
        # Perform both searches concurrently
        import asyncio
        
        semantic_task = self.semantic_search(
            query, similarity_threshold, limit, entity_types, filters
        )
        keyword_task = self.keyword_search(
            query, limit, entity_types, filters
        )
        
        semantic_response, keyword_response = await asyncio.gather(
            semantic_task, keyword_task
        )
        
        # Combine and score results
        combined_results = {}
        
        # Add semantic results with weighted scores
        semantic_weight = 1.0 - keyword_weight
        for result in semantic_response.results:
            key = f"{result.entity_type}:{result.id}"
            similarity = result.similarity if result.similarity is not None else 0.0
            combined_results[key] = SearchResult(
                id=result.id,
                content=result.content,
                similarity=float(similarity) * semantic_weight,
                metadata=result.metadata,
                entity_type=result.entity_type
            )
        
        # Add keyword results with weighted scores
        for result in keyword_response.results:
            key = f"{result.entity_type}:{result.id}"
            if key in combined_results:
                # Boost existing result
                existing = combined_results[key]
                existing_sim = existing.similarity if existing.similarity is not None else 0.0
                combined_results[key] = SearchResult(
                    id=existing.id,
                    content=existing.content,
                    similarity=float(existing_sim) + (keyword_weight * 1.0),
                    metadata=existing.metadata,
                    entity_type=existing.entity_type
                )
            else:
                # Add new keyword-only result
                combined_results[key] = SearchResult(
                    id=result.id,
                    content=result.content,
                    similarity=keyword_weight * 1.0,
                    metadata=result.metadata,
                    entity_type=result.entity_type
                )
        
        # Sort by combined score and apply limit
        final_results = sorted(
            combined_results.values(),
            key=lambda x: x.similarity,
            reverse=True
        )[:limit]
        
        # Calculate total search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=final_results,
            total_results=len(final_results),
            query_embedding_tokens=semantic_response.query_embedding_tokens,
            search_time_ms=search_time,
            mode="hybrid"
        )
    
    async def similarity_search_by_content(
        self,
        content: str,
        entity_type: str,
        similarity_threshold: float = 0.8,
        limit: int = 5,
        exclude_id: Optional[str] = None
    ) -> SearchResponse:
        """Find similar content to the provided text.
        
        Args:
            content: Content to find similar items for
            entity_type: Type of entity to search within
            similarity_threshold: Minimum similarity score
            limit: Maximum results to return
            exclude_id: ID to exclude from results (e.g., the source item)
            
        Returns:
            SearchResponse with similar content
        """
        if entity_type not in self.searchable_entities:
            return SearchResponse([], 0, 0, 0.0, "similarity")
        
        # Use the content as the query for semantic search
        search_response = await self.semantic_search(
            content,
            similarity_threshold,
            limit + (1 if exclude_id else 0),  # Get extra if excluding one
            [entity_type]
        )
        
        # Filter out excluded ID
        if exclude_id:
            filtered_results = [
                r for r in search_response.results 
                if r.id != exclude_id
            ][:limit]
        else:
            filtered_results = search_response.results
        
        return SearchResponse(
            results=filtered_results,
            total_results=len(filtered_results),
            query_embedding_tokens=search_response.query_embedding_tokens,
            search_time_ms=search_response.search_time_ms,
            mode="similarity"
        )
