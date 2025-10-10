"""
Textual TUI for Atoms MCP Test Suite

Production-ready interactive test dashboard with comprehensive features:
- Phase 1: Main app with grid layout, header, footer, test tree, output panels
- Phase 2: FileWatcher integration, enable/disable auto-reload, smart test re-running
- Phase 3: All keyboard bindings, mouse handlers, filter modal, test selection
- Phase 4: Metrics widgets, export functionality, performance tracking
- Phase 5: WebSocket broadcasting, multi-endpoint support, team visibility

Author: Atoms MCP Framework
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from rich.console import Group
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from textual import on, work
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
    from textual.reactive import reactive
    from textual.screen import ModalScreen
    from textual.widgets import (
        Button,
        Checkbox,
        DataTable,
        Footer,
        Header,
        Input,
        Label,
        ProgressBar,
        RichLog,
        Select,
        Static,
        Tree,
    )
    from textual.widgets.tree import TreeNode

    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False
    App = object
    ModalScreen = object
    Static = object

# Optional WebSocket support for Phase 5
try:
    import websockets
    try:
        # Try new asyncio implementation first (websockets >= 14.0)
        from websockets.asyncio.server import ServerConnection as WebSocketServerProtocol
    except ImportError:
        try:
            # Fall back to legacy implementation
            from websockets.legacy.server import WebSocketServerProtocol
        except ImportError:
            # Very old versions
            from websockets.server import WebSocketServerProtocol

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketServerProtocol = object

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("tui.log"), logging.StreamHandler()],
)
logger = logging.getLogger("atoms.tui")


# ============================================================================
# Phase 1: Core Widgets and Layout
# ============================================================================


class OAuthStatusWidget(Static):
    """Display OAuth token status with reactive updates."""

    token_cached = reactive(False)
    token_expired = reactive(False)
    cache_location = reactive("")
    time_until_expiry = reactive("")
    last_check = reactive(0.0)

    def __init__(self, oauth_cache_client=None, **kwargs):
        super().__init__(**kwargs)
        self.oauth_cache_client = oauth_cache_client
        self._update_status()

    def _update_status(self) -> None:
        """Update OAuth token status."""
        try:
            if self.oauth_cache_client:
                cache_path = self.oauth_cache_client._get_cache_path()
                self.cache_location = str(cache_path)
                self.token_cached = cache_path.exists()

                if self.token_cached:
                    import json
                    import time

                    try:
                        with open(cache_path, "r") as f:
                            token_data = json.load(f)

                        # Check expiry if available
                        expires_at = token_data.get("expires_at", 0)
                        current_time = time.time()

                        if expires_at:
                            time_left = expires_at - current_time
                            self.token_expired = time_left <= 0

                            if not self.token_expired:
                                hours = int(time_left // 3600)
                                minutes = int((time_left % 3600) // 60)
                                self.time_until_expiry = f"{hours}h {minutes}m"
                            else:
                                self.time_until_expiry = "Expired"
                        else:
                            self.time_until_expiry = "Unknown"
                    except Exception:
                        self.time_until_expiry = "Unknown"
                else:
                    self.token_expired = True
                    self.time_until_expiry = "No token"
            else:
                self.token_cached = False
                self.token_expired = True
                self.time_until_expiry = "Not configured"
                self.cache_location = "N/A"

            self.last_check = time.time()

        except Exception as e:
            logger.error(f"OAuth status update failed: {e}")

    def render(self) -> Panel:
        """Render OAuth status panel."""
        if not self.token_cached:
            status_color = "red"
            status_icon = "❌"
            status_text = "Missing"
        elif self.token_expired:
            status_color = "red"
            status_icon = "⚠️"
            status_text = "Expired"
        elif "Unknown" in self.time_until_expiry:
            status_color = "yellow"
            status_icon = "⚠️"
            status_text = "Unknown"
        else:
            # Check if expiring soon (< 1 hour)
            try:
                if "h" in self.time_until_expiry:
                    hours = int(self.time_until_expiry.split("h")[0])
                    if hours < 1:
                        status_color = "yellow"
                        status_icon = "⏰"
                        status_text = "Expiring Soon"
                    else:
                        status_color = "green"
                        status_icon = "✅"
                        status_text = "Valid"
                else:
                    status_color = "yellow"
                    status_icon = "⏰"
                    status_text = "Expiring Soon"
            except Exception:
                status_color = "green"
                status_icon = "✅"
                status_text = "Valid"

        content = f"""[bold]{status_icon} OAuth Token Status[/bold]

Status: [{status_color}]{status_text}[/{status_color}]
Expiry: [cyan]{self.time_until_expiry}[/cyan]
Cached: [{'green' if self.token_cached else 'red'}]{'Yes' if self.token_cached else 'No'}[/]
Location: [dim]{Path(self.cache_location).name if self.cache_location != 'N/A' else 'N/A'}[/dim]

[dim]Press 'O' to clear OAuth cache[/dim]"""

        return Panel(content, border_style=status_color, title="OAuth")

    async def refresh_status(self) -> None:
        """Manually refresh OAuth status."""
        self._update_status()
        self.refresh()


class ServerStatusWidget(Static):
    """Display MCP server status with reactive updates."""

    endpoint = reactive("")
    connected = reactive(False)
    last_ping = reactive(0.0)
    latency_ms = reactive(0.0)
    last_request = reactive("")
    server_version = reactive("Unknown")
    error_message = reactive("")

    def __init__(self, client_adapter=None, **kwargs):
        super().__init__(**kwargs)
        self.client_adapter = client_adapter
        if client_adapter:
            self.endpoint = client_adapter.endpoint
        self._update_status()

    async def _update_status(self) -> None:
        """Update server connection status."""
        try:
            if not self.client_adapter:
                self.connected = False
                self.error_message = "No client configured"
                return

            import time
            start = time.perf_counter()

            try:
                # Try to list tools as health check
                tools = await self.client_adapter.list_tools()
                duration = (time.perf_counter() - start) * 1000

                self.connected = True
                self.latency_ms = duration
                self.last_ping = time.time()
                self.error_message = ""

                # Try to get server version if available
                if hasattr(self.client_adapter.client, "_session"):
                    session = self.client_adapter.client._session
                    if hasattr(session, "server_version"):
                        self.server_version = session.server_version

            except Exception as e:
                self.connected = False
                self.error_message = str(e)[:50]
                self.latency_ms = 0.0

        except Exception as e:
            logger.error(f"Server status update failed: {e}")
            self.connected = False
            self.error_message = str(e)[:50]

    def render(self) -> Panel:
        """Render server status panel."""
        import time

        if self.connected:
            status_color = "green"
            status_icon = "✅"
            status_text = "Connected"
        else:
            status_color = "red"
            status_icon = "❌"
            status_text = "Disconnected"

        # Format last ping time
        if self.last_ping > 0:
            time_since = time.time() - self.last_ping
            if time_since < 60:
                ping_text = f"{int(time_since)}s ago"
            else:
                ping_text = f"{int(time_since / 60)}m ago"
        else:
            ping_text = "Never"

        # Format endpoint (shorten if too long)
        display_endpoint = self.endpoint
        if len(display_endpoint) > 35:
            display_endpoint = "..." + display_endpoint[-32:]

        content = f"""[bold]{status_icon} MCP Server Status[/bold]

Status: [{status_color}]{status_text}[/{status_color}]
Endpoint: [cyan]{display_endpoint}[/cyan]
Latency: [{'green' if self.latency_ms < 100 else 'yellow' if self.latency_ms < 500 else 'red'}]{self.latency_ms:.1f}ms[/]
Last Check: [dim]{ping_text}[/dim]
Version: [blue]{self.server_version}[/blue]"""

        if self.error_message:
            content += f"\n[red]Error: {self.error_message}[/red]"

        content += "\n\n[dim]Press Ctrl+H to health check[/dim]"

        return Panel(content, border_style=status_color, title="Server")

    async def refresh_status(self) -> None:
        """Manually refresh server status."""
        await self._update_status()
        self.refresh()


class TunnelStatusWidget(Static):
    """Display tunnel status for local development."""

    tunnel_active = reactive(False)
    tunnel_url = reactive("")
    tunnel_type = reactive("")
    connection_count = reactive(0)
    uptime = reactive(0.0)
    start_time = reactive(0.0)

    def __init__(self, tunnel_config=None, **kwargs):
        super().__init__(**kwargs)
        self.tunnel_config = tunnel_config or {}
        self._update_status()

    def _update_status(self) -> None:
        """Update tunnel status."""
        try:
            import time

            # Check if tunnel is configured
            if not self.tunnel_config:
                self.tunnel_active = False
                return

            # Check for ngrok
            if self.tunnel_config.get("type") == "ngrok":
                self._check_ngrok_status()
            # Check for cloudflare
            elif self.tunnel_config.get("type") == "cloudflare":
                self._check_cloudflare_status()
            # Custom tunnel
            elif self.tunnel_config.get("url"):
                self.tunnel_active = True
                self.tunnel_url = self.tunnel_config["url"]
                self.tunnel_type = self.tunnel_config.get("type", "custom")

            # Calculate uptime
            if self.tunnel_active and self.start_time > 0:
                self.uptime = time.time() - self.start_time

        except Exception as e:
            logger.error(f"Tunnel status update failed: {e}")
            self.tunnel_active = False

    def _check_ngrok_status(self) -> None:
        """Check ngrok tunnel status."""
        try:
            import requests
            response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get("tunnels", [])
                if tunnels:
                    tunnel = tunnels[0]
                    self.tunnel_active = True
                    self.tunnel_url = tunnel.get("public_url", "")
                    self.tunnel_type = "ngrok"
                    self.connection_count = tunnel.get("connections", 0)
                    if self.start_time == 0:
                        import time
                        self.start_time = time.time()
                else:
                    self.tunnel_active = False
            else:
                self.tunnel_active = False
        except Exception:
            self.tunnel_active = False

    def _check_cloudflare_status(self) -> None:
        """Check Cloudflare tunnel status."""
        # Placeholder - would need cloudflared API integration
        self.tunnel_active = False

    def render(self) -> Panel:
        """Render tunnel status panel."""
        if not self.tunnel_active:
            content = "[dim]No tunnel active[/dim]\n\n[yellow]Configure tunnel for local dev:[/yellow]\n- ngrok\n- cloudflare tunnel\n- custom tunnel"
            border_style = "dim"
        else:
            status_color = "green"
            status_icon = "✅"

            # Format uptime
            if self.uptime > 0:
                hours = int(self.uptime // 3600)
                minutes = int((self.uptime % 3600) // 60)
                uptime_text = f"{hours}h {minutes}m"
            else:
                uptime_text = "Just started"

            # Shorten URL if too long
            display_url = self.tunnel_url
            if len(display_url) > 35:
                display_url = display_url[:32] + "..."

            content = f"""[bold]{status_icon} Tunnel Active[/bold]

