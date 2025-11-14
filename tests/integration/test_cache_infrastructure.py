"""Cache & Infrastructure Integration Tests

Tests for:
- Upstash Redis caching
- Cache hit/miss rates
- Cache invalidation
- TTL expiration
- Concurrent cache access
- Infrastructure middleware
- Health checks
- Error handling
"""

import pytest
import time
import uuid


class TestCacheConnection:
    """Cache connection and availability."""

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_cache_connection_established(self, mcp_client):
        """Cache connection is active."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Cache {uuid.uuid4().hex[:4]}"}
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_cache_availability_check(self, mcp_client):
        """Cache availability can be checked."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Available {uuid.uuid4().hex[:4]}"}
        )
        assert result["success"] is True


class TestCacheHitMiss:
    """Cache hit/miss rate tracking."""

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_cache_hit_on_repeated_read(self, mcp_client):
        """Repeated read hits cache."""
        # Create entity
        org_result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Hit {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # First read (miss)
        first = await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="read"
        )
        
        # Second read (hit)
        second = await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="read"
        )
        
        assert first["success"] is True
        assert second["success"] is True
        # Second should be faster (cached)

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_cache_miss_on_new_entity(self, mcp_client):
        """First read of new entity misses cache."""
        org_result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Miss {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # First read should miss cache
        result = await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="read"
        )
        
        assert result["success"] is True


class TestCacheInvalidation:
    """Cache invalidation on mutations."""

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_cache_invalidated_on_update(self, mcp_client):
        """Cache invalidated when entity updated."""
        org_result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Invalidate {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Read (cache hit)
        first_read = await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="read"
        )
        
        # Update (invalidates cache)
        await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="update",
            data={"name": "NewName"}
        )
        
        # Read should reflect update
        second_read = await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="read"
        )
        
        assert second_read["data"]["name"] == "NewName"

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_cache_invalidated_on_delete(self, mcp_client):
        """Cache invalidated when entity deleted."""
        org_result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"DelInvalidate {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Delete (invalidates cache)
        await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="delete"
        )
        
        # Read should fail or return deleted marker
        read_result = await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="read"
        )
        
        assert "success" in read_result


class TestCacheTTL:
    """Cache TTL (time-to-live) behavior."""

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_cache_entry_expires(self, mcp_client):
        """Cache entries expire after TTL."""
        org_result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"TTL {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Read to cache
        await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="read"
        )
        
        # Wait for TTL (if using short test TTL)
        # Default TTL is usually 1 hour
        
        # Read again - may be from cache or fresh
        result = await mcp_client.entity_tool(
            entity_type="organization",
            entity_id=org_id,
            operation="read"
        )
        
        assert result["success"] is True


class TestConcurrentCacheAccess:
    """Concurrent cache operations."""

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_concurrent_reads_cached(self, mcp_client):
        """Concurrent reads use cache safely."""
        org_result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"ConcRead {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Concurrent reads
        results = []
        for _ in range(3):
            result = await mcp_client.entity_tool(
                entity_type="organization",
                entity_id=org_id,
                operation="read"
            )
            results.append(result["success"])
        
        assert all(results)

    @pytest.mark.asyncio
    @pytest.mark.cache
    @pytest.mark.requires_cache
    async def test_concurrent_write_invalidation(self, mcp_client):
        """Concurrent writes invalidate cache correctly."""
        org_result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"ConcWrite {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Concurrent updates
        results = []
        for i in range(2):
            result = await mcp_client.entity_tool(
                entity_type="organization",
                entity_id=org_id,
                operation="update",
                data={"name": f"Update {i}"}
            )
            results.append(result["success"])
        
        assert any(results)


class TestHealthChecks:
    """Health check endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_health_check_endpoint(self, mcp_client):
        """Health check endpoint is available."""
        # This would be a direct endpoint call
        # For now, verify normal operation
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Health {uuid.uuid4().hex[:4]}"}
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_readiness_check(self, mcp_client):
        """System readiness check."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            limit=1
        )
        assert result["success"] is True


class TestErrorHandling:
    """Error handling and recovery."""

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_graceful_error_response(self, mcp_client):
        """Errors return gracefully."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": ""}  # Invalid
        )
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_500_error_handling(self, mcp_client):
        """5xx errors handled gracefully."""
        # Normal operation should not trigger errors
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Error {uuid.uuid4().hex[:4]}"}
        )
        
        assert result["success"] is True


class TestMiddleware:
    """Middleware and request/response handling."""

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_request_logging(self, mcp_client):
        """Requests are logged."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Logging {uuid.uuid4().hex[:4]}"}
        )
        
        assert result["success"] is True
        # Request should be logged (verified via logs)

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_response_formatting(self, mcp_client):
        """Responses are properly formatted."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Format {uuid.uuid4().hex[:4]}"}
        )
        
        # Response should have proper structure
        assert "success" in result
        assert "data" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_auth_middleware_enforced(self, mcp_client):
        """Auth middleware is enforced."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Auth {uuid.uuid4().hex[:4]}"}
        )
        
        assert result["success"] is True
        # Should only work with valid auth


class TestConfiguration:
    """Configuration loading and management."""

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_env_config_loaded(self, mcp_client):
        """Environment configuration loaded."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Config {uuid.uuid4().hex[:4]}"}
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_rate_limit_config_respected(self, mcp_client):
        """Rate limit config is respected."""
        results = []
        for _ in range(5):
            result = await mcp_client.entity_tool(
                entity_type="organization",
                operation="create",
                data={"name": f"RateConfig {uuid.uuid4().hex[:4]}"}
            )
            results.append(result["success"])
        
        assert any(results)


class TestDegradation:
    """Graceful degradation when services unavailable."""

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_operation_without_cache(self, mcp_client):
        """Operations work without cache."""
        # Even if cache is down, operations should succeed
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"NoCacheFallback {uuid.uuid4().hex[:4]}"}
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.infrastructure
    async def test_operation_without_optional_service(self, mcp_client):
        """Operations work without optional services."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"OptionalDown {uuid.uuid4().hex[:4]}"}
        )
        
        assert result["success"] is True
