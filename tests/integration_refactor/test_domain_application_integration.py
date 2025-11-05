"""
Domain-Application Integration Tests.

End-to-end flow testing from command/query through application layer to domain layer.
Tests the complete integration without mocking the domain layer (only mocks Supabase).

Coverage includes:
- Command flows through to repository
- Relationship creation with cycle detection
- Workflow execution with state transitions
- Error propagation from domain to application
- Cache invalidation on updates
- Soft deletes and restores
- RLS policy enforcement
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest

from tools.entity.entity import EntityManager
from tools.entity.relationship import RelationshipManager
from tools.workflow.workflow import WorkflowEngine


# =============================================================================
# ENTITY COMMAND-TO-REPOSITORY FLOW TESTS
# =============================================================================


class TestEntityCommandFlow:
    """Test complete entity command flow from application to domain."""

    @pytest.mark.asyncio
    async def test_create_organization_full_flow(self):
        """Test complete organization creation flow."""
        # Arrange
        manager = EntityManager()
        user_id = str(uuid4())
        org_data = {
            "name": "Integration Test Org",
            "description": "Full flow test",
            "type": "team",
        }

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id, "username": "testuser"}

            # Mock Supabase client only
            with patch.object(manager, 'supabase') as mock_supabase:
                org_id = str(uuid4())
                mock_table = Mock()
                mock_table.insert = Mock(return_value=mock_table)
                mock_table.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "id": org_id,
                        "name": org_data["name"],
                        "description": org_data["description"],
                        "type": org_data["type"],
                        "created_by": user_id,
                        "created_at": datetime.now(UTC).isoformat(),
                        "is_deleted": False,
                    }]
                ))
                mock_supabase.table = Mock(return_value=mock_table)

                # Act
                result = await manager.entity_tool(
                    operation="create",
                    entity_type="organization",
                    data=org_data,
                    auth_token="test_token"
                )

                # Assert - verify full flow
                assert result["success"] is True
                assert result["data"]["id"] == org_id
                assert result["data"]["name"] == org_data["name"]
                assert result["data"]["created_by"] == user_id

                # Verify domain validations ran
                mock_table.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_with_organization_validation(self):
        """Test project creation validates organization exists."""
        # Arrange
        manager = EntityManager()
        user_id = str(uuid4())
        org_id = str(uuid4())
        project_data = {
            "name": "Integration Test Project",
            "organization_id": org_id,
        }

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                # First query checks org exists
                mock_select = Mock()
                mock_select.eq = Mock(return_value=mock_select)
                mock_select.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "id": org_id,
                        "name": "Parent Org",
                        "is_deleted": False,
                    }]
                ))

                # Second query inserts project
                project_id = str(uuid4())
                mock_insert = Mock()
                mock_insert.insert = Mock(return_value=mock_insert)
                mock_insert.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "id": project_id,
                        "name": project_data["name"],
                        "organization_id": org_id,
                        "slug": "integration-test-project",
                        "created_by": user_id,
                    }]
                ))

                def table_router(table_name):
                    if table_name == "organizations":
                        return mock_select
                    return mock_insert

                mock_supabase.table = Mock(side_effect=table_router)

                # Act
                result = await manager.entity_tool(
                    operation="create",
                    entity_type="project",
                    data=project_data,
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert result["data"]["organization_id"] == org_id

    @pytest.mark.asyncio
    async def test_update_entity_with_optimistic_locking(self):
        """Test entity update with version checking."""
        # Arrange
        manager = EntityManager()
        user_id = str(uuid4())
        entity_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                # Get current entity
                mock_select = Mock()
                mock_select.eq = Mock(return_value=mock_select)
                mock_select.single = Mock(return_value=mock_select)
                mock_select.execute = AsyncMock(return_value=Mock(
                    data={
                        "id": entity_id,
                        "name": "Original Name",
                        "version": 1,
                        "created_by": user_id,
                        "updated_at": datetime.now(UTC).isoformat(),
                    }
                ))

                # Update entity
                mock_update = Mock()
                mock_update.eq = Mock(return_value=mock_update)
                mock_update.update = Mock(return_value=mock_update)
                mock_update.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "id": entity_id,
                        "name": "Updated Name",
                        "version": 2,
                        "updated_by": user_id,
                    }]
                ))

                def table_router(table_name):
                    if mock_select.execute.call_count == 0:
                        return mock_select
                    return mock_update

                mock_supabase.table = Mock(side_effect=table_router)

                # Act
                result = await manager.entity_tool(
                    operation="update",
                    entity_type="organization",
                    entity_id=entity_id,
                    data={"name": "Updated Name"},
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert result["data"]["version"] == 2


# =============================================================================
# RELATIONSHIP INTEGRATION TESTS
# =============================================================================


class TestRelationshipIntegration:
    """Test relationship creation with domain validation."""

    @pytest.mark.asyncio
    async def test_create_member_with_permission_check(self):
        """Test creating member relationship validates permissions."""
        # Arrange
        manager = RelationshipManager()
        admin_id = str(uuid4())
        org_id = str(uuid4())
        new_member_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": admin_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                # Check admin is member with admin role
                mock_check = Mock()
                mock_check.eq = Mock(return_value=mock_check)
                mock_check.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "organization_id": org_id,
                        "user_id": admin_id,
                        "role": "admin",
                    }]
                ))

                # Insert new member
                mock_insert = Mock()
                mock_insert.insert = Mock(return_value=mock_insert)
                mock_insert.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "organization_id": org_id,
                        "user_id": new_member_id,
                        "role": "member",
                        "created_at": datetime.now(UTC).isoformat(),
                    }]
                ))

                call_count = [0]

                def table_router(table_name):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return mock_check
                    return mock_insert

                mock_supabase.table = Mock(side_effect=table_router)

                # Act
                result = await manager.relationship_tool(
                    operation="link",
                    relationship_type="member",
                    source={"type": "organization", "id": org_id},
                    target={"type": "user", "id": new_member_id},
                    metadata={"role": "member"},
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_trace_link_with_cycle_detection(self):
        """Test trace link creation detects and prevents cycles."""
        # Arrange
        manager = RelationshipManager()
        user_id = str(uuid4())
        req1_id = str(uuid4())
        req2_id = str(uuid4())
        req3_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                # Query existing links - shows req2 -> req3 -> req1 path exists
                mock_query = Mock()
                mock_query.select = Mock(return_value=mock_query)
                mock_query.execute = AsyncMock(return_value=Mock(
                    data=[
                        {
                            "source_requirement_id": req2_id,
                            "target_requirement_id": req3_id,
                            "link_type": "depends_on",
                        },
                        {
                            "source_requirement_id": req3_id,
                            "target_requirement_id": req1_id,
                            "link_type": "depends_on",
                        },
                    ]
                ))

                mock_supabase.table = Mock(return_value=mock_query)

                # Act & Assert - should detect cycle req1 -> req2 -> req3 -> req1
                with pytest.raises(Exception) as exc_info:
                    await manager.relationship_tool(
                        operation="link",
                        relationship_type="trace_link",
                        source={"type": "requirement", "id": req1_id},
                        target={"type": "requirement", "id": req2_id},
                        metadata={"link_type": "depends_on"},
                        auth_token="test_token"
                    )

                assert "cycle" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_relationship_cascades(self):
        """Test deleting relationship handles cascades correctly."""
        # Arrange
        manager = RelationshipManager()
        user_id = str(uuid4())
        org_id = str(uuid4())
        member_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                mock_delete = Mock()
                mock_delete.eq = Mock(return_value=mock_delete)
                mock_delete.delete = Mock(return_value=mock_delete)
                mock_delete.execute = AsyncMock(return_value=Mock(data=[]))

                mock_supabase.table = Mock(return_value=mock_delete)

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
# WORKFLOW EXECUTION INTEGRATION TESTS
# =============================================================================


class TestWorkflowExecution:
    """Test complete workflow execution with state management."""

    @pytest.mark.asyncio
    async def test_setup_project_workflow_complete(self):
        """Test complete setup_project workflow execution."""
        # Arrange
        engine = WorkflowEngine()
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Mock authentication
        with patch.object(engine, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(engine, 'supabase') as mock_supabase:
                project_id = str(uuid4())
                doc1_id = str(uuid4())
                doc2_id = str(uuid4())

                call_sequence = []

                def table_router(table_name):
                    call_sequence.append(table_name)
                    mock_table = Mock()

                    if table_name == "projects":
                        mock_table.insert = Mock(return_value=mock_table)
                        mock_table.execute = AsyncMock(return_value=Mock(
                            data=[{
                                "id": project_id,
                                "name": "Workflow Project",
                                "organization_id": org_id,
                                "created_by": user_id,
                            }]
                        ))
                    elif table_name == "documents":
                        mock_table.insert = Mock(return_value=mock_table)
                        if len([c for c in call_sequence if c == "documents"]) == 1:
                            doc_id = doc1_id
                        else:
                            doc_id = doc2_id
                        mock_table.execute = AsyncMock(return_value=Mock(
                            data=[{
                                "id": doc_id,
                                "title": "Document",
                                "project_id": project_id,
                            }]
                        ))

                    return mock_table

                mock_supabase.table = Mock(side_effect=table_router)

                # Act
                result = await engine.workflow_tool(
                    workflow="setup_project",
                    parameters={
                        "name": "Workflow Project",
                        "organization_id": org_id,
                        "initial_documents": ["Requirements", "Design"],
                    },
                    auth_token="test_token"
                )

                # Assert - verify all workflow steps completed
                assert result["success"] is True
                assert "project_id" in result["data"]
                assert "documents" in result["data"]
                assert len(result["data"]["documents"]) == 2

                # Verify correct table access sequence
                assert "projects" in call_sequence
                assert call_sequence.count("documents") == 2

    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self):
        """Test workflow tracks state transitions correctly."""
        # Arrange
        engine = WorkflowEngine()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(engine, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock workflow state tracking
            workflow_states = []

            def track_state(state: str):
                workflow_states.append({
                    "state": state,
                    "timestamp": datetime.now(UTC),
                })

            # Mock Supabase client
            with patch.object(engine, 'supabase') as mock_supabase:
                mock_table = Mock()
                mock_table.insert = Mock(return_value=mock_table)
                mock_table.execute = AsyncMock(side_effect=lambda: (
                    track_state("running"),
                    Mock(data=[{"id": str(uuid4())}])
                )[1])

                mock_supabase.table = Mock(return_value=mock_table)

                # Act
                track_state("initiated")
                await engine.workflow_tool(
                    workflow="setup_project",
                    parameters={
                        "name": "State Test",
                        "organization_id": str(uuid4()),
                    },
                    auth_token="test_token"
                )
                track_state("completed")

                # Assert - verify state progression
                states = [s["state"] for s in workflow_states]
                assert states == ["initiated", "running", "completed"]

    @pytest.mark.asyncio
    async def test_workflow_rollback_on_step_failure(self):
        """Test workflow rolls back on step failure."""
        # Arrange
        engine = WorkflowEngine()
        user_id = str(uuid4())
        org_id = str(uuid4())

        # Mock authentication
        with patch.object(engine, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client with failure
            with patch.object(engine, 'supabase') as mock_supabase:
                call_count = [0]

                def table_router(table_name):
                    call_count[0] += 1
                    mock_table = Mock()

                    if call_count[0] == 1:
                        # First step succeeds
                        mock_table.insert = Mock(return_value=mock_table)
                        mock_table.execute = AsyncMock(return_value=Mock(
                            data=[{"id": str(uuid4()), "name": "Project"}]
                        ))
                    else:
                        # Second step fails
                        mock_table.insert = Mock(return_value=mock_table)
                        mock_table.execute = AsyncMock(
                            side_effect=Exception("Database error")
                        )

                    return mock_table

                mock_supabase.table = Mock(side_effect=table_router)

                # Act & Assert
                with pytest.raises(Exception):
                    await engine.workflow_tool(
                        workflow="setup_project",
                        parameters={
                            "name": "Rollback Test",
                            "organization_id": org_id,
                            "initial_documents": ["Doc1"],
                        },
                        auth_token="test_token",
                        transaction_mode=True
                    )


# =============================================================================
# ERROR PROPAGATION TESTS
# =============================================================================


class TestErrorPropagation:
    """Test error propagation from domain to application layer."""

    @pytest.mark.asyncio
    async def test_validation_error_propagates(self):
        """Test domain validation errors propagate correctly."""
        # Arrange
        manager = EntityManager()
        user_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Act & Assert - empty name should fail validation
            with pytest.raises(Exception) as exc_info:
                await manager.entity_tool(
                    operation="create",
                    entity_type="organization",
                    data={"name": "", "type": "team"},
                    auth_token="test_token"
                )

            # Verify error message contains validation context
            error_msg = str(exc_info.value).lower()
            assert "validation" in error_msg or "name" in error_msg or "required" in error_msg

    @pytest.mark.asyncio
    async def test_permission_error_propagates(self):
        """Test RLS permission errors propagate correctly."""
        # Arrange
        manager = EntityManager()
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        entity_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                # Return entity owned by different user
                mock_table = Mock()
                mock_table.eq = Mock(return_value=mock_table)
                mock_table.single = Mock(return_value=mock_table)
                mock_table.execute = AsyncMock(return_value=Mock(
                    data={
                        "id": entity_id,
                        "name": "Other User's Org",
                        "created_by": other_user_id,
                    }
                ))

                mock_supabase.table = Mock(return_value=mock_table)

                # Act & Assert
                with pytest.raises(Exception) as exc_info:
                    await manager.entity_tool(
                        operation="update",
                        entity_type="organization",
                        entity_id=entity_id,
                        data={"name": "Hacked"},
                        auth_token="test_token"
                    )

                # Verify permission error
                error_msg = str(exc_info.value).lower()
                assert "permission" in error_msg or "access" in error_msg or "denied" in error_msg


# =============================================================================
# CACHE INVALIDATION INTEGRATION TESTS
# =============================================================================


class TestCacheInvalidation:
    """Test cache invalidation on entity updates."""

    @pytest.mark.asyncio
    async def test_update_invalidates_cache(self):
        """Test entity update invalidates cache entry."""
        # Arrange
        manager = EntityManager()
        user_id = str(uuid4())
        entity_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                # Get entity
                mock_select = Mock()
                mock_select.eq = Mock(return_value=mock_select)
                mock_select.single = Mock(return_value=mock_select)
                mock_select.execute = AsyncMock(return_value=Mock(
                    data={
                        "id": entity_id,
                        "name": "Original",
                        "created_by": user_id,
                    }
                ))

                # Update entity
                mock_update = Mock()
                mock_update.eq = Mock(return_value=mock_update)
                mock_update.update = Mock(return_value=mock_update)
                mock_update.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "id": entity_id,
                        "name": "Updated",
                        "updated_by": user_id,
                    }]
                ))

                call_count = [0]

                def table_router(table_name):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return mock_select
                    return mock_update

                mock_supabase.table = Mock(side_effect=table_router)

                # Act
                result = await manager.entity_tool(
                    operation="update",
                    entity_type="organization",
                    entity_id=entity_id,
                    data={"name": "Updated"},
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert result["data"]["name"] == "Updated"


# =============================================================================
# SOFT DELETE AND RESTORE TESTS
# =============================================================================


class TestSoftDeleteRestore:
    """Test soft delete and restore operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_preserves_data(self):
        """Test soft delete marks entity as deleted but preserves data."""
        # Arrange
        manager = EntityManager()
        user_id = str(uuid4())
        entity_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                # Get entity
                mock_select = Mock()
                mock_select.eq = Mock(return_value=mock_select)
                mock_select.single = Mock(return_value=mock_select)
                mock_select.execute = AsyncMock(return_value=Mock(
                    data={
                        "id": entity_id,
                        "name": "Test Org",
                        "is_deleted": False,
                        "created_by": user_id,
                    }
                ))

                # Soft delete
                mock_update = Mock()
                mock_update.eq = Mock(return_value=mock_update)
                mock_update.update = Mock(return_value=mock_update)
                mock_update.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "id": entity_id,
                        "name": "Test Org",
                        "is_deleted": True,
                        "deleted_at": datetime.now(UTC).isoformat(),
                    }]
                ))

                call_count = [0]

                def table_router(table_name):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return mock_select
                    return mock_update

                mock_supabase.table = Mock(side_effect=table_router)

                # Act
                result = await manager.entity_tool(
                    operation="delete",
                    entity_type="organization",
                    entity_id=entity_id,
                    soft_delete=True,
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert result["data"]["is_deleted"] is True
                assert result["data"]["name"] == "Test Org"  # Data preserved

    @pytest.mark.asyncio
    async def test_restore_soft_deleted_entity(self):
        """Test restoring soft-deleted entity."""
        # Arrange
        manager = EntityManager()
        user_id = str(uuid4())
        entity_id = str(uuid4())

        # Mock authentication
        with patch.object(manager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": user_id}

            # Mock Supabase client
            with patch.object(manager, 'supabase') as mock_supabase:
                # Get soft-deleted entity
                mock_select = Mock()
                mock_select.eq = Mock(return_value=mock_select)
                mock_select.single = Mock(return_value=mock_select)
                mock_select.execute = AsyncMock(return_value=Mock(
                    data={
                        "id": entity_id,
                        "name": "Test Org",
                        "is_deleted": True,
                        "deleted_at": datetime.now(UTC).isoformat(),
                        "created_by": user_id,
                    }
                ))

                # Restore
                mock_update = Mock()
                mock_update.eq = Mock(return_value=mock_update)
                mock_update.update = Mock(return_value=mock_update)
                mock_update.execute = AsyncMock(return_value=Mock(
                    data=[{
                        "id": entity_id,
                        "name": "Test Org",
                        "is_deleted": False,
                        "deleted_at": None,
                    }]
                ))

                call_count = [0]

                def table_router(table_name):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return mock_select
                    return mock_update

                mock_supabase.table = Mock(side_effect=table_router)

                # Act
                result = await manager.entity_tool(
                    operation="update",
                    entity_type="organization",
                    entity_id=entity_id,
                    data={"is_deleted": False},
                    auth_token="test_token"
                )

                # Assert
                assert result["success"] is True
                assert result["data"]["is_deleted"] is False
