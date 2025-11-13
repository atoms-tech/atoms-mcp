"""Shared helpers for three-variant tool test suites."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pytest

from tests.framework.conftest_shared import (
    EntityFactory,
    AssertionHelpers,
    CommonTestScenarios,
)
from tests.framework.test_base import ParametrizedTestSuite

# Canonical variant parametrization (unit, integration, e2e)
CLIENT_VARIANT_PARAMS = [
    pytest.param("unit", marks=pytest.mark.unit, id="unit"),
    pytest.param("integration", marks=pytest.mark.integration, id="integration"),
    pytest.param("e2e", marks=pytest.mark.e2e, id="e2e"),
]

FIXTURE_MAP = {
    "unit": "mcp_client_inmemory",
    "integration": "mcp_client_http",
    "e2e": "end_to_end_client",
}

ENTITY_FACTORY = EntityFactory()
ASSERTIONS = AssertionHelpers
COMMON_SCENARIOS = CommonTestScenarios


def normalize_result(result: Any) -> Dict[str, Any]:
    """Normalize FastMCP CallToolResult into a dict with success/data/error."""
    if isinstance(result, dict):
        # Already a normalized response
        return result

    response_data = getattr(result, "data", None)
    if isinstance(response_data, dict) and "success" in response_data:
        return response_data

    # Fallback: build minimal response envelope
    normalized = {
        "success": getattr(result, "success", False),
        "data": response_data if isinstance(response_data, dict) else None,
        "error": getattr(result, "error", None) or getattr(result, "message", None),
    }
    return normalized


async def create_entity(
    client: Any,
    entity_type: str,
    data: Optional[Dict[str, Any]] = None,
    **extra
) -> Tuple[str, Dict[str, Any]]:
    payload = {
        "operation": "create",
        "entity_type": entity_type,
        "data": data or ENTITY_FACTORY.organization(),
    }
    payload.update(extra)
    result = await client.call_tool("entity_tool", payload)
    response = normalize_result(result)
    entity_id = ASSERTIONS.assert_entity_created(response, entity_type)
    return entity_id, response


async def read_entity(
    client: Any,
    entity_type: str,
    entity_id: str,
    **extra
) -> Dict[str, Any]:
    payload = {
        "operation": "read",
        "entity_type": entity_type,
        "entity_id": entity_id,
    }
    payload.update(extra)
    response = normalize_result(await client.call_tool("entity_tool", payload))
    return response


async def update_entity(
    client: Any,
    entity_type: str,
    entity_id: str,
    data: Dict[str, Any],
    **extra
) -> Dict[str, Any]:
    payload = {
        "operation": "update",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "data": data,
    }
    payload.update(extra)
    response = normalize_result(await client.call_tool("entity_tool", payload))
    ASSERTIONS.assert_success(response, f"Update {entity_type}")
    return response


async def delete_entity(
    client: Any,
    entity_type: str,
    entity_id: str,
    soft_delete: bool = True,
    **extra
) -> Dict[str, Any]:
    payload = {
        "operation": "delete",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "soft_delete": soft_delete,
    }
    payload.update(extra)
    response = normalize_result(await client.call_tool("entity_tool", payload))
    ASSERTIONS.assert_success(response, f"Delete {entity_type}")
    return response


class ThreeVariantTestSuite(ParametrizedTestSuite):
    """Base suite that parametrizes tests across unit/integration/e2e clients."""

    variant_params = CLIENT_VARIANT_PARAMS

    @pytest.fixture(params=CLIENT_VARIANT_PARAMS)
    async def client(self, request):
        mode = request.param
        fixture_name = FIXTURE_MAP[mode]
        try:
            client = request.getfixturevalue(fixture_name)
        except pytest.FixtureLookupError:
            pytest.skip(f"{fixture_name} fixture not available for {mode} tests")
        self.current_mode = mode
        return client


def scenario_ids(scenarios: List[Dict[str, Any]]) -> List[str]:
    """Utility to produce pytest ids from scenario definitions."""
    return [scenario.get("name", f"scenario_{idx}") for idx, scenario in enumerate(scenarios)]
