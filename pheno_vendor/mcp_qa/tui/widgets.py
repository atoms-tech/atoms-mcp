"""
Comprehensive Textual TUI widgets for Atoms MCP test suite.

This module contains all widgets for phases 1-5 of the test framework:
- Phase 1: Core widgets for test display and monitoring
- Phase 2: Live reload and file watching
- Phase 3: Interactive filtering and selection
- Phase 4: Advanced metrics and export
- Phase 5: Collaboration and multi-endpoint support
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    OptionList,
    Static,
    Tree,
)
from textual.widgets.option_list import Option


# =============================================================================
# PHASE 1: CORE WIDGETS
# =============================================================================


class TestTreeWidget(Widget):
    """
    Collapsible tree view of tests organized by category with DataTable display.

    Features:
    - Hierarchical organization by category
    - Expandable/collapsible nodes
    - Color-coded by test status
    - Click to view details
    """

    DEFAULT_CSS = """
    TestTreeWidget {
        height: auto;
        border: solid $primary;
    }

    TestTreeWidget Tree {
        background: $surface;
    }
    """

    selected_test: reactive[Optional[str]] = reactive(None)
    test_data: reactive[Dict[str, Any]] = reactive(dict, layout=True)

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._test_results: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, List[str]] = defaultdict(list)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Tree("Test Suite", id="test-tree")

    def update_tests(self, test_results: Dict[str, Dict[str, Any]]) -> None:
        """
        Update the tree with new test results.

        Args:
            test_results: Dictionary mapping test names to their results
        """
        self._test_results = test_results
        self._organize_by_category()
        self._rebuild_tree()

    def _organize_by_category(self) -> None:
        """Organize tests by category."""
        self._categories.clear()
        for test_name, result in self._test_results.items():
            category = result.get("category", "Uncategorized")
            self._categories[category].append(test_name)

    def _rebuild_tree(self) -> None:
        """Rebuild the entire tree structure."""
        tree = self.query_one("#test-tree", Tree)
        tree.clear()
        tree.label = f"Test Suite ({len(self._test_results)} tests)"

        for category, tests in sorted(self._categories.items()):
            # Add category node
            category_node = tree.root.add(
                f"[bold]{category}[/bold] ({len(tests)} tests)",
                expand=True,
            )

            # Add test nodes
            for test_name in sorted(tests):
                result = self._test_results[test_name]
                status = result.get("status", "pending")

                # Color code by status
                if status == "passed":
                    icon = "[green]✓[/green]"
                elif status == "failed":
                    icon = "[red]✗[/red]"
                elif status == "skipped":
                    icon = "[yellow]⊘[/yellow]"
                else:
                    icon = "[dim]○[/dim]"

                duration = result.get("duration", 0)
                label = f"{icon} {test_name} ({duration:.2f}s)"

                category_node.add_leaf(label, data={"test_name": test_name})

    @on(Tree.NodeSelected)
    def handle_selection(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection."""
        if event.node.data:
            test_name = event.node.data.get("test_name")
            if test_name:
                self.selected_test = test_name
                self.post_message(self.TestSelected(test_name))

    class TestSelected(Widget.Message):
        """Posted when a test is selected."""

        def __init__(self, test_name: str) -> None:
            super().__init__()
            self.test_name = test_name


class TestDetailWidget(Widget):
    """
    Detailed test output viewer with syntax highlighting.

    Features:
    - Syntax-highlighted output
    - Stack traces with line numbers
    - Test metadata display
    - Error highlighting
    """

    DEFAULT_CSS = """
    TestDetailWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    TestDetailWidget VerticalScroll {
        height: 100%;
    }
    """

    test_data: reactive[Optional[Dict[str, Any]]] = reactive(None, layout=True)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with VerticalScroll():
            yield Static(id="detail-content")

    def watch_test_data(self, test_data: Optional[Dict[str, Any]]) -> None:
        """React to test data changes."""
        if test_data:
            self._update_display(test_data)

    def _update_display(self, test_data: Dict[str, Any]) -> None:
        """Update the detail display with test data."""
        content = self.query_one("#detail-content", Static)

        # Build the display
        renderables = []

        # Test header
        test_name = test_data.get("name", "Unknown Test")
        status = test_data.get("status", "pending")

        if status == "passed":
            status_text = "[green]PASSED[/green]"
        elif status == "failed":
            status_text = "[red]FAILED[/red]"
        elif status == "skipped":
            status_text = "[yellow]SKIPPED[/yellow]"
        else:
            status_text = "[dim]PENDING[/dim]"

        header = Text()
        header.append(f"{test_name}\n", style="bold")
        header.append(f"Status: {status_text}\n")
        header.append(f"Duration: {test_data.get('duration', 0):.3f}s\n")
        header.append(f"Category: {test_data.get('category', 'N/A')}\n")

        renderables.append(Panel(header, title="Test Info"))

        # Output
        if output := test_data.get("output"):
            renderables.append(Panel(
                Syntax(output, "python", theme="monokai", line_numbers=True),
                title="Output"
            ))

        # Error details
        if error := test_data.get("error"):
            error_text = Text()
            error_text.append(f"Error Type: {error.get('type', 'Unknown')}\n", style="bold red")
            error_text.append(f"Message: {error.get('message', 'No message')}\n", style="red")

            if traceback := error.get("traceback"):
                error_text.append("\nTraceback:\n", style="bold")
                renderables.append(Panel(error_text, title="Error", border_style="red"))
                renderables.append(Panel(
                    Syntax(traceback, "python", theme="monokai", line_numbers=True),
                    title="Stack Trace",
                    border_style="red"
                ))
            else:
                renderables.append(Panel(error_text, title="Error", border_style="red"))

        # Metadata
        if metadata := test_data.get("metadata"):
            meta_table = Table(show_header=False)
            meta_table.add_column("Key", style="cyan")
            meta_table.add_column("Value")

            for key, value in metadata.items():
                meta_table.add_row(str(key), str(value))

            renderables.append(Panel(meta_table, title="Metadata"))

        # Update content
        content.update("\n".join(str(r) for r in renderables))


