"""
Cloud Provider Adapters - Native SDK support with CLI fallback

Specialized adapters for major cloud providers using their native SDKs.
Falls back to CLI when SDK not available.
"""

from .supabase import SupabaseAdapter
from .vercel import VercelAdapter
from .neon import NeonAdapter

__all__ = [
    'SupabaseAdapter',
    'VercelAdapter',
    'NeonAdapter',
]
