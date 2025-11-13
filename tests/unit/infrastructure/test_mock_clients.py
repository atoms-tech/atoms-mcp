"""Comprehensive tests for all mock client implementations.

Tests cover:
- InMemoryAuthAdapter: Bearer tokens, sessions, credentials
- InMemoryDatabaseAdapter: CRUD, timestamps, filtering, sorting
- InMemoryStorageAdapter: Upload, download, delete operations
- InMemoryRealtimeAdapter: Subscriptions, events, filtering
- HttpMcpClient: HTTP operations, retries, health checks
"""

import pytest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.mock_adapters import (
    InMemoryDatabaseAdapter,
    InMemoryAuthAdapter,
    InMemoryStorageAdapter,
    InMemoryRealtimeAdapter,
    HttpMcpClient,
)


class TestInMemoryAuthAdapter:
    """Test AuthKit + Bearer token authentication."""

    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test session creation returns valid token."""
        auth = InMemoryAuthAdapter()
        token = await auth.create_session("user-123", "user@example.com")

        assert token.startswith("session_")
        assert len(token) > 10

    @pytest.mark.asyncio
    async def test_validate_session_token(self):
        """Test validating a created session token."""
        auth = InMemoryAuthAdapter()
        token = await auth.create_session("user-456", "alice@example.com")

        user = await auth.validate_token(token)
        assert user["user_id"] == "user-456"
        assert user["email"] == "alice@example.com"
        assert user["auth_type"] == "authkit"

    @pytest.mark.asyncio
    async def test_validate_bearer_token(self):
        """Test Bearer token (JWT-like) validation."""
        auth = InMemoryAuthAdapter()
        bearer = auth._create_bearer_token("user-789", "bob@example.com")

        # Bearer token looks like: header.payload.signature
        assert bearer.count(".") == 2

        user = await auth.validate_token(bearer)
        assert user["user_id"] == "user-789"
        assert user["email"] == "bob@example.com"
        assert user["auth_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_validate_arbitrary_token(self):
        """Test that arbitrary tokens are accepted in mock mode."""
        auth = InMemoryAuthAdapter()

        # Any non-empty string should work in mock mode
        user = await auth.validate_token("arbitrary-token-xyz")
        assert user["user_id"] == "12345678-1234-1234-1234-123456789012"
        assert user["auth_type"] == "mock_bearer"

    @pytest.mark.asyncio
    async def test_validate_empty_token_fails(self):
        """Test that empty token raises error."""
        auth = InMemoryAuthAdapter()

        with pytest.raises(ValueError):
            await auth.validate_token("")

    @pytest.mark.asyncio
    async def test_revoke_session_token(self):
        """Test revoking a session token."""
        auth = InMemoryAuthAdapter()
        token = await auth.create_session("user-111", "user@example.com")

        # Should be able to validate before revocation
        user = await auth.validate_token(token)
        assert user["user_id"] == "user-111"

        # Revoke the token
        revoked = await auth.revoke_session(token)
        assert revoked is True

        # Should fail after revocation
        with pytest.raises(ValueError, match="revoked"):
            await auth.validate_token(token)

    @pytest.mark.asyncio
    async def test_verify_credentials(self):
        """Test username/password credential verification."""
        auth = InMemoryAuthAdapter()

        user = await auth.verify_credentials("user@example.com", "password123")
        assert user is not None
        assert user["email"] == "user@example.com"
        assert user["auth_type"] == "password"

    @pytest.mark.asyncio
    async def test_verify_credentials_empty_fails(self):
        """Test that empty credentials return None."""
        auth = InMemoryAuthAdapter()

        result = await auth.verify_credentials("", "")
        assert result is None


class TestInMemoryDatabaseAdapter:
    """Test Supabase-compatible database operations."""

    @pytest.mark.asyncio
    async def test_insert_single_record(self):
        """Test inserting a single record."""
        db = InMemoryDatabaseAdapter()

        result = await db.insert("users", {"name": "Alice", "email": "alice@example.com"})

        assert "id" in result
        assert result["name"] == "Alice"
        assert result["email"] == "alice@example.com"
        assert "created_at" in result
        assert result["is_deleted"] is False

    @pytest.mark.asyncio
    async def test_insert_multiple_records(self):
        """Test inserting multiple records."""
        db = InMemoryDatabaseAdapter()

        results = await db.insert("users", [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Carol"},
        ])

        assert len(results) == 3
        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_query_all_records(self):
        """Test querying all records."""
        db = InMemoryDatabaseAdapter()
        await db.insert("users", {"name": "Alice"})
        await db.insert("users", {"name": "Bob"})

        results = await db.query("users")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_with_filter(self):
        """Test querying with filters."""
        db = InMemoryDatabaseAdapter()
        user1 = await db.insert("users", {"name": "Alice", "status": "active"})
        user2 = await db.insert("users", {"name": "Bob", "status": "inactive"})

        results = await db.query("users", filters={"status": "active"})
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_query_with_ordering(self):
        """Test querying with ordering."""
        db = InMemoryDatabaseAdapter()
        await db.insert("users", {"name": "Charlie", "age": 30})
        await db.insert("users", {"name": "Alice", "age": 25})
        await db.insert("users", {"name": "Bob", "age": 35})

        # Ascending
        results = await db.query("users", order_by="age ASC")
        assert [r["age"] for r in results] == [25, 30, 35]

        # Descending
        results = await db.query("users", order_by="age DESC")
        assert [r["age"] for r in results] == [35, 30, 25]

    @pytest.mark.asyncio
    async def test_query_with_limit_offset(self):
        """Test pagination with limit and offset."""
        db = InMemoryDatabaseAdapter()
        for i in range(10):
            await db.insert("users", {"name": f"User {i}"})

        # First page
        page1 = await db.query("users", limit=3, offset=0)
        assert len(page1) == 3

        # Second page
        page2 = await db.query("users", limit=3, offset=3)
        assert len(page2) == 3

        # Different records
        assert page1[0]["name"] != page2[0]["name"]

    @pytest.mark.asyncio
    async def test_query_with_select(self):
        """Test selecting specific columns."""
        db = InMemoryDatabaseAdapter()
        await db.insert("users", {"name": "Alice", "email": "alice@example.com", "secret": "hidden"})

        results = await db.query("users", select="name,email")
        assert "name" in results[0]
        assert "email" in results[0]
        # select filters columns for return
        assert "secret" not in results[0]

    @pytest.mark.asyncio
    async def test_get_single(self):
        """Test getting a single record."""
        db = InMemoryDatabaseAdapter()
        inserted = await db.insert("users", {"name": "Alice"})
        user_id = inserted["id"]

        result = await db.get_single("users", filters={"id": user_id})
        assert result is not None
        assert result["id"] == user_id
        assert result["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_get_single_not_found(self):
        """Test get_single returns None when not found."""
        db = InMemoryDatabaseAdapter()

        result = await db.get_single("users", filters={"id": "nonexistent"})
        assert result is None

    @pytest.mark.asyncio
    async def test_update_single_record(self):
        """Test updating a single record."""
        db = InMemoryDatabaseAdapter()
        user = await db.insert("users", {"name": "Alice", "email": "alice@old.com"})
        user_id = user["id"]

        updated = await db.update("users", {"email": "alice@new.com"}, {"id": user_id})

        # updated should be a dict (single record)
        assert isinstance(updated, dict)
        assert updated["email"] == "alice@new.com"
        assert "updated_at" in updated

    @pytest.mark.asyncio
    async def test_update_multiple_records(self):
        """Test updating multiple records."""
        db = InMemoryDatabaseAdapter()
        await db.insert("users", {"name": "Alice", "status": "inactive"})
        await db.insert("users", {"name": "Bob", "status": "inactive"})

        results = await db.update("users", {"status": "active"}, {"status": "inactive"})

        assert len(results) == 2
        assert all(r["status"] == "active" for r in results)

    @pytest.mark.asyncio
    async def test_delete_records(self):
        """Test deleting records."""
        db = InMemoryDatabaseAdapter()
        await db.insert("users", {"name": "Alice"})
        await db.insert("users", {"name": "Bob"})

        count = await db.delete("users", {"name": "Alice"})

        assert count == 1

        remaining = await db.query("users")
        assert len(remaining) == 1
        assert remaining[0]["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_count_records(self):
        """Test counting records."""
        db = InMemoryDatabaseAdapter()
        for i in range(5):
            await db.insert("users", {"name": f"User {i}", "active": i % 2 == 0})

        all_count = await db.count("users")
        assert all_count == 5

        active_count = await db.count("users", {"active": True})
        assert active_count == 3


class TestInMemoryStorageAdapter:
    """Test file/blob storage operations."""

    @pytest.mark.asyncio
    async def test_upload_and_download(self):
        """Test uploading and downloading files."""
        storage = InMemoryStorageAdapter()

        data = b"Hello World"
        url = await storage.upload("docs", "file.txt", data)

        assert "docs/file.txt" in url

        downloaded = await storage.download("docs", "file.txt")
        assert downloaded == data

    @pytest.mark.asyncio
    async def test_upload_with_metadata(self):
        """Test uploading with metadata."""
        storage = InMemoryStorageAdapter()

        url = await storage.upload(
            "images",
            "avatar.jpg",
            b"image data",
            content_type="image/jpeg",
            metadata={"owner": "alice"}
        )

        assert "images/avatar.jpg" in url

    @pytest.mark.asyncio
    async def test_delete_file(self):
        """Test deleting a file."""
        storage = InMemoryStorageAdapter()
        await storage.upload("docs", "file.txt", b"data")

        deleted = await storage.delete("docs", "file.txt")
        assert deleted is True

        # File should be gone
        content = await storage.download("docs", "file.txt")
        assert content == b""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self):
        """Test deleting a file that doesn't exist."""
        storage = InMemoryStorageAdapter()

        deleted = await storage.delete("docs", "nonexistent.txt")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_public_url(self):
        """Test getting public URL."""
        storage = InMemoryStorageAdapter()

        url = storage.get_public_url("docs", "file.txt")
        assert url == "mem://docs/file.txt"


