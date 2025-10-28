# Atoms MCP Server Configuration

## Directory Structure

```
config/
├── __init__.py              # Main module exports
├── settings.py              # Pydantic configuration classes
├── atoms.config.yaml        # Non-sensitive settings with env var defaults
├── atoms.secrets.yaml       # Sensitive settings (should be in .gitignore)
└── backup/                 # Backup of old configuration files
```

## Configuration Files

### atoms.config.yaml
Non-sensitive configurable settings with environment variable defaults:
- Server configuration (host, port, debug, telemetry)
- Tunnel configuration (enabled, hostname, health interval)
- FastMCP configuration (transport, tools)
- Resource limits (memory, connections, timeout)
- Logging configuration (level, format, file size)
- Health check configuration (endpoint, timeout, retries)

### atoms.secrets.yaml
Sensitive settings that must be provided via environment variables:
- Database credentials (password)
- Tunnel secrets (auth_token, account_id)
- API keys (OpenAI, Anthropic)
- Service credentials (MCP secret, JWT secret)

## Environment Variables

All settings can be overridden using `ATOMS_*` environment variables:

### Server
- `ATOMS_HOST` - Server host (default: 0.0.0.0)
- `ATOMS_PORT` - Server port (default: 50002)
- `ATOMS_DEBUG` - Debug mode (default: false)
- `ATOMS_TELEMETRY` - Enable telemetry (default: true)

### Tunnel
- `ATOMS_TUNNEL` - Enable tunnel (default: true)
- `ATOMS_TUNNEL_HOSTNAME` - Tunnel hostname (default: atomcp.kooshapari.com)
- `ATOMS_TUNNEL_AUTH_TOKEN` - Cloudflare auth token
- `ATOMS_CLOUDFLARE_ACCOUNT_ID` - Cloudflare account ID
- `ATOMS_HEALTH_INTERVAL` - Health check interval (default: 30)

### Database
- `ATOMS_DB_HOST` - Database host (default: localhost)
- `ATOMS_DB_PORT` - Database port (default: 5432)
- `ATOMS_DB_USERNAME` - Database username (default: atoms_db_user)
- `ATOMS_DB_PASSWORD` - Database password (required)

### API Keys
- `ATOMS_OPENAI_API_KEY` - OpenAI API key (required)
- `ATOMS_ANTHROPIC_API_KEY` - Anthropic API key (required)

### Service Secrets
- `ATOMS_MCP_SECRET` - MCP service secret (required)
- `ATOMS_JWT_SECRET` - JWT signing secret (required)

### Resources
- `ATOMS_MAX_MEMORY_MB` - Max memory in MB (default: 512)
- `ATOMS_MAX_CONNECTIONS` - Max connections (default: 100)
- `ATOMS_TIMEOUT_SECONDS` - Request timeout (default: 30)

### Logging
- `ATOMS_LOG_LEVEL` - Log level (default: INFO)
- `ATOMS_LOG_FORMAT` - Log format (default: json)
- `ATOMS_LOG_MAX_SIZE_MB` - Max log file size (default: 100)

### Health
- `ATOMS_HEALTH_ENDPOINT` - Health endpoint (default: /health)
- `ATOMS_HEALTH_TIMEOUT` - Health timeout (default: 5)
- `ATOMS_HEALTH_RETRIES` - Health retry attempts (default: 3)

## Usage

```python
from config import app_config, secrets_config, get_config_summary

# Load configuration (automatic on import)
app_config, secrets_config = load_config()

# Access configuration values
port = app_config.server.port
debug = app_config.server.debug
tunnel_hostname = app_config.tunnel.hostname
database_url = secrets_config.database.url

# Get configuration summary
print(get_config_summary(app_config, secrets_config))
```

## FastMCP Project Configuration

The repository now ships with a schema-validated `fastmcp.json` that FastMCP CLI tools read by default. It captures the three pillars from the official documentation:

- **Source** – points at `server/core.py` and calls `create_consolidated_server`, giving the CLI the same consolidated toolset that the `server` package exports.
- **Environment** – uses the `uv` backend, pins Python to `>=3.11`, and installs the repo as an editable project so local code changes are reflected without reinstalls.
- **Deployment** – defaults to `stdio` transport for desktop/CLI clients, sets log level to INFO, and seeds the expected `ATOMS_FASTMCP_*` variables so the existing config loaders pick up sane defaults.

### Running the server

With the config in place you can run the server exactly as described in the FastMCP docs:

```bash
# Auto-detects fastmcp.json in the repo root
fastmcp run

# Explicit file + HTTP overrides for local API testing
fastmcp run fastmcp.json --transport http --port 8080 --host 127.0.0.1

# Re-use an existing virtualenv/uv project
fastmcp run --skip-env
```

### Preparing reusable environments

```bash
# Pre-build an environment for CI/CD or remote hosts
fastmcp project prepare fastmcp.json --output-dir ./.fastmcp-env

# Later, re-use that environment without reinstalling dependencies
fastmcp run fastmcp.json --project ./.fastmcp-env
```

The CLI still honours ad-hoc overrides (e.g. `--with requests`, `--log-level DEBUG`), but `fastmcp.json` is now the single source of truth that can be checked into version control and shared across teams.

### atoms CLI shortcuts

If you prefer the unified `atoms` binary (installed via `uv pip install .` or `uv tool install --from . ./atoms`), the `server` sub-commands now proxy directly to `fastmcp run` and pick up every setting from `fastmcp.json`.

```bash
# Local STDIO transport (default target)
atoms server start

# HTTP transport on a custom port/host for remote testing
atoms server start --target http --host 0.0.0.0 --port 8080 --path /api/mcp

# Background execution and status helpers
atoms server start --target http --background
atoms server status
atoms server stop
```

The CLI stores state under `~/.atoms/` (PID + log files) so you can manage the server from any shell. All overrides (transport/host/path/log-level plus `--skip-env/--skip-source`) are forwarded to `fastmcp run`, which means HTTP deployment guidance from the FastMCP docs applies 1:1 to the CLI workflow.

## Security Notes

- `atoms.secrets.yaml` should be added to `.gitignore`
- All sensitive values use environment variables with `${VAR_NAME}` syntax
- Default values are provided for non-sensitive settings
- Configuration validation is performed by pydantic
