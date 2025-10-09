"""Data query and exploration tool with RAG capabilities."""

from __future__ import annotations

import os
import asyncio
from typing import Dict, Any, List, Optional, Literal

try:
    from .base import ToolBase
except ImportError:
    from tools.base import ToolBase

from schemas.enums import QueryType, RAGMode
from schemas.constants import Tables, ENTITY_TABLE_MAP, TABLES_WITHOUT_SOFT_DELETE
from schemas.rls import (
    PermissionDeniedError,
    OrganizationPolicy,
    ProjectPolicy,
    DocumentPolicy,
    RequirementPolicy,
    TestPolicy,
    ProfilePolicy,
)


class DataQueryEngine(ToolBase):
    """Advanced data querying and analysis engine with RAG capabilities."""

    def __init__(self):
        super().__init__()
        self._embedding_service = None
        self._vector_search_service = None

    def _get_policy_for_table(self, table: str):
        """Get RLS policy validator for a table."""
        user_id = self._get_user_id()
        if not user_id:
            return None

        adapters = self._get_adapters()
        db_adapter = adapters["database"]

        policy_map = {
            Tables.ORGANIZATIONS: OrganizationPolicy(user_id, db_adapter),
            Tables.PROJECTS: ProjectPolicy(user_id, db_adapter),
            Tables.DOCUMENTS: DocumentPolicy(user_id, db_adapter),
            Tables.REQUIREMENTS: RequirementPolicy(user_id, db_adapter),
            Tables.TEST_REQ: TestPolicy(user_id, db_adapter),
            Tables.PROFILES: ProfilePolicy(user_id, db_adapter),
        }
        return policy_map.get(table)

    async def _filter_results_by_rls(self, results: List[Dict[str, Any]], table: str) -> List[Dict[str, Any]]:
        """Filter results based on RLS policies."""
        policy = self._get_policy_for_table(table)
        if not policy:
            # No policy defined, return all results (tables without RLS policies)
            return results

        filtered_results = []
        for record in results:
            try:
                # Check if user can select this record
                await policy.validate_select(record)
                filtered_results.append(record)
            except PermissionDeniedError:
                # User can't see this record, skip it silently
                continue

        return filtered_results

    def _init_rag_services(self):
        """Initialize RAG services on first use."""
        if self._embedding_service is None:
            from config.vector import (
                get_embedding_service,
                get_enhanced_vector_search_service,
            )
            self._embedding_service = get_embedding_service()
            self._vector_search_service = get_enhanced_vector_search_service(self.supabase)
    
    async def _search_query(
        self,
        entities: List[str],
        search_term: str,
        conditions: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform cross-entity search with parallel execution."""

        async def search_entity(entity_type: str):
            """Search a single entity type."""
            try:
                table = self._resolve_entity_table(entity_type)

                # Build search filters
                filters = conditions.copy() if conditions else {}

                # Add search term
                if search_term:
                    filters["name"] = {"ilike": f"%{search_term}%"}

                # Add default filters
                if "is_deleted" not in filters and table not in TABLES_WITHOUT_SOFT_DELETE:
                    filters["is_deleted"] = False

                # Execute search
                entity_results = await self._db_query(
                    table,
                    filters=filters,
                    limit=limit or 10,
                    order_by="updated_at:desc"
                )

                # Filter results through RLS
                filtered_results = await self._filter_results_by_rls(entity_results, table)

                # Sanitize results
                sanitized_results = [self._sanitize_entity(r) for r in filtered_results]

                return (entity_type, {
                    "count": len(sanitized_results),
                    "results": sanitized_results
                })

            except Exception as e:
                return (entity_type, {
                    "error": str(e),
                    "count": 0,
                    "results": []
                })

        # Execute all searches in parallel
        search_tasks = [search_entity(et) for et in entities]
        search_results = await asyncio.gather(*search_tasks)

        # Convert to dict
        results = dict(search_results)

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
        """Perform aggregation queries across entities with parallel execution."""

        async def aggregate_entity(entity_type: str):
            """Aggregate a single entity type."""
            try:
                table = self._resolve_entity_table(entity_type)
                filters = conditions.copy() if conditions else {}

                # Add default filters
                if "is_deleted" not in filters and table not in TABLES_WITHOUT_SOFT_DELETE:
                    filters["is_deleted"] = False

                # Parallel execution of count queries
                from datetime import datetime, timedelta
                thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
                recent_filters = filters.copy()
                recent_filters["created_at"] = {"gte": thirty_days_ago}

                # Execute counts in parallel
                count_tasks = [
                    self._db_count(table, filters),  # total
                    self._db_count(table, recent_filters) if filters else asyncio.sleep(0)  # recent
                ]

                # Add status query if applicable
                if entity_type in ["requirement", "test", "project"]:
                    count_tasks.append(self._db_query(table, select="status", filters=filters))

                count_results = await asyncio.gather(*count_tasks, return_exceptions=True)

                total_count = count_results[0] if not isinstance(count_results[0], Exception) else 0
                recent_count = count_results[1] if len(count_results) > 1 and not isinstance(count_results[1], Exception) else 0

                # Status breakdown
                status_breakdown = {}
                if len(count_results) > 2 and not isinstance(count_results[2], Exception):
                    for record in count_results[2]:
                        status = record.get("status", "unknown")
                        status_breakdown[status] = status_breakdown.get(status, 0) + 1

                return (entity_type, {
                    "total_count": total_count,
                    "recent_count": recent_count,
                    "status_breakdown": status_breakdown
                })

            except Exception as e:
                return (entity_type, {
                    "error": str(e),
                    "total_count": 0
                })

        # Execute all aggregations in parallel
        agg_tasks = [aggregate_entity(et) for et in entities]
        agg_results = await asyncio.gather(*agg_tasks)

        # Convert to dict
        results = dict(agg_results)

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
        """Perform deep analysis of entities and their relationships with full parallelization."""

        async def analyze_entity(entity_type: str):
            try:
                table = self._resolve_entity_table(entity_type)
                filters = conditions.copy() if conditions else {}

                # Add default filters (skip for tables without is_deleted column)
                if "is_deleted" not in filters and table not in TABLES_WITHOUT_SOFT_DELETE:
                    filters["is_deleted"] = False
                
                # Basic metrics
                total_count = await self._db_count(table, filters)
                
                # Entity-specific analysis
                if entity_type == "organization":
                    # Analyze organization metrics with parallel queries
                    all_orgs = await self._db_query(table, filters=filters)
                    # Filter organizations through RLS
                    orgs = await self._filter_results_by_rls(all_orgs, table)

                    # Parallelize all member/project count queries
                    async def get_org_stats(org):
                        member_task = self._db_count(
                            Tables.ORGANIZATION_MEMBERS,
                            {"organization_id": org["id"], "status": "active"}
                        )
                        project_task = self._db_count(
                            Tables.PROJECTS,
                            {"organization_id": org["id"], "is_deleted": False}
                        )
                        return await asyncio.gather(member_task, project_task, return_exceptions=True)

                    org_stats_tasks = [get_org_stats(org) for org in orgs]
                    all_org_stats = await asyncio.gather(*org_stats_tasks)

                    member_counts = [stats[0] for stats in all_org_stats if not isinstance(stats[0], Exception)]
                    project_counts = [stats[1] for stats in all_org_stats if len(stats) > 1 and not isinstance(stats[1], Exception)]
                    
                    return (entity_type, {
                        "total_organizations": total_count,
                        "avg_members_per_org": sum(member_counts) / len(member_counts) if member_counts else 0,
                        "avg_projects_per_org": sum(project_counts) / len(project_counts) if project_counts else 0,
                        "member_distribution": {
                            "min": min(member_counts) if member_counts else 0,
                            "max": max(member_counts) if member_counts else 0
                        }
                    })

                elif entity_type == "project":
                    # Analyze project metrics with massive parallelization
                    all_projects = await self._db_query(table, filters=filters)
                    # Filter projects through RLS
                    projects = await self._filter_results_by_rls(all_projects, table)

                    async def get_project_stats(project):
                        """Get all stats for a single project in parallel."""
                        # Get documents first
                        docs = await self._db_query(
                            Tables.DOCUMENTS,
                            select="id",
                            filters={"project_id": project["id"], "is_deleted": False}
                        )

                        # Count documents and all requirements in parallel
                        doc_count = len(docs)
                        req_tasks = [
                            self._db_count(Tables.REQUIREMENTS, {"document_id": doc["id"], "is_deleted": False})
                            for doc in docs
                        ]

                        req_counts = await asyncio.gather(*req_tasks, return_exceptions=True)
                        total_reqs = sum(c for c in req_counts if not isinstance(c, Exception))

                        return (doc_count, total_reqs)

                    # Execute all project analyses in parallel
                    project_tasks = [get_project_stats(p) for p in projects]
                    all_project_stats = await asyncio.gather(*project_tasks)

                    doc_counts = [stats[0] for stats in all_project_stats]
                    req_counts = [stats[1] for stats in all_project_stats]

                    return (entity_type, {
                        "total_projects": total_count,
                        "avg_documents_per_project": sum(doc_counts) / len(doc_counts) if doc_counts else 0,
                        "avg_requirements_per_project": sum(req_counts) / len(req_counts) if req_counts else 0,
                        "complexity_distribution": {
                            "simple": len([c for c in req_counts if c < 10]),
                            "medium": len([c for c in req_counts if 10 <= c < 50]),
                            "complex": len([c for c in req_counts if c >= 50])
                        }
                    })

                elif entity_type == "requirement":
                    # Analyze requirements
                    all_reqs = await self._db_query(table, filters=filters, select="status, priority")
                    # Filter requirements through RLS
                    reqs = await self._filter_results_by_rls(all_reqs, table)

                    status_counts = {}
                    priority_counts = {}

                    for req in reqs:
                        status = req.get("status", "unknown")
                        priority = req.get("priority", "unknown")

                        status_counts[status] = status_counts.get(status, 0) + 1
                        priority_counts[priority] = priority_counts.get(priority, 0) + 1

                    # Get test coverage
                    total_reqs = len(reqs)
                    tested_reqs = await self._db_count(Tables.REQUIREMENT_TESTS)
                    coverage_percentage = (tested_reqs / total_reqs * 100) if total_reqs > 0 else 0

                    return (entity_type, {
                        "total_requirements": total_count,
                        "status_distribution": status_counts,
                        "priority_distribution": priority_counts,
                        "test_coverage": {
                            "tested_requirements": tested_reqs,
                            "coverage_percentage": round(coverage_percentage, 2)
                        }
                    })
                
                else:
                    # Basic analysis for other entity types
                    return (entity_type, {
                        "total_count": total_count,
                        "analysis": "basic_metrics_only"
                    })

            except Exception as e:
                return (entity_type, {
                    "error": str(e),
                    "total_count": 0
                })

        # Execute all analyses in parallel
        analysis_tasks = [analyze_entity(et) for et in entities]
        analysis_results = await asyncio.gather(*analysis_tasks)

        # Convert to dict
        analysis = dict(analysis_results)

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
            Tables.ORGANIZATION_MEMBERS,
            Tables.PROJECT_MEMBERS,
            Tables.TRACE_LINKS,
            Tables.ASSIGNMENTS,
            Tables.REQUIREMENT_TESTS
        ]

        for rel_table in relationship_tables:
            try:
                filters = conditions.copy() if conditions else {}

                # Add default filters (most relationship tables have is_deleted, but check just in case)
                # Currently all relationship tables have soft-delete, but being defensive
                if "is_deleted" not in filters and rel_table not in TABLES_WITHOUT_SOFT_DELETE:
                    filters["is_deleted"] = False

                count = await self._db_count(rel_table, filters)

                if count > 0:
                    # Special handling for requirement_tests to avoid JSON serialization issues
                    select_fields = "*"
                    if rel_table == Tables.REQUIREMENT_TESTS:
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
        if mode == RAGMode.AUTO.value:
            # Simple heuristic: use semantic for longer queries, keyword for short/specific terms
            if len(query.split()) >= 3:
                mode = RAGMode.SEMANTIC.value
            else:
                mode = RAGMode.KEYWORD.value

        try:
            # Perform the appropriate search
            if mode == RAGMode.SEMANTIC.value:
                search_response = await self._vector_search_service.semantic_search(
                    query=query,
                    similarity_threshold=similarity_threshold,
                    limit=limit,
                    entity_types=entities,
                    filters=conditions
                )
            elif mode == RAGMode.KEYWORD.value:
                search_response = await self._vector_search_service.keyword_search(
                    query=query,
                    limit=limit,
                    entity_types=entities,
                    filters=conditions
                )
            elif mode == RAGMode.HYBRID.value:
                search_response = await self._vector_search_service.hybrid_search(
                    query=query,
                    similarity_threshold=similarity_threshold,
                    limit=limit,
                    entity_types=entities,
                    filters=conditions
                )
            else:
                raise ValueError(f"Unsupported search mode: {mode}")
            
            # Format results and filter through RLS
            formatted_results = []
            for result in search_response.results:
                # Get the table for this entity type
                entity_type = result.entity_type
                table = self._resolve_entity_table(entity_type) if entity_type else None

                # Check RLS permissions if we have a table
                if table:
                    policy = self._get_policy_for_table(table)
                    if policy:
                        try:
                            # Validate user can select this result
                            await policy.validate_select(result.metadata)
                        except PermissionDeniedError:
                            # User can't see this record, skip it
                            continue

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
                "total_results": len(formatted_results),  # Update count after filtering
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
            
            # Format results and filter through RLS
            table = self._resolve_entity_table(entity_type)
            policy = self._get_policy_for_table(table) if table else None

            formatted_results = []
            for result in search_response.results:
                # Check RLS permissions
                if policy:
                    try:
                        await policy.validate_select(result.metadata)
                    except PermissionDeniedError:
                        # User can't see this record, skip it
                        continue

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
                "total_results": len(formatted_results),  # Update count after filtering
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
        if query_type == QueryType.SEARCH.value:
            if not search_term:
                raise ValueError("search_term is required for search queries")
            result = await _query_engine._search_query(
                valid_entities, search_term, conditions, limit
            )

        elif query_type == QueryType.AGGREGATE.value:
            result = await _query_engine._aggregate_query(
                valid_entities, conditions, projections
            )

        elif query_type == QueryType.ANALYZE.value:
            result = await _query_engine._analyze_query(
                valid_entities, conditions
            )

        elif query_type == QueryType.RELATIONSHIPS.value:
            result = await _query_engine._relationship_query(
                valid_entities, conditions
            )

        elif query_type == QueryType.RAG_SEARCH.value:
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

        elif query_type == QueryType.SIMILARITY.value:
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
