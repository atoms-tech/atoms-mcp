"""Example test demonstrating how to use the mock adapters."""

import pytest

# Note: The mock fixtures are automatically imported via pytest_plugins in conftest.py
# So we can use them directly without explicit imports

class TestMockAdapters:
    """Test that the mock adapters work correctly."""

    @pytest.mark.asyncio
    async def test_in_memory_database_operations(self, mock_database):
        """Test basic database operations with the in-memory adapter."""
        # Test empty table
        results = await mock_database.query("test_table")
        assert results == []

        # Insert a record
        await mock_database.insert("test_table", {"id": "1", "name": "Test Item"})

        # Retrieve the record
        results = await mock_database.query("test_table", filters={"id": "1"})
        assert len(results) == 1
        assert results[0]["name"] == "Test Item"

        # Update the record
        await mock_database.update("test_table", {"name": "Updated Item"}, {"id": "1"})
        results = await mock_database.get_single("test_table", filters={"id": "1"})
        assert results["name"] == "Updated Item"

        # Count records
        count = await mock_database.count("test_table")
        assert count == 1

        # Delete the record
        deleted = await mock_database.delete("test_table", {"id": "1"})
        assert deleted == 1

        # Verify it's gone
        count = await mock_database.count("test_table")
        assert count == 0

    @pytest.mark.asyncio
    async def test_in_memory_auth_operations(self, mock_auth):
        """Test basic auth operations with the in-memory adapter."""
        # Test session creation
        token = await mock_auth.create_session("user-123", "test@example.com")
        assert token.startswith("session_")

        # Test token validation
        user_info = await mock_auth.validate_token(token)
        assert user_info["user_id"] == "user-123"
        assert user_info["email"] == "test@example.com"

        # Test credentials verification
        result = await mock_auth.verify_credentials("testuser", "testpass")
        assert result["email"] == "testuser"

        # Test session revocation
        revoked = await mock_auth.revoke_session(token)
        assert revoked is True

        # Verify token is no longer valid - should raise ValueError
        with pytest.raises(ValueError, match="revoked"):
            await mock_auth.validate_token(token)

    @pytest.mark.asyncio
    async def test_in_memory_storage_operations(self, mock_storage):
        """Test basic storage operations with the in-memory adapter."""
        bucket = "test-bucket"
        path = "test-file.txt"
        content = b"Hello, World!"

        # Upload file
        url = await mock_storage.upload(bucket, path, content)
        assert url == f"mem://{bucket}/{path}"

        # Download file
        downloaded = await mock_storage.download(bucket, path)
        assert downloaded == content

        # Get public URL (should be same as upload return)
        public_url = mock_storage.get_public_url(bucket, path)
        assert public_url == url

        # Delete file
        deleted = await mock_storage.delete(bucket, path)
        assert deleted is True

        # Verify file is gone
        downloaded = await mock_storage.download(bucket, path)
        assert downloaded == b''  # InMemoryStorageAdapter returns empty bytes for missing files

    @pytest.mark.asyncio
    async def test_database_with_seed_data(self, mock_database_with_data):
        """Test database operations with pre-seeded data."""
        # Query workspaces
        workspaces = await mock_database_with_data.query("workspaces")
        assert len(workspaces) == 2
        assert workspaces[0]["name"] == "Test Workspace"

        # Query specific workspace
        ws = await mock_database_with_data.get_single(
            "workspaces",
            filters={"id": "ws-123"}
        )
        assert ws["name"] == "Test Workspace"
        assert ws["owner_user_id"] == "mock-user-123" or ws["owner_user_id"] == "user-1"

    @pytest.mark.asyncio
    async def test_mock_mcp_client(self, mock_mcp_client):
        """Test the in-memory mock MCP client."""
        # Test health check
        health = await mock_mcp_client.health()
        assert health["status"] == "ok"
        assert health["mode"] == "in-memory"

        # Test MCP call
        payload = {"action": "test_operation", "data": {"key": "value"}}
        response = await mock_mcp_client.call_mcp(payload)
        assert response["echo"] == payload
        assert response["mode"] == "in-memory"

    @pytest.mark.asyncio
    async def test_adapter_factory_uses_mocks(self, mock_adapter_factory):
        """Test that the factory returns mock adapters when configured."""
        adapters = mock_adapter_factory.get_all_adapters()

        # Verify all adapters are mock implementations
        assert adapters["auth"].__class__.__name__ == "InMemoryAuthAdapter"
        assert adapters["database"].__class__.__name__ == "InMemoryDatabaseAdapter"
        assert adapters["storage"].__class__.__name__ == "InMemoryStorageAdapter"
        assert adapters["realtime"].__class__.__name__ == "InMemoryRealtimeAdapter"

    @pytest.mark.asyncio
    async def test_persistent_session_token(self, persistent_session_token, mock_auth):
        """Test that persistent session token works across test operations."""
        # Validate token using auth adapter
        user_info = await mock_auth.validate_token(persistent_session_token)
        assert user_info["username"] == "mock@example.com"
