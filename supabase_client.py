from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from supabase import Client, create_client


class MissingSupabaseConfig(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not url or not key:
        raise MissingSupabaseConfig(
            "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set"
        )
    return create_client(url, key)

