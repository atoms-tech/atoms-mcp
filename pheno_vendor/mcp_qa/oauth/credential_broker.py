"""
Unified Credential Broker for MCP Test Suites

This module provides a single, consistent OAuth flow that:
1. Prompts for credentials interactively when missing
2. Uses Playwright to automate OAuth and capture auth tokens
3. Shows progress inline (single overwritten line)
4. Saves credentials to .env for reuse
5. Provides credentials for direct HTTP test calls

Usage:
    broker = UnifiedCredentialBroker()
    client, credentials = await broker.get_authenticated_client()

    # Use client for MCP calls
    tools = await client.list_tools()

    # Use credentials for direct HTTP calls
    response = requests.post(url, headers={"Authorization": f"Bearer {credentials.access_token}"})
"""

import asyncio
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from fastmcp import Client
from fastmcp.client.auth import OAuth

from mcp_qa.auth.credential_manager import (
    CredentialType,
    CredentialManager,
    get_credential_manager,
)
from mcp_qa.logging import get_logger
from mcp_qa.oauth.granular_progress import (
    GranularOAuthProgress,
    OAuthSteps,
)

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


@dataclass
class CapturedCredentials:
    """Credentials captured during OAuth flow."""

    # OAuth tokens
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    # User credentials (for subsequent runs)
    email: Optional[str] = None
    password: Optional[str] = None

    # Session info
    session_id: Optional[str] = None
    provider: str = "authkit"

    # Server config
    mcp_endpoint: str = ""

    def is_valid(self) -> bool:
        """Check if credentials are still valid.

        Includes a 1-hour safety margin before expiration to prevent
        race conditions where token expires during request execution.
        """
        if not self.access_token:
            return False
        # Check for placeholder token that was never actually captured
        if self.access_token in ("captured_from_oauth", "placeholder", "TODO"):
            return False
        if self.expires_at:
            # Add 1-hour safety margin before expiration
            from datetime import timedelta
            safety_margin = timedelta(hours=1)
            if datetime.now() >= (self.expires_at - safety_margin):
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        data = asdict(self)
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CapturedCredentials':
        """Create from dict."""
        if 'expires_at' in data and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class OAuthProgress:
    """
    DEPRECATED: Legacy OAuth progress wrapper.

    This class is maintained for backward compatibility but uses the new
    GranularOAuthProgress internally. New code should use GranularOAuthProgress directly.
    """

    def __init__(self):
        self.granular_progress = GranularOAuthProgress()
        self._started = False

    def update(self, message: str, step: Optional[int] = None):
        """Update progress with message."""
        if not self._started:
            self.granular_progress.start()
            self._started = True
        # Legacy method - just update most recent step or add new one
        if self.granular_progress.steps:
            last_step = self.granular_progress.steps[-1]
            self.granular_progress.update_step_description(last_step.id, message)
        else:
            step_id = f"step_{len(self.granular_progress.steps)}"
            self.granular_progress.add_step(step_id, message)
            self.granular_progress.start_step(step_id)

    def advance(self, message: str):
        """Advance to next step."""
        if not self._started:
            self.granular_progress.start()
            self._started = True
        # Complete previous step if exists
        if self.granular_progress.steps:
            last_step = self.granular_progress.steps[-1]
            if last_step.status.value == "in_progress":
                self.granular_progress.complete_step(last_step.id)
        # Add and start new step
        step_id = f"step_{len(self.granular_progress.steps)}"
        self.granular_progress.add_step(step_id, message)
        self.granular_progress.start_step(step_id)

    def complete(self, message: str):
        """Complete progress with success message."""
        # Complete last step if in progress
        if self.granular_progress.steps:
            last_step = self.granular_progress.steps[-1]
            if last_step.status.value == "in_progress":
                self.granular_progress.complete_step(last_step.id)
        self.granular_progress.complete(message)

    def error(self, message: str):
        """Show error and stop progress."""
        self.granular_progress.error(message)

    def stop(self):
        """Stop progress display."""
        if self.granular_progress.live:
            self.granular_progress.live.stop()


