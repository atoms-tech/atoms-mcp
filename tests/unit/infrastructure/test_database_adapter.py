"""Parametrized coverage for Supabase database adapter behaviors."""

from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest
from unittest.mock import MagicMock

from infrastructure.supabase_db import SupabaseDatabaseAdapter
from tests.framework.conftest_shared import EntityFactory, AssertionHelpers
from errors import ApiError


pytestmark = [pytest.mark.asyncio]


def _build_query_mock(return_data: List[Dict[str, Any]] | None = None, count: int | None = None) -> MagicMock:
    """Create a Supabase-styled query mock with fluent methods."""

    query = MagicMock()
    for method in ("select", "eq", "neq", "gt", "gte", "lt", "lte",
                   "like", "ilike", "in_", "contains", "order",
                   "limit", "range", "single", "or_", "is_"):
        getattr(query, method).return_value = query

    query.execute.return_value = SimpleNamespace(data=return_data, count=count)
    return query


@pytest.fixture
def adapter_fixture(monkeypatch):
    """Provide adapter with patched Supabase client."""

    adapter = SupabaseDatabaseAdapter()
    client = MagicMock()
    table = MagicMock()
    query = _build_query_mock([])

    table.select.return_value = query
    table.insert.return_value = query
    table.update.return_value = query
    table.delete.return_value = query

    client.from_.return_value = table
    adapter._get_client = MagicMock(return_value=client)  # type: ignore[attr-defined]

    return adapter, client, table, query


def _mode_params():
    return [
        pytest.param("unit", marks=pytest.mark.unit, id="unit"),
        pytest.param("integration", marks=pytest.mark.integration, id="integration"),
        pytest.param("e2e", marks=pytest.mark.e2e, id="e2e"),
    ]


@pytest.mark.parametrize("mode", _mode_params())
async def test_query_supports_complex_filters(mode, adapter_fixture):
    adapter, client, table, query = adapter_fixture
    mock_data = [EntityFactory.organization(name="Complex Filters Org")]
    query.execute.return_value = SimpleNamespace(data=mock_data)

    filters = {
        "_or": [
            {"name": {"ilike": "%Org%"}},
            {"slug": {"eq": "complex"}},
        ],
        "metadata": {"contains": {"tier": "enterprise"}},
        "is_deleted": False,
    }

    result = await adapter.query(
        "organizations",
        select="id,name,slug",
        filters=filters,
        order_by="updated_at:desc",
        limit=5,
        offset=0,
    )

    wrapped = {"success": True, "data": result}
    AssertionHelpers.assert_success(wrapped, "database query")

    client.from_.assert_called_with("organizations")
    assert query.or_.called
    assert query.contains.called
    query.order.assert_called_with("updated_at", desc=True)
    query.limit.assert_called_with(5)


@pytest.mark.parametrize("mode", _mode_params())
async def test_query_hits_cache_before_db(mode, adapter_fixture):
    adapter, client, table, query = adapter_fixture
    mock_data = [EntityFactory.project(name="Cached Project")]
    query.execute.return_value = SimpleNamespace(data=mock_data)

    first = await adapter.query("projects", filters={"is_deleted": False})
    second = await adapter.query("projects", filters={"is_deleted": False})

    assert first == second
    assert client.from_.call_count == 1


@pytest.mark.parametrize("mode", _mode_params())
async def test_mutations_invalidate_cache(mode, adapter_fixture):
    adapter, client, table, query = adapter_fixture
    adapter._query_cache = {"projects": ([], 0.0)}
    insert_data = EntityFactory.project(id=str(uuid.uuid4()))  # Add ID
    query.execute.return_value = SimpleNamespace(data=[insert_data])

    created = await adapter.insert("projects", insert_data)
    assert created.get("name") == insert_data["name"]
    assert adapter._query_cache == {}

    update_data = {"description": "updated"}
    query.execute.return_value = SimpleNamespace(data=[{**insert_data, **update_data}])
    updated = await adapter.update("projects", update_data, {"id": insert_data["id"]})
    assert updated["description"] == "updated"

    query.execute.return_value = SimpleNamespace(data=[insert_data])
    deleted = await adapter.delete("projects", {"id": insert_data["id"]})
    assert deleted == 1


