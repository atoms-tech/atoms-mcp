"""Example tests demonstrating cascade flow patterns.

This file shows how to use @cascade_flow decorator for automatic
test dependency ordering with predefined patterns.

Run with: pytest tests/examples/test_cascade_flow_example.py -v
"""

import pytest

from tests.framework import (
    FlowPattern,
    cascade_flow,
    depends_on,
    flow_stage,
)


@cascade_flow(FlowPattern.CRUD.value, entity_type="organization")
class TestOrganizationCRUD:
    """Example CRUD flow for organization entity.

    The @cascade_flow decorator automatically:
    1. Registers pytest.mark.dependency markers
    2. Ensures tests run in the correct order
    3. Skips dependent tests if prerequisites fail
    4. Provides test_results fixture for data sharing
    """

    @flow_stage("list", entity_type="organization")
    async def test_list_organizations(self, store_result, test_results):
        """Step 1: List existing organizations."""
        # In a real test, this would call the API
        result = {
            "success": True,
            "items": []
        }

        # Store result for dependent tests
        store_result("list_organizations", True, {"count": 0})
        assert result["success"]

    @flow_stage("create", entity_type="organization")
    @depends_on("test_list_organizations")
    async def test_create_organization(self, store_result, test_results):
        """Step 2: Create a new organization."""
        # Get result from previous test
        list_result = test_results.get_result("test_list_organizations")
        assert list_result and list_result.passed, "List test must pass first"

        # Create organization
        result = {
            "success": True,
            "id": "org_12345",
            "name": "Test Organization"
        }

        # Store result including the ID for next tests
        store_result("test_create_organization", True, {
            "org_id": result["id"],
            "org_name": result["name"]
        })

        assert result["success"]

    @flow_stage("read", entity_type="organization")
    @depends_on("test_create_organization")
    async def test_read_organization(self, store_result, test_results):
        """Step 3: Read the created organization."""
        # Get data from creation test
        org_id = test_results.get_data("org_id")
        assert org_id, "Organization ID must be available from create test"

        # Read organization
        result = {
            "success": True,
            "id": org_id,
            "name": "Test Organization"
        }

        store_result("test_read_organization", True, {"read_success": True})
        assert result["success"]

    @flow_stage("update", entity_type="organization")
    @depends_on("test_read_organization")
    async def test_update_organization(self, store_result, test_results):
        """Step 4: Update the organization."""
        org_id = test_results.get_data("org_id")
        assert org_id

        # Update organization
        result = {
            "success": True,
            "id": org_id,
            "name": "Updated Organization"
        }

        store_result("test_update_organization", True, {"updated": True})
        assert result["success"]

    @flow_stage("delete", entity_type="organization")
    @depends_on("test_update_organization")
    async def test_delete_organization(self, store_result, test_results):
        """Step 5: Delete the organization."""
        org_id = test_results.get_data("org_id")
        assert org_id

        # Delete organization
        result = {"success": True}

        store_result("test_delete_organization", True, {"deleted": True})
        assert result["success"]

    @flow_stage("verify", entity_type="organization")
    @depends_on("test_delete_organization")
    async def test_verify_deletion(self, store_result, test_results):
        """Step 6: Verify the organization was deleted."""
        # Get all previous results
        all_results = test_results.get_all_results()

        # Verify deletion
        result = {"success": True, "found": False}

        store_result("test_verify_deletion", True, {
            "total_steps": len(all_results),
            "all_passed": all(r.passed for r in all_results.values())
        })

        assert result["success"]


@cascade_flow(FlowPattern.MINIMAL_CRUD.value, entity_type="project")
class TestProjectMinimalCRUD:
    """Example minimal CRUD flow (create → read → delete only)."""

    async def test_create_project(self, store_result):
        """Create a project."""
        result = {"success": True, "id": "proj_123"}
        store_result("test_create_project", True, {"project_id": result["id"]})
        assert result["success"]

    @depends_on("test_create_project")
    async def test_read_project(self, store_result, test_results):
        """Read the project."""
        project_id = test_results.get_data("project_id")
        result = {"success": True, "id": project_id}
        store_result("test_read_project", True)
        assert result["success"]

    @depends_on("test_read_project")
    async def test_delete_project(self, store_result, test_results):
        """Delete the project."""
        project_id = test_results.get_data("project_id")
        result = {"success": True}
        store_result("test_delete_project", True)
        assert result["success"]


