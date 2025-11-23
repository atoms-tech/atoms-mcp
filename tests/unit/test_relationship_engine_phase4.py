"""Unit tests for Phase 4 Week 1: Relationship Engine.

Tests relationship traversal, dependency graphs, impact analysis, and
circular dependency detection.
"""

import pytest
from services.relationship_engine import get_relationship_engine


class TestRelationshipEnginePhase4:
    """Test Phase 4 relationship engine."""

    @pytest.fixture
    def engine(self):
        """Get relationship engine instance."""
        engine = get_relationship_engine()
        engine.relationships.clear()
        engine.dependency_cache.clear()
        return engine

    # ========== Relationship Addition Tests ==========

    def test_add_relationship(self, engine):
        """Test adding relationship."""
        engine.add_relationship("req-1", "req-2", "depends_on")

        assert "req-1" in engine.relationships
        assert len(engine.relationships["req-1"]) == 1

    def test_add_multiple_relationships(self, engine):
        """Test adding multiple relationships."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-1", "req-3", "depends_on")
        engine.add_relationship("req-2", "req-4", "depends_on")

        assert len(engine.relationships["req-1"]) == 2
        assert len(engine.relationships["req-2"]) == 1

    def test_add_relationship_with_metadata(self, engine):
        """Test adding relationship with metadata."""
        metadata = {"priority": "high", "status": "active"}
        engine.add_relationship("req-1", "req-2", "depends_on", metadata)

        rel = engine.relationships["req-1"][0]
        assert rel["metadata"] == metadata

    # ========== Traversal Tests ==========

    def test_traverse_relationships_single_level(self, engine):
        """Test traversing relationships at single level."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-1", "req-3", "depends_on")

        result = engine.traverse_relationships("req-1", depth=1)

        assert result["root"] == "req-1"
        assert "req-1" in result["nodes"]
        assert len(result["edges"]) == 2

    def test_traverse_relationships_multiple_levels(self, engine):
        """Test traversing relationships at multiple levels."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-2", "req-3", "depends_on")
        engine.add_relationship("req-3", "req-4", "depends_on")

        result = engine.traverse_relationships("req-1", depth=3)

        assert len(result["nodes"]) == 4
        assert len(result["edges"]) == 3

    def test_traverse_relationships_with_filter(self, engine):
        """Test traversing relationships with type filter."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-1", "req-3", "conflicts_with")

        result = engine.traverse_relationships(
            "req-1",
            depth=1,
            relationship_type="depends_on"
        )

        assert len(result["edges"]) == 1
        assert result["edges"][0]["type"] == "depends_on"

    # ========== Dependency Graph Tests ==========

    def test_build_dependency_graph(self, engine):
        """Test building dependency graph."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-1", "req-3", "depends_on")

        graph = engine.build_dependency_graph("req-1")

        assert graph["root"] == "req-1"
        assert "req-2" in graph["dependencies"]
        assert "req-3" in graph["dependencies"]

    def test_build_dependency_graph_caching(self, engine):
        """Test dependency graph caching."""
        engine.add_relationship("req-1", "req-2", "depends_on")

        graph1 = engine.build_dependency_graph("req-1")
        graph2 = engine.build_dependency_graph("req-1")

        assert graph1 is graph2  # Same object (cached)

    # ========== Impact Analysis Tests ==========

    def test_analyze_impact_no_dependents(self, engine):
        """Test impact analysis with no dependents."""
        engine.add_relationship("req-1", "req-2", "depends_on")

        impact = engine.analyze_impact("req-2")

        assert impact["entity_id"] == "req-2"
        assert impact["impact_level"] == "low"
        assert impact["risk_score"] == 0.0

    def test_analyze_impact_with_dependents(self, engine):
        """Test impact analysis with dependents."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-3", "req-2", "depends_on")

        impact = engine.analyze_impact("req-2")

        assert len(impact["affected_entities"]) == 2
        assert impact["impact_level"] == "medium"

    def test_analyze_impact_high_level(self, engine):
        """Test impact analysis with high impact."""
        # Create many dependents
        for i in range(25):
            engine.add_relationship(f"req-{i}", "req-2", "depends_on")

        impact = engine.analyze_impact("req-2")

        assert impact["impact_level"] == "critical"

    # ========== Circular Dependency Tests ==========

    def test_detect_no_circular_dependencies(self, engine):
        """Test detecting no circular dependencies."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-2", "req-3", "depends_on")

        cycles = engine.detect_circular_dependencies()

        assert len(cycles) == 0

    def test_detect_simple_circular_dependency(self, engine):
        """Test detecting simple circular dependency."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-2", "req-1", "depends_on")

        cycles = engine.detect_circular_dependencies()

        assert len(cycles) > 0

    def test_detect_complex_circular_dependency(self, engine):
        """Test detecting complex circular dependency."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-2", "req-3", "depends_on")
        engine.add_relationship("req-3", "req-1", "depends_on")

        cycles = engine.detect_circular_dependencies()

        assert len(cycles) > 0

    # ========== Related Entities Tests ==========

    def test_get_related_entities(self, engine):
        """Test getting related entities."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-1", "req-3", "depends_on")

        related = engine.get_related_entities("req-1")

        assert len(related) == 2
        assert any(r["id"] == "req-2" for r in related)
        assert any(r["id"] == "req-3" for r in related)

    def test_get_related_entities_with_filter(self, engine):
        """Test getting related entities with type filter."""
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-1", "req-3", "conflicts_with")

        related = engine.get_related_entities("req-1", "depends_on")

        assert len(related) == 1
        assert related[0]["id"] == "req-2"

    # ========== Complex Scenario Tests ==========

    def test_complex_dependency_chain(self, engine):
        """Test complex dependency chain."""
        # System -> Module -> Component -> Implementation
        engine.add_relationship("sys-1", "mod-1", "contains")
        engine.add_relationship("mod-1", "comp-1", "contains")
        engine.add_relationship("comp-1", "impl-1", "implements")

        result = engine.traverse_relationships("sys-1", depth=4)

        assert len(result["nodes"]) == 4
        assert len(result["edges"]) == 3

    def test_multiple_dependency_paths(self, engine):
        """Test multiple dependency paths."""
        # req-1 depends on req-2 and req-3
        # req-2 depends on req-4
        # req-3 depends on req-4
        engine.add_relationship("req-1", "req-2", "depends_on")
        engine.add_relationship("req-1", "req-3", "depends_on")
        engine.add_relationship("req-2", "req-4", "depends_on")
        engine.add_relationship("req-3", "req-4", "depends_on")

        graph = engine.build_dependency_graph("req-1")

        assert "req-2" in graph["dependencies"]
        assert "req-3" in graph["dependencies"]
        assert "req-4" in graph["dependencies"]

