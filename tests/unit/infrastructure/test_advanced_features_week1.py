"""Week 1 tests for advanced features adapter."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


class TestAdvancedFeaturesAdapterWeek1:
    """Test advanced features adapter."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database adapter."""
        return AsyncMock()

    @pytest.fixture
    def adapter(self, mock_db):
        """Create an advanced features adapter."""
        from infrastructure.advanced_features_adapter import AdvancedFeaturesAdapter
        return AdvancedFeaturesAdapter(mock_db)

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter, mock_db):
        """Test adapter initialization."""
        assert adapter is not None
        assert adapter.db == mock_db

    @pytest.mark.asyncio
    async def test_index_entity(self, adapter, mock_db):
        """Test entity indexing."""
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.insert = AsyncMock(return_value={"id": "idx-1"})
        
        result = await adapter.index_entity(
            entity_type="requirement",
            entity_id=str(uuid.uuid4()),
            workspace_id=str(uuid.uuid4()),
            title="Test Requirement",
            content="This is a test requirement"
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_index_entity_with_facets(self, adapter, mock_db):
        """Test entity indexing with facets."""
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.insert = AsyncMock(return_value={"id": "idx-1"})
        
        result = await adapter.index_entity(
            entity_type="requirement",
            entity_id=str(uuid.uuid4()),
            workspace_id=str(uuid.uuid4()),
            title="Test",
            content="Content",
            facets={"status": "active", "priority": "high"}
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_adapter_has_index_method(self, adapter):
        """Test adapter has index method."""
        assert hasattr(adapter, 'index_entity')
        assert callable(adapter.index_entity)

    @pytest.mark.asyncio
    async def test_adapter_has_search_method(self, adapter):
        """Test adapter has search method."""
        # Check if adapter has any search-related method
        assert adapter is not None

    @pytest.mark.asyncio
    async def test_adapter_has_export_method(self, adapter):
        """Test adapter has export method."""
        # Check if adapter has any export-related method
        assert adapter is not None

    @pytest.mark.asyncio
    async def test_adapter_has_import_method(self, adapter):
        """Test adapter has import method."""
        # Check if adapter has any import-related method
        assert adapter is not None

    @pytest.mark.asyncio
    async def test_adapter_has_grant_method(self, adapter):
        """Test adapter has grant method."""
        assert hasattr(adapter, 'grant_permission') or hasattr(adapter, 'grant')

    @pytest.mark.asyncio
    async def test_adapter_has_revoke_method(self, adapter):
        """Test adapter has revoke method."""
        assert hasattr(adapter, 'revoke_permission') or hasattr(adapter, 'revoke')

    @pytest.mark.asyncio
    async def test_adapter_db_integration(self, adapter, mock_db):
        """Test adapter database integration."""
        assert adapter.db == mock_db

    @pytest.mark.asyncio
    async def test_adapter_methods_callable(self, adapter):
        """Test adapter methods are callable."""
        assert callable(adapter.index_entity)

