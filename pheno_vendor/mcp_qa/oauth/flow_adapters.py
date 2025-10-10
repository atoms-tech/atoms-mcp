"""
OAuth Flow Adapters for Different Providers and User Flows

This module provides specialized adapters for various OAuth flows:
- AuthKit Standard (email/password)
- AuthKit Standalone Connect (3rd party auth)
- Google OAuth
- GitHub OAuth
- Custom provider support

Each adapter handles provider-specific selectors and workflows.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from mcp_qa.logging import get_logger

# Import for type hints only (avoid circular import)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mcp_qa.oauth.granular_progress import GranularOAuthProgress


class InvalidCredentialsError(Exception):
    """Raised when invalid login credentials are detected."""
    pass


@dataclass
class FlowConfig:
    """Configuration for an OAuth flow."""

    name: str
    selectors: Dict[str, str]
    steps: list[str]
    timing: Dict[str, float] = None
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timing is None:
            self.timing = {
                "page_load": 2.0,
                "input_fill": 0.3,
                "button_click": 1.0,
                "navigation": 3.0,
                "allow_enable": 1.0,
            }


class OAuthFlowAdapter(ABC):
    """Base class for OAuth flow adapters."""

    def __init__(self, email: str, password: str, debug: bool = False):
        self.email = email
        self.password = password
        self.debug = debug
        self.debug_dir = Path.cwd() / ".oauth_debug"
        if debug:
            self.debug_dir.mkdir(exist_ok=True)
        self._last_url_before_signin: Optional[str] = None
        self._last_url_after_signin: Optional[str] = None
        self.logger = get_logger(__name__).bind(email=email, debug=debug)
        self._progress_tracker: Optional['GranularOAuthProgress'] = None

    def set_progress_tracker(self, progress: 'GranularOAuthProgress'):
        """Set progress tracker for granular step updates."""
        self._progress_tracker = progress

    @abstractmethod
    def get_config(self) -> FlowConfig:
        """Return the flow configuration."""
        pass

    def _sanitize_text(self, text: Optional[str]) -> Optional[str]:
        """Mask sensitive values such as email/password before logging."""
        if not text:
            return text

        sanitized = text
        if self.email:
            sanitized = sanitized.replace(self.email, "***EMAIL***")
        if self.password:
            sanitized = sanitized.replace(self.password, "***PASSWORD***")
        return sanitized

    async def dump_page_state(
        self, page, step_name: str, error: Optional[Exception] = None
    ):
        """Dump page HTML, accessibility tree, and optional screenshot for debugging."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{step_name}_{timestamp}"

        html_content: Optional[str] = None
        sanitized_html: Optional[str] = None
        accessibility_snapshot: Optional[str] = None

        try:
            html_content = await page.content()
            sanitized_html = self._sanitize_text(html_content)
        except Exception as exc:
            self.logger.warning("Unable to capture HTML content", error=str(exc), emoji="⚠️")

        try:
            tree = await page.accessibility.snapshot()
            if tree:
                accessibility_snapshot = self._sanitize_text(json.dumps(tree, indent=2))
        except Exception as exc:
            self.logger.debug("Accessibility snapshot failed", error=str(exc), emoji="⚠️")

        dump_dir = self.debug_dir
        dump_dir.mkdir(exist_ok=True)

        if sanitized_html:
            html_file = dump_dir / f"{prefix}.html"
            try:
                html_file.write_text(sanitized_html)
                self.logger.debug("OAuth HTML dump saved", file=str(html_file), emoji="📄")
            except Exception as exc:
                self.logger.debug("Failed to write HTML dump", error=str(exc), emoji="⚠️")

            preview = sanitized_html[:2000]
            if preview:
                self.logger.debug("HTML preview (first 2000 chars)", preview=preview, emoji="📄")

        if accessibility_snapshot:
            tree_file = dump_dir / f"{prefix}_tree.json"
            try:
                tree_file.write_text(accessibility_snapshot)
                self.logger.debug("Accessibility tree saved", file=str(tree_file), emoji="🌳")
            except Exception as exc:
                self.logger.debug("Failed to write accessibility tree", error=str(exc), emoji="⚠️")

            tree_preview = accessibility_snapshot[:2000]
            if tree_preview:
                self.logger.debug("Accessibility preview (first 2000 chars)", preview=tree_preview, emoji="🌳")

        try:
            info_lines = [f"URL: {page.url}"]
            if error:
                info_lines.append(f"Error: {self._sanitize_text(str(error))}")
            info_file = dump_dir / f"{prefix}_info.txt"
            info_file.write_text("\n".join(info_lines))
            self.logger.debug("Context saved", file=str(info_file), emoji="🔗")
        except Exception as exc:
            self.logger.debug("Failed to write context info", error=str(exc), emoji="⚠️")

        if self.debug:
            try:
                screenshot_file = dump_dir / f"{prefix}.png"
                await page.screenshot(path=str(screenshot_file))
                self.logger.debug("Screenshot saved", file=str(screenshot_file), emoji="📸")
            except Exception as exc:
                self.logger.debug("Screenshot capture failed", error=str(exc), emoji="⚠️")

    async def wait_for_selector_safe(
        self, page, selector: str, timeout: float = 5000, step_name: str = "unknown"
    ) -> bool:
        """
        Wait for selector with debug dumping on failure.

        Returns:
            True if selector found, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            self.logger.debug(
                "Selector not found",
                selector=selector,
                step=step_name,
                emoji="⚠️"
            )
            await self.dump_page_state(page, f"selector_not_found_{step_name}", e)
            return False

    async def execute_flow(self, page, oauth_url: str) -> bool:
        """
        Execute the OAuth flow.

        Args:
            page: Playwright page object
            oauth_url: OAuth authorization URL

        Returns:
            True if successful, False otherwise
        """
        config = self.get_config()

        # Navigate to OAuth URL
        if self._progress_tracker:
            # Import here to avoid circular dependency
            from mcp_qa.oauth.granular_progress import OAuthSteps
            self._progress_tracker.add_step(*OAuthSteps.NAVIGATE_LOGIN)
            self._progress_tracker.start_step("navigate_login")

        await page.goto(oauth_url, wait_until="networkidle")
        await asyncio.sleep(config.timing["page_load"])

        if self._progress_tracker:
            self._progress_tracker.complete_step("navigate_login")

        if self.debug:
            await self.dump_page_state(page, "initial_load")

        # Execute flow steps
        for step in config.steps:
            try:
                # Report progress for each step
                if self._progress_tracker:
                    step_description = self._get_step_description(step)
                    if step_description:
                        step_id, desc = step_description
                        self._progress_tracker.add_step(step_id, desc)
                        self._progress_tracker.start_step(step_id)

                if step == "fill_email":
                    await self._fill_email(page, config)
                elif step == "click_continue_if_present":
                    await self._click_continue_if_present(page, config)
                elif step == "fill_password":
                    await self._fill_password(page, config)
                elif step == "click_signin":
                    await self._click_signin(page, config)
                elif step == "verify_login_transition":
                    if not await self._verify_login_transition(page, config):
                        if self._progress_tracker:
                            step_description = self._get_step_description(step)
                            if step_description:
                                self._progress_tracker.complete_step(
                                    step_description[0],
                                    error="Login verification failed"
                                )
                        return False
                elif step == "click_allow":
                    await self._click_allow(page, config)
                elif step == "third_party_auth":
                    await self._third_party_auth(page, config)
                else:
                    self.logger.warning("Unknown step", step=step, emoji="⚠️")

                # Complete the step
                if self._progress_tracker:
                    step_description = self._get_step_description(step)
                    if step_description:
                        self._progress_tracker.complete_step(step_description[0])

            except Exception as e:
                self.logger.error("Step failed", step=step, error=str(e), emoji="❌")
                await self.dump_page_state(page, f"step_failed_{step}", e)

                # Mark step as failed in progress
                if self._progress_tracker:
                    step_description = self._get_step_description(step)
                    if step_description:
                        self._progress_tracker.complete_step(
                            step_description[0],
                            error=str(e)
                        )
                return False

        return True

    def _get_step_description(self, step: str) -> Optional[tuple[str, str]]:
        """
        Get progress step ID and description for a flow step.

        Args:
            step: Flow step name

        Returns:
            Tuple of (step_id, description) or None
        """
        # Import here to avoid circular dependency
        from mcp_qa.oauth.granular_progress import OAuthSteps

        step_map = {
            "fill_email": OAuthSteps.ENTER_EMAIL,
            "fill_password": OAuthSteps.ENTER_PASSWORD,
            "click_continue": OAuthSteps.CLICK_CONTINUE,
            "click_continue_if_present": OAuthSteps.CLICK_CONTINUE,
            "click_signin": OAuthSteps.CLICK_SIGNIN,
            "click_allow": OAuthSteps.CLICK_ALLOW,
            "verify_login_transition": ("verify_login", "Verifying login transition"),
            "third_party_auth": ("third_party_auth", "Completing third-party authentication"),
        }

        return step_map.get(step)

    async def _fill_email(self, page, config: FlowConfig):
        """Fill email field."""
        selector = config.selectors.get("email", "#email")
        
        # Try primary selector first
        if await self.wait_for_selector_safe(page, selector, timeout=2000, step_name="fill_email"):
            await page.fill(selector, self.email)
            await asyncio.sleep(config.timing["input_fill"])
            return
        
        # Fallback: Try by accessible name
        fallback_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[placeholder*="email" i]',
            'input[aria-label*="email" i]',
        ]
        
        for fallback in fallback_selectors:
            try:
                element = await page.query_selector(fallback)
                if element and await element.is_visible():
                    await page.fill(fallback, self.email)
                    await asyncio.sleep(config.timing["input_fill"])
                    self.logger.debug(f"Filled email using fallback selector: {fallback}")
                    return
            except Exception:
                continue
        
        self.logger.warning("Could not find email field with any selector", emoji="⚠️")

    async def _fill_password(self, page, config: FlowConfig):
        """Fill password field."""
        selector = config.selectors.get("password", "#password")
        
        # Try primary selector first
        if await self.wait_for_selector_safe(page, selector, timeout=2000, step_name="fill_password"):
            await page.fill(selector, self.password)
            await asyncio.sleep(config.timing["input_fill"])
            return
        
        # Fallback: Try by type and other attributes
        fallback_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[placeholder*="password" i]',
            'input[aria-label*="password" i]',
        ]
        
        for fallback in fallback_selectors:
            try:
                element = await page.query_selector(fallback)
                if element and await element.is_visible():
                    await page.fill(fallback, self.password)
                    await asyncio.sleep(config.timing["input_fill"])
                    self.logger.debug(f"Filled password using fallback selector: {fallback}")
                    return
            except Exception:
                continue
        
        self.logger.warning("Could not find password field with any selector", emoji="⚠️")

    async def _click_signin(self, page, config: FlowConfig):
        """Click sign in button."""
        selector = config.selectors.get("signin_button", 'button[type="submit"]')
        if await self.wait_for_selector_safe(page, selector, step_name="click_signin"):
            self._last_url_before_signin = page.url
            await page.click(selector)
            await page.wait_for_load_state("networkidle", timeout=10000)
            await asyncio.sleep(config.timing["navigation"])
            self._last_url_after_signin = page.url

    async def _verify_login_transition(self, page, config: FlowConfig) -> bool:
        """Allow adapters to verify that the login submit advanced the flow."""
        return True

    async def _click_allow(self, page, config: FlowConfig):
        """Click allow/consent button."""
        selector = config.selectors.get(
            "allow_button",
            (
                "button:has-text('Allow access'), "
                "button:has-text('Allow Access'), "
                "button:has-text('Allow'), button:has-text('Authorize'), "
                'button:has-text(\'Continue\'), button[value="approve"][type="submit"]'
            ),
        )
        options = config.options or {}
        consent_mode = str(options.get("consent_mode", "required")).lower()
        optional_timeout = int(options.get("allow_optional_timeout", 5000))
        enabled_timeout = int(
            options.get("allow_enabled_timeout", max(optional_timeout, 10000))
        )

        if consent_mode == "skip":
            if self.debug:
                print("Skipping consent step (consent_mode=skip).")
            return

        if consent_mode == "optional":
            try:
                await page.wait_for_selector(selector, timeout=optional_timeout)
            except Exception:
                if self.debug:
                    print(
                        "Consent button not found; continuing because consent is optional."
                    )
                return
        else:
            if not await self.wait_for_selector_safe(
                page,
                selector,
                timeout=max(optional_timeout, 15000),
                step_name="click_allow_wait",
            ):
                return

        enabled_selector = f"{selector}:not([disabled])"
        await asyncio.sleep(config.timing["allow_enable"])

        if consent_mode == "optional":
            try:
                await page.wait_for_selector(enabled_selector, timeout=enabled_timeout)
            except Exception:
                if self.debug:
                    print(
                        "Consent button never enabled; continuing because consent is optional."
                    )
                return
        else:
            if not await self.wait_for_selector_safe(
                page,
                enabled_selector,
                timeout=enabled_timeout,
                step_name="click_allow_enabled",
            ):
                return

        await page.click(selector)
        await asyncio.sleep(config.timing["navigation"] + 2)

    async def _click_continue_if_present(self, page, config: FlowConfig):
        """Click 'Continue' button if present (for two-step login forms)."""
        selector = config.selectors.get("continue_button", "button:has-text('Continue')")
        
        try:
            # Check if continue button exists (short timeout)
            element = await page.wait_for_selector(selector, timeout=2000)
            if element and await element.is_visible():
                self.logger.debug("Found Continue button, clicking...", emoji="👆")
                await page.click(selector)
                # Wait for password field to appear
                await asyncio.sleep(config.timing.get("navigation", 2.0))
                self.logger.debug("Clicked Continue, waiting for password field")
        except Exception:
            # No continue button found - this is fine, might be single-step form
            self.logger.debug("No Continue button found, proceeding...")
            pass
    
    async def _third_party_auth(self, page, config: FlowConfig):
        """Handle third-party authentication (Google, GitHub, etc.)."""
        # Override in subclasses
        pass


class AuthKitStandardFlow(OAuthFlowAdapter):
    """AuthKit standard email/password flow."""

    def __init__(
        self,
        email: str,
        password: str,
        *,
        consent_mode: str = "optional",
        max_login_attempts: int = 2,
        login_field_selector: Optional[str] = None,
        post_signin_grace: float = 2.0,
        allow_optional_timeout: int = 7000,
        debug: bool = False,
    ):
        super().__init__(email, password, debug)
        mode = str(consent_mode).lower()
        if mode not in {"required", "optional", "skip"}:
            raise ValueError(
                "consent_mode must be one of 'required', 'optional', or 'skip'"
            )
        self.consent_mode = mode
        self.max_login_attempts = max(1, int(max_login_attempts))
        self.login_field_selector = login_field_selector or "#email"
        self.post_signin_grace = float(post_signin_grace)
        self.allow_optional_timeout = int(allow_optional_timeout)

    def get_config(self) -> FlowConfig:
        steps = [
            "fill_email",
            "click_continue_if_present",  # New step for two-step forms
            "fill_password",
            "click_signin",
            "verify_login_transition",
        ]
        if self.consent_mode != "skip":
            steps.append("click_allow")

        return FlowConfig(
            name="authkit_standard",
            selectors={
                "email": "#email",
                "password": "#password",
                "continue_button": "button:has-text('Continue'), button:has-text('Next')",
                "signin_button": 'button[type="submit"]',
                "allow_button": (
                    "button:has-text('Allow access'), "
                    "button:has-text('Allow Access'), "
                    "button:has-text('Allow'), button:has-text('Authorize'), "
                    'button:has-text(\'Continue\'), button[value="approve"][type="submit"]'
                ),
            },
            steps=steps,
            options={
                "consent_mode": self.consent_mode,
                "allow_optional_timeout": self.allow_optional_timeout,
                "max_login_attempts": self.max_login_attempts,
                "login_field_selector": self.login_field_selector,
                "post_signin_grace": self.post_signin_grace,
            },
        )

    async def _verify_login_transition(self, page, config: FlowConfig) -> bool:
        login_selector = config.options.get(
            "login_field_selector"
        ) or config.selectors.get("email")
        post_signin_grace = float(config.options.get("post_signin_grace", 2.0))
        max_attempts = int(config.options.get("max_login_attempts", 1))

        if post_signin_grace > 0:
            await asyncio.sleep(post_signin_grace)

        if await self._login_transition_detected(page, login_selector):
            return True

        for attempt in range(2, max_attempts + 1):
            print(
                f"⚠️  AuthKit login did not advance; retrying {attempt}/{max_attempts}..."
            )
            await self._fill_email(page, config)
            await self._fill_password(page, config)
            await self._click_signin(page, config)

            if post_signin_grace > 0:
                await asyncio.sleep(post_signin_grace)

            if await self._login_transition_detected(page, login_selector):
                return True

        print("❌ AuthKit login failed to progress after retries.")
        await self.dump_page_state(page, "authkit_login_retry_exhausted")
        return False

    async def _check_for_invalid_credentials(self, page) -> bool:
        """Check if invalid credentials error is displayed."""
        try:
            # Check accessibility tree for error message
            tree = await page.accessibility.snapshot()
            if tree:
                tree_str = json.dumps(tree)
                if "Invalid login credentials" in tree_str or "invalid credentials" in tree_str.lower():
                    return True
            
            # Also check HTML content
            html = await page.content()
            if "Invalid login credentials" in html or "invalid credentials" in html.lower():
                return True
                
            # Check for common error selectors
            error_selectors = [
                "[role='alert']",
                ".error-message",
                ".alert-error",
                "[data-testid='error']"
            ]
            
            for selector in error_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        if text and ("invalid" in text.lower() and "credential" in text.lower()):
                            return True
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug("Error checking for invalid credentials", error=str(e))
        
        return False

    async def _login_transition_detected(
        self,
        page,
        login_selector: Optional[str],
    ) -> bool:
        """Determine if the AuthKit login page advanced after submitting credentials."""
        # Check for invalid credentials first
        if await self._check_for_invalid_credentials(page):
            raise InvalidCredentialsError("Invalid login credentials detected")
        
        if self._last_url_before_signin and self._last_url_after_signin:
            if self._last_url_after_signin != self._last_url_before_signin:
                return True

        if not login_selector:
            return False

        try:
            element = await page.query_selector(login_selector)
        except Exception:
            return True

        if not element:
            return True

        try:
            is_visible = await element.is_visible()
        except Exception:
            return True

        return not is_visible


class AuthKitAdaptiveFlow(AuthKitStandardFlow):
    """AuthKit flow that retries login and treats consent as optional by default."""

    def __init__(
        self,
        email: str,
        password: str,
        *,
        max_login_attempts: int = 3,
        post_signin_grace: float = 2.0,
        allow_optional_timeout: int = 7000,
        debug: bool = False,
    ):
        super().__init__(
            email,
            password,
            consent_mode="optional",
            max_login_attempts=max_login_attempts,
            post_signin_grace=post_signin_grace,
            allow_optional_timeout=allow_optional_timeout,
            debug=debug,
        )


class AuthKitStandaloneConnectFlow(OAuthFlowAdapter):
    """AuthKit standalone connect flow (3rd party providers)."""

    def __init__(
        self,
        email: str,
        password: str,
        provider: str = "google",
        *,
        consent_mode: str = "optional",
        debug: bool = False,
    ):
        super().__init__(email, password, debug)
        self.provider = provider
        mode = str(consent_mode).lower()
        if mode not in {"required", "optional", "skip"}:
            raise ValueError(
                "consent_mode must be one of 'required', 'optional', or 'skip'"
            )
        self.consent_mode = mode

    def get_config(self) -> FlowConfig:
        steps = ["third_party_auth"]
        if self.consent_mode != "skip":
            steps.append("click_allow")

        return FlowConfig(
            name=f"authkit_standalone_{self.provider}",
            selectors={
                "provider_button": f'button[data-provider="{self.provider}"]',
                "google_email": 'input[type="email"]',
                "google_password": 'input[type="password"]',
                "google_next": "#identifierNext",
                "google_submit": "#passwordNext",
            },
            steps=steps,
            options={
                "consent_mode": self.consent_mode,
                "allow_optional_timeout": 8000,
            },
        )

    async def _third_party_auth(self, page, config: FlowConfig):
        """Handle Google/GitHub/etc authentication."""
        if self.provider == "google":
            await self._google_auth(page, config)
        elif self.provider == "github":
            await self._github_auth(page, config)
        else:
            print(f"⚠️  Unsupported provider: {self.provider}")

    async def _google_auth(self, page, config: FlowConfig):
        """Google OAuth flow."""
        # Click Google sign in button
        provider_btn = config.selectors["provider_button"]
        if await self.wait_for_selector_safe(
            page, provider_btn, step_name="google_provider"
        ):
            await page.click(provider_btn)
            await asyncio.sleep(2)

        # Fill email
        email_selector = config.selectors["google_email"]
        if await self.wait_for_selector_safe(
            page, email_selector, step_name="google_email"
        ):
            await page.fill(email_selector, self.email)
            await page.click(config.selectors["google_next"])
            await asyncio.sleep(2)

        # Fill password
        password_selector = config.selectors["google_password"]
        if await self.wait_for_selector_safe(
            page, password_selector, step_name="google_password"
        ):
            await page.fill(password_selector, self.password)
            await page.click(config.selectors["google_submit"])
            await asyncio.sleep(3)

    async def _github_auth(self, page, config: FlowConfig):
        """GitHub OAuth flow."""
        # Click GitHub sign in button
        provider_btn = 'button[data-provider="github"]'
        if await self.wait_for_selector_safe(
            page, provider_btn, step_name="github_provider"
        ):
            await page.click(provider_btn)
            await asyncio.sleep(2)

        # Fill GitHub credentials
        if await self.wait_for_selector_safe(
            page, "#login_field", step_name="github_login"
        ):
            await page.fill("#login_field", self.email)
            await page.fill("#password", self.password)
            await page.click('input[type="submit"]')
            await asyncio.sleep(3)


class GoogleOAuthFlow(OAuthFlowAdapter):
    """Direct Google OAuth flow (not via AuthKit)."""

    def get_config(self) -> FlowConfig:
        return FlowConfig(
            name="google_direct",
            selectors={
                "email": 'input[type="email"]',
                "email_next": "#identifierNext",
                "password": 'input[type="password"]',
                "password_next": "#passwordNext",
                "allow_button": 'button[data-action="allow"]',
            },
            steps=[
                "fill_email",
                "click_next_email",
                "fill_password",
                "click_next_password",
                "click_allow",
            ],
        )

    async def _click_next_email(self, page, config: FlowConfig):
        """Click next after email."""
        await page.click(config.selectors["email_next"])
        await asyncio.sleep(2)

    async def _click_next_password(self, page, config: FlowConfig):
        """Click next after password."""
        await page.click(config.selectors["password_next"])
        await asyncio.sleep(3)


class GitHubOAuthFlow(OAuthFlowAdapter):
    """Direct GitHub OAuth flow."""

    def get_config(self) -> FlowConfig:
        return FlowConfig(
            name="github_direct",
            selectors={
                "email": "#login_field",
                "password": "#password",
                "signin_button": 'input[type="submit"]',
                "authorize_button": 'button[name="authorize"]',
            },
            steps=["fill_email", "fill_password", "click_signin", "click_authorize"],
        )

    async def _click_authorize(self, page, config: FlowConfig):
        """Click authorize button."""
        selector = config.selectors.get("authorize_button", 'button[name="authorize"]')
        if await self.wait_for_selector_safe(
            page, selector, step_name="github_authorize"
        ):
            await page.click(selector)
            await asyncio.sleep(3)


class CustomOAuthFlow(OAuthFlowAdapter):
    """
    Custom OAuth flow with configurable selectors.

    Usage:
        config = FlowConfig(
            name="my_custom_flow",
            selectors={'email': '#username', 'password': '#pwd', ...},
            steps=["fill_email", "fill_password", "click_signin"]
        )
        adapter = CustomOAuthFlow(email, password, config)
    """

    def __init__(
        self, email: str, password: str, config: FlowConfig, debug: bool = False
    ):
        super().__init__(email, password, debug)
        self.custom_config = config

    def get_config(self) -> FlowConfig:
        return self.custom_config


# Factory for creating adapters
class OAuthFlowFactory:
    """Factory for creating OAuth flow adapters."""

    _adapters = {
        "authkit": AuthKitStandardFlow,
        "authkit_standard": AuthKitStandardFlow,
        "authkit_adaptive": AuthKitAdaptiveFlow,
        "authkit_connect": AuthKitStandaloneConnectFlow,
        "google": GoogleOAuthFlow,
        "github": GitHubOAuthFlow,
    }

    @classmethod
    def create(
        cls, provider: str, email: str, password: str, debug: bool = False, **kwargs
    ) -> OAuthFlowAdapter:
        """
        Create an OAuth flow adapter.

        Args:
            provider: Provider name (authkit, google, github, etc.)
            email: User email
            password: User password
            debug: Enable debug mode (HTML dumps on failures)
            **kwargs: Additional provider-specific arguments

        Returns:
            OAuthFlowAdapter instance

        Example:
            # AuthKit standard
            adapter = OAuthFlowFactory.create('authkit', email, password)

            # AuthKit with Google
            adapter = OAuthFlowFactory.create('authkit_connect', email, password, provider='google')

            # Direct Google
            adapter = OAuthFlowFactory.create('google', email, password, debug=True)
        """
        adapter_class = cls._adapters.get(provider.lower())

        if not adapter_class:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Available: {', '.join(cls._adapters.keys())}"
            )

        return adapter_class(email, password, debug=debug, **kwargs)

    @classmethod
    def register(cls, name: str, adapter_class: type):
        """Register a custom adapter."""
        cls._adapters[name] = adapter_class

    @classmethod
    def list_providers(cls) -> list[str]:
        """List available providers."""
        return list(cls._adapters.keys())


def create_oauth_adapter(
    provider: str = "authkit",
    email: str = "",
    password: str = "",
    debug: bool = False,
    **kwargs,
) -> OAuthFlowAdapter:
    """
    Convenience function to create OAuth adapter.

    Args:
        provider: Provider name (default: authkit)
        email: User email
        password: User password
        debug: Enable debug mode with HTML dumps
        **kwargs: Provider-specific arguments

    Returns:
        OAuthFlowAdapter instance
    """
    return OAuthFlowFactory.create(provider, email, password, debug, **kwargs)
