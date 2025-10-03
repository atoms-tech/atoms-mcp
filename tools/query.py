"""Data query and exploration tool with RAG capabilities."""

from __future__ import annotations

import os
from typing import Dict, Any, List, Optional, Literal

try:
    from .base import ToolBase
except ImportError:
    from tools.base import ToolBase


class DataQueryEngine(ToolBase):
    """Advanced data querying and analysis engine with RAG capabilities."""

    def __init__(self):
        super().__init__()
        self._embedding_service = None
        self._vector_search_service = None

    
    def _init_rag_services(self):
        """Initialize RAG services on first use."""
        if self._embedding_service is None:
            from services.embedding_factory import get_embedding_service
            from services.enhanced_vector_search import EnhancedVectorSearchService

            # Get the embedding service (Vertex AI with gemini-embedding-001 only)
            self._embedding_service = get_embedding_service()
            self._vector_search_service = EnhancedVectorSearchService(self.supabase, self._embedding_service)
    
    async def _search_query(
        self,
        entities: List[str],
        search_term: str,
        conditions: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform cross-entity search."""
        results = {}
        
        for entity_type in entities:
            try:
                table = self._resolve_entity_table(entity_type)
                
                # Build search filters
                filters = conditions.copy() if conditions else {}
                
                # Add search term (simplified - in practice would use full-text search)
                if search_term:
                    filters["name"] = {"ilike": f"%{search_term}%"}
                
                # Add default filters
                if "is_deleted" not in filters:
                    filters["is_deleted"] = False
                
                # Execute search
                entity_results = await self._db_query(
                    table,
                    filters=filters,
                    limit=limit or 10,
                    order_by="updated_at:desc"
                )

                # Sanitize results to prevent token overflow
                sanitized_results = []
                for result in entity_results:
                    sanitized_results.append(self._sanitize_entity(result))

                results[entity_type] = {
                    "count": len(entity_results),
                    "results": sanitized_results
                }
                
            except Exception as e:
                results[entity_type] = {
                    "error": str(e),
                    "count": 0,
                    "results": []
                }
        
        return {
            "search_term": search_term,
            "entities_searched": entities,
            "total_results": sum(r.get("count", 0) for r in results.values()),
            "results_by_entity": results
        }
    
    async def _aggregate_query(
        self,
        entities: List[str],
        conditions: Optional[Dict[str, Any]] = None,
        projections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Perform aggregation queries across entities."""
        results = {}
        
        for entity_type in entities:
            try:
                table = self._resolve_entity_table(entity_type)
                filters = conditions.copy() if conditions else {}
                
                # Add default filters
                if "is_deleted" not in filters:
                    filters["is_deleted"] = False
                
                # Get total count
                total_count = await self._db_count(table, filters)
                
                # Get status breakdown if entity has status field
                status_breakdown = {}
                if entity_type in ["requirement", "test", "project"]:
                    # This is simplified - would need proper aggregation queries
                    all_records = await self._db_query(
                        table,
                        select="status",
                        filters=filters
                    )
                    for record in all_records:
                        status = record.get("status", "unknown")
                        status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                # Get date-based aggregations
                recent_count = 0
                if total_count > 0:
                    # Count created in last 30 days
                    from datetime import datetime, timedelta
                    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
                    recent_filters = filters.copy()
                    recent_filters["created_at"] = {"gte": thirty_days_ago}
                    recent_count = await self._db_count(table, recent_filters)
                
                results[entity_type] = {
                    "total_count": total_count,
                    "recent_count": recent_count,
                    "status_breakdown": status_breakdown
                }
                
            except Exception as e:
                results[entity_type] = {
                    "error": str(e),
                    "total_count": 0
                }
        
        return {
            "aggregation_type": "summary_stats",
            "entities_analyzed": entities,
            "results": results
        }
    
    async def _analyze_query(
        self,
        entities: List[str],
        conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform deep analysis of entities and their relationships."""
        analysis = {}
        
        for entity_type in entities:
            try:
                table = self._resolve_entity_table(entity_type)
                filters = conditions.copy() if conditions else {}
                
                if "is_deleted" not in filters:
                    filters["is_deleted"] = False
                
                # Basic metrics
                total_count = await self._db_count(table, filters)
                
                # Entity-specific analysis
                if entity_type == "organization":
                    # Analyze organization metrics
                    orgs = await self._db_query(table, filters=filters)
                    
                    member_counts = []
                    project_counts = []
                    
                    for org in orgs:
                        # Get member count
                        member_count = await self._db_count(
                            "organization_members",
                            {"organization_id": org["id"], "status": "active"}
                        )
                        member_counts.append(member_count)
                        
                        # Get project count
                        project_count = await self._db_count(
                            "projects",
                            {"organization_id": org["id"], "is_deleted": False}
                        )
                        project_counts.append(project_count)
                    
                    analysis[entity_type] = {
                        "total_organizations": total_count,
                        "avg_members_per_org": sum(member_counts) / len(member_counts) if member_counts else 0,
                        "avg_projects_per_org": sum(project_counts) / len(project_counts) if project_counts else 0,
                        "member_distribution": {
                            "min": min(member_counts) if member_counts else 0,
                            "max": max(member_counts) if member_counts else 0
                        }
                    }
                
                elif entity_type == "project":
                    # Analyze project metrics
                    projects = await self._db_query(table, filters=filters)
                    
                    doc_counts = []
                    req_counts = []
                    
                    for project in projects:
                        # Get document count
                        doc_count = await self._db_count(
                            "documents",
                            {"project_id": project["id"], "is_deleted": False}
                        )
                        doc_counts.append(doc_count)
                        
                        # Get requirement count (through documents)
                        docs = await self._db_query(
                            "documents",
                            select="id",
                            filters={"project_id": project["id"], "is_deleted": False}
                        )
                        
                        project_req_count = 0
                        for doc in docs:
                            req_count = await self._db_count(
                                "requirements",
                                {"document_id": doc["id"], "is_deleted": False}
                            )
                            project_req_count += req_count
                        
                        req_counts.append(project_req_count)
                    
                    analysis[entity_type] = {
                        "total_projects": total_count,
                        "avg_documents_per_project": sum(doc_counts) / len(doc_counts) if doc_counts else 0,
                        "avg_requirements_per_project": sum(req_counts) / len(req_counts) if req_counts else 0,
                        "complexity_distribution": {
                            "simple": len([c for c in req_counts if c < 10]),
                            "medium": len([c for c in req_counts if 10 <= c < 50]),
                            "complex": len([c for c in req_counts if c >= 50])
                        }
                    }
                
                elif entity_type == "requirement":
                    # Analyze requirements
                    reqs = await self._db_query(table, filters=filters, select="status, priority")
                    
                    status_counts = {}
                    priority_counts = {}
                    
                    for req in reqs:
                        status = req.get("status", "unknown")
                        priority = req.get("priority", "unknown")
                        
                        status_counts[status] = status_counts.get(status, 0) + 1
                        priority_counts[priority] = priority_counts.get(priority, 0) + 1
                    
                    # Get test coverage
                    total_reqs = len(reqs)
                    tested_reqs = await self._db_count("requirement_tests")
                    coverage_percentage = (tested_reqs / total_reqs * 100) if total_reqs > 0 else 0
                    
                    analysis[entity_type] = {
                        "total_requirements": total_count,
                        "status_distribution": status_counts,
                        "priority_distribution": priority_counts,
                        "test_coverage": {
                            "tested_requirements": tested_reqs,
                            "coverage_percentage": round(coverage_percentage, 2)
                        }
                    }
                
                else:
                    # Basic analysis for other entity types
                    analysis[entity_type] = {
                        "total_count": total_count,
                        "analysis": "basic_metrics_only"
                    }
                    
            except Exception as e:
                analysis[entity_type] = {
                    "error": str(e),
                    "total_count": 0
                }
        
        return {
            "analysis_type": "deep_analysis",
            "entities_analyzed": entities,
            "analysis": analysis
        }
    
    async def _relationship_query(
        self,
        entities: List[str],
        conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze relationships between entities."""
        relationships = {}
        
        # Analyze common relationship patterns
        relationship_tables = [
            "organization_members",
            "project_members", 
            "trace_links",
            "assignments",
            "requirement_tests"
        ]
        
        for rel_table in relationship_tables:
            try:
                filters = conditions.copy() if conditions else {}

                # Add default filters
                if "is_deleted" not in filters:
                    filters["is_deleted"] = False

                count = await self._db_count(rel_table, filters)

                if count > 0:
                    # Special handling for requirement_tests to avoid JSON serialization issues
                    select_fields = "*"
                    if rel_table == "requirement_tests":
                        # Select only basic fields, avoid problematic columns
                        select_fields = "id,requirement_id,test_id,relationship_type,coverage_level,created_at,updated_at,created_by,is_deleted"

                    # Get sample relationships for analysis
                    samples = await self._db_query(
                        rel_table,
                        select=select_fields,
                        filters=filters,
                        limit=10,
                        order_by="created_at:desc"
                    )

                    relationships[rel_table] = {
                        "total_count": count,
                        "recent_samples": samples
                    }

            except Exception as e:
                # Gracefully handle errors - don't fail entire query
                relationships[rel_table] = {
                    "error": f"INTERNAL_SERVER_ERROR: {str(e)}",
                    "total_count": 0
                }
        
        return {
            "query_type": "relationship_analysis",
            "relationship_tables": relationship_tables,
            "relationships": relationships
        }
    
    async def _rag_search_query(
        self,
        query: str,
        mode: Literal["semantic", "keyword", "hybrid", "auto"] = "auto",
        entities: Optional[List[str]] = None,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform RAG-enabled search across entities."""
        self._init_rag_services()
        
        # Auto-detect search mode if needed
        if mode == "auto":
            # Simple heuristic: use semantic for longer queries, keyword for short/specific terms
            if len(query.split()) >= 3:
                mode = "semantic"
            else:
                mode = "keyword"
        
        try:
            # Perform the appropriate search
            if mode == "semantic":
                search_response = await self._vector_search_service.semantic_search(
                    query=query,
                    similarity_threshold=similarity_threshold,
                    limit=limit,
                    entity_types=entities,
                    filters=conditions
                )
            elif mode == "keyword":
                search_response = await self._vector_search_service.keyword_search(
                    query=query,
                    limit=limit,
                    entity_types=entities,
                    filters=conditions
                )
            elif mode == "hybrid":
                search_response = await self._vector_search_service.hybrid_search(
                    query=query,
                    similarity_threshold=similarity_threshold,
                    limit=limit,
                    entity_types=entities,
                    filters=conditions
                )
            else:
                raise ValueError(f"Unsupported search mode: {mode}")
            
            # Format results for consistent API
            formatted_results = []
            for result in search_response.results:
                formatted_results.append({
                    "id": result.id,
                    "entity_type": result.entity_type,
                    "content": result.content,
                    "similarity_score": result.similarity,
                    "metadata": self._sanitize_entity(result.metadata)
                })
            
            return {
                "search_type": "rag_search",
                "query": query,
                "mode": search_response.mode,
                "total_results": search_response.total_results,
                "results": formatted_results,
                "query_embedding_tokens": search_response.query_embedding_tokens,
                "search_time_ms": search_response.search_time_ms,
                "entities_searched": entities or ["all"]
            }
            
        except Exception as e:
            return {
                "search_type": "rag_search",
                "query": query,
                "mode": mode,
                "error": str(e),
                "total_results": 0,
                "results": []
            }
    
    async def _similarity_analysis(
        self,
        content: str,
        entity_type: str,
        similarity_threshold: float = 0.8,
        limit: int = 5,
        exclude_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find content similar to the provided text."""
        self._init_rag_services()
        
        try:
            search_response = await self._vector_search_service.similarity_search_by_content(
                content=content,
                entity_type=entity_type,
                similarity_threshold=similarity_threshold,
                limit=limit,
                exclude_id=exclude_id
            )
            
            # Format results
            formatted_results = []
            for result in search_response.results:
                formatted_results.append({
                    "id": result.id,
                    "entity_type": result.entity_type,
                    "content": result.content,
                    "similarity_score": result.similarity,
                    "metadata": result.metadata
                })
            
            return {
                "analysis_type": "similarity_analysis",
                "source_content": content[:200] + "..." if len(content) > 200 else content,
                "entity_type": entity_type,
                "total_results": search_response.total_results,
                "results": formatted_results,
                "query_embedding_tokens": search_response.query_embedding_tokens,
                "search_time_ms": search_response.search_time_ms
            }
            
        except Exception as e:
            return {
                "analysis_type": "similarity_analysis",
                "source_content": content[:200] + "..." if len(content) > 200 else content,
                "entity_type": entity_type,
                "error": str(e),
                "total_results": 0,
                "results": []
            }


# Global query engine instance
_query_engine = DataQueryEngine()


async def data_query(
    auth_token: str,
    query_type: Literal["search", "aggregate", "analyze", "relationships", "rag_search", "similarity"],
    entities: List[str],
    conditions: Optional[Dict[str, Any]] = None,
    projections: Optional[List[str]] = None,
    search_term: Optional[str] = None,
    limit: Optional[int] = None,
    format_type: str = "detailed",
    # RAG-specific parameters
    rag_mode: Literal["semantic", "keyword", "hybrid", "auto"] = "auto",
    similarity_threshold: float = 0.7,
    content: Optional[str] = None,
    entity_type: Optional[str] = None,
    exclude_id: Optional[str] = None
) -> Dict[str, Any]:
    """Query and analyze data across multiple entity types with RAG capabilities.
    
    Args:
        auth_token: Authentication token
        query_type: Type of query to perform (search, aggregate, analyze, relationships, rag_search, similarity)
        entities: List of entity types to query
        conditions: Filter conditions to apply
        projections: Specific fields to include (for aggregate queries)
        search_term: Text search term (for search and rag_search queries)
        limit: Maximum results per entity
        format_type: Result format (detailed, summary, raw)
        rag_mode: RAG search mode (semantic, keyword, hybrid, auto)
        similarity_threshold: Minimum similarity score for RAG searches (0-1)
        content: Content text for similarity analysis
        entity_type: Entity type for similarity analysis
        exclude_id: ID to exclude from similarity results
    
    Returns:
        Dict containing query results and analysis
    """
    try:
        # Validate authentication
        await _query_engine._validate_auth(auth_token)
        
        # Validate entity types
        valid_entities = []
        for entity in entities:
            try:
                _query_engine._resolve_entity_table(entity)
                valid_entities.append(entity)
            except ValueError:
                # Skip invalid entity types
                pass
        
        if not valid_entities:
            raise ValueError("No valid entity types provided")
        
        # Execute query based on type
        if query_type == "search":
            if not search_term:
                raise ValueError("search_term is required for search queries")
            result = await _query_engine._search_query(
                valid_entities, search_term, conditions, limit
            )
        
        elif query_type == "aggregate":
            result = await _query_engine._aggregate_query(
                valid_entities, conditions, projections
            )
        
        elif query_type == "analyze":
            result = await _query_engine._analyze_query(
                valid_entities, conditions
            )
        
        elif query_type == "relationships":
            result = await _query_engine._relationship_query(
                valid_entities, conditions
            )
        
        elif query_type == "rag_search":
            if not search_term:
                raise ValueError("search_term is required for rag_search queries")
            result = await _query_engine._rag_search_query(
                query=search_term,
                mode=rag_mode,
                entities=valid_entities,
                similarity_threshold=similarity_threshold,
                limit=limit,
                conditions=conditions
            )
        
        elif query_type == "similarity":
            if not content:
                raise ValueError("content is required for similarity queries")

            # Accept both entity_type (singular) and entities (array) for flexibility
            target_entity_type = entity_type
            if not target_entity_type and valid_entities:
                # Use first valid entity from entities array
                target_entity_type = valid_entities[0]

            if not target_entity_type:
                raise ValueError("entity_type (singular) or entities (array) is required for similarity queries")

            result = await _query_engine._similarity_analysis(
                content=content,
                entity_type=target_entity_type,
                similarity_threshold=similarity_threshold,
                limit=limit,
                exclude_id=exclude_id
            )
        
        else:
            raise ValueError(f"Unknown query type: {query_type}")
        
        return _query_engine._format_result(result, format_type)
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query_type": query_type,
            "entities": entities
        }
