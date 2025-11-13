"""
Test Data Generators

Provides factories for generating realistic test data.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class DataGenerator:
    """Generate test data for entities."""

    __test__ = False  # Prevent pytest collection

    @staticmethod
    def timestamp() -> str:
        """Generate timestamp string for unique identifiers."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    @staticmethod
    def unique_id(prefix: str = "") -> str:
        """Generate unique identifier."""
        ts = DataGenerator.timestamp()
        return f"{prefix}{ts}" if prefix else ts

    @staticmethod
    def uuid() -> str:
        """Generate a random UUID string."""
        return str(uuid.uuid4())

    @staticmethod
    def organization_data(name: Optional[str] = None) -> Dict[str, Any]:
        """Generate organization test data."""
        unique = DataGenerator.unique_id()
        return {
            "name": name or f"Test Org {unique}",
            "slug": f"test-org-{unique}",
            "description": f"Automated test organization created at {unique}",
            "type": "team",
        }

    @staticmethod
    def project_data(name: Optional[str] = None, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate project test data."""
        unique = DataGenerator.unique_id()
        project_name = name or f"Test Project {unique}"
        data = {
            "name": project_name,
            "description": f"Automated test project created at {unique}",
            "slug": f"test-project-{unique}",  # Auto-generate slug from name
        }
        # organization_id is required - use provided value, "auto" for auto resolution, or generate a mock ID
        if organization_id is None:
            # For basic scenarios, use a mock organization ID
            data["organization_id"] = DataGenerator.uuid()
        else:
            data["organization_id"] = organization_id
        return data

    @staticmethod
    def document_data(name: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate document test data."""
        unique = DataGenerator.unique_id()
        data = {
            "name": name or f"Test Document {unique}",
            "description": f"Automated test document created at {unique}",
            "type": "specification",
        }
        # project_id is required - use provided value, "auto" for auto resolution, or generate a mock ID
        if project_id is None:
            # For basic scenarios, use a mock project ID
            data["project_id"] = DataGenerator.uuid()
        else:
            data["project_id"] = project_id
        return data

    @staticmethod
    def requirement_data(name: Optional[str] = None, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate requirement test data."""
        unique = DataGenerator.unique_id()
        data = {
            "name": name or f"REQ-TEST-{unique}",
            "description": f"Automated test requirement created at {unique}",
            "priority": "medium",
            "status": "active",
        }
        # document_id is required - use provided value, "auto" for auto resolution, or generate a mock ID
        if document_id is None:
            # For basic scenarios, use a mock document ID
            data["document_id"] = DataGenerator.uuid()
        else:
            data["document_id"] = document_id
        return data

    @staticmethod
    def test_data(title: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate test case data."""
        unique = DataGenerator.unique_id()
        data = {
            "title": title or f"Test Case {unique}",
            "description": f"Automated test case created at {unique}",
            "status": "pending",
            "priority": "medium",
        }
        # project_id is required - use provided value, "auto" for auto resolution, or generate a mock ID
        if project_id is None:
            # For basic scenarios, use a mock project ID
            data["project_id"] = DataGenerator.uuid()
        else:
            data["project_id"] = project_id
        return data

    @staticmethod
    def batch_data(entity_type: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate batch test data for entity type."""
        generators = {
            "organization": DataGenerator.organization_data,
            "project": DataGenerator.project_data,
            "document": DataGenerator.document_data,
            "requirement": DataGenerator.requirement_data,
            "test": DataGenerator.test_data,
        }

        generator = generators.get(entity_type)
        if not generator:
            return []

        return [generator() for _ in range(count)]
