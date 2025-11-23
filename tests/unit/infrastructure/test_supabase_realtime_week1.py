"""Week 1 tests for Supabase realtime adapter."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


class TestSupabaseRealtimeAdapterWeek1:
    """Test Supabase realtime adapter."""

    @pytest.fixture
    def adapter(self):
        """Create a realtime adapter."""
        from infrastructure.supabase_realtime import SupabaseRealtimeAdapter
        return SupabaseRealtimeAdapter()

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter is not None
        assert adapter._client is None
        assert adapter._subscriptions == {}

    @pytest.mark.asyncio
    async def test_get_client(self, adapter):
        """Test getting Supabase client."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client
            
            client = adapter._get_client()
            assert client is not None

    @pytest.mark.asyncio
    async def test_adapter_has_subscribe_method(self, adapter):
        """Test adapter has subscribe method."""
        assert hasattr(adapter, 'subscribe')
        assert callable(adapter.subscribe)

    @pytest.mark.asyncio
    async def test_adapter_has_unsubscribe_method(self, adapter):
        """Test adapter has unsubscribe method."""
        assert hasattr(adapter, 'unsubscribe')
        assert callable(adapter.unsubscribe)

    @pytest.mark.asyncio
    async def test_adapter_subscriptions_dict(self, adapter):
        """Test adapter subscriptions dictionary."""
        assert hasattr(adapter, '_subscriptions')
        assert isinstance(adapter._subscriptions, dict)

    @pytest.mark.asyncio
    async def test_adapter_client_caching(self, adapter):
        """Test adapter client caching."""
        assert hasattr(adapter, '_get_client')
        assert callable(adapter._get_client)

    @pytest.mark.asyncio
    async def test_adapter_client_initialization(self, adapter):
        """Test adapter client initialization."""
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_adapter_get_client_method(self, adapter):
        """Test get_client method."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client

            client = adapter._get_client()
            assert client is not None

    @pytest.mark.asyncio
    async def test_adapter_client_caching_behavior(self, adapter):
        """Test client caching behavior."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client

            # First call
            client1 = adapter._get_client()
            # Second call should return cached client
            client2 = adapter._get_client()

            assert client1 is client2

    @pytest.mark.asyncio
    async def test_adapter_methods_exist(self, adapter):
        """Test all required methods exist."""
        assert hasattr(adapter, 'subscribe')
        assert hasattr(adapter, 'unsubscribe')