class TestInMemoryRealtimeAdapter:
    """Test realtime subscriptions and events."""

    @pytest.mark.asyncio
    async def test_subscribe_to_events(self):
        """Test subscribing to table events."""
        realtime = InMemoryRealtimeAdapter()

        events = []
        async def callback(event):
            events.append(event)

        sub_id = await realtime.subscribe("users", callback)

        assert sub_id.startswith("sub_")

    @pytest.mark.asyncio
    async def test_emit_and_receive_event(self):
        """Test emitting and receiving events."""
        realtime = InMemoryRealtimeAdapter()

        events = []
        async def callback(event):
            events.append(event)

        await realtime.subscribe("users", callback, events=["INSERT"])
        await realtime._emit("users", "INSERT", {"id": "123", "name": "Alice"})

        assert len(events) == 1
        assert events[0]["event"] == "INSERT"
        assert events[0]["row"]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_event_filtering(self):
        """Test that only subscribed events are delivered."""
        realtime = InMemoryRealtimeAdapter()

        events = []
        async def callback(event):
            events.append(event)

        # Only subscribe to INSERT
        await realtime.subscribe("users", callback, events=["INSERT"])

        # Emit different events
        await realtime._emit("users", "INSERT", {"id": "1"})
        await realtime._emit("users", "UPDATE", {"id": "2"})
        await realtime._emit("users", "DELETE", {"id": "3"})

        # Should only receive INSERT
        assert len(events) == 1
        assert events[0]["event"] == "INSERT"

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from events."""
        realtime = InMemoryRealtimeAdapter()

        events = []
        async def callback(event):
            events.append(event)

        sub_id = await realtime.subscribe("users", callback)

        # Unsubscribe
        unsubscribed = await realtime.unsubscribe(sub_id)
        assert unsubscribed is True

        # Events should not be delivered
        await realtime._emit("users", "INSERT", {"id": "1"})
        assert len(events) == 0


class TestHttpMcpClient:
    """Test HTTP MCP client functionality."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test initializing HTTP client."""
        client = HttpMcpClient("http://localhost:8000")

        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30
        assert client.max_retries == 3

        await client.close()

    @pytest.mark.asyncio
    async def test_health_check_no_connection(self):
        """Test health check with connection error."""
        client = HttpMcpClient("http://localhost:9999")  # Port that doesn't exist

        # Should raise ConnectionError when server is unreachable
        with pytest.raises(ConnectionError):
            await client.health()

        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using HttpMcpClient as async context manager."""
        async with HttpMcpClient("http://localhost:8000") as client:
            assert client is not None

        # Session should be closed after context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
