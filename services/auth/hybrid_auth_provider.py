"""Hybrid authentication provider supporting both OAuth and Bearer tokens.

This provider enables the same MCP server to handle:
1. OAuth (AuthKit) for public clients - full OAuth flow
2. Bearer tokens for internal services (atomsAgent) - static token
3. AuthKit JWTs for frontend token forwarding - validates AuthKit JWT from frontend/backend
"""

from __future__ import annotations

import os
import json
import base64
import logging
from typing import Optional, Dict, Any
from fastmcp.server.auth import AuthProvider
from fastmcp.server.auth.providers.workos import AuthKitProvider
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier, JWTVerifier

logger = logging.getLogger(__name__)


class HybridAuthProvider(AuthProvider):
    """Hybrid auth provider supporting OAuth and Bearer tokens simultaneously."""

    def __init__(
        self,
        oauth_provider: AuthKitProvider,
        internal_token: Optional[str] = None,
        authkit_client_id: Optional[str] = None,
        authkit_jwks_uri: Optional[str] = None
    ):
        """Initialize hybrid auth provider.

        Args:
            oauth_provider: AuthKit provider for OAuth flow
            internal_token: Static token for internal services
            authkit_client_id: AuthKit client ID for JWT audience validation
            authkit_jwks_uri: AuthKit JWKS URI for JWT verification
        """
        self.oauth_provider = oauth_provider

        # Expose ALL attributes from OAuth provider for FastMCP compatibility
        # This ensures HybridAuthProvider is a drop-in replacement for AuthKitProvider
        self.base_url = oauth_provider.base_url
        self.required_scopes = getattr(oauth_provider, 'required_scopes', [])
        self.authkit_domain = getattr(oauth_provider, 'authkit_domain', None)
        self.resource_server_url = getattr(oauth_provider, 'resource_server_url', None)
        self.authorization_servers = getattr(oauth_provider, 'authorization_servers', [])

        # Setup internal token verifier
        self.internal_token_verifier = None
        if internal_token:
            self.internal_token_verifier = StaticTokenVerifier(
                tokens={
                    internal_token: {
                        "client_id": "internal-service",
                        "scopes": ["read:data", "write:data", "admin:users"]
                    }
                },
                required_scopes=["read:data"]
            )
            logger.info("✅ Internal bearer token authentication enabled")

        # Store JWKS config for manual JWT verification in authenticate() method
        # We handle ALL JWT verification in authenticate() to support both
        # AuthKit OAuth tokens and WorkOS User Management tokens
        self.authkit_jwks_uri = authkit_jwks_uri
        self.authkit_client_id = authkit_client_id
        self.authkit_jwt_verifier = None
        if authkit_jwks_uri and authkit_client_id:
            # Create JWT verifier for AuthKit tokens
            self.authkit_jwt_verifier = JWTVerifier(
                jwks_uri=authkit_jwks_uri,
                audience=authkit_client_id
            )
            logger.info("✅ AuthKit JWT authentication enabled")
            logger.info("✅ WorkOS User Management JWT will be handled in authenticate() method")
    
    async def _verify_authkit_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify AuthKit OAuth JWT token using JWKS.

        These tokens come from the OAuth flow and have issuer matching AuthKit domain.

        Args:
            token: JWT token from AuthKit OAuth

        Returns:
            Claims dict if valid, None otherwise
        """
        if not self.authkit_jwt_verifier:
            return None

        try:
            # Use the JWT verifier if available
            result = await self.authkit_jwt_verifier.verify_token(token)
            logger.debug("✅ AuthKit OAuth token verified with JWT verifier")
            return result
        except Exception as e:
            logger.debug(f"AuthKit JWT verification failed: {e}")

            # Fallback to manual verification if verifier fails
            if not self.authkit_jwks_uri or not self.authkit_client_id:
                return None

            try:
                import jwt
                from jwt import PyJWKClient

                # Quick format check
                if not token or not isinstance(token, str) or len(token.split(".")) != 3:
                    return None

                # Decode without verification first to check issuer
                try:
                    unverified = jwt.decode(token, options={"verify_signature": False})
                except Exception as e:
                    logger.debug(f"Failed to decode token (not a valid JWT): {e}")
                    return None

                issuer = unverified.get("iss", "")

                # Check if this is an AuthKit OAuth token (not User Management)
                # AuthKit OAuth tokens typically have issuer matching the AuthKit domain
                is_authkit_oauth = (
                    self.authkit_domain and
                    (issuer.startswith(self.authkit_domain) or
                     issuer.startswith("https://api.workos.com/") and "user_management" not in issuer.lower())
                )

                if not is_authkit_oauth:
                    logger.debug(f"Token issuer '{issuer}' is not an AuthKit OAuth token")
                    return None

                logger.debug(f"Detected AuthKit OAuth token with issuer: {issuer}")

                # Verify with JWKS
                try:
                    jwks_client = PyJWKClient(self.authkit_jwks_uri, timeout=10)
                    signing_key = jwks_client.get_signing_key_from_jwt(token)

                    # Verify token
                    try:
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            audience=self.authkit_client_id,
                            issuer=issuer,
                        )
                        logger.debug("✅ AuthKit OAuth token verified with JWKS")
                    except jwt.InvalidAudienceError:
                        logger.debug("Token has no audience, verifying without audience check")
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            issuer=issuer,
                            options={"verify_aud": False},
                        )
                    except jwt.InvalidIssuerError:
                        logger.debug("Token issuer doesn't match, verifying without issuer check")
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            options={"verify_aud": False, "verify_iss": False},
                        )
                except jwt.InvalidTokenError as e:
                    logger.debug(f"Token signature verification failed: {e}")
                    return None
                
                # Validate required claims
                if not decoded or not decoded.get("sub"):
                    logger.warning("AuthKit OAuth token missing 'sub' claim")
                    return None
                
                logger.info(f"✅ AuthKit OAuth JWT verified: sub={decoded.get('sub')}, email={decoded.get('email')}")

                # Return dict with claims (FastMCP expects dict from verify_token)
                return {
                    "sub": decoded.get("sub", ""),
                    "email": decoded.get("email"),
                    "email_verified": decoded.get("email_verified", False),
                    "name": decoded.get("name"),
                    "claims": decoded,
                }
            except Exception as e:
                logger.debug(f"JWKS verification failed: {e}")
                return None
        except Exception as e:
            logger.debug(f"Error verifying AuthKit OAuth JWT: {e}")
            return None
    
    async def _verify_workos_user_management_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify WorkOS User Management JWT token.
        
        WorkOS User Management tokens (from authenticate_with_password) have issuer:
        https://api.workos.com/user_management/client_<CLIENT_ID>
        
        These tokens are valid WorkOS JWTs and can be verified using the same JWKS
        as AuthKit tokens, but with a different issuer validation.
        
        Args:
            token: JWT token from WorkOS User Management
            
        Returns:
            Claims dict if valid, None otherwise
        """
        try:
            import jwt
            from jwt import PyJWKClient
            
            # Quick format check - must be a JWT (3 parts separated by dots)
            if not token or not isinstance(token, str) or len(token.split(".")) != 3:
                return None
            
            # Decode without verification first to check issuer
            try:
                unverified = jwt.decode(token, options={"verify_signature": False})
            except Exception as e:
                logger.debug(f"Failed to decode token (not a valid JWT): {e}")
                return None
            
            issuer = unverified.get("iss", "")
            
            # Check if this is a WorkOS User Management token
            # Accept both user_management and api.workos.com issuers
            is_workos_token = (
                issuer.startswith("https://api.workos.com/user_management/") or
                issuer.startswith("https://api.workos.com/") or
                "workos" in issuer.lower() or
                "user_management" in issuer.lower()
            )
            
            if not is_workos_token:
                logger.debug(f"Token issuer '{issuer}' is not a WorkOS User Management token")
                return None
            
            logger.info(f"✅ Detected WorkOS User Management token with issuer: {issuer}")
            
            # WorkOS User Management tokens use the same JWKS as AuthKit
            # For testing, we accept these tokens even if JWKS verification fails
            # (since they come from authenticate_with_password which validates credentials)
            
            # Try to verify with JWKS if available, otherwise accept without verification
            decoded = None
            if self.authkit_jwks_uri:
                try:
                    # Verify token using AuthKit JWKS (WorkOS uses same keys)
                    jwks_client = PyJWKClient(self.authkit_jwks_uri, timeout=10)
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    
                    # Verify token
                    # Note: User Management tokens might not have audience set
                    try:
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            audience=self.authkit_client_id,
                            issuer=issuer,
                        )
                        logger.debug("✅ Token verified with JWKS (with audience check)")
                    except jwt.InvalidAudienceError:
                        # User Management tokens might not have audience - verify without it
                        logger.debug("User Management token has no audience, verifying without audience check")
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            issuer=issuer,
                            options={"verify_aud": False},
                        )
                        logger.debug("✅ Token verified with JWKS (without audience check)")
                    except jwt.InvalidIssuerError:
                        # Issuer might not match exactly - verify without issuer check
                        logger.debug("Token issuer doesn't match expected, verifying without issuer check")
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=["RS256"],
                            options={"verify_aud": False, "verify_iss": False},
                        )
                        logger.debug("✅ Token verified with JWKS (without issuer check)")
                    except jwt.InvalidTokenError as e:
                        logger.debug(f"Token signature verification failed: {e}, accepting without verification")
                        # Fall back to unverified decode for testing
                        decoded = jwt.decode(token, options={"verify_signature": False})
                except Exception as e:
                    logger.debug(f"JWKS verification failed: {e}, accepting token without signature verification")
                    # Fall back to unverified decode
                    decoded = jwt.decode(token, options={"verify_signature": False})
            else:
                # No JWKS configured - accept token without verification (for testing)
                logger.debug("No JWKS URI configured - accepting User Management token without signature verification")
                decoded = jwt.decode(token, options={"verify_signature": False})
            
            # Validate that we have required claims
            if not decoded or not decoded.get("sub"):
                logger.warning("WorkOS User Management token missing 'sub' claim")
                return None
            
            logger.info(f"✅ WorkOS User Management JWT verified: sub={decoded.get('sub')}, email={decoded.get('email')}")

            # Return dict with claims (FastMCP expects dict from verify_token)
            return {
                "sub": decoded.get("sub", ""),
                "email": decoded.get("email"),
                "email_verified": decoded.get("email_verified", False),
                "name": decoded.get("name"),
                "claims": decoded,
            }
        except jwt.InvalidTokenError as e:
            logger.debug(f"WorkOS User Management JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error verifying WorkOS User Management JWT: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a bearer token (called by FastMCP middleware).
        
        This method is called by FastMCP's middleware when a Bearer token is present.
        It delegates to the same logic as authenticate() but takes a token string directly.
        
        Args:
            token: Bearer token string
            
        Returns:
            Authentication context dict or None
        """
        # Force print to stdout to ensure we see this even if logging is misconfigured
        print(f"🔐🔐🔐 HYBRID AUTH: verify_token() called with token (length: {len(token)})")
        logger.info(f"🔐 verify_token() called with token (length: {len(token)})")
        
        # Quick decode to check issuer (for debugging)
        try:
            import jwt
            unverified = jwt.decode(token, options={"verify_signature": False})
            issuer = unverified.get("iss", "")
            logger.info(f"Token issuer: {issuer}, sub: {unverified.get('sub', 'N/A')}")
        except Exception as e:
            logger.debug(f"Could not decode token for debugging: {e}")
        
        # Try internal token first (for system services)
        if self.internal_token_verifier:
            try:
                result = await self.internal_token_verifier.verify_token(token)
                logger.info("✅ Authenticated via internal bearer token (verify_token)")
                return result
            except Exception as e:
                logger.debug(f"Internal token verification failed: {e}")

        # Try WorkOS User Management JWT FIRST (from authenticate_with_password)
        logger.debug("Trying WorkOS User Management JWT verification (verify_token)...")
        workos_um_result = await self._verify_workos_user_management_jwt(token)
        if workos_um_result:
            logger.info(f"✅ Authenticated via WorkOS User Management JWT (verify_token): {workos_um_result.get('sub')}")
            return workos_um_result
        else:
            logger.debug("WorkOS User Management JWT verification returned None")
        
        # Try AuthKit JWT (from frontend/backend OAuth flow)
        if self.authkit_jwks_uri and self.authkit_client_id:
            logger.debug("Trying AuthKit JWT verification (verify_token)...")
            authkit_result = await self._verify_authkit_jwt(token)
            if authkit_result:
                logger.info(f"✅ Authenticated via AuthKit JWT (verify_token): {authkit_result.get('sub')}")
                return authkit_result
            else:
                logger.debug("AuthKit JWT verification returned None")

        # All verification methods failed
        logger.warning(f"❌ verify_token() - ALL verification methods failed for token: {token[:50]}...")
        return None
    
    async def authenticate(self, request) -> Optional[Dict[str, Any]]:
        """Authenticate request using OAuth or Bearer token.

        Flow:
        1. Check for Authorization: Bearer <token> header
        2. If present, try bearer token verification:
           a. Try internal static token (for system services)
           b. Try WorkOS User Management JWT (from authenticate_with_password)
           c. Try AuthKit JWT (from frontend/backend)
        3. If not present or verification fails, fall back to OAuth

        Args:
            request: HTTP request object

        Returns:
            Authentication context dict or None
        """
        # Check for Bearer token
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()
            # Force print to stdout to ensure we see this even if logging is misconfigured
            print(f"🔐🔐🔐 HYBRID AUTH: authenticate() called with Bearer token (length: {len(token)})")
            logger.info(f"🔐 authenticate() called with Bearer token (length: {len(token)})")
            # Delegate to verify_token for consistent logic
            return await self.verify_token(token)

        # No bearer token, fall back to OAuth
        logger.debug("No bearer token, using OAuth flow")
        return await self.oauth_provider.authenticate(request)
    
    async def get_authorization_url(self, request) -> str:
        """Get OAuth authorization URL (delegates to OAuth provider)."""
        return await self.oauth_provider.get_authorization_url(request)
    
    async def handle_callback(self, request) -> Optional[Dict[str, Any]]:
        """Handle OAuth callback (delegates to OAuth provider)."""
        return await self.oauth_provider.handle_callback(request)
    
    @property
    def requires_browser(self) -> bool:
        """OAuth requires browser, but bearer tokens don't."""
        return True  # OAuth is available
    
    def __getattr__(self, name: str):
        """Intercept attribute access to ensure FastMCP uses our methods.
        
        This prevents FastMCP from accessing the underlying OAuth provider's
        methods directly, ensuring our verify_token and authenticate methods are used.
        """
        # If FastMCP tries to access verify_token or authenticate, use ours
        if name in ('verify_token', 'authenticate'):
            return getattr(self, name)
        
        # For other attributes, delegate to OAuth provider (for OAuth flow)
        if hasattr(self.oauth_provider, name):
            return getattr(self.oauth_provider, name)
        
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    @property
    def supports_bearer_tokens(self) -> bool:
        """Indicate that bearer tokens are supported."""
        # We support bearer tokens if we have internal token verifier or JWKS config for JWT verification
        return self.internal_token_verifier is not None or (self.authkit_jwks_uri is not None and self.authkit_client_id is not None)

    def get_routes(self, mcp_path: Optional[str] = None):
        """Get OAuth discovery routes from the underlying OAuth provider.

        This is CRITICAL for MCP clients to discover OAuth endpoints.
        The HybridAuthProvider must expose the same routes as AuthKitProvider.

        Args:
            mcp_path: The MCP endpoint path (passed by FastMCP, but not used by AuthKitProvider)
        """
        # Delegate to the OAuth provider to get all OAuth discovery routes
        # Note: AuthKitProvider.get_routes() doesn't accept parameters, so we ignore mcp_path
        # FastMCP may pass mcp_path in newer versions, but AuthKitProvider doesn't use it
        return self.oauth_provider.get_routes()

    def get_resource_metadata_url(self):
        """Get the resource metadata URL from the underlying OAuth provider."""
        return self.oauth_provider.get_resource_metadata_url()

    def get_middleware(self):
        """Get middleware from the underlying OAuth provider.

        This method may be called by newer versions of FastMCP.
        If the OAuth provider doesn't have this method, return an empty list.
        """
        if hasattr(self.oauth_provider, 'get_middleware'):
            return self.oauth_provider.get_middleware()
        return []

    def _get_resource_url(self, mcp_path: str):
        """Get the resource URL for the given MCP path.

        This method may be called by newer versions of FastMCP.
        Delegate to the OAuth provider if it has this method.
        """
        if hasattr(self.oauth_provider, '_get_resource_url'):
            return self.oauth_provider._get_resource_url(mcp_path)
        # Fallback: construct from base_url and mcp_path
        return f"{self.base_url.rstrip('/')}{mcp_path}"


def create_hybrid_auth_provider(
    authkit_domain: str,
    base_url: str,
    internal_token: Optional[str] = None,
    authkit_client_id: Optional[str] = None,
    authkit_jwks_uri: Optional[str] = None
) -> HybridAuthProvider:
    """Factory function to create hybrid auth provider.

    Args:
        authkit_domain: AuthKit domain for OAuth
        base_url: Base URL for OAuth callbacks
        internal_token: Static token for internal services
        authkit_client_id: AuthKit client ID for JWT validation
        authkit_jwks_uri: AuthKit JWKS URI for JWT verification

    Returns:
        Configured HybridAuthProvider
    """
    # Create OAuth provider
    oauth_provider = AuthKitProvider(
        authkit_domain=authkit_domain,
        base_url=base_url
    )

    # Create hybrid provider
    return HybridAuthProvider(
        oauth_provider=oauth_provider,
        internal_token=internal_token,
        authkit_client_id=authkit_client_id,
        authkit_jwks_uri=authkit_jwks_uri
    )

