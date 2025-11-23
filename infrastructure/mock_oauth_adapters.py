"""Enhanced mock OAuth adapters with PKCE and DCR (Dynamic Client Registration) support.

FastMCP Pattern References:
- https://fastmcp.wiki/en/servers/auth/token-verification (internal Bearer tokens)
- https://fastmcp.wiki/en/servers/auth/remote-oauth (public OAuth with DCR)
- https://fastmcp.wiki/en/patterns/testing (pytest patterns)

Extends InMemoryAuthAdapter with:
- OAuth 2.0 PKCE (Proof Key for Code Exchange) flow per RFC 7231
- DCR (Dynamic Client Registration) per RFC 6749
- Authorization code flow with state validation
- Token exchange and refresh
- Pending authentication tracking (like AuthKit Standalone Connect)
- OpenID Connect (ID tokens with nonce)

This implementation follows FastMCP's RemoteAuthProvider pattern, which composes
a TokenVerifier with OAuth discovery endpoints for automated MCP client authentication.
"""

import hashlib
import secrets
import json
import time
import base64
from typing import Any, Dict, Optional
from infrastructure.mocks import InMemoryAuthAdapter


class MockOAuthAuthAdapter(InMemoryAuthAdapter):
    """Extended AuthKit mock with OAuth PKCE and DCR support.
    
    Simulates the full OAuth 2.0 flow including:
    - Authorization endpoint (returns code)
    - Token endpoint (exchanges code for tokens)
    - PKCE code challenge/verifier
    - Pending authentication state (like real AuthKit)
    """
    
    def __init__(self, *, default_user: Optional[Dict[str, Any]] = None):
        super().__init__(default_user=default_user)
        
        # OAuth PKCE state tracking
        self._auth_codes: Dict[str, Dict[str, Any]] = {}  # code -> auth context
        self._pending_auth_states: Dict[str, Dict[str, Any]] = {}  # state -> metadata
        self._pending_auth_tokens: Dict[str, Dict[str, Any]] = {}  # pending_token -> data
        self._pkce_verifiers: Dict[str, str] = {}  # state -> code_verifier
        
        # DCR (Dynamic Client Registration)
        self._dcr_clients: Dict[str, Dict[str, Any]] = {}  # client_id -> client info
        self._dcr_counter = 0
        self._auth_code_counter = 0
    
    # =====================================================
    # OAuth PKCE Handshake Simulation
    # =====================================================
    
    def create_authorization_request(
        self,
        client_id: str,
        redirect_uri: str,
        *,
        code_challenge: str,
        code_challenge_method: str = "S256",
        state: Optional[str] = None,
        nonce: Optional[str] = None,
    ) -> str:
        """Simulate /authorize endpoint.
        
        Args:
            client_id: OAuth client ID
            redirect_uri: Redirect URI from client
            code_challenge: PKCE code challenge (SHA256 hash of verifier)
            code_challenge_method: "S256" (SHA256) or "plain"
            state: CSRF protection state
            nonce: OpenID Connect nonce
            
        Returns:
            Authorization code (ready to exchange for token)
        """
        state = state or secrets.token_urlsafe(32)
        self._auth_code_counter += 1
        auth_code = f"auth_code_{self._auth_code_counter}_{secrets.token_urlsafe(16)}"
        
        self._pending_auth_states[state] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "nonce": nonce,
            "created_at": time.time(),
        }
        
        self._auth_codes[auth_code] = {
            "state": state,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "nonce": nonce,
            "created_at": time.time(),
            "expires_at": time.time() + 600,  # 10 minutes
        }
        
        return auth_code
    
    async def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> Dict[str, Any]:
        """Simulate /token endpoint (code exchange).
        
        Args:
            code: Authorization code from /authorize
            client_id: OAuth client ID
            redirect_uri: Must match /authorize request
            code_verifier: PKCE code verifier
            
        Returns:
            Token response with access_token, id_token, etc.
            
        Raises:
            ValueError: If code invalid or PKCE verification fails
        """
        if code not in self._auth_codes:
            raise ValueError("Invalid authorization code")
        
        auth_context = self._auth_codes[code]
        
        # Validate code hasn't expired
        if auth_context["expires_at"] < time.time():
            raise ValueError("Authorization code has expired")
        
        # Validate client_id matches
        if auth_context["client_id"] != client_id:
            raise ValueError("Client ID mismatch")
        
        # Validate redirect_uri matches
        if auth_context["redirect_uri"] != redirect_uri:
            raise ValueError("Redirect URI mismatch")
        
        # Verify PKCE code challenge
        self._verify_pkce(
            code_verifier,
            auth_context["code_challenge"],
            auth_context["code_challenge_method"]
        )
        
        # Generate tokens
        now = int(time.time())
        exp = now + 3600  # 1 hour
        
        # Access token (JWT-like)
        access_token = self._create_access_token(
            self._default_user["user_id"],
            client_id,
            exp
        )
        
        # ID token (OpenID Connect)
        id_token = self._create_id_token(
            self._default_user["user_id"],
            client_id,
            auth_context.get("nonce"),
            exp
        )
        
        # Refresh token
        refresh_token = f"refresh_{secrets.token_urlsafe(32)}"
        self._tokens[refresh_token] = {
            "user_info": self._default_user,
            "expires_at": now + 86400 * 7,  # 7 days
        }
        
        # Mark code as used
        del self._auth_codes[code]
        if auth_context["state"] in self._pending_auth_states:
            del self._pending_auth_states[auth_context["state"]]
        
        return {
            "access_token": access_token,
            "id_token": id_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "openid profile email",
        }
    
    def _verify_pkce(
        self,
        code_verifier: str,
        code_challenge: str,
        method: str = "S256"
    ) -> bool:
        """Verify PKCE code challenge."""
        if method == "S256":
            # SHA256 hash
            challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip("=")
        elif method == "plain":
            challenge = code_verifier
        else:
            raise ValueError(f"Unsupported code_challenge_method: {method}")
        
        if challenge != code_challenge:
            raise ValueError("PKCE verification failed")
        
        return True
    
    def _create_access_token(self, user_id: str, client_id: str, exp: int) -> str:
        """Create mock access token."""
        now = int(time.time())
        payload = {
            "sub": user_id,
            "aud": client_id,
            "iss": "mock-authkit",
            "iat": now,
            "exp": exp,
            "scope": "openid profile email",
        }
        
        # Simulate JWT structure (not cryptographically valid)
        header = base64.b64encode(b'{"alg":"RS256","typ":"JWT"}').decode().rstrip("=")
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = base64.b64encode(f"sig_{now}".encode()).decode().rstrip("=")
        
        token = f"{header}.{payload_b64}.{signature}"
        
        self._tokens[token] = {
            "user_info": self._default_user,
            "expires_at": exp,
        }
        
        return token
    
    def _create_id_token(
        self,
        user_id: str,
        client_id: str,
        nonce: Optional[str],
        exp: int
    ) -> str:
        """Create mock ID token (OpenID Connect)."""
        now = int(time.time())
        payload = {
            "sub": user_id,
            "aud": client_id,
            "iss": "mock-authkit",
            "iat": now,
            "exp": exp,
            "nonce": nonce,
            "email": self._default_user["email"],
            "email_verified": self._default_user.get("email_verified", True),
            "name": self._default_user.get("name"),
            "given_name": self._default_user.get("given_name"),
            "family_name": self._default_user.get("family_name"),
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # Simulate JWT
        header = base64.b64encode(b'{"alg":"RS256","typ":"JWT"}').decode().rstrip("=")
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = base64.b64encode(f"sig_{now}".encode()).decode().rstrip("=")
        
        return f"{header}.{payload_b64}.{signature}"
    
    # =====================================================
    # Pending Authentication (like real AuthKit)
    # =====================================================
    
    def create_pending_authentication(
        self,
        user_id: str,
        email: str,
        redirect_uri: str,
        **kwargs
    ) -> str:
        """Create pending authentication (like AuthKit does in Standalone Connect).
        
        Returns:
            pending_authentication_token for completing the handshake
        """
        token = f"pending_auth_{secrets.token_urlsafe(32)}"
        
        self._pending_auth_tokens[token] = {
            "user_id": user_id,
            "email": email,
            "redirect_uri": redirect_uri,
            "metadata": kwargs,
            "created_at": time.time(),
            "expires_at": time.time() + 3600,
        }
        
        return token
    
    async def complete_pending_authentication(
        self,
        pending_authentication_token: str,
        external_auth_id: str,
        user_data: Dict[str, Any],
    ) -> str:
        """Complete pending authentication (like real AuthKit complete endpoint).
        
        Returns:
            JWT access token for the authenticated user
        """
        if pending_authentication_token not in self._pending_auth_tokens:
            raise ValueError("Invalid pending authentication token")
        
        auth_data = self._pending_auth_tokens[pending_authentication_token]
        
        if auth_data["expires_at"] < time.time():
            raise ValueError("Pending authentication has expired")
        
        # Create user session with the provided data
        user_id = user_data.get("id") or auth_data["user_id"]
        
        # Create JWT token
        token = await self.create_session(
            user_id,
            user_data.get("email") or auth_data["email"],
            access_token=external_auth_id,
        )
        
        # Clean up
        del self._pending_auth_tokens[pending_authentication_token]
        
        return token
    
    # =====================================================
    # DCR (Dynamic Client Registration)
    # =====================================================
    
    def register_client(
        self,
        client_name: str,
        redirect_uris: list[str],
        **metadata
    ) -> Dict[str, Any]:
        """Register a new OAuth client (DCR).
        
        Args:
            client_name: Name of the client
            redirect_uris: List of allowed redirect URIs
            **metadata: Additional client metadata
            
        Returns:
            Client credentials (client_id, client_secret, etc.)
        """
        self._dcr_counter += 1
        client_id = f"client_{self._dcr_counter}_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32)
        
        client_info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "response_types": ["code", "id_token", "token"],
            "grant_types": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_method": "client_secret_basic",
            "metadata": metadata,
            "created_at": time.time(),
        }
        
        self._dcr_clients[client_id] = client_info
        
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
        }
    
    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get registered client info."""
        return self._dcr_clients.get(client_id)
    
    def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        """Validate redirect URI is registered for client."""
        client = self._dcr_clients.get(client_id)
        if not client:
            return False
        return redirect_uri in client["redirect_uris"]


# =====================================================
# Utility Functions for Tests
# =====================================================

def create_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code verifier and challenge.
    
    Returns:
        (code_verifier, code_challenge)
    """
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    return code_verifier, code_challenge
