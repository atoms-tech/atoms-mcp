"""
MCP Server Integration Tests.

Tests MCP server tool invocation end-to-end.
Tests actual MCP tool protocol including schema validation and error responses.

Coverage includes:
- entity_tools: create_entity, get_entity, list_entities
- relationship_tools: create_relationship, find_path
- query_tools: search_entities, get_analytics
- workflow_tools: execute_workflow
- Tool schema validation
- Error responses
- Authentication flow
"""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest


# =============================================================================
# MCP ENTITY TOOL TESTS
# =============================================================================


class TestMCPEntityTools:
    """Test MCP entity tools."""

    @pytest.mark.asyncio
    async def test_mcp_entity_tool_create(self):
        """Test entity_tool with create operation via MCP."""
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
                    "name": "MCP Test Org",
                    "type": "team",
                    "created_by": user_id,
                }

                # Act - call as MCP would
                result = await manager.entity_tool(
                    operation="create",
                    entity_type="organization",
                    data={
                        "name": "MCP Test Org",
                        "type": "team",
                    },
                    auth_token="oauth-session"
                )

                # Assert - verify MCP response format
                assert "success" in result
                assert "data" in result
                assert result["success"] is True
                assert result["data"]["id"] == org_id

    @pytest.mark.asyncio
    async def test_mcp_entity_tool_read(self):
        """Test entity_tool with read operation via MCP."""
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
                    "name": "MCP Org",
                    "type": "team",
                }

                # Act
                result = await manager.entity_tool(
                    operation="read",
                    entity_type="organization",
                    entity_id=entity_id,
                    auth_token="oauth-session"
                )

                # Assert
                assert result["success"] is True
                assert result["data"]["id"] == entity_id

    @pytest.mark.asyncio
    async def test_mcp_entity_tool_list(self):
        """Test entity_tool with list operation via MCP."""
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
                    limit=10,
                    offset=0,
                    auth_token="oauth-session"
                )

                # Assert
                assert result["success"] is True
                assert "data" in result
                assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_mcp_entity_tool_update(self):
        """Test entity_tool with update operation via MCP."""
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
                    "name": "Old Name",
                    "created_by": user_id,
                }

                with patch.object(manager, '_db_update', new_callable=AsyncMock) as mock_update:
                    mock_update.return_value = {
                        "id": entity_id,
                        "name": "Updated Name",
                    }

                    # Act
                    result = await manager.entity_tool(
                        operation="update",
                        entity_type="organization",
                        entity_id=entity_id,
                        data={"name": "Updated Name"},
                        auth_token="oauth-session"
                    )

                    # Assert
                    assert result["success"] is True
                    assert result["data"]["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_mcp_entity_tool_delete(self):
        """Test entity_tool with delete operation via MCP."""
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
                    "name": "To Delete",
                    "created_by": user_id,
                }

                with patch.object(manager, '_db_update', new_callable=AsyncMock) as mock_update:
                    mock_update.return_value = {
                        "id": entity_id,
                        "is_deleted": True,
                    }

                    # Act
                    result = await manager.entity_tool(
                        operation="delete",
                        entity_type="organization",
                        entity_id=entity_id,
                        soft_delete=True,
                        auth_token="oauth-session"
                    )

                    # Assert
                    assert result["success"] is True


# =============================================================================
# MCP RELATIONSHIP TOOL TESTS
# =============================================================================


class TestMCPRelationshipTools:
    """Test MCP relationship tools."""

    @pytest.mark.asyncio
    async def test_mcp_relationship_tool_link(self):
        """Test relationship_tool with link operation via MCP."""
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
                    auth_token="oauth-session"
                )

                # Assert
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_mcp_relationship_tool_list(self):
        """Test relationship_tool with list operation via MCP."""
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
                    {"user_id": str(uuid4()), "role": "admin"},
                    {"user_id": str(uuid4()), "role": "member"},
                ]

                # Act
                result = await manager.relationship_tool(
                    operation="list",
                    relationship_type="member",
                    source={"type": "organization", "id": org_id},
                    auth_token="oauth-session"
                )

                # Assert
                assert result["success"] is True
                assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_mcp_relationship_tool_find_path(self):
        """Test relationship_tool with find_path operation via MCP."""
        # Arrange
        from tools.entity.relationship import RelationshipManager

        manager = RelationshipManager()
        user_id = str(uuid4())
        req1_id = str(uuid4())
        req2_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock path finding
            with patch.object(manager, '_find_path', new_callable=AsyncMock) as mock_find:
                mock_find.return_value = {
                    "path": [req1_id, req2_id],
                    "length": 1,
                }

                # Act
                result = await manager.relationship_tool(
                    operation="find_path",
                    relationship_type="trace_link",
                    source={"type": "requirement", "id": req1_id},
                    target={"type": "requirement", "id": req2_id},
                    auth_token="oauth-session"
                )

                # Assert
                assert result["success"] is True
                assert "path" in result


