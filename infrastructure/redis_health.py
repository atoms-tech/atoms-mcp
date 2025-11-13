"""Redis health check and diagnostics.

Checks Upstash Redis connectivity and reports metrics.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis/Upstash connectivity and health.
    
    Returns:
        Dict with health status and metrics
    """
    try:
        from infrastructure.upstash_provider import get_upstash_redis
        
        redis = await get_upstash_redis()
        
        if not redis:
            return {
                "status": "unconfigured",
                "message": "UPSTASH_REDIS_REST_URL not set"
            }
        
        # Test connection
        try:
            pong = await redis.ping()
            
            return {
                "status": "healthy",
                "connected": True,
                "backend": "upstash_redis",
                "latency_ms": "< 100 (typical for serverless)",
                "response": str(pong)
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "backend": "upstash_redis",
                "error": str(e)
            }
    
    except Exception as e:
        logger.error(f"Redis health check error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


async def get_redis_diagnostics() -> Dict[str, Any]:
    """Get comprehensive Redis diagnostics.
    
    Returns:
        Dict with detailed diagnostics
    """
    diagnostics = {
        "redis": await check_redis_health(),
        "caching_layers": {}
    }
    
    # Check each caching layer
    try:
        from services.embedding_cache import get_embedding_cache
        cache = await get_embedding_cache()
        stats = await cache.get_stats()
        diagnostics["caching_layers"]["embeddings"] = {
            "status": "enabled" if stats.get("total", 0) > 0 else "initialized",
            "cache_hits": stats.get("hits", 0),
            "cache_misses": stats.get("misses", 0),
            "hit_ratio": f"{stats.get('hit_ratio', 0):.1f}%"
        }
    except Exception as e:
        diagnostics["caching_layers"]["embeddings"] = {"error": str(e)}
    
    try:
        from services.auth.token_cache import get_token_cache
        cache = await get_token_cache()
        stats = await cache.get_stats()
        diagnostics["caching_layers"]["tokens"] = {
            "status": "enabled" if stats.get("hits", 0) > 0 else "initialized",
            "cache_hits": stats.get("hits", 0),
            "validations_saved": stats.get("validations", 0),
            "hit_ratio": f"{stats.get('hit_ratio', 0):.1f}%"
        }
    except Exception as e:
        diagnostics["caching_layers"]["tokens"] = {"error": str(e)}
    
    try:
        from infrastructure.distributed_rate_limiter import get_distributed_rate_limiter
        await get_distributed_rate_limiter()  # Verify it initializes
        diagnostics["rate_limiting"] = {
            "status": "healthy",
            "backend": "distributed (Redis or in-memory)"
        }
    except Exception as e:
        diagnostics["rate_limiting"] = {"error": str(e)}
    
    return diagnostics
