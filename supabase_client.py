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
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        raise MissingSupabaseConfig(
            "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set"
        )

    # Create client
    client = create_client(url, key)

    # For third-party auth (WorkOS/AuthKit), DON'T use set_session
    # Instead, pass the JWT directly in API headers
    # The Supabase client will use it automatically when making requests
    if access_token:
        # Store the token for use in requests
        # For third-party JWTs, we set it on the headers instead of session
        try:
            # Detect token type
            is_authkit = False
            try:
                import jwt as jwt_lib
                decoded = jwt_lib.decode(access_token, options={"verify_signature": False})
                iss = decoded.get('iss', '')
                is_authkit = 'workos' in iss or 'authkit' in iss.lower()
            except:
                pass

            if is_authkit:
                # For AuthKit JWTs (third-party), set in headers, not session
                logger.debug("✅ Using AuthKit JWT in headers for RLS context")
                # The client library will automatically use this in the Authorization header
                client.postgrest.auth(access_token)
            else:
                # For Supabase JWTs, set both the auth session and PostgREST header
                client.auth.set_session(
                    access_token=access_token,
                    refresh_token=None
                )
                # Ensure PostgREST requests include the bearer token so RLS evaluates
                # under the 'authenticated' role with auth.uid(). Some versions of
                # supabase-py require explicit postgrest.auth() for database queries.
                try:
                    client.postgrest.auth(access_token)
                except Exception as e2:
                    logger.debug(f"postgrest.auth failed (continuing): {e2}")
                logger.debug("✅ Session + PostgREST auth set with Supabase JWT for RLS context")
        except Exception as e:
            logger.warning(f"⚠️ Could not configure auth: {e}")
            # Continue anyway - queries may still work

    return client
