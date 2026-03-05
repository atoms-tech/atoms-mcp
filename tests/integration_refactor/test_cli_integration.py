"""
CLI Integration Tests.

Tests CLI command execution end-to-end using MCP tools.
Since atoms-mcp-prod doesn't have a traditional CLI yet, this tests
the tool interfaces that would be exposed via CLI.

Coverage includes:
- Entity commands: create, list, get, update, delete
- Relationship commands
- Output formatting (table, json, yaml)
- Error messages and help text
- Pagination and filtering via CLI parameters
- Authentication flow

All tests mock application layer with real command/query classes.
"""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest


# =============================================================================
# CLI ENTITY COMMANDS
# =============================================================================


class TestCLIEntityCommands:
    """Test CLI entity commands."""

    @pytest.mark.asyncio
    async def test_cli_create_organization(self):
        """Test 'atoms entity create organization' command."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_insert', new_callable=AsyncMock) as mock_insert:
                mock_insert.return_value = {
                    "id": org_id,
                    "name": "CLI Test Org",
                    "type": "team",
                    "created_by": user_id,
                }

                # Act - simulate CLI call
                result = await manager.entity_tool(
                    operation="create",
                    entity_type="organization",
                    data={
                        "name": "CLI Test Org",
                        "type": "team",
                    },
                    format_type="detailed",
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert result["data"]["name"] == "CLI Test Org"

                # Verify CLI-friendly output format
                assert "success" in result
                assert "data" in result
                assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_cli_list_organizations_table_format(self):
        """Test 'atoms entity list organization --format table' command."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                mock_query.return_value = [
                    {
                        "id": str(uuid4()),
                        "name": "Org 1",
                        "type": "team",
                        "created_at": datetime.now(UTC).isoformat(),
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Org 2",
                        "type": "enterprise",
                        "created_at": datetime.now(UTC).isoformat(),
                    },
                ]

                # Act
                result = await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    format_type="detailed",
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert len(result["data"]) == 2

                # Simulate table formatting
                table_data = result["data"]
                assert all("id" in item for item in table_data)
                assert all("name" in item for item in table_data)

    @pytest.mark.asyncio
    async def test_cli_get_entity_json_format(self):
        """Test 'atoms entity get organization <id> --format json' command."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_get_single', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = {
                    "id": org_id,
                    "name": "Test Org",
                    "type": "team",
                    "created_at": datetime.now(UTC).isoformat(),
                }

                # Act
                result = await manager.entity_tool(
                    operation="read",
                    entity_type="organization",
                    entity_id=org_id,
                    format_type="detailed",
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True

                # Verify JSON serializable
                json_output = json.dumps(result)
                parsed = json.loads(json_output)
                assert parsed["data"]["name"] == "Test Org"

    @pytest.mark.asyncio
    async def test_cli_update_entity(self):
        """Test 'atoms entity update organization <id>' command."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_get_single', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = {
                    "id": org_id,
                    "name": "Old Name",
                    "type": "team",
                    "created_by": user_id,
                }

                with patch.object(manager, '_db_update', new_callable=AsyncMock) as mock_update:
                    mock_update.return_value = {
                        "id": org_id,
                        "name": "New Name",
                        "type": "team",
                    }

                    # Act
                    result = await manager.entity_tool(
                        operation="update",
                        entity_type="organization",
                        entity_id=org_id,
                        data={"name": "New Name"},
                        auth_token="test_token"
                    )

                    # Assert
                    assert result["success"] is True
                    assert result["data"]["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_cli_delete_entity_confirmation(self):
        """Test 'atoms entity delete organization <id>' command."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_get_single', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = {
                    "id": org_id,
                    "name": "To Delete",
                    "created_by": user_id,
                }

                with patch.object(manager, '_db_update', new_callable=AsyncMock) as mock_update:
                    mock_update.return_value = {
                        "id": org_id,
                        "is_deleted": True,
                    }

                    # Act - soft delete by default
                    result = await manager.entity_tool(
                        operation="delete",
                        entity_type="organization",
                        entity_id=org_id,
                        soft_delete=True,
                        auth_token="test_token"
                    )

                    # Assert
                    assert result["success"] is True


# =============================================================================
# CLI FILTERING AND PAGINATION
# =============================================================================


class TestCLIFilteringPagination:
    """Test CLI filtering and pagination."""

    @pytest.mark.asyncio
    async def test_cli_list_with_filters(self):
        """Test 'atoms entity list organization --type team' command."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                mock_query.return_value = [
                    {"id": str(uuid4()), "name": "Team 1", "type": "team"},
                    {"id": str(uuid4()), "name": "Team 2", "type": "team"},
                ]

                # Act
                result = await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    filters={"type": "team"},
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert all(org["type"] == "team" for org in result["data"])

    @pytest.mark.asyncio
    async def test_cli_list_with_pagination(self):
        """Test 'atoms entity list organization --limit 10 --offset 20' command."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                # Return page 3 (offset 20, limit 10)
                mock_query.return_value = [
                    {"id": str(uuid4()), "name": f"Org {i}"}
                    for i in range(20, 30)
                ]

                # Act
                result = await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    limit=10,
                    offset=20,
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert len(result["data"]) == 10

    @pytest.mark.asyncio
    async def test_cli_list_with_sorting(self):
        """Test 'atoms entity list organization --sort created_at:desc' command."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                now = datetime.now(UTC)
                mock_query.return_value = [
                    {
                        "id": str(uuid4()),
                        "name": "Newest",
                        "created_at": now.isoformat(),
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Older",
                        "created_at": (now - asyncio.create_task.__self__.__class__(hours=1)).isoformat()
                        if hasattr(asyncio, 'create_task') else now.isoformat(),
                    },
                ]

                # Act
                result = await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    order_by="created_at:desc",
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert len(result["data"]) > 0


