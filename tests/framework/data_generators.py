"""
Test Data Generators - Consolidated Entity Factory

Provides unified factories for generating realistic test data.
Consolidates DataGenerator and EntityFactory into single comprehensive class.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class EntityFactory:
    """Unified factory for generating test entities with consistent structure.
    
    Consolidates functionality from DataGenerator and EntityFactory.
    Provides both comprehensive data generation and flexible override patterns.
    """

    __test__ = False  # Prevent pytest collection

    # Utility methods (from DataGenerator)
    @staticmethod
    def timestamp() -> str:
        """Generate timestamp string for unique identifiers."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    @staticmethod
    def unique_id(prefix: str = "") -> str:
        """Generate unique identifier."""
        ts = EntityFactory.timestamp()
        return f"{prefix}{ts}" if prefix else ts

    @staticmethod
    def uuid() -> str:
        """Generate a random UUID string."""
        return str(uuid.uuid4())

    # Entity data methods (consolidated from both classes)
    @staticmethod
    def organization(name: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Create organization test data.
        
        Args:
            name: Optional organization name
            **overrides: Additional fields to override defaults
            
        Returns:
            Dictionary with organization test data
        """
        unique = EntityFactory.unique_id()
        data = {
            "name": name or f"Test Org {unique}",
            "slug": f"test-org-{unique}",
            "description": f"Automated test organization created at {unique}",
            "type": "team",
        }
        data.update(overrides)
        return data

    # Alias for backward compatibility
    @staticmethod
    def organization_data(name: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Alias for organization() - backward compatibility."""
        return EntityFactory.organization(name, **overrides)

    @staticmethod
    def project(org_id: Optional[str] = None, name: Optional[str] = None, organization_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Create project test data.
        
        Args:
            org_id: Organization ID (alias for organization_id)
            name: Optional project name
            organization_id: Organization ID (preferred over org_id)
            **overrides: Additional fields to override defaults
            
        Returns:
            Dictionary with project test data
        """
        unique = EntityFactory.unique_id()
        project_name = name or f"Test Project {unique}"
        data = {
            "name": project_name,
            "description": f"Automated test project created at {unique}",
            "slug": f"test-project-{unique}",
            "organization_id": organization_id or org_id or EntityFactory.uuid(),
        }
        data.update(overrides)
        return data

    # Alias for backward compatibility
    @staticmethod
    def project_data(name: Optional[str] = None, organization_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Alias for project() - backward compatibility."""
        return EntityFactory.project(organization_id=organization_id, name=name, **overrides)

    @staticmethod
    def document(project_id: Optional[str] = None, name: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Create document test data.
        
        Args:
            project_id: Project ID
            name: Optional document name
            **overrides: Additional fields to override defaults
            
        Returns:
            Dictionary with document test data
        """
        unique = EntityFactory.unique_id()
        data = {
            "name": name or f"Test Document {unique}",
            "description": f"Automated test document created at {unique}",
            "type": "specification",
            "content": "Test document content",
            "project_id": project_id or EntityFactory.uuid(),
        }
        data.update(overrides)
        return data

    # Alias for backward compatibility
    @staticmethod
    def document_data(name: Optional[str] = None, project_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Alias for document() - backward compatibility."""
        return EntityFactory.document(project_id=project_id, name=name, **overrides)

    @staticmethod
    def requirement(name: Optional[str] = None, document_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Create requirement test data.
        
        Args:
            name: Optional requirement name
            document_id: Document ID
            **overrides: Additional fields to override defaults
            
        Returns:
            Dictionary with requirement test data
        """
        unique = EntityFactory.unique_id()
        data = {
            "name": name or f"REQ-TEST-{unique}",
            "description": f"Automated test requirement created at {unique}",
            "priority": "high",
            "status": "active",
            "document_id": document_id or EntityFactory.uuid(),
        }
        data.update(overrides)
        return data

    # Alias for backward compatibility
    @staticmethod
    def requirement_data(name: Optional[str] = None, document_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Alias for requirement() - backward compatibility."""
        return EntityFactory.requirement(name=name, document_id=document_id, **overrides)

    @staticmethod
    def test_case(title: Optional[str] = None, project_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Create test case data.
        
        Args:
            title: Optional test case title
            project_id: Project ID
            **overrides: Additional fields to override defaults
            
        Returns:
            Dictionary with test case data
        """
        unique = EntityFactory.unique_id()
        data = {
            "title": title or f"Test Case {unique}",
            "description": f"Automated test case created at {unique}",
            "status": "pending",
            "priority": "medium",
            "project_id": project_id or EntityFactory.uuid(),
        }
        data.update(overrides)
        return data

    # Alias for backward compatibility
    @staticmethod
    def test_data(title: Optional[str] = None, project_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Alias for test_case() - backward compatibility."""
        return EntityFactory.test_case(title=title, project_id=project_id, **overrides)

    @staticmethod
    def property(name: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Create property test data.
        
        Args:
            name: Optional property name
            **overrides: Additional fields to override defaults
            
        Returns:
            Dictionary with property test data
        """
        data = {
            "name": name or f"Prop-{uuid.uuid4().hex[:8]}",
            "value": "test-value",
        }
        data.update(overrides)
        return data

    @staticmethod
    def batch_data(entity_type: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate batch test data for entity type.
        
        Args:
            entity_type: Type of entity to generate
            count: Number of entities to generate
            
        Returns:
            List of entity data dictionaries
        """
        generators = {
            "organization": EntityFactory.organization,
            "project": EntityFactory.project,
            "document": EntityFactory.document,
            "requirement": EntityFactory.requirement,
            "test": EntityFactory.test_case,
            "test_case": EntityFactory.test_case,
        }

        generator = generators.get(entity_type)
        if not generator:
            return []

        return [generator() for _ in range(count)]


# Backward compatibility alias
DataGenerator = EntityFactory
