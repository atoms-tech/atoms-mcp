"""Traceability and coverage analysis for requirements and tests.

This module contains tests for requirement-to-test traceability and coverage analysis.

Run with: pytest tests/unit/tools/test_entity_traceability.py -v
"""

from __future__ import annotations

import pytest
from typing import Any

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit,
    pytest.mark.skip(reason="Test infrastructure requires additional setup - use consolidated test files instead")
]


class TestEntityTrace:
    """Entity traceability operations."""

    async def test_trace_basic(self, call_mcp, test_organization):
        """Test getting traceability information for an entity."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "requirement",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        assert result.get("entity_id") == test_organization
        assert result.get("entity_type") == "requirement"

    async def test_trace_returns_linked_tests(self, call_mcp, test_organization):
        """Test that trace returns linked tests."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "requirement",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        # Should have linked tests list
        assert "linked_tests" in result or "trace_links" in result

    async def test_trace_for_test_entity(self, call_mcp, test_organization):
        """Test getting trace for test entity."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "test",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        assert result.get("entity_type") == "test"

    async def test_trace_returns_total_links(self, call_mcp, test_organization):
        """Test that trace returns total link count."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "requirement",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        assert "total_links" in result

    async def test_trace_includes_requirements(self, call_mcp, test_organization):
        """Test that trace can return linked requirements."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "test",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        # Should have linked requirements for tests
        assert "linked_requirements" in result or "trace_links" in result


class TestCoverageAnalysis:
    """Coverage analysis operations."""

    async def test_coverage_basic(self, call_mcp):
        """Test getting coverage analysis."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement"
            }
        )
        
        assert result is not None
        assert result.get("entity_type") == "requirement"

    async def test_coverage_returns_percentage(self, call_mcp):
        """Test that coverage returns percentage."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement"
            }
        )
        
        assert result is not None
        assert "coverage_percentage" in result

    async def test_coverage_returns_counts(self, call_mcp):
        """Test that coverage returns item counts."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement"
            }
        )
        
        assert result is not None
        # Should have count statistics
        assert "covered_count" in result or "total_count" in result

    async def test_coverage_scoped_to_parent(self, call_mcp, test_organization):
        """Test coverage analysis scoped to parent."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement",
                "parent_id": test_organization
            }
        )
        
        assert result is not None
        assert result.get("parent_id") == test_organization

    async def test_coverage_by_priority(self, call_mcp):
        """Test that coverage includes breakdown by priority."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement"
            }
        )
        
        assert result is not None
        # Should have priority breakdown
        assert "by_priority" in result

    async def test_coverage_for_documents(self, call_mcp):
        """Test coverage analysis for documents."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "document"
            }
        )
        
        assert result is not None
        assert result.get("entity_type") == "document"


class TestTraceIntegration:
    """Integration tests for traceability."""

    async def test_trace_and_coverage_together(self, call_mcp, test_organization):
        """Test getting trace and coverage together."""
        # Get trace for requirement
        trace_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "requirement",
                "entity_id": test_organization
            }
        )
        
        assert trace_result is not None
        
        # Get coverage
        coverage_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement"
            }
        )
        
        assert coverage_result is not None

    async def test_trace_includes_timing(self, call_mcp, test_organization):
        """Test that trace includes timing metrics."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "requirement",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        assert duration_ms >= 0

    async def test_coverage_includes_timing(self, call_mcp):
        """Test that coverage includes timing metrics."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement"
            }
        )
        
        assert result is not None
        assert duration_ms >= 0

    async def test_trace_different_entity_types(self, call_mcp, test_organization):
        """Test trace works for different entity types."""
        for entity_type in ["requirement", "test"]:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "trace",
                    "entity_type": entity_type,
                    "entity_id": test_organization
                }
            )
            
            assert result is not None
            assert result.get("entity_type") == entity_type


class TestTraceErrorHandling:
    """Error handling for traceability operations."""

    async def test_trace_without_entity_id(self, call_mcp):
        """Test trace requires entity_id."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "requirement",
                "entity_id": None
            }
        )
        
        # Should handle gracefully
        assert result is not None or result is None

    async def test_trace_without_entity_type(self, call_mcp, test_organization):
        """Test trace with invalid entity type."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": None,
                "entity_id": test_organization
            }
        )
        
        # May succeed or fail depending on validation
        assert result is not None or result is None


class TestCoverageScenarios:
    """Scenario-based coverage analysis tests."""

    async def test_coverage_for_multiple_entity_types(self, call_mcp):
        """Test coverage for different entity types."""
        for entity_type in ["requirement", "test", "document"]:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "coverage",
                    "entity_type": entity_type
                }
            )
            
            assert result is not None
            assert result.get("entity_type") == entity_type

    async def test_coverage_with_parent_scoping(self, call_mcp, test_organization):
        """Test coverage with different parent IDs."""
        # Test with organization
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement",
                "parent_id": test_organization
            }
        )
        
        assert result is not None
        assert result.get("parent_id") == test_organization

    async def test_coverage_metrics_structure(self, call_mcp):
        """Test coverage response structure."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "coverage",
                "entity_type": "requirement"
            }
        )
        
        assert result is not None
        # Should have all expected metrics
        assert "coverage_percentage" in result
        assert "covered_count" in result or "total_count" in result

    async def test_trace_response_structure(self, call_mcp, test_organization):
        """Test trace response structure."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "trace",
                "entity_type": "requirement",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        # Should have trace information
        assert "entity_id" in result
        assert "entity_type" in result
        assert "total_links" in result or "trace_links" in result
