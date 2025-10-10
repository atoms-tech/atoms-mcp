"""Rich console logging helpers for PyDevKit.

Provides structured logging setup, Rich-based progress indicators, and
human-friendly status helpers with graceful fallbacks when optional
dependencies are unavailable.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional

# Optional Rich dependency
try:  # pragma: no cover - optional dependency
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )
    from rich.text import Text

    HAS_RICH = True
except ImportError:  # pragma: no cover
    Console = None  # type: ignore
    Progress = None  # type: ignore
    Panel = None  # type: ignore
    Text = None  # type: ignore
    SpinnerColumn = TextColumn = BarColumn = TaskProgressColumn = None  # type: ignore
    HAS_RICH = False

# Optional observability-kit dependency for structured JSON logs
try:  # pragma: no cover - optional dependency
    from observability.logging.structured import StructuredFormatter

    HAS_STRUCTURED = True
except ImportError:  # pragma: no cover
    StructuredFormatter = None  # type: ignore
    HAS_STRUCTURED = False

_LOGGING_CONFIGURED = False
_LOG_LEVEL = "WARNING"
_DEFAULT_FORMAT = "%(levelname)s | %(name)s | %(message)s"
_DEFAULT_FORMAT_WITH_TS = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(
    *,
    level: str = "WARNING",
    fmt: str = "plain",
    use_color: bool = True,
    use_timestamps: bool = True,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> None:
    """Configure root logging handlers.

    Args:
        level: Log level name (DEBUG, INFO, etc.).
        fmt: Either "plain" (default) or "json" for structured output.
        use_color: Currently retained for API compatibility; Rich handles color.
        use_timestamps: Include timestamps in plain output.
        extra_fields: Static metadata to include in structured logs when supported.
    """

    global _LOGGING_CONFIGURED, _LOG_LEVEL

    handlers = []

    if fmt == "json" and HAS_STRUCTURED:
        handler = logging.StreamHandler()
        handler.setFormatter(
            StructuredFormatter(
                include_timestamp=True,
                include_level=True,
                include_logger=True,
                include_context=True,
                extra_fields=extra_fields or {},
            )
        )
        handlers.append(handler)
    else:
        # Plain formatter fallback
        fmt_string = _DEFAULT_FORMAT_WITH_TS if use_timestamps else _DEFAULT_FORMAT
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt_string))
        handlers.append(handler)

    logging.basicConfig(level=getattr(logging, level.upper(), logging.WARNING), handlers=handlers, force=True)

    _LOGGING_CONFIGURED = True
    _LOG_LEVEL = level.upper()


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger, auto-configuring on first use."""

    if not _LOGGING_CONFIGURED:
        setup_logging()
    return logging.getLogger(name)


if HAS_RICH:
    console = Console(stderr=True)
else:  # pragma: no cover - fallback console
    class _FallbackConsole:
        def print(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            print(*args)

    console = _FallbackConsole()  # type: ignore


class ProgressLogger:
    """Context manager providing Rich progress indicators with graceful fallback."""

    def __init__(self, description: str, total: Optional[int] = None):
        self.description = description
        self.total = total
        self.progress = None
        self.task_id = None
        self.logger = get_logger(__name__)

    def __enter__(self):  # pragma: no cover - trivial
        if HAS_RICH and Progress:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn() if self.total else TextColumn(""),
                TaskProgressColumn() if self.total else TextColumn(""),
                console=console,
                transient=True,
            )
            self.progress.start()
            self.task_id = self.progress.add_task(
                self.description,
                total=self.total if self.total else None,
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover - trivial
        if self.progress:
            self.progress.stop()
        return False

    def update(self, description: Optional[str] = None, advance: int = 1):
        if self.progress and self.task_id is not None:
            if description:
                self.progress.update(self.task_id, description=description)
            if self.total:
                self.progress.advance(self.task_id, advance)

    def complete(self, message: Optional[str] = None):
        if self.progress and self.task_id is not None:
            if message:
                self.progress.update(self.task_id, description=message)
            if self.total:
                self.progress.update(self.task_id, completed=self.total)


def _render_text(message: str, style: str = "") -> str:
    if HAS_RICH and Text:
        return str(Text(message, style=style))
    return message


def print_banner(text: str, style: str = "bold cyan") -> None:
    if HAS_RICH and Panel:
        console.print(Panel(Text(text, style=style), border_style="cyan"))
    else:  # pragma: no cover - fallback
        print(f"\n{'=' * 60}\n{text}\n{'=' * 60}\n")


def print_status(emoji: str, message: str, style: str = "") -> None:
    if HAS_RICH:
        console.print(f"{emoji} {_render_text(message, style)}")
    else:  # pragma: no cover - fallback
        print(f"{emoji} {message}")


def print_error(message: str) -> None:
    print_status("❌", message, "bold red")


def print_success(message: str) -> None:
    print_status("✅", message, "bold green")


def print_warning(message: str) -> None:
    print_status("⚠️", message, "bold yellow")


def print_info(message: str) -> None:
    print_status("ℹ️", message, "cyan")


@contextmanager
def quiet_mode():
    global _LOG_LEVEL
    old_level = _LOG_LEVEL
    setup_logging(level="ERROR")
    try:
        yield
    finally:
        setup_logging(level=old_level)


__all__ = [
    "setup_logging",
    "get_logger",
    "ProgressLogger",
    "print_banner",
    "print_status",
    "print_error",
    "print_success",
    "print_warning",
    "print_info",
    "quiet_mode",
    "console",
]
