"""Simplified Supabase client - no service role needed!

With WorkOS third-party auth, we only need anon key + user JWTs.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from supabase import Client, create_client

logger = logging.getLogger(__name__)


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

    Note: Not cached - ensures thread safety and proper JWT context per request.
    """
    # Use connection pooler for serverless environments (6x faster!)
    # Falls back to direct URL if pooler not configured
    pooler_url = os.getenv("SUPABASE_POOLER_URL")
    direct_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")

    url = pooler_url or direct_url
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        raise MissingSupabaseConfig(
            "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set"
        )

    # Create client
    client = create_client(url, key)

    # Set the JWT for RLS context (works for both Supabase and third-party JWTs)
    if access_token:
        try:
            # For database queries, we need to set the Authorization header
            # This works for both Supabase JWTs and third-party JWTs (like AuthKit)
            # The postgrest client will use this token for RLS evaluation
            client.postgrest.auth(access_token)
            logger.debug("✅ JWT set for RLS context in database queries")
        except Exception as e:
            logger.warning(f"⚠️ Could not configure auth: {e}")
            # Continue anyway - queries may still work

    return client
