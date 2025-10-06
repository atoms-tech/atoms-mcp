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
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operation."""
        import hashlib
        import json
        key_data = {"op": operation, **kwargs}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get cached result if still valid."""
        import time
        if cache_key in self._query_cache:
            data, timestamp = self._query_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._query_cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, data: Any):
        """Cache result with timestamp."""
        import time
        self._query_cache[cache_key] = (data, time.time())
        # Limit cache size
        if len(self._query_cache) > 1000:
            self._query_cache.clear()

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
        """Execute a query on a table with caching."""
        # Check cache for read-only queries
        cache_key = self._get_cache_key("query", table=table, select=select, filters=filters, order_by=order_by, limit=limit, offset=offset)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

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
            data = getattr(result, "data", []) or []

            # Cache result
            self._set_cache(cache_key, data)

            return data

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
    
    def _invalidate_cache_for_table(self, table: str):
        """Invalidate all cached queries for a table."""
        keys_to_remove = [k for k in self._query_cache.keys() if table in str(k)]
        for key in keys_to_remove:
            del self._query_cache[key]

    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        returning: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Insert one or more records with cache invalidation.

        Note: Supabase v2.5+ automatically returns all fields on insert.
        The 'returning' parameter is kept for API compatibility but is ignored.
        """
        try:
            client = self._get_client()
            query = client.from_(table).insert(data)
            result = query.execute()
            result_data = getattr(result, "data", None)

            if result_data is None:
                raise ValueError("Insert operation returned no data")

            # Invalidate cache for this table
            self._invalidate_cache_for_table(table)

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
        """Update records with cache invalidation.

        Note: Supabase v2.5+ automatically returns updated data.
        The 'returning' parameter is kept for API compatibility but is ignored.
        """
        try:
            client = self._get_client()
            query = client.from_(table).update(data)
            query = self._apply_filters(query, filters)

            result = query.execute()
            result_data = getattr(result, "data", []) or []

            # Invalidate cache for this table
            self._invalidate_cache_for_table(table)

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
        """Delete records with cache invalidation.

        Note: Supabase v2.5+ automatically returns deleted data.
        """
        try:
            client = self._get_client()
            query = client.from_(table).delete()
            query = self._apply_filters(query, filters)

            result = query.execute()
            deleted_rows = getattr(result, "data", []) or []

            # Invalidate cache for this table
            self._invalidate_cache_for_table(table)

            return len(deleted_rows)

        except Exception as e:
            raise normalize_error(e, f"Failed to delete from {table}")
    
    async def count(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count records in a table with caching."""
        # Check cache
        cache_key = self._get_cache_key("count", table=table, filters=filters)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        try:
            client = self._get_client()
            query = client.from_(table).select("*", count="exact", head=True)

            query = self._apply_filters(query, filters)

            result = query.execute()
            count = getattr(result, "count", 0) or 0

            # Cache result
            self._set_cache(cache_key, count)

            return count

        except Exception as e:
            raise normalize_error(e, f"Failed to count records in {table}")
