# Upstash Redis Integration Guide

Complete implementation guide for Upstash Redis caching in Atoms MCP server.

## Overview

This implementation provides **distributed, serverless caching** using Upstash Redis with automatic fallback to in-memory storage. It covers:

1. **Phase 1**: Distributed rate limiting (Upstash Redis)
2. **Phase 2**: Response caching middleware (FastMCP)
3. **Phase 3**: Embedding cache (Vertex AI cost reduction)
4. **Phase 4**: Token cache (AuthKit JWKS reduction)

---

## Setup Instructions

### 1. Create Upstash Redis Database

1. Go to [console.upstash.com](https://console.upstash.com)
2. Click "Create Database" > Redis
3. Choose:
   - **Region**: us-east-1 (or nearest to your deployment)
   - **Type**: Serverless (recommended for Vercel)
   - **Eviction**: allkeys-lru (auto-cleanup)
4. Copy the credentials:
   - `UPSTASH_REDIS_REST_URL` (e.g., `https://xxx.upstash.io`)
   - `UPSTASH_REDIS_REST_TOKEN`

### 2. Add to Environment

**For Vercel Production:**
```bash
# In Vercel Dashboard > Settings > Environment Variables
UPSTASH_REDIS_REST_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token-here
UPSTASH_REDIS_ENABLED=true

# Caching TTL (seconds)
CACHE_TTL_EMBEDDING=86400      # 24 hours
CACHE_TTL_TOKEN=3600           # 1 hour
CACHE_TTL_RESPONSE=3600        # 1 hour
```

**For Local Development:**
```bash
# In .env.local
UPSTASH_REDIS_REST_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token-here
```

### 3. Install Dependencies

```bash
uv pip install upstash-redis upstash-ratelimit py-key-value-aio
```

Or via uv.lock update:
```bash
uv sync
```

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                      FastMCP Server                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Rate Limiter    │  │  Response Cache  │                │
│  │  (Distributed)   │  │  (Middleware)    │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                      │                          │
│  ┌────────────────────────────────────────┐                │
│  │  Embedding Cache   │  Token Cache       │                │
│  │  (Vertex AI)       │  (AuthKit)         │                │
│  └────────┬───────────┴────────┬──────────┘                │
│           │                     │                          │
└───────────┼─────────────────────┼──────────────────────────┘
            │                     │
            └─────────┬───────────┘
                      │
            ┌─────────▼──────────┐
            │  Upstash Redis     │
            │  (HTTP REST API)   │
            └────────────────────┘
```

### Data Flow

#### Rate Limiting
```
Request → DistributedRateLimiter.check_limit()
        → Redis INCR (atomic counter)
        → If over limit: reject with 429
        → Fallback: in-memory if Redis down
```

#### Embedding Cache
```
EmbeddingService.generate_embedding()
  1. Check local in-memory cache (fastest)
  2. Check Redis cache (distributed)
  3. Call Vertex AI API (most expensive)
  4. Store in local cache + Redis cache
```

#### Token Cache
```
SupabaseAuthAdapter.validate_token()
  1. Check Redis cache first
  2. Decode JWT + validate claims
  3. Store result in Redis (1 hour TTL)
  4. Return cached on subsequent requests
```

#### Response Caching
```
FastMCP Middleware (automatic)
  - Caches tool call responses
  - Uses Redis as backend
  - Configurable TTL (default 1 hour)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `infrastructure/upstash_provider.py` | Upstash client wrapper + KV store interface |
| `infrastructure/distributed_rate_limiter.py` | Distributed rate limiting with Redis backend |
| `services/embedding_cache.py` | Embedding cache (Vertex AI cost reduction) |
| `services/auth/token_cache.py` | Token claim caching (AuthKit optimization) |
| `infrastructure/redis_monitoring.py` | Metrics & observability |
| `infrastructure/redis_health.py` | Health checks & diagnostics |

---

## Configuration

### Environment Variables

```bash
# Required for Upstash
UPSTASH_REDIS_REST_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token-here

# Optional: Control caching behavior
UPSTASH_REDIS_ENABLED=true        # Master switch (default: detect from URL)
MCP_RATE_LIMIT_BACKEND=distributed # 'distributed' (Redis) or 'memory'

# TTL Configuration (seconds)
CACHE_TTL_EMBEDDING=86400         # 24 hours (embeddings change rarely)
CACHE_TTL_TOKEN=3600              # 1 hour (JWT expiration)
CACHE_TTL_RESPONSE=3600           # 1 hour (tool responses)

# Observability
REDIS_METRICS_ENABLED=true
REDIS_LOG_LEVEL=INFO
```

### Rate Limit Tiers

Edit `DistributedRateLimiter.limits` in `infrastructure/distributed_rate_limiter.py`:

```python
self.limits = {
    "default": {"requests": 120, "window": 60},    # 120 req/min
    "search": {"requests": 30, "window": 60},      # 30 searches/min
    "auth": {"requests": 10, "window": 60},        # 10 auth attempts/min
    # Add more as needed
}
```

---

## Usage Examples

### Check Rate Limit Status

```python
from infrastructure.distributed_rate_limiter import get_distributed_rate_limiter

limiter = await get_distributed_rate_limiter()

# Check if user is within limit
result = await limiter.check_rate_limit("user_123", "search")
if result["allowed"]:
    print(f"Allowed, remaining: {result['remaining']}")
else:
    print(f"Rate limited, retry after: {result['retry_after']}s")
```

### Get Embedding (with cache)

```python
from services.embedding_vertex import VertexAIEmbeddingService

service = VertexAIEmbeddingService()

# Automatically caches locally + Upstash
result = await service.generate_embedding("Hello world")
print(f"Embedding: {result.embedding}")
print(f"Cached: {result.cached}")  # True if from cache
```

### Get Cache Statistics

```python
from services.embedding_cache import get_embedding_cache

cache = await get_embedding_cache()
stats = await cache.get_stats()

print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit ratio: {stats['hit_ratio']:.1f}%")
```

### Health Check

```python
from infrastructure.redis_health import get_redis_diagnostics

diagnostics = await get_redis_diagnostics()
print(diagnostics)
# Output:
# {
#   "redis": {"status": "healthy", "connected": True, ...},
#   "caching_layers": {
#     "embeddings": {"hits": 45, "hit_ratio": "85.2%"},
#     "tokens": {"hits": 230, "hit_ratio": "92.1%"}
#   },
#   "rate_limiting": {"status": "healthy", ...}
# }
```

---

## Performance & Cost Impact

### Vertex AI Embedding Cost Reduction

**Scenario**: 100 daily API calls, 60% cache hit ratio

```
Without caching:
  - 100 calls × $0.02 per 1M tokens = ~$0.002/day
  - Annual: ~$0.73

With caching (60% hit):
  - 40 calls × $0.02 per 1M tokens = ~$0.0008/day
  - Annual: ~$0.29
  - Savings: $0.44/year per service

For scale (10k calls/day):
  - Without: $20/year
  - With cache: $8/year (60% reduction)
```

### AuthKit JWKS Call Reduction

**Without caching**:
- Every token validation → JWKS HTTP call
- ~100 calls/day per service
- Adds 50-200ms per request

**With caching**:
- 1 JWKS call per unique token
- 90%+ cache hit ratio
- Auth latency: ~5ms cached vs ~100ms without

### Rate Limiting Performance

**In-memory (current)**:
- ✅ Fast: < 1ms per check
- ❌ Not distributed: each Vercel replica has separate limits
- ❌ Users can bypass by spreading requests across replicas

**Distributed Redis (new)**:
- ⚠️ Network latency: ~5-20ms per check (Upstash optimized)
- ✅ Shared across all replicas
- ✅ Atomic counter (no race conditions)
- ✅ Built-in TTL/expiration

---

## Monitoring

### Via Upstash Dashboard

1. Go to [console.upstash.com](https://console.upstash.com)
2. Select your database
3. View:
   - **Stats**: Commands/sec, memory usage, connections
   - **Commands**: Real-time command log
   - **Backups**: Automatic daily backups

### Via Application Logs

```python
# Enable metrics
from infrastructure.redis_monitoring import get_redis_metrics

metrics = await get_redis_metrics()
all_metrics = await metrics.get_all_metrics()

print(all_metrics)
# {
#   "embedding_cache": {"hits": 234, "misses": 41, "hit_ratio": 85.1},
#   "token_cache": {"hits": 1245, "misses": 95, "hit_ratio": 92.9},
#   "rate_limiting": {"checks": 5432, "exceeded": 2},
#   "redis_status": {"connected": True, "latency_ms": 15}
# }
```

### CloudWatch/Vercel Logs

Look for log patterns:
```
✅ Distributed rate limiter initialized: Upstash Redis
✅ Response caching middleware enabled (TTL: 3600s)
✅ Connected to Upstash Redis
Cache hit for embedding: ...
Token cache hit for user: ...
```

---

## Troubleshooting

### Redis Connection Fails

**Symptom**: `Failed to connect to Upstash Redis`

**Solution**:
1. Verify credentials in environment variables
2. Check that URL format is correct: `https://xxx.upstash.io`
3. Ensure token has no leading/trailing whitespace
4. Test connection:
   ```python
   from upstash_redis.asyncio import Redis
   redis = Redis.from_env()
   await redis.ping()
   ```

### Rate Limit Not Working

**Symptom**: Users can exceed rate limit

**Solution**:
1. Check that distributed rate limiter initialized (not in-memory fallback)
2. Verify `MCP_RATE_LIMIT_RPM` env var set correctly
3. Check Redis connection is active

### Cache Misses for Embeddings

**Symptom**: Cache hit ratio < 50%

**Causes**:
- Text normalization: slight variations in text (spaces, case) = different cache keys
- TTL expiration: embeddings expire after 24 hours (configurable)
- Redis memory limit: old embeddings evicted (increase Upstash quota)

**Solution**:
- Normalize text before embedding: `.strip().lower()`
- Increase `CACHE_TTL_EMBEDDING` for longer retention
- Upgrade Upstash plan for more storage

### High Latency on Rate Limit Checks

**Symptom**: Tool calls slow (>500ms)

**Causes**:
- Network latency to Upstash
- Redis is at capacity (slow commands)

**Solution**:
1. Choose closer Upstash region
2. Monitor Redis latency: `redis.ping()`
3. Upgrade to higher Upstash tier
4. Temporarily use in-memory rate limiter: `MCP_RATE_LIMIT_BACKEND=memory`

---

## Advanced Topics

### Custom Cache Keys

For embedding cache, modify `EmbeddingCache._make_key()`:

```python
def _make_key(self, text: str, model: str) -> str:
    # Current: hash-based
    # Custom: include entity type
    entity_type = text.split(":")[0]  # "entity:requirement:..."
    return f"embed:{model}:{entity_type}:{hash_text}"
```

### Cache Invalidation

Manually clear cache:

```python
# Clear embedding
cache = await get_embedding_cache()
await cache.clear("old text", "gemini-embedding-001")

# Clear token
token_cache = await get_token_cache()
await token_cache.invalidate(jwt_token)

# Reset rate limit
limiter = await get_distributed_rate_limiter()
await limiter.reset_user("user_id", "search")
```

### Backup Strategy

Upstash automatically backs up daily. To export:

```bash
# Via Upstash CLI (if installed)
upstash redis export --database-id <id> > backup.rdb
```

---

## Best Practices

1. **Set appropriate TTLs**
   - Short-lived data (1 hour): tokens, responses
   - Long-lived data (24 hours): embeddings
   - Never cache sensitive data unencrypted

2. **Monitor hit ratios**
   - Embedding cache: target > 80%
   - Token cache: target > 90%
   - If lower, investigate cache key collisions

3. **Handle failures gracefully**
   - All caches have automatic fallback to direct computation
   - Rate limiting fails open (allows requests)
   - Application continues even if Redis is down

4. **Regularly review metrics**
   - Check Upstash dashboard weekly
   - Monitor cost trends
   - Adjust TTLs based on hit ratios

5. **Security**
   - Rotate tokens regularly in Upstash console
   - Use HTTPS (always enabled with Upstash HTTP API)
   - Never commit credentials to git
   - Use Vercel environment variables for secrets

---

## Cost Estimation

### Upstash Pricing (as of Nov 2025)

| Tier | Price | Commands/month | Best For |
|------|-------|-----------------|----------|
| Free | $0 | 10K | Development |
| Pro | $0.2/100K commands | Unlimited | Production |

### ROI Calculator

```python
# Example: Production setup
requests_per_day = 5000
cache_hit_ratio = 0.70  # 70%
vertex_cost_per_call = 0.00002

# Without caching
daily_cost = requests_per_day * vertex_cost_per_call
yearly_cost = daily_cost * 365  # $36.50

# With caching
cached_calls = requests_per_day * (1 - cache_hit_ratio)
daily_cost_cached = cached_calls * vertex_cost_per_call
yearly_cost_cached = daily_cost_cached * 365  # $10.95

# Upstash cost (conservative estimate: 50K commands/day)
upstash_daily = 50000 * (0.2 / 100000)  # $0.10/day
upstash_yearly = upstash_daily * 365  # $36.50

# Total savings
savings = yearly_cost - (yearly_cost_cached + upstash_yearly)
# = $36.50 - ($10.95 + $36.50) = -$10.95 (cost neutral in this scenario)
# But: massive performance improvement + distribution benefits!
```

---

## Support & Resources

- **Upstash Docs**: https://upstash.com/docs/redis/features/restapi
- **FastMCP Docs**: https://fastmcp.wiki/en/servers/storage-backends
- **Redis Commands**: https://redis.io/commands/
- **Python SDK**: https://github.com/upstash/redis-python

---

## Migration Path (Future)

If you outgrow Upstash:

1. **Redis Cloud** ($5-100+/month for self-managed)
2. **AWS ElastiCache** (managed Redis)
3. **Dragonfly** (Redis-compatible, better performance)

All are compatible with the same code due to py-key-value-aio abstraction.

---

**Last Updated**: November 2025  
**Implementation Status**: ✅ Complete (all phases)  
**Production Ready**: ✅ Yes (with proper monitoring)