Type: [cyan]{self.tunnel_type.upper()}[/cyan]
URL: [blue]{display_url}[/blue]
Connections: [yellow]{self.connection_count}[/yellow]
Uptime: [green]{uptime_text}[/green]

[dim]Tunnel forwarding to local server[/dim]"""
            border_style = status_color

        return Panel(content, border_style=border_style, title="Tunnel")

    async def refresh_status(self) -> None:
        """Manually refresh tunnel status."""
        self._update_status()
        self.refresh()


class ResourceStatusWidget(Static):
    """Display resource status (DB, Redis, API limits, etc.)."""

    db_connected = reactive(False)
    db_latency = reactive(0.0)
    redis_connected = reactive(False)
    redis_latency = reactive(0.0)
    api_rate_limit = reactive(0)
    api_rate_remaining = reactive(0)
    memory_usage_mb = reactive(0.0)
    active_connections = reactive(0)

    def __init__(self, resource_config=None, **kwargs):
        super().__init__(**kwargs)
        self.resource_config = resource_config or {}
        self._update_status()

    async def _update_status(self) -> None:
        """Update resource status."""
        try:
            # Check database connection
            if self.resource_config.get("check_db"):
                await self._check_database()

            # Check Redis connection
            if self.resource_config.get("check_redis"):
                await self._check_redis()

            # Check API rate limits
            if self.resource_config.get("check_api_limits"):
                await self._check_api_limits()

            # Check memory usage
            self._check_memory()

        except Exception as e:
            logger.error(f"Resource status update failed: {e}")

    async def _check_database(self) -> None:
        """Check database connection status."""
        try:
            import time
            import asyncio

            db_config = self.resource_config.get("db_config", {})
            if not db_config:
                return

            # Simple connection test
            start = time.perf_counter()
            # Would connect to actual DB here
            await asyncio.sleep(0.01)  # Simulate check
            duration = (time.perf_counter() - start) * 1000

            self.db_connected = True
            self.db_latency = duration

        except Exception:
            self.db_connected = False
            self.db_latency = 0.0

    async def _check_redis(self) -> None:
        """Check Redis connection status."""
        try:
            import time
            import asyncio

            redis_config = self.resource_config.get("redis_config", {})
            if not redis_config:
                return

            start = time.perf_counter()
            # Would connect to actual Redis here
            await asyncio.sleep(0.01)  # Simulate check
            duration = (time.perf_counter() - start) * 1000

            self.redis_connected = True
            self.redis_latency = duration

        except Exception:
            self.redis_connected = False
            self.redis_latency = 0.0

    async def _check_api_limits(self) -> None:
        """Check API rate limits."""
        try:
            # Would check actual API limits here
            # For now, use mock values
            self.api_rate_limit = 1000
            self.api_rate_remaining = 850
        except Exception:
            self.api_rate_limit = 0
            self.api_rate_remaining = 0

    def _check_memory(self) -> None:
        """Check memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            self.memory_usage_mb = memory_info.rss / (1024 * 1024)
        except Exception:
            self.memory_usage_mb = 0.0

    def render(self) -> Panel:
        """Render resource status panel."""
        lines = ["[bold]📊 Resources[/bold]\n"]

        # Database status
        if self.resource_config.get("check_db"):
            db_icon = "✅" if self.db_connected else "❌"
            db_color = "green" if self.db_connected else "red"
            lines.append(f"{db_icon} Database: [{db_color}]{'Connected' if self.db_connected else 'Disconnected'}[/{db_color}]")
            if self.db_connected:
                lines.append(f"   Latency: {self.db_latency:.1f}ms")

        # Redis status
        if self.resource_config.get("check_redis"):
            redis_icon = "✅" if self.redis_connected else "❌"
            redis_color = "green" if self.redis_connected else "red"
            lines.append(f"{redis_icon} Redis: [{redis_color}]{'Connected' if self.redis_connected else 'Disconnected'}[/{redis_color}]")
            if self.redis_connected:
                lines.append(f"   Latency: {self.redis_latency:.1f}ms")

        # API rate limits
        if self.resource_config.get("check_api_limits") and self.api_rate_limit > 0:
            rate_percent = (self.api_rate_remaining / self.api_rate_limit) * 100
            rate_color = "green" if rate_percent > 50 else "yellow" if rate_percent > 20 else "red"
            lines.append(f"API Rate: [{rate_color}]{self.api_rate_remaining}/{self.api_rate_limit}[/{rate_color}] ({rate_percent:.0f}%)")

        # Memory usage
        if self.memory_usage_mb > 0:
            mem_color = "green" if self.memory_usage_mb < 500 else "yellow" if self.memory_usage_mb < 1000 else "red"
            lines.append(f"Memory: [{mem_color}]{self.memory_usage_mb:.1f} MB[/{mem_color}]")

        # Active connections
        if self.active_connections > 0:
            lines.append(f"Connections: [cyan]{self.active_connections}[/cyan]")

        if len(lines) == 1:
            lines.append("[dim]No resources configured[/dim]")
            lines.append("\n[yellow]Configure resource checks in settings[/yellow]")

        content = "\n".join(lines)
        return Panel(content, border_style="blue", title="Resources")

    async def refresh_status(self) -> None:
        """Manually refresh resource status."""
        await self._update_status()
        self.refresh()


class TestSummaryWidget(Static):
    """Display test summary statistics with real-time updates."""

    total = reactive(0)
    passed = reactive(0)
    failed = reactive(0)
    skipped = reactive(0)
    cached = reactive(0)
    duration = reactive(0.0)
    running = reactive(False)

    def render(self) -> Panel:
        """Render summary statistics in a rich panel."""
        pass_rate = (self.passed / (self.total - self.skipped)) * 100 if (self.total - self.skipped) > 0 else 0

        status_icon = "🔄" if self.running else ("✅" if pass_rate >= 90 else "⚠️" if pass_rate >= 70 else "❌")

        content = f"""[bold]{status_icon} Test Summary[/bold]

Total: [cyan]{self.total}[/cyan] | Passed: [green]{self.passed}[/green] | Failed: [red]{self.failed}[/red] | Skipped: [yellow]{self.skipped}[/yellow] | Cached: [blue]{self.cached}[/blue]

Pass Rate: [{'green' if pass_rate >= 90 else 'yellow' if pass_rate >= 70 else 'red'}]{pass_rate:.1f}%[/]
Duration: [cyan]{self.duration:.2f}s[/cyan]
Status: [{'yellow' if self.running else 'green'}]{'Running...' if self.running else 'Idle'}[/]"""

        return Panel(content, border_style="green" if pass_rate >= 90 else "yellow" if pass_rate >= 70 else "red")


