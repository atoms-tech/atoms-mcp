"""Supabase realtime adapter implementation."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from .adapters import RealtimeAdapter
from ..supabase_client import get_supabase
from ..errors import normalize_error, ApiError


class SupabaseRealtimeAdapter(RealtimeAdapter):
    """Supabase-based realtime adapter."""
    
    def __init__(self):
        self._client = None
        self._subscriptions: Dict[str, Any] = {}
    
    def _get_client(self):
        """Get Supabase client, cached."""
        if self._client is None:
            self._client = get_supabase()
        return self._client
    
    async def subscribe(
        self,
        table: str,
        callback: callable,
        *,
        filters: Optional[Dict[str, Any]] = None,
        events: Optional[List[str]] = None
    ) -> str:
        """Subscribe to real-time changes on a table."""
        try:
            client = self._get_client()
            subscription_id = str(uuid.uuid4())
            
            # Default to all events if not specified
            if events is None:
                events = ["INSERT", "UPDATE", "DELETE"]
            
            # Create subscription configuration
            subscription_config = {
                "event": "*",  # Listen to all events by default
                "schema": "public",
                "table": table
            }
            
            # Apply filters if provided
            if filters:
                subscription_config["filter"] = filters
            
            # Note: This is a simplified implementation
            # In a real implementation, you'd need to handle Supabase's
            # realtime subscription API properly
            subscription = client.table(table).on(
                subscription_config["event"],
                callback
            ).subscribe()
            
            self._subscriptions[subscription_id] = {
                "subscription": subscription,
                "table": table,
                "callback": callback
            }
            
            return subscription_id
        
        except Exception as e:
            raise normalize_error(e, f"Failed to subscribe to {table}")
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from real-time changes."""
        try:
            if subscription_id not in self._subscriptions:
                return False
            
            subscription_info = self._subscriptions[subscription_id]
            subscription = subscription_info["subscription"]
            
            # Unsubscribe from Supabase
            client = self._get_client()
            client.remove_subscription(subscription)
            
            # Remove from our tracking
            del self._subscriptions[subscription_id]
            
            return True
        
        except Exception:
            return False
    
    def list_subscriptions(self) -> List[str]:
        """List active subscription IDs (utility method)."""
        return list(self._subscriptions.keys())
    
    def get_subscription_info(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get info about a subscription (utility method)."""
        if subscription_id not in self._subscriptions:
            return None
        
        info = self._subscriptions[subscription_id]
        return {
            "subscription_id": subscription_id,
            "table": info["table"],
            "active": True
        }