"""Complete project workflow E2E tests (full deployment mode only)."""

from __future__ import annotations

import pytest
import pytest_asyncio

from tests.e2e.helpers import E2EDeploymentHarness

pytestmark = [pytest.mark.e2e, pytest.mark.full_workflow]


@pytest_asyncio.fixture
async def deployment_harness(end_to_end_client):
    """Attach the deterministic deployment harness to the E2E client."""

    harness = E2EDeploymentHarness()
    end_to_end_client.call_tool.side_effect = harness.call_tool
    return harness


@pytest.mark.asyncio
async def test_organization_creation_full_context(
    deployment_harness,
    workflow_scenarios,
    e2e_test_cleanup,
):
    """Precondition: the scenario builder provisions org/project/doc stacks."""

    track_entity, _ = e2e_test_cleanup
    scenario = workflow_scenarios["complete_project"]
    graph = await scenario()

    org_id = track_entity("organization", graph["organization_id"])
    org = deployment_harness.get_entities("organization")[org_id]

    assert org["type"] == "organization"
    assert org["name"].startswith("E2E Test Org")


@pytest.mark.asyncio
async def test_project_creation_with_org_context(
    deployment_harness,
    workflow_scenarios,
    e2e_test_cleanup,
):
    """Precondition: organization exists; verify project binds to it."""

    track_entity, _ = e2e_test_cleanup
    graph = await workflow_scenarios["complete_project"]()

    track_entity("project", graph["project_id"])
    project = deployment_harness.get_entities("project")[graph["project_id"]]

    assert project["organization_id"] == graph["organization_id"]
    assert project["status"] == "active"


@pytest.mark.asyncio
async def test_document_creation_with_project_context(
    deployment_harness,
    workflow_scenarios,
    e2e_test_cleanup,
):
    """Assumption: scenario builder attaches three documents to the project."""

    track_entity, _ = e2e_test_cleanup
    graph = await workflow_scenarios["complete_project"]()

    for doc_id in graph["document_ids"]:
        track_entity("document", doc_id)
        doc = deployment_harness.get_entities("document")[doc_id]
        assert doc["project_id"] == graph["project_id"]
        assert doc["name"].startswith("E2E Test Doc")


@pytest.mark.asyncio
async def test_requirement_creation_with_document_context(
    deployment_harness,
    workflow_scenarios,
    e2e_test_cleanup,
    end_to_end_client,
):
    """Requirement inherits document context when created via entity tool."""

    track_entity, _ = e2e_test_cleanup
    graph = await workflow_scenarios["complete_project"]()

    doc_id = graph["document_ids"][0]
    result = await end_to_end_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "requirement",
            "data": {
                "name": "Derived Requirement",
                "document_id": doc_id,
                "description": "Document-scoped requirement",
            },
        },
    )

    assert result["success"] is True
    req_id = track_entity("requirement", result["data"]["id"])
    requirement = deployment_harness.get_entities("requirement")[req_id]
    assert requirement["document_id"] == doc_id


@pytest.mark.asyncio
async def test_test_case_creation_flow(
    deployment_harness,
    workflow_scenarios,
    e2e_test_cleanup,
    end_to_end_client,
):
    """Create test case tied to project context and ensure persistence."""

    track_entity, _ = e2e_test_cleanup
    graph = await workflow_scenarios["complete_project"]()

    payload = {
        "operation": "create",
        "entity_type": "test",
        "data": {
            "title": "Regression Scenario",
            "project_id": graph["project_id"],
            "priority": "medium",
        },
    }
    result = await end_to_end_client.call_tool("entity_tool", payload)

    assert result["success"] is True
    test_id = track_entity("test", result["data"]["id"])
    stored = deployment_harness.get_entities("test")[test_id]
    assert stored["project_id"] == graph["project_id"]


@pytest.mark.asyncio
async def test_relationships_established_for_project_stack(
    deployment_harness,
    workflow_scenarios,
):
    """Scenario builder connects documents and requirements automatically."""

    graph = await workflow_scenarios["complete_project"]()
    rels = deployment_harness.get_relationships()
    expected = len(graph["document_ids"]) * len(graph["requirement_ids"] or [1])
    assert len(rels) >= expected
    assert all(rel["relationship_type"] == "references" for rel in rels)


@pytest.mark.asyncio
async def test_workflow_execution_completes(
    deployment_harness,
    end_to_end_client,
):
    """Execute workflow through workflow_tool and ensure metrics updated."""

    workflow = {
        "operation": "execute",
        "data": {
            "name": "complete_project",
            "steps": ["create_org", "create_project", "verify_rel"],
        },
    }
    result = await end_to_end_client.call_tool("workflow_tool", workflow)

    assert result["success"] is True
    assert "execution_id" in result["data"]
    assert deployment_harness.get_completion_rate() == 1.0


@pytest.mark.asyncio
async def test_cross_entity_search_returns_all_types(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Search should span organizations, projects, documents, and requirements."""

    await workflow_scenarios["complete_project"]()
    result = await end_to_end_client.call_tool(
        "data_query",
        {"operation": "search", "query": "E2E Test"},
    )

    assert result["success"] is True
    types = {item["type"] for item in result["data"]}
    assert {"organization", "project", "document"}.issubset(types)


@pytest.mark.asyncio
async def test_delete_cascade_marks_dependents(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Deleting the organization in soft-delete mode cascades through tree."""

    graph = await workflow_scenarios["complete_project"]()
    await end_to_end_client.call_tool(
        "entity_tool",
        {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": graph["organization_id"],
            "soft_delete": True,
            "cascade": True,
        },
    )

    project = deployment_harness.get_entities("project")[graph["project_id"]]
    assert project["is_deleted"] is True
    doc = deployment_harness.get_entities("document")[graph["document_ids"][0]]
    assert doc["is_deleted"] is True


@pytest.mark.asyncio
async def test_restore_from_soft_delete_recovers_entities(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Restoring previously soft-deleted records re-activates the tree."""

    graph = await workflow_scenarios["complete_project"]()
    await end_to_end_client.call_tool(
        "entity_tool",
        {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": graph["organization_id"],
            "soft_delete": True,
            "cascade": True,
        },
    )

    await end_to_end_client.call_tool(
        "entity_tool",
        {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": graph["organization_id"],
            "data": {"is_deleted": False},
        },
    )

    org = deployment_harness.get_entities("organization")[graph["organization_id"]]
    assert org["is_deleted"] is False

    # restore one document manually to ensure leaves can revive
    doc_id = graph["document_ids"][0]
    await end_to_end_client.call_tool(
        "entity_tool",
        {
            "operation": "update",
            "entity_type": "document",
            "entity_id": doc_id,
            "data": {"is_deleted": False},
        },
    )
    doc = deployment_harness.get_entities("document")[doc_id]
    assert doc["is_deleted"] is False
