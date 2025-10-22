"""
Test Utilities

Common utilities for testing.
"""

from typing import Any, Dict, List, Optional, Union
import time
import asyncio
from datetime import datetime


class AssertionHelpers:
    """Helper functions for test assertions."""
    
    @staticmethod
    def assert_response_success(response: Dict[str, Any]) -> bool:
        """Assert that a response indicates success.
        
        Args:
            response: The response to check
            
        Returns:
            True if response indicates success
        """
        if not isinstance(response, dict):
            return False
        
        # Check for success field
        if 'success' in response:
            return bool(response['success'])
        
        # Check for error field (absence indicates success)
        if 'error' in response:
            return not bool(response['error'])
        
        return True
    
    @staticmethod
    def assert_has_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Assert that data has all required fields.
        
        Args:
            data: The data to check
            required_fields: List of required field names
            
        Returns:
            True if all required fields are present
        """
        return all(field in data for field in required_fields)
    
    @staticmethod
    def assert_field_type(data: Dict[str, Any], field_name: str, expected_type: type) -> bool:
        """Assert that a field has the expected type.
        
        Args:
            data: The data to check
            field_name: Name of the field to check
            expected_type: Expected type of the field
            
        Returns:
            True if field has expected type
        """
        if field_name not in data:
            return False
        return isinstance(data[field_name], expected_type)


class EntityFactory:
    """Factory for creating test entities."""
    
    @staticmethod
    def create_organization_data(name: str = "Test Organization", **kwargs) -> Dict[str, Any]:
        """Create test organization data.
        
        Args:
            name: Organization name
            **kwargs: Additional fields
            
        Returns:
            Organization data dictionary
        """
        return {
            "name": name,
            "description": f"Test organization: {name}",
            "domain": "test.example.com",
            "settings": {},
            "status": "active",
            **kwargs
        }
    
    @staticmethod
    def create_project_data(name: str = "Test Project", organization_id: str = "test-org-1", **kwargs) -> Dict[str, Any]:
        """Create test project data.
        
        Args:
            name: Project name
            organization_id: Organization ID
            **kwargs: Additional fields
            
        Returns:
            Project data dictionary
        """
        return {
            "name": name,
            "description": f"Test project: {name}",
            "organization_id": organization_id,
            "settings": {},
            "status": "active",
            "tags": ["test"],
            **kwargs
        }
    
    @staticmethod
    def create_document_data(title: str = "Test Document", project_id: str = "test-project-1", **kwargs) -> Dict[str, Any]:
        """Create test document data.
        
        Args:
            title: Document title
            project_id: Project ID
            **kwargs: Additional fields
            
        Returns:
            Document data dictionary
        """
        return {
            "title": title,
            "content": f"Test content for {title}",
            "project_id": project_id,
            "document_type": "document",
            "metadata": {},
            "status": "draft",
            "version": "1.0",
            "tags": ["test"],
            **kwargs
        }
    
    @staticmethod
    def create_requirement_data(title: str = "Test Requirement", document_id: str = "test-doc-1", **kwargs) -> Dict[str, Any]:
        """Create test requirement data.
        
        Args:
            title: Requirement title
            document_id: Document ID
            **kwargs: Additional fields
            
        Returns:
            Requirement data dictionary
        """
        return {
            "title": title,
            "description": f"Test requirement: {title}",
            "document_id": document_id,
            "priority": "medium",
            "status": "draft",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"],
            "metadata": {},
            "tags": ["test"],
            **kwargs
        }
    
    @staticmethod
    def create_test_data(name: str = "Test Case", project_id: str = "test-project-1", **kwargs) -> Dict[str, Any]:
        """Create test case data.
        
        Args:
            name: Test case name
            project_id: Project ID
            **kwargs: Additional fields
            
        Returns:
            Test case data dictionary
        """
        return {
            "name": name,
            "description": f"Test case: {name}",
            "project_id": project_id,
            "test_type": "unit",
            "status": "draft",
            "steps": [
                {"step": 1, "action": "Setup", "expected": "Ready"},
                {"step": 2, "action": "Execute", "expected": "Success"}
            ],
            "expected_result": "Test passes",
            "metadata": {},
            "tags": ["test"],
            **kwargs
        }


class PerformanceAnalyzer:
    """Analyzer for test performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation.
        
        Args:
            operation: Name of the operation to time
        """
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and record the duration.
        
        Args:
            operation: Name of the operation to time
            
        Returns:
            Duration in seconds
        """
        if operation not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(duration)
        del self.start_times[operation]
        
        return duration
    
    def get_average_time(self, operation: str) -> float:
        """Get average time for an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Average time in seconds
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return 0.0
        
        return sum(self.metrics[operation]) / len(self.metrics[operation])
    
    def get_total_time(self, operation: str) -> float:
        """Get total time for an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Total time in seconds
        """
        if operation not in self.metrics:
            return 0.0
        
        return sum(self.metrics[operation])
    
    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of all performance metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        summary = {}
        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    "count": len(times),
                    "total": sum(times),
                    "average": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times)
                }
        return summary
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.start_times.clear()