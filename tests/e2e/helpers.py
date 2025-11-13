"""Shared helpers for E2E workflow tests.

Provides a deterministic in-memory harness that mimics the consolidated
FastMCP deployment so E2E tests can exercise workflow logic while the
real infrastructure remains mocked inside tests/e2e/conftest.py.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


def _now_iso() -> str:
    """Return deterministic-ish timestamp for test entities."""
    return "2025-01-01T00:00:00Z"


@dataclass
class WorkflowMetrics:
    """Track workflow completion KPIs for reporting."""

    runs: int = 0
    successes: int = 0
    failures: int = 0
    issues: List[str] = field(default_factory=list)

    def completion_rate(self) -> float:
        if self.runs == 0:
            return 0.0
        return self.successes / self.runs


class E2EDeploymentHarness:
    """In-memory harness that services `end_to_end_client.call_tool` requests."""

    def __init__(self) -> None:
        self.entities: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        self.relationships: List[Dict[str, Any]] = []
        self.metrics = WorkflowMetrics()
        self.operation_log: List[Tuple[str, str]] = []
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public helpers used by tests for assertions
    # ------------------------------------------------------------------
    def get_entities(self, entity_type: str) -> Dict[str, Dict[str, Any]]:
        return self.entities.get(entity_type, {})

    def get_relationships(self) -> List[Dict[str, Any]]:
        return list(self.relationships)

    def get_completion_rate(self) -> float:
        return self.metrics.completion_rate()

    def get_issues(self) -> List[str]:
        return list(self.metrics.issues)

    # ------------------------------------------------------------------
    # Tool emulation
    # ------------------------------------------------------------------
    async def call_tool(self, tool: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Entry point wired to `end_to_end_client.call_tool` via side_effect."""

        async with self._lock:
            operation = payload.get("operation", "")
            self.operation_log.append((tool, operation))

            try:
                if tool == "entity_tool":
                    return await self._handle_entity_operation(payload)
                if tool == "relationship_tool":
                    return self._handle_relationship_operation(payload)
                if tool == "workflow_tool":
                    return self._handle_workflow_operation(payload)
                if tool == "data_query":
                    return self._handle_data_query(payload)
            except Exception as exc:  # pragma: no cover - handled in tests
                self.metrics.issues.append(str(exc))
                return {"success": False, "error": str(exc)}

            return {
                "success": False,
                "error": f"Unsupported tool {tool}",
            }

    # --------------------------- Entity tool -------------------------
    async def _handle_entity_operation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        operation = payload["operation"].lower()
        entity_type = payload.get("entity_type", "").lower()

        if operation == "create":
            data = payload.get("data", {})
            created = self._create_entity(entity_type, data)
            return {"success": True, "data": created}

        if operation == "read":
            entity_id = payload.get("entity_id")
            entity = self.entities.get(entity_type, {}).get(entity_id)
            if entity and not entity.get("is_deleted"):
                return {"success": True, "data": entity}
            return {"success": False, "error": f"{entity_type} {entity_id} not found"}

        if operation == "list":
            include_deleted = payload.get("include_deleted", False)
            items = [
                entity
                for entity in self.entities.get(entity_type, {}).values()
                if include_deleted or not entity.get("is_deleted")
            ]
            return {"success": True, "data": items}

        if operation == "update":
            entity_id = payload.get("entity_id")
            data = payload.get("data", {})
            entity = self.entities.get(entity_type, {}).get(entity_id)
            if not entity:
                return {"success": False, "error": f"{entity_type} {entity_id} missing"}
            version_check = payload.get("if_match_version")
            if version_check is not None and entity.get("version", 1) != version_check:
                raise ValueError("Concurrent update detected")
            entity.update(data)
            entity.setdefault("updated_at", _now_iso())
            entity["is_deleted"] = data.get("is_deleted", entity.get("is_deleted", False))
            entity["version"] = entity.get("version", 1) + 1
            return {"success": True, "data": entity}

        if operation == "delete":
            entity_id = payload.get("entity_id")
            soft_delete = payload.get("soft_delete", True)
            cascade = payload.get("cascade", True)
            removed = self._delete_entity(entity_type, entity_id, soft_delete, cascade)
            if not removed:
                return {"success": False, "error": "Delete failed"}
            return {"success": True, "data": {"deleted": entity_id}}

        if operation == "search":
            term = payload.get("search_term", "").lower()
            matches = [
                entity
                for entity in self.entities.get(entity_type, {}).values()
                if term in entity.get("name", "").lower() and not entity.get("is_deleted")
            ]
            return {"success": True, "data": matches}

        if operation == "batch_create":
            batch = payload.get("batch", [])
            results = []
            for item in batch:
                missing = _required_parent(entity_type)
                if missing and missing not in item:
                    results.append({"error": f"Missing {missing}"})
                    continue
                results.append(self._create_entity(entity_type, item))
            return {"success": True, "data": results}

        return {"success": False, "error": f"Unsupported entity op {operation}"}

    # ----------------------- Relationship tool ----------------------
    def _handle_relationship_operation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        operation = payload["operation"].lower()

        if operation == "create":
            rel = {
                "id": uuid.uuid4().hex,
                "source_id": payload["source_id"],
                "target_id": payload["target_id"],
                "relationship_type": payload.get("relationship_type", "relates_to"),
            }
            if rel in self.relationships:
                return {"success": False, "error": "Duplicate relationship"}
            self.relationships.append(rel)
            return {"success": True, "data": rel}

        if operation == "cleanup_orphans":
            before = len(self.relationships)
            existing_ids = {entity_id for items in self.entities.values() for entity_id in items}
            self.relationships = [
                rel for rel in self.relationships if rel["source_id"] in existing_ids and rel["target_id"] in existing_ids
            ]
            return {"success": True, "data": {"removed": before - len(self.relationships)}}

        return {"success": False, "error": f"Unsupported relationship op {operation}"}

    # -------------------------- Workflow tool -----------------------
    def _handle_workflow_operation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        operation = payload.get("operation")
        if operation != "execute":
            return {"success": False, "error": "Unsupported workflow op"}

        self.metrics.runs += 1
        context = payload.get("data", {})
        execution_id = uuid.uuid4().hex

        if context.get("simulate_failure"):
            self.metrics.failures += 1
            self.metrics.issues.append(context.get("failure_reason", "workflow failure"))
            return {"success": False, "error": "Workflow failed", "data": {"execution_id": execution_id}}

        self.metrics.successes += 1
        return {"success": True, "data": {"execution_id": execution_id, "steps": context.get("steps", [])}}

    # --------------------------- Data query -------------------------
    def _handle_data_query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query = payload.get("query", "") or payload.get("search_term", "")
        query = query.lower()
        results = []
        for entity_type, store in self.entities.items():
            for entity in store.values():
                if entity.get("is_deleted"):
                    continue
                haystack = " ".join([
                    entity.get("name", ""),
                    entity.get("description", ""),
                    entity_type,
                ]).lower()
                if query in haystack:
                    results.append({"type": entity_type, **entity})
        return {"success": True, "data": results}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _create_entity(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        valid_types = {"organization", "project", "document", "requirement", "test"}
        if entity_type not in valid_types:
            raise ValueError(f"Unsupported entity type {entity_type}")

        required_parent = _required_parent(entity_type)
        if required_parent and required_parent not in data:
            raise ValueError(f"Missing {required_parent} for {entity_type}")

        entity_id = data.get("id") or str(uuid.uuid4())
        entity = {
            **data,
            "id": entity_id,
            "name": data.get("name") or f"{entity_type}-{entity_id[:6]}",
            "created_at": data.get("created_at", _now_iso()),
            "updated_at": data.get("updated_at", _now_iso()),
            "type": entity_type,
            "is_deleted": data.get("is_deleted", False),
            "version": data.get("version", 1),
        }
        self.entities[entity_type][entity_id] = entity
        return entity

    def _delete_entity(self, entity_type: str, entity_id: str, soft: bool, cascade: bool) -> bool:
        entity = self.entities.get(entity_type, {}).get(entity_id)
        if not entity:
            return False

        if soft:
            entity["is_deleted"] = True
            entity["deleted_at"] = _now_iso()
        else:
            del self.entities[entity_type][entity_id]

        if cascade:
            for child_type, parent_field in _parent_links().items():
                if parent_field["parent"] == entity_type:
                    child_store = self.entities.get(child_type, {})
                    for child_id, child in list(child_store.items()):
                        if child.get(parent_field["field"]) == entity_id:
                            self._delete_entity(child_type, child_id, soft, cascade)
        return True


def _parent_links() -> Dict[str, Dict[str, str]]:
    """Return mapping describing hierarchy for cascade logic."""

    return {
        "project": {"parent": "organization", "field": "organization_id"},
        "document": {"parent": "project", "field": "project_id"},
        "requirement": {"parent": "document", "field": "document_id"},
        "test": {"parent": "project", "field": "project_id"},
    }


def _required_parent(entity_type: str) -> Optional[str]:
    links = _parent_links().get(entity_type)
    return links["field"] if links else None


__all__ = ["E2EDeploymentHarness"]
