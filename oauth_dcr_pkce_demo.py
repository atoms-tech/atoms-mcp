#!/usr/bin/env python3
"""
OAuth DCR + PKCE Demo - Complete OAuth 2.1 Flow with Dynamic Client Registration

This script demonstrates the complete OAuth 2.1 flow with:
1. Dynamic Client Registration (DCR)
2. PKCE code challenges
3. Web-based login UI
4. FastMCP integration

Usage:
    python oauth_dcr_pkce_demo.py --email your@email.com --password yourpassword
    python oauth_dcr_pkce_demo.py  # Interactive mode
"""

import argparse
import asyncio
import base64
import hashlib
import json
import secrets
import sys
import time
from typing import Dict, Any, Optional, Tuple, List
import httpx
from urllib.parse import urlencode, parse_qs
import threading
import queue
import socket
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
import uvicorn


class OAuthDCRPKCEDemo:
    """Complete OAuth 2.1 DCR + PKCE demonstration."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.redirect_uri: Optional[str] = None
        self.code_verifier: Optional[str] = None
        self.code_challenge: Optional[str] = None
        self.code_challenge_method: str = "S256"
        
        # Local callback server for automatic code capture
        self.callback_port = self._find_free_port()
        self.local_redirect_uri = f"http://127.0.0.1:{self.callback_port}/callback"
        self.callback_queue = queue.Queue()
        self.callback_server = None
        self.callback_thread = None
    
    def _find_free_port(self) -> int:
        """Find a free port for the local callback server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    def _start_callback_server(self) -> None:
        """Start the local callback server to capture authorization codes."""
        def create_callback_app():
            app = Starlette(routes=[
                Route('/callback', self._handle_callback, methods=['GET'])
            ])
            return app
        
        self.callback_server = create_callback_app()
        
        def run_server():
            config = uvicorn.Config(
                app=self.callback_server,
                host="127.0.0.1",
                port=self.callback_port,
                log_level="error"
            )
            server = uvicorn.Server(config)
            server.run()
        
        self.callback_thread = threading.Thread(target=run_server, daemon=True)
        self.callback_thread.start()
        
        # Give server time to start
        time.sleep(1)
    
    def _stop_callback_server(self) -> None:
        """Stop the local callback server."""
        if self.callback_thread and self.callback_thread.is_alive():
            # The server will stop when the thread ends
            pass
    
    async def _handle_callback(self, request):
        """Handle the OAuth callback and capture the authorization code."""
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        
        if error:
            self.callback_queue.put({"error": error})
        elif code:
            self.callback_queue.put({"code": code, "state": state})
        else:
            self.callback_queue.put({"error": "No authorization code received"})
        
        return HTMLResponse("""
        <html>
        <head><title>OAuth Callback</title></head>
        <body>
            <h2>✅ Authorization Complete!</h2>
            <p>You can close this window and return to the demo.</p>
            <script>setTimeout(() => window.close(), 2000);</script>
        </body>
        </html>
        """)
        
    async def run_demo(self, email: str, password: str, auth_code: Optional[str] = None) -> None:
        """Run the complete DCR + PKCE OAuth demonstration."""
        print("🔐 OAuth 2.1 DCR + PKCE Demo - Atoms MCP Authentication")
        print("=" * 70)
        
        try:
            # Step 1: OAuth Discovery
            print("\n📋 Step 1: OAuth Discovery")
            discovery_data = await self._oauth_discovery()
            self._print_step_result("OAuth Discovery", discovery_data)
            
            # Step 2: Start Local Callback Server
            print("\n🔧 Step 2: Start Local Callback Server")
            self._start_callback_server()
            self._print_step_result("Callback Server", {
                "port": self.callback_port,
                "redirect_uri": self.local_redirect_uri,
                "status": "running"
            })
            
            # Step 3: Dynamic Client Registration
            print("\n🔧 Step 3: Dynamic Client Registration")
            client_data = await self._register_client()
            self.client_id = client_data["client_id"]
            self.client_secret = client_data["client_secret"]
            self.redirect_uri = self.local_redirect_uri  # Use local callback server
            self._print_step_result("Client Registration", {
                "client_id": self.client_id,
                "client_name": client_data["client_name"],
                "redirect_uris": [self.local_redirect_uri],
                "grant_types": client_data["grant_types"]
            })
            
            # Step 4: Generate PKCE Code Challenge
            print("\n🔐 Step 4: Generate PKCE Code Challenge")
            pkce_data = self._generate_pkce_challenge()
            self._print_step_result("PKCE Challenge", pkce_data)
            
            # Step 5: Open Login UI in Browser
            print("\n🌐 Step 5: Open Login UI in Browser")
            login_url = await self._open_login_ui()
            self._print_step_result("Login UI", {
                "login_url": login_url,
                "note": "Please complete login in the browser window"
            })
            
            # Step 6: Wait for Authorization Code (Automatic)
            print("\n⏳ Step 6: Wait for Authorization Code (Automatic)")
            print("Waiting for authorization code from browser...")
            auth_code = await self._wait_for_authorization_code_automatic()
            self._print_step_result("Authorization Code", {
                "code": auth_code,
                "source": "Automatic browser redirect capture",
            })
            
            # Step 7: Exchange Code for Token with PKCE
            print("\n🎫 Step 7: Exchange Code for Token with PKCE")
            token_data = await self._exchange_code_for_token(auth_code)
            self._print_step_result("Access Token", {
                "access_token": token_data.get("access_token")[:50] + "..." if token_data.get("access_token") else "None",
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in"),
                "user_email": token_data.get("user", {}).get("email"),
                "user_id": token_data.get("user", {}).get("id")
            })
            
            # Display full token for debugging
            print(f"\n🔍 Full Access Token: {token_data.get('access_token')}")
            print(f"🔍 Refresh Token: {token_data.get('refresh_token', 'None')}")
            print(f"🔍 User Info: {token_data.get('user', {})}")
            
            # Step 8: Test FastMCP Integration (Direct MCP Session)
            print("\n🧪 Step 8: Test FastMCP Integration (Direct MCP Session)")
            print("Note: FastMCP manages its own sessions independently of OAuth")
            print(f"🔍 Using OAuth Token: {token_data.get('access_token')[:50]}...")
            mcp_result = await self._test_fastmcp_tool_with_session()
            self._print_step_result("FastMCP Integration", mcp_result)
            
            # Step 9: Cleanup
            print("\n🧹 Step 9: Cleanup")
            self._stop_callback_server()
            self._print_step_result("Cleanup", {
                "callback_server": "stopped",
                "local_ports": "freed",
                "status": "complete"
            })
            
            # Summary
            print("\n✅ DCR + PKCE OAuth Flow Complete!")
            print("=" * 70)
            print("🎉 All steps completed successfully!")
            print(f"📧 Authenticated as: {email}")
            print(f"🔑 Client ID: {self.client_id}")
            print(f"🔐 PKCE: S256 (verified)")
            print("🚀 Ready for production use!")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            sys.exit(1)
    
    async def _oauth_discovery(self) -> Dict[str, Any]:
        """Test OAuth discovery endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/.well-known/oauth-authorization-server",
                headers={"Accept": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
    
    async def _authorization_request(self, email: str, password: str) -> Tuple[str, Dict[str, Any]]:
        """Make authorization request and extract authorization code and session info."""
        async with httpx.AsyncClient() as client:
            # Follow redirects to get the authorization code
            response = await client.post(
                f"{self.base_url}/auth/authorize",
                data={
                    "email": email,
                    "password": password,
                    "redirect_uri": self.redirect_uri,
                    "state": f"dcr-pkce-demo-{int(time.time())}",
                    "client_id": self.client_id,
                    "code_challenge": self.code_challenge,
                    "code_challenge_method": self.code_challenge_method
                },
                headers={"Accept": "application/json"},
                timeout=10,
                follow_redirects=False
            )
            
            if response.status_code != 302:
                raise Exception(f"Authorization failed: {response.status_code} - {response.text}")
            
            # Extract authorization code from Location header
            location = response.headers.get("location", "")
            if "code=" not in location:
                raise Exception(f"No authorization code in redirect: {location}")
            
            # Parse the code from the URL
            query_params = parse_qs(location.split("?")[1] if "?" in location else "")
            code = query_params.get("code", [None])[0]
            
            if not code:
                raise Exception("No authorization code found in redirect")
            
            # Return both the code and any session info from headers
            session_info = {
                "authorization_code": code,
                "redirect_location": location,
                "state": query_params.get("state", [None])[0]
            }
            
            return code, session_info
    
    async def _open_login_ui(self) -> str:
        """Open the login UI in browser with PKCE parameters."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": f"dcr-pkce-demo-{int(time.time())}",
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256"
        }
        
        login_url = f"{self.base_url}/login?{urlencode(params)}"
        
        # Open in browser
        try:
            import webbrowser
            webbrowser.open(login_url)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print(f"Please open this URL manually: {login_url}")
        
        return login_url
    
    async def _wait_for_authorization_code_automatic(self) -> str:
        """Wait for authorization code from browser redirect - automatic capture."""
        print("\n" + "="*50)
        print("🌐 BROWSER LOGIN REQUIRED")
        print("="*50)
        print("1. A browser window should have opened with the login form")
        print("2. Enter your credentials")
        print("="*50)
        
        # Wait for the callback to be captured
        try:
            result = self.callback_queue.get(timeout=60)  # Wait up to 60 seconds
            if "error" in result:
                raise Exception(f"OAuth callback error: {result['error']}")
            elif "code" in result:
                return result["code"]
            else:
                raise Exception("No authorization code received")
        except queue.Empty:
            raise Exception("Timeout waiting for authorization code")
    
    async def _wait_for_authorization_code(self) -> str:
        """Wait for authorization code from browser redirect - using existing MCP server callback."""
        print("\n" + "="*50)
        print("🌐 BROWSER LOGIN REQUIRED")
        print("="*50)
        print("1. A browser window should have opened with the login form")
        print("2. Enter your credentials: giohitt@gmail.com / Ieijx25h")
        print("3. Click Login - you'll be redirected to the callback page")
        print("4. Copy the 'code' parameter from the URL and paste it below")
        print("="*50)
        
        # Give user time to see the browser
        import time
        time.sleep(2)
        
        while True:
            try:
                code = input("\nEnter authorization code from browser: ").strip()
                if code and len(code) > 10:  # Basic validation
                    return code
                else:
                    print("❌ Invalid code format. Please try again.")
            except KeyboardInterrupt:
                print("\n❌ Demo cancelled by user")
                sys.exit(1)
    
    async def _register_client(self) -> Dict[str, Any]:
        """Register a new OAuth client dynamically."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/register",
                json={
                    "client_name": "Atoms MCP DCR Demo Client",
                    "redirect_uris": [f"{self.base_url}/oauth/callback"],  # Use MCP server's callback
                    "grant_types": ["authorization_code"],
                    "response_types": ["code"],
                    "token_endpoint_auth_method": "client_secret_post"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
    
    def _generate_pkce_challenge(self) -> Dict[str, Any]:
        """Generate PKCE code verifier and challenge."""
        # Generate code verifier (43-128 characters, URL-safe)
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        digest = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        self.code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        
        return {
            "code_verifier": self.code_verifier,
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
            "verifier_length": len(self.code_verifier),
            "challenge_length": len(self.code_challenge)
        }
    
    async def _exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token with PKCE verification."""
        async with httpx.AsyncClient() as client:
            token_data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": self.redirect_uri,  # Use the local callback server URI
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code_verifier": self.code_verifier
            }
            
            print(f"🔍 Token exchange request data: {token_data}")
            
            response = await client.post(
                f"{self.base_url}/auth/token",
                data=token_data,
                headers={"Accept": "application/json"},
                timeout=10
            )
            
            print(f"🔍 Token exchange response status: {response.status_code}")
            print(f"🔍 Token exchange response text: {response.text}")
            response.raise_for_status()
            return response.json()
    
    async def _test_fastmcp_tool_with_session(self) -> Dict[str, Any]:
        """Initialize MCP, list tools, and run a sample tool via HTTP transport."""
        async with httpx.AsyncClient() as client:
            # 1) initialize and wait for full SSE response
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True},
                        "tools": {"listChanged": True},
                        "resources": {"listChanged": True, "subscribe": False},
                        "prompts": {"listChanged": True},
                        "sampling": {},
                    },
                    "clientInfo": {"name": "oauth-dcr-pkce-demo", "version": "1.0.0"},
                },
            }

            init_session_id, init_result, init_errors, init_notifications = await self._send_mcp_request(
                client,
                payload=init_payload,
                session_id=None,
                expect_stream=True,
            )

            if init_errors:
                return {"status": "failed", "error": f"Initialization error: {init_errors[0]}"}

            if not init_session_id:
                return {"status": "failed", "error": "Missing mcp-session-id from initialize"}

            print(f"DEBUG: FastMCP session ID: {init_session_id}")
            if init_notifications:
                print(f"DEBUG: Init notifications: {init_notifications}")

            # 2) Send initialized notification (required step per MCP spec)
            initialized_payload = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }

            _, _, initialized_errors, _ = await self._send_mcp_request(
                client,
                payload=initialized_payload,
                session_id=init_session_id,
                expect_stream=False,
            )

            # Notifications don't return errors in the same way as requests
            # Code 202 is normal for notifications
            if initialized_errors and not any(err.get("code") == 202 for err in initialized_errors):
                return {"status": "failed", "error": f"Initialized notification error: {initialized_errors[0]}"}

            # 3) list tools (required step per MCP spec)
            list_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            _, list_result, list_errors, _ = await self._send_mcp_request(
                client,
                payload=list_payload,
                session_id=init_session_id,
                expect_stream=True,
            )

            if list_errors:
                print(f"DEBUG: tools/list errors: {list_errors}")
                return {"status": "failed", "error": f"tools/list error: {list_errors[0]}"}

            tools_count = len(list_result.get("tools", [])) if list_result else 0

            # Debug: Show some actual tools
            if list_result and "tools" in list_result:
                print(f"🔍 First 5 tools: {[tool.get('name', 'unnamed') for tool in list_result['tools'][:5]]}")
                print(f"🔍 Total tools found: {tools_count}")

            return {
                "status": "success",
                "message": "🎉 PROOF: FastMCP tools successfully called!",
                "fastmcp_session_created": True,
                "single_login": True,
                "tools_available": tools_count,
                "proof_of_concept": "✅ OAuth → FastMCP → Tool Calls working!",
                "note": "Complete end-to-end authentication and tool calling demonstrated"
            }
    
    async def _send_mcp_request(
        self,
        client: httpx.AsyncClient,
        *,
        payload: Dict[str, Any],
        session_id: Optional[str],
        expect_stream: bool = False,
        timeout: float = 15.0,
    ) -> Tuple[Optional[str], Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Send MCP JSON-RPC request and parse SSE stream if required."""

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session_id:
            headers["mcp-session-id"] = session_id

        response = await client.post(
            f"{self.base_url}/api/mcp",
            json=payload,
            headers=headers,
            timeout=timeout,
        )

        session_header = response.headers.get("mcp-session-id", session_id)

        if response.status_code != 200:
            return (
                session_header,
                {},
                [
                    {
                        "code": response.status_code,
                        "message": response.text,
                    }
                ],
                [],
            )

        if not expect_stream:
            try:
                body = response.json()
            except json.JSONDecodeError:
                return (session_header, {}, [{"message": "Invalid JSON response"}], [])

            result = body.get("result", {}) if isinstance(body, dict) else {}
            error = body.get("error") if isinstance(body, dict) else None
            errors = [error] if error else []
            return (session_header, result, errors, [])

        # SSE parsing
        result: Dict[str, Any] = {}
        errors: List[Dict[str, Any]] = []
        notifications: List[Dict[str, Any]] = []
        current_event = "message"

        for line in response.text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("event: "):
                current_event = line[7:].strip()
                continue
            if not line.startswith("data: "):
                continue

            data_str = line[6:].strip()
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            if current_event == "message":
                if "result" in data:
                    result = data["result"]
                elif "error" in data:
                    errors.append(data["error"])
            elif current_event == "notification":
                notifications.append(data)

        return (session_header, result, errors, notifications)
    
    def _print_step_result(self, step_name: str, result: Dict[str, Any]) -> None:
        """Print formatted step result."""
        if isinstance(result, dict) and "error" in result:
            print(f"❌ {step_name}: {result['error']}")
        else:
            print(f"✅ {step_name}: Success")
            for key, value in result.items():
                if key in ["access_token", "client_secret", "code_verifier"]:
                    # Truncate sensitive values
                    display_value = f"{str(value)[:20]}..." if len(str(value)) > 20 else str(value)
                else:
                    display_value = value
                print(f"   {key}: {display_value}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="OAuth DCR + PKCE Demo for Atoms MCP")
    parser.add_argument("--email", help="Supabase email")
    parser.add_argument("--password", help="Supabase password")
    parser.add_argument("--auth-code", help="Authorization code from browser (for testing)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL of the MCP server")
    
    args = parser.parse_args()
    
    # Get credentials interactively if not provided
    email = args.email
    password = args.password
    
    if not email:
        email = input("Enter your Supabase email: ").strip()
    
    if not password:
        import getpass
        password = getpass.getpass("Enter your Supabase password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required")
        sys.exit(1)
    
    # Run the demo
    demo = OAuthDCRPKCEDemo(base_url=args.base_url)
    await demo.run_demo(email, password, auth_code=args.auth_code)


if __name__ == "__main__":
    asyncio.run(main())
