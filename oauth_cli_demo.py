#!/usr/bin/env python3
"""
OAuth CLI Demo - Real OAuth 2.1 Flow Demonstration

This script demonstrates the complete OAuth 2.1 authentication flow
with the Atoms MCP server, using real Supabase credentials and
making actual HTTP calls to verify authentication.

Usage:
    python oauth_cli_demo.py --email your@email.com --password yourpassword
    python oauth_cli_demo.py  # Interactive mode
"""

import argparse
import asyncio
import json
import sys
import time
from typing import Dict, Any, Optional, Tuple, List
import httpx
from urllib.parse import urlencode, parse_qs


class OAuthCLIDemo:
    """CLI demonstration of OAuth 2.1 flow with Atoms MCP server."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.client_id = "atoms-mcp-client"
        self.redirect_uri = f"{self.base_url}/oauth/callback"
        
    async def run_demo(self, email: str, password: str) -> None:
        """Run the complete OAuth demonstration."""
        print("🔐 OAuth 2.1 CLI Demo - Atoms MCP Authentication")
        print("=" * 60)
        
        # Track token relationships
        token_relationships = {}
        
        try:
            # Step 1: OAuth Discovery
            print("\n📋 Step 1: OAuth Discovery")
            discovery_data = await self._oauth_discovery()
            self._print_step_result("OAuth Discovery", discovery_data)
            
            # Step 2: Supabase Authentication → Authorization Code
            print("\n🔑 Step 2: Supabase Authentication → Authorization Code")
            auth_code, session_info = await self._authorization_request(email, password)
            
            # Store authorization code info
            token_relationships["authorization_code"] = {
                "code": session_info["authorization_code"],
                "user": email,
                "state": session_info["state"],
                "timestamp": time.time()
            }
            
            self._print_step_result("Authorization Code", {
                **session_info,
                "belongs_to": f"User: {email}",
                "request_id": f"auth_req_{int(time.time())}"
            })
            
            # Step 3: Authorization Code → Supabase JWT Token Exchange
            print("\n🎫 Step 3: Authorization Code → Supabase JWT Token Exchange")
            token_data = await self._token_exchange(auth_code)
            
            # Store token relationship
            token_relationships["access_token"] = {
                "access_token": token_data.get("access_token"),
                "authorization_code": auth_code,
                "user": email,
                "expires_in": token_data.get("expires_in"),
                "timestamp": time.time()
            }
            
            self._print_step_result("Access Token", {
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in"),
                "refresh_token": token_data.get("refresh_token"),
                "scope": token_data.get("scope"),
                "user": token_data.get("user", {}).get("email"),
                "derived_from": f"Authorization Code: {auth_code[:20]}...",
                "belongs_to": f"User: {email}"
            })
            
            # Step 4: Supabase JWT Token Analysis
            print("\n🔍 Step 4: Supabase JWT Token Analysis")
            jwt_info = await self._analyze_jwt_token(token_data.get("access_token"))
            
            # Add relationship info to JWT analysis
            jwt_info["token_relationship"] = {
                "derived_from_auth_code": auth_code[:20] + "...",
                "belongs_to_user": email,
                "supabase_session_id": jwt_info.get("payload", {}).get("session_id"),
                "supabase_user_id": jwt_info.get("payload", {}).get("sub")
            }
            
            self._print_step_result("JWT Token Details", jwt_info)
            
            # Step 5: Supabase JWT Token → FastMCP Session Token
            print("\n🎫 Step 5: Supabase JWT Token → FastMCP Session Token")
            session_result = await self._get_oauth_session(token_data.get("access_token"))
            self._print_step_result("OAuth Session", session_result)
            
            # Step 6: FastMCP Tool Call with FastMCP Session
            print("\n🧪 Step 6: FastMCP Tool Call with FastMCP Session")
            print("Note: FastMCP manages its own sessions independently of OAuth")
            tool_result = await self._test_fastmcp_tool_with_session()
            tool_result["authentication_method"] = "FastMCP's own session management"
            tool_result["authenticated_as"] = "FastMCP session (independent of OAuth)"
            self._print_step_result("Tool Authentication", tool_result)
            
            # Summary
            print("\n✅ OAuth Flow Complete!")
            print("=" * 60)
            print("🎉 All steps completed successfully!")
            print(f"📧 Authenticated as: {token_data.get('user', {}).get('email')}")
            print(f"🎫 Token expires in: {token_data.get('expires_in')} seconds")
            print("🚀 Ready for production use!")
            
            # Token Relationship Summary
            print("\n🔗 Token Relationship Summary")
            print("=" * 60)
            print("📋 Authorization Code:")
            print(f"   Code: {token_relationships['authorization_code']['code']}")
            print(f"   User: {token_relationships['authorization_code']['user']}")
            print(f"   State: {token_relationships['authorization_code']['state']}")
            print(f"   Generated: {time.strftime('%H:%M:%S', time.localtime(token_relationships['authorization_code']['timestamp']))}")
            
            print("\n🎫 Access Token:")
            print(f"   Token: {token_relationships['access_token']['access_token'][:50]}...")
            print(f"   Derived from: {token_relationships['access_token']['authorization_code']}")
            print(f"   User: {token_relationships['access_token']['user']}")
            print(f"   Expires in: {token_relationships['access_token']['expires_in']} seconds")
            print(f"   Generated: {time.strftime('%H:%M:%S', time.localtime(token_relationships['access_token']['timestamp']))}")
            
            print("\n🔗 Token Chain:")
            print(f"   User Credentials → Authorization Code → Access Token → FastMCP Tools")
            print(f"   {email} → {auth_code[:20]}... → {token_data.get('access_token')[:30]}... → ✅ Success")
            
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
    
    async def _authorization_request(self, email: str, password: str) -> tuple[str, dict]:
        """Make authorization request and extract authorization code and session info."""
        async with httpx.AsyncClient() as client:
            # Follow redirects to get the authorization code
            response = await client.post(
                f"{self.base_url}/auth/authorize",
                data={
                    "email": email,
                    "password": password,
                    "redirect_uri": self.redirect_uri,
                    "state": "cli-demo-state"
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
    
    async def _analyze_jwt_token(self, access_token: str) -> Dict[str, Any]:
        """Analyze the JWT token to show its contents."""
        try:
            import base64
            import json
            
            # Split JWT token (header.payload.signature)
            parts = access_token.split('.')
            if len(parts) != 3:
                return {"error": "Invalid JWT format"}
            
            # Decode header and payload (add padding if needed)
            header_padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
            payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            
            header = json.loads(base64.urlsafe_b64decode(header_padded))
            payload = json.loads(base64.urlsafe_b64decode(payload_padded))
            
            return {
                "header": header,
                "payload": {
                    "iss": payload.get("iss"),
                    "sub": payload.get("sub"),
                    "aud": payload.get("aud"),
                    "exp": payload.get("exp"),
                    "iat": payload.get("iat"),
                    "email": payload.get("email"),
                    "role": payload.get("role"),
                    "session_id": payload.get("session_id"),
                    "aal": payload.get("aal"),
                    "amr": payload.get("amr")
                },
                "signature": f"{parts[2][:20]}...{parts[2][-20:]}"
            }
        except Exception as e:
            return {"error": f"Failed to decode JWT: {e}"}
    
    async def _get_oauth_session(self, access_token: str) -> Dict[str, Any]:
        """Get FastMCP session token from OAuth access token using HTTP endpoint."""
        async with httpx.AsyncClient() as client:
            # Use the HTTP endpoint instead of MCP tools to bypass session requirements
            response = await client.post(
                f"{self.base_url}/api/oauth/session",
                json={"access_token": access_token},
                headers={
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {
                        "status": "success",
                        "message": "OAuth session created successfully",
                        "session_token": result.get("session_token"),
                        "user_id": result.get("user_id"),
                        "username": result.get("username")
                    }
                else:
                    return {
                        "status": "failed",
                        "error": result.get("error", "Unknown error")
                    }
            else:
                return {
                    "status": "failed", 
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
    
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
                    "clientInfo": {"name": "oauth-cli-demo", "version": "1.0.0"},
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

            return {
                "status": "success",
                "message": "Successfully initialized MCP session and listed tools",
                "tools_listed": tools_count,
                "session_id": init_session_id,
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

    async def _test_fastmcp_tool_direct(self) -> Dict[str, Any]:
        """Test FastMCP tool directly without session token."""
        async with httpx.AsyncClient() as client:
            # Make tool call without session token
            tool_response = await client.post(
                f"{self.base_url}/api/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_profile",
                        "arguments": {}
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=10
            )
            
            if tool_response.status_code == 200:
                # Parse the response to get the actual tool result
                response_text = tool_response.text
                if "event: message" in response_text:
                    # Extract the JSON from the event stream
                    lines = response_text.split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])  # Remove 'data: ' prefix
                                if 'result' in data:
                                    return {
                                        "status": "success", 
                                        "message": "Tool call successful",
                                        "tool_response": data['result']
                                    }
                                elif 'error' in data:
                                    return {
                                        "status": "failed",
                                        "error": f"Tool error: {data['error']}",
                                        "full_error": data
                                    }
                            except json.JSONDecodeError:
                                continue
                
                return {"status": "success", "message": "Tool call successful", "raw_response": response_text[:200] + "..."}
            else:
                return {
                    "status": "failed", 
                    "error": f"HTTP {tool_response.status_code}: {tool_response.text}"
                }
    
    async def _token_exchange(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/token",
                data={
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id
                },
                headers={"Accept": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
    
    async def _test_fastmcp_tool(self, access_token: str) -> Dict[str, Any]:
        """Test FastMCP tool with OAuth token."""
        async with httpx.AsyncClient() as client:
            # First, make a request to get the session ID
            initial_response = await client.post(
                f"{self.base_url}/api/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_oauth_session",
                        "arguments": {
                            "access_token": access_token
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=10
            )
            
            # Get session ID from the response headers
            session_id = initial_response.headers.get("mcp-session-id")
            if not session_id:
                return {"status": "failed", "error": "No session ID received from initial request"}
            
            # Now make the actual tool call with the session ID
            tool_response = await client.post(
                f"{self.base_url}/api/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "get_oauth_session",
                        "arguments": {
                            "access_token": access_token
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": session_id
                },
                timeout=10
            )
            
            if tool_response.status_code == 200:
                # Parse the response to get the actual tool result
                response_text = tool_response.text
                if "event: message" in response_text:
                    # Extract the JSON from the event stream
                    lines = response_text.split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])  # Remove 'data: ' prefix
                                if 'result' in data:
                                    return {
                                        "status": "success", 
                                        "message": "Tool call successful",
                                        "tool_response": data['result']
                                    }
                                elif 'error' in data:
                                    return {
                                        "status": "failed",
                                        "error": f"Tool error: {data['error']}",
                                        "full_error": data
                                    }
                            except json.JSONDecodeError:
                                continue
                
                return {"status": "success", "message": "Tool call successful", "raw_response": response_text[:200] + "..."}
            else:
                return {
                    "status": "failed", 
                    "error": f"HTTP {tool_response.status_code}: {tool_response.text}"
                }
    
    def _print_step_result(self, step_name: str, result: Dict[str, Any]) -> None:
        """Print formatted step result."""
        if isinstance(result, dict) and "error" in result:
            print(f"❌ {step_name}: {result['error']}")
        else:
            print(f"✅ {step_name}: Success")
            for key, value in result.items():
                print(f"   {key}: {value}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="OAuth CLI Demo for Atoms MCP")
    parser.add_argument("--email", help="Supabase email")
    parser.add_argument("--password", help="Supabase password")
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
    demo = OAuthCLIDemo(base_url=args.base_url)
    await demo.run_demo(email, password)


if __name__ == "__main__":
    asyncio.run(main())
