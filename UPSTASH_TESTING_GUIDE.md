# Upstash Redis Integration Testing Guide

Comprehensive testing procedures for all phases of the Upstash Redis integration.

## Quick Start

### 1. Local Testing (Without Real Upstash)

```bash
# Install dependencies
uv pip install upstash-redis upstash-ratelimit py-key-value-aio

# Run tests without UPSTASH credentials
# All components gracefully fallback to in-memory
pytest tests/ -v -k redis
```

### 2. With Upstash (Production-like)

```bash
# Add to .env.local
UPSTASH_REDIS_REST_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token

# Run all tests
pytest tests/ -v
```

---

## Test Suites

### Phase 1: Distributed Rate Limiting

#### Unit Tests

```python
# tests/unit/infrastructure/test_distributed_rate_limiter.py

import pytest
from infrastructure.distributed_rate_limiter import DistributedRateLimiter

@pytest.mark.asyncio
async def test_rate_limit_check():
    """Test basic rate limit check."""
    limiter = DistributedRateLimiter(redis_client=None)  # In-memory
    
    # Should allow first 120 requests
    for i in range(120):
        result = await limiter.check_rate_limit("user_1", "default")
        assert result["allowed"] is True
        assert result["current_count"] == i + 1
    
    # 121st should be blocked
    result = await limiter.check_rate_limit("user_1", "default")
    assert result["allowed"] is False
    assert result["error"] is not None

@pytest.mark.asyncio
async def test_different_operation_types():
    """Test different rate limit tiers."""
    limiter = DistributedRateLimiter(redis_client=None)
    
    # Search has 30 limit
    for i in range(30):
        result = await limiter.check_rate_limit("user_1", "search")
        assert result["allowed"] is True
    
    result = await limiter.check_rate_limit("user_1", "search")
    assert result["allowed"] is False  # 31st blocked
    
    # But default should still work (separate counter)
    result = await limiter.check_rate_limit("user_1", "default")
    assert result["allowed"] is True

@pytest.mark.asyncio
async def test_get_remaining():
    """Test remaining requests calculation."""
    limiter = DistributedRateLimiter(redis_client=None)
    
    # Make 50 requests
    for i in range(50):
        await limiter.check_rate_limit("user_1", "default")
    
    # Should have 70 remaining (120 - 50)
    remaining = await limiter.get_remaining("user_1", "default")
    assert remaining == 70

@pytest.mark.asyncio
async def test_window_reset():
    """Test rate limit window reset after expiration."""
    limiter = DistributedRateLimiter(redis_client=None)
    
    # Fill window
    for i in range(120):
        await limiter.check_rate_limit("user_1", "default")
    
    # Should be blocked
    result = await limiter.check_rate_limit("user_1", "default")
    assert result["allowed"] is False
    
    # Manually reset to simulate time passing
    await limiter.reset_user("user_1", "default")
    
    # Should allow again
    result = await limiter.check_rate_limit("user_1", "default")
    assert result["allowed"] is True
```

#### Integration Tests (with real Upstash)

```bash
# Mark with @pytest.mark.upstash to run only with real Redis
pytest tests/ -m upstash -v -k rate_limit
```

### Phase 2: Response Caching Middleware

#### Unit Tests