@cascade_flow(FlowPattern.HIERARCHICAL.value, entity_type="workspace")
class TestWorkspaceHierarchy:
    """Example hierarchical flow (parent → children → interactions → cleanup)."""

    async def test_setup_parent(self, store_result):
        """Setup parent workspace."""
        result = {"success": True, "id": "ws_parent_123"}
        store_result("test_setup_parent", True, {"parent_id": result["id"]})
        assert result["success"]

    @depends_on("test_setup_parent")
    async def test_create_children(self, store_result, test_results):
        """Create child workspaces."""
        parent_id = test_results.get_data("parent_id")
        children = [
            {"id": "ws_child_1", "parent_id": parent_id},
            {"id": "ws_child_2", "parent_id": parent_id},
        ]
        store_result("test_create_children", True, {
            "children": [c["id"] for c in children]
        })
        assert len(children) == 2

    @depends_on("test_create_children")
    async def test_interact(self, store_result, test_results):
        """Perform interactions between parent and children."""
        parent_id = test_results.get_data("parent_id")
        children = test_results.get_data("children")

        result = {
            "success": True,
            "interactions": len(children)
        }

        store_result("test_interact", True, {"interactions_count": result["interactions"]})
        assert result["success"]

    @depends_on("test_interact")
    async def test_cleanup(self, store_result, test_results):
        """Cleanup all resources."""
        all_data = test_results.get_all_data()
        result = {"success": True}
        store_result("test_cleanup", True)
        assert result["success"]


@cascade_flow(FlowPattern.WORKFLOW.value, entity_type="document")
class TestDocumentWorkflow:
    """Example workflow pattern (setup → execute → verify → cleanup)."""

    async def test_setup(self, store_result):
        """Setup: Create necessary resources."""
        doc_id = "doc_123"
        store_result("test_setup", True, {"doc_id": doc_id})

    @depends_on("test_setup")
    async def test_execute(self, store_result, test_results):
        """Execute: Perform main workflow."""
        doc_id = test_results.get_data("doc_id")
        result = {"success": True, "processed": True}
        store_result("test_execute", True, {"result": result})
        assert result["success"]

    @depends_on("test_execute")
    async def test_verify(self, store_result, test_results):
        """Verify: Check workflow results."""
        result_data = test_results.get_data("result")
        assert result_data and result_data.get("processed")
        store_result("test_verify", True)

    @depends_on("test_verify")
    async def test_cleanup(self, store_result):
        """Cleanup: Remove temporary resources."""
        store_result("test_cleanup", True)


# Example: Conditional test based on flow stage
class TestConditionalFlow:
    """Example showing conditional test execution based on flow stage."""

    async def test_stage_a(self, store_result):
        """First test in sequence."""
        store_result("test_stage_a", True, {"value": 42})

    @depends_on("test_stage_a")
    @pytest.mark.skip(reason="Demonstrating optional skip")
    async def test_stage_b_optional(self, store_result, test_results):
        """Optional test that can be skipped."""
        value = test_results.get_data("value")
        store_result("test_stage_b_optional", True)

    @depends_on("test_stage_a")
    async def test_stage_c_required(self, store_result, test_results):
        """Required test that depends on stage A."""
        value = test_results.get_data("value")
        assert value == 42
        store_result("test_stage_c_required", True)


# Visualize flow patterns
@pytest.mark.no_header
def test_visualize_flows():
    """Generate visualizations of all flow patterns."""
    try:
        from tests.framework import FlowVisualizer
        FlowVisualizer.visualize_all(".flow_diagrams")
        print("✓ Flow diagrams generated in .flow_diagrams/")
    except ImportError:
        print("⚠ Graphviz not installed, skipping flow visualization")


__all__ = [
    "TestOrganizationCRUD",
    "TestProjectMinimalCRUD",
    "TestWorkspaceHierarchy",
    "TestDocumentWorkflow",
    "TestConditionalFlow",
    "test_visualize_flows",
]
