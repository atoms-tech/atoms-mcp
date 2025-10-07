# Optimizations Quick Reference Card

## 30-Second Start

```python
from framework.optimizations import create_optimized_client

client = create_optimized_client("http://localhost:8080")
await client.initialize()
result = await client.call_tool("get_entity", {"id": "123"})
await client.close()
```

## Environment Variables Cheatsheet

```bash
# Quick tuning for different scenarios

# High-load testing (more connections, larger cache)
export MCP_POOL_MAX_SIZE=50
export MCP_CACHE_MAX_ENTRIES=5000
export MCP_BATCH_SIZE=50

# Low-latency testing (minimal pooling, no batching)
export MCP_POOL_MIN_SIZE=2
export MCP_POOL_MAX_SIZE=5
export MCP_ENABLE_BATCHING=false

# Memory-constrained (smaller cache, fewer connections)
export MCP_CACHE_MAX_ENTRIES=100
export MCP_POOL_MAX_SIZE=5

# Debug mode (disable all optimizations)
export MCP_ENABLE_POOLING=false
export MCP_ENABLE_BATCHING=false
export MCP_ENABLE_CACHING=false
```

## Common Patterns

### Pytest Fixture (copy to conftest.py)
```python
@pytest.fixture
async def client():
    from framework.optimizations import create_optimized_client
    c = create_optimized_client("http://localhost:8080")
    await c.initialize()
    yield c
    await c.close()
```

### Batch Operations
```python
# Automatically batched
tasks = [client.call_tool("get_entity", {"id": str(i)}) for i in range(100)]
results = await asyncio.gather(*tasks)
```

### Cache Control
```python
# Cached (read operations)
await client.call_tool("get_entity", {"id": "123"}, use_cache=True)

# Not cached (write operations)
await client.call_tool("update_entity", {"id": "123", "name": "new"}, use_cache=False)
```

### Get Statistics
```python
stats = client.get_stats()
print(f"Cache hit rate: {stats['cache']['hit_rate']}")
print(f"Active connections: {stats['connection_pool']['active_connections']}")
```

## Component Overview

| Component | Purpose | Key Feature |
|-----------|---------|-------------|
| PooledMCPClient | Connection pooling | 4-20 reusable connections |
| BatchRequestOptimizer | Request batching | Groups 10+ requests |
| ConcurrencyOptimizer | Worker management | CPU cores × 2 workers |
| ResponseCacheLayer | Response caching | 1000 entries, 60s TTL |
| NetworkOptimizer | HTTP optimization | HTTP/2, compression |

## Performance Expectations

| Scenario | Speedup |
|----------|---------|
| Single test | 3.3× |
| 10 parallel | 5× |
| 100 parallel | 6.25× |
| Full suite | 5× |

## Troubleshooting 1-Liners

```bash
# Too many connections?
export MCP_POOL_MAX_SIZE=10

# Cache not working?
# Check tool name starts with: get_, list_, search_, query_, find_

# Memory issues?
export MCP_CACHE_MAX_ENTRIES=100

# Slow tests?
pytest -n auto  # Use all CPU cores
```

## Configuration Presets

### Preset 1: Maximum Performance
```python
OptimizationFlags(
    pool_min_size=10, pool_max_size=50,
    batch_size=50, cache_max_entries=5000,
    cache_ttl_seconds=300, worker_multiplier=4
)
```

### Preset 2: Balanced
```python
OptimizationFlags()  # Uses defaults
```

### Preset 3: Conservative
```python
OptimizationFlags(
    pool_min_size=2, pool_max_size=10,
    batch_size=5, cache_max_entries=100,
    cache_ttl_seconds=30
)
```

## Read More

- **Full docs:** `OPTIMIZATIONS_README.md`
- **Integration:** `INTEGRATION_GUIDE.md`
- **Examples:** `optimizations_example.py`
