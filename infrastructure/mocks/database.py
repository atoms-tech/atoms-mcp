"""In-memory database adapter for testing.

Provides Supabase-compatible database operations without external dependencies.
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
    """Internal table representation."""
    rows: List[Dict[str, Any]] = field(default_factory=list)


def _match(row: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    """Check if row matches all filters."""
    if not filters:
        return True
    return all(row.get(k) == v for k, v in filters.items())


def _select(rows: List[Dict[str, Any]], select: Optional[str]) -> List[Dict[str, Any]]:
    """Select specific columns from rows."""
    if not select or select == "*":
        return rows
    cols = [c.strip() for c in select.split(",")]
    return [{c: r.get(c) for c in cols} for r in rows]


def _select_one(row: Dict[str, Any], select: Optional[str]) -> Dict[str, Any]:
    """Select specific columns from single row."""
    if not select or select == "*":
        return row
    cols = [c.strip() for c in select.split(",")]
    return {c: row.get(c) for c in cols}


class InMemoryDatabaseAdapter(DatabaseAdapter):
    """In-memory database adapter for testing."""

    def __init__(self, seed_data: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        """Initialize with optional seed data."""
        self._tables: Dict[str, _Table] = {}
        self._access_token = None
        seed_data = seed_data or {}
        for name, rows in seed_data.items():
            self._tables[name] = _Table(rows=list(rows))

    def set_access_token(self, token: str) -> None:
        """Set access token for database operations."""
        self._access_token = token

    def _tbl(self, name: str) -> _Table:
        """Get or create table."""
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
        """Query table with filters, ordering, and pagination."""
        rows = [r for r in self._tbl(table).rows if _match(r, filters)]
        
        if order_by:
            if ":" in order_by:
                key, _, direction = order_by.partition(":")
            else:
                parts = order_by.strip().split()
                key = parts[0]
                direction = parts[1] if len(parts) > 1 else "ASC"
            
            def safe_sort_key(r):
                val = r.get(key)
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
        """Get single row matching filters."""
        rows = await self.query(table, select=select, filters=filters, limit=1)
        return rows[0] if rows else None

    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        returning: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Insert record(s) with auto-generated fields."""
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

    def _prepare_row(
        self, table: str, data: Dict[str, Any], is_insert: bool = False
    ) -> Dict[str, Any]:
        """Prepare row with auto-generated fields."""
        row_data = dict(data)
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        if is_insert and "id" not in row_data:
            row_data["id"] = str(uuid.uuid4())

        if is_insert and "created_at" not in row_data:
            row_data["created_at"] = now_iso

        if "updated_at" not in row_data:
            row_data["updated_at"] = now_iso

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
        """Update records matching filters."""
        updated: List[Dict[str, Any]] = []
        update_data = self._prepare_row(table, data, is_insert=False)

        for row in self._tbl(table).rows:
            if _match(row, filters):
                row.update(update_data)
                updated.append(dict(row))

        results = [_select_one(r, returning) for r in updated] if returning else updated
        if len(results) == 1:
            return results[0]
        return results

    async def delete(self, table: str, filters: Dict[str, Any]) -> int:
        """Delete records matching filters."""
        before = len(self._tbl(table).rows)
        self._tbl(table).rows = [
            r for r in self._tbl(table).rows if not _match(r, filters)
        ]
        return before - len(self._tbl(table).rows)

    async def count(
        self, table: str, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count records matching filters."""
        return len([r for r in self._tbl(table).rows if _match(r, filters)])

