"""Simplified Supabase client - no service role needed!

With WorkOS third-party auth, we only need anon key + user JWTs.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Client cache: token_hash -> (client, created_time)
_client_cache: dict = {}
_cache_ttl = 300  # 5 minutes


class MissingSupabaseConfig(RuntimeError):
    pass


def get_supabase(access_token: Optional[str] = None) -> Client:
    """Get Supabase client with user JWT for RLS context.

    With WorkOS configured as Supabase third-party provider,
    both Supabase JWTs and AuthKit JWTs work directly!

    Args:
        access_token: User's JWT (Supabase or AuthKit).
                     With third-party auth configured, both types work!

    Returns:
        Supabase client instance

    Note: Cached per-token for performance in serverless environments.
    """
    import hashlib
    import time

    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        raise MissingSupabaseConfig(
            "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set"
        )

    # Create cache key from token (or use 'anon' for no token)
    cache_key = "anon"
    if access_token:
        cache_key = hashlib.md5(access_token.encode()).hexdigest()[:16]

    # Check cache
    now = time.time()
    if cache_key in _client_cache:
        cached_client, created_at = _client_cache[cache_key]
        if now - created_at < _cache_ttl:
            logger.debug(f"✅ Using cached Supabase client (age: {now - created_at:.1f}s)")
            return cached_client
        else:
            # Expired, remove from cache
            del _client_cache[cache_key]

    # Create new client
    client = create_client(url, key)

    # Set the JWT for RLS context
    if access_token:
        try:
            client.postgrest.auth(access_token)
            logger.debug("✅ JWT set for RLS context in database queries")
        except Exception as e:
            logger.warning(f"⚠️ Could not configure auth: {e}")

    # Cache it
    _client_cache[cache_key] = (client, now)

    # Clean old entries (keep cache size manageable)
    if len(_client_cache) > 100:
        cutoff = now - _cache_ttl
        _client_cache.clear()  # Simple approach: clear all on overflow

    logger.debug(f"✅ Created new Supabase client (cached for {_cache_ttl}s)")
    return client
