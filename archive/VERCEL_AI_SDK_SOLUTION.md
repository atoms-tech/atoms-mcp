# Vercel AI SDK Solution for Vertex AI Embeddings

## Perfect Solution Found! 🎉

**Vercel AI SDK** has native support for Google Vertex AI embeddings with a **lightweight package** designed specifically for serverless!

## The Solution

### Package: `@ai-sdk/google-vertex`

**Key Benefits**:
- ✅ **Lightweight** - Designed for Vercel serverless
- ✅ **Native Vertex AI support** - Uses `text-embedding-004`
- ✅ **Edge Runtime support** - Works in Vercel Edge Functions
- ✅ **No heavy SDK** - Uses REST API under the hood
- ✅ **Built-in auth** - Handles Google Cloud auth

### Installation

```bash
npm install @ai-sdk/google-vertex ai
# or
pnpm add @ai-sdk/google-vertex ai
```

**Size**: ~5-10MB (vs 200MB+ for google-cloud-aiplatform)

## Implementation

### 1. Create Vercel AI SDK Embedding Service

```python
# services/embedding_vercel_vertex.py
"""Vertex AI embeddings using Vercel AI SDK (lightweight for serverless)."""

import os
import asyncio
import subprocess
import json
from typing import Optional, NamedTuple

class EmbeddingResult(NamedTuple):
    embedding: list[float]
    tokens_used: int
    model: str
    cached: bool = False

class VercelVertexEmbeddingService:
    """Lightweight Vertex AI embedding service using Vercel AI SDK."""
    
    def __init__(self, model: str = "text-embedding-004"):
        self.model = model
        self.project = os.getenv("GOOGLE_VERTEX_PROJECT")
        self.location = os.getenv("GOOGLE_VERTEX_LOCATION", "us-central1")
        
        if not self.project:
            raise ValueError("GOOGLE_VERTEX_PROJECT required")
    
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """Generate embedding using Vercel AI SDK."""
        model = model or self.model
        
        # Call Node.js script that uses Vercel AI SDK
        script = f"""
        const {{ vertex }} = require('@ai-sdk/google-vertex');
        const {{ embed }} = require('ai');
        
        async function generateEmbedding() {{
          const model = vertex.textEmbeddingModel('{model}');
          const {{ embedding }} = await embed({{
            model,
            value: process.argv[1]
          }});
          console.log(JSON.stringify({{ embedding }}));
        }}
        
        generateEmbedding().catch(console.error);
        """
        
        # Execute Node.js script
        result = await asyncio.create_subprocess_exec(
            'node', '-e', script, text,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise RuntimeError(f"Embedding generation failed: {stderr.decode()}")
        
        data = json.loads(stdout.decode())
        
        return EmbeddingResult(
            embedding=data['embedding'],
            tokens_used=0,  # Vercel AI SDK doesn't expose this
            model=model,
            cached=False
        )
```

## Better Approach: Use Vertex AI REST API Directly

Since we're in Python, let's use the Vertex AI REST API directly (no heavy SDK needed):

```python
# services/embedding_vertex_rest.py
"""Vertex AI embeddings using REST API (lightweight for serverless)."""

import os
import httpx
import asyncio
from typing import Optional, NamedTuple
from google.auth import default
from google.auth.transport.requests import Request

class EmbeddingResult(NamedTuple):
    embedding: list[float]
    tokens_used: int
    model: str
    cached: bool = False

class VertexAIRestEmbeddingService:
    """Lightweight Vertex AI embedding service using REST API."""
    
    def __init__(self, model: str = "text-embedding-004"):
        self.model = model
        self.project = os.getenv("GOOGLE_VERTEX_PROJECT")
        self.location = os.getenv("GOOGLE_VERTEX_LOCATION", "us-central1")
        
        if not self.project:
            raise ValueError("GOOGLE_VERTEX_PROJECT required")
        
        self.endpoint = (
            f"https://{self.location}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project}/locations/{self.location}/"
            f"publishers/google/models/{model}:predict"
        )
        
        # Get credentials
        self.credentials, _ = default()
    
    def _get_access_token(self) -> str:
        """Get Google Cloud access token."""
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token
    
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """Generate embedding using Vertex AI REST API."""
        
        # Get access token
        token = await asyncio.to_thread(self._get_access_token)
        
        # Make REST API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "instances": [{"content": text}]
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract embedding
            embedding = data["predictions"][0]["embeddings"]["values"]
            
            return EmbeddingResult(
                embedding=embedding,
                tokens_used=0,
                model=model or self.model,
                cached=False
            )
```

## Dependencies

### Option 1: Vercel AI SDK (Node.js)
```json
{
  "dependencies": {
    "@ai-sdk/google-vertex": "^0.0.x",
    "ai": "^3.x"
  }
}
```

### Option 2: REST API (Python - Recommended)
```txt
# requirements.txt
google-auth>=2.0.0  # ~2MB (lightweight!)
httpx>=0.28.1
```

## Comparison

| Approach | Size | Pros | Cons |
|----------|------|------|------|
| **google-cloud-aiplatform** | 200MB+ | Full SDK | Too large for Vercel |
| **Vercel AI SDK** | ~10MB | Native Vercel support | Requires Node.js |
| **REST API** | ~2MB | Lightweight, Python-native | Manual auth handling |

## Recommendation

**Use REST API approach** (Option 2):
- ✅ Lightweight (~2MB vs 200MB)
- ✅ Python-native (no Node.js needed)
- ✅ Works in Vercel serverless
- ✅ Uses Vertex AI (as required)
- ✅ Simple implementation

## Implementation Plan

1. Create `services/embedding_vertex_rest.py`
2. Update `services/embedding_factory.py` to use REST service
3. Add `google-auth` to requirements.txt
4. Test locally
5. Deploy to Vercel

## Environment Variables

```bash
# .env
GOOGLE_VERTEX_PROJECT=your-project-id
GOOGLE_VERTEX_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# For Vercel (use service account JSON)
GOOGLE_CLIENT_EMAIL=...
GOOGLE_PRIVATE_KEY=...
```

## Next Steps

1. Implement REST API embedding service
2. Update embedding factory
3. Test deployment size
4. Deploy to Vercel
5. Verify embeddings work

This solves the size issue while keeping Vertex AI! 🎉

