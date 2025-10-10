#!/usr/bin/env python3
"""Backward-compatible shim that delegates to the consolidated `atoms` CLI."""

from atoms import main


def _run() -> int:
    """Execute the shared CLI entry point."""
    return main()


if __name__ == "__main__":
    raise SystemExit(_run())
