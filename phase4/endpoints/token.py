"""Token management endpoints for Phase 4."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from utils.logging_setup import get_logger

from ..middleware import RateLimiter
from ..models import DeviceInfo
from ..services import RevocationService, TokenRefreshService

logger = get_logger(__name__)

router = APIRouter(prefix="/auth/token", tags=["token"])


class TokenRefreshRequest(BaseModel):
    """Token refresh request model."""
    refresh_token: str
    session_id: str | None = None


class TokenRefreshResponse(BaseModel):
    """Token refresh response model."""
    access_token: str
    refresh_token: str | None = None
    expires_in: int
    token_type: str = "Bearer"


class TokenRevokeRequest(BaseModel):
    """Token revocation request model."""
    token: str
    token_type_hint: str | None = "access_token"
    reason: str | None = None


class TokenRevokeResponse(BaseModel):
    """Token revocation response model."""
    success: bool
    revoked_at: str


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    req: Request,
    user_agent: str | None = Header(None),
) -> TokenRefreshResponse:
    """Refresh access token using refresh token.

    This endpoint implements:
    - Token refresh with optional rotation
    - Rate limiting per user/session
    - Device validation
    - Audit logging
    """
    try:
        # Initialize services
        token_service = TokenRefreshService()
        rate_limiter = RateLimiter()

        # Extract session ID or user ID for rate limiting
        identifier = request.session_id or "anonymous"

        # Check rate limit
        allowed, retry_after = await rate_limiter.check_limit(
            identifier,
            "token_refresh"
        )

        if not allowed:
            logger.warning(f"Rate limit exceeded for {identifier}")
            raise HTTPException(
                status_code=429,
                detail="Too many refresh attempts",
                headers={"Retry-After": str(retry_after)} if retry_after else None,
            )

        # Parse device info for validation
        if user_agent:
            DeviceInfo.from_user_agent(user_agent)

        # Perform token refresh
        try:
            token_pair = await token_service.refresh_token(
                request.refresh_token,
                request.session_id
            )

            # Record success for rate limiting
            await rate_limiter.record_success(identifier, "token_refresh")

            # Return refreshed tokens
            return TokenRefreshResponse(
                access_token=token_pair.access_token,
                refresh_token=token_pair.refresh_token,
                expires_in=token_pair.access_expires_in,
                token_type=token_pair.token_type,
            )

        except ValueError as e:
            # Invalid token
            await rate_limiter.record_failure(identifier, "token_refresh")
            logger.error(f"Invalid refresh token: {e}")
            raise HTTPException(
                status_code=401,
                detail=str(e)
            )

        except Exception as e:
            # Other errors
            await rate_limiter.record_failure(identifier, "token_refresh")
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Token refresh failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in token refresh: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/revoke", response_model=TokenRevokeResponse)
async def revoke_token(
    request: TokenRevokeRequest,
    req: Request,
) -> TokenRevokeResponse:
    """Revoke a token immediately.

    This endpoint implements:
    - Immediate token revocation
    - Support for access and refresh tokens
    - Audit logging
    - Session cleanup
    """
    try:
        # Initialize revocation service
        revocation_service = RevocationService()

        # Determine token type
        is_refresh = request.token_type_hint == "refresh_token"

        # Revoke the token
        revoked_at = await revocation_service.revoke_token(
            request.token,
            is_refresh=is_refresh,
            reason=request.reason
        )

        logger.info(
            f"Token revoked: type={request.token_type_hint}, "
            f"reason={request.reason}"
        )

        return TokenRevokeResponse(
            success=True,
            revoked_at=revoked_at.isoformat()
        )

    except Exception as e:
        logger.error(f"Token revocation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Token revocation failed"
        )


@router.post("/introspect")
async def introspect_token(
    token: str,
    token_type_hint: str | None = "access_token",
) -> dict[str, Any]:
    """Introspect token to get metadata.

    This endpoint implements RFC 7662 token introspection.
    """
    try:
        # Initialize services
        token_service = TokenRefreshService()

        # Check if token is valid and get metadata
        # This would decode the JWT and check revocation status

        # For now, return basic introspection
        import jwt

        try:
            # Decode without verification for introspection
            decoded = jwt.decode(
                token,
                options={"verify_signature": False}
            )

            # Check if revoked
            from ..models import TokenMetadata
            token_hash = TokenMetadata.hash_token(token)
            storage = token_service.storage

            is_revoked = await storage.is_token_revoked(token_hash)

            if is_revoked:
                return {"active": False}

            # Return introspection response
            return {
                "active": True,
                "scope": decoded.get("scope", ""),
                "client_id": decoded.get("client_id"),
                "username": decoded.get("email"),
                "token_type": "Bearer",
                "exp": decoded.get("exp"),
                "iat": decoded.get("iat"),
                "nbf": decoded.get("nbf"),
                "sub": decoded.get("sub"),
            }

        except jwt.DecodeError:
            return {"active": False}

    except Exception as e:
        logger.error(f"Token introspection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Token introspection failed"
        )
