# Embedding Architecture Analysis

## Current Understanding (Corrected)

You're absolutely right! Let me clarify the architecture:

### What We Actually Have

#### 1. **Search Capabilities** (Multiple Modes)

**Keyword Search** (PostgreSQL FTS):
- Uses `tsvector` and `ts_rank` in Postgres
- RPC functions: `search_requirements_fts`, `search_documents_fts`, etc.
- **No embeddings needed** ✅
- **Works in Vercel** ✅

**Semantic Search** (pgvector):
- Uses pgvector extension in Supabase Postgres
- RPC functions: `match_requirements`, `match_documents`, etc.
- Compares query embedding with stored embeddings
- **Requires embeddings** ⚠️

**Hybrid Search**:
- Combines keyword + semantic
- Weighted results from both

#### 2. **Vertex AI Role** (Embedding Generation ONLY)

**What Vertex AI Does**:
- Generates embeddings using `gemini-embedding-001`
- 768-dimensional vectors
- Used for **backfilling** and **progressive fill**
- **NOT used for search** - that's pgvector!

**What Vertex AI Does NOT Do**:
- ❌ Does NOT perform search
- ❌ Does NOT store embeddings
- ❌ Does NOT handle queries

#### 3. **Storage & Search** (Supabase/Postgres)

**pgvector Extension**:
- Stores embeddings in Postgres columns
- Performs cosine similarity search
- RPC functions handle the search
- **This runs in Supabase** ✅

**PostgreSQL FTS**:
- Full-text search with `tsvector`
- Ranking with `ts_rank`
- **This runs in Supabase** ✅

---

## The Problem

### Vertex AI is ONLY for Embedding Generation

**Current Flow**:
```
1. User creates entity (e.g., requirement)
2. Background task calls Vertex AI
3. Vertex AI generates embedding (768-dim vector)
4. Embedding stored in Postgres
5. Later: Search uses pgvector (NOT Vertex AI)
```

**The Issue**:
- Vertex AI SDK (`google-cloud-aiplatform`) is 200MB+
- Only used for step 2 (embedding generation)
- Search (step 5) uses Supabase/pgvector (no Vertex AI needed)

---

## Solutions for Vercel Deployment

### Option 1: Use OpenAI Embeddings (Recommended)

**Pros**:
- Lightweight SDK (`openai` package ~5MB)
- High quality embeddings
- Fast API
- Works in Vercel serverless

**Cons**:
- Costs money ($0.00002/1K tokens)
- External dependency

**Implementation**:
```python
# services/embedding_openai.py
from openai import AsyncOpenAI

class OpenAIEmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "text-embedding-3-small"  # 1536 dims, cheap
    
    async def generate_embedding(self, text: str):
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
```

**Cost**: ~$0.02 per 1M tokens (very cheap)

---

### Option 2: Use Supabase Edge Functions for Embeddings

**Pros**:
- No size limits
- Can use any embedding service
- Separate from main deployment

**Cons**:
- Additional complexity
- Network latency

**Architecture**:
```
MCP Server (Vercel)
  ├─ CRUD operations
  ├─ Search (uses existing embeddings)
  └─ Calls Edge Function for new embeddings →

Supabase Edge Function
  ├─ Receives text
  ├─ Calls Vertex AI / OpenAI
  └─ Returns embedding
```

---

### Option 3: Use Hugging Face Inference API

**Pros**:
- Free tier available
- Good quality embeddings
- Lightweight SDK

**Cons**:
- Slower than OpenAI
- Rate limits on free tier

**Implementation**:
```python
# services/embedding_hf.py
import httpx

class HuggingFaceEmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY")
        self.model = "sentence-transformers/all-MiniLM-L6-v2"
    
    async def generate_embedding(self, text: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{self.model}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"inputs": text}
            )
            return response.json()
```

---

### Option 4: Make Embeddings Optional (Current)

**Pros**:
- Deployment works now
- Keyword search still available
- Can add embeddings later

**Cons**:
- No semantic search in production
- Missing key feature

**Status**: ✅ Currently implemented

---

## Recommended Solution

### Hybrid Approach: OpenAI for Production + Vertex AI for Dev

**Production (Vercel)**:
```python
# services/embedding_factory.py
def get_embedding_service():
    # Check environment
    if os.getenv("OPENAI_API_KEY"):
        from .embedding_openai import OpenAIEmbeddingService
        return OpenAIEmbeddingService()
    
    # Fallback to mock
    from .embedding_mock import MockEmbeddingService
    return MockEmbeddingService()
```

**Development (Local)**:
```python
# With Vertex AI
if os.getenv("GOOGLE_CLOUD_PROJECT"):
    from .embedding_vertex import VertexAIEmbeddingService
    return VertexAIEmbeddingService()
```

**Benefits**:
- ✅ Works in Vercel (OpenAI SDK is tiny)
- ✅ Semantic search available
- ✅ Can still use Vertex AI locally
- ✅ Minimal code changes

---

## Implementation Plan

### Step 1: Add OpenAI Embedding Service

```bash
# Add to requirements.txt
openai>=1.0.0  # ~5MB
```

### Step 2: Create OpenAI Service

```python
# services/embedding_openai.py
```

### Step 3: Update Factory

```python
# services/embedding_factory.py
def get_embedding_service():
    # Try OpenAI first (production)
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddingService()
    
    # Try Vertex AI (development)
    if _check_vertex_ai_available():
        return VertexAIEmbeddingService()
    
    # Fallback to mock
    return MockEmbeddingService()
```

### Step 4: Deploy

```bash
vercel --prod
```

---

## Cost Analysis

### OpenAI Embeddings

**Model**: `text-embedding-3-small`
- **Dimensions**: 1536 (vs 768 for Vertex AI)
- **Cost**: $0.00002 per 1K tokens
- **Example**: 1M requirements @ 100 tokens each = $2

**Model**: `text-embedding-3-large`
- **Dimensions**: 3072
- **Cost**: $0.00013 per 1K tokens
- **Higher quality but more expensive**

### Vertex AI Embeddings

**Model**: `gemini-embedding-001`
- **Dimensions**: 768
- **Cost**: Free tier, then ~$0.00001 per 1K tokens
- **Issue**: 200MB+ SDK

---

## Recommendation

**Immediate**: Use OpenAI embeddings for production
**Long-term**: Consider Supabase Edge Functions for flexibility

**Why OpenAI**:
1. ✅ Tiny SDK (~5MB vs 200MB)
2. ✅ High quality embeddings
3. ✅ Fast and reliable
4. ✅ Very cheap ($2 per 1M requirements)
5. ✅ Works in Vercel serverless

**Next Steps**:
1. Add OpenAI embedding service
2. Update factory to prefer OpenAI
3. Keep Vertex AI for local dev
4. Deploy to Vercel
5. Test semantic search

---

## Summary

**You were right!**:
- Vertex AI is ONLY for embedding generation
- pgvector (Supabase) handles all search
- PostgreSQL FTS handles keyword search
- No "RAG service" needed - it's all in Supabase

**The fix**:
- Replace Vertex AI with OpenAI for embedding generation
- Keep pgvector for search (already in Supabase)
- Keep PostgreSQL FTS for keyword search (already in Supabase)
- Everything works in Vercel!

