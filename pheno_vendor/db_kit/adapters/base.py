"""Abstract adapter interface for database operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class DatabaseAdapter(ABC):
    """Abstract interface for database adapters."""
    
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
        """Execute a SELECT query on a table.
        
        Args:
            table: Table name
            select: Columns to select (default: "*")
            filters: Filter conditions
            order_by: Order by clause (e.g., "created_at:desc")
            limit: Maximum rows to return
            offset: Number of rows to skip
            
        Returns:
            List of row dictionaries
        """
        pass
    
    @abstractmethod
    async def get_single(
        self,
        table: str,
        filters: Dict[str, Any],
        *,
        select: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a single row matching filters.
        
        Args:
            table: Table name
            filters: Filter conditions
            select: Columns to select (default: "*")
            
        Returns:
            Row dictionary or None if not found
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
        """Insert one or more rows.
        
        Args:
            table: Table name
            data: Row data (single dict or list of dicts)
            returning: Columns to return (default: "*")
            
        Returns:
            Inserted row(s)
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        table: str,
        filters: Dict[str, Any],
        data: Dict[str, Any],
        *,
        returning: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Update rows matching filters.
        
        Args:
            table: Table name
            filters: Filter conditions
            data: Update data
            returning: Columns to return (default: "*")
            
        Returns:
            Updated rows
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        table: str,
        filters: Dict[str, Any],
        *,
        returning: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Delete rows matching filters.
        
        Args:
            table: Table name
            filters: Filter conditions
            returning: Columns to return (default: "*")
            
        Returns:
            Deleted rows
        """
        pass
    
    @abstractmethod
    async def upsert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        conflict_columns: Optional[List[str]] = None,
        returning: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Insert or update rows.
        
        Args:
            table: Table name
            data: Row data (single dict or list of dicts)
            conflict_columns: Columns to check for conflicts
            returning: Columns to return (default: "*")
            
        Returns:
            Upserted row(s)
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        sql: str,
        params: Optional[Union[List, Dict]] = None
    ) -> Any:
        """Execute raw SQL query.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count rows matching filters.
        
        Args:
            table: Table name
            filters: Filter conditions
            
        Returns:
            Row count
        """
        pass
