# Performance Implementation Guide - Code Patterns & Examples

## 1. Redis-Backed Query Caching

### Pattern: Cache Layer Adapter
```python
class RedisQueryCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 3600
    
    async def get_or_fetch(self, cache_key, fetch_fn, ttl=None):
        """Get from cache or fetch and cache."""
        # Try Redis first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Fetch and cache
        result = await fetch_fn()
        await self.redis.setex(
            cache_key,
            ttl or self.default_ttl,
            json.dumps(result)
        )
        return result
    
    async def invalidate_pattern(self, pattern):
        """Invalidate all keys matching pattern."""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

### Integration into data_query
```python
async def data_query(
    query_type: str,
    query: str,
    cache_key: Optional[str] = None,
    cache_ttl: int = 3600,
    use_cache: bool = True,
    **kwargs
):
    # Generate cache key if not provided
    if use_cache and not cache_key:
        cache_key = f"{query_type}:{query}:{hash(str(kwargs))}"
    
    # Use cache layer
    if use_cache:
        result = await query_cache.get_or_fetch(
            cache_key,
            lambda: _execute_query(query_type, query, **kwargs),
            ttl=cache_ttl
        )
    else:
        result = await _execute_query(query_type, query, **kwargs)
    
    return result
```

---

## 2. Intelligent Prefetching

### Pattern: Prefetch Manager
```python
class PrefetchManager:
    def __init__(self, db_adapter, redis_client, embedding_service):
        self.db = db_adapter
        self.redis = redis_client
        self.embeddings = embedding_service
    
    async def predict_and_prefetch(self, user_id, current_entity_type, 
                                   current_entity_id, prefetch_depth=2):
        """Predict related entities and prefetch."""
        # Get user's access patterns
        patterns = await self._get_user_patterns(user_id)
        
        # Predict likely next entities
        predictions = await self._predict_next_entities(
            current_entity_type, current_entity_id, patterns
        )
        
        # Prefetch in background
        for entity_type, entity_ids in predictions.items():
            await self._prefetch_batch(entity_type, entity_ids)
    
    async def _prefetch_batch(self, entity_type, entity_ids):
        """Prefetch batch of entities."""
        # Fetch from DB
        entities = await self.db.query(
            entity_type,
            filters={"id": {"in": entity_ids}}
        )
        
        # Cache in Redis
        for entity in entities:
            cache_key = f"entity:{entity_type}:{entity['id']}"
            await self.redis.setex(
                cache_key,
                3600,
                json.dumps(entity)
            )
```

### Integration into entity_operation
```python
async def entity_operation(
    operation: str,
    entity_type: str,
    entity_id: str,
    prefetch_related: bool = False,
    **kwargs
):
    # Get entity
    entity = await _get_entity(entity_type, entity_id)
    
    # Prefetch related if requested
    if prefetch_related:
        await prefetch_manager.predict_and_prefetch(
            user_id=kwargs.get("user_id"),
            current_entity_type=entity_type,
            current_entity_id=entity_id
        )
    
    return entity
```

---

## 3. Hybrid Search with Caching

### Pattern: Hybrid Search Service
```python
class HybridSearchService:
    def __init__(self, vector_search, keyword_search, redis_cache):
        self.vector_search = vector_search
        self.keyword_search = keyword_search
        self.cache = redis_cache
    
    async def hybrid_search(self, query, entity_types, cache_key=None):
        """Perform hybrid search with caching."""
        # Check cache
        if cache_key:
            cached = await self.cache.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Perform both searches concurrently
        semantic_results, keyword_results = await asyncio.gather(
            self.vector_search.semantic_search(query, entity_types),
            self.keyword_search.keyword_search(query, entity_types)
        )
        
        # Combine and rank
        combined = self._combine_results(semantic_results, keyword_results)
        
        # Cache results
        if cache_key:
            await self.cache.setex(cache_key, 3600, json.dumps(combined))
        
        return combined
    
    def _combine_results(self, semantic, keyword):
        """Combine semantic and keyword results with weighted ranking."""
        # Create result map
        results_map = {}
        
        # Add semantic results (weight: 0.6)
        for result in semantic:
            key = f"{result.entity_type}:{result.id}"
            results_map[key] = {
                **result.dict(),
                "semantic_score": result.similarity,
                "keyword_score": 0.0,
                "combined_score": result.similarity * 0.6
            }
        
        # Add/merge keyword results (weight: 0.4)
        for result in keyword:
            key = f"{result.entity_type}:{result.id}"
            if key in results_map:
                results_map[key]["keyword_score"] = result.similarity
                results_map[key]["combined_score"] = (
                    results_map[key]["semantic_score"] * 0.6 +
                    result.similarity * 0.4
                )
            else:
                results_map[key] = {
                    **result.dict(),
                    "semantic_score": 0.0,
                    "keyword_score": result.similarity,
                    "combined_score": result.similarity * 0.4
                }
        
        # Sort by combined score
        return sorted(
            results_map.values(),
            key=lambda x: x["combined_score"],
            reverse=True
        )
