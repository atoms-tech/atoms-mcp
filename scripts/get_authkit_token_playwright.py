#!/usr/bin/env python3
"""Get AuthKit JWT token via automated Playwright OAuth flow.

This script automates the WorkOS AuthKit OAuth flow using Playwright:
1. Opens the authorization URL
2. Fills in email/password credentials
3. Completes the OAuth flow
4. Extracts the JWT token from the callback

Usage:
    python scripts/get_authkit_token_playwright.py
    
    Or with custom credentials:
    ATOMS_TEST_EMAIL=your@email.com ATOMS_TEST_PASSWORD=yourpass python scripts/get_authkit_token_playwright.py

Environment variables:
    - WORKOS_API_KEY (required)
    - WORKOS_CLIENT_ID (required)
    - FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN (required)
    - FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL (required, for callback)
    - ATOMS_TEST_EMAIL (default: kooshapari@kooshapari.com)
    - ATOMS_TEST_PASSWORD (default: ASD3on54_Pax90)
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

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
        pass  # python-dotenv not available


async def get_authkit_token_via_playwright():
    """Get AuthKit JWT token by automating OAuth flow with Playwright."""
    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")
    workos_client_id = os.getenv("WORKOS_CLIENT_ID")
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
    base_url = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL")
    
    if not workos_client_id:
        print("❌ WORKOS_CLIENT_ID required")
        return None
    
    if not authkit_domain:
        print("❌ FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN required")
        return None
    
    if not base_url:
        print("❌ FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL required")
        print("   This is used as the redirect_uri for OAuth callback")
        return None
    
    # Check if Playwright is installed
    try:
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    except ImportError:
        print("❌ Playwright not installed")
        print("   Install with: pip install playwright")
        print("   Then run: playwright install chromium")
        return None
    
    print(f"🔐 Authenticating as: {email}")
    print(f"🔑 Client ID: {workos_client_id}")
    print(f"🌐 AuthKit Domain: {authkit_domain}")
    print(f"🔗 Base URL: {base_url}")
    print()
    
    # Construct authorization URL using WorkOS SDK (same as OAuth script)
    redirect_uri = f"{base_url.rstrip('/')}/api/mcp/auth/callback"
    
    # Use WorkOS SDK to get the correct authorization URL
    try:
        from workos import WorkOSClient
        workos_api_key = os.getenv("WORKOS_API_KEY")
        if not workos_api_key:
            print("❌ WORKOS_API_KEY required for getting authorization URL")
            return None
        
        workos_client = WorkOSClient(api_key=workos_api_key, client_id=workos_client_id)
        
        # Use WorkOS SDK's method to get authorization URL (same as OAuth script)
        try:
            full_auth_url = workos_client.user_management.get_authorization_url(
                provider="authkit",
                redirect_uri=redirect_uri,
            )
            print(f"✅ Got authorization URL from WorkOS SDK")
        except Exception as e:
            print(f"⚠️  WorkOS SDK method failed: {e}")
            print(f"   Falling back to manual URL construction...")
            # Fallback to manual construction
            auth_url = f"{authkit_domain.rstrip('/')}/authorize"
            from urllib.parse import urlencode
            auth_params = {
                "client_id": workos_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
            }
            full_auth_url = f"{auth_url}?{urlencode(auth_params)}"
    except ImportError:
        print("⚠️  WorkOS SDK not available, using manual URL construction...")
        # Fallback to manual construction
        auth_url = f"{authkit_domain.rstrip('/')}/authorize"
        from urllib.parse import urlencode
        auth_params = {
            "client_id": workos_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
        }
        full_auth_url = f"{auth_url}?{urlencode(auth_params)}"
    
    print(f"📋 OAuth Configuration:")
    print(f"   Redirect URI: {redirect_uri}")
    print(f"   Full Authorization URL: {full_auth_url}")
    print()
    
    token = None
    error_message = None
    
    async with async_playwright() as p:
        print("🌐 Launching browser (headless mode)...")
        # Use headless mode for automation (set HEADLESS=false to show browser)
        headless = os.getenv("HEADLESS", "true").lower() != "false"
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Intercept network requests to capture the token
            captured_token = None
            captured_error = None
            
            async def handle_response(response):
                nonlocal captured_token, captured_error
                
                # Check if this is the callback response
                if redirect_uri in response.url or "/callback" in response.url:
                    try:
                        # Try to get token from response body
                        body = await response.text()
                        if body:
                            # Try to parse as JSON
                            try:
                                data = json.loads(body)
                                if "access_token" in data:
                                    captured_token = data["access_token"]
                                elif "token" in data:
                                    captured_token = data["token"]
                            except json.JSONDecodeError:
                                # Not JSON, check URL params
                                pass
                        
                        # Check URL parameters
                        parsed = urlparse(response.url)
                        params = parse_qs(parsed.query)
                        if "access_token" in params:
                            captured_token = params["access_token"][0]
                        elif "token" in params:
                            captured_token = params["token"][0]
                        elif "code" in params:
                            # We got an authorization code, need to exchange it
                            code = params["code"][0]
                            print(f"✅ Got authorization code: {code[:20]}...")
                            # Exchange code for token (if we can)
                            captured_token = f"code:{code}"  # Mark as code for exchange
                    except Exception as e:
                        print(f"⚠️  Error processing callback: {e}")
                
                # Check for error responses
                if response.status >= 400:
                    try:
                        body = await response.text()
                        if "error" in body.lower():
                            captured_error = body
                    except:
                        pass
            
            page.on("response", handle_response)
            
            print(f"🔗 Navigating to authorization URL...")
            await page.goto(full_auth_url, wait_until="networkidle", timeout=30000)
            
            # Wait a bit for page to load
            await asyncio.sleep(2)
            
            print(f"📝 Looking for login form...")
            
            # Step 1: Find and fill email field
            print(f"📧 Step 1: Entering email...")
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[id*="email"]',
                'input[placeholder*="email" i]',
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = await page.wait_for_selector(selector, timeout=10000)
                    if email_field:
                        break
                except:
                    continue
            
            if not email_field:
                # Take screenshot for debugging
                await page.screenshot(path="authkit_login_debug.png")
                print("❌ Could not find email field")
                print("   Screenshot saved to: authkit_login_debug.png")
                print(f"   Page title: {await page.title()}")
                print(f"   Page URL: {page.url}")
                await browser.close()
                return None
            
            print(f"✅ Found email field, entering email...")
            await email_field.fill(email)
            await asyncio.sleep(0.5)  # Brief pause after typing
            
            # Step 2: Find and click "Continue" button (AuthKit two-step flow)
            print(f"➡️  Step 2: Clicking Continue...")
            continue_selectors = [
                'button:has-text("Continue")',
                'button:has-text("continue")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Next")',
                'button:has-text("next")',
            ]
            
            continue_button = None
            for selector in continue_selectors:
                try:
                    continue_button = await page.wait_for_selector(selector, timeout=5000)
                    if continue_button:
                        break
                except:
                    continue
            
            if not continue_button:
                print("⚠️  Could not find Continue button, trying to find password field directly...")
                # Maybe it's a single-step form, try password field
            else:
                print(f"✅ Found Continue button, clicking...")
                await continue_button.click()
                
                # Wait for password field to appear (page transition)
                print(f"⏳ Waiting for password field to appear...")
                await asyncio.sleep(2)
            
            # Step 3: Find and fill password field
            print(f"🔑 Step 3: Entering password...")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id*="password"]',
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await page.wait_for_selector(selector, timeout=10000)
                    if password_field:
                        break
                except:
                    continue
            
            if not password_field:
                # Take screenshot for debugging
                await page.screenshot(path="authkit_password_debug.png")
                print("❌ Could not find password field")
                print("   Screenshot saved to: authkit_password_debug.png")
                print(f"   Page title: {await page.title()}")
                print(f"   Page URL: {page.url}")
                await browser.close()
                return None
            
            print(f"✅ Found password field, entering password...")
            await password_field.fill(password)
            await asyncio.sleep(0.5)  # Brief pause after typing
            
            # Step 4: Find and click submit/sign in button
            print(f"🔐 Step 4: Submitting login...")
            submit_selectors = [
                'button:has-text("Sign in")',
                'button:has-text("sign in")',
                'button:has-text("Log in")',
                'button:has-text("log in")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Continue")',  # Some flows use Continue for password too
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = await page.wait_for_selector(selector, timeout=5000)
                    if submit_button:
                        break
                except:
                    continue
            
            if not submit_button:
                print("⚠️  Could not find submit button, trying Enter key...")
                await password_field.press("Enter")
            else:
                print(f"✅ Found submit button, clicking...")
                await submit_button.click()
            
            # Wait for navigation/redirect
            print(f"⏳ Waiting for OAuth callback...")
            
            # Check if we hit radar challenge (bot detection)
            current_url = page.url
            if "radar-challenge" in current_url.lower():
                print(f"🛡️  Detected radar challenge (bot detection), waiting for completion...")
                print(f"   Current URL: {current_url[:100]}...")
                
                # Wait for radar challenge to complete (usually auto-completes in 2-5 seconds)
                try:
                    # Wait for URL to change away from radar-challenge
                    await page.wait_for_url(
                        lambda url: "radar-challenge" not in url.lower(),
                        timeout=15000  # Give it up to 15 seconds
                    )
                    print(f"✅ Radar challenge completed, continuing...")
                    # Give it a moment to process
                    await asyncio.sleep(1)
                except PlaywrightTimeoutError:
                    print(f"⚠️  Radar challenge taking longer than expected, continuing anyway...")
                    # Continue - sometimes it redirects even if we timeout
            
            try:
                # Wait for redirect to callback URL or for token in response
                await page.wait_for_url(
                    lambda url: (
                        redirect_uri in url or 
                        "/callback" in url or 
                        "code=" in url or 
                        "access_token=" in url or
                        "pending_authentication_token" in url  # Radar challenge might have this
                    ),
                    timeout=30000
                )
                
                # If we're still on radar-challenge with pending_authentication_token, extract it
                current_url = page.url
                if "pending_authentication_token" in current_url and "radar-challenge" in current_url:
                    print(f"📋 Found pending_authentication_token in radar challenge URL")
                    # Extract the token from URL
                    parsed = urlparse(current_url)
                    params = parse_qs(parsed.query)
                    if "pending_authentication_token" in params:
                        pending_token = params["pending_authentication_token"][0]
                        print(f"   Extracted pending token: {pending_token[:20]}...")
                        # Wait a bit more for redirect
                        await asyncio.sleep(3)
                        # Check if we've been redirected
                        current_url = page.url
                        if "radar-challenge" not in current_url.lower():
                            print(f"✅ Redirected away from radar challenge")
                        else:
                            print(f"⚠️  Still on radar challenge, may need manual intervention")
            except PlaywrightTimeoutError:
                # Check if we're on a different page (might have redirected)
                current_url = page.url
                print(f"⚠️  Timeout waiting for callback. Current URL: {current_url}")
                
                # Check if we're on an error page
                if "error" in current_url.lower():
                    error_message = f"OAuth error in URL: {current_url}"
                    print(f"❌ {error_message}")
                elif "radar-challenge" in current_url.lower():
                    print(f"⚠️  Still on radar challenge page")
                    print(f"   This may require manual intervention or longer wait time")
                    # Try waiting a bit more
                    await asyncio.sleep(5)
                    current_url = page.url
                    if "radar-challenge" not in current_url.lower():
                        print(f"✅ Radar challenge completed after additional wait")
                    else:
                        # Take screenshot
                        await page.screenshot(path="authkit_callback_debug.png")
                        print("   Screenshot saved to: authkit_callback_debug.png")
                else:
                    # Take screenshot
                    await page.screenshot(path="authkit_callback_debug.png")
                    print("   Screenshot saved to: authkit_callback_debug.png")
            
            # Give it a moment for any async responses
            await asyncio.sleep(2)
            
            # Check if we captured a token
            if captured_token:
                if captured_token.startswith("code:"):
                    # We got an authorization code, need to exchange it
                    code = captured_token.replace("code:", "")
                    print(f"📋 Got authorization code from response, attempting to exchange for token...")
                    
                    # Try to exchange code for token using WorkOS SDK
                    try:
                        from workos import WorkOSClient
                        workos_api_key = os.getenv("WORKOS_API_KEY")
                        if workos_api_key:
                            workos_client = WorkOSClient(api_key=workos_api_key, client_id=workos_client_id)
                            
                            # Exchange code for token
                            try:
                                # authenticate_with_code only takes 'code' and optional 'session' parameter
                                cookie_password = os.getenv("WORKOS_COOKIE_PASSWORD")
                                session_config = None
                                if cookie_password:
                                    session_config = {
                                        "seal_session": True,
                                        "cookie_password": cookie_password,
                                    }
                                
                                auth_response = workos_client.user_management.authenticate_with_code(
                                    code=code,
                                    session=session_config,
                                )
                                
                                # Extract token from response (same logic as OAuth script)
                                if hasattr(auth_response, 'access_token'):
                                    token = auth_response.access_token
                                elif hasattr(auth_response, 'token'):
                                    token = auth_response.token
                                elif hasattr(auth_response, 'user') and hasattr(auth_response.user, 'access_token'):
                                    token = auth_response.user.access_token
                                
                                # Check for sealed session
                                if not token and hasattr(auth_response, 'sealed_session'):
                                    cookie_password = os.getenv("WORKOS_COOKIE_PASSWORD")
                                    if cookie_password:
                                        try:
                                            session = workos_client.user_management.load_sealed_session(
                                                sealed_session=auth_response.sealed_session,
                                                cookie_password=cookie_password,
                                            )
                                            auth_result = session.authenticate()
                                            if auth_result.authenticated and hasattr(auth_result, 'access_token'):
                                                token = auth_result.access_token
                                        except Exception as sealed_error:
                                            print(f"⚠️  Sealed session handling failed: {sealed_error}")
                                
                                if token:
                                    print(f"✅ Successfully exchanged code for token!")
                                else:
                                    print(f"⚠️  Code exchange succeeded but no token in response")
                                    print(f"   Response type: {type(auth_response)}")
                                    print(f"   Response attributes: {dir(auth_response)}")
                            except Exception as exchange_error:
                                print(f"❌ Code exchange failed: {exchange_error}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"⚠️  WORKOS_API_KEY not set, cannot exchange code")
                            token = None
                    except ImportError:
                        print(f"⚠️  WorkOS SDK not available, cannot exchange code")
                        token = None
                else:
                    token = captured_token
                    print(f"✅ Captured token from response!")
            
            # Also check current URL for token or code
            current_url = page.url
            if not token and current_url:
                parsed = urlparse(current_url)
                params = parse_qs(parsed.query)
                
                # Check for pending_authentication_token (from radar challenge)
                if "pending_authentication_token" in params and not token:
                    pending_token = params["pending_authentication_token"][0]
                    print(f"📋 Found pending_authentication_token: {pending_token[:20]}...")
                    print(f"   Waiting for final redirect...")
                    # Wait a bit more for the redirect to complete
                    try:
                        await page.wait_for_url(
                            lambda url: "pending_authentication_token" not in url,
                            timeout=10000
                        )
                        # Re-check URL after redirect
                        current_url = page.url
                        parsed = urlparse(current_url)
                        params = parse_qs(parsed.query)
                    except PlaywrightTimeoutError:
                        print(f"⚠️  Still waiting for redirect from pending token...")
                
                if "access_token" in params:
                    token = params["access_token"][0]
                    print(f"✅ Found token in URL parameters!")
                elif "code" in params:
                    code = params["code"][0]
                    print(f"📋 Found authorization code in URL: {code[:20]}...")
                    print(f"   Attempting to exchange code for token...")
                    
                    # Try to exchange code for token using WorkOS SDK
                    try:
                        from workos import WorkOSClient
                        workos_api_key = os.getenv("WORKOS_API_KEY")
                        if workos_api_key:
                            workos_client = WorkOSClient(api_key=workos_api_key, client_id=workos_client_id)
                            
                            # Exchange code for token
                            try:
                                # authenticate_with_code only takes 'code' and optional 'session' parameter
                                # Note: redirect_uri is not needed - it's inferred from the code
                                cookie_password = os.getenv("WORKOS_COOKIE_PASSWORD")
                                session_config = None
                                if cookie_password:
                                    # Try to use SessionConfig if available, otherwise use dict
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
                                
                                # Extract token from response (same logic as first occurrence)
                                if hasattr(auth_response, 'access_token'):
                                    token = auth_response.access_token
                                elif hasattr(auth_response, 'token'):
                                    token = auth_response.token
                                elif hasattr(auth_response, 'user') and hasattr(auth_response.user, 'access_token'):
                                    token = auth_response.user.access_token
                                
                                # Check for sealed session
                                if not token and hasattr(auth_response, 'sealed_session'):
                                    if cookie_password:
                                        try:
                                            session = workos_client.user_management.load_sealed_session(
                                                sealed_session=auth_response.sealed_session,
                                                cookie_password=cookie_password,
                                            )
                                            auth_result = session.authenticate()
                                            if auth_result.authenticated and hasattr(auth_result, 'access_token'):
                                                token = auth_result.access_token
                                        except Exception as sealed_error:
                                            print(f"⚠️  Sealed session handling failed: {sealed_error}")
                                
                                if token:
                                    print(f"✅ Successfully exchanged code for token!")
                                else:
                                    print(f"⚠️  Code exchange succeeded but no token in response")
                                    print(f"   Response type: {type(auth_response)}")
                                    print(f"   Response attributes: {dir(auth_response)}")
                            except Exception as exchange_error:
                                print(f"❌ Code exchange failed: {exchange_error}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"⚠️  WORKOS_API_KEY not set, cannot exchange code")
                    except ImportError:
                        print(f"⚠️  WorkOS SDK not available, cannot exchange code")
            
            # Check page content for token
            if not token:
                try:
                    content = await page.content()
                    # Look for token in page content (might be in a script tag or data attribute)
                    import re
                    token_patterns = [
                        r'"access_token"\s*:\s*"([^"]+)"',
                        r'"token"\s*:\s*"([^"]+)"',
                        r'access_token=([^\s&"]+)',
                    ]
                    for pattern in token_patterns:
                        match = re.search(pattern, content)
                        if match:
                            token = match.group(1)
                            print(f"✅ Found token in page content!")
                            break
                except Exception as e:
                    print(f"⚠️  Could not check page content: {e}")
            
            if captured_error:
                error_message = captured_error
                print(f"❌ Error captured: {error_message}")
            
        except Exception as e:
            print(f"❌ Error during OAuth flow: {e}")
            import traceback
            traceback.print_exc()
            # Take screenshot for debugging
            try:
                await page.screenshot(path="authkit_error_debug.png")
                print("   Screenshot saved to: authkit_error_debug.png")
            except:
                pass
        
        finally:
            # Keep browser open for a moment to inspect (only in non-headless mode)
            headless = os.getenv("HEADLESS", "true").lower() != "false"
            if not headless:
                print(f"\n⏳ Keeping browser open for 5 seconds to inspect...")
                await asyncio.sleep(5)
            await browser.close()
    
    if token:
        # Validate token format
        if isinstance(token, str) and len(token.split(".")) == 3:
            print(f"\n✅ Successfully obtained JWT token!")
            print(f"Token preview: {token[:50]}...{token[-20:]}")
            print(f"Token length: {len(token)} characters")
            
            # Decode token to show claims
            try:
                import jwt
                decoded = jwt.decode(token, options={"verify_signature": False})
                print(f"\n📋 Token claims:")
                print(f"   - sub (user_id): {decoded.get('sub', 'N/A')}")
                print(f"   - email: {decoded.get('email', 'N/A')}")
                print(f"   - iss (issuer): {decoded.get('iss', 'N/A')}")
                print(f"   - exp (expires): {decoded.get('exp', 'N/A')}")
                if decoded.get('exp'):
                    from datetime import datetime
                    exp_time = datetime.fromtimestamp(decoded['exp'])
                    print(f"     (expires at: {exp_time})")
            except Exception as e:
                print(f"\n⚠️  Could not decode token: {e}")
            
            # Save token to OS keychain
            try:
                from authkit_token_cache import save_token_to_keychain, is_token_expired
                if save_token_to_keychain(token):
                    # Check expiration and show info
                    is_expiring, expires_at = is_token_expired(token)
                    if expires_at:
                        from datetime import datetime
                        exp_time = datetime.fromtimestamp(expires_at)
                        time_until_expiry = expires_at - int(time.time())
                        if time_until_expiry > 0:
                            hours = time_until_expiry // 3600
                            minutes = (time_until_expiry % 3600) // 60
                            print(f"\n💾 Token saved to OS keychain (expires in ~{hours}h {minutes}m)")
                            print(f"   Will auto-refresh when expired or expiring soon")
                        else:
                            print(f"\n💾 Token saved to OS keychain (expired, will refresh on next use)")
                    else:
                        print(f"\n💾 Token saved to OS keychain (will be reused automatically)")
                else:
                    print(f"\n⚠️  Could not save to keychain, but token is available")
            except ImportError:
                print(f"\n⚠️  keyring not available, token not saved to keychain")
            except Exception as e:
                print(f"\n⚠️  Failed to save to keychain: {e}")
            
            print(f"\n💡 To use this token:")
            print(f"   export ATOMS_TEST_AUTH_TOKEN=\"{token}\"")
            print(f"\n   Or set it in your .env file:")
            print(f"   ATOMS_TEST_AUTH_TOKEN={token}")
            print(f"\n   (Token is also saved to OS keychain for automatic reuse)")
            
            return token
        else:
            print(f"\n⚠️  Token doesn't appear to be a valid JWT")
            print(f"Token: {token[:100]}...")
            return None
    else:
        if error_message:
            print(f"\n❌ Failed to get token: {error_message}")
        else:
            print(f"\n❌ Failed to get token from OAuth flow")
            print(f"   The OAuth flow may require manual intervention")
            print(f"   Or the token might be handled server-side")
        return None


if __name__ == "__main__":
    token = asyncio.run(get_authkit_token_via_playwright())
    if token:
        print(f"\n✅ Token ready for use!")
        sys.exit(0)
    else:
        print(f"\n❌ Could not get token")
        sys.exit(1)
