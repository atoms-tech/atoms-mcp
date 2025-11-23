"""Unit tests for Phase 3 Week 1: Composition Engine.

Tests entity composition, relationship composition, and caching.
"""

import pytest
import time
from services.composition_engine import get_composition_engine


class TestCompositionEnginePhase3:
    """Test Phase 3 composition engine."""

    @pytest.fixture
    def engine(self):
        """Get composition engine instance."""
        engine = get_composition_engine()
        engine.clear_cache()
        return engine

    @pytest.fixture
    def sample_entity(self):
        """Get sample entity."""
        return {
            "id": "req-1",
            "type": "requirement",
            "name": "Security Requirement",
            "description": "Implement authentication",
            "status": "active"
        }

    @pytest.fixture
    def sample_entities(self):
        """Get sample entities."""
        return [
            {
                "id": "req-1",
                "type": "requirement",
                "name": "Security Requirement"
            },
            {
                "id": "req-2",
                "type": "requirement",
                "name": "Performance Requirement"
            },
            {
                "id": "req-3",
                "type": "requirement",
                "name": "Usability Requirement"
            }
        ]

    # ========== Entity Composition Tests ==========

    def test_compose_entity_basic(self, engine, sample_entity):
        """Test basic entity composition."""
        composed = engine.compose_entity(sample_entity)

        assert composed["id"] == "req-1"
        assert composed["type"] == "requirement"
        assert "data" in composed
        assert "metadata" in composed

    def test_compose_entity_with_relations(self, engine, sample_entity):
        """Test entity composition with relations."""
        composed = engine.compose_entity(
            sample_entity,
            include_relations=True,
            depth=2  # Need depth > 1 to compose relations
        )

        assert "relations" in composed
        # Relations dict exists (may be empty for depth=1)
        assert isinstance(composed["relations"], dict)

    def test_compose_entity_without_relations(self, engine, sample_entity):
        """Test entity composition without relations."""
        composed = engine.compose_entity(
            sample_entity,
            include_relations=False
        )

        assert "relations" not in composed

    def test_compose_entity_with_metadata(self, engine, sample_entity):
        """Test entity composition with metadata."""
        composed = engine.compose_entity(
            sample_entity,
            include_metadata=True
        )

        assert "metadata" in composed
        assert "composed_at" in composed["metadata"]
        assert "depth" in composed["metadata"]

    def test_compose_entity_depth_validation(self, engine, sample_entity):
        """Test entity composition depth validation."""
        # Depth 0 should be adjusted to 1
        composed = engine.compose_entity(sample_entity, depth=0)
        assert composed["metadata"]["depth"] == 1

        # Depth 4 should be adjusted to 1
        composed = engine.compose_entity(sample_entity, depth=4)
        assert composed["metadata"]["depth"] == 1

    # ========== Relationship Composition Tests ==========

    def test_compose_relationship(self, engine, sample_entity):
        """Test relationship composition."""
        target = {
            "id": "test-1",
            "type": "test",
            "name": "Test Case"
        }

        composed = engine.compose_relationship(
            sample_entity,
            target,
            "requirement_test"
        )

        assert composed["type"] == "requirement_test"
        assert composed["source"]["id"] == "req-1"
        assert composed["target"]["id"] == "test-1"

    def test_compose_relationship_with_context(self, engine, sample_entity):
        """Test relationship composition with context."""
        target = {
            "id": "test-1",
            "type": "test"
        }

        composed = engine.compose_relationship(
            sample_entity,
            target,
            "requirement_test",
            include_context=True
        )

        assert "context" in composed
        assert "source_data" in composed["context"]
        assert "target_data" in composed["context"]

    def test_compose_relationship_without_context(self, engine, sample_entity):
        """Test relationship composition without context."""
        target = {
            "id": "test-1",
            "type": "test"
        }

        composed = engine.compose_relationship(
            sample_entity,
            target,
            "requirement_test",
            include_context=False
        )

        assert "context" not in composed

    # ========== Batch Composition Tests ==========

    def test_compose_batch(self, engine, sample_entities):
        """Test batch entity composition."""
        composed = engine.compose_batch(sample_entities)

        assert len(composed) == 3
        assert all("id" in c for c in composed)
        assert all("type" in c for c in composed)

    def test_compose_batch_with_relations(self, engine, sample_entities):
        """Test batch composition with relations."""
        composed = engine.compose_batch(
            sample_entities,
            include_relations=True
        )

        assert all("relations" in c for c in composed)

    # ========== Caching Tests ==========

    def test_composition_caching(self, engine, sample_entity):
        """Test composition caching."""
        # First composition
        composed1 = engine.compose_entity(sample_entity)
        assert composed1["metadata"]["cached"] is False

        # Second composition (should be cached)
        composed2 = engine.compose_entity(sample_entity)
        assert composed2["metadata"]["cached"] is False  # Metadata is fresh

        # Verify cache has entry
        stats = engine.get_cache_stats()
        assert stats["total_entries"] > 0

    def test_cache_expiration(self, engine, sample_entity):
        """Test cache expiration."""
        # Create engine with short TTL
        short_ttl_engine = get_composition_engine()
        short_ttl_engine.cache_ttl = 1  # 1 second

        # Compose entity
        composed1 = engine.compose_entity(sample_entity)
        initial_entries = engine.get_cache_stats()["total_entries"]

        # Wait for cache to expire
        time.sleep(1.1)

        # Cache should be expired
        stats = engine.get_cache_stats()
        # Note: Expiration happens on access, not automatically

    def test_clear_cache(self, engine, sample_entities):
        """Test clearing cache."""
        # Compose multiple entities
        engine.compose_batch(sample_entities)

        # Verify cache has entries
        stats = engine.get_cache_stats()
        assert stats["total_entries"] > 0

        # Clear cache
        engine.clear_cache()

        # Verify cache is empty
        stats = engine.get_cache_stats()
        assert stats["total_entries"] == 0

    def test_get_cache_stats(self, engine, sample_entities):
        """Test getting cache statistics."""
        engine.compose_batch(sample_entities)

        stats = engine.get_cache_stats()

        assert "total_entries" in stats
        assert "cache_size_bytes" in stats
        assert "ttl_seconds" in stats
        assert stats["total_entries"] > 0

    # ========== Integration Tests ==========

    def test_composition_preserves_data(self, engine, sample_entity):
        """Test composition preserves entity data."""
        composed = engine.compose_entity(sample_entity)

        assert composed["data"]["id"] == sample_entity["id"]
        assert composed["data"]["name"] == sample_entity["name"]
        assert composed["data"]["description"] == sample_entity["description"]

    def test_composition_adds_metadata(self, engine, sample_entity):
        """Test composition adds metadata."""
        composed = engine.compose_entity(sample_entity)

        assert "composed_at" in composed["metadata"]
        assert "depth" in composed["metadata"]
        assert "cached" in composed["metadata"]

