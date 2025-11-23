"""Temporal Engine for Atoms MCP - Change history and temporal queries.

Provides change history tracking, temporal queries, audit trail integration,
time-based filtering, and version comparison.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class TemporalEngine:
    """Engine for tracking and querying temporal data."""

    def __init__(self, retention_days: int = 90):
        """Initialize temporal engine.
        
        Args:
            retention_days: Days to retain change history
        """
        self.retention_days = retention_days
        self.change_history = defaultdict(list)
        self.entity_versions = defaultdict(list)

    def track_change(
        self,
        entity_id: str,
        entity_type: str,
        change_type: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        changed_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track a change to an entity.
        
        Args:
            entity_id: Entity ID
            entity_type: Type of entity
            change_type: Type of change (create, update, delete)
            old_value: Previous value
            new_value: New value
            changed_by: User who made change
            metadata: Additional metadata
            
        Returns:
            Change record dict
        """
        change = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "change_type": change_type,
            "old_value": old_value,
            "new_value": new_value,
            "changed_by": changed_by,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.change_history[entity_id].append(change)

        # Store version
        if new_value:
            self.entity_versions[entity_id].append({
                "version": len(self.entity_versions[entity_id]) + 1,
                "data": new_value,
                "timestamp": change["timestamp"],
                "change_type": change_type
            })

        logger.info(f"Change tracked: {entity_id} ({change_type})")
        return change

    def get_change_history(
        self,
        entity_id: str,
        time_range: Optional[Tuple[str, str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get change history for entity.
        
        Args:
            entity_id: Entity ID
            time_range: Tuple of (start_time, end_time) ISO strings
            limit: Maximum number of changes to return
            
        Returns:
            List of change records
        """
        changes = self.change_history.get(entity_id, [])

        if time_range:
            start_time = datetime.fromisoformat(time_range[0])
            end_time = datetime.fromisoformat(time_range[1])

            changes = [
                c for c in changes
                if start_time <= datetime.fromisoformat(c["timestamp"]) <= end_time
            ]

        # Sort by timestamp descending
        changes.sort(key=lambda c: c["timestamp"], reverse=True)
        return changes[:limit]

    def query_at_time(
        self,
        entity_id: str,
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """Query entity state at specific time.
        
        Args:
            entity_id: Entity ID
            timestamp: ISO timestamp
            
        Returns:
            Entity state at that time or None
        """
        query_time = datetime.fromisoformat(timestamp)
        versions = self.entity_versions.get(entity_id, [])

        # Find version at or before query time
        matching_version = None
        for version in versions:
            version_time = datetime.fromisoformat(version["timestamp"])
            if version_time <= query_time:
                matching_version = version
            else:
                break

        return matching_version

    def compare_versions(
        self,
        entity_id: str,
        time1: str,
        time2: str
    ) -> Dict[str, Any]:
        """Compare entity versions at two times.
        
        Args:
            entity_id: Entity ID
            time1: First ISO timestamp
            time2: Second ISO timestamp
            
        Returns:
            Comparison dict with differences
        """
        version1 = self.query_at_time(entity_id, time1)
        version2 = self.query_at_time(entity_id, time2)

        comparison = {
            "entity_id": entity_id,
            "time1": time1,
            "time2": time2,
            "version1": version1,
            "version2": version2,
            "differences": []
        }

        if version1 and version2:
            data1 = version1.get("data", {})
            data2 = version2.get("data", {})

            # Find differences
            all_keys = set(data1.keys()) | set(data2.keys())
            for key in all_keys:
                val1 = data1.get(key)
                val2 = data2.get(key)

                if val1 != val2:
                    comparison["differences"].append({
                        "field": key,
                        "old_value": val1,
                        "new_value": val2
                    })

        return comparison

    def get_audit_trail(
        self,
        entity_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get audit trail for entity.
        
        Args:
            entity_id: Entity ID
            limit: Maximum entries to return
            
        Returns:
            List of audit trail entries
        """
        changes = self.change_history.get(entity_id, [])
        changes.sort(key=lambda c: c["timestamp"], reverse=True)

        return [
            {
                "timestamp": c["timestamp"],
                "change_type": c["change_type"],
                "changed_by": c["changed_by"],
                "summary": self._summarize_change(c)
            }
            for c in changes[:limit]
        ]

    def get_entities_changed_since(
        self,
        timestamp: str,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get entities changed since timestamp.
        
        Args:
            timestamp: ISO timestamp
            entity_type: Filter by entity type
            
        Returns:
            List of changed entities
        """
        query_time = datetime.fromisoformat(timestamp)
        changed_entities = []

        for entity_id, changes in self.change_history.items():
            for change in changes:
                change_time = datetime.fromisoformat(change["timestamp"])

                if change_time >= query_time:
                    if entity_type and change["entity_type"] != entity_type:
                        continue

                    changed_entities.append({
                        "entity_id": entity_id,
                        "entity_type": change["entity_type"],
                        "last_changed": change["timestamp"],
                        "change_type": change["change_type"]
                    })
                    break

        return changed_entities

    def get_entities_not_updated(
        self,
        days: int,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get entities not updated in N days.
        
        Args:
            days: Number of days
            entity_type: Filter by entity type
            
        Returns:
            List of stale entities
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        stale_entities = []

        for entity_id, changes in self.change_history.items():
            if not changes:
                continue

            last_change = changes[-1]
            last_change_time = datetime.fromisoformat(last_change["timestamp"])

            if last_change_time < cutoff_time:
                if entity_type and last_change["entity_type"] != entity_type:
                    continue

                stale_entities.append({
                    "entity_id": entity_id,
                    "entity_type": last_change["entity_type"],
                    "last_updated": last_change["timestamp"],
                    "days_since_update": (datetime.now() - last_change_time).days
                })

        return stale_entities

    def cleanup_old_changes(self) -> int:
        """Remove changes older than retention period.
        
        Returns:
            Number of changes removed
        """
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0

        for entity_id in list(self.change_history.keys()):
            changes = self.change_history[entity_id]
            original_count = len(changes)

            self.change_history[entity_id] = [
                c for c in changes
                if datetime.fromisoformat(c["timestamp"]) >= cutoff_time
            ]

            removed_count += original_count - len(self.change_history[entity_id])

        logger.info(f"Cleaned up {removed_count} old changes")
        return removed_count

    def _summarize_change(self, change: Dict[str, Any]) -> str:
        """Summarize a change for display.
        
        Args:
            change: Change record
            
        Returns:
            Summary string
        """
        change_type = change["change_type"]
        entity_type = change["entity_type"]

        if change_type == "create":
            return f"Created {entity_type}"
        elif change_type == "update":
            return f"Updated {entity_type}"
        elif change_type == "delete":
            return f"Deleted {entity_type}"
        else:
            return f"{change_type} {entity_type}"


# Global temporal engine instance
_temporal_engine = None


def get_temporal_engine() -> TemporalEngine:
    """Get global temporal engine instance."""
    global _temporal_engine
    if _temporal_engine is None:
        _temporal_engine = TemporalEngine()
    return _temporal_engine

