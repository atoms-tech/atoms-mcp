#!/usr/bin/env python3
"""Get a real AuthKit JWT token via OAuth flow.

This script performs the OAuth flow to authenticate with WorkOS/AuthKit
and retrieve a real JWT token for E2E testing.

Usage:
    # Interactive mode (opens browser)
    python scripts/get_authkit_token_oauth.py
    
    # Non-interactive mode (requires manual code entry)
    python scripts/get_authkit_token_oauth.py --manual

Environment variables:
    - WORKOS_API_KEY (required)
    - WORKOS_CLIENT_ID (required)
    - WORKOS_REDIRECT_URI (required, e.g., http://localhost:3000/callback)
    - WORKOS_COOKIE_PASSWORD (optional, for sealed sessions)
"""

import os
import sys
import asyncio
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Load .env file if it exists
env_file = Path(".env")
if env_file.exists():
    try:
        from dotenv import dotenv_values
        env_vars = dotenv_values(".env")
        for k, v in env_vars.items():
            if v and k not in os.environ:
                os.environ[k] = v
    except ImportError:
        pass

# Import WorkOS SDK - use WorkOSClient (newer SDK) or WorkOS (older SDK)
try:
    from workos import WorkOSClient
    WorkOS = WorkOSClient  # Alias for compatibility
except ImportError:
    try:
        from workos import WorkOS
    except ImportError:
        try:
            # Try alternative import path
            import workos
            if hasattr(workos, 'WorkOSClient'):
                WorkOS = workos.WorkOSClient
            elif hasattr(workos, 'WorkOS'):
                WorkOS = workos.WorkOS
            else:
                print("❌ WorkOS Python SDK not installed or wrong version")
                print("   Install with: pip install workos")
                print("   Or with uv: uv pip install workos")
                print("\n   If using uv, make sure you're in the virtual environment:")
                print("   source .venv/bin/activate")
                sys.exit(1)
        except ImportError:
            print("❌ WorkOS Python SDK not installed")
            print("   Install with: pip install workos")
            print("   Or with uv: uv pip install workos")
            print("\n   If using uv, make sure you're in the virtual environment:")
            print("   source .venv/bin/activate")
            sys.exit(1)


def get_authorization_url(workos_client, redirect_uri: str) -> str:
    """Get OAuth authorization URL from WorkOS."""
    try:
        # Use User Management to get authorization URL
        auth_url = workos_client.user_management.get_authorization_url(
            provider="authkit",
            redirect_uri=redirect_uri,
        )
        return auth_url
    except Exception as e:
        print(f"❌ Failed to get authorization URL: {e}")
        return None