class SummaryStatsWidget(Widget):
    """
    Live-updating summary statistics with reactive attributes.

    Features:
    - Real-time test counts
    - Pass/fail rates
    - Average duration
    - Color-coded metrics
    """

    DEFAULT_CSS = """
    SummaryStatsWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """

    total_tests: reactive[int] = reactive(0)
    passed: reactive[int] = reactive(0)
    failed: reactive[int] = reactive(0)
    skipped: reactive[int] = reactive(0)
    running: reactive[int] = reactive(0)
    avg_duration: reactive[float] = reactive(0.0)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="stats-content")

    def watch_total_tests(self, total: int) -> None:
        """React to total tests change."""
        self._update_display()

    def watch_passed(self, passed: int) -> None:
        """React to passed tests change."""
        self._update_display()

    def watch_failed(self, failed: int) -> None:
        """React to failed tests change."""
        self._update_display()

    def watch_skipped(self, skipped: int) -> None:
        """React to skipped tests change."""
        self._update_display()

    def watch_running(self, running: int) -> None:
        """React to running tests change."""
        self._update_display()

    def watch_avg_duration(self, avg: float) -> None:
        """React to average duration change."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the statistics display."""
        content = self.query_one("#stats-content", Static)

        # Calculate percentages
        total = self.total_tests or 1  # Avoid division by zero
        pass_rate = (self.passed / total) * 100
        fail_rate = (self.failed / total) * 100

        # Build stats table
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total Tests", str(self.total_tests))
        table.add_row("Passed", f"[green]{self.passed}[/green] ({pass_rate:.1f}%)")
        table.add_row("Failed", f"[red]{self.failed}[/red] ({fail_rate:.1f}%)")
        table.add_row("Skipped", f"[yellow]{self.skipped}[/yellow]")
        table.add_row("Running", f"[blue]{self.running}[/blue]")
        table.add_row("Avg Duration", f"{self.avg_duration:.3f}s")

        content.update(table)


class ProgressBarWidget(Widget):
    """
    Multi-level progress tracking (overall + per-category).

    Features:
    - Overall progress bar
    - Per-category progress
    - Real-time updates
    - Color-coded by status
    """

    DEFAULT_CSS = """
    ProgressBarWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """

    total: reactive[int] = reactive(0)
    completed: reactive[int] = reactive(0)
    category_progress: reactive[Dict[str, Tuple[int, int]]] = reactive(dict, layout=True)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="progress-content")

    def watch_total(self, total: int) -> None:
        """React to total change."""
        self._update_display()

    def watch_completed(self, completed: int) -> None:
        """React to completed change."""
        self._update_display()

    def watch_category_progress(self, progress: Dict[str, Tuple[int, int]]) -> None:
        """React to category progress change."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the progress display."""
        content = self.query_one("#progress-content", Static)

        # Create progress display
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )

        # Overall progress
        overall_task = progress.add_task(
            "Overall",
            total=self.total or 1,
            completed=self.completed,
        )

        # Category progress
        for category, (completed, total) in sorted(self.category_progress.items()):
            progress.add_task(
                f"  {category}",
                total=total or 1,
                completed=completed,
            )

        content.update(progress)


