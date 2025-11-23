"""In-memory database adapter for testing.

Provides Supabase-compatible database operations using in-memory storage.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone

try:
    from ..adapters import DatabaseAdapter
except ImportError:
    from infrastructure.adapters import DatabaseAdapter


@dataclass
class _Table:
    """Internal table representation for in-memory storage."""
    rows: List[Dict[str, Any]] = field(default_factory=list)


def _match(row: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    """Match a row against filter criteria."""
    if not filters:
        return True
    
    for k, v in filters.items():
        # Handle _or operator (list of filter dicts - match ANY)
        if k == "_or":
            if isinstance(v, list):
                # For _or, row must match at least one of the filter dicts
                if not any(_match(row, sub_filter) for sub_filter in v):
                    return False
            continue
        
        row_value = row.get(k)
        
        # Handle special operators (for Supabase-style filters)
        if isinstance(v, dict):
            # Support ilike (case-insensitive substring match)
            if "ilike" in v:
                pattern = v["ilike"]
                # ilike patterns use % as wildcard
                if isinstance(row_value, str) and isinstance(pattern, str):
                    # Convert SQL ILIKE pattern to regex
                    search_str = pattern.replace("%", ".*").replace("_", ".")
                    import re
                    if not re.search(search_str, row_value, re.IGNORECASE):
                        return False
                else:
                    return False
            # Support contains (for JSON/array fields)
            elif "contains" in v:
                search_term = v["contains"]
                if isinstance(row_value, (dict, list)):
                    if isinstance(row_value, dict):
                        # Check if search term is in any value
                        if not any(search_term in str(val).lower() for val in row_value.values()):
                            return False
                    elif isinstance(row_value, list):
                        if not any(search_term in str(item).lower() for item in row_value):
                            return False
                else:
                    return False
            else:
                # Other operators not supported, treat as mismatch
                return False
        else:
            # Standard equality match
            # Handle None values: if filter is False and row doesn't have the key, treat as match
            # (e.g., is_deleted: False matches rows without is_deleted field)
            if v is False and row_value is None:
                continue  # Match: missing field is treated as False
            if row_value != v:
                return False
    
    return True


def _select(rows: List[Dict[str, Any]], select: Optional[str]) -> List[Dict[str, Any]]:
    """Select specific columns from rows."""
    if not select or select == "*":
        return [dict(r) for r in rows]
    cols = [c.strip() for c in select.split(",")]
    return [{k: r.get(k) for k in cols} for r in rows]


def _select_one(row: Dict[str, Any], select: Optional[str]) -> Dict[str, Any]:
    """Select specific columns from a single row."""
    return _select([row], select)[0]


class InMemoryDatabaseAdapter(DatabaseAdapter):
    """In-memory database adapter for testing.
    
    Provides Supabase-compatible database operations using in-memory storage.
    Supports query, insert, update, delete, and count operations.
    """
    
    def __init__(self, seed_data: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        """Initialize in-memory database adapter.
        
        Args:
            seed_data: Optional dict mapping table names to lists of initial rows
        """
        self._tables: Dict[str, _Table] = {}
        self._access_token = None
        seed_data = seed_data or {}
        for name, rows in seed_data.items():
            self._tables[name] = _Table(rows=list(rows))
    
    def set_access_token(self, token: str) -> None:
        """Set access token for database operations."""
        self._access_token = token

    def _tbl(self, name: str) -> _Table:
        """Get or create table by name."""
        if name not in self._tables:
            self._tables[name] = _Table()
        return self._tables[name]

    async def query(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query records from table."""
        rows = [r for r in self._tbl(table).rows if _match(r, filters)]
        if order_by:
            # Handle both "field:direction" and "field ASC/DESC" formats
            if ":" in order_by:
                key, _, direction = order_by.partition(":")
            else:
                # Handle "field ASC" or "field DESC" format
                parts = order_by.strip().split()
                key = parts[0]
                direction = parts[1] if len(parts) > 1 else "ASC"
            
            def safe_sort_key(r):
                val = r.get(key)
                # Put None values at the end, regardless of direction
                return (val is None, val)
            rows.sort(key=safe_sort_key, reverse=direction.upper() == "DESC")
        if offset:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return _select(rows, select)

    async def get_single(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a single record from table."""
        rows = await self.query(table, select=select, filters=filters, limit=1)
        return rows[0] if rows else None

    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        returning: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Insert record(s) into table.
        
        Auto-generates:
        - id (UUID) if not provided
        - created_at timestamp if column exists in schema
        - is_deleted = False if column exists in schema
        """
        if isinstance(data, dict):
            row_data = self._prepare_row(table, data, is_insert=True)
            self._tbl(table).rows.append(row_data)
            return _select_one(row_data, returning)
        else:
            results = []
            for row in data:
                row_data = self._prepare_row(table, row, is_insert=True)
                self._tbl(table).rows.append(row_data)
                results.append(_select_one(row_data, returning))
            return results
    
    def _prepare_row(self, table: str, data: Dict[str, Any], is_insert: bool = False) -> Dict[str, Any]:
        """Prepare a row for insertion/update with auto-generated fields."""
        row_data = dict(data)
        # Use timezone-aware UTC timestamp (ISO 8601 format)
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Auto-generate ID only on insert if not present
        if is_insert and "id" not in row_data:
            row_data["id"] = str(uuid.uuid4())
        
        # Auto-set created_at on insert
        if is_insert and "created_at" not in row_data:
            row_data["created_at"] = now_iso
        
        # Auto-set updated_at on insert/update
        if "updated_at" not in row_data:
            row_data["updated_at"] = now_iso
        
        # Auto-set is_deleted to False on insert if not specified
        if is_insert and "is_deleted" not in row_data:
            row_data["is_deleted"] = False
        
        return row_data

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        *,
        returning: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Update record(s) matching filters.
        
        Auto-updates:
        - updated_at timestamp
        """
        updated: List[Dict[str, Any]] = []
        update_data = self._prepare_row(table, data, is_insert=False)
        
        for row in self._tbl(table).rows:
            if _match(row, filters):
                row.update(update_data)
                updated.append(dict(row))
        
        # Match Supabase adapter behavior: return single dict if only one record updated
        results = [_select_one(r, returning) for r in updated] if returning else updated
        if len(results) == 1:
            return results[0]
        return results

    async def delete(self, table: str, filters: Dict[str, Any]) -> int:
        """Delete records matching filters."""
        before = len(self._tbl(table).rows)
        self._tbl(table).rows = [r for r in self._tbl(table).rows if not _match(r, filters)]
        return before - len(self._tbl(table).rows)

    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching filters."""
        return len([r for r in self._tbl(table).rows if _match(r, filters)])
