#!/usr/bin/env python3
"""Automated OAuth login using Playwright.

This module handles the AuthKit OAuth flow automatically by:
1. Starting a local callback server
2. Opening the OAuth URL in Playwright
3. Automating the login form
4. Capturing the OAuth callback
5. Extracting the session token
"""

import asyncio
from typing import Optional
import http.server
import socketserver
import urllib.parse
from threading import Thread
import queue
import time


async def automated_oauth_login(
    oauth_url: str,
    email: str,
    password: str,
    callback_port: int = 0
) -> Optional[str]:
    """Automate OAuth login flow using Playwright.

    Args:
        oauth_url: The OAuth authorization URL
        email: User email for login
        password: User password for login
        callback_port: Port for callback server (0 = random)

    Returns:
        Access token or session_id from OAuth callback
    """
    from mcp__playwright__browser_navigate import browser_navigate
    from mcp__playwright__browser_snapshot import browser_snapshot
    from mcp__playwright__browser_click import browser_click
    from mcp__playwright__browser_type import browser_type
    from mcp__playwright__browser_close import browser_close

    # Queue to receive token from callback
    token_queue = queue.Queue()

    # Simple HTTP server to capture OAuth callback
    class CallbackHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)

            if "/callback" in parsed.path or "/oauth-complete" in parsed.path:
                query = urllib.parse.parse_qs(parsed.query)

                # Extract token/session_id from query params
                token = (
                    query.get("access_token", [None])[0] or
                    query.get("session_id", [None])[0] or
                    query.get("code", [None])[0]
                )

                # Also check cookies
                if not token:
                    cookie_header = self.headers.get("Cookie", "")
                    for cookie in cookie_header.split(";"):
                        cookie = cookie.strip()
                        if "=" in cookie:
                            key, value = cookie.split("=", 1)
                            if key in ["mcp_session_id", "access_token"]:
                                token = value
                                break

                if token:
                    token_queue.put(token)
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                        <html><body>
                        <h1>Authentication Successful!</h1>
                        <p>You can close this window.</p>
                        <script>window.close();</script>
                        </body></html>
                    """)
                else:
                    # Store the full URL for debugging
                    token_queue.put(f"ERROR:No token in {self.path}")
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                        <html><body>
                        <h1>Authentication Complete</h1>
                        <p>Checking for token...</p>
                        </body></html>
                    """)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress logs

    # Start callback server
    with socketserver.TCPServer(("", callback_port), CallbackHandler) as httpd:
        actual_port = httpd.server_address[1]
        callback_url = f"http://localhost:{actual_port}/callback"

        print(f"🎧 Started callback server on port {actual_port}")

        # Start server in background
        server_thread = Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        try:
            # Add callback URL to OAuth URL
            if "?" in oauth_url:
                full_url = f"{oauth_url}&redirect_uri={urllib.parse.quote(callback_url)}"
            else:
                full_url = f"{oauth_url}?redirect_uri={urllib.parse.quote(callback_url)}"

            print(f"🌐 Navigating to OAuth URL with Playwright...")

            # Navigate to OAuth URL
            await browser_navigate(url=full_url)
            await asyncio.sleep(2)  # Wait for page load

            # Take snapshot to see what's on the page
            snapshot = await browser_snapshot()
            print(f"📸 Page snapshot captured")

            # Look for email input field
            print(f"🔍 Looking for login form...")

            # Type email
            # Note: You'll need to adjust these selectors based on actual AuthKit form
            try:
                await browser_type(
                    element="email input field",
                    ref="input[type='email'], input[name='email'], #email",
                    text=email
                )
                print(f"✅ Entered email")
            except Exception as e:
                print(f"⚠️  Could not find email field: {e}")

            # Type password
            try:
                await browser_type(
                    element="password input field",
                    ref="input[type='password'], input[name='password'], #password",
                    text=password,
                    submit=True  # Submit the form
                )
                print(f"✅ Entered password and submitted")
            except Exception as e:
                print(f"⚠️  Could not find password field: {e}")

            # Wait for callback
            print(f"⏳ Waiting for OAuth callback...")

            token = None
            for i in range(30):  # Wait up to 30 seconds
                try:
                    token = token_queue.get(timeout=1)
                    break
                except queue.Empty:
                    if i % 5 == 0:
                        print(f"   Still waiting... ({i}s)")
                    continue

            if token and not token.startswith("ERROR:"):
                print(f"✅ Received token: {token[:20]}...")
                await browser_close()
                return token
            else:
                print(f"❌ No token received: {token}")
                print(f"📸 Taking final screenshot...")
                await browser_snapshot()
                await browser_close()
                return None

        finally:
            httpd.shutdown()


async def get_oauth_token_automated(
    mcp_endpoint: str,
    email: str,
    password: str
) -> Optional[str]:
    """Get OAuth token using automated Playwright login.

    Args:
        mcp_endpoint: MCP server endpoint
        email: User email
        password: User password

    Returns:
        OAuth access token or session_id
    """
    # Construct OAuth start URL
    oauth_url = f"{mcp_endpoint}/auth/start"

    print(f"\n🤖 Starting automated OAuth flow...")
    print(f"📧 Email: {email}")
    print(f"🔗 OAuth URL: {oauth_url}")

    token = await automated_oauth_login(oauth_url, email, password)

    return token
