"""Abstract base class for realtime adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class RealtimeAdapter(ABC):
    """Abstract interface for real-time subscriptions."""
    
    @abstractmethod
    async def subscribe(
        self,
        table: str,
        callback: callable,
        *,
        filters: Optional[Dict[str, Any]] = None,
        events: Optional[List[str]] = None
    ) -> str:
        """Subscribe to real-time changes.
        
        Args:
            table: Table to watch
            callback: Function to call on changes
            filters: Filter conditions
            events: Event types to watch (INSERT, UPDATE, DELETE)
            
        Returns:
            Subscription ID
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from real-time changes.
        
        Args:
            subscription_id: Subscription to cancel
            
        Returns:
            True if unsubscribed, False if not found
        """
        pass

