"""Authentication providers for FastMCP integration."""

from .supabase_provider import (
    create_supabase_jwt_verifier,
    SupabaseAuthProvider  # Backward compatibility alias
)
from .supabase_bearer_provider import (
    create_supabase_bearer_provider,
    SupabaseTokenVerifier
)
from .supabase_oauth_provider import (
    create_supabase_oauth_provider,
    SupabaseOAuthProvider
)
from .simple_auth_provider import (
    create_supabase_simple_auth_provider,
    SupabaseSimpleAuthProvider
)

__all__ = [
    "create_supabase_jwt_verifier",
    "SupabaseAuthProvider", 
    "create_supabase_bearer_provider",
    "SupabaseTokenVerifier",
    "create_supabase_oauth_provider",
    "SupabaseOAuthProvider",
    "create_supabase_simple_auth_provider",
    "SupabaseSimpleAuthProvider"
]