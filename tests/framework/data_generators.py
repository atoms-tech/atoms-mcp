"""
Data Generators for Test Framework

Provides data generation utilities for creating test entities.
"""

import uuid
from typing import Any


class DataGenerator:
    """Generates test data for various entity types."""

    @staticmethod
    def uuid() -> str:
        """Generate a UUID string."""
        return str(uuid.uuid4())

    @staticmethod
    def organization_data(name: str | None = None, **kwargs) -> dict[str, Any]:
        """Generate organization test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Org {uid}",
            "slug": kwargs.get("slug", f"test-org-{uid}"),
            "type": kwargs.get("type", "team"),
            "description": kwargs.get("description", f"Test organization {uid}"),
            **{k: v for k, v in kwargs.items() if k not in ["slug", "type", "description"]},
        }

    @staticmethod
    def project_data(name: str | None = None, organization_id: str | None = None, **kwargs) -> dict[str, Any]:
        """Generate project test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Project {uid}",
            "organization_id": organization_id or DataGenerator.uuid(),
            "description": kwargs.get("description", f"Test project {uid}"),
            **{k: v for k, v in kwargs.items() if k != "description"},
        }

    @staticmethod
    def document_data(title: str | None = None, project_id: str | None = None, **kwargs) -> dict[str, Any]:
        """Generate document test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "title": title or f"Test Document {uid}",
            "project_id": project_id or DataGenerator.uuid(),
            "description": kwargs.get("description", f"Test document {uid}"),
            **{k: v for k, v in kwargs.items() if k != "description"},
        }

    @staticmethod
    def requirement_data(title: str | None = None, document_id: str | None = None, **kwargs) -> dict[str, Any]:
        """Generate requirement test data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "title": title or f"Test Requirement {uid}",
            "document_id": document_id or DataGenerator.uuid(),
            "block_id": kwargs.get("block_id", DataGenerator.uuid()),
            "description": kwargs.get("description", f"Test requirement {uid}"),
            "priority": kwargs.get("priority", "medium"),
            "status": kwargs.get("status", "active"),
            **{k: v for k, v in kwargs.items() if k not in ["title", "description", "priority", "status", "block_id"]},
        }

    @staticmethod
    def test_data(name: str | None = None, project_id: str | None = None, **kwargs) -> dict[str, Any]:
        """Generate test entity data."""
        uid = uuid.uuid4().hex[:8]
        return {
            "name": name or f"Test Case {uid}",
            "project_id": project_id or DataGenerator.uuid(),
            "description": kwargs.get("description", f"Test case {uid}"),
            "priority": kwargs.get("priority", "medium"),
            "status": kwargs.get("status", "pending"),
            **{k: v for k, v in kwargs.items() if k not in ["name", "description", "priority", "status"]},
        }


class EntityFactory:
    """Composable factory helpers with concise method names for workflows."""

    @staticmethod
    def organization(name: str | None = None, **kwargs) -> dict[str, Any]:
        return DataGenerator.organization_data(name=name, **kwargs)

    @staticmethod
    def project(organization_id: str | None = None, name: str | None = None, **kwargs) -> dict[str, Any]:
        return DataGenerator.project_data(name=name, organization_id=organization_id, **kwargs)

    @staticmethod
    def document(project_id: str | None = None, title: str | None = None, **kwargs) -> dict[str, Any]:
        return DataGenerator.document_data(title=title, project_id=project_id, **kwargs)

    @staticmethod
    def requirement(
        document_id: str | None = None, block_id: str | None = None, title: str | None = None, **kwargs
    ) -> dict[str, Any]:
        data = DataGenerator.requirement_data(title=title, document_id=document_id, **kwargs)
        if block_id:
            data["block_id"] = block_id
        return data

    @staticmethod
    def test_entity(
        project_id: str | None = None, requirement_id: str | None = None, name: str | None = None, **kwargs
    ) -> dict[str, Any]:
        data = DataGenerator.test_data(name=name or "Workflow Test Case", project_id=project_id, **kwargs)
        if requirement_id:
            data.setdefault("requirement_id", requirement_id)
        return data

    @staticmethod
    def generate_requirements(count: int, **kwargs) -> list[dict[str, Any]]:
        """Generate a list of requirement data for workflow tests."""
        import uuid

        requirements = []
        for i in range(count):
            uid = uuid.uuid4().hex[:8]
            req = DataGenerator.requirement_data(
                title=kwargs.get("name", f"Requirement {uid}"),
                description=kwargs.get("description", f"Generated requirement {i + 1}"),
                priority=kwargs.get("priority", ["high", "medium", "low"][i % 3]),
                status=kwargs.get("status", "active"),
                **{k: v for k, v in kwargs.items() if k not in ["name", "description", "priority", "status"]},
            )
            req["block_id"] = kwargs.get("block_id", f"block_{uid}")
            req["external_id"] = kwargs.get("external_id", f"EXT-{uid}")
            requirements.append(req)
        return requirements

    @staticmethod
    def generate_document_names(count: int) -> list[str]:
        """Generate a list of document names for workflow tests."""
        import uuid

        templates = [
            "Requirements Specification",
            "Technical Design",
            "User Manual",
            "Test Plan",
            "API Documentation",
            "Architecture Overview",
            "Security Guidelines",
            "Deployment Guide",
        ]

        if count <= len(templates):
            return templates[:count]

        names = templates.copy()
        for _ in range(count - len(templates)):
            names.append(f"Document {uuid.uuid4().hex[:8]}")
        return names
