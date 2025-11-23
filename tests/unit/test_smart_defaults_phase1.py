"""Unit tests for Phase 1 Week 4: Smart Defaults & Error Handling.

Tests fuzzy matching, batch context, pagination state, and operation history.
"""

import pytest
from services.fuzzy_matcher import FuzzyMatcher
from services.context_manager import get_context


class TestFuzzyMatcherPhase1:
    """Test fuzzy matching for error suggestions."""

    def test_exact_match(self):
        """Test exact string matching."""
        ratio = FuzzyMatcher.similarity_ratio("requirement-123", "requirement-123")
        assert ratio == 1.0

    def test_case_insensitive_match(self):
        """Test case-insensitive matching."""
        ratio = FuzzyMatcher.similarity_ratio("Requirement-123", "requirement-123")
        assert ratio == 1.0

    def test_partial_match(self):
        """Test partial string matching."""
        ratio = FuzzyMatcher.similarity_ratio("req-123", "requirement-123")
        assert 0.5 < ratio < 1.0

    def test_no_match(self):
        """Test non-matching strings."""
        ratio = FuzzyMatcher.similarity_ratio("abc", "xyz")
        assert ratio < 0.5

    def test_find_similar_strings(self):
        """Test finding similar strings from candidates."""
        candidates = ["requirement-1", "requirement-2", "requirement-3", "project-1"]
        matches = FuzzyMatcher.find_similar("requirement-123", candidates, threshold=0.6)
        
        assert len(matches) > 0
        assert matches[0][0].startswith("requirement")
        assert matches[0][1] > 0.6

    def test_find_similar_entities(self):
        """Test finding similar entities by ID or name."""
        entities = [
            {"id": "req-1", "name": "Security Requirement"},
            {"id": "req-2", "name": "Performance Requirement"},
            {"id": "proj-1", "name": "My Project"}
        ]
        
        suggestions = FuzzyMatcher.find_similar_entities(
            "req-123",
            entities,
            threshold=0.5,
            limit=2
        )
        
        assert len(suggestions) > 0
        assert suggestions[0]["entity"]["id"].startswith("req")

    def test_format_suggestions(self):
        """Test formatting suggestions for display."""
        suggestions = [
            {
                "entity": {"id": "req-1", "name": "Security Requirement"},
                "field": "id",
                "matched_value": "req-1",
                "similarity": 0.95
            }
        ]
        
        formatted = FuzzyMatcher.format_suggestions("req-123", suggestions)
        
        assert len(formatted) == 1
        assert "Security Requirement" in formatted[0]
        assert "95%" in formatted[0]


class TestSmartDefaultsPhase1:
    """Test smart defaults and batch context."""

    @pytest.fixture
    def context(self):
        """Get global context instance."""
        ctx = get_context()
        ctx.clear()
        return ctx

    # ========== Batch Context Tests ==========

    def test_record_operation(self, context):
        """Test recording operations."""
        result = {"success": True, "entity_id": "req-1", "data": {"name": "Test"}}
        context.record_operation("create", "requirement", result)
        
        history = context.get_operation_history()
        assert len(history) == 1
        assert history[0]["operation"] == "create"
        assert history[0]["entity_type"] == "requirement"

    def test_get_last_created_entity(self, context):
        """Test getting last created entity."""
        result = {"success": True, "entity_id": "req-1", "data": {"name": "Test"}}
        context.record_operation("create", "requirement", result)
        
        last = context.get_last_created_entity("requirement")
        assert last is not None
        assert last["id"] == "req-1"

    def test_last_created_entity_by_type(self, context):
        """Test tracking last created entity per type."""
        # Create requirement
        req_result = {"success": True, "entity_id": "req-1", "data": {"name": "Req"}}
        context.record_operation("create", "requirement", req_result)
        
        # Create test
        test_result = {"success": True, "entity_id": "test-1", "data": {"name": "Test"}}
        context.record_operation("create", "test", test_result)
        
        # Verify both are tracked
        assert context.get_last_created_entity("requirement")["id"] == "req-1"
        assert context.get_last_created_entity("test")["id"] == "test-1"

    # ========== Pagination State Tests ==========

    def test_set_pagination_state(self, context):
        """Test setting pagination state."""
        context.set_pagination_state("requirement", limit=20, offset=0, total=100)
        
        state = context.get_pagination_state("requirement")
        assert state is not None
        assert state["limit"] == 20
        assert state["offset"] == 0
        assert state["total"] == 100

    def test_pagination_has_next(self, context):
        """Test pagination has_next flag."""
        context.set_pagination_state("requirement", limit=20, offset=0, total=100)
        
        state = context.get_pagination_state("requirement")
        assert state["has_next"] is True
        assert state["has_previous"] is False

    def test_pagination_has_previous(self, context):
        """Test pagination has_previous flag."""
        context.set_pagination_state("requirement", limit=20, offset=40, total=100)
        
        state = context.get_pagination_state("requirement")
        assert state["has_next"] is True
        assert state["has_previous"] is True

    def test_get_next_page_offset(self, context):
        """Test getting next page offset."""
        context.set_pagination_state("requirement", limit=20, offset=0, total=100)
        
        next_offset = context.get_next_page_offset("requirement")
        assert next_offset == 20

    def test_get_next_page_offset_last_page(self, context):
        """Test getting next page offset on last page."""
        context.set_pagination_state("requirement", limit=20, offset=80, total=100)
        
        next_offset = context.get_next_page_offset("requirement")
        assert next_offset is None

    # ========== Operation History Tests ==========

    def test_operation_history_limit(self, context):
        """Test operation history is limited to 50."""
        # Record 60 operations
        for i in range(60):
            result = {"success": True, "entity_id": f"req-{i}", "data": {}}
            context.record_operation("create", "requirement", result)
        
        history = context.get_operation_history()
        assert len(history) <= 50

    def test_operation_history_order(self, context):
        """Test operation history maintains order."""
        for i in range(5):
            result = {"success": True, "entity_id": f"req-{i}", "data": {}}
            context.record_operation("create", "requirement", result)
        
        history = context.get_operation_history()
        assert history[0]["entity_id"] == "req-0"
        assert history[-1]["entity_id"] == "req-4"

    def test_get_operation_history_limit(self, context):
        """Test getting limited operation history."""
        for i in range(10):
            result = {"success": True, "entity_id": f"req-{i}", "data": {}}
            context.record_operation("create", "requirement", result)
        
        history = context.get_operation_history(limit=5)
        assert len(history) == 5
        assert history[0]["entity_id"] == "req-5"

