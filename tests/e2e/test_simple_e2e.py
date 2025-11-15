"""Simple E2E test to verify fixture setup."""

import pytest
import os

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestSimpleE2E:
    """Simple test to verify E2E setup."""

    async def test_environment_has_supabase(self):
        """Test that Supabase environment variables are available."""
        assert os.getenv("NEXT_PUBLIC_SUPABASE_URL"), "NEXT_PUBLIC_SUPABASE_URL not set"
        assert os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"), "NEXT_PUBLIC_SUPABASE_ANON_KEY not set"
        print("✅ Supabase environment variables are available")

    async def test_can_skip_with_reason(self, e2e_auth_token):
        """Test that we can see the skip reason."""
        # This test will likely be skipped but helps us understand why
        assert True, "This test should run or show skip reason"