```

### Integration into data_query
```python
async def data_query(
    query_type: str,
    query: str,
    entity_types: List[str],
    search_modes: List[str] = ["semantic", "keyword"],
    combine_strategy: str = "weighted_rank",
    cache_results: bool = True,
    **kwargs
):
    if query_type == "hybrid_search":
        cache_key = f"hybrid:{query}:{':'.join(entity_types)}" if cache_results else None
        
        result = await hybrid_search_service.hybrid_search(
            query, entity_types, cache_key
        )
        return result
```

---

## 4. Smart Embedding Generation

### Pattern: Smart Embedding Service
```python
class SmartEmbeddingService:
    def __init__(self, embedding_service, db_adapter, redis_cache):
        self.embeddings = embedding_service
        self.db = db_adapter
        self.cache = redis_cache
    
    async def smart_embed_and_search(self, query, entity_type, 
                                     auto_generate=True, batch_size=50):
        """Generate embeddings on-demand and search."""
        # Generate query embedding
        query_embedding = await self.embeddings.generate_embedding(query)
        
        # Check which entities need embeddings
        if auto_generate:
            missing = await self._find_missing_embeddings(entity_type, batch_size)
            if missing:
                await self._batch_generate_embeddings(entity_type, missing)
        
        # Perform vector search
        results = await self.db.vector_search(
            entity_type,
            query_embedding,
            limit=10
        )
        
        return results
    
    async def _batch_generate_embeddings(self, entity_type, entity_ids):
        """Batch generate embeddings for efficiency."""
        # Fetch entities
        entities = await self.db.query(
            entity_type,
            filters={"id": {"in": entity_ids}}
        )
        
        # Generate embeddings in parallel (batches of 10)
        for i in range(0, len(entities), 10):
            batch = entities[i:i+10]
            embeddings = await asyncio.gather(*[
                self.embeddings.generate_embedding(
                    entity.get("name", "") + " " + entity.get("description", "")
                )
                for entity in batch
            ])
            
            # Update DB with embeddings
            for entity, embedding in zip(batch, embeddings):
                await self.db.update(
                    entity_type,
                    filters={"id": entity["id"]},
                    data={"embedding": embedding.embedding}
                )
```

---

## 5. Cache Invalidation Strategy

### Pattern: Smart Invalidation
```python
class CacheInvalidationManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def invalidate_on_mutation(self, entity_type, entity_id, operation):
        """Invalidate related caches on entity mutation."""
        # Invalidate entity cache
        await self.redis.delete(f"entity:{entity_type}:{entity_id}")
        
        # Invalidate search caches
        await self.redis.delete(f"search:*:{entity_type}:*")
        
        # Invalidate related entity caches
        related_types = self._get_related_types(entity_type)
        for related_type in related_types:
            await self.redis.delete(f"entity:{related_type}:*")
        
        # Invalidate user-specific caches
        await self.redis.delete(f"user:*:cache:*")
    
    def _get_related_types(self, entity_type):
        """Get entity types related to this type."""
        relationships = {
            "requirement": ["test_req", "document", "project"],
            "test_req": ["requirement", "project"],
            "document": ["requirement", "project"],
            "project": ["requirement", "test_req", "document"]
        }
        return relationships.get(entity_type, [])
```

---

## 6. Performance Monitoring

### Pattern: Metrics Collection
```python
class PerformanceMetrics:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def record_operation(self, operation_type, duration_ms, cache_hit=False):
        """Record operation metrics."""
        key = f"metrics:{operation_type}"
        
        # Increment counters
        await self.redis.incr(f"{key}:count")
        if cache_hit:
            await self.redis.incr(f"{key}:cache_hits")
        
        # Track latency (simple average)
        await self.redis.lpush(f"{key}:latencies", duration_ms)
        await self.redis.ltrim(f"{key}:latencies", 0, 999)  # Keep last 1000
    
    async def get_stats(self, operation_type):
        """Get operation statistics."""
        key = f"metrics:{operation_type}"
        
        count = await self.redis.get(f"{key}:count") or 0
        cache_hits = await self.redis.get(f"{key}:cache_hits") or 0
        latencies = await self.redis.lrange(f"{key}:latencies", 0, -1)
        
        avg_latency = sum(int(l) for l in latencies) / len(latencies) if latencies else 0
        
        return {
            "total_operations": int(count),
            "cache_hits": int(cache_hits),
            "cache_hit_rate": int(cache_hits) / int(count) if count else 0,
            "avg_latency_ms": avg_latency
        }
```

---

## Testing Pattern

```python
async def test_hybrid_search_with_cache():
    """Test hybrid search with caching."""
    # First search (cache miss)
    start = time.time()
    result1 = await data_query(
        query_type="hybrid_search",
        query="authentication",
        entity_types=["requirement"],
        cache_results=True
    )
    time1 = time.time() - start
    
    # Second search (cache hit)
    start = time.time()
    result2 = await data_query(
        query_type="hybrid_search",
        query="authentication",
        entity_types=["requirement"],
        cache_results=True
    )
    time2 = time.time() - start
    
    # Cache hit should be 5-10x faster
    assert time2 < time1 / 5
    assert result1 == result2
```

