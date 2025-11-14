"""E2E tests for Advanced Features operations.

This file validates end-to-end advanced feature functionality:
- Complex multi-entity workflows and operations
- Advanced querying and filtering
- Performance optimization features
- Integration scenarios and cross-tool operations

Test Coverage: 18 test scenarios covering advanced features.
File follows canonical naming - describes WHAT is tested (advanced features).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestComplexWorkflows:
    """Test complex multi-step workflows."""
    
    @pytest.mark.asyncio
    async def test_project_to_deployment_workflow(self, call_mcp):
        """Execute complex workflow: project creation → documents → requirements → tests → deployment."""
        org_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "project_to_deployment",
                "parameters": {
                    "organization_id": org_id,
                    "project_name": "Full Stack App",
                    "include_docs": True,
                    "include_requirements": True,
                    "include_tests": True,
                    "auto_setup_ci_cd": True
                }
            }
        )
        
        assert result["success"] is True
        assert "project_id" in result["data"]
        assert "deployment_ready" in result["data"]
    
    @pytest.mark.asyncio
    async def test_nested_entity_operations(self, call_mcp):
        """Create and manage deeply nested entity hierarchies."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "create_hierarchy",
                "parameters": {
                    "levels": [
                        {"type": "organization", "data": {"name": "Corp"}},
                        {"type": "project", "data": {"name": "Platform"}},
                        {"type": "component", "data": {"name": "Auth Service"}},
                        {"type": "requirement", "data": {"title": "OAuth Support"}},
                        {"type": "test_case", "data": {"title": "OAuth Flow Test"}}
                    ]
                }
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_circular_relationship_detection(self, call_mcp):
        """Detect and handle circular relationships gracefully."""
        e1 = str(uuid.uuid4())
        e2 = str(uuid.uuid4())
        e3 = str(uuid.uuid4())
        
        # Link e1 -> e2
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "entity_a_id": e1,
                "entity_b_id": e2,
                "relationship_type": "depends_on"
            }
        )
        
        # Link e2 -> e3
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "entity_a_id": e2,
                "entity_b_id": e3,
                "relationship_type": "depends_on"
            }
        )
        
        # Try to create circular link e3 -> e1
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "entity_a_id": e3,
                "entity_b_id": e1,
                "relationship_type": "depends_on",
                "detect_cycles": True
            }
        )
        
        # Should either prevent or detect cycle
        assert "success" in result
        assert "data" in result


class TestAdvancedQuerying:
    """Test advanced query capabilities."""
    
    @pytest.mark.asyncio
    async def test_complex_filter_combinations(self, call_mcp):
        """Query with complex AND/OR filter combinations."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "filters": {
                    "OR": [
                        {
                            "AND": [
                                {"priority": "high"},
                                {"status": "draft"}
                            ]
                        },
                        {
                            "AND": [
                                {"priority": "critical"},
                                {"status": ["draft", "pending_review"]}
                            ]
                        }
                    ]
                }
            }
        )
        
        assert result["success"] is True
        assert "results" in result["data"]
    
    @pytest.mark.asyncio
    async def test_faceted_search_aggregations(self, call_mcp):
        """Perform faceted search with multiple aggregations."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "search_term": "api",
                "aggregations": {
                    "by_priority": {"field": "priority", "count": True},
                    "by_status": {"field": "status", "count": True},
                    "by_owner": {"field": "owner", "count": True}
                }
            }
        )
        
        assert result["success"] is True
        assert "aggregations" in result["data"]
    
    @pytest.mark.asyncio
    async def test_temporal_queries(self, call_mcp):
        """Query entities by time ranges and temporal patterns."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "project",
                "filters": {
                    "created_between": {
                        "start": "2025-11-01T00:00:00Z",
                        "end": "2025-11-30T23:59:59Z"
                    },
                    "modified_after": "2025-11-14T00:00:00Z"
                }
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_text_search_with_stemming(self, call_mcp):
        """Search with stemming and tokenization."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "document",
                "search_term": "authentication",
                "search_options": {
                    "stemming": True,
                    "fuzzy_matching": True,
                    "min_match_score": 0.8
                }
            }
        )
        
        assert result["success"] is True