# =============================================================================
# MCP QUERY TOOL TESTS
# =============================================================================


class TestMCPQueryTools:
    """Test MCP query tools."""

    @pytest.mark.asyncio
    async def test_mcp_query_tool_search(self):
        """Test query_tool with search operation via MCP."""
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
                    auth_token="oauth-session"
                )

                # Assert
                assert result["success"] is True
                assert "total_results" in result
                assert result["total_results"] == 2

    @pytest.mark.asyncio
    async def test_mcp_query_tool_aggregate(self):
        """Test query_tool with aggregate operation via MCP."""
        # Arrange
        from tools.query import DataQueryEngine

        engine = DataQueryEngine()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(engine, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database
            with patch.object(engine, '_db_count', new_callable=AsyncMock) as mock_count:
                mock_count.side_effect = [10, 25]

                # Act
                result = await engine.query_tool(
                    query_type="aggregate",
                    entities=["organization", "project"],
                    auth_token="oauth-session"
                )

                # Assert
                assert result["success"] is True
                assert "results_by_entity" in result

    @pytest.mark.asyncio
    async def test_mcp_query_tool_rag_search(self):
        """Test query_tool with RAG search via MCP."""
        # Arrange
        from tools.query import DataQueryEngine

        engine = DataQueryEngine()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(engine, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock RAG services
            with patch.object(engine, '_init_rag_services'):
                with patch.object(engine, '_embedding_service') as mock_embed:
                    mock_embed.embed_query = Mock(return_value=[0.1] * 768)

                    with patch.object(engine, '_vector_search_service') as mock_vector:
                        mock_vector.similarity_search = AsyncMock(return_value=[
                            {"id": str(uuid4()), "content": "Test", "similarity": 0.9}
                        ])

                        # Act
                        result = await engine.query_tool(
                            query_type="rag_search",
                            entities=["requirement"],
                            search_term="authentication",
                            rag_mode="semantic",
                            auth_token="oauth-session"
                        )

                        # Assert
                        assert result["success"] is True


# =============================================================================
# MCP WORKFLOW TOOL TESTS
# =============================================================================


class TestMCPWorkflowTools:
    """Test MCP workflow tools."""

    @pytest.mark.asyncio
    async def test_mcp_workflow_tool_setup_project(self):
        """Test workflow_tool with setup_project via MCP."""
        # Arrange
        from tools.workflow.workflow import WorkflowEngine

        engine = WorkflowEngine()
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Mock authentication
        with patch.object(engine, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock database operations
            with patch.object(engine, '_db_insert', new_callable=AsyncMock) as mock_insert:
                project_id = str(uuid4())
                mock_insert.side_effect = [
                    {"id": project_id, "name": "Test Project"},
                    {"id": str(uuid4()), "title": "Doc 1"},
                ]

                # Act
                result = await engine.workflow_tool(
                    workflow="setup_project",
                    parameters={
                        "name": "Test Project",
                        "organization_id": org_id,
                        "initial_documents": ["Requirements"],
                    },
                    auth_token="oauth-session"
                )

                # Assert
                assert result["success"] is True
                assert "project_id" in result["data"]


# =============================================================================
# MCP SCHEMA VALIDATION TESTS
# =============================================================================


class TestMCPSchemaValidation:
    """Test MCP tool schema validation."""

    @pytest.mark.asyncio
    async def test_mcp_entity_tool_validates_operation(self):
        """Test entity_tool validates operation parameter."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await manager.entity_tool(
                    operation="invalid_op",
                    entity_type="organization",
                    auth_token="oauth-session"
                )

            error_msg = str(exc_info.value).lower()
            assert "operation" in error_msg or "invalid" in error_msg

    @pytest.mark.asyncio
    async def test_mcp_entity_tool_validates_entity_type(self):
        """Test entity_tool validates entity_type parameter."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await manager.entity_tool(
                    operation="list",
                    entity_type="invalid_type",
                    auth_token="oauth-session"
                )

            error_msg = str(exc_info.value).lower()
            assert "entity" in error_msg or "type" in error_msg or "invalid" in error_msg

    @pytest.mark.asyncio
    async def test_mcp_relationship_tool_validates_source(self):
        """Test relationship_tool validates source parameter."""
        # Arrange
        from tools.entity.relationship import RelationshipManager

        manager = RelationshipManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Act & Assert - missing type in source
            with pytest.raises(Exception) as exc_info:
                await manager.relationship_tool(
                    operation="link",
                    relationship_type="member",
                    source={"id": str(uuid4())},  # Missing type
                    target={"type": "user", "id": str(uuid4())},
                    auth_token="oauth-session"
                )

            error_msg = str(exc_info.value).lower()
            assert "source" in error_msg or "type" in error_msg


# =============================================================================
# MCP ERROR RESPONSE TESTS
# =============================================================================


class TestMCPErrorResponses:
    """Test MCP tool error response format."""

    @pytest.mark.asyncio
    async def test_mcp_tool_authentication_error(self):
        """Test MCP tool returns proper error for authentication failure."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()

        # Mock failed authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = ValueError("Authentication failed")

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    auth_token="invalid_token"
                )

            assert "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_mcp_tool_validation_error(self):
        """Test MCP tool returns proper error for validation failure."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Act & Assert - invalid data
            with pytest.raises(Exception) as exc_info:
                await manager.entity_tool(
                    operation="create",
                    entity_type="organization",
                    data={},  # Missing required fields
                    auth_token="oauth-session"
                )

            error_msg = str(exc_info.value).lower()
            assert "validation" in error_msg or "required" in error_msg

    @pytest.mark.asyncio
    async def test_mcp_tool_not_found_error(self):
        """Test MCP tool returns proper error for not found."""
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
                        auth_token="oauth-session"
                    )

                assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_mcp_tool_permission_denied_error(self):
        """Test MCP tool returns proper error for permission denied."""
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
                    "name": "Other's Org",
                    "created_by": other_user_id,
                }

                # Mock RLS denies
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
                            auth_token="oauth-session"
                        )

                    error_msg = str(exc_info.value).lower()
                    assert "permission" in error_msg or "denied" in error_msg