class LogStreamWidget(Widget):
    """
    Live log output stream with auto-scroll.

    Features:
    - Real-time log streaming
    - Auto-scroll to latest
    - Log level filtering
    - Color-coded by level
    """

    DEFAULT_CSS = """
    LogStreamWidget {
        height: auto;
        border: solid $primary;
    }

    LogStreamWidget VerticalScroll {
        height: 100%;
    }
    """

    max_lines: int = 1000
    auto_scroll: reactive[bool] = reactive(True)

    def __init__(
        self,
        max_lines: int = 1000,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.max_lines = max_lines
        self._logs: List[Tuple[datetime, str, str]] = []

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with VerticalScroll(id="log-scroll"):
            yield Static(id="log-content")

    def add_log(self, level: str, message: str) -> None:
        """
        Add a log message.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
        """
        timestamp = datetime.now()
        self._logs.append((timestamp, level, message))

        # Trim old logs
        if len(self._logs) > self.max_lines:
            self._logs = self._logs[-self.max_lines:]

        self._update_display()

    def clear_logs(self) -> None:
        """Clear all logs."""
        self._logs.clear()
        self._update_display()

    def _update_display(self) -> None:
        """Update the log display."""
        content = self.query_one("#log-content", Static)

        # Build log text
        log_text = Text()

        for timestamp, level, message in self._logs:
            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]

            # Color code by level
            if level == "ERROR" or level == "CRITICAL":
                style = "red"
            elif level == "WARNING":
                style = "yellow"
            elif level == "INFO":
                style = "green"
            else:
                style = "dim"

            log_text.append(f"[{time_str}] ", style="dim")
            log_text.append(f"{level:8} ", style=style)
            log_text.append(f"{message}\n")

        content.update(log_text)

        # Auto-scroll to bottom
        if self.auto_scroll:
            scroll = self.query_one("#log-scroll", VerticalScroll)
            scroll.scroll_end(animate=False)


# =============================================================================
# PHASE 2: LIVE RELOAD WIDGETS
# =============================================================================


class FileWatcherWidget(Widget):
    """
    Display watched files and recent changes.

    Features:
    - List of watched files/directories
    - Recent change notifications
    - File status indicators
    - Click to focus on file
    """

    DEFAULT_CSS = """
    FileWatcherWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """

    watched_paths: reactive[List[Path]] = reactive(list, layout=True)
    recent_changes: reactive[List[Tuple[datetime, Path, str]]] = reactive(list, layout=True)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="watcher-content")

    def watch_watched_paths(self, paths: List[Path]) -> None:
        """React to watched paths change."""
        self._update_display()

    def watch_recent_changes(self, changes: List[Tuple[datetime, Path, str]]) -> None:
        """React to recent changes."""
        self._update_display()

    def add_change(self, path: Path, event_type: str) -> None:
        """
        Add a file change event.

        Args:
            path: Path to changed file
            event_type: Type of change (modified, created, deleted)
        """
        timestamp = datetime.now()
        self.recent_changes = [(timestamp, path, event_type)] + self.recent_changes[:19]

    def _update_display(self) -> None:
        """Update the watcher display."""
        content = self.query_one("#watcher-content", Static)

        # Build display
        text = Text()

        # Watched paths
        text.append("Watched Paths:\n", style="bold")
        for path in self.watched_paths:
            text.append(f"  📁 {path}\n", style="cyan")

        text.append("\n")

        # Recent changes
        text.append("Recent Changes:\n", style="bold")
        for timestamp, path, event_type in self.recent_changes[:10]:
            time_str = timestamp.strftime("%H:%M:%S")

            if event_type == "created":
                icon = "[green]+[/green]"
            elif event_type == "deleted":
                icon = "[red]-[/red]"
            else:
                icon = "[yellow]~[/yellow]"

            text.append(f"  [{time_str}] {icon} {path.name}\n")

        content.update(Panel(text, title="File Watcher"))


class ReloadIndicatorWidget(Widget):
    """
    Visual indicator when reloading tests.

    Features:
    - Animated reload indicator
    - Reload status messages
    - Progress feedback
    - Color-coded states
    """

    DEFAULT_CSS = """
    ReloadIndicatorWidget {
        height: 3;
        border: solid $primary;
        padding: 1;
    }
    """

    is_reloading: reactive[bool] = reactive(False)
    reload_message: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="reload-content")

    def watch_is_reloading(self, reloading: bool) -> None:
        """React to reload state change."""
        self._update_display()

    def watch_reload_message(self, message: str) -> None:
        """React to reload message change."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the reload indicator."""
        content = self.query_one("#reload-content", Static)

        if self.is_reloading:
            text = Text()
            text.append("🔄 ", style="bold blue")
            text.append("Reloading... ", style="bold")
            if self.reload_message:
                text.append(self.reload_message, style="dim")
            content.update(text)
        else:
            content.update("")


# =============================================================================
# PHASE 3: INTERACTIVE WIDGETS
# =============================================================================