@pytest.mark.parametrize("mode", _mode_params())
async def test_get_single_returns_none_on_not_found(mode, adapter_fixture):
    adapter, _, _, query = adapter_fixture

    class NotFoundError(Exception):
        code = "PGRST116"

    query.single.return_value = query
    query.execute.side_effect = NotFoundError()

    result = await adapter.get_single("projects", filters={"id": "missing"})
    assert result is None


@pytest.mark.parametrize("mode", _mode_params())
async def test_count_caches_results(mode, adapter_fixture):
    adapter, client, table, query = adapter_fixture
    query.execute.return_value = SimpleNamespace(count=7, data=None)

    first = await adapter.count("documents", filters={"project_id": "proj"})
    second = await adapter.count("documents", filters={"project_id": "proj"})

    assert first == second == 7
    assert client.from_.call_count == 1


@pytest.mark.parametrize("mode", _mode_params())
async def test_access_token_applied_for_rls(mode, monkeypatch):
    adapter = SupabaseDatabaseAdapter()
    captured = {}

    def fake_get_supabase(access_token=None):
        captured["token"] = access_token
        client = MagicMock()
        table = MagicMock()
        query = _build_query_mock([EntityFactory.organization()])
        table.select.return_value = query
        client.from_.return_value = table
        return client

    monkeypatch.setattr("infrastructure.supabase_db.get_supabase", fake_get_supabase)
    adapter.set_access_token("token-123")

    result = await adapter.query("organizations", limit=1)
    assert result
    assert captured["token"] == "token-123"


@pytest.mark.parametrize("mode", _mode_params())
async def test_query_normalizes_errors(mode, adapter_fixture):
    adapter, _, _, query = adapter_fixture

    query.execute.side_effect = RuntimeError("boom")

    with pytest.raises(ApiError):
        await adapter.query("projects")


@pytest.mark.parametrize("mode", _mode_params())
async def test_concurrent_queries_share_cache(mode, adapter_fixture):
    adapter, client, table, query = adapter_fixture
    query.execute.return_value = SimpleNamespace(data=[EntityFactory.document()])

    async def perform_query():
        return await adapter.query("documents", filters={"project_id": "proj"})

    results = await asyncio.gather(perform_query(), perform_query())
    assert results[0] == results[1]
    assert client.from_.call_count == 1


@pytest.mark.parametrize("mode", _mode_params())
async def test_transactional_sequence_simulated(mode, adapter_fixture):
    adapter, _, _, query = adapter_fixture
    org = EntityFactory.organization()
    project = EntityFactory.project(org_id=org.get("organization_id"), name="Txn Project")

    query.execute.side_effect = [
        SimpleNamespace(data=[project]),  # insert
        SimpleNamespace(data=[{**project, "name": "Txn Project v2"}]),  # update
        SimpleNamespace(data=[project]),  # delete returns 1 row
    ]

    created = await adapter.insert("projects", project)
    updated = await adapter.update("projects", {"name": "Txn Project v2"}, {"id": created.get("id")})
    deleted = await adapter.delete("projects", {"id": created.get("id")})

    assert updated["name"].endswith("v2")
    assert deleted == 1


@pytest.mark.parametrize("mode", _mode_params())
async def test_cached_counts_reduce_rate_limits(mode, adapter_fixture):
    adapter, client, table, query = adapter_fixture
    query.execute.return_value = SimpleNamespace(count=3)

    # First call populates cache
    await adapter.count("requirements", filters={"priority": "high"})

    # Simulate heavy load by zeroing execute count before second round
    client.from_.reset_mock()
    second = await adapter.count("requirements", filters={"priority": "high"})

    assert second == 3
    client.from_.assert_not_called()