# =============================================================================
# MCP PERFORMANCE TESTS
# =============================================================================


class TestMCPPerformance:
    """Test MCP tool performance characteristics."""

    @pytest.mark.asyncio
    async def test_mcp_tool_response_time(self):
        """Test MCP tool response time is acceptable."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock fast database
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                mock_query.return_value = [{"id": str(uuid4()), "name": "Org"}]

                # Act
                start = datetime.now(UTC)
                result = await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    auth_token="oauth-session"
                )
                elapsed = (datetime.now(UTC) - start).total_seconds()

                # Assert - should complete quickly
                assert result["success"] is True
                assert elapsed < 1.0  # Less than 1 second

    @pytest.mark.asyncio
    async def test_mcp_tool_handles_large_result_sets(self):
        """Test MCP tool handles large result sets efficiently."""
        # Arrange
        from tools.entity.entity import EntityManager

        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock large result set
            with patch.object(manager, '_db_query', new_callable=AsyncMock) as mock_query:
                mock_query.return_value = [
                    {"id": str(uuid4()), "name": f"Org {i}"}
                    for i in range(100)
                ]

                # Act
                result = await manager.entity_tool(
                    operation="list",
                    entity_type="organization",
                    auth_token="oauth-session"
                )

                # Assert - should truncate or paginate
                assert result["success"] is True
                # Should auto-paginate large results
                assert "truncated" in result or len(result["data"]) <= 10
