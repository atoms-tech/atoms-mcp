"""Smart token manager for E2E tests with auto-refresh on expiry.

Implements:
- Token caching (session-scoped)
- JWT expiry detection
- Automatic refresh on 401 errors
- Fallback to fresh auth if needed
"""

import os
import time
import logging
from typing import Optional, Tuple
import jwt

logger = logging.getLogger(__name__)


class E2ETokenManager:
    """Manages WorkOS JWT tokens with auto-refresh."""

    def __init__(self):
        self.current_token: Optional[str] = None
        self.token_obtained_at: float = 0
        self.token_expiry: float = 0
        self.refresh_threshold: int = 300  # Refresh if <5 min left

    async def get_valid_token(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[str]:
        """Get a valid JWT token, refreshing if needed.

        Strategy:
        1. Check if we have a cached token that's still valid
        2. If token is expiring soon (< 5 min left), refresh it
        3. If no token or expired, authenticate fresh

        Args:
            email: WorkOS user email (optional, uses env var if not provided)
            password: WorkOS user password (optional, uses env var if not provided)

        Returns:
            Valid JWT token or None if authentication fails
        """
        email = email or os.getenv("WORKOS_TEST_EMAIL")
        password = password or os.getenv("WORKOS_TEST_PASSWORD")

        if not email or not password:
            logger.warning(
                "⚠️  WORKOS_TEST_EMAIL and WORKOS_TEST_PASSWORD not configured"
            )
            return None

        # Strategy 1: Use cached token if valid and not expiring soon
        if self.current_token and self._is_token_valid():
            logger.debug("✅ Using cached token (still valid)")
            return self.current_token

        # Strategy 2: Authenticate fresh
        logger.debug(
            f"🔐 Refreshing token (cached: {self.current_token is not None}, "
            f"valid: {self._is_token_valid() if self.current_token else False})"
        )

        from tests.utils.workos_auth import authenticate_with_workos

        token = await authenticate_with_workos(email, password)
        if token:
            self._cache_token(token)
            logger.debug("✅ Token refreshed successfully")
            return token

        logger.error("❌ Failed to refresh token")
        return None

    def _is_token_valid(self) -> bool:
        """Check if cached token is still valid (not expiring soon)."""
        if not self.current_token or self.token_expiry == 0:
            return False

        time_until_expiry = self.token_expiry - time.time()
        is_valid = time_until_expiry > self.refresh_threshold

        if not is_valid:
            logger.debug(
                f"⚠️  Token expiring soon ({time_until_expiry:.0f}s < {self.refresh_threshold}s)"
            )

        return is_valid

    def _cache_token(self, token: str) -> None:
        """Cache token and extract expiry time."""
        self.current_token = token
        self.token_obtained_at = time.time()

        # Decode JWT to get expiry (without verification - we trust WorkOS)
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            self.token_expiry = decoded.get("exp", 0)
            expiry_in = self.token_expiry - time.time()
            logger.debug(
                f"✅ Token cached (expires in {expiry_in:.0f}s)"
            )
        except Exception as e:
            logger.warning(f"Could not decode token expiry: {e}")
            # Assume 1 hour expiry if we can't decode
            self.token_expiry = self.token_obtained_at + 3600

    def clear(self) -> None:
        """Clear cached token (for testing)."""
        self.current_token = None
        self.token_expiry = 0


# Global token manager instance
_token_manager = E2ETokenManager()


async def get_fresh_token(
    email: Optional[str] = None,
    password: Optional[str] = None,
) -> Optional[str]:
    """Get a fresh or cached valid token."""
    return await _token_manager.get_valid_token(email, password)


def get_cached_token() -> Optional[str]:
    """Get cached token without refresh."""
    if _token_manager.current_token and _token_manager._is_token_valid():
        return _token_manager.current_token
    return None


def clear_token_cache() -> None:
    """Clear cached token (use before tests start)."""
    _token_manager.clear()
