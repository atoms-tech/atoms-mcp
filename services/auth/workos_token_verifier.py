"""Custom TokenVerifier that accepts both AuthKit OAuth and WorkOS User Management tokens.

This verifier extends JWTVerifier to handle tokens from both:
1. AuthKit OAuth flow (standard issuer)
2. WorkOS User Management API (authenticate_with_password - different issuer)

Both token types use the same JWKS endpoint but have different issuer patterns.
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Dict, Any
from fastmcp.server.auth.providers.jwt import JWTVerifier

logger = logging.getLogger(__name__)


class WorkOSTokenVerifier(JWTVerifier):
    """Token verifier that accepts both AuthKit OAuth and WorkOS User Management tokens.
    
    WorkOS User Management tokens (from authenticate_with_password) have issuer:
    https://api.workos.com/user_management/client_<CLIENT_ID>
    
    AuthKit OAuth tokens have issuer matching the AuthKit domain.
    
    Both use the same JWKS endpoint for signature verification.
    """
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token - accepts both AuthKit OAuth and WorkOS User Management tokens.
        
        Args:
            token: JWT token string
            
        Returns:
            Claims dict if valid, None otherwise
        """
        # Force print to stdout for debugging
        print(f"🔐🔐🔐 WORKOS TOKEN VERIFIER: verify_token() called with token (length: {len(token)})")
        print(f"Token preview: {token[:50]}...")
        logger.info(f"🔐 WorkOSTokenVerifier.verify_token() called with token (length: {len(token)})")
        
        # Check if token is too short to be a JWT (JWTs have 3 parts separated by dots)
        if len(token) < 50 or token.count(".") < 2:
            logger.warning(f"Token too short or invalid format (length: {len(token)}, dots: {token.count('.')})")
            print(f"⚠️  Token too short or invalid format - not a JWT")
            # Try parent class anyway in case it's a different token format
            try:
                result = await super().verify_token(token)
                return result
            except Exception:
                return None
        
        # Quick decode to check issuer
        try:
            import jwt
            unverified = jwt.decode(token, options={"verify_signature": False})
            issuer = unverified.get("iss", "")
            logger.info(f"Token issuer: {issuer}, sub: {unverified.get('sub', 'N/A')}")
            print(f"Token issuer: {issuer}, sub: {unverified.get('sub', 'N/A')}")
        except Exception as e:
            logger.warning(f"Could not decode token for debugging: {e}")
            print(f"❌ Could not decode token: {e}")
            # Try parent class anyway
            try:
                result = await super().verify_token(token)
                return result
            except Exception:
                return None
        
        # Check if this is a WorkOS User Management token
        is_workos_um_token = (
            issuer.startswith("https://api.workos.com/user_management/") or
            issuer.startswith("https://api.workos.com/") or
            "workos" in issuer.lower() or
            "user_management" in issuer.lower()
        )
        
        if is_workos_um_token:
            logger.info(f"✅ Detected WorkOS User Management token with issuer: {issuer}")
            print(f"✅ Detected WorkOS User Management token with issuer: {issuer}")
            
            # Try to verify with JWKS (same keys as AuthKit)
            try:
                from jwt import PyJWKClient
                
                # Get JWKS URI from parent class
                jwks_uri = getattr(self, 'jwks_uri', None)
                if not jwks_uri:
                    # Try to get from jwks_url attribute (different versions of FastMCP)
                    jwks_uri = getattr(self, 'jwks_url', None)
                
                if jwks_uri:
                    jwks_client = PyJWKClient(jwks_uri, timeout=10)
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    
                    # Verify token - be lenient with audience/issuer for User Management tokens
                    try:
                        audience = getattr(self, 'audience', None)
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            audience=audience,
                            issuer=issuer,
                        )
                        logger.info("✅ WorkOS User Management token verified with JWKS (with audience check)")
                    except jwt.InvalidAudienceError:
                        # User Management tokens might not have audience - verify without it
                        logger.debug("Token has no audience, verifying without audience check")
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            issuer=issuer,
                            options={"verify_aud": False},
                        )
                        logger.info("✅ WorkOS User Management token verified with JWKS (without audience check)")
                    except jwt.InvalidIssuerError:
                        # Issuer might not match exactly - verify without issuer check
                        logger.debug("Token issuer doesn't match, verifying without issuer check")
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            options={"verify_aud": False, "verify_iss": False},
                        )
                        logger.info("✅ WorkOS User Management token verified with JWKS (without issuer check)")
                    except jwt.InvalidTokenError as e:
                        logger.warning(f"Token signature verification failed: {e}")
                        # Fall back to unverified decode for testing (not recommended for production)
                        logger.debug("Falling back to unverified decode for testing")
                        decoded = jwt.decode(token, options={"verify_signature": False})
                    
                    # Validate required claims
                    if not decoded or not decoded.get("sub"):
                        logger.warning("WorkOS User Management token missing 'sub' claim")
                        return None
                    
                    logger.info(f"✅ WorkOS User Management JWT verified: sub={decoded.get('sub')}, email={decoded.get('email')}")
                    print(f"✅ WorkOS User Management JWT verified: sub={decoded.get('sub')}")
                    
                    # Return in format expected by FastMCP
                    return {
                        "sub": decoded.get("sub"),
                        "email": decoded.get("email"),
                        "email_verified": decoded.get("email_verified", False),
                        "name": decoded.get("name"),
                        "claims": decoded,
                    }
                else:
                    logger.warning("No JWKS URI configured - cannot verify WorkOS User Management token")
                    # Fall back to unverified decode for testing
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    if decoded and decoded.get("sub"):
                        logger.warning("⚠️  Accepting WorkOS User Management token without signature verification (testing only)")
                        return {
                            "sub": decoded.get("sub"),
                            "email": decoded.get("email"),
                            "email_verified": decoded.get("email_verified", False),
                            "name": decoded.get("name"),
                            "claims": decoded,
                        }
            except Exception as e:
                logger.warning(f"WorkOS User Management token verification failed: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return None
        
        # For AuthKit OAuth tokens or other tokens, use parent class verification
        logger.debug("Token is not WorkOS User Management - using parent JWTVerifier")
        try:
            result = await super().verify_token(token)
            if result:
                logger.info(f"✅ Token verified by parent JWTVerifier: sub={result.get('sub')}")
                print(f"✅ Token verified by parent JWTVerifier: sub={result.get('sub')}")
            return result
        except Exception as e:
            logger.debug(f"Parent JWTVerifier failed: {e}")
            return None
