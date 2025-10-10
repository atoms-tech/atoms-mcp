"""Utility functions and fixtures for comprehensive entity tool testing."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any


class EntityFactory:
    """Factory for creating test entity data."""

    @staticmethod
    def organization(
        name: str | None = None,
        slug: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Create organization test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Org {uid}",
            "slug": slug or f"test-org-{uid}",
            "type": kwargs.get("type", "team"),
            "description": kwargs.get("description", f"Test organization {uid}"),
            **{k: v for k, v in kwargs.items() if k not in ["type", "description"]}
        }

    @staticmethod
    def project(
        organization_id: str,
        name: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Create project test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Project {uid}",
            "organization_id": organization_id,
            "description": kwargs.get("description", f"Test project {uid}"),
            **{k: v for k, v in kwargs.items() if k != "description"}
        }

    @staticmethod
    def document(
        project_id: str,
        name: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Create document test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Document {uid}",
            "project_id": project_id,
            "description": kwargs.get("description", f"Test document {uid}"),
            **{k: v for k, v in kwargs.items() if k != "description"}
        }

    @staticmethod
    def requirement(
        document_id: str,
        block_id: str,
        name: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Create requirement test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Requirement {uid}",
            "document_id": document_id,
            "block_id": block_id,
            "description": kwargs.get("description", f"Test requirement {uid}"),
            "priority": kwargs.get("priority", "medium"),
            "status": kwargs.get("status", "active"),
            **{k: v for k, v in kwargs.items()
               if k not in ["description", "priority", "status"]}
        }

    @staticmethod
    def test_entity(
        project_id: str,
        title: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Create test entity test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "title": title or f"Test Case {uid}",
            "project_id": project_id,
            "description": kwargs.get("description", f"Test case {uid}"),
            "priority": kwargs.get("priority", "medium"),
            "status": kwargs.get("status", "pending"),
            **{k: v for k, v in kwargs.items()
               if k not in ["description", "priority", "status"]}
        }


class EntityHierarchyBuilder:
    """Build entity hierarchies for testing."""

    def __init__(self, call_mcp: Callable):
        self.call_mcp = call_mcp
        self.created_entities = {
            "organizations": [],
            "projects": [],
            "documents": [],
            "requirements": [],
            "tests": []
        }

    async def build_full_hierarchy(
        self,
        org_count: int = 1,
        projects_per_org: int = 2,
        docs_per_project: int = 2
    ) -> dict[str, list[dict[str, Any]]]:
        """Build a complete entity hierarchy for testing.

        Args:
            org_count: Number of organizations to create
            projects_per_org: Number of projects per organization
            docs_per_project: Number of documents per project

        Returns:
            Dictionary with all created entities
        """
        # Create organizations
        for _ in range(org_count):
            org_data = EntityFactory.organization()
            result, _ = await self.call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "organization",
                    "data": org_data,
                }
            )
            if result.get("success"):
                org = result["data"]
                self.created_entities["organizations"].append(org)

                # Create projects for this org
                for _ in range(projects_per_org):
                    project_data = EntityFactory.project(org["id"])
                    proj_result, _ = await self.call_mcp(
                        "entity_tool",
                        {
                            "operation": "create",
                            "entity_type": "project",
                            "data": project_data,
                        }
                    )
                    if proj_result.get("success"):
                        project = proj_result["data"]
                        self.created_entities["projects"].append(project)

                        # Create documents for this project
                        for _ in range(docs_per_project):
                            doc_data = EntityFactory.document(project["id"])
                            doc_result, _ = await self.call_mcp(
                                "entity_tool",
                                {
                                    "operation": "create",
                                    "entity_type": "document",
                                    "data": doc_data,
                                }
                            )
                            if doc_result.get("success"):
                                self.created_entities["documents"].append(
                                    doc_result["data"]
                                )

        return self.created_entities

    async def cleanup(self, soft_delete: bool = True):
        """Clean up all created entities."""
        # Delete in reverse order to respect foreign keys
        for doc in self.created_entities["documents"]:
            try:
                await self.call_mcp(
                    "entity_tool",
                    {
                        "operation": "delete",
                        "entity_type": "document",
                        "entity_id": doc["id"],
                        "soft_delete": soft_delete,
                    }
                )
            except Exception:
                pass

        for project in self.created_entities["projects"]:
            try:
                await self.call_mcp(
                    "entity_tool",
                    {
                        "operation": "delete",
                        "entity_type": "project",
                        "entity_id": project["id"],
                        "soft_delete": soft_delete,
                    }
                )
            except Exception:
                pass

        for org in self.created_entities["organizations"]:
            try:
                await self.call_mcp(
                    "entity_tool",
                    {
                        "operation": "delete",
                        "entity_type": "organization",
                        "entity_id": org["id"],
                        "soft_delete": soft_delete,
                    }
                )
            except Exception:
                pass


class PerformanceAnalyzer:
    """Analyze performance metrics from test results."""

    def __init__(self):
        self.metrics = []

    def record_metric(
        self,
        operation: str,
        entity_type: str,
        duration_ms: float,
        entity_count: int = 1,
        **kwargs
    ):
        """Record a performance metric."""
        self.metrics.append({
            "operation": operation,
            "entity_type": entity_type,
            "duration_ms": duration_ms,
            "entity_count": entity_count,
            "per_entity_ms": duration_ms / entity_count if entity_count > 0 else duration_ms,
            "timestamp": datetime.now(UTC).isoformat(),
            **kwargs
        })

    def get_stats(
        self,
        operation: str | None = None,
        entity_type: str | None = None
    ) -> dict[str, Any]:
        """Get performance statistics."""
        filtered = self.metrics

        if operation:
            filtered = [m for m in filtered if m["operation"] == operation]
        if entity_type:
            filtered = [m for m in filtered if m["entity_type"] == entity_type]

        if not filtered:
            return {}

        durations = [m["duration_ms"] for m in filtered]
        per_entity = [m["per_entity_ms"] for m in filtered]

        return {
            "count": len(filtered),
            "total_duration_ms": sum(durations),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "avg_per_entity_ms": sum(per_entity) / len(per_entity),
            "percentile_95_ms": self._percentile(durations, 95),
            "percentile_99_ms": self._percentile(durations, 99),
        }

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def generate_report(self) -> str:
        """Generate a performance analysis report."""
        operations = set(m["operation"] for m in self.metrics)
        entity_types = set(m["entity_type"] for m in self.metrics)

        report = ["# Performance Analysis Report\n\n"]
        report.append(f"Total Measurements: {len(self.metrics)}\n\n")

        # Overall stats
        overall = self.get_stats()
        if overall:
            report.append("## Overall Performance\n")
            report.append(f"- Average Duration: {overall['avg_duration_ms']:.2f}ms\n")
            report.append(f"- 95th Percentile: {overall['percentile_95_ms']:.2f}ms\n")
            report.append(f"- 99th Percentile: {overall['percentile_99_ms']:.2f}ms\n\n")

        # Per operation
        report.append("## Performance by Operation\n\n")
        for op in sorted(operations):
            stats = self.get_stats(operation=op)
            if stats:
                report.append(f"### {op.upper()}\n")
                report.append(f"- Count: {stats['count']}\n")
                report.append(f"- Average: {stats['avg_duration_ms']:.2f}ms\n")
                report.append(f"- Min: {stats['min_duration_ms']:.2f}ms\n")
                report.append(f"- Max: {stats['max_duration_ms']:.2f}ms\n")
                report.append(f"- 95th %ile: {stats['percentile_95_ms']:.2f}ms\n\n")

        # Per entity type
        report.append("## Performance by Entity Type\n\n")
        for entity_type in sorted(entity_types):
            stats = self.get_stats(entity_type=entity_type)
            if stats:
                report.append(f"### {entity_type}\n")
                report.append(f"- Count: {stats['count']}\n")
                report.append(f"- Average: {stats['avg_duration_ms']:.2f}ms\n")
                report.append(f"- Per Entity: {stats['avg_per_entity_ms']:.2f}ms\n\n")

        return "".join(report)


class AssertionHelpers:
    """Helper methods for common assertions in entity tests."""

    @staticmethod
    def assert_entity_created(result: dict[str, Any], entity_type: str):
        """Assert that an entity was successfully created."""
        assert result.get("success") is True, f"Create failed: {result.get('error')}"
        assert "data" in result, "No data in create response"
        assert "id" in result["data"], "No ID in created entity"

        # Check common auto-generated fields
        if entity_type in ["organization", "project", "document"]:
            assert "created_at" in result["data"], "No created_at timestamp"
            assert "updated_at" in result["data"], "No updated_at timestamp"

        # Check entity-specific fields
        if entity_type == "organization":
            assert "slug" in result["data"], "No slug in organization"
        elif entity_type == "project":
            assert "slug" in result["data"], "No slug in project"
            assert "organization_id" in result["data"], "No organization_id in project"
        elif entity_type == "document":
            assert "project_id" in result["data"], "No project_id in document"
        elif entity_type == "requirement":
            assert "external_id" in result["data"], "No external_id in requirement"

    @staticmethod
    def assert_entity_read(result: dict[str, Any], entity_id: str):
        """Assert that an entity was successfully read."""
        assert result.get("success") is True, f"Read failed: {result.get('error')}"
        assert "data" in result, "No data in read response"
        assert result["data"]["id"] == entity_id, "Wrong entity returned"

    @staticmethod
    def assert_entity_updated(result: dict[str, Any], expected_values: dict[str, Any]):
        """Assert that an entity was successfully updated."""
        assert result.get("success") is True, f"Update failed: {result.get('error')}"
        assert "data" in result, "No data in update response"

        # Check that expected values are present
        for key, value in expected_values.items():
            assert result["data"].get(key) == value, \
                f"Expected {key}={value}, got {result['data'].get(key)}"

        # Check that updated_at was modified
        assert "updated_at" in result["data"], "No updated_at timestamp"

    @staticmethod
    def assert_entity_deleted(delete_result: dict[str, Any], read_result: dict[str, Any]):
        """Assert that an entity was successfully deleted."""
        assert delete_result.get("success") is True, \
            f"Delete failed: {delete_result.get('error')}"

        # For soft delete, entity should still exist but be marked deleted
        # For hard delete, entity should not exist

    @staticmethod
    def assert_search_results(
        result: dict[str, Any],
        min_count: int = 0,
        max_count: int | None = None
    ):
        """Assert that search results are valid."""
        assert result.get("success") is True, f"Search failed: {result.get('error')}"
        assert "data" in result, "No data in search response"
        assert isinstance(result["data"], list), "Search data is not a list"

        count = len(result["data"])
        assert count >= min_count, f"Expected at least {min_count} results, got {count}"

        if max_count is not None:
            assert count <= max_count, f"Expected at most {max_count} results, got {count}"

    @staticmethod
    def assert_list_results(
        result: dict[str, Any],
        parent_id: str | None = None,
        parent_key: str | None = None
    ):
        """Assert that list results are valid."""
        assert result.get("success") is True, f"List failed: {result.get('error')}"
        assert "data" in result, "No data in list response"
        assert isinstance(result["data"], list), "List data is not a list"

        # If parent filtering, verify all results have correct parent
        if parent_id and parent_key:
            for item in result["data"]:
                assert item.get(parent_key) == parent_id, \
                    f"Item has wrong {parent_key}: {item.get(parent_key)}"

    @staticmethod
    def assert_batch_results(result: dict[str, Any], expected_count: int):
        """Assert that batch operation results are valid."""
        assert result.get("success") is True, f"Batch failed: {result.get('error')}"
        assert "data" in result, "No data in batch response"
        assert isinstance(result["data"], list), "Batch data is not a list"
        assert len(result["data"]) == expected_count, \
            f"Expected {expected_count} results, got {len(result['data'])}"

        # Check that all items have IDs
        for item in result["data"]:
            assert "id" in item, "Batch item missing ID"


class TestDataValidator:
    """Validate test data integrity and consistency."""

    @staticmethod
    def validate_timestamps(entity: dict[str, Any]) -> list[str]:
        """Validate entity timestamps."""
        issues = []

        if "created_at" not in entity:
            issues.append("Missing created_at timestamp")

        if "updated_at" not in entity:
            issues.append("Missing updated_at timestamp")

        if "created_at" in entity and "updated_at" in entity:
            try:
                created = datetime.fromisoformat(entity["created_at"].replace("Z", "+00:00"))
                updated = datetime.fromisoformat(entity["updated_at"].replace("Z", "+00:00"))

                if updated < created:
                    issues.append("updated_at is before created_at")
            except (ValueError, AttributeError, TypeError):
                issues.append("Invalid timestamp format")

        return issues

    @staticmethod
    def validate_foreign_keys(
        entity: dict[str, Any],
        entity_type: str
    ) -> list[str]:
        """Validate foreign key relationships."""
        issues = []

        fk_requirements = {
            "project": ["organization_id"],
            "document": ["project_id"],
            "requirement": ["document_id", "block_id"],
            "test": ["project_id"],
        }

        if entity_type in fk_requirements:
            for fk in fk_requirements[entity_type]:
                if fk not in entity or not entity[fk]:
                    issues.append(f"Missing or empty foreign key: {fk}")

        return issues

    @staticmethod
    def validate_required_fields(
        entity: dict[str, Any],
        entity_type: str
    ) -> list[str]:
        """Validate required fields."""
        issues = []

        required_fields = {
            "organization": ["name", "slug"],
            "project": ["name", "organization_id"],
            "document": ["name", "project_id"],
            "requirement": ["name", "document_id", "block_id"],
            "test": ["title", "project_id"],
        }

        if entity_type in required_fields:
            for field in required_fields[entity_type]:
                if field not in entity or not entity[field]:
                    issues.append(f"Missing or empty required field: {field}")

        return issues


# Export all utilities
__all__ = [
    "AssertionHelpers",
    "EntityFactory",
    "EntityHierarchyBuilder",
    "PerformanceAnalyzer",
    "TestDataValidator",
]