```python
# tests/unit/services/test_embedding_cache.py

import pytest
from services.embedding_cache import EmbeddingCache

@pytest.mark.asyncio
async def test_embedding_cache_basic():
    """Test basic embedding caching."""
    cache = EmbeddingCache(redis_client=None)  # In-memory
    
    text = "Hello world"
    embedding = [0.1, 0.2, 0.3, 0.4]
    model = "gemini-embedding-001"
    
    # Cache should be empty initially
    result = await cache.get(text, model)
    assert result is None
    
    # Set embedding
    success = await cache.set(text, embedding, model)
    assert success is True
    
    # Get should return cached embedding
    result = await cache.get(text, model)
    assert result == embedding

@pytest.mark.asyncio
async def test_embedding_cache_ttl():
    """Test embedding cache with TTL."""
    import time
    cache = EmbeddingCache(redis_client=None)
    
    text = "Hello world"
    embedding = [0.1, 0.2, 0.3]
    
    # Set with 1 second TTL
    await cache.set(text, embedding, ttl=1)
    
    # Should exist immediately
    assert await cache.get(text) is not None
    
    # After TTL, in-memory would still have it
    # (Redis would expire automatically)
    await asyncio.sleep(1.1)
    # Note: In-memory implementation doesn't implement TTL

@pytest.mark.asyncio
async def test_cache_stats():
    """Test cache statistics tracking."""
    cache = EmbeddingCache(redis_client=None)
    
    text = "Test"
    embedding = [0.1, 0.2]
    
    # Set and get (hit)
    await cache.set(text, embedding)
    await cache.get(text)
    
    # Miss
    await cache.get("nonexistent")
    
    stats = await cache.get_stats()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1

@pytest.mark.asyncio
async def test_token_cache():
    """Test token caching."""
    from services.auth.token_cache import TokenCache
    
    cache = TokenCache(redis_client=None)
    
    token = "jwt_token_abc123"
    claims = {"user_id": "user_1", "email": "user@example.com"}
    
    # Cache token
    success = await cache.set(token, claims)
    assert success is True
    
    # Retrieve from cache
    cached = await cache.get(token)
    assert cached == claims
    
    # Invalidate
    await cache.invalidate(token)
    cached = await cache.get(token)
    assert cached is None
```

### Phase 3: Embedding Cache Integration

#### End-to-End Test

```python
# tests/e2e/test_embedding_cache_e2e.py

import pytest
from services.embedding_vertex import VertexAIEmbeddingService
from services.embedding_cache import get_embedding_cache

@pytest.mark.asyncio
async def test_embedding_cache_integration():
    """Test embedding service with caching."""
    service = VertexAIEmbeddingService()
    
    text = "Test embedding text"
    
    # First call: cache miss, calls Vertex AI
    result1 = await service.generate_embedding(text)
    assert result1.cached is False
    embedding1 = result1.embedding
    
    # Second call: should hit cache
    result2 = await service.generate_embedding(text)
    assert result2.cached is True
    assert result2.embedding == embedding1
    
    # Verify Redis has it too
    cache = await get_embedding_cache()
    redis_embedding = await cache.get(text)
    assert redis_embedding == embedding1

@pytest.mark.asyncio
async def test_embedding_cache_stats():
    """Test cache statistics after multiple calls."""
    service = VertexAIEmbeddingService()
    cache = await get_embedding_cache()
    
    # Make 10 requests: 5 unique, repeated twice
    texts = ["text_1", "text_2", "text_3", "text_4", "text_5"]
    for _ in range(2):
        for text in texts:
            await service.generate_embedding(text)
    
    stats = await cache.get_stats()
    
    # Should have high hit ratio (5 misses, 5 hits)
    assert stats["misses"] == 5
    assert stats["hits"] == 5
    assert stats["hit_ratio"] == 50.0
```

### Phase 4: Token Cache Integration

#### Unit Tests

```python
# tests/unit/auth/test_token_cache.py

import pytest
from infrastructure.supabase_auth import SupabaseAuthAdapter
from services.auth.token_cache import get_token_cache

@pytest.mark.asyncio
async def test_token_validation_with_cache():
    """Test token validation uses cache."""
    adapter = SupabaseAuthAdapter()
    
    # Create test token
    jwt_token = create_test_jwt_token(
        user_id="user_1",
        email="user@example.com",
        issuer="https://authkit.com"
    )
    
    # First validation: cache miss
    import time
    start = time.time()
    result1 = await adapter.validate_token(jwt_token)
    duration1 = time.time() - start
    
    # Second validation: should hit cache
    start = time.time()
    result2 = await adapter.validate_token(jwt_token)
    duration2 = time.time() - start
    
    # Cached call should be much faster
    assert result2 == result1
    assert duration2 < duration1  # Cache is faster
    
    # Verify cache contains token
    cache = await get_token_cache()
    cached = await cache.get(jwt_token)
    assert cached is not None
    assert cached["user_id"] == "user_1"
```

