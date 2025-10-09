"""
Authentication and authorization utilities for MCP server.

This module provides utilities for extracting and validating bearer tokens
from FastMCP's AuthKit OAuth integration.

Pythonic Patterns Applied:
- Type hints with Optional and Union
- Dataclass for token representation
- Context manager for rate limiting
- Custom exceptions for error handling
- Protocol for extensibility
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional, Protocol

from fastmcp.server.dependencies import get_access_token

from utils.logging_setup import get_logger

logger = get_logger("atoms_fastmcp.auth")


class RateLimiter(Protocol):
    """Protocol for rate limiter implementations."""
    
    async def check_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit."""
        ...
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for user."""
        ...


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, user_id: str, remaining: int):
        self.user_id = user_id
        self.remaining = remaining
        super().__init__(
            f"Rate limit exceeded for user {user_id}. "
            f"Remaining: {remaining} requests in current window."
        )


@dataclass(frozen=True)
class BearerToken:
    """Represents a bearer token with metadata.
    
    Attributes:
        token: The actual token string
        source: Where the token was extracted from
        claims: Optional claims dictionary
    """
    token: str
    source: str
    claims: Optional[dict[str, Any]] = None
    
    def __str__(self) -> str:
        """Return masked token for logging."""
        if len(self.token) > 10:
            return f"{self.token[:4]}...{self.token[-4:]}"
        return "***"


def extract_bearer_token() -> Optional[BearerToken]:
    """Extract bearer token from FastMCP's AuthKit OAuth.
    
    For stateless serverless with AuthKit:
    - FastMCP's AuthKitProvider validates OAuth tokens
    - Token is available via get_access_token()
    - No SessionMiddleware needed
    
    Returns:
        BearerToken if found, None otherwise
        
    Examples:
        >>> token = extract_bearer_token()
        >>> if token:
        ...     print(f"Token from {token.source}")
    """
    # Get token from FastMCP's OAuth context
    access_token = get_access_token()
    if not access_token:
        logger.debug("No access token from FastMCP")
        return None
    
    # AuthKit tokens are stored in .token attribute
    token_str = getattr(access_token, "token", None)
    if token_str:
        logger.debug("Using AuthKit token from FastMCP")
        claims = getattr(access_token, "claims", None)
        return BearerToken(
            token=token_str,
            source="authkit.token",
            claims=claims if isinstance(claims, dict) else None
        )
    
    # Fallback: check claims dict
    claims = getattr(access_token, "claims", None)
    if isinstance(claims, dict):
        for key in ("access_token", "token", "supabase_jwt"):
            candidate = claims.get(key)
            if candidate:
                logger.debug(f"Using token from claims.{key}")
                return BearerToken(
                    token=candidate,
                    source=f"authkit.claims.{key}",
                    claims=claims
                )
    
    logger.debug("No valid token found in access_token object")
    return None


async def check_rate_limit(
    user_id: str,
    rate_limiter: Optional[RateLimiter] = None
) -> None:
    """Check rate limit for user and raise exception if exceeded.
    
    Args:
        user_id: User identifier for rate limiting
        rate_limiter: Optional rate limiter instance
        
    Raises:
        RateLimitExceeded: If rate limit exceeded
        
    Examples:
        >>> await check_rate_limit("user_123", my_limiter)
    """
    if rate_limiter and not await rate_limiter.check_limit(user_id):
        remaining = rate_limiter.get_remaining(user_id)
        raise RateLimitExceeded(user_id, remaining)


@asynccontextmanager
async def rate_limited_operation(
    user_id: str,
    rate_limiter: Optional[RateLimiter] = None
) -> AsyncIterator[None]:
    """Context manager for rate-limited operations.
    
    Args:
        user_id: User identifier for rate limiting
        rate_limiter: Optional rate limiter instance
        
    Yields:
        None
        
    Raises:
        RateLimitExceeded: If rate limit exceeded
        
    Examples:
        >>> async with rate_limited_operation("user_123", limiter):
        ...     await perform_expensive_operation()
    """
    await check_rate_limit(user_id, rate_limiter)
    try:
        yield
    finally:
        # Could add cleanup logic here
        pass


async def apply_rate_limit_if_configured(
    rate_limiter: Optional[RateLimiter] = None
) -> Optional[BearerToken]:
    """Apply rate limiting if configured and return auth token.
    
    This is a convenience function that combines token extraction
    and rate limiting in one call.
    
    Args:
        rate_limiter: Optional rate limiter instance
        
    Returns:
        BearerToken if found, None otherwise
        
    Raises:
        RateLimitExceeded: If rate limit exceeded
        RuntimeError: If auth validation fails
        
    Examples:
        >>> token = await apply_rate_limit_if_configured(my_limiter)
        >>> if token:
        ...     print(f"Authenticated with {token.source}")
    """
    bearer_token = extract_bearer_token()
    
    # Only apply rate limiting if we have a token and rate limiter is configured
    if bearer_token and rate_limiter:
        # Extract user_id from token without full validation (tools will validate)
        try:
            from tools.base import ToolBase
            tool_base = ToolBase()
            await tool_base._validate_auth(bearer_token.token)
            user_id = tool_base._get_user_id()
            await check_rate_limit(user_id, rate_limiter)
        except RateLimitExceeded:
            # Re-raise rate limit exceptions
            raise
        except Exception as e:
            # If auth parsing fails, tools will handle it
            # Only propagate rate limit errors
            logger.debug(f"Auth validation during rate limit check failed: {e}")
    
    return bearer_token


def get_token_string(bearer_token: Optional[BearerToken]) -> Optional[str]:
    """Extract token string from BearerToken.
    
    Convenience function for backward compatibility.
    
    Args:
        bearer_token: BearerToken instance or None
        
    Returns:
        Token string or None
        
    Examples:
        >>> token = extract_bearer_token()
        >>> token_str = get_token_string(token)
    """
    return bearer_token.token if bearer_token else None


__all__ = [
    "extract_bearer_token",
    "check_rate_limit",
    "apply_rate_limit_if_configured",
    "rate_limited_operation",
    "get_token_string",
    "BearerToken",
    "RateLimiter",
    "RateLimitExceeded",
]