def authenticate_with_code(workos_client, code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for session/token."""
    try:
        cookie_password = os.getenv("WORKOS_COOKIE_PASSWORD")
        
        # Authenticate with code
        # Note: authenticate_with_code doesn't take redirect_uri - it's inferred from the code
        session_config = None
        if cookie_password:
            # Try to import SessionConfig, fall back to dict if not available
            try:
                from workos.types.user_management.session import SessionConfig
                session_config = SessionConfig(
                    seal_session=True,
                    cookie_password=cookie_password,
                )
            except ImportError:
                # Fall back to dict format
                session_config = {
                    "seal_session": True,
                    "cookie_password": cookie_password,
                }
        
        auth_response = workos_client.user_management.authenticate_with_code(
            code=code,
            session=session_config,
        )
        
        # Extract token from response
        # WorkOS returns different structures depending on configuration
        token = None
        
        # Try to get access_token from response
        if hasattr(auth_response, 'access_token'):
            token = auth_response.access_token
        elif hasattr(auth_response, 'token'):
            token = auth_response.token
        elif hasattr(auth_response, 'user') and hasattr(auth_response.user, 'access_token'):
            token = auth_response.user.access_token
        
        # If we have a sealed session, we might need to extract token differently
        if not token and hasattr(auth_response, 'sealed_session'):
            # For sealed sessions, we need to load and authenticate to get token
            if cookie_password:
                session = workos_client.user_management.load_sealed_session(
                    sealed_session=auth_response.sealed_session,
                    cookie_password=cookie_password,
                )
                auth_result = session.authenticate()
                if auth_result.authenticated and hasattr(auth_result, 'access_token'):
                    token = auth_result.access_token
        
        return {
            "success": True,
            "token": token,
            "user": auth_response.user if hasattr(auth_response, 'user') else None,
            "sealed_session": auth_response.sealed_session if hasattr(auth_response, 'sealed_session') else None,
        }
    except Exception as e:
        print(f"❌ Failed to authenticate with code: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def start_local_server(port: int = 3000):
    """Start a simple HTTP server to receive OAuth callback."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    callback_code = None
    callback_error = None
    
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal callback_code, callback_error
            
            if self.path.startswith("/callback"):
                # Parse query parameters
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                
                if "code" in params:
                    callback_code = params["code"][0]
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body><h1>Authentication successful!</h1>"
                        b"<p>You can close this window.</p></body></html>"
                    )
                elif "error" in params:
                    callback_error = params["error"][0]
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        f"<html><body><h1>Authentication failed</h1>"
                        f"<p>Error: {callback_error}</p></body></html>".encode()
                    )
                else:
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>No code or error in callback</h1></body></html>")
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            pass  # Suppress server logs
    
    server = HTTPServer(("localhost", port), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    return server, lambda: callback_code, lambda: callback_error


def main():
    """Main function to get AuthKit token via OAuth."""
    workos_api_key = os.getenv("WORKOS_API_KEY")
    workos_client_id = os.getenv("WORKOS_CLIENT_ID")
    
    # Use WORKOS_REDIRECT_URI if set, otherwise try to construct from base_url,
    # or fall back to the default that should be in the WorkOS config
    redirect_uri = os.getenv("WORKOS_REDIRECT_URI")
    
    if not redirect_uri:
        # Try to construct from base_url (for MCP server)
        base_url = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL")
        if base_url:
            redirect_uri = f"{base_url.rstrip('/')}/api/mcp/auth/callback"
        else:
            # Use the default redirect URI from WorkOS config
            # Based on your config, the default is: http://localhost:3000/auth/callback
            redirect_uri = "http://localhost:3000/auth/callback"
    
    if not workos_api_key or not workos_client_id:
        print("❌ WORKOS_API_KEY and WORKOS_CLIENT_ID required")
        print("   Set them in your environment or .env file")
        return None
    
    print(f"🔐 Getting AuthKit token via OAuth flow")
    print(f"🔑 Client ID: {workos_client_id}")
    print(f"🌐 Redirect URI: {redirect_uri}")
    print()
    print("💡 Make sure this redirect URI is configured in your WorkOS dashboard:")
    print(f"   {redirect_uri}")
    print("   If not, set WORKOS_REDIRECT_URI to one of your configured URIs")
    print()
    
    # Initialize WorkOS client (requires both api_key and client_id)
    workos_client = WorkOS(api_key=workos_api_key, client_id=workos_client_id)
    
    # Get authorization URL
    print("Step 1: Getting authorization URL...")
    auth_url = get_authorization_url(workos_client, redirect_uri)
    
    if not auth_url:
        print("❌ Failed to get authorization URL")
        return None
    
    print(f"✅ Authorization URL: {auth_url}")
    print()
    
    # Parse redirect URI to get port
    parsed_redirect = urlparse(redirect_uri)
    port = parsed_redirect.port or 3000
    
    # Start local server to receive callback
    print(f"Step 2: Starting local server on port {port}...")
    server, get_code, get_error = start_local_server(port)
    print(f"✅ Local server started at {redirect_uri}")
    print()
    
    # Open browser
    print("Step 3: Opening browser for authentication...")
    print("   Please complete the OAuth flow in your browser")
    print()
    webbrowser.open(auth_url)
    
    # Wait for callback
    print("⏳ Waiting for OAuth callback...")
    import time
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        code = get_code()
        error = get_error()
        
        if code:
            print(f"✅ Received authorization code")
            server.shutdown()
            
            # Exchange code for token
            print()
            print("Step 4: Exchanging code for token...")
            result = authenticate_with_code(workos_client, code, redirect_uri)
            
            if result.get("success") and result.get("token"):
                token = result["token"]
                print(f"✅ Successfully authenticated!")
                print()
                print(f"Token (first 50 chars): {token[:50]}...")
                print()
                print(f"✅ Set this as your ATOMS_TEST_AUTH_TOKEN:")
                print(f"export ATOMS_TEST_AUTH_TOKEN=\"{token}\"")
                return token
            else:
                print(f"❌ Failed to get token: {result.get('error', 'Unknown error')}")
                return None
        
        if error:
            print(f"❌ OAuth error: {error}")
            server.shutdown()
            return None
        
        time.sleep(0.5)
    
    print("❌ Timeout waiting for OAuth callback")
    server.shutdown()
    return None


if __name__ == "__main__":
    token = main()
    if token:
        sys.exit(0)
    else:
        sys.exit(1)
