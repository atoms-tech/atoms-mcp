"""Unit tests for Phase 3 Week 3: Advanced Search.

Tests advanced search filters, full-text search, and search optimization.
"""

import pytest
from services.advanced_search import get_advanced_search


class TestAdvancedSearchPhase3:
    """Test Phase 3 advanced search."""

    @pytest.fixture
    def search_engine(self):
        """Get advanced search instance."""
        return get_advanced_search()

    @pytest.fixture
    def sample_entities(self):
        """Get sample entities."""
        return [
            {
                "id": "req-1",
                "type": "requirement",
                "name": "Security Authentication",
                "description": "Implement user authentication",
                "status": "active",
                "priority": "high"
            },
            {
                "id": "req-2",
                "type": "requirement",
                "name": "Performance Optimization",
                "description": "Optimize database queries",
                "status": "active",
                "priority": "medium"
            },
            {
                "id": "req-3",
                "type": "requirement",
                "name": "User Interface Design",
                "description": "Design responsive UI",
                "status": "completed",
                "priority": "high"
            },
            {
                "id": "req-4",
                "type": "requirement",
                "name": "API Documentation",
                "description": "Document REST API",
                "status": "pending",
                "priority": "low"
            }
        ]

    # ========== Full-Text Search Tests ==========

    def test_full_text_search_basic(self, search_engine, sample_entities):
        """Test basic full-text search."""
        results = search_engine.full_text_search(sample_entities, "Security")

        assert len(results) == 1
        assert results[0]["id"] == "req-1"

    def test_full_text_search_case_insensitive(self, search_engine, sample_entities):
        """Test case-insensitive full-text search."""
        results = search_engine.full_text_search(
            sample_entities,
            "security",
            case_sensitive=False
        )

        assert len(results) == 1

    def test_full_text_search_case_sensitive(self, search_engine, sample_entities):
        """Test case-sensitive full-text search."""
        results = search_engine.full_text_search(
            sample_entities,
            "security",
            case_sensitive=True
        )

        assert len(results) == 0

    def test_full_text_search_multiple_results(self, search_engine, sample_entities):
        """Test full-text search with multiple results."""
        results = search_engine.full_text_search(sample_entities, "Design")

        assert len(results) >= 1

    def test_full_text_search_specific_fields(self, search_engine, sample_entities):
        """Test full-text search on specific fields."""
        results = search_engine.full_text_search(
            sample_entities,
            "authentication",
            fields=["description"]
        )

        assert len(results) == 1

    # ========== Filter Search Tests ==========

    def test_filter_search_single_filter(self, search_engine, sample_entities):
        """Test filter search with single filter."""
        filters = {"status": "active"}
        results = search_engine.filter_search(sample_entities, filters)

        assert len(results) == 2
        assert all(r["status"] == "active" for r in results)

    def test_filter_search_multiple_filters(self, search_engine, sample_entities):
        """Test filter search with multiple filters."""
        filters = {"status": "active", "priority": "high"}
        results = search_engine.filter_search(sample_entities, filters)

        assert len(results) == 1
        assert results[0]["id"] == "req-1"

    def test_filter_search_list_value(self, search_engine, sample_entities):
        """Test filter search with list value."""
        filters = {"status": ["active", "completed"]}
        results = search_engine.filter_search(sample_entities, filters)

        assert len(results) == 3

    def test_filter_search_range(self, search_engine):
        """Test filter search with range."""
        entities = [
            {"id": "1", "value": 10},
            {"id": "2", "value": 20},
            {"id": "3", "value": 30}
        ]

        filters = {"value": {"min": 15, "max": 25}}
        results = search_engine.filter_search(entities, filters)

        assert len(results) == 1
        assert results[0]["id"] == "2"

    # ========== Combined Search Tests ==========

    def test_combined_search_query_only(self, search_engine, sample_entities):
        """Test combined search with query only."""
        result = search_engine.combined_search(
            sample_entities,
            query="Security"
        )

        assert result["total"] == 1
        assert len(result["results"]) == 1

    def test_combined_search_filters_only(self, search_engine, sample_entities):
        """Test combined search with filters only."""
        result = search_engine.combined_search(
            sample_entities,
            filters={"status": "active"}
        )

        assert result["total"] == 2

    def test_combined_search_query_and_filters(self, search_engine, sample_entities):
        """Test combined search with query and filters."""
        result = search_engine.combined_search(
            sample_entities,
            query="Design",
            filters={"status": "completed"}
        )

        assert result["total"] == 1

    def test_combined_search_pagination(self, search_engine, sample_entities):
        """Test combined search pagination."""
        result = search_engine.combined_search(
            sample_entities,
            limit=2,
            offset=0
        )

        assert len(result["results"]) == 2
        assert result["has_next"] is True

    # ========== Faceted Search Tests ==========

    def test_faceted_search(self, search_engine, sample_entities):
        """Test faceted search."""
        result = search_engine.faceted_search(
            sample_entities,
            facet_fields=["status", "priority"]
        )

        assert "facets" in result
        assert "status" in result["facets"]
        assert "priority" in result["facets"]

    def test_faceted_search_with_query(self, search_engine, sample_entities):
        """Test faceted search with query."""
        result = search_engine.faceted_search(
            sample_entities,
            facet_fields=["status"],
            query="requirement"
        )

        assert result["total"] > 0

    # ========== Suggestion Tests ==========

    def test_suggest_basic(self, search_engine, sample_entities):
        """Test basic suggestions."""
        suggestions = search_engine.suggest(
            sample_entities,
            "Security",
            field="name"
        )

        assert len(suggestions) > 0
        assert "Security Authentication" in suggestions

    def test_suggest_case_insensitive(self, search_engine, sample_entities):
        """Test case-insensitive suggestions."""
        suggestions = search_engine.suggest(
            sample_entities,
            "security",
            field="name"
        )

        assert len(suggestions) > 0

    def test_suggest_limit(self, search_engine, sample_entities):
        """Test suggestion limit."""
        suggestions = search_engine.suggest(
            sample_entities,
            "P",
            field="name",
            limit=2
        )

        assert len(suggestions) <= 2

    # ========== Edge Cases ==========

    def test_empty_query(self, search_engine, sample_entities):
        """Test empty query."""
        results = search_engine.full_text_search(sample_entities, "")

        assert len(results) == 0

    def test_no_matches(self, search_engine, sample_entities):
        """Test search with no matches."""
        results = search_engine.full_text_search(sample_entities, "nonexistent")

        assert len(results) == 0

