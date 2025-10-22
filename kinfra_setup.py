#!/usr/bin/env python3
"""Legacy wrapper delegating to the consolidated atoms CLI."""

from __future__ import annotations

from pathlib import Path

from infra_common import ProjectSettings, run_cli

ROOT = Path(__file__).resolve().parent.parent

SETTINGS = ProjectSettings(
    name="atoms-mcp",
    display_name="Atoms MCP",
    project_root=ROOT / "atoms-mcp-prod",
    config_path=ROOT / "atoms-mcp-prod" / "kinfra_config.yaml",
    state_file=ROOT / "atoms-mcp-prod" / ".infra_state.json",
    default_command=["python", "-m", "server"],
    default_workdir=Path("."),
    default_env={},
    default_port=8100,
    default_domain="atoms.kooshapari.com",
    default_kill_existing=False,
    default_enable_tunnel=False,
)


def main() -> int:
    return run_cli(SETTINGS)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