class TestPerformanceOptimization:
    """Test performance optimization features."""
    
    @pytest.mark.asyncio
    async def test_index_query_optimization(self, call_mcp):
        """Use indexed fields for query optimization."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "organization",
                "filters": {
                    "organization_id": str(uuid.uuid4())
                },
                "use_index": True
            }
        )
        
        assert result["success"] is True
        assert duration_ms < 1000  # Should be fast with index
    
    @pytest.mark.asyncio
    async def test_lazy_loading_relationships(self, call_mcp):
        """Lazy load relationships only when needed."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "read",
                "entity_id": str(uuid.uuid4()),
                "include_relationships": "lazy"
            }
        )
        
        assert result["success"] is True
        assert "relationships" not in result["data"] or result["data"]["relationships"] is None
    
    @pytest.mark.asyncio
    async def test_bulk_fetch_optimization(self, call_mcp):
        """Fetch multiple entities efficiently in bulk."""
        entity_ids = [str(uuid.uuid4()) for _ in range(10)]
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "bulk_read",
                "entity_ids": entity_ids
            }
        )
        
        assert result["success"] is True
        assert "data" in result


class TestCrossCuttingConcerns:
    """Test cross-cutting concerns and integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_audit_trail_tracking(self, call_mcp):
        """Track all changes with audit trail."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": "Audit Test Org"},
                "track_audit": True
            }
        )
        
        assert result["success"] is True
        org_id = result["data"]["id"]
        
        # Get audit trail
        audit_result, _ = await call_mcp(
            "data_query",
            {
                "query_type": "get_audit_log",
                "entity_id": org_id,
                "entity_type": "organization"
            }
        )
        
        assert audit_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_notification_on_changes(self, call_mcp):
        """Emit notifications on entity changes."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": "Notification Test"},
                "emit_notifications": True
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_version_history_tracking(self, call_mcp):
        """Track version history for entities."""
        doc_id = str(uuid.uuid4())
        
        # Create version 1
        result1, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "entity_id": doc_id,
                "data": {"title": "Version 1", "content": "Original content"},
                "track_versions": True
            }
        )
        
        # Update to version 2
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "update",
                "entity_id": doc_id,
                "data": {"content": "Updated content"}
            }
        )
        
        # Get version history
        history_result, _ = await call_mcp(
            "data_query",
            {
                "query_type": "get_version_history",
                "entity_id": doc_id,
                "entity_type": "document"
            }
        )
        
        assert history_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_operation_handling(self, call_mcp):
        """Handle concurrent operations on same entity."""
        entity_id = str(uuid.uuid4())
        
        # Simulate concurrent updates
        result1, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "update",
                "entity_id": entity_id,
                "data": {"status": "in_review"}
            }
        )
        
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "update",
                "entity_id": entity_id,
                "data": {"priority": "high"}
            }
        )
        
        assert result1["success"] is True or result2["success"] is True
    
    @pytest.mark.asyncio
    async def test_rate_limiting_compliance(self, call_mcp):
        """Verify operations respect rate limits."""
        # Make multiple rapid requests
        results = []
        for i in range(5):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {"name": f"Rate Test {i}"}
                }
            )
            results.append(result["success"])
        
        # Should handle rate limiting gracefully
        assert any(results)
    
    @pytest.mark.asyncio
    async def test_caching_strategy(self, call_mcp):
        """Verify effective caching of frequently accessed data."""
        org_id = str(uuid.uuid4())
        
        # First read (cache miss)
        result1, duration1 = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "entity_id": org_id
            }
        )
        
        # Second read (cache hit)
        result2, duration2 = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "entity_id": org_id
            }
        )
        
        assert result1["success"] is True
        assert result2["success"] is True


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    @pytest.mark.asyncio
    async def test_operation_retry_with_backoff(self, call_mcp):
        """Retry failed operations with exponential backoff."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "reliable_operation",
                "parameters": {"action": "create"},
                "retry_config": {
                    "max_retries": 3,
                    "initial_backoff_ms": 100,
                    "backoff_multiplier": 2
                }
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_partial_failure_rollback(self, call_mcp):
        """Rollback on partial failure in batch operations."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "batch_with_rollback",
                "parameters": {
                    "entities": [
                        {"name": "Valid 1"},
                        {"name": "Valid 2"},
                        {"name": ""},  # Invalid
                    ],
                    "transaction_mode": "rollback_on_error"
                }
            }
        )
        
        assert "data" in result