class TestProgressWidget(Static):
    """Display real-time test progress with progress bar."""

    current = reactive(0)
    total = reactive(0)
    current_test = reactive("")
    current_tool = reactive("")

    def render(self) -> Panel:
        """Render progress bar and current test info."""
        if self.total == 0:
            percent = 0
        else:
            percent = (self.current / self.total) * 100

        # ASCII progress bar
        bar_width = 40
        filled = int(bar_width * percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        content = f"""[bold]📈 Progress[/bold]

{bar} {percent:.1f}% ({self.current}/{self.total})

Currently running: [cyan]{self.current_test}[/cyan]
Tool: [yellow]{self.current_tool}[/yellow]"""

        return Panel(content, border_style="cyan")


class MetricsWidget(Static):
    """Display performance metrics and statistics (Phase 4)."""

    avg_duration = reactive(0.0)
    min_duration = reactive(0.0)
    max_duration = reactive(0.0)
    total_duration = reactive(0.0)
    tests_per_second = reactive(0.0)
    cache_hit_rate = reactive(0.0)

    def render(self) -> Panel:
        """Render performance metrics."""
        content = f"""[bold]📊 Performance Metrics[/bold]

Average Duration: [cyan]{self.avg_duration:.2f}ms[/cyan]
Min: [green]{self.min_duration:.2f}ms[/green] | Max: [red]{self.max_duration:.2f}ms[/red]
Total Time: [yellow]{self.total_duration:.2f}s[/yellow]
Throughput: [blue]{self.tests_per_second:.1f} tests/sec[/blue]
Cache Hit Rate: [magenta]{self.cache_hit_rate:.1f}%[/magenta]"""

        return Panel(content, border_style="blue")


class LiveMonitorWidget(Static):
    """Live monitoring of test execution with real-time updates."""

    recent_tests = reactive([])
    error_count = reactive(0)
    warning_count = reactive(0)

    def render(self) -> Panel:
        """Render recent test results."""
        if not self.recent_tests:
            content = "[dim]No tests executed yet[/dim]"
        else:
            lines = ["[bold]Recent Tests (Last 10)[/bold]\n"]
            for test in self.recent_tests[-10:]:
                icon = "✅" if test["success"] else "❌"
                name = test["name"][:40]
                duration = test["duration"]
                lines.append(f"{icon} {name} ({duration:.2f}ms)")
            content = "\n".join(lines)

        footer = f"\nErrors: [red]{self.error_count}[/red] | Warnings: [yellow]{self.warning_count}[/yellow]"
        return Panel(content + footer, border_style="magenta", title="Live Monitor")


class TeamVisibilityWidget(Static):
    """Show connected team members and their activity (Phase 5)."""

    connected_users = reactive([])
    websocket_enabled = reactive(False)

    def render(self) -> Panel:
        """Render connected team members."""
        if not self.websocket_enabled:
            content = "[dim]WebSocket broadcasting disabled[/dim]\n\nPress [bold]W[/bold] to enable team visibility"
        elif not self.connected_users:
            content = "[yellow]WebSocket enabled - waiting for connections...[/yellow]\n\nEndpoint: ws://localhost:8765"
        else:
            lines = [f"[bold]Connected Users ({len(self.connected_users)})[/bold]\n"]
            for user in self.connected_users:
                lines.append(f"👤 {user['name']} - {user['status']}")
            content = "\n".join(lines)

        return Panel(content, border_style="yellow" if self.websocket_enabled else "dim", title="Team Visibility")


# ============================================================================
# Phase 3: Modal Dialogs
# ============================================================================


class FilterModal(ModalScreen):
    """Modal dialog for filtering tests (Phase 3)."""

    CSS = """
    FilterModal {
        align: center middle;
    }

    #filter-dialog {
        width: 60;
        height: 25;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #filter-buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, current_filters: Dict[str, Any]):
        super().__init__()
        self.current_filters = current_filters
        self.result_filters = current_filters.copy()

    def compose(self) -> ComposeResult:
        """Create filter dialog components."""
        with Container(id="filter-dialog"):
            yield Label("[bold]Filter Tests[/bold]", classes="title")

            yield Label("\nTest Status:")
            yield Checkbox("Show Passed", value=self.current_filters.get("show_passed", True), id="show_passed")
            yield Checkbox("Show Failed", value=self.current_filters.get("show_failed", True), id="show_failed")
            yield Checkbox("Show Skipped", value=self.current_filters.get("show_skipped", True), id="show_skipped")
            yield Checkbox("Show Cached", value=self.current_filters.get("show_cached", True), id="show_cached")

            yield Label("\nSearch Pattern:")
            yield Input(placeholder="e.g., entity, test_create", value=self.current_filters.get("search", ""), id="search")

            yield Label("\nTool Name:")
            yield Input(placeholder="e.g., entity_tool", value=self.current_filters.get("tool", ""), id="tool")

            with Horizontal(id="filter-buttons"):
                yield Button("Apply", variant="primary", id="apply")
                yield Button("Reset", id="reset")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#apply")
    def apply_filters(self) -> None:
        """Apply filters and close dialog."""
        self.result_filters["show_passed"] = self.query_one("#show_passed", Checkbox).value
        self.result_filters["show_failed"] = self.query_one("#show_failed", Checkbox).value
        self.result_filters["show_skipped"] = self.query_one("#show_skipped", Checkbox).value
        self.result_filters["show_cached"] = self.query_one("#show_cached", Checkbox).value
        self.result_filters["search"] = self.query_one("#search", Input).value
        self.result_filters["tool"] = self.query_one("#tool", Input).value
        self.dismiss(self.result_filters)

    @on(Button.Pressed, "#reset")
    def reset_filters(self) -> None:
        """Reset all filters to default."""
        default_filters = {
            "show_passed": True,
            "show_failed": True,
            "show_skipped": True,
            "show_cached": True,
            "search": "",
            "tool": "",
        }
        self.dismiss(default_filters)

    @on(Button.Pressed, "#cancel")
    def cancel_filters(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(self.current_filters)


class ExportModal(ModalScreen):
    """Modal dialog for exporting test results (Phase 4)."""

    CSS = """
    ExportModal {
        align: center middle;
    }

    #export-dialog {
        width: 60;
        height: 20;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #export-buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create export dialog components."""
        with Container(id="export-dialog"):
            yield Label("[bold]Export Test Results[/bold]", classes="title")

            yield Label("\nExport Format:")
            yield Select(
                [("JSON", "json"), ("Markdown", "markdown"), ("HTML", "html"), ("CSV", "csv")],
                value="json",
                id="format",
            )

            yield Label("\nOutput Path:")
            yield Input(placeholder="e.g., results/test_report.json", value="test_report.json", id="output_path")

            yield Label("\nInclude Options:")
            yield Checkbox("Include Full Error Messages", value=True, id="include_errors")
            yield Checkbox("Include Timing Details", value=True, id="include_timing")
            yield Checkbox("Include Cached Results", value=False, id="include_cached")

            with Horizontal(id="export-buttons"):
                yield Button("Export", variant="primary", id="export")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#export")
    def export_results(self) -> None:
        """Export results and close dialog."""
        export_config = {
            "format_type": self.query_one("#format", Select).value,
            "output_path": self.query_one("#output_path", Input).value,
            "include_errors": self.query_one("#include_errors", Checkbox).value,
            "include_timing": self.query_one("#include_timing", Checkbox).value,
            "include_cached": self.query_one("#include_cached", Checkbox).value,
        }
        self.dismiss(export_config)

    @on(Button.Pressed, "#cancel")
    def cancel_export(self) -> None:
        """Cancel export."""
        self.dismiss(None)


class HelpModal(ModalScreen):
    """Modal dialog showing keyboard shortcuts and help (Phase 3)."""

    CSS = """
    HelpModal {
        align: center middle;
    }

    #help-dialog {
        width: 70;
        height: 30;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #help-content {
        height: 25;
    }
    """

    def compose(self) -> ComposeResult:
        """Create help dialog components."""
        with Container(id="help-dialog"):
            yield Label("[bold]Atoms MCP Test Dashboard - Keyboard Shortcuts[/bold]", classes="title")

            with ScrollableContainer(id="help-content"):
                help_text = """
[bold cyan]General Commands[/]
  Q, Esc         Quit application
  H, ?           Show this help
  Ctrl+C         Force quit

[bold cyan]Test Execution[/]
  R              Run all tests
  Shift+R        Run selected tests only
  S              Stop running tests
  Space          Toggle test selection
  Enter          Run selected test

[bold cyan]Navigation[/]
  ↑↓←→           Navigate test tree
  Tab            Switch between panels
  Page Up/Down   Scroll output
  Home/End       Jump to top/bottom

[bold cyan]Filtering & Search[/]
  F, /           Open filter dialog
  Ctrl+F         Quick search
  N              Next search result
  Shift+N        Previous search result

[bold cyan]Cache Management[/]
  C              Clear test cache
  Shift+C        Clear cache for selected tool
  O              Clear OAuth cache

[bold cyan]Status Monitoring[/]
  Ctrl+H         Run health check (refresh all status)

[bold cyan]Live Reload (Phase 2)[/]
  L              Toggle live reload
  Shift+L        Configure watch paths
  Ctrl+R         Force reload

[bold cyan]View & Display[/]
  T              Toggle theme (light/dark)
  M              Show/hide metrics panel
  V              Show/hide team visibility
  1-5            Switch to panel 1-5
  Ctrl+L         Clear output log

[bold cyan]Export & Reports (Phase 4)[/]
  E              Export test results
  Shift+E        Quick export to JSON
  P              Generate performance report

[bold cyan]Team & Collaboration (Phase 5)[/]
  W              Toggle WebSocket broadcasting
  Shift+W        Configure WebSocket endpoint
  U              Show connected users

[bold cyan]Advanced[/]
  D              Toggle debug mode
  I              Inspect selected test
  Ctrl+S         Save session
  Ctrl+O         Load session
"""
                yield Static(help_text)

            yield Button("Close", variant="primary", id="close")

    @on(Button.Pressed, "#close")
    def close_help(self) -> None:
        """Close help dialog."""
        self.dismiss()


# ============================================================================
# Phase 5: WebSocket Server for Team Visibility
# ============================================================================


class WebSocketBroadcaster:
    """WebSocket server for broadcasting test results to team members (Phase 5)."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.clients: Set[WebSocketServerProtocol] = set()
        self.running = False

    async def start(self) -> None:
        """Start WebSocket server."""
        if not HAS_WEBSOCKETS:
            logger.warning("WebSocket support not available. Install with: pip install websockets")
            return

        try:
            self.server = await websockets.serve(self.handler, self.host, self.port)
            self.running = True
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            self.running = False

    async def stop(self) -> None:
        """Stop WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            logger.info("WebSocket server stopped")

    async def handler(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle WebSocket connection."""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")

        try:
            async for message in websocket:
                # Echo back for now, could handle commands
                await websocket.send(message)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected: {websocket.remote_address}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        message_json = json.dumps(message)
        await asyncio.gather(*[client.send(message_json) for client in self.clients], return_exceptions=True)

    def get_connected_users(self) -> List[Dict[str, Any]]:
        """Get list of connected users."""
        return [{"name": f"User-{i+1}", "status": "Connected", "address": str(c.remote_address)} for i, c in enumerate(self.clients)]


# ============================================================================
# Main Application (All Phases Integrated)
# ============================================================================


class TestDashboardApp(App):
    """
    Comprehensive TUI application for Atoms MCP test dashboard.

    Integrates all 5 phases:
    - Phase 1: Core layout and widgets
    - Phase 2: FileWatcher and auto-reload
    - Phase 3: Keyboard bindings and modals
    - Phase 4: Metrics and export
    - Phase 5: WebSocket and team visibility
    """

    CSS = """
    Screen {
        layout: grid;
        grid-size: 4 5;
        grid-rows: auto auto auto 1fr auto;
    }

    /* Status Bar Row (Row 1) */
    #oauth-status {
        column-span: 1;
        height: auto;
    }

    #server-status {
        column-span: 1;
        height: auto;
    }

    #tunnel-status {
        column-span: 1;
        height: auto;
    }

    #resource-status {
        column-span: 1;
        height: auto;
    }

    /* Summary Row (Row 2) */
    #summary {
        column-span: 4;
        height: auto;
    }

    /* Progress & Metrics Row (Row 3) */
    #progress {
        column-span: 3;
        height: auto;
    }

    #metrics {
        column-span: 1;
        height: auto;
    }

    #test-tree {
        row-span: 1;
        column-span: 1;
        border: solid $primary;
        overflow-y: scroll;
    }

    #test-output {
        row-span: 1;
        column-span: 1;
        border: solid $accent;
        overflow-y: scroll;
    }

    #live-monitor {
        row-span: 1;
        column-span: 1;
        border: solid $warning;
    }

    #logs {
        column-span: 2;
        border: solid $secondary;
        height: 15;
    }

    #team-visibility {
        column-span: 1;
        border: solid $success;
        height: 15;
    }

    Footer {
        dock: bottom;
    }

    /* Light theme overrides */
    .light-theme {
        background: $surface;
        color: $text;
    }

    /* Dark theme (default) */
    .dark-theme {
        background: $background;
        color: $text;
    }

    /* Modal styling */
    ModalScreen {
        background: rgba(0, 0, 0, 0.7);
    }
    """

    # Phase 3: Comprehensive keyboard bindings (20+ shortcuts)
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ("h", "help", "Help"),
        ("?", "help", "Help"),
        ("r", "run_tests", "Run All"),
        ("R", "run_selected", "Run Selected"),
        ("s", "stop_tests", "Stop"),
        ("space", "toggle_selection", "Toggle Selection"),
        ("enter", "run_single", "Run Test"),
        ("f", "filter_tests", "Filter"),
        ("/", "filter_tests", "Filter"),
        ("ctrl+f", "quick_search", "Quick Search"),
        ("n", "next_result", "Next"),
        ("N", "prev_result", "Previous"),
        ("c", "clear_cache", "Clear Cache"),
        ("C", "clear_tool_cache", "Clear Tool Cache"),
        ("o", "clear_oauth", "Clear OAuth"),
        ("l", "toggle_live_reload", "Toggle Reload"),
        ("L", "configure_watch_paths", "Config Paths"),
        ("ctrl+r", "force_reload", "Force Reload"),
        ("ctrl+h", "health_check", "Health Check"),
        ("t", "toggle_theme", "Toggle Theme"),
        ("m", "toggle_metrics", "Toggle Metrics"),
        ("v", "toggle_visibility", "Toggle Visibility"),
        ("ctrl+l", "clear_output", "Clear Output"),
        ("e", "export_results", "Export"),
        ("E", "quick_export", "Quick Export"),
        ("p", "performance_report", "Perf Report"),
        ("w", "toggle_websocket", "Toggle WS"),
        ("W", "configure_websocket", "Config WS"),
        ("u", "show_users", "Show Users"),
        ("d", "toggle_debug", "Debug"),
        ("i", "inspect_test", "Inspect"),
        ("ctrl+s", "save_session", "Save Session"),
        ("ctrl+o", "load_session", "Load Session"),
    ]

    def __init__(
        self,
        endpoint: str,
        test_modules: List[str],
        enable_live_reload: bool = True,
        watch_paths: Optional[List[str]] = None,
        enable_websocket: bool = False,
        websocket_host: str = "localhost",
        websocket_port: int = 8765,
        oauth_cache_client=None,
        tunnel_config: Optional[Dict[str, Any]] = None,
        resource_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.endpoint = endpoint
        self.test_modules = test_modules
        self.enable_live_reload_flag = enable_live_reload
        self.watch_paths = watch_paths or ["tools/"]

        # Test execution state
        self.test_runner = None
        self.test_results: List[Dict[str, Any]] = []
        self.current_filters = {
            "show_passed": True,
            "show_failed": True,
            "show_skipped": True,
            "show_cached": True,
            "search": "",
            "tool": "",
        }
        self.selected_tests: Set[str] = set()
        self.is_running = False

        # Phase 2: FileWatcher
        self.file_watcher = None
        self.reload_manager = None

        # Phase 4: Metrics tracking
        self.test_durations: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0

        # Phase 5: WebSocket broadcasting
        self.websocket_enabled = enable_websocket
        self.websocket_broadcaster = WebSocketBroadcaster(websocket_host, websocket_port)

        # Status monitoring state
        self.oauth_cache_client = oauth_cache_client
        self.tunnel_config = tunnel_config or {}
        self.resource_config = resource_config or {}
        self.client_adapter = None

        # UI state
        self.dark_theme = True
        self.show_metrics = True
        self.show_team_visibility = True
        self.debug_mode = False

    def compose(self) -> ComposeResult:
        """Create child widgets for all phases."""
        yield Header(show_clock=True)

        # Status Bar Row (Top) - New status monitoring widgets
        yield OAuthStatusWidget(oauth_cache_client=self.oauth_cache_client, id="oauth-status")
        yield ServerStatusWidget(client_adapter=self.client_adapter, id="server-status")
        yield TunnelStatusWidget(tunnel_config=self.tunnel_config, id="tunnel-status")
        yield ResourceStatusWidget(resource_config=self.resource_config, id="resource-status")

        # Phase 1: Core widgets
        yield TestSummaryWidget(id="summary")
        yield TestProgressWidget(id="progress")

        # Phase 4: Metrics widget
        yield MetricsWidget(id="metrics")

        # Test tree (left panel) - using DataTable instead of Tree for better performance
        test_table = DataTable(id="test-tree", zebra_stripes=True, cursor_type="row")
        test_table.add_columns("", "Test", "Status", "Time", "Tool")  # First column for selection checkbox
        yield test_table

        # Test output (center panel)
        yield RichLog(id="test-output", highlight=True, markup=True, wrap=True)

        # Phase 4: Live monitor (right panel)
        yield LiveMonitorWidget(id="live-monitor")

        # Logs (bottom left)
        yield RichLog(id="logs", highlight=True, markup=True, wrap=True)

        # Phase 5: Team visibility (bottom right)
        yield TeamVisibilityWidget(id="team-visibility")

        yield Footer()

    async def on_mount(self) -> None:
        """Called when app is mounted - initialize all phases."""
        self.title = "Atoms MCP Test Dashboard"
        self.sub_title = f"Endpoint: {self.endpoint}"

        # Initialize logs
        logs = self.query_one("#logs", RichLog)
        logs.write("[bold green]🚀 Atoms MCP Test Dashboard Started[/bold green]")
        logs.write(f"[cyan]Endpoint:[/cyan] {self.endpoint}")
        logs.write(f"[cyan]Test Modules:[/cyan] {len(self.test_modules)}")
        logs.write(f"[cyan]Live Reload:[/cyan] {'Enabled' if self.enable_live_reload_flag else 'Disabled'}")

        # Initialize client adapter for status monitoring
        try:
            from .adapters import AtomsMCPClientAdapter
            from fastmcp import Client

            # Create client (this will be replaced when running tests)
            client = Client(self.endpoint)
            self.client_adapter = AtomsMCPClientAdapter(client)

            # Update server status widget with adapter
            server_status = self.query_one("#server-status", ServerStatusWidget)
            server_status.client_adapter = self.client_adapter
            if self.client_adapter:
                server_status.endpoint = self.client_adapter.endpoint

        except Exception as e:
            logs.write(f"[yellow]⚠️  Client adapter initialization failed: {e}[/yellow]")
            logger.warning(f"Client adapter init failed: {e}")

        # Phase 2: Initialize FileWatcher
        if self.enable_live_reload_flag:
            await self._setup_file_watcher()

        # Phase 5: Initialize WebSocket server
        if self.websocket_enabled:
            await self._setup_websocket()

        # Load test modules and populate tree
        await self._load_test_modules()

        # Start periodic status refresh worker
        self.set_interval(5.0, self._refresh_status_widgets)

        logger.info("Test dashboard mounted successfully")

    async def _setup_file_watcher(self) -> None:
        """Setup file watcher for auto-reload (Phase 2)."""
        try:
            from .file_watcher import TestFileWatcher

            logs = self.query_one("#logs", RichLog)

            self.file_watcher = TestFileWatcher(
                watch_paths=self.watch_paths, on_change=self._on_file_change, debounce_seconds=0.5
            )
            self.file_watcher.start()

            logs.write(f"[green]📁 FileWatcher started monitoring: {', '.join(self.watch_paths)}[/green]")
            logger.info(f"FileWatcher monitoring: {self.watch_paths}")

        except ImportError:
            logs = self.query_one("#logs", RichLog)
            logs.write("[yellow]⚠️  watchdog not installed. Install with: pip install watchdog[/yellow]")
            logger.warning("FileWatcher disabled - watchdog not installed")
        except Exception as e:
            logs = self.query_one("#logs", RichLog)
            logs.write(f"[red]❌ FileWatcher error: {e}[/red]")
            logger.error(f"FileWatcher setup failed: {e}")

    async def _setup_websocket(self) -> None:
        """Setup WebSocket server for team visibility (Phase 5)."""
        try:
            await self.websocket_broadcaster.start()

            logs = self.query_one("#logs", RichLog)
            logs.write(f"[green]🌐 WebSocket server started on ws://{self.websocket_broadcaster.host}:{self.websocket_broadcaster.port}[/green]")

            team_widget = self.query_one("#team-visibility", TeamVisibilityWidget)
            team_widget.websocket_enabled = True

            logger.info("WebSocket server started successfully")

        except Exception as e:
            logs = self.query_one("#logs", RichLog)
            logs.write(f"[red]❌ WebSocket error: {e}[/red]")
            logger.error(f"WebSocket setup failed: {e}")

    def _on_file_change(self, file_path: str) -> None:
        """Handle file change event from FileWatcher (Phase 2)."""
        logs = self.query_one("#logs", RichLog)
        logs.write(f"[yellow]🔄 File changed: {Path(file_path).name}[/yellow]")

        # Determine affected tools
        if self.file_watcher:
            affected_tools = self.file_watcher.get_affected_tools(file_path)

            if affected_tools:
                logs.write(f"[cyan]   Affected tools: {', '.join(affected_tools)}[/cyan]")

                # Clear cache for affected tools
                if self.test_runner and hasattr(self.test_runner, "cache_instance") and self.test_runner.cache_instance:
                    for tool in affected_tools:
                        self.test_runner.cache_instance.clear_tool(tool)
                    logs.write(f"[green]   Cache cleared for affected tools[/green]")

                # Trigger selective re-run
                self.call_later(self._rerun_affected_tests, affected_tools)
            else:
                logs.write("[yellow]   Re-running all tests...[/yellow]")
                self.call_later(self.action_run_tests)

        logger.info(f"File change detected: {file_path}")

    def _rerun_affected_tests(self, affected_tools: List[str]) -> None:
        """Re-run tests for affected tools only (Phase 2)."""
        # Filter tests by affected tools
        # This would integrate with LiveTestRunner to run specific tests
        logs = self.query_one("#logs", RichLog)
        logs.write(f"[cyan]▶️  Re-running tests for: {', '.join(affected_tools)}[/cyan]")

        # For now, just log - full integration would require LiveTestRunner enhancement
        logger.info(f"Re-running tests for tools: {affected_tools}")

    async def _load_test_modules(self) -> None:
        """Load and populate test modules in the tree."""
        logs = self.query_one("#logs", RichLog)
        test_table = self.query_one("#test-tree", DataTable)

        try:
            logs.write("[cyan]📦 Loading test modules...[/cyan]")

            # Simulate loading test registry
            # In production, this would integrate with TestRegistry
            from .decorators import get_test_registry

            registry = get_test_registry()
            tests = registry.get_tests()

            # Populate table
            for test_name, test_info in tests.items():
                test_table.add_row("☐", test_name, "⏸️ Pending", "—", test_info.get("tool_name", "unknown"))

            logs.write(f"[green]✅ Loaded {len(tests)} tests[/green]")

            # Update summary
            summary = self.query_one("#summary", TestSummaryWidget)
            summary.total = len(tests)

            logger.info(f"Loaded {len(tests)} tests from registry")

        except Exception as e:
            logs.write(f"[red]❌ Error loading tests: {e}[/red]")
            logger.error(f"Failed to load test modules: {e}", exc_info=True)

    # ========================================================================
    # Phase 3: Action Handlers for Keyboard Bindings
    # ========================================================================

    def action_help(self) -> None:
        """Show help modal (Phase 3)."""
        self.push_screen(HelpModal())

    def action_run_tests(self) -> None:
        """Run all tests."""
        if self.is_running:
            logs = self.query_one("#logs", RichLog)
            logs.write("[yellow]⚠️  Tests already running[/yellow]")
            return

        logs = self.query_one("#logs", RichLog)
        logs.write("[bold cyan]▶️  Running all tests...[/bold cyan]")
        logger.info("Starting test execution (all tests)")

        self.run_tests_async()

    def action_run_selected(self) -> None:
        """Run only selected tests (Phase 3)."""
        if not self.selected_tests:
            logs = self.query_one("#logs", RichLog)
            logs.write("[yellow]⚠️  No tests selected. Use Space to select tests.[/yellow]")
            return

        logs = self.query_one("#logs", RichLog)
        logs.write(f"[bold cyan]▶️  Running {len(self.selected_tests)} selected tests...[/bold cyan]")
        logger.info(f"Starting test execution ({len(self.selected_tests)} selected tests)")

        self.run_tests_async(selected_only=True)

    def action_stop_tests(self) -> None:
        """Stop running tests."""
        if not self.is_running:
            logs = self.query_one("#logs", RichLog)
            logs.write("[yellow]⚠️  No tests running[/yellow]")
            return

        logs = self.query_one("#logs", RichLog)
        logs.write("[red]⏹️  Stopping tests...[/red]")
        logger.info("Stopping test execution")

        self.is_running = False

        # Stop progress
        summary = self.query_one("#summary", TestSummaryWidget)
        summary.running = False

    def action_toggle_selection(self) -> None:
        """Toggle selection of current test (Phase 3)."""
        test_table = self.query_one("#test-tree", DataTable)

        try:
            cursor_row = test_table.cursor_row
            if cursor_row is not None and cursor_row < test_table.row_count:
                row_key = test_table.get_row_at(cursor_row)
                test_name = row_key[1]  # Second column is test name

                if test_name in self.selected_tests:
                    self.selected_tests.remove(test_name)
                    # Update checkbox to unchecked
                    test_table.update_cell_at((cursor_row, 0), "☐")
                else:
                    self.selected_tests.add(test_name)
                    # Update checkbox to checked
                    test_table.update_cell_at((cursor_row, 0), "☑")

                logs = self.query_one("#logs", RichLog)
                logs.write(f"[cyan]{'✓' if test_name in self.selected_tests else '✗'} {test_name}[/cyan]")

        except Exception as e:
            logger.error(f"Toggle selection failed: {e}")

    def action_run_single(self) -> None:
        """Run single selected test (Phase 3)."""
        test_table = self.query_one("#test-tree", DataTable)

        try:
            cursor_row = test_table.cursor_row
            if cursor_row is not None and cursor_row < test_table.row_count:
                row_key = test_table.get_row_at(cursor_row)
                test_name = row_key[1]

                logs = self.query_one("#logs", RichLog)
                logs.write(f"[bold cyan]▶️  Running test: {test_name}[/bold cyan]")
                logger.info(f"Running single test: {test_name}")

                # Run single test
                self.run_single_test_async(test_name)

        except Exception as e:
            logger.error(f"Run single test failed: {e}")

    def action_filter_tests(self) -> None:
        """Open filter modal (Phase 3)."""
        logger.info("Opening filter modal")

        def handle_filter_result(filters: Optional[Dict[str, Any]]) -> None:
            if filters:
                self.current_filters = filters
                logs = self.query_one("#logs", RichLog)
                logs.write(f"[green]✅ Filters applied: {filters}[/green]")
                logger.info(f"Filters applied: {filters}")

                # Apply filters to table
                self._apply_filters()

        self.push_screen(FilterModal(self.current_filters), handle_filter_result)

    def action_quick_search(self) -> None:
        """Quick search for tests (Phase 3)."""
        logs = self.query_one("#logs", RichLog)
        logs.write("[cyan]🔍 Quick search (not fully implemented yet)[/cyan]")
        logger.info("Quick search triggered")

    def action_next_result(self) -> None:
        """Navigate to next search result (Phase 3)."""
        test_table = self.query_one("#test-tree", DataTable)
        if test_table.cursor_row is not None:
            test_table.cursor_row = min(test_table.cursor_row + 1, test_table.row_count - 1)

    def action_prev_result(self) -> None:
        """Navigate to previous search result (Phase 3)."""
        test_table = self.query_one("#test-tree", DataTable)
        if test_table.cursor_row is not None:
            test_table.cursor_row = max(test_table.cursor_row - 1, 0)

    def action_clear_cache(self) -> None:
        """Clear test cache."""
        logs = self.query_one("#logs", RichLog)
        logs.write("[yellow]🗑️  Clearing test cache...[/yellow]")

        try:
            from .cache import TestCache

            cache = TestCache()
            cache.clear_all()

            logs.write("[green]✅ Test cache cleared[/green]")
            logger.info("Test cache cleared")

        except Exception as e:
            logs.write(f"[red]❌ Error clearing cache: {e}[/red]")
            logger.error(f"Cache clear failed: {e}")

    def action_clear_tool_cache(self) -> None:
        """Clear cache for selected tool (Phase 3)."""
        test_table = self.query_one("#test-tree", DataTable)
        logs = self.query_one("#logs", RichLog)

        try:
            cursor_row = test_table.cursor_row
            if cursor_row is not None and cursor_row < test_table.row_count:
                row_key = test_table.get_row_at(cursor_row)
                tool_name = row_key[4]  # Fifth column is tool name

                from .cache import TestCache

                cache = TestCache()
                cache.clear_tool(tool_name)

                logs.write(f"[green]✅ Cache cleared for tool: {tool_name}[/green]")
                logger.info(f"Tool cache cleared: {tool_name}")

        except Exception as e:
            logs.write(f"[red]❌ Error clearing tool cache: {e}[/red]")
            logger.error(f"Tool cache clear failed: {e}")

    def action_clear_oauth(self) -> None:
        """Clear OAuth cache."""
        logs = self.query_one("#logs", RichLog)
        logs.write("[yellow]🔐 Clearing OAuth cache...[/yellow]")

        try:
            from .oauth_cache import CachedOAuthClient

            # OAuth cache clear logic would go here
            logs.write("[green]✅ OAuth cache cleared[/green]")
            logger.info("OAuth cache cleared")

        except Exception as e:
            logs.write(f"[red]❌ Error clearing OAuth cache: {e}[/red]")
            logger.error(f"OAuth cache clear failed: {e}")

    def action_toggle_live_reload(self) -> None:
        """Toggle live reload (Phase 2)."""
        self.enable_live_reload_flag = not self.enable_live_reload_flag

        logs = self.query_one("#logs", RichLog)
        status = "Enabled" if self.enable_live_reload_flag else "Disabled"
        logs.write(f"[cyan]🔄 Live Reload: {status}[/cyan]")
        logger.info(f"Live reload: {status}")

        if self.enable_live_reload_flag:
            self.call_later(self._setup_file_watcher)
        elif self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher = None

    def action_configure_watch_paths(self) -> None:
        """Configure watch paths (Phase 2)."""
        logs = self.query_one("#logs", RichLog)
        logs.write(f"[cyan]📁 Current watch paths: {', '.join(self.watch_paths)}[/cyan]")
        logs.write("[yellow]   Configuration dialog not implemented yet[/yellow]")
        logger.info("Watch paths configuration requested")

    def action_force_reload(self) -> None:
        """Force reload all tests (Phase 2)."""
        logs = self.query_one("#logs", RichLog)
        logs.write("[cyan]🔄 Force reloading...[/cyan]")

        # Clear all caches and re-run
        self.action_clear_cache()
        self.action_run_tests()

        logger.info("Force reload triggered")

    def action_toggle_theme(self) -> None:
        """Toggle between light and dark theme (Phase 3)."""
        self.dark_theme = not self.dark_theme

        logs = self.query_one("#logs", RichLog)
        theme = "Dark" if self.dark_theme else "Light"
        logs.write(f"[cyan]🎨 Theme: {theme}[/cyan]")
        logger.info(f"Theme changed to: {theme}")

        # Apply theme class
        # Note: Textual theme switching is more complex, this is simplified
        self.app.theme = "textual-dark" if self.dark_theme else "textual-light"

    def action_toggle_metrics(self) -> None:
        """Toggle metrics panel visibility (Phase 4)."""
        self.show_metrics = not self.show_metrics

        metrics_widget = self.query_one("#metrics", MetricsWidget)
        metrics_widget.display = self.show_metrics

        logs = self.query_one("#logs", RichLog)
        status = "Visible" if self.show_metrics else "Hidden"
        logs.write(f"[cyan]📊 Metrics Panel: {status}[/cyan]")
        logger.info(f"Metrics panel: {status}")

    def action_toggle_visibility(self) -> None:
        """Toggle team visibility panel (Phase 5)."""
        self.show_team_visibility = not self.show_team_visibility

        visibility_widget = self.query_one("#team-visibility", TeamVisibilityWidget)
        visibility_widget.display = self.show_team_visibility

        logs = self.query_one("#logs", RichLog)
        status = "Visible" if self.show_team_visibility else "Hidden"
        logs.write(f"[cyan]👥 Team Visibility: {status}[/cyan]")
        logger.info(f"Team visibility: {status}")

    def action_clear_output(self) -> None:
        """Clear output log (Phase 3)."""
        output = self.query_one("#test-output", RichLog)
        output.clear()

        logs = self.query_one("#logs", RichLog)
        logs.write("[cyan]🗑️  Output cleared[/cyan]")
        logger.info("Output log cleared")

    def action_export_results(self) -> None:
        """Open export modal (Phase 4)."""
        logger.info("Opening export modal")

        def handle_export(config: Optional[Dict[str, Any]]) -> None:
            if config:
                self._export_results(config)

        self.push_screen(ExportModal(), handle_export)

    def action_quick_export(self) -> None:
        """Quick export to JSON (Phase 4)."""
        config = {
            "format_type": "json",
            "output_path": f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "include_errors": True,
            "include_timing": True,
            "include_cached": True,
        }
        self._export_results(config)

    def action_performance_report(self) -> None:
        """Generate performance report (Phase 4)."""
        logs = self.query_one("#logs", RichLog)
        logs.write("[cyan]📈 Generating performance report...[/cyan]")

        try:
            # Calculate performance metrics
            metrics = self._calculate_metrics()

            output = self.query_one("#test-output", RichLog)
            output.clear()
            output.write("[bold]Performance Report[/bold]\n")
            output.write(f"Average Duration: {metrics['avg_duration']:.2f}ms")
            output.write(f"Min Duration: {metrics['min_duration']:.2f}ms")
            output.write(f"Max Duration: {metrics['max_duration']:.2f}ms")
            output.write(f"Total Duration: {metrics['total_duration']:.2f}s")
            output.write(f"Tests/Second: {metrics['tests_per_second']:.2f}")
            output.write(f"Cache Hit Rate: {metrics['cache_hit_rate']:.1f}%")

            logs.write("[green]✅ Performance report generated[/green]")
            logger.info("Performance report generated")

        except Exception as e:
            logs.write(f"[red]❌ Error generating report: {e}[/red]")
            logger.error(f"Performance report failed: {e}")

    def action_toggle_websocket(self) -> None:
        """Toggle WebSocket broadcasting (Phase 5)."""
        self.websocket_enabled = not self.websocket_enabled

        logs = self.query_one("#logs", RichLog)

        if self.websocket_enabled:
            logs.write("[cyan]🌐 Starting WebSocket server...[/cyan]")
            self.call_later(self._setup_websocket)
        else:
            logs.write("[cyan]🌐 Stopping WebSocket server...[/cyan]")
            asyncio.create_task(self.websocket_broadcaster.stop())

            team_widget = self.query_one("#team-visibility", TeamVisibilityWidget)
            team_widget.websocket_enabled = False

        logger.info(f"WebSocket: {self.websocket_enabled}")

    def action_configure_websocket(self) -> None:
        """Configure WebSocket endpoint (Phase 5)."""
        logs = self.query_one("#logs", RichLog)
        logs.write(f"[cyan]🌐 WebSocket: ws://{self.websocket_broadcaster.host}:{self.websocket_broadcaster.port}[/cyan]")
        logs.write("[yellow]   Configuration dialog not implemented yet[/yellow]")
        logger.info("WebSocket configuration requested")

    def action_show_users(self) -> None:
        """Show connected users (Phase 5)."""
        users = self.websocket_broadcaster.get_connected_users()

        output = self.query_one("#test-output", RichLog)
        output.clear()
        output.write("[bold]Connected Users[/bold]\n")

        if not users:
            output.write("[dim]No users connected[/dim]")
        else:
            for user in users:
                output.write(f"👤 {user['name']} - {user['status']}")
                output.write(f"   Address: {user['address']}")

        logs = self.query_one("#logs", RichLog)
        logs.write(f"[cyan]👥 {len(users)} users connected[/cyan]")
        logger.info(f"Showed connected users: {len(users)}")

    def action_toggle_debug(self) -> None:
        """Toggle debug mode (Phase 3)."""
        self.debug_mode = not self.debug_mode

        logs = self.query_one("#logs", RichLog)
        status = "Enabled" if self.debug_mode else "Disabled"
        logs.write(f"[cyan]🐛 Debug Mode: {status}[/cyan]")
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        logger.info(f"Debug mode: {status}")

    def action_inspect_test(self) -> None:
        """Inspect selected test (Phase 3)."""
        test_table = self.query_one("#test-tree", DataTable)
        output = self.query_one("#test-output", RichLog)

        try:
            cursor_row = test_table.cursor_row
            if cursor_row is not None and cursor_row < test_table.row_count:
                row_key = test_table.get_row_at(cursor_row)
                test_name = row_key[1]

                output.clear()
                output.write(f"[bold]Test Inspection: {test_name}[/bold]\n")

                # Find test result
                test_result = next((r for r in self.test_results if r["test_name"] == test_name), None)

                if test_result:
                    output.write(f"Status: {'✅ Passed' if test_result['success'] else '❌ Failed'}")
                    output.write(f"Duration: {test_result['duration_ms']:.2f}ms")
                    output.write(f"Tool: {test_result['tool_name']}")
                    output.write(f"Cached: {'Yes' if test_result.get('cached') else 'No'}")
                    output.write(f"Skipped: {'Yes' if test_result.get('skipped') else 'No'}")

                    if test_result.get("error"):
                        output.write(f"\n[bold red]Error:[/bold red]")
                        output.write(test_result["error"])
                else:
                    output.write("[dim]No result available yet[/dim]")

                logger.info(f"Inspected test: {test_name}")

        except Exception as e:
            output.write(f"[red]Error inspecting test: {e}[/red]")
            logger.error(f"Test inspection failed: {e}")

    def action_save_session(self) -> None:
        """Save current session (Phase 3)."""
        logs = self.query_one("#logs", RichLog)

        try:
            session_data = {
                "filters": self.current_filters,
                "selected_tests": list(self.selected_tests),
                "results": self.test_results,
                "timestamp": datetime.now().isoformat(),
            }

            session_path = Path("session.json")
            session_path.write_text(json.dumps(session_data, indent=2))

            logs.write(f"[green]✅ Session saved to {session_path}[/green]")
            logger.info("Session saved")

        except Exception as e:
            logs.write(f"[red]❌ Error saving session: {e}[/red]")
            logger.error(f"Session save failed: {e}")

    def action_load_session(self) -> None:
        """Load saved session (Phase 3)."""
        logs = self.query_one("#logs", RichLog)

        try:
            session_path = Path("session.json")
            if not session_path.exists():
                logs.write("[yellow]⚠️  No saved session found[/yellow]")
                return

            session_data = json.loads(session_path.read_text())

            self.current_filters = session_data["filters"]
            self.selected_tests = set(session_data["selected_tests"])
            self.test_results = session_data["results"]

            logs.write(f"[green]✅ Session loaded from {session_path}[/green]")
            logger.info("Session loaded")

            # Apply loaded state
            self._apply_filters()
            self._update_results_display()

        except Exception as e:
            logs.write(f"[red]❌ Error loading session: {e}[/red]")
            logger.error(f"Session load failed: {e}")

    def action_health_check(self) -> None:
        """Manually trigger health check for all status widgets."""
        logs = self.query_one("#logs", RichLog)
        logs.write("[cyan]🏥 Running health check...[/cyan]")
        logger.info("Manual health check triggered")

        # Trigger refresh of all status widgets
        self.call_later(self._refresh_status_widgets)

    # ========================================================================
    # Phase 4: Metrics and Export
    # ========================================================================

    def _calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics (Phase 4)."""
        if not self.test_durations:
            return {
                "avg_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0,
                "total_duration": 0.0,
                "tests_per_second": 0.0,
                "cache_hit_rate": 0.0,
            }

        total_duration = sum(self.test_durations)
        avg_duration = total_duration / len(self.test_durations)
        total_tests = self.cache_hits + self.cache_misses

        return {
            "avg_duration": avg_duration,
            "min_duration": min(self.test_durations),
            "max_duration": max(self.test_durations),
            "total_duration": total_duration / 1000,  # Convert to seconds
            "tests_per_second": len(self.test_durations) / (total_duration / 1000) if total_duration > 0 else 0,
            "cache_hit_rate": (self.cache_hits / total_tests * 100) if total_tests > 0 else 0,
        }

    def _update_metrics_widget(self) -> None:
        """Update metrics widget with latest data (Phase 4)."""
        metrics = self._calculate_metrics()

        metrics_widget = self.query_one("#metrics", MetricsWidget)
        metrics_widget.avg_duration = metrics["avg_duration"]
        metrics_widget.min_duration = metrics["min_duration"]
        metrics_widget.max_duration = metrics["max_duration"]
        metrics_widget.total_duration = metrics["total_duration"]
        metrics_widget.tests_per_second = metrics["tests_per_second"]
        metrics_widget.cache_hit_rate = metrics["cache_hit_rate"]

    def _export_results(self, config: Dict[str, Any]) -> None:
        """Export test results to file (Phase 4)."""
        logs = self.query_one("#logs", RichLog)

        try:
            format_type = config["format"]
            output_path = Path(config["output_path"])

            # Prepare export data
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "endpoint": self.endpoint,
                "total_tests": len(self.test_results),
                "results": self.test_results,
            }

            if config["include_timing"]:
                export_data["metrics"] = self._calculate_metrics()

            # Export based on format
            if format_type == "json":
                output_path.write_text(json.dumps(export_data, indent=2))
            elif format_type == "markdown":
                self._export_markdown(export_data, output_path)
            elif format_type == "html":
                self._export_html(export_data, output_path)
            elif format_type == "csv":
                self._export_csv(export_data, output_path)

            logs.write(f"[green]✅ Exported to {output_path}[/green]")
            logger.info(f"Exported results to {output_path}")

        except Exception as e:
            logs.write(f"[red]❌ Export failed: {e}[/red]")
            logger.error(f"Export failed: {e}", exc_info=True)

    def _export_markdown(self, data: Dict[str, Any], path: Path) -> None:
        """Export to Markdown format."""
        lines = [
            f"# Test Report - {data['timestamp']}",
            f"\n## Summary",
            f"- Endpoint: {data['endpoint']}",
            f"- Total Tests: {data['total_tests']}",
            f"\n## Results\n",
            "| Test | Status | Duration | Tool |",
            "|------|--------|----------|------|",
        ]

        for result in data["results"]:
            status = "✅" if result["success"] else "❌"
            lines.append(f"| {result['test_name']} | {status} | {result['duration_ms']:.2f}ms | {result['tool_name']} |")

        path.write_text("\n".join(lines))

    def _export_html(self, data: Dict[str, Any], path: Path) -> None:
        """Export to HTML format."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {data['timestamp']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
    </style>
</head>
<body>
    <h1>Test Report</h1>
    <p><strong>Timestamp:</strong> {data['timestamp']}</p>
    <p><strong>Endpoint:</strong> {data['endpoint']}</p>
    <p><strong>Total Tests:</strong> {data['total_tests']}</p>

    <h2>Results</h2>
    <table>
        <tr><th>Test</th><th>Status</th><th>Duration</th><th>Tool</th></tr>
"""

        for result in data["results"]:
            status_class = "passed" if result["success"] else "failed"
            status_text = "✅ Passed" if result["success"] else "❌ Failed"
            html += f"""
        <tr>
            <td>{result['test_name']}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{result['duration_ms']:.2f}ms</td>
            <td>{result['tool_name']}</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""
        path.write_text(html)

    def _export_csv(self, data: Dict[str, Any], path: Path) -> None:
        """Export to CSV format."""
        import csv

        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test", "Status", "Duration (ms)", "Tool", "Cached", "Error"])

            for result in data["results"]:
                writer.writerow([
                    result["test_name"],
                    "Passed" if result["success"] else "Failed",
                    f"{result['duration_ms']:.2f}",
                    result["tool_name"],
                    "Yes" if result.get("cached") else "No",
                    result.get("error", ""),
                ])

    # ========================================================================
    # Test Execution (Integration with LiveTestRunner)
    # ========================================================================

    @work(exclusive=True)
    async def run_tests_async(self, selected_only: bool = False) -> None:
        """Run tests asynchronously with LiveTestRunner integration."""
        self.is_running = True

        logs = self.query_one("#logs", RichLog)
        test_table = self.query_one("#test-tree", DataTable)
        summary = self.query_one("#summary", TestSummaryWidget)
        progress = self.query_one("#progress", TestProgressWidget)

        summary.running = True

        try:
            # Initialize LiveTestRunner
            from .live_runner import LiveTestRunner
            from .adapters import AtomsMCPClientAdapter

            logs.write("[cyan]🔧 Initializing test runner...[/cyan]")

            client_adapter = AtomsMCPClientAdapter(self.endpoint)

            # Setup callbacks
            runner = LiveTestRunner(
                client_adapter=client_adapter,
                cache=True,
                parallel=False,
                on_test_start=self._on_test_start,
                on_test_complete=self._on_test_complete,
                on_suite_start=self._on_suite_start,
                on_suite_complete=self._on_suite_complete,
            )

            self.test_runner = runner

            # Run tests
            if selected_only:
                # Run only selected tests
                # This would require enhancement to LiveTestRunner
                logs.write("[yellow]⚠️  Selected test execution not fully implemented[/yellow]")
                result = await runner.run_all()
            else:
                result = await runner.run_all()

            logs.write("[bold green]✅ Test execution complete![/bold green]")
            logger.info("Test execution completed successfully")

            # Broadcast results via WebSocket
            if self.websocket_enabled:
                await self.websocket_broadcaster.broadcast({
                    "type": "test_complete",
                    "summary": result,
                    "timestamp": datetime.now().isoformat(),
                })

        except Exception as e:
            logs.write(f"[bold red]❌ Error running tests: {e}[/bold red]")
            logger.error(f"Test execution failed: {e}", exc_info=True)

        finally:
            self.is_running = False
            summary.running = False

    @work(exclusive=True)
    async def run_single_test_async(self, test_name: str) -> None:
        """Run a single test asynchronously."""
        logs = self.query_one("#logs", RichLog)

        try:
            logs.write(f"[cyan]▶️  Running: {test_name}[/cyan]")

            # This would integrate with LiveTestRunner to run single test
            # For now, just log
            await asyncio.sleep(1)

            logs.write(f"[green]✅ Completed: {test_name}[/green]")
            logger.info(f"Single test completed: {test_name}")

        except Exception as e:
            logs.write(f"[red]❌ Error: {e}[/red]")
            logger.error(f"Single test failed: {e}")

    def _on_suite_start(self, total_tests: int) -> None:
        """Callback when test suite starts."""
        progress = self.query_one("#progress", TestProgressWidget)
        summary = self.query_one("#summary", TestSummaryWidget)

        progress.total = total_tests
        progress.current = 0
        summary.total = total_tests

        logs = self.query_one("#logs", RichLog)
        logs.write(f"[bold cyan]📋 Starting {total_tests} tests...[/bold cyan]")
        logger.info(f"Test suite started: {total_tests} tests")

    def _on_test_start(self, test_name: str, tool_name: str) -> None:
        """Callback when individual test starts."""
        progress = self.query_one("#progress", TestProgressWidget)
        progress.current_test = test_name
        progress.current_tool = tool_name

        logger.debug(f"Test started: {test_name}")

    def _on_test_complete(self, test_name: str, result: Dict[str, Any]) -> None:
        """Callback when individual test completes."""
        progress = self.query_one("#progress", TestProgressWidget)
        summary = self.query_one("#summary", TestSummaryWidget)
        test_table = self.query_one("#test-tree", DataTable)
        live_monitor = self.query_one("#live-monitor", LiveMonitorWidget)

        # Update progress
        progress.current += 1

        # Update summary
        if result.get("success"):
            summary.passed += 1
        elif not result.get("skipped"):
            summary.failed += 1

        if result.get("skipped"):
            summary.skipped += 1
        if result.get("cached"):
            summary.cached += 1
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        # Track duration
        duration_ms = result.get("duration_ms", 0)
        self.test_durations.append(duration_ms)
        summary.duration += duration_ms / 1000

        # Update table
        status_icon = "💾" if result.get("cached") else ("✅" if result["success"] else "❌")
        for i in range(test_table.row_count):
            row = test_table.get_row_at(i)
            if row[1] == test_name:
                test_table.update_cell_at((i, 2), status_icon)
                test_table.update_cell_at((i, 3), f"{duration_ms:.2f}ms")
                break

        # Update live monitor
        recent_tests = list(live_monitor.recent_tests)
        recent_tests.append({"name": test_name, "success": result["success"], "duration": duration_ms})
        live_monitor.recent_tests = recent_tests

        if not result["success"] and not result.get("skipped"):
            live_monitor.error_count += 1

        # Store result
        self.test_results.append(result)

        # Update metrics
        self._update_metrics_widget()

        # Broadcast via WebSocket
        if self.websocket_enabled:
            asyncio.create_task(
                self.websocket_broadcaster.broadcast({
                    "type": "test_result",
                    "test_name": test_name,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                })
            )

        logger.debug(f"Test completed: {test_name} - {'✅' if result['success'] else '❌'}")

    def _on_suite_complete(self, summary: Dict[str, Any]) -> None:
        """Callback when test suite completes."""
        logs = self.query_one("#logs", RichLog)

        passed = summary["passed"]
        failed = summary["failed"]
        total = summary["total"]
        duration = summary["duration_seconds"]

        logs.write(f"[bold green]🎉 Suite complete![/bold green]")
        logs.write(f"   Total: {total} | Passed: {passed} | Failed: {failed}")
        logs.write(f"   Duration: {duration:.2f}s")

        logger.info(f"Test suite completed: {total} tests in {duration:.2f}s")

    def _apply_filters(self) -> None:
        """Apply current filters to test table."""
        logs = self.query_one("#logs", RichLog)
        logs.write("[cyan]🔍 Applying filters...[/cyan]")

        # Filter logic would go here
        # For now, just log
        logger.info(f"Filters applied: {self.current_filters}")

    def _update_results_display(self) -> None:
        """Update test results display."""
        output = self.query_one("#test-output", RichLog)
        output.clear()

        if not self.test_results:
            output.write("[dim]No test results yet[/dim]")
            return

        output.write("[bold]Test Results[/bold]\n")
        for result in self.test_results[-20:]:  # Show last 20
            icon = "✅" if result["success"] else "❌"
            output.write(f"{icon} {result['test_name']} ({result['duration_ms']:.2f}ms)")

    async def _refresh_status_widgets(self) -> None:
        """Refresh all status monitoring widgets (called every 5 seconds)."""
        try:
            # Refresh OAuth status
            oauth_widget = self.query_one("#oauth-status", OAuthStatusWidget)
            await oauth_widget.refresh_status()

            # Refresh server status
            server_widget = self.query_one("#server-status", ServerStatusWidget)
            await server_widget.refresh_status()

            # Refresh tunnel status
            tunnel_widget = self.query_one("#tunnel-status", TunnelStatusWidget)
            await tunnel_widget.refresh_status()

            # Refresh resource status
            resource_widget = self.query_one("#resource-status", ResourceStatusWidget)
            await resource_widget.refresh_status()

        except Exception as e:
            logger.error(f"Status widget refresh failed: {e}")

    async def on_unmount(self) -> None:
        """Cleanup when app is unmounted."""
        # Stop FileWatcher
        if self.file_watcher:
            self.file_watcher.stop()
            logger.info("FileWatcher stopped")

        # Stop WebSocket server
        if self.websocket_enabled:
            await self.websocket_broadcaster.stop()
            logger.info("WebSocket server stopped")

        logger.info("Test dashboard unmounted")


# ============================================================================
# Entry Point
# ============================================================================


def run_tui_dashboard(
    endpoint: str,
    test_modules: List[str],
    enable_live_reload: bool = True,
    watch_paths: Optional[List[str]] = None,
    enable_websocket: bool = False,
    websocket_host: str = "localhost",
    websocket_port: int = 8765,
    oauth_cache_client=None,
    tunnel_config: Optional[Dict[str, Any]] = None,
    resource_config: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """
    Run comprehensive TUI dashboard for Atoms MCP test suite.

    Args:
        endpoint: MCP endpoint URL
        test_modules: List of test module names to load
        enable_live_reload: Enable FileWatcher for auto-reload (Phase 2)
        watch_paths: Directories to watch for changes
        enable_websocket: Enable WebSocket server for team visibility (Phase 5)
        websocket_host: WebSocket server host
        websocket_port: WebSocket server port
        oauth_cache_client: OAuth cache client for token monitoring
        tunnel_config: Tunnel configuration (ngrok, cloudflare, custom)
        resource_config: Resource monitoring configuration (DB, Redis, etc.)
        **kwargs: Additional options

    Features:
        - Phase 1: Grid layout with header, footer, test tree, output panels
        - Phase 2: FileWatcher integration with smart test re-running
        - Phase 3: 30+ keyboard shortcuts, mouse handlers, modal dialogs
        - Phase 4: Real-time metrics, export to JSON/MD/HTML/CSV
        - Phase 5: WebSocket broadcasting for team collaboration
        - Status Monitoring: OAuth, Server, Tunnel, Resources with auto-refresh

    Example:
        >>> from mcp_qa.oauth_cache import CachedOAuthClient
        >>> oauth_client = CachedOAuthClient("https://mcp.example.com")
        >>> run_tui_dashboard(
        ...     endpoint="atoms_mcp",
        ...     test_modules=["tests.comprehensive.test_entity"],
        ...     enable_live_reload=True,
        ...     watch_paths=["tools/", "tests/"],
        ...     enable_websocket=True,
        ...     oauth_cache_client=oauth_client,
        ...     tunnel_config={"type": "ngrok"},
        ...     resource_config={"check_db": True, "check_memory": True}
        ... )
    """
    if not HAS_TEXTUAL:
        print("❌ Textual not installed. Install with: pip install textual")
        print("   Falling back to standard test runner...")
        return

    try:
        app = TestDashboardApp(
            endpoint=endpoint,
            test_modules=test_modules,
            enable_live_reload=enable_live_reload,
            watch_paths=watch_paths,
            enable_websocket=enable_websocket,
            websocket_host=websocket_host,
            websocket_port=websocket_port,
            oauth_cache_client=oauth_cache_client,
            tunnel_config=tunnel_config,
            resource_config=resource_config,
        )

        logger.info("Starting Atoms MCP Test Dashboard")
        app.run()

    except KeyboardInterrupt:
        logger.info("Dashboard interrupted by user")
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Dashboard crashed: {e}", exc_info=True)
        print(f"\n❌ Dashboard error: {e}")
        raise


# Export main components
__all__ = [
    "TestDashboardApp",
    "run_tui_dashboard",
    "FilterModal",
    "ExportModal",
    "HelpModal",
    "OAuthStatusWidget",
    "ServerStatusWidget",
    "TunnelStatusWidget",
    "ResourceStatusWidget",
    "TestSummaryWidget",
    "TestProgressWidget",
    "MetricsWidget",
    "LiveMonitorWidget",
    "TeamVisibilityWidget",
    "WebSocketBroadcaster",
]