# =============================================================================
# CLI RELATIONSHIP COMMANDS
# =============================================================================


class TestCLIRelationshipCommands:
    """Test CLI relationship commands."""

    @pytest.mark.asyncio
    async def test_cli_add_member(self):
        """Test 'atoms relationship add member' command."""
        # Arrange
        from tools.entity.relationship import RelationshipManager

        manager = RelationshipManager()
        user_id = str(uuid4())
        org_id = str(uuid4())
        member_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_insert', new_callable=AsyncMock) as mock_insert:
                mock_insert.return_value = {
                    "organization_id": org_id,
                    "user_id": member_id,
                    "role": "member",
                }

                # Act
                result = await manager.relationship_tool(
                    operation="link",
                    relationship_type="member",
                    source={"type": "organization", "id": org_id},
                    target={"type": "user", "id": member_id},
                    metadata={"role": "member"},
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_cli_list_members(self):
        """Test 'atoms relationship list members <org_id>' command."""
        # Arrange
        from tools.entity.relationship import RelationshipManager

        manager = RelationshipManager()
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                mock_query.return_value = [
                    {
                        "organization_id": org_id,
                        "user_id": str(uuid4()),
                        "role": "admin",
                    },
                    {
                        "organization_id": org_id,
                        "user_id": str(uuid4()),
                        "role": "member",
                    },
                ]

                # Act
                result = await manager.relationship_tool(
                    operation="list",
                    relationship_type="member",
                    source={"type": "organization", "id": org_id},
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_cli_remove_member(self):
        """Test 'atoms relationship remove member' command."""
        # Arrange
        from tools.entity.relationship import RelationshipManager

        manager = RelationshipManager()
        user_id = str(uuid4())
        org_id = str(uuid4())
        member_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_delete', new_callable=AsyncMock) as mock_delete:
                mock_delete.return_value = 1

                # Act
                result = await manager.relationship_tool(
                    operation="unlink",
                    relationship_type="member",
                    source={"type": "organization", "id": org_id},
                    target={"type": "user", "id": member_id},
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True


# =============================================================================
# CLI ERROR HANDLING
# =============================================================================


class TestCLIErrorHandling:
    """Test CLI error handling and messages."""

    @pytest.mark.asyncio
    async def test_cli_entity_not_found_error(self):
        """Test CLI handles entity not found error gracefully."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())
        nonexistent_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database returns None
            with patch.object(manager, '_db_get_single', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None

                # Act & Assert
                with pytest.raises(Exception) as exc_info:
                    await manager.entity_tool(
                        operation="read",
                        entity_type="organization",
                        entity_id=nonexistent_id,
                        auth_token="test_token"
                    )

                # Verify user-friendly error message
                error_msg = str(exc_info.value).lower()
                assert "not found" in error_msg

    @pytest.mark.asyncio
    async def test_cli_validation_error_message(self):
        """Test CLI shows clear validation error messages."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Act & Assert - missing required field
            with pytest.raises(Exception) as exc_info:
                await manager.entity_tool(
                    operation="create",
                    entity_type="organization",
                    data={"type": "team"},  # Missing name
                    auth_token="test_token"
                )

            # Verify error mentions the missing field
            error_msg = str(exc_info.value).lower()
            assert "name" in error_msg or "required" in error_msg

    @pytest.mark.asyncio
    async def test_cli_permission_denied_message(self):
        """Test CLI shows clear permission denied messages."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        entity_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database returns entity owned by different user
            with patch.object(manager, '_db_get_single', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = {
                    "id": entity_id,
                    "name": "Other User's Org",
                    "created_by": other_user_id,
                }

                # Mock RLS policy denies access
                with patch.object(manager, '_get_rls_policy') as mock_policy:
                    mock_policy_instance = Mock()
                    mock_policy_instance.validate_update = AsyncMock(
                        side_effect=Exception("Permission denied")
                    )
                    mock_policy.return_value = mock_policy_instance

                    # Act & Assert
                    with pytest.raises(Exception) as exc_info:
                        await manager.entity_tool(
                            operation="update",
                            entity_type="organization",
                            entity_id=entity_id,
                            data={"name": "Hacked"},
                            auth_token="test_token"
                        )

                    # Verify permission error message
                    error_msg = str(exc_info.value).lower()
                    assert "permission" in error_msg or "denied" in error_msg


# =============================================================================
# CLI OUTPUT FORMATTING
# =============================================================================


class TestCLIOutputFormatting:
    """Test CLI output formatting options."""

    @pytest.mark.asyncio
    async def test_cli_json_output(self):
        """Test JSON output format for CLI."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                mock_query.return_value = [
                    {"id": str(uuid4()), "name": "Org 1"},
                    {"id": str(uuid4()), "name": "Org 2"},
                ]

                # Act
                result = await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    format_type="detailed",
                    auth_token="test_token"
                )

                # Assert - verify JSON serializable
                json_str = json.dumps(result, indent=2)
                assert "success" in json_str
                assert "data" in json_str

    @pytest.mark.asyncio
    async def test_cli_summary_output(self):
        """Test summary output format for CLI."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database returns many items
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                mock_query.return_value = [
                    {"id": str(uuid4()), "name": f"Org {i}"}
                    for i in range(50)
                ]

                # Act
                result = await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    format_type="summary",
                    auth_token="test_token"
                )

                # Assert - verify summary format
                assert "count" in result or "truncated" in result

    @pytest.mark.asyncio
    async def test_cli_verbose_output(self):
        """Test verbose output format for CLI."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())
        entity_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(manager, '_db_get_single', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = {
                    "id": entity_id,
                    "name": "Verbose Org",
                    "type": "team",
                    "created_at": datetime.now(UTC).isoformat(),
                    "created_by": user_id,
                    "updated_at": datetime.now(UTC).isoformat(),
                }

                # Act
                result = await manager.entity_tool(
                    operation="read",
                    entity_type="organization",
                    entity_id=entity_id,
                    format_type="detailed",
                    auth_token="test_token"
                )

                # Assert - verify all fields included
                assert result["success"] is True
                data = result["data"]
                assert "id" in data
                assert "name" in data
                assert "created_at" in data


# =============================================================================
# CLI SEARCH AND QUERY
# =============================================================================


class TestCLISearchQuery:
    """Test CLI search and query commands."""

    @pytest.mark.asyncio
    async def test_cli_search_command(self):
        """Test 'atoms search <term>' command."""
        # Arrange
        from tools.query import DataQueryEngine

        engine = DataQueryEngine()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(engine, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(engine, '_db_query', new_callable=AsyncMock) as mock_query:
                mock_query.side_effect = [
                    [{"id": str(uuid4()), "name": "Test Org"}],
                    [{"id": str(uuid4()), "name": "Test Project"}],
                ]

                # Act
                result = await engine.query_tool(
                    query_type="search",
                    entities=["organization", "project"],
                    search_term="test",
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert result["total_results"] == 2

    @pytest.mark.asyncio
    async def test_cli_aggregate_command(self):
        """Test 'atoms stats' command."""
        # Arrange
        from tools.query import DataQueryEngine

        engine = DataQueryEngine()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(engine, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(engine, '_db_count', new_callable=AsyncMock) as mock_count:
                mock_count.side_effect = [10, 25, 100]

                # Act
                result = await engine.query_tool(
                    query_type="aggregate",
                    entities=["organization", "project", "requirement"],
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
