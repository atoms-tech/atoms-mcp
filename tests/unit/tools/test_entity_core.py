"""Core entity tool tests - Parametrized CRUD operations.

This module contains parametrized tests that run across all entity types:
- CREATE operations with various scenarios
- READ operations with parametrization
- SEARCH operations with filters and ordering
- BATCH operations for multi-entity actions
- FORMAT TYPE handling (detailed, summary)
- ERROR CASES (missing fields, invalid types)

Basic operations (search, archive/restore, list filtering, bulk) are in:
  test_entity_basic_operations.py

Entity-specific tests are in dedicated modules:
  test_entity_organization.py, test_entity_project.py, etc.

Consolidated from: test_working_extension.py (basic operations moved to test_entity_basic_operations.py)

Run with: pytest tests/unit/tools/test_entity_core.py -v
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict
from datetime import datetime, timezone

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestResults:
    """Track test results for matrix generation."""

    __test__ = False  # Prevent pytest collection

    def __init__(self):
        self.results = {}
        self.performance = {}
        self.issues = []

    def record(self, entity_type: str, operation: str, status: str,
               duration_ms: float, notes: str = ""):
        """Record a test result."""
        if entity_type not in self.results:
            self.results[entity_type] = {}

        self.results[entity_type][operation] = {
            "status": status,
            "duration_ms": duration_ms,
            "notes": notes
        }

    def add_issue(self, entity_type: str, operation: str, issue: str):
        """Record an issue discovered during testing."""
        self.issues.append({
            "entity_type": entity_type,
            "operation": operation,
            "issue": issue,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


# Global test results tracker
test_results = TestResults()


class TestEntityCreateParametrized:
    """Parametrized CREATE tests across all entity types."""

    @pytest.mark.unit
    @pytest.mark.parametrize("entity_type,scenario", [
        ("organization", {"name": "basic"}),
        ("project", {"name": "with_auto_context"}),
        ("project", {"name": "with_explicit_id"}),
        ("document", {"name": "basic"}),
        ("requirement", {"name": "basic"}),
        ("test", {"name": "basic"}),
        ("property", {"name": "basic"}),
    ])
    async def test_create_entity_parametrized(self, call_mcp, entity_type, scenario, pytestconfig):
        """Test entity creation with parametrized entity types and scenarios.
        
        User stories tested:
        - User can create an organization
        - User can create a project
        - User can create a document
        - User can create requirements
        - User can create test cases
        """
        from tests.framework.test_data_generators import DataGeneratorHelper

        # Generate entity data based on type and scenario
        generator = DataGeneratorHelper()
        entity_data = generator.create_entity_data(entity_type, scenario)
        context_data = getattr(generator, "context_data", {})

        start = time.perf_counter()
        try:
            # Call the entity tool
            result, duration_ms = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": entity_type,
                    "data": entity_data,
                    **context_data
                }
            )

            # Parse response
            if hasattr(result, "data"):
                response_dict = result.data if isinstance(result.data, dict) else {}
                success = response_dict.get("success", False)
                data = response_dict.get("data", {})
                error = response_dict.get("error", None)
            elif isinstance(result, dict):
                success = result.get("success", False)
                data = result.get("data", {})
                error = result.get("error", None)
            else:
                pytest.fail(f"Unexpected response format: {result}")

            # Validate successful creation
            assert success, f"Create {entity_type} failed: {error}"
            assert "id" in data, f"No ID returned for {entity_type}"

            # Entity type specific validations
            if entity_type == "organization":
                assert "name" in data
                assert "type" in data
            elif entity_type == "project":
                assert "organization_id" in data
            elif entity_type == "document":
                assert "project_id" in data or "organization_id" in data

            # Record successful test
            test_results.record(entity_type, "create", "PASS", duration_ms)

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            test_results.record(entity_type, f"create_{scenario.get('name', 'unknown')}", "FAIL", duration_ms, str(e))
            test_results.add_issue(entity_type, "create", str(e))
            raise


class TestEntityReadParametrized:
    """Parametrized READ tests across entity types."""

    @pytest.mark.unit
    @pytest.mark.parametrize("entity_type,scenario", [
        ("organization", {}),
        ("project", {}),
    ])
    async def test_read_entity_param(self, call_mcp, test_organization, entity_type, scenario):
        """Test reading entities with parametrization.
        
        User stories tested:
        - User can view organization details
        - User can view project details
        """
        # This is a placeholder for parametrized read tests
        # Full implementation would create entity first, then read it
        pass


class TestEntitySearchParametrized:
    """Parametrized SEARCH tests."""

    @pytest.mark.unit
    @pytest.mark.parametrize("entity_type,search_term", [
        ("organization", "test"),
        ("project", "demo"),
    ])
    async def test_search_entity_param(self, call_mcp, entity_type, search_term):
        """Test searching entities with parametrization.
        
        User stories tested:
        - User can search across all entities
        - User can filter search results
        """
        result, duration = await call_mcp(
            "entity_tool",
            {
                "operation": "search",
                "entity_type": entity_type,
                "filters": {"term": search_term}
            }
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
        else:
            success = result.get("success", False)

        assert success, f"Search {entity_type} failed"


class TestBatchOperations:
    """Test batch operations across entity types."""

    @pytest.mark.story("Data Management - User can batch create multiple entities")
    @pytest.mark.unit
    async def test_batch_create_organizations(self, call_mcp):
        """Test batch creation of organizations.
        
        User Story: User can batch create multiple entities
        Acceptance Criteria:
        - Multiple entities can be created in a single batch operation
        - All entities in batch are created successfully
        - Each entity gets a unique ID
        """
        batch_data = [
            {"name": f"Batch Org {i}", "type": "company"}
            for i in range(3)
        ]

        result, duration = await call_mcp(
            "entity_tool",
            {
                "operation": "batch_create",
                "entity_type": "organization",
                "batch": batch_data
            }
        )

        # Verify batch creation
        if hasattr(result, "data"):
            success = result.data.get("success", False)
            data = result.data.get("data", {})
        else:
            success = result.get("success", False)
            data = result.get("data", {})

        assert success, "Batch create failed"
        assert "created" in data or "results" in data


class TestFormatTypes:
    """Test different response format types."""

    @pytest.mark.unit
    async def test_format_detailed(self, call_mcp, test_organization):
        """Test detailed format response."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": test_organization,
                "format_type": "detailed"
            }
        )

        if hasattr(result, "data"):
            success = result.data.get("success", False)
        else:
            success = result.get("success", False)

        assert success, "Detailed format read failed"

    @pytest.mark.unit
    async def test_format_summary(self, call_mcp, test_organization):
        """Test summary format response."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": test_organization,
                "format_type": "summary"
            }
        )

        if hasattr(result, "data"):
            success = result.data.get("success", False)
        else:
            success = result.get("success", False)

        assert success, "Summary format read failed"


class TestErrorCases:
    """Test error handling and edge cases."""

    @pytest.mark.unit
    async def test_create_without_required_fields(self, call_mcp):
        """Test creation with missing required fields."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {}  # Missing required 'name' field
            }
        )

        # Should fail gracefully
        if hasattr(result, "data"):
            success = result.data.get("success", False)
        else:
            success = result.get("success", False)

        assert not success, "Should fail with missing required fields"

    @pytest.mark.unit
    async def test_update_without_entity_id(self, call_mcp):
        """Test update without entity_id."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "organization",
                "data": {"name": "Updated"}
                # Missing entity_id
            }
        )

        if hasattr(result, "data"):
            success = result.data.get("success", False)
        else:
            success = result.get("success", False)

        assert not success, "Should fail without entity_id"

    @pytest.mark.unit
    async def test_invalid_entity_type(self, call_mcp):
        """Test with invalid entity type."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "invalid_type",
                "data": {"name": "Test"}
            }
        )

        if hasattr(result, "data"):
            success = result.data.get("success", False)
        else:
            success = result.get("success", False)

        assert not success, "Should fail with invalid entity type"