class UnifiedCredentialBroker:
    """
    Unified credential broker that handles the complete OAuth flow.

    Features:
    - Interactive credential prompts
    - Playwright OAuth automation
    - Inline progress display
    - Credential caching in .env
    - Token capture for direct HTTP calls
    - Session-wide authentication (one auth per endpoint per session)
    """

    # Class-level session state (shared across all instances)
    _session_authenticated: Dict[str, bool] = {}  # Dict[str, bool] keyed by endpoint
    _session_credentials: Dict[str, CapturedCredentials] = {}  # Dict[str, CapturedCredentials] keyed by endpoint
    _session_lock = asyncio.Lock()  # For thread-safe access

    def __init__(
        self,
        mcp_endpoint: Optional[str] = None,
        provider: str = "authkit",
        debug: bool = False,
    ):
        self.mcp_endpoint = mcp_endpoint or os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")
        self.provider = provider
        self.debug = debug or os.getenv("OAUTH_DEBUG", "").lower() in ("1", "true", "yes")
        self.env_file = Path.cwd() / ".env"
        self.cache_file = Path.home() / ".atoms_mcp_test_cache" / "credentials.json"
        self.cache_file.parent.mkdir(exist_ok=True)

        self._credentials: Optional[CapturedCredentials] = None
        self._client: Optional[Client] = None
        self._oauth_url: Optional[str] = None
        self._callback_port: Optional[int] = None
        self._credential_manager: Optional[CredentialManager] = None
        self.logger = get_logger(__name__).bind(provider=provider)

    def _load_credentials_from_env(self) -> Optional[Dict[str, str]]:
        """
        Load credentials from .env file.
        
        Automatically loads common credential fields:
        - ATOMS_TEST_EMAIL / ZEN_TEST_EMAIL
        - ATOMS_TEST_PASSWORD / ZEN_TEST_PASSWORD  
        - MCP_ENDPOINT
        - OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET
        - Any other env vars needed for testing
        """
        if not self.env_file.exists():
            # Try alternate locations
            alternate_env = Path.home() / ".mcp_qa" / ".env"
            if alternate_env.exists():
                self.env_file = alternate_env
            else:
                return None

        creds = {}
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    creds[key] = value

        # Auto-set environment variables for downstream use
        for key, value in creds.items():
            if key not in os.environ:
                os.environ[key] = value

        return creds

    def _get_credential_manager(self) -> Optional[CredentialManager]:
        """Lazy-load the shared credential manager."""
        if self._credential_manager is not None:
            return self._credential_manager

        try:
            self._credential_manager = get_credential_manager()
        except Exception as exc:
            self.logger.warning("Credential manager unavailable", error=str(exc))
            self._credential_manager = None

        return self._credential_manager

    def _load_from_secret_manager(
        self,
        manager: CredentialManager,
    ) -> Optional[Tuple[str, str]]:
        """Attempt to fetch provider credentials from the secure store."""
        credentials = manager.get_credentials_by_provider(self.provider)

        prioritized = []
        fallbacks = []
        for credential in credentials:
            if credential.credential_type != CredentialType.PASSWORD:
                continue
            if not credential.value:
                continue
            metadata = credential.metadata or {}
            source = metadata.get("source")
            if credential.email and source in {"env", "oauth_broker"}:
                prioritized.append(credential)
            else:
                fallbacks.append(credential)

        for credential in prioritized + fallbacks:
            email = credential.email
            if not email:
                continue
            self.logger.info(
                "Using credentials from secure store",
                credential_name=credential.name,
                emoji="🔐"
            )
            return email, credential.value

        return None

    def _persist_to_secret_manager(
        self,
        manager: CredentialManager,
        email: str,
        password: str,
    ) -> None:
        """Store or update credentials in the secure manager for future runs."""
        name = f"{self.provider}_{self._sanitize_identifier(email)}_login"
        metadata = {"source": "oauth_broker", "provider": self.provider}

        existing = manager.get_credential(name)
        if existing:
            update_kwargs: Dict[str, Any] = {}
            if existing.value != password:
                update_kwargs["value"] = password
            if email and existing.email != email:
                update_kwargs["email"] = email

            combined_metadata = existing.metadata.copy() if existing.metadata else {}
            metadata_changed = False
            for key, value in metadata.items():
                if combined_metadata.get(key) != value:
                    combined_metadata[key] = value
                    metadata_changed = True
            if metadata_changed:
                update_kwargs["metadata"] = combined_metadata

            if update_kwargs:
                manager.update_credential(name, **update_kwargs)
        else:
            manager.store_credential(
                name=name,
                credential_type=CredentialType.PASSWORD,
                provider=self.provider,
                value=password,
                email=email,
                metadata=metadata,
            )

    @staticmethod
    def _sanitize_identifier(value: Optional[str]) -> str:
        """Sanitize user-provided identifiers for credential naming."""
        if not value:
            return "default"
        return "".join(ch.lower() if ch.isalnum() else "_" for ch in value)

    def _save_credentials_to_env(self, email: str, password: str):
        """Save credentials to .env file."""
        # Read existing .env
        existing_lines = []
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                existing_lines = f.readlines()

        # Update or add credentials
        updated = False
        password_updated = False
        new_lines = []

        for line in existing_lines:
            if line.strip().startswith('ATOMS_TEST_EMAIL=') or line.strip().startswith('ZEN_TEST_EMAIL='):
                new_lines.append(f'ATOMS_TEST_EMAIL={email}\n')
                updated = True
            elif line.strip().startswith('ATOMS_TEST_PASSWORD=') or line.strip().startswith('ZEN_TEST_PASSWORD='):
                new_lines.append(f'ATOMS_TEST_PASSWORD={password}\n')
                password_updated = True
            else:
                new_lines.append(line)

        # Add if not found
        if not updated:
            new_lines.append(f'ATOMS_TEST_EMAIL={email}\n')
        if not password_updated:
            new_lines.append(f'ATOMS_TEST_PASSWORD={password}\n')

        # Write back
        with open(self.env_file, 'w') as f:
            f.writelines(new_lines)

        self.logger.info("Credentials saved to .env", env_file=str(self.env_file), emoji="✅")

    def _prompt_for_credentials(self) -> Tuple[str, str]:
        """
        Retrieve credentials from secure store, environment, or prompt.
        
        Tries multiple sources in order:
        1. Secure credential manager (if available)
        2. Environment variables / .env file
        3. Interactive prompt (fallback)
        
        Supports multiple credential key patterns:
        - ATOMS_TEST_EMAIL / ZEN_TEST_EMAIL / TEST_EMAIL / MCP_EMAIL
        - ATOMS_TEST_PASSWORD / ZEN_TEST_PASSWORD / TEST_PASSWORD / MCP_PASSWORD
        """
        env_creds = self._load_credentials_from_env() or {}

        # Ensure the secure store can bootstrap using any credentials loaded from the
        # environment (especially the master password) before we instantiate it.
        manager = self._get_credential_manager()

        if manager:
            stored = self._load_from_secret_manager(manager)
            if stored:
                return stored

        # Try multiple credential key patterns
        email_keys = ['ATOMS_TEST_EMAIL', 'ZEN_TEST_EMAIL', 'TEST_EMAIL', 'MCP_EMAIL']
        password_keys = ['ATOMS_TEST_PASSWORD', 'ZEN_TEST_PASSWORD', 'TEST_PASSWORD', 'MCP_PASSWORD']

        email = None
        password = None

        # Try to find email from env (first match wins)
        if env_creds:
            for key in email_keys:
                value = env_creds.get(key)
                if value:
                    email = value
                    self.logger.info("Using email from .env", key=key, email=value, emoji="📧")
                    break

        if not email:
            email = input("📧 Enter email: ").strip()

        # Try to find password from env (first match wins)
        if env_creds:
            for key in password_keys:
                value = env_creds.get(key)
                if value:
                    password = value
                    self.logger.info("Using password from .env", key=key, emoji="🔑")
                    break

        # If we have credentials from the environment and a credential manager, store
        # them immediately so future runs can pull straight from the secure store.
        if manager and email and password:
            self._persist_to_secret_manager(manager, email, password)
            return email, password

        if not password:
            import getpass
            password = getpass.getpass("🔑 Enter password: ").strip()

        # Save to .env if new or missing
        if not env_creds or not any(key in env_creds for key in email_keys):
            save = input("💾 Save credentials to .env? (y/n): ").strip().lower()
            if save in ['y', 'yes']:
                self._save_credentials_to_env(email, password)

        if manager:
            self._persist_to_secret_manager(manager, email, password)

        return email, password
    
    def _prompt_for_new_credentials(self) -> Tuple[str, str]:
        """
        Prompt user for new credentials (after invalid credentials detected).

        Returns:
            (email, password) tuple
        """
        import getpass

        print("")
        print("❌ Invalid credentials detected. Please enter new credentials:")
        print("")

        email = input("📧 Enter email: ").strip()
        password = getpass.getpass("🔑 Enter password: ").strip()

        # Save to credential manager if available
        manager = self._get_credential_manager()
        if manager and email and password:
            self._persist_to_secret_manager(manager, email, password)

        return email, password

    async def ensure_session_authenticated(self, force_reauth: bool = False) -> CapturedCredentials:
        """
        Ensure authentication happens once per endpoint per session.

        This should be called BEFORE test collection to ensure auth is complete.
        Uses a lock to prevent multiple simultaneous auth flows.
        Shows rich progress bar during OAuth flow.

        Args:
            force_reauth: Force re-authentication even if already authenticated

        Returns:
            CapturedCredentials object with access token and user info

        Raises:
            RuntimeError: If authentication fails
        """
        async with self._session_lock:
            endpoint_key = self.mcp_endpoint

            # Check if already authenticated for this endpoint
            if not force_reauth and endpoint_key in self._session_authenticated:
                if self._session_authenticated[endpoint_key]:
                    credentials = self._session_credentials.get(endpoint_key)
                    if credentials and credentials.is_valid():
                        self.logger.info(
                            "Using existing session authentication",
                            endpoint=endpoint_key,
                            email=credentials.email,
                            emoji="✅"
                        )
                        return credentials
                    else:
                        # Credentials expired or invalid
                        self.logger.warning(
                            "Session credentials expired or invalid, re-authenticating",
                            endpoint=endpoint_key,
                            emoji="⚠️"
                        )

            # Create progress tracker for OAuth flow
            progress = GranularOAuthProgress()
            progress.start()

            # Step 1: Check cache
            progress.add_step(*OAuthSteps.PULL_CREDENTIALS)
            progress.start_step("pull_credentials")

            cached_creds = None
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, 'r') as f:
                        data = json.load(f)
                    cached_creds = CapturedCredentials.from_dict(data)
                    if cached_creds.is_valid():
                        progress.complete_step("pull_credentials")
                        # Store in session cache
                        self._session_credentials[endpoint_key] = cached_creds
                        self._session_authenticated[endpoint_key] = True

                        # Show completion message
                        if HAS_RICH:
                            from rich.console import Console
                            console = Console()
                            expires_str = cached_creds.expires_at.strftime("%Y-%m-%d %H:%M:%S") if cached_creds.expires_at else "unknown"
                            console.print(
                                f"\n[bold green]✅ Authentication complete[/bold green]\n"
                                f"   [cyan]User:[/cyan] {cached_creds.email or 'unknown'}\n"
                                f"   [cyan]Expires:[/cyan] {expires_str}\n"
                                f"   [cyan]Endpoint:[/cyan] {endpoint_key}\n"
                            )

                        progress.complete("Authentication complete (using cached credentials)")
                        return cached_creds
                    else:
                        progress.skip_step("pull_credentials", "Cached credentials expired")
                except Exception as e:
                    progress.skip_step("pull_credentials", f"Cache read failed: {e}")
                    self.logger.debug(f"Failed to load cached credentials: {e}")
            else:
                progress.skip_step("pull_credentials", "No cache file found")

            # Step 2: Perform full OAuth flow
            progress.add_step("launch_browser", "Launching browser for OAuth")
            progress.start_step("launch_browser")

            try:
                # Get authenticated client
                client, credentials = await self.get_authenticated_client()

                # Store in session cache
                self._session_credentials[endpoint_key] = credentials
                self._session_authenticated[endpoint_key] = True

                # Show completion message with user info
                if HAS_RICH:
                    from rich.console import Console
                    console = Console()
                    expires_str = credentials.expires_at.strftime("%Y-%m-%d %H:%M:%S") if credentials.expires_at else "unknown"
                    console.print(
                        f"\n[bold green]✅ Authentication complete[/bold green]\n"
                        f"   [cyan]User:[/cyan] {credentials.email or 'unknown'}\n"
                        f"   [cyan]Expires:[/cyan] {expires_str}\n"
                        f"   [cyan]Endpoint:[/cyan] {endpoint_key}\n"
                    )

                progress.complete_step("launch_browser")
                progress.complete("Authentication complete")

                return credentials

            except Exception as e:
                self.logger.error(
                    "Session authentication failed",
                    endpoint=endpoint_key,
                    error=str(e),
                    emoji="❌"
                )
                progress.error(f"Authentication failed: {e}")
                # Mark as not authenticated
                self._session_authenticated[endpoint_key] = False
                raise RuntimeError(f"Authentication failed: {e}") from e

    async def _automate_oauth_with_playwright(
        self,
        oauth_url: str,
        email: str,
        password: str,
        progress: Optional[GranularOAuthProgress] = None
    ) -> bool:
        """
        Automate OAuth flow using Playwright.

        Args:
            oauth_url: OAuth authorization URL
            email: User email
            password: User password
            progress: Optional progress tracker for granular step updates

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use PlaywrightOAuthAdapter from same package
            from .playwright_adapter import PlaywrightOAuthAdapter

            # Create adapter with debug mode
            adapter = PlaywrightOAuthAdapter(
                email=email,
                password=password,
                provider=self.provider,
                debug=self.debug
            )

            # Set credential reprompt callback
            adapter.set_credential_reprompt_callback(self._prompt_for_new_credentials)

            # Set progress tracker on adapter for granular updates
            if progress:
                adapter.set_progress_tracker(progress)

            # Run automation with retry and credential reprompt support
            success = await adapter.automate_login_with_retry(
                oauth_url,
                allow_credential_reprompt=True
            )

            if success:
                # Update stored credentials if they changed
                if adapter.email != email or adapter.password != password:
                    manager = self._get_credential_manager()
                    if manager:
                        self._persist_to_secret_manager(
                            manager,
                            adapter.email,
                            adapter.password
                        )
                return True
            else:
                return False

        except Exception as e:
            self.logger.error("OAuth automation error", error=str(e))
            if progress:
                progress.error(f"OAuth automation error: {e}")
            return False

    async def _trigger_callback(self, callback_url: str):
        """Trigger OAuth callback."""
        import httpx
        async with httpx.AsyncClient() as client:
            await client.get(callback_url, follow_redirects=True)

    async def get_authenticated_client(self) -> tuple[Client, CapturedCredentials]:
        """
        Get authenticated MCP client and captured credentials.

        This is the main entry point. It will:
        1. Check for cached credentials
        2. Prompt for credentials if missing
        3. Use Playwright to automate OAuth
        4. Capture auth tokens
        5. Return both MCP client and credentials

        Returns:
            (FastMCP Client, CapturedCredentials)
        """
        # Use new granular progress for detailed step tracking
        progress = GranularOAuthProgress()
        progress.start()

        # Step 1: Check cache
        progress.add_step(*OAuthSteps.PULL_CREDENTIALS)
        progress.start_step("pull_credentials")

        cached_creds = None
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                cached_creds = CapturedCredentials.from_dict(data)
                if cached_creds.is_valid():
                    progress.complete_step("pull_credentials")
                    self.logger.info(
                        "Cached tokens found but token-based auth not implemented, using OAuth",
                        emoji="⚠️"
                    )
                else:
                    progress.skip_step("pull_credentials", "Cached credentials expired")
            except Exception as e:
                progress.skip_step("pull_credentials", f"Cache read failed: {e}")
                self.logger.debug(f"Failed to load cached credentials: {e}")
        else:
            progress.skip_step("pull_credentials", "No cache file found")

        # Step 2: Load credentials from credential manager or environment
        progress.add_step(*OAuthSteps.LOAD_ENV_CREDENTIALS)
        progress.start_step("load_env_credentials")

        email, password = self._prompt_for_credentials()
        progress.complete_step("load_env_credentials")

        # Step 3: Initialize OAuth flow
        progress.add_step(*OAuthSteps.INIT_OAUTH)
        progress.start_step("init_oauth")

        oauth_url_captured = asyncio.Event()
        auth_token_captured = asyncio.Event()

        class CaptureOAuth(OAuth):
            """OAuth handler that captures URL and token."""

            def __init__(self, broker: 'UnifiedCredentialBroker', *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.broker = broker
                self.broker._callback_port = self.redirect_port
                self.broker.logger.debug("CaptureOAuth initialized", redirect_port=self.redirect_port)

            async def redirect_handler(self, authorization_url: str) -> None:
                """Called when OAuth URL is ready."""
                self.broker.logger.debug("redirect_handler called", url=authorization_url)
                self.broker._oauth_url = authorization_url
                oauth_url_captured.set()

            async def launch_browser(self, authorization_url: str) -> None:
                """Override launch_browser to capture URL before launching."""
                self.broker.logger.debug("launch_browser called", url=authorization_url)
                # Capture URL first
                self.broker._oauth_url = authorization_url
                oauth_url_captured.set()
                # Don't actually launch browser - we'll handle it with Playwright
                # Just set the event and return

        # Create client with our custom OAuth
        oauth = CaptureOAuth(self, mcp_url=self.mcp_endpoint, client_name="MCP Test Suite")
        client = Client(self.mcp_endpoint, auth=oauth)
        progress.complete_step("init_oauth")

        # Step 4: Fetch OAuth URL
        progress.add_step(*OAuthSteps.FETCH_OAUTH_URL)
        progress.start_step("fetch_oauth_url")

        # Start OAuth flow
        self.logger.debug("Starting OAuth flow...")
        self.logger.debug(f"OAuth redirect handler: {oauth.redirect_handler}")
        self.logger.debug(f"OAuth launch_browser: {oauth.launch_browser}")
        auth_task = asyncio.create_task(client.__aenter__())

        # Wait for either OAuth URL or auth completion
        # If server has cached credentials, it may complete immediately with 202 Accepted
        self.logger.debug("Waiting for OAuth URL or immediate auth completion...")

        # Race between OAuth URL being captured and auth task completing
        oauth_url_task = asyncio.create_task(oauth_url_captured.wait())

        # Poll with progress updates every 2 seconds
        start_time = asyncio.get_event_loop().time()
        timeout = 30.0
        poll_interval = 2.0

        done = set()
        pending = {auth_task, oauth_url_task}

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                break

            # Update progress description based on elapsed time
            if elapsed < 5:
                progress.update_step_description("fetch_oauth_url", "Contacting MCP server")
            elif elapsed < 10:
                progress.update_step_description("fetch_oauth_url", "Fetching OAuth configuration")
            elif elapsed < 15:
                progress.update_step_description("fetch_oauth_url", "Preparing authorization request")
            elif elapsed < 20:
                progress.update_step_description("fetch_oauth_url", "Awaiting OAuth response")
            else:
                progress.update_step_description(
                    "fetch_oauth_url",
                    f"Still waiting ({int(timeout - elapsed)}s left)"
                )

            # Check if any task completed
            new_done, pending = await asyncio.wait(
                pending,
                timeout=poll_interval,
                return_when=asyncio.FIRST_COMPLETED
            )

            if new_done:
                done = new_done
                break
        
        # Check what completed
        if auth_task in done:
            # Auth task completed - check if it succeeded or failed
            oauth_url_task.cancel()
            try:
                await oauth_url_task
            except asyncio.CancelledError:
                pass

            progress.complete_step("fetch_oauth_url")

            # Check if auth task completed successfully or with error
            try:
                exception = auth_task.exception()
                if exception:
                    # Auth task failed - raise the error
                    self.logger.error(f"Authentication failed: {exception}", emoji="❌")
                    progress.error(f"Authentication failed: {exception}")
                    raise exception
            except asyncio.InvalidStateError:
                # Task is still running (shouldn't happen but handle it)
                self.logger.error("Auth task in invalid state")
                progress.error("Authentication in invalid state")
                raise RuntimeError("Auth task completed but is in invalid state")

            # Auth completed successfully
            self.logger.info("Authentication completed immediately (cached session)", emoji="✅")
            progress.complete("Authentication complete (cached session)")
        elif oauth_url_task in done:
            # OAuth URL was captured - need to automate login
            # DO NOT cancel auth_task - we need it to complete after OAuth automation
            self.logger.debug(f"OAuth URL captured: {self._oauth_url}")
            progress.complete_step("fetch_oauth_url")

            # Pass progress to Playwright automation for granular step tracking
            success = await self._automate_oauth_with_playwright(
                self._oauth_url, email, password, progress
            )
            if not success:
                progress.error("OAuth automation failed")
                raise RuntimeError("OAuth automation failed")
            
            # Wait for auth to complete after automation with granular progress
            # Add token exchange step
            progress.add_step(*OAuthSteps.EXCHANGE_TOKEN)
            progress.start_step("exchange_token")

            # Poll auth task completion with progress updates
            start_time = asyncio.get_event_loop().time()
            timeout = 60.0
            poll_interval = 2.0  # Check every 2 seconds

            try:
                while not auth_task.done():
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        raise asyncio.TimeoutError()

                    # Update progress message based on elapsed time
                    if elapsed < 10:
                        progress.update_step_description("exchange_token", "Processing OAuth callback")
                    elif elapsed < 20:
                        progress.update_step_description("exchange_token", "Validating access token")
                    elif elapsed < 30:
                        progress.update_step_description("exchange_token", "Verifying credentials")
                    elif elapsed < 40:
                        progress.update_step_description("exchange_token", "Waiting for server response")
                    else:
                        progress.update_step_description(
                            "exchange_token",
                            f"Still waiting ({int(timeout - elapsed)}s left)"
                        )

                    # Wait a bit before checking again
                    try:
                        await asyncio.wait_for(auth_task, timeout=poll_interval)
                        break  # Task completed
                    except asyncio.TimeoutError:
                        # Continue polling
                        continue

                progress.complete_step("exchange_token")
            except asyncio.CancelledError:
                # This can happen if the OAuth callback completed successfully
                # and FastMCP cancelled the auth task internally
                self.logger.debug("Auth task was cancelled (OAuth likely completed)")
                progress.complete_step("exchange_token")
            except asyncio.TimeoutError:
                # Check if auth_task is actually done (might be cancelled)
                if auth_task.done():
                    try:
                        # Try to get the result or exception
                        auth_task.result()
                        self.logger.info("Auth task completed despite timeout")
                        progress.complete_step("exchange_token")
                    except asyncio.CancelledError:
                        self.logger.debug("Auth task was cancelled (OAuth completed)")
                        progress.complete_step("exchange_token")
                    except Exception as e:
                        progress.error(f"Authentication failed: {e}")
                        raise
                else:
                    progress.error("Authentication timeout after OAuth")
                    raise RuntimeError("Authentication timed out after OAuth automation")
            except Exception as e:
                progress.error(f"Authentication failed: {e}")
                raise
        else:
            # Timeout - neither completed
            self.logger.error("Timeout waiting for OAuth URL or auth completion")
            self.logger.error(f"Auth task done: {auth_task.done()}")
            self.logger.error(f"OAuth URL captured: {oauth_url_captured.is_set()}")

            # Try to get exception info from auth task
            if auth_task.done():
                try:
                    exc = auth_task.exception()
                    if exc:
                        self.logger.error(f"Auth task exception: {exc}")
                except Exception as e:
                    self.logger.error(f"Could not check auth task exception: {e}")
            else:
                self.logger.error(
                    "Possible causes: 1) FastMCP OAuth not responding, "
                    "2) MCP server not initiating OAuth flow, 3) Network/firewall issue"
                )

            progress.error("Timeout waiting for authentication")
            raise RuntimeError("OAuth URL not received and auth did not complete - MCP server may be down or slow")

        # Create credentials object
        progress.add_step(*OAuthSteps.SAVE_SESSION)
        progress.start_step("save_session")

        # Extract the actual access token from the OAuth flow
        # The client has a transport which has an auth object (the OAuth instance)
        # The OAuth instance inherits from OAuthClientProvider which has context.current_tokens
        access_token = None
        expires_at = None
        refresh_token = None

        try:
            # Debug: Check what we have
            self.logger.debug(f"Client type: {type(client)}")
            self.logger.debug(f"Has transport: {hasattr(client, 'transport')}")

            # Access the OAuth handler through the client's transport
            if hasattr(client, 'transport') and hasattr(client.transport, 'auth'):
                auth_obj = client.transport.auth
                self.logger.debug(f"Auth type: {type(auth_obj)}")
                self.logger.debug(f"Has context: {hasattr(auth_obj, 'context')}")

                # The auth object is an OAuth instance which inherits from OAuthClientProvider
                if hasattr(auth_obj, 'context'):
                    context = auth_obj.context
                    self.logger.debug(f"Context type: {type(context)}")
                    self.logger.debug(f"Has current_tokens: {hasattr(context, 'current_tokens')}")
                    self.logger.debug(f"current_tokens value: {context.current_tokens if hasattr(context, 'current_tokens') else 'N/A'}")

                    if hasattr(context, 'current_tokens'):
                        current_tokens = context.current_tokens
                        if current_tokens:
                            access_token = current_tokens.access_token
                            refresh_token = current_tokens.refresh_token
                            # Calculate expiration time from expires_in if available
                            if hasattr(current_tokens, 'expires_in') and current_tokens.expires_in:
                                expires_at = datetime.now() + timedelta(seconds=current_tokens.expires_in)
                            self.logger.info(
                                "Successfully captured access token from OAuth flow",
                                token_length=len(access_token) if access_token else 0,
                                has_refresh=bool(refresh_token),
                                expires_at=expires_at.isoformat() if expires_at else None,
                                emoji="🔑"
                            )
                        else:
                            self.logger.warning("current_tokens is None", emoji="⚠️")
                    else:
                        self.logger.warning("context has no current_tokens attribute", emoji="⚠️")
                else:
                    self.logger.warning("auth has no context attribute", emoji="⚠️")
            else:
                self.logger.warning("client has no transport.auth", emoji="⚠️")
        except Exception as e:
            self.logger.warning(
                "Failed to extract access token from OAuth context",
                error=str(e),
                emoji="⚠️"
            )
            import traceback
            self.logger.debug(f"Token extraction traceback: {traceback.format_exc()}")

        # Fallback if we couldn't get the token
        if not access_token:
            self.logger.warning(
                "Access token not found in OAuth context, using placeholder",
                emoji="⚠️"
            )
            access_token = "captured_from_oauth"  # Placeholder fallback
            expires_at = datetime.now() + timedelta(hours=24)

        credentials = CapturedCredentials(
            access_token=access_token,
            refresh_token=refresh_token,
            email=email,
            password=password,
            provider=self.provider,
            mcp_endpoint=self.mcp_endpoint,
            expires_at=expires_at
        )

        # Cache credentials
        with open(self.cache_file, 'w') as f:
            json.dump(credentials.to_dict(), f, indent=2)

        progress.complete_step("save_session")

        self._client = client
        self._credentials = credentials

        # Complete the entire OAuth flow
        progress.complete("Authentication complete")

        return client, credentials

    async def close(self):
        """Clean up resources."""
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
            except RuntimeError as e:
                # Ignore "not holding this lock" errors during cleanup
                # This can happen when async generators are closed while tasks are cancelled
                if "not holding this lock" not in str(e):
                    raise
                self.logger.debug("Ignoring lock cleanup error during client close", error=str(e))


# Convenience function
async def get_authenticated_mcp_client(
    mcp_endpoint: Optional[str] = None,
    provider: str = "authkit"
) -> tuple[Client, CapturedCredentials]:
    """
    Convenience function to get authenticated client and credentials.

    Usage:
        client, creds = await get_authenticated_mcp_client()

        # Use client for MCP calls
        tools = await client.list_tools()

        # Use creds for direct HTTP
        response = httpx.post(url, headers={"Authorization": f"Bearer {creds.access_token}"})
    """
    broker = UnifiedCredentialBroker(mcp_endpoint, provider)
    return await broker.get_authenticated_client()
