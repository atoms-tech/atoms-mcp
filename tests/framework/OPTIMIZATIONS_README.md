# MCP Test Suite Optimizations

This document describes the performance optimizations available for the MCP test suite.

## Overview

The `optimizations.py` module provides a comprehensive set of performance optimizations for MCP test execution, including:

- Connection pooling with automatic reconnection
- Request batching and deduplication
- Response caching with TTL
- Concurrency optimization
- Network-level optimizations (HTTP/2, compression, keep-alive)

## Components

### 1. PooledMCPClient

A connection pool manager that maintains reusable HTTP connections.

**Features:**
- Configurable pool size (min: 4, max: 20 by default)
- Automatic connection health checking
- Reconnection on failure
- Connection timeout handling
- Thread-safe connection management

**Configuration:**
```python
from framework.optimizations import PooledMCPClient

client = PooledMCPClient(
    base_url="http://localhost:8080",
    min_connections=4,      # Initial pool size
    max_connections=20,     # Maximum pool size
    connection_timeout=30,  # Connection timeout in seconds
    enable_http2=True,      # Enable HTTP/2
)
```

**Statistics:**
```python
stats = client.get_stats()
# Returns:
# {
#     "total_connections": 10,
#     "active_connections": 3,
#     "idle_connections": 7,
#     "failed_connections": 0,
#     "reconnections": 1,
#     "total_requests": 1500
# }
```

### 2. BatchRequestOptimizer

Batches multiple requests together to reduce HTTP overhead.

**Features:**
- Automatic request batching (default: 10 requests per batch)
- Request deduplication (identical requests share results)
- Parallel request processing
- Configurable batch timeout

**Configuration:**
```python
from framework.optimizations import BatchRequestOptimizer

optimizer = BatchRequestOptimizer(
    client=pooled_client,
    batch_size=10,          # Requests per batch
    batch_timeout=0.1,      # Max wait time in seconds
)
```

**How it works:**
1. Requests are queued until batch size is reached or timeout expires
2. Duplicate requests are detected and deduplicated
3. All requests in batch are executed in parallel
4. Results are distributed to all waiting futures

### 3. ConcurrencyOptimizer

Manages optimal concurrency for test execution.

**Features:**
- CPU-aware worker count (CPU cores × 2 by default)
- Memory-aware scaling
- Dynamic worker adjustment
- Rate limiting protection

**Configuration:**
```python
from framework.optimizations import ConcurrencyOptimizer

optimizer = ConcurrencyOptimizer(
    worker_multiplier=2,    # Workers = CPU cores × multiplier
    max_workers=None,       # Override automatic calculation
    memory_limit_gb=4.0,    # Memory constraint
)

# Get optimal worker count
workers = optimizer.get_optimal_worker_count()

# Create rate limiter
rate_limiter = optimizer.create_rate_limiter(max_concurrent=10)

# Use in async context
async with optimizer.limit_concurrency():
    # Your concurrent operations
    pass
```

### 4. ResponseCacheLayer

LRU cache for MCP responses with TTL support.

**Features:**
- LRU eviction policy
- Configurable cache size (default: 1000 entries)
- Time-to-live (TTL) for entries (default: 60 seconds)
- Thread-safe operations
- Cache hit/miss statistics

**Configuration:**
```python
from framework.optimizations import ResponseCacheLayer

cache = ResponseCacheLayer(
    max_size=1000,          # Maximum cache entries
    default_ttl=60,         # TTL in seconds
)

# Store and retrieve
cache.set("get_entity", {"id": "123"}, result_data)
cached = cache.get("get_entity", {"id": "123"})

# Get statistics
stats = cache.get_stats()
# Returns:
# {
#     "hits": 450,
#     "misses": 50,
#     "hit_rate": "90.00%",
#     "entries": 100,
#     "max_size": 1000
# }
```

### 5. NetworkOptimizer

Network-level HTTP optimizations.

**Features:**
- HTTP/2 multiplexing
- Keep-alive connections
- Compression (gzip, deflate, brotli)
- Automatic retries
- Connection pooling limits

**Configuration:**
```python
from framework.optimizations import NetworkOptimizer

client = NetworkOptimizer.create_optimized_client(
    base_url="http://localhost:8080",
    enable_http2=True,
    enable_compression=True,
    timeout=30,
)
```

## OptimizedMCPClient

The main client that combines all optimizations.

### Basic Usage

```python
from framework.optimizations import create_optimized_client

# Create with default settings
client = create_optimized_client("http://localhost:8080")

try:
    # Initialize (creates connection pool, etc.)
    await client.initialize()

    # Make requests
    result = await client.call_tool("get_entity", {"entity_id": "123"})

    # Get statistics
    stats = client.get_stats()
    print(f"Performance stats: {stats}")

finally:
    # Clean up
    await client.close()
```

### Custom Configuration

```python
from framework.optimizations import OptimizationFlags, OptimizedMCPClient

flags = OptimizationFlags(
    enable_connection_pooling=True,
    enable_batch_requests=True,
    enable_response_caching=True,
    enable_concurrency_optimization=True,
    enable_network_optimization=True,
    pool_min_size=8,
    pool_max_size=40,
    batch_size=20,
    cache_max_entries=2000,
    cache_ttl_seconds=120,
    worker_multiplier=3,
)

client = OptimizedMCPClient("http://localhost:8080", flags=flags)
```

### Environment Variables

All optimizations can be configured via environment variables:

