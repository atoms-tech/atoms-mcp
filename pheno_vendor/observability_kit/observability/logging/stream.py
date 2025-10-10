"""Helpers for streaming structured log output from files."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncIterator, Dict, Optional, Callable, Any


async def stream_log_file(
    path: Path,
    *,
    follow: bool = True,
    decoder: Optional[Callable[[str], Any]] = None,
    poll_interval: float = 0.5,
) -> AsyncIterator[Dict[str, Any]]:
    """Yield structured log entries from a file.

    Args:
        path: Path to the log file to stream.
        follow: When True, keeps tailing the file, otherwise stops at EOF.
        decoder: Optional callable that converts a raw line into a structured
            payload. Defaults to JSON decoding.
        poll_interval: Sleep interval when waiting for new data in follow mode.

    Yields:
        Dicts representing structured log events. If decoding fails the
        ``raw`` line is returned alongside an ``error`` key.
    """

    decoder = decoder or _default_decoder

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        if follow:
            handle.seek(0, 2)

        while True:
            line = handle.readline()
            if not line:
                if not follow:
                    break
                await asyncio.sleep(poll_interval)
                continue

            line = line.strip()
            if not line:
                continue

            try:
                payload = decoder(line)
                if isinstance(payload, dict):
                    yield payload
                else:
                    yield {"data": payload}
            except Exception:  # pragma: no cover - diagnostics only
                yield {"raw": line, "error": "decode_failed"}


def _default_decoder(line: str) -> Dict[str, Any]:
    """Parse a JSON log line into a dictionary."""
    return json.loads(line)


__all__ = ["stream_log_file"]
