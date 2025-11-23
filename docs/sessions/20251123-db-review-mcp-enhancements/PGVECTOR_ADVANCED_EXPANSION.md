# pgvector Advanced Expansion - Deeper Capabilities

## 🎯 FOUNDATION: You Already Have pgvector + PostgreSQL FTS

**Current Setup**:
- ✅ pgvector extension installed
- ✅ PostgreSQL full-text search (tsvector/tsquery)
- ✅ Semantic search capability
- ✅ Keyword search capability

**Opportunity**: Leverage advanced pgvector features + FTS optimizations for 3-10x performance

---

## 📊 PGVECTOR ADVANCED FEATURES (DEEPER)

### 1. HNSW vs IVFFlat Indexing Strategy

**Current State**: Likely using default sequential scan

**HNSW (Hierarchical Navigable Small World)**:
- ✅ Better for high-dimensional vectors (>100 dims)
- ✅ Better recall (99%+)
- ✅ Slower index build (O(n log n))
- ✅ Lower memory usage
- ✅ Better for real-time updates

**IVFFlat (Inverted File Flat)**:
- ✅ Better for lower-dimensional vectors (<100 dims)
- ✅ Faster index build
- ✅ Higher memory usage
- ✅ Tunable recall/speed tradeoff

**Recommendation**: Use HNSW for embeddings (typically 384-1536 dims)

```sql
-- Create HNSW index with tuned parameters
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- For production: higher quality
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 24, ef_construction = 100);
```

### 2. Vector Similarity Operators

**Available Operators**:
- `<->` - L2 distance (Euclidean)
- `<#>` - Negative inner product
- `<=>` - Cosine distance

**Recommendation**: Use cosine distance for embeddings

```sql
-- Cosine similarity search
SELECT id, name, 1 - (embedding <=> query_embedding) as similarity
FROM embeddings
WHERE 1 - (embedding <=> query_embedding) > 0.7
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

### 3. Vector Quantization & Compression

**Opportunity**: Reduce storage/memory by 4-8x

```sql
-- Store quantized vectors (int8 instead of float32)
ALTER TABLE embeddings ADD COLUMN embedding_quantized int8[];

-- Quantize: scale float32 to int8 range
UPDATE embeddings 
SET embedding_quantized = (embedding * 127)::int8[];

-- Create index on quantized vectors
CREATE INDEX ON embeddings USING hnsw (embedding_quantized vector_cosine_ops);
```

### 4. Approximate Nearest Neighbor (ANN) Tuning

**ef_search Parameter** (query-time tuning):

```sql
-- Fast but lower recall (ef_search = 40)
SET hnsw.ef_search = 40;
SELECT * FROM embeddings ORDER BY embedding <=> query_embedding LIMIT 10;

-- Balanced (ef_search = 100)
SET hnsw.ef_search = 100;

-- Slow but high recall (ef_search = 200)
SET hnsw.ef_search = 200;
```

---

## 📊 POSTGRESQL FTS ADVANCED FEATURES (DEEPER)

### 1. BM25 Ranking (Better than tsvector)

**Current**: PostgreSQL tsvector uses TF-IDF (basic)

**BM25**: Industry standard ranking algorithm

**Option A: pg_textsearch Extension** (Rust-based)
```sql
-- Install pg_textsearch extension
CREATE EXTENSION pg_textsearch;

-- Create BM25 index
CREATE INDEX ON documents USING bm25 (content);

-- Query with BM25 ranking
SELECT id, title, bm25_score(content, query) as score
FROM documents
WHERE content @@ plainto_tsquery(query)
ORDER BY bm25_score(content, query) DESC;
```

**Option B: ParadeDB** (PostgreSQL fork with BM25)
- Drop-in replacement for PostgreSQL
- Native BM25 support
- Better ranking than tsvector

### 2. Advanced FTS Query Operators

**Phrase Search**:
```sql
-- Exact phrase matching
SELECT * FROM documents 
WHERE content @@ phraseto_tsquery('english', 'machine learning');
```

**Proximity Search** (words within N positions):
```sql
-- Words within 5 positions
SELECT * FROM documents 
WHERE content @@ tsquery 'machine <5> learning';
```

**Boolean Operators**:
```sql
-- Complex queries
SELECT * FROM documents 
WHERE content @@ tsquery '(machine | deep) & learning & !neural';
```

### 3. Custom Dictionaries & Thesaurus

**Synonym Support**:
```sql
-- Create synonym dictionary
CREATE TEXT SEARCH DICTIONARY my_synonyms (
    TEMPLATE = synonym,
    SYNONYMS = my_synonyms
);

-- Use in configuration
ALTER TEXT SEARCH CONFIGURATION english 
    ALTER MAPPING FOR word WITH my_synonyms, english_stem;
```

### 4. Weighted FTS Columns

**Rank Different Columns**:
```sql
-- Weight title (A) higher than content (D)
SELECT id, title, 
       ts_rank(
           setweight(to_tsvector('english', title), 'A') ||
           setweight(to_tsvector('english', content), 'D'),
           plainto_tsquery('english', query)
       ) as rank
FROM documents
WHERE (setweight(to_tsvector('english', title), 'A') ||
       setweight(to_tsvector('english', content), 'D')) @@ 
      plainto_tsquery('english', query)
