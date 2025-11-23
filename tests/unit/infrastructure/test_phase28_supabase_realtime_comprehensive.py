"""Phase 28: Comprehensive tests for SupabaseRealtimeAdapter to reach 85%+ coverage."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Callable


class TestSupabaseRealtimeAdapter:
    """Comprehensive tests for SupabaseRealtimeAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create SupabaseRealtimeAdapter instance."""
        from infrastructure.supabase_realtime import SupabaseRealtimeAdapter
        return SupabaseRealtimeAdapter()

    @pytest.fixture
    def mock_supabase_client(self):
        """Create mock Supabase client."""
        mock = MagicMock()
        mock_table = MagicMock()
        mock_table.on.return_value.subscribe.return_value = MagicMock()
        mock.table.return_value = mock_table
        mock.remove_subscription = MagicMock()
        return mock

    @pytest.mark.asyncio
    async def test_subscribe_basic(self, adapter, mock_supabase_client):
        """Test basic subscription."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback = MagicMock()
            subscription_id = await adapter.subscribe("documents", callback)
            
            assert subscription_id is not None
            assert subscription_id in adapter._subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_with_filters(self, adapter, mock_supabase_client):
        """Test subscription with filters."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback = MagicMock()
            subscription_id = await adapter.subscribe(
                "documents",
                callback,
                filters={"status": "active"}
            )
            
            assert subscription_id is not None

    @pytest.mark.asyncio
    async def test_subscribe_with_events(self, adapter, mock_supabase_client):
        """Test subscription with specific events."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback = MagicMock()
            subscription_id = await adapter.subscribe(
                "documents",
                callback,
                events=["INSERT", "UPDATE"]
            )
            
            assert subscription_id is not None

    @pytest.mark.asyncio
    async def test_subscribe_default_events(self, adapter, mock_supabase_client):
        """Test subscription with default events."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback = MagicMock()
            subscription_id = await adapter.subscribe("documents", callback)
            
            assert subscription_id is not None

    @pytest.mark.asyncio
    async def test_subscribe_error_handling(self, adapter, mock_supabase_client):
        """Test subscription error handling."""
        mock_supabase_client.table.return_value.on.side_effect = Exception("Connection error")
        
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback = MagicMock()
            with pytest.raises(Exception):
                await adapter.subscribe("documents", callback)

    @pytest.mark.asyncio
    async def test_unsubscribe_success(self, adapter, mock_supabase_client):
        """Test successful unsubscribe."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback = MagicMock()
            subscription_id = await adapter.subscribe("documents", callback)
            
            result = await adapter.unsubscribe(subscription_id)
            
            assert result is True
            assert subscription_id not in adapter._subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe_invalid_id(self, adapter):
        """Test unsubscribe with invalid ID."""
        result = await adapter.unsubscribe("invalid_id")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe_error_handling(self, adapter, mock_supabase_client):
        """Test unsubscribe error handling."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback = MagicMock()
            subscription_id = await adapter.subscribe("documents", callback)
            
            # Cause error during unsubscribe
            mock_supabase_client.remove_subscription.side_effect = Exception("Error")
            
            result = await adapter.unsubscribe(subscription_id)
            
            assert result is False

    def test_list_subscriptions(self, adapter, mock_supabase_client):
        """Test listing subscriptions."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback1 = MagicMock()
            callback2 = MagicMock()
            
            # Create subscriptions
            import asyncio
            sub1 = asyncio.run(adapter.subscribe("documents", callback1))
            sub2 = asyncio.run(adapter.subscribe("requirements", callback2))
            
            subscriptions = adapter.list_subscriptions()
            
            assert len(subscriptions) == 2
            assert sub1 in subscriptions
            assert sub2 in subscriptions

    def test_get_subscription_info(self, adapter, mock_supabase_client):
        """Test getting subscription info."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            callback = MagicMock()
            import asyncio
            subscription_id = asyncio.run(adapter.subscribe("documents", callback))
            
            info = adapter.get_subscription_info(subscription_id)
            
            assert info is not None
            assert info["subscription_id"] == subscription_id
            assert info["table"] == "documents"
            assert info["active"] is True

    def test_get_subscription_info_invalid(self, adapter):
        """Test getting info for invalid subscription."""
        info = adapter.get_subscription_info("invalid_id")
        
        assert info is None

    def test_get_client_caching(self, adapter, mock_supabase_client):
        """Test client caching."""
        with patch('infrastructure.supabase_realtime.get_supabase', return_value=mock_supabase_client):
            client1 = adapter._get_client()
            client2 = adapter._get_client()
            
            assert client1 is client2
            assert adapter._client is not None
