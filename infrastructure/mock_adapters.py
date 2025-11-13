"""Mock adapters for in-memory testing: Supabase + AuthKit Bearer tokens.

This module provides complete in-memory implementations of:
- InMemoryDatabaseAdapter: Supabase-compatible database operations
- InMemoryStorageAdapter: File/blob storage operations
- InMemoryAuthAdapter: AuthKit + Bearer token validation
- InMemoryRealtimeAdapter: Realtime subscriptions and events
- HttpMcpClient: HTTP client for local/hosted MCP servers

All adapters are fully functional for unit/integration testing.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
import time
import base64
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta, timezone

try:
    from .adapters import AuthAdapter, DatabaseAdapter, StorageAdapter, RealtimeAdapter
except ImportError:
    from infrastructure.adapters import AuthAdapter, DatabaseAdapter, StorageAdapter, RealtimeAdapter


# -----------------------------
# In-memory Database Mock
# -----------------------------

@dataclass
class _Table:
    rows: List[Dict[str, Any]] = field(default_factory=list)


class InMemoryDatabaseAdapter(DatabaseAdapter):
    def __init__(self, seed_data: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self._tables: Dict[str, _Table] = {}
        self._access_token = None
        seed_data = seed_data or {}
        for name, rows in seed_data.items():
            self._tables[name] = _Table(rows=list(rows))
    
    def set_access_token(self, token: str) -> None:
        """Set access token for database operations."""
        self._access_token = token

    def _tbl(self, name: str) -> _Table:
        if name not in self._tables:
            self._tables[name] = _Table()
        return self._tables[name]

    async def query(self, table: str, *, select: Optional[str] = None, filters: Optional[Dict[str, Any]] = None,
                    order_by: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        rows = [r for r in self._tbl(table).rows if _match(r, filters)]
        if order_by:
            key, _, direction = order_by.partition(":")
            def safe_sort_key(r):
                val = r.get(key)
                # Put None values at the end, regardless of direction
                return (val is None, val)
            rows.sort(key=safe_sort_key, reverse=direction.lower() == "desc")
        if offset:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return _select(rows, select)

    async def get_single(self, table: str, *, select: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        rows = await self.query(table, select=select, filters=filters, limit=1)
        return rows[0] if rows else None

    async def insert(self, table: str, data: Union[Dict[str, Any], List[Dict[str, Any]]], *, returning: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
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
        
        # Auto-generate ID if not present
        if "id" not in row_data:
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

    async def update(self, table: str, data: Dict[str, Any], filters: Dict[str, Any], *, returning: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
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
        before = len(self._tbl(table).rows)
        self._tbl(table).rows = [r for r in self._tbl(table).rows if not _match(r, filters)]
        return before - len(self._tbl(table).rows)

    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        return len([r for r in self._tbl(table).rows if _match(r, filters)])


# -----------------------------
# In-memory Storage Mock
# -----------------------------

class InMemoryStorageAdapter(StorageAdapter):
    def __init__(self):
        self._buckets: Dict[str, Dict[str, bytes]] = {}

    async def upload(self, bucket: str, path: str, data: bytes, *, content_type: Optional[str] = None, metadata: Optional[Dict[str, str]] = None) -> str:
        self._buckets.setdefault(bucket, {})[path] = data
        return self.get_public_url(bucket, path)

    async def download(self, bucket: str, path: str) -> bytes:
        return self._buckets.get(bucket, {}).get(path, b"")

    async def delete(self, bucket: str, path: str) -> bool:
        return bool(self._buckets.get(bucket, {}).pop(path, None))

    def get_public_url(self, bucket: str, path: str) -> str:
        return f"mem://{bucket}/{path}"


# -----------------------------
# In-memory Auth Mock (AuthKit + Bearer tokens)
# -----------------------------

class InMemoryAuthAdapter(AuthAdapter):
    """Mock AuthKit authentication adapter with Bearer token support.
    
    Supports:
    - Bearer token validation (AuthKit JWT pattern)
    - Session creation and revocation
    - Custom mock users for testing
    - Multiple concurrent sessions
    """
    
    def __init__(self, *, default_user: Optional[Dict[str, Any]] = None):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._tokens: Dict[str, Dict[str, Any]] = {}  # Bearer token -> user info
        self._revoked_tokens: set = set()
        self._token_counter = 0
        
        # Default mock user (mimics AuthKit user structure)
        self._default_user = default_user or {
            "user_id": "mock-user-123",
            "email": "mock@example.com",
            "email_verified": True,
            "name": "Mock User",
            "given_name": "Mock",
            "family_name": "User",
        }

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate Bearer token and return user info.
        
        Supports:
        - Session tokens (from create_session)
        - Bearer tokens (mock JWT format)
        - Test tokens (any non-empty string in test mode)
        """
        if not token:
            raise ValueError("Invalid token: empty")
        
        # Check if it's a known session token
        if token in self._sessions:
            session = self._sessions[token]
            if session.get("revoked_at"):
                raise ValueError("Session token has been revoked")
            return session["user_info"]
        
        # Check if it's a known Bearer token
        if token in self._tokens:
            token_data = self._tokens[token]
            if token in self._revoked_tokens:
                raise ValueError("Bearer token has been revoked")
            if token_data.get("expires_at") and token_data["expires_at"] < time.time():
                raise ValueError("Bearer token has expired")
            return token_data["user_info"]
        
        # In mock mode, accept any non-empty token as a valid Bearer token
        # This allows tests to pass custom tokens without pre-registering them
        return {
            **self._default_user,
            "access_token": token,
            "auth_type": "mock_bearer",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,  # 1 hour expiry
        }

    async def create_session(
        self,
        user_id: str,
        username: str,
        *,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> str:
        """Create a new session (returns Bearer token style string).
        
        Args:
            user_id: User identifier from AuthKit
            username: User's email/username
            access_token: Optional Supabase/AuthKit access token
            refresh_token: Optional refresh token
            
        Returns:
            Session Bearer token (can be used for API calls)
        """
        self._token_counter += 1
        session_id = f"session_{self._token_counter}_{uuid.uuid4().hex[:8]}"
        
        user_info = {
            "user_id": user_id,
            "email": username,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "auth_type": "authkit",
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400,  # 24 hour expiry
        }
        
        self._sessions[session_id] = {
            "user_info": user_info,
            "created_at": time.time(),
            "revoked_at": None,
        }
        
        return session_id

    async def revoke_session(self, token: str) -> bool:
        """Revoke a session token.
        
        Args:
            token: Session token to revoke
            
        Returns:
            True if token was revoked, False if not found
        """
        if token in self._sessions:
            self._sessions[token]["revoked_at"] = time.time()
            return True
        if token in self._tokens:
            self._revoked_tokens.add(token)
            return True
        return False

    async def verify_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify username/password credentials (mock implementation).
        
        In mock mode, any non-empty username/password is valid.
        """
        if username and password:
            return {
                "user_id": f"user_{username}_{uuid.uuid4().hex[:8]}",
                "email": username,
                "name": username.split("@")[0],
                "auth_type": "password",
            }
        return None
    
    def _create_bearer_token(self, user_id: str, username: str) -> str:
        """Create a mock Bearer token (JWT-like structure for testing).
        
        Format: base64(header).base64(payload).base64(signature)
        """
        self._token_counter += 1
        token_id = self._token_counter
        
        payload = {
            "user_id": user_id,
            "email": username,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "iss": "mock-authkit",
            "sub": user_id,
        }
        
        # Simulate JWT structure (not cryptographically valid, just for testing)
        header = base64.b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = base64.b64encode(f"sig_{token_id}".encode()).decode().rstrip("=")
        
        token = f"{header}.{payload_b64}.{signature}"
        
        user_info = {
            "user_id": user_id,
            "email": username,
            "auth_type": "bearer",
            "iat": payload["iat"],
            "exp": payload["exp"],
        }
        
        self._tokens[token] = {
            "user_info": user_info,
            "expires_at": payload["exp"],
        }
        
        return token


# -----------------------------
# Simple Realtime Mock
# -----------------------------

class InMemoryRealtimeAdapter(RealtimeAdapter):
    def __init__(self):
        self._subs: Dict[str, Dict[str, Any]] = {}
        self._next = 1

    async def subscribe(self, table: str, callback: Callable, *, filters: Optional[Dict[str, Any]] = None, events: Optional[List[str]] = None) -> str:
        sid = f"sub_{self._next}"
        self._next += 1
        self._subs[sid] = {"table": table, "callback": callback, "filters": filters or {}, "events": set(events or ["INSERT","UPDATE","DELETE"]) }
        return sid

    async def unsubscribe(self, subscription_id: str) -> bool:
        return bool(self._subs.pop(subscription_id, None))

    # helper to broadcast in tests
    async def _emit(self, table: str, event: str, row: Dict[str, Any]):
        for sub in self._subs.values():
            if sub["table"] == table and event in sub["events"]:
                await _maybe_await(sub["callback"]({"event": event, "row": row}))


# -----------------------------
# HTTP MCP Client (against local or hosted)
# -----------------------------

class HttpMcpClient:
    """HTTP client for local/hosted MCP servers.
    
    Supports:
    - Connection pooling and reuse
    - Exponential backoff retry logic
    - Health check validation
    - Request/response logging
    """
    
    def __init__(self, base_url: str, *, timeout: int = 30, max_retries: int = 3):
        """Initialize HTTP MCP client.
        
        Args:
            base_url: Base URL of MCP server (e.g., http://localhost:8000)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retries on transient errors (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = None
        self._last_health_check = None
        self._is_healthy = False

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None:
            try:
                import aiohttp
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                self._session = aiohttp.ClientSession(timeout=timeout)
            except ImportError:
                raise ImportError("aiohttp is required for HttpMcpClient. Install it with: pip install aiohttp")
        return self._session

    async def health(self) -> Dict[str, Any]:
        """Check MCP server health.
        
        Returns:
            Health status dict (e.g., {"status": "ok", "uptime": 12345})
            
        Raises:
            ConnectionError: If server is unreachable
        """
        try:
            sess = await self._get_session()
            async with sess.get(f"{self.base_url}/health") as r:
                r.raise_for_status()
                result = await r.json()
                self._is_healthy = True
                self._last_health_check = time.time()
                return result
        except Exception as e:
            self._is_healthy = False
            raise ConnectionError(f"Failed to connect to MCP server at {self.base_url}: {e}")

    async def call_mcp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP server method with retry logic.
        
        Args:
            payload: MCP request payload (must include 'method' field)
            
        Returns:
            MCP response dict
            
        Raises:
            ConnectionError: If all retries are exhausted
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                sess = await self._get_session()
                async with sess.post(
                    f"{self.base_url}/api/mcp",
                    json=payload,
                ) as r:
                    r.raise_for_status()
                    result = await r.json()
                    self._is_healthy = True
                    return result
            except Exception as e:
                last_error = e
                
                # Exponential backoff: 2^attempt seconds (1s, 2s, 4s, ...)
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
        
        self._is_healthy = False
        raise ConnectionError(
            f"MCP call failed after {self.max_retries} attempts: {last_error}"
        )

    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# -----------------------------
# Utilities
# -----------------------------

def _match(row: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
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
    if not select or select == "*":
        return [dict(r) for r in rows]
    cols = [c.strip() for c in select.split(",")]
    return [{k: r.get(k) for k in cols} for r in rows]


def _select_one(row: Dict[str, Any], select: Optional[str]) -> Dict[str, Any]:
    return _select([row], select)[0]


async def _maybe_await(x: Any):
    if asyncio.iscoroutine(x):
        return await x
    return x
