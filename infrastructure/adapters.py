"""Abstract base classes for infrastructure adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class AuthAdapter(ABC):
    """Abstract interface for authentication services."""
    
    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate an auth token and return user info.
        
        Args:
            token: JWT token or session token
            
        Returns:
            Dict containing user info: {"user_id": str, "username": str, ...}
            
        Raises:
            ValueError: If token is invalid or expired
        """
        pass
    
    @abstractmethod
    async def create_session(self, user_id: str, username: str) -> str:
        """Create a new session token.
        
        Args:
            user_id: User identifier
            username: User's username/email
            
        Returns:
            Session token string
        """
        pass
    
    @abstractmethod
    async def revoke_session(self, token: str) -> bool:
        """Revoke a session token.
        
        Args:
            token: Session token to revoke
            
        Returns:
            True if token was revoked, False if not found
        """
        pass
    
    @abstractmethod
    async def verify_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify username/password credentials.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            User info dict if valid, None if invalid
        """
        pass


class DatabaseAdapter(ABC):
    """Abstract interface for database operations."""
    
    @abstractmethod
    async def query(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query on a table.
        
        Args:
            table: Table name
            select: Columns to select (defaults to "*")
            filters: WHERE conditions
            order_by: ORDER BY clause
            limit: LIMIT clause
            offset: OFFSET clause
            
        Returns:
            List of matching records
        """
        pass
    
    @abstractmethod
    async def get_single(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a single record from a table.
        
        Args:
            table: Table name
            select: Columns to select
            filters: WHERE conditions
            
        Returns:
            Single record or None if not found
        """
        pass
    
    @abstractmethod
    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        returning: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Insert one or more records.
        
        Args:
            table: Table name
            data: Record(s) to insert
            returning: Columns to return
            
        Returns:
            Inserted record(s)
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        *,
        returning: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Update records.
        
        Args:
            table: Table name
            data: Updates to apply
            filters: WHERE conditions
            returning: Columns to return
            
        Returns:
            Updated record(s)
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        table: str,
        filters: Dict[str, Any]
    ) -> int:
        """Delete records.
        
        Args:
            table: Table name
            filters: WHERE conditions
            
        Returns:
            Number of deleted records
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count records in a table.
        
        Args:
            table: Table name
            filters: WHERE conditions
            
        Returns:
            Record count
        """
        pass


class StorageAdapter(ABC):
    """Abstract interface for file storage services."""
    
    @abstractmethod
    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload a file.
        
        Args:
            bucket: Storage bucket name
            path: File path within bucket
            data: File data
            content_type: MIME type
            metadata: Additional metadata
            
        Returns:
            Public URL or file identifier
        """
        pass
    
    @abstractmethod
    async def download(self, bucket: str, path: str) -> bytes:
        """Download a file.
        
        Args:
            bucket: Storage bucket name
            path: File path within bucket
            
        Returns:
            File data
        """
        pass
    
    @abstractmethod
    async def delete(self, bucket: str, path: str) -> bool:
        """Delete a file.
        
        Args:
            bucket: Storage bucket name
            path: File path within bucket
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def get_public_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file.
        
        Args:
            bucket: Storage bucket name
            path: File path within bucket
            
        Returns:
            Public URL
        """
        pass


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