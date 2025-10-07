"""
OAuth Authentication Helper

Provides automated OAuth login using Playwright for Atoms MCP testing.
"""

import asyncio
import os
from typing import Optional


# Default test credentials
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")


async def automate_oauth_login_with_retry(oauth_url: str, vercel_log_file: Optional[str] = None, max_retries: int = 3) -> bool:
    """Automate OAuth with retry logic (silent mode)."""
    for attempt in range(1, max_retries + 1):
        try:
            result = await automate_oauth_login(oauth_url, vercel_log_file)
            if result:
                return True

            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            error_msg = str(e)
            if "502" in error_msg or "503" in error_msg or "530" in error_msg:
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return False
            else:
                raise

    return False


async def automate_oauth_login(oauth_url: str, vercel_log_file: Optional[str] = None) -> bool:
    """Automate OAuth login with detailed progress bar for each step."""
    try:
        from playwright.async_api import async_playwright
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    except ImportError:
        return False

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[green]{task.completed}/{task.total}"),
        ) as progress:
            oauth_task = progress.add_task("[cyan]🔐 OAuth Flow", total=6)

            async with async_playwright() as p:
                # Step 1: Launch browser
                progress.update(oauth_task, description="[cyan]Step 1/6: Launching browser")
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                progress.advance(oauth_task)
                await asyncio.sleep(0.3)

                # Step 2: Navigate to OAuth page
                progress.update(oauth_task, description="[cyan]Step 2/6: Navigating to OAuth page")
                await page.goto(oauth_url)
                await asyncio.sleep(1)
                progress.advance(oauth_task)

                # Step 3: Fill credentials
                progress.update(oauth_task, description="[cyan]Step 3/6: Entering credentials")
                await page.fill("#email", TEST_EMAIL)
                await asyncio.sleep(0.3)
                await page.fill("#password", TEST_PASSWORD)
                await asyncio.sleep(0.3)
                progress.advance(oauth_task)

                # Step 4: Click Sign in
                progress.update(oauth_task, description="[cyan]Step 4/6: Clicking Sign in")
                await page.click('button[type="submit"]')
                await asyncio.sleep(2)
                progress.advance(oauth_task)

                # Step 5: Click Allow
                progress.update(oauth_task, description="[cyan]Step 5/6: Authorizing access")
                try:
                    allow_button = 'button[value="approve"][type="submit"]:not([disabled])'
                    await page.wait_for_selector(allow_button, timeout=8000)
                    await page.click(allow_button)
                    await asyncio.sleep(1)
                except Exception:
                    pass
                progress.advance(oauth_task)

                # Step 6: Wait for callback
                progress.update(oauth_task, description="[cyan]Step 6/6: Completing OAuth callback")
                await asyncio.sleep(3)
                progress.advance(oauth_task)

                await browser.close()
                progress.update(oauth_task, description="[green]✅ OAuth completed successfully")
                return True

    except Exception as e:
        print(f"❌ OAuth failed: {e}")
        return False
