"""Example tests demonstrating @harmful decorator usage.

This file shows how to use the @harmful decorator for automatic
entity tracking and cleanup in test cascades.

Run with: pytest tests/examples/test_harmful_example.py -v
"""

import pytest

from tests.framework import (
    CleanupStrategy,
    EntityType,
    create_and_track,
    harmful,
    harmful_context,
)


class TestHarmfulDecorator:
    """Tests using @harmful decorator for automatic cleanup."""

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_create_organization(self, fast_http_client, harmful_tracker):
        """Example test that creates an organization.

        The @harmful decorator automatically:
        1. Tracks entities created by the test
        2. Cleans them up in reverse dependency order on test completion
        3. Handles errors gracefully
        """
        result = await fast_http_client.call_tool("workspace_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "Test Org", "domain": "test.example.com"}
        })

        assert result["success"], "Failed to create organization"
        org_id = result.get("id")
        assert org_id, "No organization ID returned"

        # Track the entity for automatic cleanup
        entity = create_and_track(harmful_tracker, EntityType.ORGANIZATION, result, "Test Org")
        assert entity.id == org_id

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_create_workspace(self, fast_http_client, harmful_tracker):
        """Example test that creates a workspace under an organization."""
        # First create the parent organization
        org_result = await fast_http_client.call_tool("workspace_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "Parent Org"}
        })
        create_and_track(harmful_tracker, EntityType.ORGANIZATION, org_result, "Parent Org")

        # Then create the workspace
        ws_result = await fast_http_client.call_tool("workspace_tool", {
            "operation": "create",
            "entity_type": "workspace",
            "data": {
                "name": "Test Workspace",
                "parent_id": org_result.get("id")
            }
        })

        assert ws_result["success"]
        # Track the workspace
        create_and_track(harmful_tracker, EntityType.WORKSPACE, ws_result, "Test Workspace")

        # On test completion, cleanup will happen in order:
        # WORKSPACE → ORGANIZATION (reverse dependency order)


class TestHarmfulContext:
    """Tests using harmful_context async context manager."""

    async def test_create_with_context_manager(self, fast_http_client):
        """Example test using harmful_context for automatic cleanup."""
        async with harmful_context(
            "test_create_with_context",
            http_client=fast_http_client
        ) as tracker:
            # Create organization
            org_result = await fast_http_client.call_tool("workspace_tool", {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": "Context Test Org"}
            })

            org_entity = create_and_track(
                tracker,
                EntityType.ORGANIZATION,
                org_result,
                "Context Test Org"
            )
            assert org_entity.id

            # Create project
            project_result = await fast_http_client.call_tool("workspace_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": "Test Project",
                    "organization_id": org_result.get("id")
                }
            })

            create_and_track(
                tracker,
                EntityType.PROJECT,
                project_result,
                "Test Project"
            )

            # Automatic cleanup on exit:
            # Cleans up PROJECT before ORGANIZATION


class TestCascadeCleanup:
    """Tests demonstrating cascade cleanup order."""

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_full_entity_hierarchy(self, fast_http_client, harmful_tracker):
        """Test creating full entity hierarchy with proper cleanup order."""
        # Create top-level organization
        org_result = await fast_http_client.call_tool("workspace_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "Hierarchy Test"}
        })
        org = create_and_track(harmful_tracker, EntityType.ORGANIZATION, org_result)

        # Create workspace
        ws_result = await fast_http_client.call_tool("workspace_tool", {
            "operation": "create",
            "entity_type": "workspace",
            "data": {
                "name": "Test Workspace",
                "organization_id": org.id
            }
        })
        ws = create_and_track(harmful_tracker, EntityType.WORKSPACE, ws_result)

        # Create project
        proj_result = await fast_http_client.call_tool("workspace_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": "Test Project",
                "workspace_id": ws.id
            }
        })
        proj = create_and_track(harmful_tracker, EntityType.PROJECT, proj_result)

        # Create document
        doc_result = await fast_http_client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "document",
            "data": {
                "name": "Test Doc",
                "project_id": proj.id,
                "content": "Test content"
            }
        })
        doc = create_and_track(harmful_tracker, EntityType.DOCUMENT, doc_result)

        assert org.id
        assert ws.id
        assert proj.id
        assert doc.id

        # Cleanup order on test completion:
        # DOCUMENT → PROJECT → WORKSPACE → ORGANIZATION


@pytest.mark.cold
class TestHarmfulWithMocks:
    """Test @harmful decorator with mocked HTTP client."""

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_with_mock_client(self, harmful_tracker):
        """Example test with mocked dependencies."""
        # In COLD mode, this would use mocked HTTP client
        # @harmful still tracks and cleans up properly
        result = {
            "success": True,
            "id": "mock_org_123",
            "name": "Mock Org"
        }

        entity = create_and_track(harmful_tracker, EntityType.ORGANIZATION, result)
        assert entity.id == "mock_org_123"


@pytest.mark.integration
class TestHarmfulErrorHandling:
    """Tests demonstrating error handling in @harmful decorator."""

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_entity_creation_failure_cleanup(self, fast_http_client, harmful_tracker):
        """Test that cleanup still happens even if test fails."""
        # Create a valid entity
        org_result = await fast_http_client.call_tool("workspace_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "Error Test"}
        })

        create_and_track(harmful_tracker, EntityType.ORGANIZATION, org_result)

        # Intentionally fail the test
        assert False, "This test fails intentionally"
        # Even though the test fails, @harmful will still clean up the organization


# Utility to print cleanup summary
def print_harmful_summary(tracker):
    """Print a summary of harmful state tracking."""
    summary = tracker.cleanup_summary()
    print("\n=== Harmful State Summary ===")
    for test_name, state in summary.items():
        print(f"\nTest: {test_name}")
        print(f"  Entities tracked: {state['entities_tracked']}")
        print(f"  Cleanup results: {state['cleanup_results']}")


__all__ = [
    "TestHarmfulDecorator",
    "TestHarmfulContext",
    "TestCascadeCleanup",
    "TestHarmfulWithMocks",
    "TestHarmfulErrorHandling",
]
