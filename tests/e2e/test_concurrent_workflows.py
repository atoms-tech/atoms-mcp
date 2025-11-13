"""Parallel workflow stress tests for full deployment mode."""

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
async def test_parallel_organization_creation(
    deployment_harness,
    workflow_scenarios,
    e2e_test_cleanup,
):
    """Scenario builder spins up 5 orgs concurrently without collisions."""

    track_entity, _ = e2e_test_cleanup
    report = await workflow_scenarios["parallel_workflow"]()

    assert report["total_created"] == 5
    assert report["successful"] == 5
    for org in report["organizations"]:
        track_entity("organization", org["id"])
        stored = deployment_harness.get_entities("organization")[org["id"]]
        assert stored["name"].startswith("Parallel Org")


@pytest.mark.asyncio
async def test_parallel_project_creation(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Create projects concurrently anchored to scenario org context."""

    graph = await workflow_scenarios["complete_project"]()
    org_id = graph["organization_id"]

    async def create_project(i: int):
        return await end_to_end_client.call_tool(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Parallel Project {i}",
                    "organization_id": org_id,
                },
            },
        )

    results = await asyncio.gather(*(create_project(i) for i in range(5)))
    assert all(result["success"] for result in results)

    project_store = deployment_harness.get_entities("project")
    assert len(project_store) >= 6  # scenario created one, plus 5 new
    assert {p["organization_id"] for p in project_store.values()} == {org_id}


@pytest.mark.asyncio
async def test_parallel_document_creation(
    deployment_harness,
    workflow_scenarios,
    end_to_end_client,
):
    """Documents created in parallel inherit the scenario project context."""

    graph = await workflow_scenarios["complete_project"]()
    project_id = graph["project_id"]

    async def create_doc(i: int):
        return await end_to_end_client.call_tool(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Parallel Doc {i}",
                    "project_id": project_id,
                },
            },
        )

    results = await asyncio.gather(*(create_doc(i) for i in range(6)))
    assert sum(1 for r in results if r["success"]) == 6

    docs = deployment_harness.get_entities("document")
    assert len(docs) >= len(graph["document_ids"]) + 6
    assert all(doc["project_id"] == project_id for doc in docs.values())


@pytest.mark.asyncio
async def test_success_rate_measurement(
    deployment_harness,
    end_to_end_client,
):
    """Measure workflow completion metrics under mixed outcomes."""

    async def run_workflow(index: int, fail: bool = False):
        return await end_to_end_client.call_tool(
            "workflow_tool",
            {
                "operation": "execute",
                "data": {
                    "name": f"wf-{index}",
                    "steps": ["create", "link", "finish"],
                    "simulate_failure": fail,
                    "failure_reason": "forced" if fail else None,
                },
            },
        )

    await asyncio.gather(*(run_workflow(i) for i in range(3)))
    await asyncio.gather(*(run_workflow(i, fail=True) for i in range(3, 5)))

    assert deployment_harness.metrics.runs == 5
    assert deployment_harness.metrics.successes == 3
    assert pytest.approx(deployment_harness.get_completion_rate(), 0.01) == 0.6


@pytest.mark.asyncio
async def test_no_data_corruption_during_parallel_flows(
    deployment_harness,
    end_to_end_client,
):
    """Validate that concurrent creations keep unique IDs and payloads intact."""

    async def create_org(i: int):
        return await end_to_end_client.call_tool(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": f"Integrity Org {i}"},
            },
        )

    await asyncio.gather(*(create_org(i) for i in range(10)))
    store = deployment_harness.get_entities("organization")

    assert len(store) >= 10
    assert len({org["name"] for org in store.values()}) == len(store)
