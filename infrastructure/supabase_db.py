"""Supabase database adapter implementation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

try:
    from .adapters import DatabaseAdapter
    from ..supabase_client import get_supabase
    from ..errors import normalize_error
except ImportError:
    from infrastructure.adapters import DatabaseAdapter
    from supabase_client import get_supabase
    from errors import normalize_error


class SupabaseDatabaseAdapter(DatabaseAdapter):
    """Supabase-based database adapter with caching for serverless performance."""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._query_cache: Dict[str, Any] = {}  # Simple in-memory cache
        self._cache_ttl = 30  # seconds

    def set_access_token(self, token: str):
        """Set user's access token for RLS context.

        This must be called before any database operations to ensure
        proper Row-Level Security context.
        """
        self._access_token = token

    def _get_client(self):
        """Get Supabase client with user's JWT for RLS context.

        Creates a fresh client with the user's access token to ensure
        auth.uid() returns the correct user ID for RLS policies.
        """
        return get_supabase(access_token=self._access_token)
    
    def _apply_filters(self, query, filters: Optional[Dict[str, Any]]):
        """Apply filters to a Supabase query."""
        if not filters:
            return query
        
        for key, value in filters.items():
            if value is None:
                query = query.is_(key, None)
            elif isinstance(value, dict):
                # Handle special operators
                for op, val in value.items():
                    if op == "eq":
                        query = query.eq(key, val)
                    elif op == "neq":
                        query = query.neq(key, val)
                    elif op == "gt":
                        query = query.gt(key, val)
                    elif op == "gte":
                        query = query.gte(key, val)
                    elif op == "lt":
                        query = query.lt(key, val)
                    elif op == "lte":
                        query = query.lte(key, val)
                    elif op == "like":
                        query = query.like(key, val)
                    elif op == "ilike":
                        query = query.ilike(key, val)
                    elif op == "in":
                        query = query.in_(key, val)
                    elif op == "not_in":
                        query = query.not_.in_(key, val)
            else:
                query = query.eq(key, value)
        
        return query
    
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
        """Execute a query on a table."""
        try:
            client = self._get_client()
            query = client.from_(table).select(select or "*")
            
            query = self._apply_filters(query, filters)
            
            if order_by:
                # Parse order_by string: "column" or "column:desc"
                parts = order_by.split(":")
                col = parts[0]
                desc = len(parts) > 1 and parts[1].lower() == "desc"
                query = query.order(col, desc=desc)
            
            if offset:
                query = query.range(offset, (offset + limit - 1) if limit else None)
            elif limit:
                query = query.limit(limit)
            
            result = query.execute()
            return getattr(result, "data", []) or []
        
        except Exception as e:
            raise normalize_error(e, f"Failed to query table {table}")
    
    async def get_single(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a single record from a table."""
        try:
            client = self._get_client()
            query = client.from_(table).select(select or "*")
            
            query = self._apply_filters(query, filters)
            
            result = query.single().execute()
            return getattr(result, "data", None)
        
        except Exception as e:
            # Supabase raises exception for not found, we want None
            if hasattr(e, 'code') and e.code == 'PGRST116':
                return None
            raise normalize_error(e, f"Failed to get single record from {table}")
    
    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        returning: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Insert one or more records.

        Note: Supabase v2.5+ automatically returns all fields on insert.
        The 'returning' parameter is kept for API compatibility but is ignored.
        """
        try:
            client = self._get_client()
            # Supabase v2.5+ insert returns all fields by default
            # Do not chain .select() after .insert() - it's not supported
            query = client.from_(table).insert(data)
            result = query.execute()
            result_data = getattr(result, "data", None)

            if result_data is None:
                raise ValueError("Insert operation returned no data")

            # Return single dict if input was single dict, list otherwise
            if isinstance(data, dict):
                return result_data[0] if result_data else {}
            return result_data

        except Exception as e:
            raise normalize_error(e, f"Failed to insert into {table}")
    
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        *,
        returning: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Update records.

        Note: Supabase v2.5+ automatically returns updated data.
        The 'returning' parameter is kept for API compatibility but is ignored.
        """
        try:
            client = self._get_client()
            query = client.from_(table).update(data)
            query = self._apply_filters(query, filters)

            # Execute without chaining .select() - Supabase v2.5+ returns data automatically
            result = query.execute()
            result_data = getattr(result, "data", []) or []

            # Return single dict if only one record updated
            if len(result_data) == 1:
                return result_data[0]
            return result_data

        except Exception as e:
            raise normalize_error(e, f"Failed to update {table}")
    
    async def delete(
        self,
        table: str,
        filters: Dict[str, Any]
    ) -> int:
        """Delete records.

        Note: Supabase v2.5+ automatically returns deleted data.
        """
        try:
            client = self._get_client()
            query = client.from_(table).delete()
            query = self._apply_filters(query, filters)

            # Execute without chaining .select() - Supabase v2.5+ returns data automatically
            result = query.execute()
            deleted_rows = getattr(result, "data", []) or []
            return len(deleted_rows)
        
        except Exception as e:
            raise normalize_error(e, f"Failed to delete from {table}")
    
    async def count(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count records in a table."""
        try:
            client = self._get_client()
            query = client.from_(table).select("*", count="exact", head=True)
            
            query = self._apply_filters(query, filters)
            
            result = query.execute()
            return getattr(result, "count", 0) or 0
        
        except Exception as e:
            raise normalize_error(e, f"Failed to count records in {table}")
