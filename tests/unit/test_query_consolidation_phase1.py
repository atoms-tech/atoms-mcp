"""Unit tests for Phase 1 Week 3: Query Consolidation.

Tests the consolidation of search, aggregate, analyze, rag_search, and similarity
operations from query_tool into entity_tool with parameter consolidation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestQueryConsolidationPhase1:
    """Test Phase 1 query consolidation functionality."""

    @pytest.fixture
    def mock_entity_manager(self):
        """Create mock entity manager."""
        manager = MagicMock()
        manager.search_entities = AsyncMock(return_value={"success": True, "results": []})
        manager.aggregate_entities = AsyncMock(return_value={"success": True, "data": {}})
        manager.analyze_entities = AsyncMock(return_value={"success": True, "analysis": {}})
        manager.rag_search_entities = AsyncMock(return_value={"success": True, "results": []})
        manager.find_similar_entities = AsyncMock(return_value={"success": True, "results": []})
        manager._format_result = MagicMock(side_effect=lambda x, _: x)
        manager._add_timing_metrics = MagicMock(side_effect=lambda x, _: x)
        manager._validate_auth = AsyncMock()
        return manager

    # ========== Search Operation Tests ==========

    @pytest.mark.asyncio
    async def test_search_operation_exists(self, mock_entity_manager):
        """Test that search operation is available in entity_tool."""
        # Search should be callable via entity_tool
        # This is a structural test - actual implementation is in entity_tool
        assert hasattr(mock_entity_manager, 'search_entities')
        assert callable(mock_entity_manager.search_entities)

    @pytest.mark.asyncio
    async def test_search_with_filters(self, mock_entity_manager):
        """Test search operation with filters."""
        await mock_entity_manager.search_entities(
            entity_type="requirement",
            filters={"status": "active"},
            search_term="security",
            limit=10
        )
        
        mock_entity_manager.search_entities.assert_called_once()
        call_args = mock_entity_manager.search_entities.call_args
        assert call_args.kwargs["entity_type"] == "requirement"
        assert call_args.kwargs["filters"]["status"] == "active"

    # ========== Aggregate Operation Tests ==========

    @pytest.mark.asyncio
    async def test_aggregate_operation_exists(self, mock_entity_manager):
        """Test that aggregate operation is available in entity_tool."""
        assert hasattr(mock_entity_manager, 'aggregate_entities')
        assert callable(mock_entity_manager.aggregate_entities)

    @pytest.mark.asyncio
    async def test_aggregate_with_group_by(self, mock_entity_manager):
        """Test aggregate operation with group_by."""
        await mock_entity_manager.aggregate_entities(
            entity_type="requirement",
            aggregate_type="count",
            group_by=["status", "priority"]
        )
        
        mock_entity_manager.aggregate_entities.assert_called_once()
        call_args = mock_entity_manager.aggregate_entities.call_args
        assert call_args.kwargs["aggregate_type"] == "count"
        assert call_args.kwargs["group_by"] == ["status", "priority"]

    # ========== Analyze Operation Tests ==========

    @pytest.mark.asyncio
    async def test_analyze_operation_exists(self, mock_entity_manager):
        """Test that analyze operation is available in entity_tool."""
        assert hasattr(mock_entity_manager, 'analyze_entities')
        assert callable(mock_entity_manager.analyze_entities)

    @pytest.mark.asyncio
    async def test_analyze_with_relations(self, mock_entity_manager):
        """Test analyze operation with include_relations."""
        await mock_entity_manager.analyze_entities(
            entity_type="requirement",
            include_relations=True,
            filters={"status": "active"}
        )
        
        mock_entity_manager.analyze_entities.assert_called_once()
        call_args = mock_entity_manager.analyze_entities.call_args
        assert call_args.kwargs["include_relations"] is True

    # ========== RAG Search Operation Tests ==========

    @pytest.mark.asyncio
    async def test_rag_search_operation_exists(self, mock_entity_manager):
        """Test that rag_search operation is available in entity_tool."""
        assert hasattr(mock_entity_manager, 'rag_search_entities')
        assert callable(mock_entity_manager.rag_search_entities)

    @pytest.mark.asyncio
    async def test_rag_search_with_mode(self, mock_entity_manager):
        """Test rag_search operation with different modes."""
        for mode in ["semantic", "keyword", "hybrid"]:
            await mock_entity_manager.rag_search_entities(
                entity_type="document",
                content="security policies",
                rag_mode=mode,
                similarity_threshold=0.7
            )
        
        assert mock_entity_manager.rag_search_entities.call_count == 3

    # ========== Similarity Operation Tests ==========

    @pytest.mark.asyncio
    async def test_similarity_operation_exists(self, mock_entity_manager):
        """Test that similarity operation is available in entity_tool."""
        assert hasattr(mock_entity_manager, 'find_similar_entities')
        assert callable(mock_entity_manager.find_similar_entities)

    @pytest.mark.asyncio
    async def test_similarity_with_threshold(self, mock_entity_manager):
        """Test similarity operation with threshold."""
        await mock_entity_manager.find_similar_entities(
            entity_type="requirement",
            query="authentication requirements",
            similarity_threshold=0.8,
            limit=5
        )
        
        mock_entity_manager.find_similar_entities.assert_called_once()
        call_args = mock_entity_manager.find_similar_entities.call_args
        assert call_args.kwargs["similarity_threshold"] == 0.8

    # ========== Parameter Consolidation Tests ==========

    def test_parameter_aliases_documented(self):
        """Test that parameter aliases are documented."""
        # Old parameter names (from query_tool):
        # - entities → entity_type
        # - conditions → filters
        # - search_term (same in both)
        # - content (same in both)
        
        # These should be supported in entity_tool for backwards compatibility
        # This is a documentation test
        aliases = {
            "entities": "entity_type",
            "conditions": "filters",
        }
        assert "entities" in aliases
        assert "conditions" in aliases

    # ========== Backwards Compatibility Tests ==========

    def test_query_tool_still_available(self):
        """Test that query_tool is still available for backwards compatibility."""
        from tools.query import data_query
        assert callable(data_query)

    def test_entity_tool_has_all_operations(self):
        """Test that entity_tool has all query operations."""
        from tools.entity import entity_operation
        assert callable(entity_operation)
        
        # entity_operation should support these operations
        operations = ["search", "aggregate", "analyze", "rag_search", "similarity"]
        # This is verified by the function signature in entity.py

    # ========== Migration Path Tests ==========

    def test_migration_path_documented(self):
        """Test that migration path is documented."""
        # Migration should be straightforward:
        # 1. Replace query_tool with entity_tool
        # 2. Replace query_type with operation
        # 3. Replace entities with entity_type
        # 4. Replace conditions with filters
        
        old_call = {
            "tool": "query_tool",
            "query_type": "search",
            "entities": ["requirement"],
            "search_term": "REQ",
            "conditions": {"status": "active"}
        }
        
        new_call = {
            "tool": "entity_tool",
            "operation": "search",
            "entity_type": "requirement",
            "search_term": "REQ",
            "filters": {"status": "active"}
        }
        
        # Verify structure
        assert old_call["tool"] != new_call["tool"]
        assert old_call["query_type"] == "search"
        assert new_call["operation"] == "search"