```bash
# Enable/disable optimizations
export MCP_ENABLE_POOLING=true
export MCP_ENABLE_BATCHING=true
export MCP_ENABLE_CONCURRENCY=true
export MCP_ENABLE_CACHING=true
export MCP_ENABLE_NETWORK_OPT=true

# Connection pool settings
export MCP_POOL_MIN_SIZE=8
export MCP_POOL_MAX_SIZE=40
export MCP_CONNECTION_TIMEOUT=30

# Batch settings
export MCP_BATCH_SIZE=20

# Cache settings
export MCP_CACHE_MAX_ENTRIES=2000
export MCP_CACHE_TTL=120

# Concurrency settings
export MCP_WORKER_MULTIPLIER=3

# Network settings
export MCP_ENABLE_HTTP2=true
export MCP_ENABLE_COMPRESSION=true
export MCP_REQUEST_TIMEOUT=60
```

Then use:
```python
from framework.optimizations import OptimizationFlags, OptimizedMCPClient

flags = OptimizationFlags.from_env()
client = OptimizedMCPClient("http://localhost:8080", flags=flags)
```

## Integration with Tests

### Pytest Fixture

```python
# conftest.py
import pytest
from framework.optimizations import create_optimized_client

@pytest.fixture
async def optimized_client():
    """Provide an optimized MCP client for tests."""
    client = create_optimized_client("http://localhost:8080")
    await client.initialize()

    yield client

    # Print stats after test
    stats = client.get_stats()
    print(f"\nTest optimization stats: {stats}")

    await client.close()

# test_example.py
async def test_entity_operations(optimized_client):
    """Test with optimized client."""
    result = await optimized_client.call_tool(
        "get_entity",
        {"entity_id": "123"}
    )
    assert result is not None
```

### Selective Optimization

```python
# Enable only specific optimizations
flags = OptimizationFlags(
    enable_connection_pooling=True,
    enable_batch_requests=False,     # Disabled
    enable_response_caching=True,
    enable_concurrency_optimization=False,  # Disabled
    enable_network_optimization=True,
)

client = OptimizedMCPClient("http://localhost:8080", flags=flags)
```

### Cache Control

```python
# Cache read operations
result1 = await client.call_tool(
    "get_entity",
    {"entity_id": "123"},
    use_cache=True  # Will be cached
)

# Don't cache write operations
await client.call_tool(
    "create_entity",
    {"name": "test"},
    use_cache=False  # Won't be cached
)

# Read-only operations are automatically detected and cached
# (prefixes: get_, list_, search_, query_, find_)
```

## Performance Benchmarks

Expected performance improvements:

| Scenario | Without Optimization | With Optimization | Speedup |
|----------|---------------------|-------------------|---------|
| 100 sequential requests | ~50s | ~15s | 3.3x |
| 100 parallel requests | ~30s | ~5s | 6x |
| 1000 requests with duplicates | ~500s | ~80s | 6.25x |
| High-load test suite | ~10min | ~2min | 5x |

Cache hit rates:
- Read-heavy workloads: 70-90% hit rate
- Mixed workloads: 40-60% hit rate
- Write-heavy workloads: 10-20% hit rate

## Best Practices

1. **Always initialize before use**: Call `await client.initialize()` before making requests

2. **Always clean up**: Call `await client.close()` in finally block or use async context manager

3. **Use caching wisely**: Enable caching for read operations, disable for writes

4. **Monitor statistics**: Use `client.get_stats()` to track performance

5. **Tune for your workload**:
   - High concurrency: Increase `pool_max_size` and `worker_multiplier`
   - Read-heavy: Increase `cache_max_entries` and `cache_ttl_seconds`
   - Latency-sensitive: Increase `pool_min_size` to avoid cold starts
   - Memory-constrained: Reduce `cache_max_entries` and `pool_max_size`

6. **Use environment variables**: Keep configuration separate from code

7. **Test with optimizations**: Always test with optimizations enabled in CI/CD

8. **Disable selectively**: If issues arise, disable specific optimizations to isolate

## Troubleshooting

### High memory usage
- Reduce `cache_max_entries`
- Reduce `pool_max_size`
- Reduce `cache_ttl_seconds`

### Connection timeouts
- Increase `connection_timeout`
- Increase `request_timeout`
- Reduce `pool_max_size` if overwhelming server

### Poor cache hit rate
- Increase `cache_ttl_seconds` if data is relatively stable
- Ensure read operations are properly prefixed (get_, list_, etc.)
- Check if requests have identical parameters

### Batch overhead
- Reduce `batch_size` for latency-sensitive operations
- Increase `batch_timeout` to allow more batching
- Disable batching for real-time requirements

## Examples

See `optimizations_example.py` for comprehensive examples including:
- Basic usage
- Custom configuration
- Environment variables
- Selective optimizations
- Cache control
- Pytest fixtures
- Performance comparison

## API Reference

### OptimizationFlags
```python
OptimizationFlags(
    enable_connection_pooling: bool = True,
    enable_batch_requests: bool = True,
    enable_concurrency_optimization: bool = True,
    enable_response_caching: bool = True,
    enable_network_optimization: bool = True,
    pool_min_size: int = 4,
    pool_max_size: int = 20,
    batch_size: int = 10,
    cache_max_entries: int = 1000,
    cache_ttl_seconds: int = 60,
    worker_multiplier: int = 2,
    enable_http2: bool = True,
    enable_compression: bool = True,
    connection_timeout: int = 30,
    request_timeout: int = 60,
)
```

### OptimizedMCPClient
```python
client = OptimizedMCPClient(base_url: str, flags: OptimizationFlags)

await client.initialize()
result = await client.call_tool(tool_name: str, arguments: Dict, use_cache: bool = True)
stats = client.get_stats()
await client.close()
```

### Convenience Function
```python
client = create_optimized_client(
    base_url: str,
    **kwargs  # Any OptimizationFlags parameters
)
```