ORDER BY rank DESC;
```

---

## 📊 HYBRID SEARCH OPTIMIZATION (DEEPER)

### 1. Combined Ranking Strategy

```sql
-- Hybrid search: semantic + keyword + metadata
WITH semantic_results AS (
    SELECT id, 1 - (embedding <=> query_embedding) as semantic_score
    FROM embeddings
    ORDER BY embedding <=> query_embedding
    LIMIT 100
),
keyword_results AS (
    SELECT id, ts_rank(fts_vector, query_tsquery) as keyword_score
    FROM documents
    WHERE fts_vector @@ query_tsquery
    LIMIT 100
)
SELECT 
    COALESCE(s.id, k.id) as id,
    COALESCE(s.semantic_score, 0) * 0.6 +
    COALESCE(k.keyword_score, 0) * 0.4 as combined_score
FROM semantic_results s
FULL OUTER JOIN keyword_results k ON s.id = k.id
ORDER BY combined_score DESC
LIMIT 10;
```

### 2. LLM-Based Reranking

```python
# services/search/reranker.py - NEW

class HybridSearchReranker:
    """Rerank hybrid search results using LLM."""
    
    async def rerank(self, query: str, results: List[dict], top_k: int = 5):
        """Rerank results using semantic similarity."""
        # Get embeddings for results
        result_embeddings = await self.embeddings.batch_generate(
            [r.get("text", "") for r in results]
        )
        
        # Get query embedding
        query_embedding = await self.embeddings.generate(query)
        
        # Score each result
        scores = []
        for result, embedding in zip(results, result_embeddings):
            similarity = self._cosine_similarity(query_embedding, embedding)
            scores.append((result, similarity))
        
        # Sort and return top_k
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
```

---

## 📊 MATERIALIZED VIEWS FOR PERFORMANCE (DEEPER)

### 1. Incremental Materialized Views (pg_ivm)

**Problem**: Full refresh is slow

**Solution**: pg_ivm - only updates changed rows

```sql
-- Install pg_ivm extension
CREATE EXTENSION pg_ivm;

-- Create incremental materialized view
CREATE INCREMENTAL MATERIALIZED VIEW search_index AS
SELECT 
    id,
    name,
    embedding,
    to_tsvector('english', content) as fts_vector,
    created_at
FROM documents
WHERE status = 'published';

-- Create indexes
CREATE INDEX ON search_index USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON search_index USING gin (fts_vector);

-- Refresh only changed rows (fast!)
REFRESH MATERIALIZED VIEW CONCURRENTLY search_index;
```

### 2. Partial Indexes for Hot Data

```sql
-- Index only recent/popular documents
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WHERE created_at > NOW() - INTERVAL '30 days'
  AND view_count > 100;
```

---

## 📊 QUERY OPTIMIZATION STRATEGIES (DEEPER)

### 1. Explain Analyze for Tuning

```sql
-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM embeddings 
ORDER BY embedding <=> query_embedding 
LIMIT 10;

-- Look for:
-- - Sequential scan (bad) vs Index scan (good)
-- - Actual vs Planned rows
-- - Execution time
```

### 2. Connection Pooling & Caching

```python
# infrastructure/postgres_pool.py - ENHANCE

from asyncpg import create_pool

class PostgresPool:
    """Connection pool with query caching."""
    
    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 20):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool = None
        self.query_cache = {}
    
    async def initialize(self):
        """Initialize connection pool."""
        self.pool = await create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=60
        )
    
    async def execute_cached(self, query: str, *args, ttl: int = 300):
        """Execute query with caching."""
        cache_key = (query, args)
        
        # Check cache
        if cache_key in self.query_cache:
            cached_result, timestamp = self.query_cache[cache_key]
            if time.time() - timestamp < ttl:
                return cached_result
        
        # Execute query
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query, *args)
        
        # Cache result
        self.query_cache[cache_key] = (result, time.time())
        return result
```

---

## 🎯 IMPLEMENTATION ROADMAP

### Phase 1: Index Optimization (1 day)
- [ ] Create HNSW index on embeddings
- [ ] Tune m and ef_construction parameters
- [ ] Benchmark vs sequential scan
- [ ] Test with production data

### Phase 2: FTS Enhancement (1 day)
- [ ] Implement BM25 ranking (pg_textsearch)
- [ ] Add weighted column ranking
- [ ] Test phrase/proximity search
- [ ] Benchmark vs tsvector

### Phase 3: Hybrid Search (1.5 days)
- [ ] Implement combined ranking
- [ ] Add LLM-based reranking
- [ ] Test relevance improvements
- [ ] Optimize query performance

### Phase 4: Materialized Views (1 day)
- [ ] Install pg_ivm extension
- [ ] Create incremental materialized views
- [ ] Set up refresh schedule
- [ ] Monitor performance

### Phase 5: Query Optimization (0.5 days)
- [ ] Analyze query plans
- [ ] Implement connection pooling
- [ ] Add query caching
- [ ] Performance testing

**TOTAL: 5 days (40 hours)**

---

## 📊 EXPECTED PERFORMANCE IMPROVEMENTS

✅ **Search latency**: 500ms → 50-150ms (3-10x faster)  
✅ **Index size**: 30-50% reduction (quantization)  
✅ **Query throughput**: 2-5x improvement (caching)  
✅ **Recall accuracy**: 95%+ (HNSW tuning)  
✅ **Ranking quality**: 2-3x better (BM25)  
✅ **Refresh time**: 100ms → 10ms (pg_ivm)  

---

## 💡 QUICK WINS (Start Here)

1. **Create HNSW index** (30 min) - Immediate 3-5x speedup
2. **Implement BM25** (2 hours) - Better ranking
3. **Hybrid search** (4 hours) - Combined results
4. **pg_ivm setup** (2 hours) - Fast refreshes
5. **Query caching** (2 hours) - Reduce load

