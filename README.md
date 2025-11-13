# Atoms MCP Server

This repo contains the FastMCP implementation that powers the Atoms platform. It
packages a single consolidated server (`server.py`) plus the ASGI export in
`app.py`, the hybrid auth provider, infrastructure adapters, and the tool/service
layer that the test suite exercises.

## Getting Started

1. Create a virtualenv and install dependencies via `uv` (preferred):
   ```bash
   uv sync
   ```
2. Activate the env before running any scripts or tests:
   ```bash
   source .venv/bin/activate
   ```
3. Run the FastMCP server locally with:
   ```bash
   uv run python server.py
   ```

## Tests

Run the service/unit tests with:
```bash
uv run pytest
```

## Additional Docs

- `llms-full.txt` — canonical FastMCP contract (authoritative instructions)
- `AGENTS.md`, `CLAUDE.md`, `WARP.md` — repo-specific guidance summaries

Deploy-specific configs live under `vercel.json`, `cloudrun.yaml`, and
`sst.config.ts`. Services/auth/infrastructure directories each contain the
shared abstractions other modules must reuse.
