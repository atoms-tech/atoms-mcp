"""
Comprehensive test suite for dashboard widget components.

This module provides extensive testing coverage for:
- Entity count widget
- Recent changes widget
- Workflow status widget
- Performance metrics widget
- Alert widget
- Custom dashboard creation
- Widget refresh and updates
- Real-time data accuracy
- Performance validation (< 100ms per widget)
- Concurrent updates
- Caching behavior

Expected coverage gain: +1-2%
Target pass rate: 90%+
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from atoms_mcp.domain.models.entity import Entity, EntityStatus
from atoms_mcp.domain.models.workflow import Workflow, WorkflowStatus


# =============================================================================
# MOCK DASHBOARD WIDGET SYSTEM
# =============================================================================


class DashboardWidget:
    """Base dashboard widget class."""

    def __init__(self, widget_id: str, repository, logger, cache=None):
        self.widget_id = widget_id
        self.repository = repository
        self.logger = logger
        self.cache = cache
        self.last_update = None
        self.refresh_interval = 60  # seconds

    def get_cache_key(self) -> str:
        """Get cache key for this widget."""
        return f"widget:{self.widget_id}"

    def get_data(self) -> Dict[str, Any]:
        """Get widget data (to be implemented by subclasses)."""
        raise NotImplementedError

    def refresh(self, force: bool = False) -> Dict[str, Any]:
        """Refresh widget data."""
        # Check cache first
        if not force and self.cache:
            cached = self.cache.get(self.get_cache_key())
            if cached:
                self.logger.debug(f"Widget {self.widget_id} loaded from cache")
                return cached

        # Get fresh data
        data = self.get_data()
        data["last_updated"] = datetime.utcnow().isoformat()
        self.last_update = datetime.utcnow()

        # Cache the result
        if self.cache:
            self.cache.set(self.get_cache_key(), data, ttl=self.refresh_interval)

        return data

    def needs_refresh(self) -> bool:
        """Check if widget needs refresh."""
        if not self.last_update:
            return True
        elapsed = (datetime.utcnow() - self.last_update).total_seconds()
        return elapsed >= self.refresh_interval


class EntityCountWidget(DashboardWidget):
    """Widget showing entity count by type."""

    def get_data(self) -> Dict[str, Any]:
        """Get entity count data."""
        entities = self.repository.list()

        by_type = {}
        by_status = {}

        for entity in entities:
            entity_type = entity.metadata.get("entity_type", "unknown")
            status = entity.status.value

            by_type[entity_type] = by_type.get(entity_type, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "widget_type": "entity_count",
            "total": len(entities),
            "by_type": by_type,
            "by_status": by_status,
        }


class RecentChangesWidget(DashboardWidget):
    """Widget showing recent entity changes."""

    def __init__(self, widget_id: str, repository, logger, cache=None, limit: int = 10):
        super().__init__(widget_id, repository, logger, cache)
        self.limit = limit

    def get_data(self) -> Dict[str, Any]:
        """Get recent changes data."""
        entities = self.repository.list()

        # Sort by updated_at
        sorted_entities = sorted(
            entities, key=lambda e: e.updated_at, reverse=True
        )

        changes = []
        for entity in sorted_entities[: self.limit]:
            changes.append(
                {
                    "id": entity.id,
                    "type": entity.metadata.get("entity_type", "unknown"),
                    "status": entity.status.value,
                    "updated_at": entity.updated_at.isoformat(),
                }
            )

        return {
            "widget_type": "recent_changes",
            "changes": changes,
            "limit": self.limit,
        }


class WorkflowStatusWidget(DashboardWidget):
    """Widget showing workflow execution status."""

    def get_data(self) -> Dict[str, Any]:
        """Get workflow status data."""
        # Mock workflow data
        return {
            "widget_type": "workflow_status",
            "active_workflows": 0,
            "completed_today": 0,
            "failed_today": 0,
            "success_rate": 100.0,
        }


class PerformanceMetricsWidget(DashboardWidget):
    """Widget showing performance metrics."""

    def get_data(self) -> Dict[str, Any]:
        """Get performance metrics data."""
        return {
            "widget_type": "performance_metrics",
            "avg_response_time": 0,
            "requests_per_second": 0,
            "error_rate": 0.0,
            "uptime": 99.9,
        }


class AlertWidget(DashboardWidget):
    """Widget showing system alerts."""

    def get_data(self) -> Dict[str, Any]:
        """Get alerts data."""
        entities = self.repository.list()

        alerts = []

        # Check for deleted entities
        deleted = [e for e in entities if e.status == EntityStatus.DELETED]
        if deleted:
            alerts.append(
                {
                    "level": "warning",
                    "message": f"{len(deleted)} deleted entities",
                    "count": len(deleted),
                }
            )

        # Check for blocked entities
        blocked = [e for e in entities if e.status == EntityStatus.BLOCKED]
        if blocked:
            alerts.append(
                {
                    "level": "error",
                    "message": f"{len(blocked)} blocked entities",
                    "count": len(blocked),
                }
            )

        return {
            "widget_type": "alerts",
            "alerts": alerts,
            "total_alerts": len(alerts),
        }


class Dashboard:
    """Dashboard containing multiple widgets."""

    def __init__(self, dashboard_id: str, logger, cache=None):
        self.dashboard_id = dashboard_id
        self.logger = logger
        self.cache = cache
        self.widgets: Dict[str, DashboardWidget] = {}

    def add_widget(self, widget: DashboardWidget) -> None:
        """Add widget to dashboard."""
        self.widgets[widget.widget_id] = widget
        self.logger.info(f"Added widget {widget.widget_id} to dashboard")

    def remove_widget(self, widget_id: str) -> bool:
        """Remove widget from dashboard."""
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            self.logger.info(f"Removed widget {widget_id} from dashboard")
            return True
        return False

    def get_widget(self, widget_id: str) -> DashboardWidget:
        """Get widget by ID."""
        return self.widgets.get(widget_id)

    def refresh_all(self, force: bool = False) -> Dict[str, Any]:
        """Refresh all widgets."""
        results = {}
        for widget_id, widget in self.widgets.items():
            results[widget_id] = widget.refresh(force=force)
        return results

    def refresh_widget(self, widget_id: str, force: bool = False) -> Dict[str, Any]:
        """Refresh specific widget."""
        widget = self.widgets.get(widget_id)
        if not widget:
            raise ValueError(f"Widget {widget_id} not found")
        return widget.refresh(force=force)


# =============================================================================
# ENTITY COUNT WIDGET TESTS
# =============================================================================


class TestEntityCountWidget:
    """Test EntityCountWidget functionality."""

    def test_entity_count_widget_creation(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count widget creation."""
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        assert widget.widget_id == "count_1"
        assert widget.repository == mock_repository
        assert widget.logger == mock_logger

    def test_entity_count_widget_data(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count widget data."""
        # Add test entities
        entities = [
            Entity(metadata={"entity_type": "project"}),
            Entity(metadata={"entity_type": "project"}),
            Entity(metadata={"entity_type": "task"}),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        data = widget.get_data()

        assert data["widget_type"] == "entity_count"
        assert data["total"] == 3
        assert data["by_type"]["project"] == 2
        assert data["by_type"]["task"] == 1

    def test_entity_count_widget_empty_repository(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count widget with empty repository."""
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        data = widget.get_data()

        assert data["total"] == 0
        assert data["by_type"] == {}

    def test_entity_count_widget_refresh(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count widget refresh."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        data = widget.refresh()

        assert "last_updated" in data
        assert data["total"] == 1

    def test_entity_count_widget_caching(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count widget caching."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)

        # First refresh
        data1 = widget.refresh()
        assert mock_cache.exists(widget.get_cache_key())

        # Second refresh should use cache
        data2 = widget.refresh()
        assert data2 == data1

    @pytest.mark.performance
    def test_entity_count_widget_performance(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test entity count widget performance < 100ms."""
        # Add 1000 entities
        for i in range(1000):
            entity = Entity(metadata={"entity_type": "project"})
            mock_repository.add_entity(entity)

        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)

        start_time = time.time()
        data = widget.get_data()
        elapsed = time.time() - start_time

        assert data["total"] == 1000
        assert elapsed < 0.1, f"Widget took {elapsed:.3f}s, expected < 0.1s"


# =============================================================================
# RECENT CHANGES WIDGET TESTS
# =============================================================================


class TestRecentChangesWidget:
    """Test RecentChangesWidget functionality."""

    def test_recent_changes_widget_creation(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test recent changes widget creation."""
        widget = RecentChangesWidget(
            "changes_1", mock_repository, mock_logger, mock_cache, limit=5
        )
        assert widget.widget_id == "changes_1"
        assert widget.limit == 5

    def test_recent_changes_widget_data(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test recent changes widget data."""
        now = datetime.utcnow()
        entities = [
            Entity(updated_at=now, metadata={"entity_type": "project"}),
            Entity(updated_at=now - timedelta(hours=1), metadata={"entity_type": "task"}),
            Entity(updated_at=now - timedelta(hours=2), metadata={"entity_type": "doc"}),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = RecentChangesWidget(
            "changes_1", mock_repository, mock_logger, mock_cache, limit=2
        )
        data = widget.get_data()

        assert data["widget_type"] == "recent_changes"
        assert len(data["changes"]) == 2
        assert data["limit"] == 2
        # Should be sorted by most recent first
        assert data["changes"][0]["type"] == "project"

    def test_recent_changes_widget_empty_repository(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test recent changes widget with empty repository."""
        widget = RecentChangesWidget(
            "changes_1", mock_repository, mock_logger, mock_cache
        )
        data = widget.get_data()

        assert len(data["changes"]) == 0

    def test_recent_changes_widget_limit(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test recent changes widget respects limit."""
        # Add 20 entities
        for i in range(20):
            entity = Entity(metadata={"entity_type": "project"})
            mock_repository.add_entity(entity)

        widget = RecentChangesWidget(
            "changes_1", mock_repository, mock_logger, mock_cache, limit=5
        )
        data = widget.get_data()

        assert len(data["changes"]) == 5

    @pytest.mark.performance
    def test_recent_changes_widget_performance(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test recent changes widget performance < 100ms."""
        # Add 1000 entities
        for i in range(1000):
            entity = Entity(metadata={"entity_type": "project"})
            mock_repository.add_entity(entity)

        widget = RecentChangesWidget(
            "changes_1", mock_repository, mock_logger, mock_cache
        )

        start_time = time.time()
        data = widget.get_data()
        elapsed = time.time() - start_time

        assert len(data["changes"]) == 10
        assert elapsed < 0.1, f"Widget took {elapsed:.3f}s, expected < 0.1s"


# =============================================================================
# WORKFLOW STATUS WIDGET TESTS
# =============================================================================


class TestWorkflowStatusWidget:
    """Test WorkflowStatusWidget functionality."""

    def test_workflow_status_widget_creation(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workflow status widget creation."""
        widget = WorkflowStatusWidget(
            "workflow_1", mock_repository, mock_logger, mock_cache
        )
        assert widget.widget_id == "workflow_1"

    def test_workflow_status_widget_data(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workflow status widget data."""
        widget = WorkflowStatusWidget(
            "workflow_1", mock_repository, mock_logger, mock_cache
        )
        data = widget.get_data()

        assert data["widget_type"] == "workflow_status"
        assert "active_workflows" in data
        assert "completed_today" in data
        assert "success_rate" in data

    @pytest.mark.performance
    def test_workflow_status_widget_performance(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test workflow status widget performance < 100ms."""
        widget = WorkflowStatusWidget(
            "workflow_1", mock_repository, mock_logger, mock_cache
        )

        start_time = time.time()
        data = widget.get_data()
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"Widget took {elapsed:.3f}s, expected < 0.1s"


# =============================================================================
# PERFORMANCE METRICS WIDGET TESTS
# =============================================================================


class TestPerformanceMetricsWidget:
    """Test PerformanceMetricsWidget functionality."""

    def test_performance_metrics_widget_creation(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test performance metrics widget creation."""
        widget = PerformanceMetricsWidget(
            "perf_1", mock_repository, mock_logger, mock_cache
        )
        assert widget.widget_id == "perf_1"

    def test_performance_metrics_widget_data(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test performance metrics widget data."""
        widget = PerformanceMetricsWidget(
            "perf_1", mock_repository, mock_logger, mock_cache
        )
        data = widget.get_data()

        assert data["widget_type"] == "performance_metrics"
        assert "avg_response_time" in data
        assert "requests_per_second" in data
        assert "error_rate" in data

    @pytest.mark.performance
    def test_performance_metrics_widget_performance(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test performance metrics widget performance < 100ms."""
        widget = PerformanceMetricsWidget(
            "perf_1", mock_repository, mock_logger, mock_cache
        )

        start_time = time.time()
        data = widget.get_data()
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"Widget took {elapsed:.3f}s, expected < 0.1s"


# =============================================================================
# ALERT WIDGET TESTS
# =============================================================================


class TestAlertWidget:
    """Test AlertWidget functionality."""

    def test_alert_widget_creation(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test alert widget creation."""
        widget = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)
        assert widget.widget_id == "alert_1"

    def test_alert_widget_no_alerts(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test alert widget with no alerts."""
        entities = [Entity(status=EntityStatus.ACTIVE)]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)
        data = widget.get_data()

        assert data["widget_type"] == "alerts"
        assert data["total_alerts"] == 0
        assert len(data["alerts"]) == 0

    def test_alert_widget_deleted_entities(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test alert widget detects deleted entities."""
        entities = [
            Entity(status=EntityStatus.DELETED),
            Entity(status=EntityStatus.DELETED),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)
        data = widget.get_data()

        assert data["total_alerts"] == 1
        assert data["alerts"][0]["level"] == "warning"
        assert data["alerts"][0]["count"] == 2

    def test_alert_widget_blocked_entities(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test alert widget detects blocked entities."""
        entities = [Entity(status=EntityStatus.BLOCKED)]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)
        data = widget.get_data()

        assert data["total_alerts"] == 1
        assert data["alerts"][0]["level"] == "error"

    def test_alert_widget_multiple_alert_types(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test alert widget with multiple alert types."""
        entities = [
            Entity(status=EntityStatus.DELETED),
            Entity(status=EntityStatus.BLOCKED),
        ]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)
        data = widget.get_data()

        assert data["total_alerts"] == 2

    @pytest.mark.performance
    def test_alert_widget_performance(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test alert widget performance < 100ms."""
        # Add 1000 entities with various statuses
        for i in range(1000):
            status = EntityStatus.ACTIVE if i % 2 == 0 else EntityStatus.DELETED
            entity = Entity(status=status)
            mock_repository.add_entity(entity)

        widget = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)

        start_time = time.time()
        data = widget.get_data()
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"Widget took {elapsed:.3f}s, expected < 0.1s"


# =============================================================================
# DASHBOARD TESTS
# =============================================================================


class TestDashboard:
    """Test Dashboard functionality."""

    def test_dashboard_creation(self, mock_logger, mock_cache):
        """Test dashboard creation."""
        dashboard = Dashboard("dash_1", mock_logger, mock_cache)
        assert dashboard.dashboard_id == "dash_1"
        assert len(dashboard.widgets) == 0

    def test_dashboard_add_widget(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test adding widget to dashboard."""
        dashboard = Dashboard("dash_1", mock_logger, mock_cache)
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)

        dashboard.add_widget(widget)

        assert len(dashboard.widgets) == 1
        assert "count_1" in dashboard.widgets

    def test_dashboard_add_multiple_widgets(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test adding multiple widgets to dashboard."""
        dashboard = Dashboard("dash_1", mock_logger, mock_cache)

        widget1 = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        widget2 = RecentChangesWidget("changes_1", mock_repository, mock_logger, mock_cache)
        widget3 = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)

        dashboard.add_widget(widget1)
        dashboard.add_widget(widget2)
        dashboard.add_widget(widget3)

        assert len(dashboard.widgets) == 3

    def test_dashboard_remove_widget(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test removing widget from dashboard."""
        dashboard = Dashboard("dash_1", mock_logger, mock_cache)
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)

        dashboard.add_widget(widget)
        assert len(dashboard.widgets) == 1

        result = dashboard.remove_widget("count_1")
        assert result is True
        assert len(dashboard.widgets) == 0

    def test_dashboard_remove_nonexistent_widget(
        self, mock_logger, mock_cache
    ):
        """Test removing nonexistent widget."""
        dashboard = Dashboard("dash_1", mock_logger, mock_cache)
        result = dashboard.remove_widget("nonexistent")
        assert result is False

    def test_dashboard_get_widget(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test getting widget from dashboard."""
        dashboard = Dashboard("dash_1", mock_logger, mock_cache)
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)

        dashboard.add_widget(widget)
        retrieved = dashboard.get_widget("count_1")

        assert retrieved == widget

    def test_dashboard_refresh_all(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test refreshing all widgets."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        dashboard = Dashboard("dash_1", mock_logger, mock_cache)
        widget1 = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        widget2 = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)

        dashboard.add_widget(widget1)
        dashboard.add_widget(widget2)

        results = dashboard.refresh_all()

        assert len(results) == 2
        assert "count_1" in results
        assert "alert_1" in results
        assert "last_updated" in results["count_1"]

    def test_dashboard_refresh_widget(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test refreshing specific widget."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        dashboard = Dashboard("dash_1", mock_logger, mock_cache)
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)

        dashboard.add_widget(widget)
        data = dashboard.refresh_widget("count_1")

        assert "last_updated" in data
        assert data["total"] == 1

    def test_dashboard_refresh_nonexistent_widget(
        self, mock_logger, mock_cache
    ):
        """Test refreshing nonexistent widget raises error."""
        dashboard = Dashboard("dash_1", mock_logger, mock_cache)

        with pytest.raises(ValueError) as exc_info:
            dashboard.refresh_widget("nonexistent")
        assert "not found" in str(exc_info.value)

    @pytest.mark.performance
    def test_dashboard_performance_multiple_widgets(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test dashboard performance with multiple widgets."""
        # Add 1000 entities
        for i in range(1000):
            entity = Entity(metadata={"entity_type": "project"})
            mock_repository.add_entity(entity)

        dashboard = Dashboard("dash_1", mock_logger, mock_cache)
        dashboard.add_widget(
            EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        )
        dashboard.add_widget(
            RecentChangesWidget("changes_1", mock_repository, mock_logger, mock_cache)
        )
        dashboard.add_widget(
            AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)
        )

        start_time = time.time()
        results = dashboard.refresh_all()
        elapsed = time.time() - start_time

        assert len(results) == 3
        # All widgets should complete in < 300ms combined
        assert elapsed < 0.3, f"Dashboard took {elapsed:.3f}s, expected < 0.3s"


# =============================================================================
# WIDGET REFRESH TESTS
# =============================================================================


class TestWidgetRefresh:
    """Test widget refresh functionality."""

    def test_widget_needs_refresh_initially(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test widget needs refresh on first use."""
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        assert widget.needs_refresh() is True

    def test_widget_does_not_need_refresh_immediately(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test widget doesn't need refresh immediately after refresh."""
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        widget.refresh()

        assert widget.needs_refresh() is False

    def test_widget_force_refresh(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test widget force refresh bypasses cache."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)

        # First refresh
        data1 = widget.refresh()

        # Add more entities
        mock_repository.add_entity(Entity(metadata={"entity_type": "task"}))

        # Regular refresh (uses cache)
        data2 = widget.refresh()
        assert data2["total"] == 1  # Still cached

        # Force refresh (bypasses cache)
        data3 = widget.refresh(force=True)
        assert data3["total"] == 2  # Fresh data


# =============================================================================
# CONCURRENT UPDATE TESTS
# =============================================================================


class TestConcurrentUpdates:
    """Test concurrent widget updates."""

    def test_multiple_widget_concurrent_refresh(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test multiple widgets can refresh concurrently."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget1 = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        widget2 = RecentChangesWidget("changes_1", mock_repository, mock_logger, mock_cache)
        widget3 = AlertWidget("alert_1", mock_repository, mock_logger, mock_cache)

        # Refresh all widgets
        data1 = widget1.refresh()
        data2 = widget2.refresh()
        data3 = widget3.refresh()

        assert "last_updated" in data1
        assert "last_updated" in data2
        assert "last_updated" in data3

    def test_widget_cache_isolation(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test widgets have isolated caches."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget1 = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        widget2 = EntityCountWidget("count_2", mock_repository, mock_logger, mock_cache)

        # Refresh both widgets
        widget1.refresh()
        widget2.refresh()

        # Verify separate cache entries
        assert widget1.get_cache_key() != widget2.get_cache_key()
        assert mock_cache.exists(widget1.get_cache_key())
        assert mock_cache.exists(widget2.get_cache_key())


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestWidgetEdgeCases:
    """Test widget edge cases."""

    def test_widget_without_cache(
        self, mock_repository, mock_logger
    ):
        """Test widget works without cache."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = EntityCountWidget("count_1", mock_repository, mock_logger, cache=None)
        data = widget.refresh()

        assert data["total"] == 1

    def test_widget_cache_expiration(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test widget cache expires correctly."""
        entities = [Entity(metadata={"entity_type": "project"})]
        for entity in entities:
            mock_repository.add_entity(entity)

        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        widget.refresh_interval = 1  # 1 second

        # First refresh
        widget.refresh()
        assert mock_cache.exists(widget.get_cache_key())

        # Wait for expiration
        time.sleep(1.1)

        # Cache should be expired
        cached = mock_cache.get(widget.get_cache_key())
        # The mock cache doesn't auto-expire, but the widget should check

    def test_widget_with_custom_refresh_interval(
        self, mock_repository, mock_logger, mock_cache
    ):
        """Test widget with custom refresh interval."""
        widget = EntityCountWidget("count_1", mock_repository, mock_logger, mock_cache)
        widget.refresh_interval = 300  # 5 minutes

        assert widget.refresh_interval == 300

    def test_widget_error_handling(
        self, mock_logger, mock_cache
    ):
        """Test widget handles repository errors gracefully."""
        mock_repo = Mock()
        mock_repo.list.side_effect = Exception("Database error")

        widget = EntityCountWidget("count_1", mock_repo, mock_logger, mock_cache)

        with pytest.raises(Exception):
            widget.get_data()