class FilterDialogWidget(Widget):
    """
    Modal dialog for test filtering.

    Features:
    - Filter by status
    - Filter by category
    - Filter by name pattern
    - Apply/cancel buttons
    """

    DEFAULT_CSS = """
    FilterDialogWidget {
        align: center middle;
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    FilterDialogWidget Input {
        margin: 1 0;
    }

    FilterDialogWidget Button {
        margin: 1 1;
    }
    """

    def __init__(
        self,
        current_filters: Optional[Dict[str, Any]] = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._current_filters = current_filters or {}

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Filter Tests", classes="dialog-title")

        yield Label("Status:")
        yield Checkbox("Passed", id="filter-passed", value=self._current_filters.get("passed", True))
        yield Checkbox("Failed", id="filter-failed", value=self._current_filters.get("failed", True))
        yield Checkbox("Skipped", id="filter-skipped", value=self._current_filters.get("skipped", True))
        yield Checkbox("Pending", id="filter-pending", value=self._current_filters.get("pending", True))

        yield Label("Name Pattern:")
        yield Input(
            placeholder="Filter by name (regex supported)",
            id="filter-pattern",
            value=self._current_filters.get("pattern", ""),
        )

        yield Label("Category:")
        yield Input(
            placeholder="Filter by category",
            id="filter-category",
            value=self._current_filters.get("category", ""),
        )

        with Horizontal():
            yield Button("Apply", variant="primary", id="apply-filter")
            yield Button("Cancel", variant="default", id="cancel-filter")

    @on(Button.Pressed, "#apply-filter")
    def handle_apply(self) -> None:
        """Handle apply button press."""
        filters = {
            "passed": self.query_one("#filter-passed", Checkbox).value,
            "failed": self.query_one("#filter-failed", Checkbox).value,
            "skipped": self.query_one("#filter-skipped", Checkbox).value,
            "pending": self.query_one("#filter-pending", Checkbox).value,
            "pattern": self.query_one("#filter-pattern", Input).value,
            "category": self.query_one("#filter-category", Input).value,
        }
        self.post_message(self.FiltersApplied(filters))

    @on(Button.Pressed, "#cancel-filter")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.post_message(self.FiltersCancelled())

    class FiltersApplied(Widget.Message):
        """Posted when filters are applied."""

        def __init__(self, filters: Dict[str, Any]) -> None:
            super().__init__()
            self.filters = filters

    class FiltersCancelled(Widget.Message):
        """Posted when filter dialog is cancelled."""
        pass


class TestSelectorWidget(Widget):
    """
    Multi-select tests with checkboxes.

    Features:
    - Checkbox list of all tests
    - Select all/none
    - Filter integration
    - Bulk actions
    """

    DEFAULT_CSS = """
    TestSelectorWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    TestSelectorWidget VerticalScroll {
        height: 100%;
    }
    """

    available_tests: reactive[List[str]] = reactive(list, layout=True)
    selected_tests: reactive[Set[str]] = reactive(set)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical():
            with Horizontal():
                yield Button("Select All", id="select-all", variant="primary")
                yield Button("Select None", id="select-none", variant="default")

            with VerticalScroll():
                yield Container(id="test-checkboxes")

    def watch_available_tests(self, tests: List[str]) -> None:
        """React to available tests change."""
        self._rebuild_checkboxes()

    def _rebuild_checkboxes(self) -> None:
        """Rebuild the checkbox list."""
        container = self.query_one("#test-checkboxes", Container)
        container.remove_children()

        for test_name in self.available_tests:
            checkbox = Checkbox(
                test_name,
                value=test_name in self.selected_tests,
                id=f"test-{test_name}",
            )
            container.mount(checkbox)

    @on(Button.Pressed, "#select-all")
    def handle_select_all(self) -> None:
        """Select all tests."""
        self.selected_tests = set(self.available_tests)
        for checkbox in self.query(Checkbox):
            checkbox.value = True

    @on(Button.Pressed, "#select-none")
    def handle_select_none(self) -> None:
        """Deselect all tests."""
        self.selected_tests = set()
        for checkbox in self.query(Checkbox):
            checkbox.value = False

    @on(Checkbox.Changed)
    def handle_checkbox_change(self, event: Checkbox.Changed) -> None:
        """Handle individual checkbox changes."""
        test_name = event.checkbox.label.plain
        if event.checkbox.value:
            self.selected_tests = self.selected_tests | {test_name}
        else:
            self.selected_tests = self.selected_tests - {test_name}


class CommandPaletteWidget(Widget):
    """
    Quick action search and execution.

    Features:
    - Fuzzy search for commands
    - Keyboard shortcuts
    - Recent commands
    - Command categories
    """

    DEFAULT_CSS = """
    CommandPaletteWidget {
        align: center top;
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    CommandPaletteWidget Input {
        margin: 1 0;
    }

    CommandPaletteWidget OptionList {
        height: 20;
    }
    """

    def __init__(
        self,
        commands: Optional[List[Dict[str, Any]]] = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._commands = commands or []
        self._filtered_commands = self._commands.copy()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Command Palette", classes="dialog-title")
        yield Input(placeholder="Type to search commands...", id="command-search")
        yield OptionList(id="command-list")

    def on_mount(self) -> None:
        """Handle mount event."""
        self._update_command_list()

    @on(Input.Changed, "#command-search")
    def handle_search(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        query = event.value.lower()

        if not query:
            self._filtered_commands = self._commands.copy()
        else:
            self._filtered_commands = [
                cmd for cmd in self._commands
                if query in cmd.get("name", "").lower() or
                   query in cmd.get("description", "").lower()
            ]

        self._update_command_list()

    def _update_command_list(self) -> None:
        """Update the command list."""
        option_list = self.query_one("#command-list", OptionList)
        option_list.clear_options()

        for cmd in self._filtered_commands:
            name = cmd.get("name", "Unknown")
            description = cmd.get("description", "")
            shortcut = cmd.get("shortcut", "")

            label = f"{name}"
            if shortcut:
                label += f" [{shortcut}]"
            if description:
                label += f" - {description}"

            option_list.add_option(Option(label, id=name))

    @on(OptionList.OptionSelected, "#command-list")
    def handle_command_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle command selection."""
        if event.option_id:
            self.post_message(self.CommandSelected(str(event.option_id)))

    class CommandSelected(Widget.Message):
        """Posted when a command is selected."""

        def __init__(self, command_id: str) -> None:
            super().__init__()
            self.command_id = command_id


# =============================================================================
# PHASE 4: ADVANCED WIDGETS
# =============================================================================


class MetricsDashboardWidget(Widget):
    """
    CPU/memory/network metrics dashboard with sparklines.

    Features:
    - Real-time metric tracking
    - Sparkline charts
    - Threshold alerts
    - Historical data
    """

    DEFAULT_CSS = """
    MetricsDashboardWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """

    cpu_usage: reactive[float] = reactive(0.0)
    memory_usage: reactive[float] = reactive(0.0)
    network_sent: reactive[int] = reactive(0)
    network_recv: reactive[int] = reactive(0)

    def __init__(
        self,
        history_size: int = 50,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.history_size = history_size
        self._cpu_history: List[float] = []
        self._memory_history: List[float] = []

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="metrics-content")

    def watch_cpu_usage(self, usage: float) -> None:
        """React to CPU usage change."""
        self._cpu_history.append(usage)
        if len(self._cpu_history) > self.history_size:
            self._cpu_history.pop(0)
        self._update_display()

    def watch_memory_usage(self, usage: float) -> None:
        """React to memory usage change."""
        self._memory_history.append(usage)
        if len(self._memory_history) > self.history_size:
            self._memory_history.pop(0)
        self._update_display()

    def watch_network_sent(self, sent: int) -> None:
        """React to network sent change."""
        self._update_display()

    def watch_network_recv(self, recv: int) -> None:
        """React to network received change."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the metrics display."""
        content = self.query_one("#metrics-content", Static)

        # Build metrics table
        table = Table(title="System Metrics", show_header=True)
        table.add_column("Metric", style="bold")
        table.add_column("Current", justify="right")
        table.add_column("Trend", justify="center")

        # CPU
        cpu_sparkline = self._generate_sparkline(self._cpu_history)
        cpu_color = "red" if self.cpu_usage > 80 else "yellow" if self.cpu_usage > 50 else "green"
        table.add_row(
            "CPU Usage",
            f"[{cpu_color}]{self.cpu_usage:.1f}%[/{cpu_color}]",
            cpu_sparkline,
        )

        # Memory
        mem_sparkline = self._generate_sparkline(self._memory_history)
        mem_color = "red" if self.memory_usage > 80 else "yellow" if self.memory_usage > 50 else "green"
        table.add_row(
            "Memory Usage",
            f"[{mem_color}]{self.memory_usage:.1f}%[/{mem_color}]",
            mem_sparkline,
        )

        # Network
        table.add_row(
            "Network Sent",
            self._format_bytes(self.network_sent),
            "",
        )
        table.add_row(
            "Network Recv",
            self._format_bytes(self.network_recv),
            "",
        )

        content.update(table)

    def _generate_sparkline(self, data: List[float]) -> str:
        """Generate a simple ASCII sparkline."""
        if not data:
            return ""

        # Sparkline characters
        chars = "▁▂▃▄▅▆▇█"

        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val or 1

        sparkline = ""
        for value in data[-20:]:  # Last 20 values
            normalized = (value - min_val) / range_val
            index = int(normalized * (len(chars) - 1))
            sparkline += chars[index]

        return sparkline

    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} PB"


class TimelineWidget(Widget):
    """
    Test execution timeline visualization.

    Features:
    - Chronological test execution
    - Duration bars
    - Parallel execution tracking
    - Interactive timeline
    """

    DEFAULT_CSS = """
    TimelineWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    TimelineWidget VerticalScroll {
        height: 100%;
    }
    """

    test_events: reactive[List[Dict[str, Any]]] = reactive(list, layout=True)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with VerticalScroll():
            yield Static(id="timeline-content")

    def watch_test_events(self, events: List[Dict[str, Any]]) -> None:
        """React to test events change."""
        self._update_display()

    def add_event(self, test_name: str, event_type: str, timestamp: datetime) -> None:
        """
        Add a timeline event.

        Args:
            test_name: Name of the test
            event_type: Type of event (start, end, error)
            timestamp: Event timestamp
        """
        self.test_events = self.test_events + [{
            "test_name": test_name,
            "event_type": event_type,
            "timestamp": timestamp,
        }]

    def _update_display(self) -> None:
        """Update the timeline display."""
        content = self.query_one("#timeline-content", Static)

        if not self.test_events:
            content.update("No test events yet")
            return

        # Group events by test
        test_timelines: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for event in self.test_events:
            test_timelines[event["test_name"]].append(event)

        # Build timeline text
        text = Text()

        for test_name, events in sorted(test_timelines.items()):
            # Find start and end events
            start_event = next((e for e in events if e["event_type"] == "start"), None)
            end_event = next((e for e in events if e["event_type"] == "end"), None)

            if start_event and end_event:
                duration = (end_event["timestamp"] - start_event["timestamp"]).total_seconds()
                bar_length = int(duration * 10)  # Scale for display

                time_str = start_event["timestamp"].strftime("%H:%M:%S")
                text.append(f"[{time_str}] ", style="dim")
                text.append(test_name, style="bold")
                text.append(" ")
                text.append("█" * min(bar_length, 50), style="cyan")
                text.append(f" {duration:.2f}s\n")

        content.update(Panel(text, title="Timeline"))


class CacheStatsWidget(Widget):
    """
    Cache hit rates and performance statistics.

    Features:
    - Hit/miss ratios
    - Cache size tracking
    - Performance metrics
    - Eviction statistics
    """

    DEFAULT_CSS = """
    CacheStatsWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """

    cache_hits: reactive[int] = reactive(0)
    cache_misses: reactive[int] = reactive(0)
    cache_size: reactive[int] = reactive(0)
    cache_max_size: reactive[int] = reactive(1000)
    evictions: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="cache-content")

    def watch_cache_hits(self, hits: int) -> None:
        """React to cache hits change."""
        self._update_display()

    def watch_cache_misses(self, misses: int) -> None:
        """React to cache misses change."""
        self._update_display()

    def watch_cache_size(self, size: int) -> None:
        """React to cache size change."""
        self._update_display()

    def watch_evictions(self, evictions: int) -> None:
        """React to evictions change."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the cache stats display."""
        content = self.query_one("#cache-content", Static)

        # Calculate statistics
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        fill_rate = (self.cache_size / self.cache_max_size * 100) if self.cache_max_size > 0 else 0

        # Build stats table
        table = Table(title="Cache Statistics", show_header=False)
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Cache Hits", f"[green]{self.cache_hits}[/green]")
        table.add_row("Cache Misses", f"[red]{self.cache_misses}[/red]")
        table.add_row("Hit Rate", f"{hit_rate:.2f}%")
        table.add_row("Cache Size", f"{self.cache_size} / {self.cache_max_size}")
        table.add_row("Fill Rate", f"{fill_rate:.1f}%")
        table.add_row("Evictions", str(self.evictions))

        content.update(table)


class ExportDialogWidget(Widget):
    """
    Export options dialog for test results.

    Features:
    - Multiple export formats
    - Output destination selection
    - Format-specific options
    - Preview capability
    """

    DEFAULT_CSS = """
    ExportDialogWidget {
        align: center middle;
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    ExportDialogWidget Input {
        margin: 1 0;
    }

    ExportDialogWidget Button {
        margin: 1 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Export Test Results", classes="dialog-title")

        yield Label("Format:")
        yield OptionList(
            Option("HTML Report", id="html"),
            Option("JSON Data", id="json"),
            Option("CSV Summary", id="csv"),
            Option("Screenshot", id="screenshot"),
            id="format-list",
        )

        yield Label("Output Path:")
        yield Input(
            placeholder="Path to save export",
            id="output-path",
            value="./test-results",
        )

        yield Label("Options:")
        yield Checkbox("Include logs", id="include-logs", value=True)
        yield Checkbox("Include screenshots", id="include-screenshots", value=False)
        yield Checkbox("Include metrics", id="include-metrics", value=True)

        with Horizontal():
            yield Button("Export", variant="primary", id="export-button")
            yield Button("Cancel", variant="default", id="cancel-export")

    @on(Button.Pressed, "#export-button")
    def handle_export(self) -> None:
        """Handle export button press."""
        selected_format = None
        format_list = self.query_one("#format-list", OptionList)
        if format_list.highlighted is not None:
            option = format_list.get_option_at_index(format_list.highlighted)
            selected_format = option.id if option else None

        export_options = {
            "format_type": selected_format,
            "output_path": self.query_one("#output-path", Input).value,
            "include_logs": self.query_one("#include-logs", Checkbox).value,
            "include_screenshots": self.query_one("#include-screenshots", Checkbox).value,
            "include_metrics": self.query_one("#include-metrics", Checkbox).value,
        }
        self.post_message(self.ExportRequested(export_options))

    @on(Button.Pressed, "#cancel-export")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.post_message(self.ExportCancelled())

    class ExportRequested(Widget.Message):
        """Posted when export is requested."""

        def __init__(self, options: Dict[str, Any]) -> None:
            super().__init__()
            self.options = options

    class ExportCancelled(Widget.Message):
        """Posted when export is cancelled."""
        pass


# =============================================================================
# PHASE 5: COLLABORATION WIDGETS
# =============================================================================


class MultiEndpointWidget(Widget):
    """
    Compare test results across multiple endpoints.

    Features:
    - Side-by-side comparison
    - Diff highlighting
    - Per-endpoint statistics
    - Sync/async execution
    """

    DEFAULT_CSS = """
    MultiEndpointWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    MultiEndpointWidget VerticalScroll {
        height: 100%;
    }
    """

    endpoint_results: reactive[Dict[str, Dict[str, Any]]] = reactive(dict, layout=True)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with VerticalScroll():
            yield Static(id="endpoint-content")

    def watch_endpoint_results(self, results: Dict[str, Dict[str, Any]]) -> None:
        """React to endpoint results change."""
        self._update_display()

    def update_endpoint(self, endpoint: str, results: Dict[str, Any]) -> None:
        """
        Update results for a specific endpoint.

        Args:
            endpoint: Endpoint identifier
            results: Test results for this endpoint
        """
        current = self.endpoint_results.copy()
        current[endpoint] = results
        self.endpoint_results = current

    def _update_display(self) -> None:
        """Update the multi-endpoint display."""
        content = self.query_one("#endpoint-content", Static)

        if not self.endpoint_results:
            content.update("No endpoint results yet")
            return

        # Build comparison table
        table = Table(title="Multi-Endpoint Comparison", show_header=True)
        table.add_column("Metric", style="bold")

        for endpoint in sorted(self.endpoint_results.keys()):
            table.add_column(endpoint, justify="center")

        # Add metrics rows
        metrics = ["total", "passed", "failed", "skipped", "avg_duration"]

        for metric in metrics:
            row = [metric.replace("_", " ").title()]

            for endpoint in sorted(self.endpoint_results.keys()):
                results = self.endpoint_results[endpoint]
                value = results.get(metric, 0)

                if metric == "avg_duration":
                    row.append(f"{value:.3f}s")
                elif metric == "passed":
                    row.append(f"[green]{value}[/green]")
                elif metric == "failed":
                    row.append(f"[red]{value}[/red]")
                elif metric == "skipped":
                    row.append(f"[yellow]{value}[/yellow]")
                else:
                    row.append(str(value))

            table.add_row(*row)

        content.update(table)


class TeamViewWidget(Widget):
    """
    Show active team members and their test sessions.

    Features:
    - Online user list
    - Current test activity
    - User avatars/indicators
    - Real-time updates
    """

    DEFAULT_CSS = """
    TeamViewWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """

    team_members: reactive[List[Dict[str, Any]]] = reactive(list, layout=True)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="team-content")

    def watch_team_members(self, members: List[Dict[str, Any]]) -> None:
        """React to team members change."""
        self._update_display()

    def add_member(self, member_id: str, name: str, status: str = "online") -> None:
        """
        Add or update a team member.

        Args:
            member_id: Unique member identifier
            name: Display name
            status: Member status (online, away, testing)
        """
        current = self.team_members.copy()

        # Update or add member
        for member in current:
            if member["id"] == member_id:
                member["name"] = name
                member["status"] = status
                member["last_seen"] = datetime.now()
                break
        else:
            current.append({
                "id": member_id,
                "name": name,
                "status": status,
                "last_seen": datetime.now(),
            })

        self.team_members = current

    def remove_member(self, member_id: str) -> None:
        """
        Remove a team member.

        Args:
            member_id: Unique member identifier
        """
        self.team_members = [
            m for m in self.team_members if m["id"] != member_id
        ]

    def _update_display(self) -> None:
        """Update the team view display."""
        content = self.query_one("#team-content", Static)

        if not self.team_members:
            content.update("No team members online")
            return

        # Build team list
        table = Table(title="Team Activity", show_header=True)
        table.add_column("Status", width=8)
        table.add_column("Name", style="bold")
        table.add_column("Last Seen", justify="right")

        for member in self.team_members:
            # Status indicator
            status = member.get("status", "offline")
            if status == "online":
                status_icon = "[green]●[/green]"
            elif status == "away":
                status_icon = "[yellow]●[/yellow]"
            elif status == "testing":
                status_icon = "[blue]●[/blue]"
            else:
                status_icon = "[dim]●[/dim]"

            # Time since last seen
            last_seen = member.get("last_seen", datetime.now())
            time_diff = (datetime.now() - last_seen).total_seconds()

            if time_diff < 60:
                time_str = "just now"
            elif time_diff < 3600:
                time_str = f"{int(time_diff / 60)}m ago"
            else:
                time_str = f"{int(time_diff / 3600)}h ago"

            table.add_row(
                status_icon,
                member.get("name", "Unknown"),
                time_str,
            )

        content.update(table)


class BroadcastWidget(Widget):
    """
    WebSocket status and broadcast events.

    Features:
    - Connection status
    - Event stream
    - Message history
    - Reconnection handling
    """

    DEFAULT_CSS = """
    BroadcastWidget {
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    BroadcastWidget VerticalScroll {
        height: 100%;
    }
    """

    is_connected: reactive[bool] = reactive(False)
    connection_url: reactive[str] = reactive("")
    events: reactive[List[Dict[str, Any]]] = reactive(list, layout=True)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="connection-status")
        with VerticalScroll():
            yield Static(id="broadcast-events")

    def watch_is_connected(self, connected: bool) -> None:
        """React to connection status change."""
        self._update_status()

    def watch_connection_url(self, url: str) -> None:
        """React to connection URL change."""
        self._update_status()

    def watch_events(self, events: List[Dict[str, Any]]) -> None:
        """React to events change."""
        self._update_events()

    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Add a broadcast event.

        Args:
            event_type: Type of event
            data: Event data
        """
        self.events = self.events + [{
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(),
        }]

    def _update_status(self) -> None:
        """Update the connection status display."""
        status = self.query_one("#connection-status", Static)

        if self.is_connected:
            status_text = Text()
            status_text.append("● ", style="green")
            status_text.append("Connected ", style="bold green")
            if self.connection_url:
                status_text.append(f"to {self.connection_url}", style="dim")
        else:
            status_text = Text()
            status_text.append("● ", style="red")
            status_text.append("Disconnected", style="bold red")

        status.update(status_text)

    def _update_events(self) -> None:
        """Update the events display."""
        events_content = self.query_one("#broadcast-events", Static)

        if not self.events:
            events_content.update("No events yet")
            return

        # Build events text
        text = Text()

        for event in self.events[-50:]:  # Show last 50 events
            timestamp = event["timestamp"].strftime("%H:%M:%S")
            event_type = event["type"]

            text.append(f"[{timestamp}] ", style="dim")
            text.append(f"{event_type}\n", style="cyan")

            # Show event data
            for key, value in event["data"].items():
                text.append(f"  {key}: {value}\n", style="dim")

        events_content.update(text)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_default_commands() -> List[Dict[str, Any]]:
    """
    Create default command palette commands.

    Returns:
        List of command dictionaries
    """
    return [
        {
            "name": "run_all",
            "description": "Run all tests",
            "shortcut": "Ctrl+R",
            "category": "test",
        },
        {
            "name": "run_selected",
            "description": "Run selected tests",
            "shortcut": "Ctrl+Shift+R",
            "category": "test",
        },
        {
            "name": "filter_tests",
            "description": "Filter tests",
            "shortcut": "Ctrl+F",
            "category": "view",
        },
        {
            "name": "clear_logs",
            "description": "Clear log output",
            "shortcut": "Ctrl+L",
            "category": "view",
        },
        {
            "name": "export_results",
            "description": "Export test results",
            "shortcut": "Ctrl+E",
            "category": "file",
        },
        {
            "name": "toggle_reload",
            "description": "Toggle auto-reload",
            "shortcut": "Ctrl+W",
            "category": "test",
        },
        {
            "name": "show_metrics",
            "description": "Show metrics dashboard",
            "shortcut": "Ctrl+M",
            "category": "view",
        },
        {
            "name": "quit",
            "description": "Quit application",
            "shortcut": "Ctrl+Q",
            "category": "app",
        },
    ]
