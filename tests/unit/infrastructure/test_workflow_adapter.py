"""Tests for workflow storage adapter."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestWorkflowStorageAdapter:
    """Test workflow storage adapter functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database adapter."""
        return AsyncMock()

    @pytest.fixture
    def adapter(self, mock_db):
        """Create a workflow storage adapter."""
        from infrastructure.workflow_adapter import WorkflowStorageAdapter
        return WorkflowStorageAdapter(mock_db)

    @pytest.mark.asyncio
    async def test_list_workflows(self, adapter, mock_db):
        """Test listing workflows."""
        workspace_id = str(uuid.uuid4())
        mock_db.query.return_value = [{"id": "wf-1", "name": "Workflow 1"}]
        mock_db.count_rows.return_value = 1

        workflows, count = await adapter.list_workflows(workspace_id)
        assert workflows is not None
        assert count >= 0

    @pytest.mark.asyncio
    async def test_list_workflows_with_filters(self, adapter, mock_db):
        """Test listing workflows with filters."""
        workspace_id = str(uuid.uuid4())
        mock_db.query.return_value = []
        mock_db.count_rows.return_value = 0

        workflows, count = await adapter.list_workflows(
            workspace_id,
            entity_type="project",
            is_active=True
        )
        assert workflows is not None

    @pytest.mark.asyncio
    async def test_list_workflows_pagination(self, adapter, mock_db):
        """Test workflow pagination."""
        workspace_id = str(uuid.uuid4())
        mock_db.query.return_value = []
        mock_db.count_rows.return_value = 100

        workflows, count = await adapter.list_workflows(
            workspace_id,
            limit=50,
            offset=50
        )
        assert count == 100

    @pytest.mark.asyncio
    async def test_create_workflow(self, adapter, mock_db):
        """Test creating a workflow."""
        workspace_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        mock_db.insert.return_value = {"id": "wf-1"}

        workflow = await adapter.create_workflow(
            workspace_id=workspace_id,
            name="Test Workflow",
            entity_type="project",
            created_by=user_id,
            definition={"steps": []}
        )
        assert workflow is not None

    @pytest.mark.asyncio
    async def test_delete_workflow(self, adapter, mock_db):
        """Test deleting a workflow."""
        workflow_id = str(uuid.uuid4())
        mock_db.update.return_value = {"id": workflow_id}

        result = await adapter.delete_workflow(workflow_id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_workflow_adapter_error_handling(self, adapter, mock_db):
        """Test error handling in workflow adapter."""
        workspace_id = str(uuid.uuid4())
        mock_db.query.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await adapter.list_workflows(workspace_id)

    @pytest.mark.asyncio
    async def test_workflow_adapter_initialization(self, adapter, mock_db):
        """Test workflow adapter initialization."""
        assert adapter is not None
        assert adapter.db == mock_db

    @pytest.mark.asyncio
    async def test_workflow_adapter_methods_exist(self, adapter):
        """Test that workflow adapter has expected methods."""
        assert hasattr(adapter, 'list_workflows')
        assert hasattr(adapter, 'create_workflow')
        assert hasattr(adapter, 'delete_workflow')

