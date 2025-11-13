"""Error recovery regression tests for full deployment workflows."""

from __future__ import annotations

import asyncio
import pytest
import pytest_asyncio

from tests.e2e.helpers import E2EDeploymentHarness

pytestmark = [pytest.mark.e2e, pytest.mark.full_workflow]


@pytest_asyncio.fixture
async def deployment_harness(end_to_end_client):
    harness = E2EDeploymentHarness()
    end_to_end_client.call_tool.side_effect = harness.call_tool
    return harness


@pytest.mark.asyncio
async def test_invalid_input_handling(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Invalid entity type from scenario builder should be rejected with error."""

    scenario = workflow_scenarios["error_recovery"]
    payloads = await scenario()

    result = await end_to_end_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": payloads["invalid_entity_type"],
            "data": payloads["missing_required_data"],
        },
    )

    assert result["success"] is False
    assert "Unsupported" in result["error"]


@pytest.mark.asyncio
async def test_concurrent_update_conflicts(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Concurrent updates must fail when version checks differ."""

    await workflow_scenarios["complete_project"]()
    requirement_store = deployment_harness.get_entities("requirement")
    requirement_id = next(iter(requirement_store))
    requirement = requirement_store[requirement_id]
    version = requirement["version"]

    async def update(name: str, version_hint: int):
        return await end_to_end_client.call_tool(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "requirement",
                "entity_id": requirement_id,
                "if_match_version": version_hint,
                "data": {"name": name},
            },
        )

    first, second = await asyncio.gather(update("Req v1", version), update("Req v2", version))

    assert first["success"] ^ second["success"]
    assert "Concurrent update" in (first.get("error", "") + second.get("error", ""))


@pytest.mark.asyncio
async def test_partial_batch_failure_handling(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Batch create returns error entries while continuing to create valid rows."""

    graph = await workflow_scenarios["complete_project"]()
    document_id = graph["document_ids"][0]
    result = await end_to_end_client.call_tool(
        "entity_tool",
        {
            "operation": "batch_create",
            "entity_type": "requirement",
            "batch": [
                {"name": "Valid Batch Req", "document_id": document_id},
                {"name": "Broken Req"},
            ],
        },
    )

    assert result["success"] is True
    created, error_entry = result["data"]
    assert "id" in created
    assert "error" in error_entry


@pytest.mark.asyncio
async def test_transaction_rolls_back_on_failure(
    deployment_harness,
    end_to_end_client,
):
    """Workflow failures should increment failure metrics and capture issues."""

    result = await end_to_end_client.call_tool(
        "workflow_tool",
        {
            "operation": "execute",
            "data": {"name": "rollback-flow", "simulate_failure": True, "failure_reason": "db"},
        },
    )

    assert result["success"] is False
    assert deployment_harness.metrics.failures == 1
    assert "db" in deployment_harness.get_issues()[0]


@pytest.mark.asyncio
async def test_orphaned_entity_cleanup(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Deleting dependencies followed by cleanup removes orphan relationships."""

    graph = await workflow_scenarios["complete_project"]()
    doc_id = graph["document_ids"][0]
    req_id = graph["requirement_ids"][0]

    initial_count = len(deployment_harness.get_relationships())
    await end_to_end_client.call_tool(
        "relationship_tool",
        {
            "operation": "create",
            "source_type": "document",
            "source_id": doc_id,
            "target_type": "requirement",
            "target_id": req_id,
            "relationship_type": "verifies",
        },
    )

    await end_to_end_client.call_tool(
        "entity_tool",
        {
            "operation": "delete",
            "entity_type": "requirement",
            "entity_id": req_id,
            "soft_delete": False,
        },
    )

    cleanup = await end_to_end_client.call_tool(
        "relationship_tool",
        {"operation": "cleanup_orphans"},
    )

    assert cleanup["success"] is True
    assert cleanup["data"]["removed"] >= 1
    assert len(deployment_harness.get_relationships()) == initial_count