### Phase 5: Server Health Check

#### Health Check Tests

```bash
# Test health endpoint
curl http://localhost:8000/health
# Expected response:
# {
#   "status": "healthy",
#   "redis": {"connected": true, "backend": "upstash_redis"},
#   "caching": {
#     "embeddings": {"hits": 45, "hit_ratio": "85.2%"},
#     "tokens": {"hits": 230, "hit_ratio": "92.1%"}
#   }
# }
```

---

## Performance Benchmarks

### Benchmark: Rate Limiting Latency

```python
# tests/performance/test_rate_limiter_perf.py

import pytest
import time
from infrastructure.distributed_rate_limiter import DistributedRateLimiter

@pytest.mark.performance
@pytest.mark.asyncio
async def test_rate_limiter_latency():
    """Benchmark rate limiter latency."""
    limiter = DistributedRateLimiter(redis_client=None)  # In-memory
    
    durations = []
    iterations = 1000
    
    for i in range(iterations):
        start = time.time()
        await limiter.check_rate_limit(f"user_{i % 10}", "default")
        duration = (time.time() - start) * 1000  # milliseconds
        durations.append(duration)
    
    # Calculate statistics
    avg_latency = sum(durations) / len(durations)
    p95_latency = sorted(durations)[int(len(durations) * 0.95)]
    p99_latency = sorted(durations)[int(len(durations) * 0.99)]
    
    print(f"\nRate Limiter Latency (in-memory):")
    print(f"  Average: {avg_latency:.2f}ms")
    print(f"  P95: {p95_latency:.2f}ms")
    print(f"  P99: {p99_latency:.2f}ms")
    
    # Assertions
    assert avg_latency < 1.0, "Average latency should be < 1ms"
    assert p99_latency < 5.0, "P99 latency should be < 5ms"
```

### Benchmark: Cache Hit Ratio

```python
# tests/performance/test_cache_perf.py

@pytest.mark.performance
@pytest.mark.asyncio
async def test_embedding_cache_hit_ratio():
    """Benchmark embedding cache hit ratio."""
    cache = EmbeddingCache(redis_client=None)
    
    # Simulate realistic access pattern (Zipf distribution)
    # 80% of requests are for 20% of embeddings
    texts = [f"text_{i}" for i in range(100)]
    embeddings = {t: [float(i) for i in range(10)] for i, t in enumerate(texts)}
    
    # Cache all embeddings
    for text, emb in embeddings.items():
        await cache.set(text, emb)
    
    # Generate 1000 requests with Zipf distribution
    import random
    requests = []
    for _ in range(1000):
        if random.random() < 0.8:
            # 80% of time, request from top 20
            text = random.choice(texts[:20])
        else:
            # 20% of time, request from all
            text = random.choice(texts)
        requests.append(text)
    
    # Execute requests
    hits = 0
    for text in requests:
        result = await cache.get(text)
        if result is not None:
            hits += 1
    
    hit_ratio = hits / len(requests)
    print(f"\nCache Hit Ratio: {hit_ratio:.1%}")
    
    assert hit_ratio > 0.8, "Hit ratio should be > 80%"
```

---

## Stress Testing

### Load Test: Rate Limiter Under Load

```bash
# Using Apache Bench
ab -n 1000 -c 100 http://localhost:8000/api/mcp/call

# Expected:
# - All requests within rate limit
# - Response time: ~50-100ms
# - No 429 errors (unless intentionally testing limits)
```

### Load Test: Cache under Load

