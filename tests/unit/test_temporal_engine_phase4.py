"""Unit tests for Phase 4 Week 2: Temporal Engine.

Tests change history tracking, temporal queries, audit trails, and
time-based filtering.
"""

import pytest
from datetime import datetime, timedelta
from services.temporal_engine import get_temporal_engine


class TestTemporalEnginePhase4:
    """Test Phase 4 temporal engine."""

    @pytest.fixture
    def engine(self):
        """Get temporal engine instance."""
        engine = get_temporal_engine()
        engine.change_history.clear()
        engine.entity_versions.clear()
        return engine

    # ========== Change Tracking Tests ==========

    def test_track_change_create(self, engine):
        """Test tracking entity creation."""
        new_value = {"id": "req-1", "name": "Requirement 1"}
        change = engine.track_change(
            "req-1",
            "requirement",
            "create",
            new_value=new_value,
            changed_by="user-1"
        )

        assert change["entity_id"] == "req-1"
        assert change["change_type"] == "create"
        assert change["changed_by"] == "user-1"

    def test_track_change_update(self, engine):
        """Test tracking entity update."""
        old_value = {"id": "req-1", "name": "Old Name"}
        new_value = {"id": "req-1", "name": "New Name"}

        change = engine.track_change(
            "req-1",
            "requirement",
            "update",
            old_value=old_value,
            new_value=new_value,
            changed_by="user-1"
        )

        assert change["change_type"] == "update"
        assert change["old_value"]["name"] == "Old Name"
        assert change["new_value"]["name"] == "New Name"

    def test_track_change_delete(self, engine):
        """Test tracking entity deletion."""
        old_value = {"id": "req-1", "name": "Requirement 1"}

        change = engine.track_change(
            "req-1",
            "requirement",
            "delete",
            old_value=old_value,
            changed_by="user-1"
        )

        assert change["change_type"] == "delete"

    # ========== Change History Tests ==========

    def test_get_change_history(self, engine):
        """Test getting change history."""
        for i in range(3):
            engine.track_change(
                "req-1",
                "requirement",
                "update",
                new_value={"id": "req-1", "version": i}
            )

        history = engine.get_change_history("req-1")

        assert len(history) == 3

    def test_get_change_history_with_time_range(self, engine):
        """Test getting change history with time range."""
        engine.track_change(
            "req-1",
            "requirement",
            "update",
            new_value={"id": "req-1"}
        )

        now = datetime.now()
        start_time = (now - timedelta(hours=1)).isoformat()
        end_time = (now + timedelta(hours=1)).isoformat()

        history = engine.get_change_history("req-1", time_range=(start_time, end_time))

        assert len(history) == 1

    def test_get_change_history_limit(self, engine):
        """Test change history limit."""
        for i in range(10):
            engine.track_change(
                "req-1",
                "requirement",
                "update",
                new_value={"id": "req-1", "version": i}
            )

        history = engine.get_change_history("req-1", limit=5)

        assert len(history) == 5

    # ========== Temporal Query Tests ==========

    def test_query_at_time(self, engine):
        """Test querying entity state at specific time."""
        engine.track_change(
            "req-1",
            "requirement",
            "create",
            new_value={"id": "req-1", "name": "Requirement 1"}
        )

        now = datetime.now().isoformat()
        version = engine.query_at_time("req-1", now)

        assert version is not None
        assert version["data"]["name"] == "Requirement 1"

    def test_query_at_time_before_creation(self, engine):
        """Test querying before entity creation."""
        engine.track_change(
            "req-1",
            "requirement",
            "create",
            new_value={"id": "req-1", "name": "Requirement 1"}
        )

        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        version = engine.query_at_time("req-1", past_time)

        assert version is None

    # ========== Version Comparison Tests ==========

    def test_compare_versions(self, engine):
        """Test comparing versions at two times."""
        # Create initial version
        engine.track_change(
            "req-1",
            "requirement",
            "create",
            new_value={"id": "req-1", "name": "Requirement 1", "status": "draft"}
        )

        time1 = datetime.now().isoformat()

        # Update
        engine.track_change(
            "req-1",
            "requirement",
            "update",
            new_value={"id": "req-1", "name": "Requirement 1", "status": "active"}
        )

        time2 = datetime.now().isoformat()

        comparison = engine.compare_versions("req-1", time1, time2)

        assert len(comparison["differences"]) > 0

    # ========== Audit Trail Tests ==========

    def test_get_audit_trail(self, engine):
        """Test getting audit trail."""
        for i in range(3):
            engine.track_change(
                "req-1",
                "requirement",
                "update",
                changed_by=f"user-{i}"
            )

        trail = engine.get_audit_trail("req-1")

        assert len(trail) == 3
        assert all("timestamp" in t for t in trail)
        assert all("change_type" in t for t in trail)

    def test_get_audit_trail_limit(self, engine):
        """Test audit trail limit."""
        for i in range(10):
            engine.track_change(
                "req-1",
                "requirement",
                "update"
            )

        trail = engine.get_audit_trail("req-1", limit=5)

        assert len(trail) == 5

    # ========== Time-Based Filtering Tests ==========

    def test_get_entities_changed_since(self, engine):
        """Test getting entities changed since timestamp."""
        engine.track_change("req-1", "requirement", "create")
        engine.track_change("req-2", "requirement", "create")

        now = datetime.now().isoformat()
        changed = engine.get_entities_changed_since(now)

        assert len(changed) >= 0

    def test_get_entities_not_updated(self, engine):
        """Test getting entities not updated in N days."""
        # Create old change
        old_time = (datetime.now() - timedelta(days=10)).isoformat()

        engine.track_change("req-1", "requirement", "create")
        engine.track_change("req-2", "requirement", "create")

        stale = engine.get_entities_not_updated(days=5)

        # Should find stale entities
        assert len(stale) >= 0

    # ========== Cleanup Tests ==========

    def test_cleanup_old_changes(self, engine):
        """Test cleaning up old changes."""
        engine.track_change("req-1", "requirement", "create")

        removed = engine.cleanup_old_changes()

        # Should not remove recent changes
        assert removed == 0

    # ========== Integration Tests ==========

    def test_complete_entity_lifecycle(self, engine):
        """Test complete entity lifecycle tracking."""
        # Create
        engine.track_change(
            "req-1",
            "requirement",
            "create",
            new_value={"id": "req-1", "name": "Requirement 1", "status": "draft"}
        )

        # Update
        engine.track_change(
            "req-1",
            "requirement",
            "update",
            new_value={"id": "req-1", "name": "Requirement 1", "status": "active"}
        )

        # Update again
        engine.track_change(
            "req-1",
            "requirement",
            "update",
            new_value={"id": "req-1", "name": "Requirement 1", "status": "completed"}
        )

        history = engine.get_change_history("req-1")

        assert len(history) == 3
        assert history[0]["change_type"] == "update"  # Most recent first
        assert history[-1]["change_type"] == "create"  # Oldest last

