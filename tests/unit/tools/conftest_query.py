"""Shared fixtures for query tool tests."""

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def test_entities_fixture():
    """Fixture that just provides test entity data (no creation)."""
    return [
        {
            "name": "Python Web Application",
            "entity_type": "project",
            "description": "A web application built with Python Flask framework for REST APIs",
        },
        {
            "name": "Database Design Document",
            "entity_type": "document",
            "description": "Comprehensive database schema design for PostgreSQL",
        },
        {
            "name": "User Authentication Module",
            "entity_type": "project",
            "description": "JWT-based authentication system with OAuth2 integration",
        },
    ]


@pytest_asyncio.fixture
async def test_entities(call_mcp, test_entities_fixture):
    """Create test entities for search tests."""
    entity_ids = []
    
    for entity_data in test_entities_fixture:
        try:
            result, _ = await call_mcp("entity_tool", {
                "operation": "create",
                "entity_type": entity_data["entity_type"],
                "data": {
                    "name": entity_data["name"],
                    "description": entity_data.get("description", ""),
                }
            })
            if result.get("success"):
                entity_ids.append(result["data"]["id"])
        except Exception:
            # If entity creation fails, just continue
            pass
    
    yield entity_ids
    
    # Cleanup
    for entity_id in entity_ids:
        try:
            await call_mcp("entity_tool", {
                "operation": "delete",
                "entity_id": entity_id
            })
        except:
            pass