```python
# tests/load/test_cache_load.py

@pytest.mark.load
@pytest.mark.asyncio
async def test_cache_concurrent_access():
    """Test cache under concurrent load."""
    import asyncio
    from services.embedding_cache import EmbeddingCache
    
    cache = EmbeddingCache(redis_client=None)
    
    async def worker(worker_id, iterations):
        for i in range(iterations):
            text = f"text_{worker_id}_{i % 10}"  # 10 unique texts per worker
            embedding = [float(j) for j in range(10)]
            
            # Set
            await cache.set(text, embedding)
            # Get
            result = await cache.get(text)
            assert result is not None
    
    # Run 50 concurrent workers, 100 iterations each
    workers = [
        worker(i, 100)
        for i in range(50)
    ]
    
    start = time.time()
    await asyncio.gather(*workers)
    duration = time.time() - start
    
    print(f"\nCache Load Test Results:")
    print(f"  Workers: 50")
    print(f"  Iterations per worker: 100")
    print(f"  Total operations: 5000")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {5000/duration:.0f} ops/sec")
    
    stats = await cache.get_stats()
    print(f"  Cache hits: {stats['hits']}")
    print(f"  Cache misses: {stats['misses']}")
    print(f"  Hit ratio: {stats['hit_ratio']:.1f}%")
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/test-upstash.yml

name: Test Upstash Integration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      
      - name: Install dependencies
        run: |
          uv pip install -e ".[dev]"
      
      - name: Test without Upstash (fallback mode)
        run: |
          pytest tests/ -v -m "not upstash"
      
      - name: Test with Upstash
        if: ${{ secrets.UPSTASH_REDIS_REST_URL != '' }}
        env:
          UPSTASH_REDIS_REST_URL: ${{ secrets.UPSTASH_REDIS_REST_URL }}
          UPSTASH_REDIS_REST_TOKEN: ${{ secrets.UPSTASH_REDIS_REST_TOKEN }}
        run: |
          pytest tests/ -v -m upstash
```

---

## Monitoring & Observability

### Log Checklist

After deployment, verify these logs appear:

```
✅ Distributed rate limiter initialized: Upstash Redis (or in-memory fallback)
✅ Response caching middleware enabled (TTL: 3600s)
✅ Connected to Upstash Redis
✅ Initialized embedding cache: Upstash Redis (or no-op)
✅ Initialized token cache: Upstash Redis (or no-op)
```

### Metrics to Check

```python
# Check cache statistics
from infrastructure.redis_monitoring import get_redis_metrics

metrics = await get_redis_metrics()
all_metrics = await metrics.get_all_metrics()

# Should show:
# - embedding_cache.hit_ratio > 70%
# - token_cache.hit_ratio > 80%
# - redis_status.connected == true
# - rate_limiting backend == "distributed"
```

---

## Rollback Procedure

If issues arise:

1. **Immediate**: Remove Upstash env vars
   ```bash
   # In Vercel: unset UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN
   ```

2. **Code**: All components gracefully fallback to in-memory
   - Rate limiting: in-memory SlidingWindowRateLimiter
   - Caching: no-op (direct computation)
   - Operation: fully functional, no data loss

3. **Recovery**: Re-enable Upstash after fix
   ```bash
   # Set env vars again
   ```

---

## Debugging Tips

### Check Redis Connection

```python
from upstash_redis.asyncio import Redis

redis = Redis.from_env()
try:
    await redis.ping()
    print("✅ Redis connected")
except Exception as e:
    print(f"❌ Redis error: {e}")
```

### View Redis Data

```python
# List all keys
redis = Redis.from_env()
keys = await redis.keys("*")
print(f"Total keys: {len(keys)}")
for key in keys[:10]:  # First 10
    value = await redis.get(key)
    print(f"{key}: {value}")
```

### Monitor Cache Behavior

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all debug logs will show cache hits/misses
service.generate_embedding("text")  # "Cache hit for embedding"
adapter.validate_token(token)  # "Token cache hit"
```

---

## Success Criteria

✅ All tests pass (unit + integration)  
✅ Cache hit ratios meet targets (embeddings >80%, tokens >90%)  
✅ Rate limiting works across Vercel replicas  
✅ Performance: auth latency <10ms (cached vs 100ms uncached)  
✅ No increase in error rate after deployment  
✅ Upstash Redis connected in production logs  

---

**Last Updated**: November 2025  
**Status**: ✅ Ready for testing
