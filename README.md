# Atoms MCP - Knowledge Management System

Multi-tenant knowledge management system with requirements tracking, test management, and AI-powered search capabilities.

## Quick Start

```bash
# Install dependencies (creates .venv)
uv sync

# Set environment variables
export SUPABASE_URL="https://ydogoylwenufckscqijp.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-key"

# Optional: point to a custom YAML config (defaults live in config/app.defaults.yaml)
# export ATOMS_SETTINGS_FILE="$(pwd)/config/app.yaml"

# Endpoint selection: environment switch (default = production / https://mcp.atoms.tech)
#   local  -> https://atomcp.kooshapari.com
#   dev    -> https://devmcp.atoms.tech
#   preview-> https://devmcp.atoms.tech
#   prod   -> https://mcp.atoms.tech
# export ATOMS_TARGET_ENVIRONMENT=local

# Start server
python start_atoms.sh
```

## CLI Shortcuts

```bash
./atoms start             # Launch local server with defaults
./atoms deploy            # Deploy to production (mcp.atoms.tech)
./atoms deploy dev        # Deploy to preview (devmcp.atoms.tech)
./atoms test local cold   # Run "cold" markers against the local stack
./atoms stats cloc        # Code statistics with cloc (honors .clocignore)
./atoms stats vulture     # Check for unused code via vulture
```

## Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get up and running in 5 minutes
- **[Testing Guide](TESTING_GUIDE.md)** - How to run and write tests
- **[Complete Schema System](COMPLETE_SCHEMA_SYSTEM.md)** - Type-safe schema documentation

### Schema & Database
- **[Schema Documentation](docs/schema/)** - RLS, triggers, sync system
- **[Deployment Guides](docs/deployment/)** - Vercel, WorkOS, 3-tier setup

### Reference
- **[Reference Documentation](docs/reference/)** - Supabase-pydantic, schema reference

## Features

✅ Multi-tenant organization management
✅ Requirements tracking with INCOSE/EARS formats
✅ Test management and traceability
✅ Document blocks with properties
✅ Vector semantic search
✅ Full-text search
✅ OAuth 2.0 authentication
✅ Row-level security
✅ Real-time updates

## Architecture

- **FastAPI/FastMCP** - MCP server
- **Supabase** - PostgreSQL database with vector extensions
- **WorkOS AuthKit** - OAuth authentication
- **Type-safe schemas** - TypedDict + Pydantic validation
- **RLS validation** - Server-side permission checks
- **Trigger emulation** - Client-side data transformation

## Development

```bash
# Run tests
pytest tests/ -v

# Check schema sync
python scripts/sync_schema.py --check

# Sync with database
python scripts/sync_schema.py --update
```

## License

MIT
