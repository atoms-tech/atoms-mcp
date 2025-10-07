# TUI Status Monitoring Enhancement Guide

## Overview

The Atoms MCP Test Dashboard TUI has been enhanced with comprehensive status monitoring widgets that provide real-time visibility into system health, authentication status, network connectivity, and resource usage.

## New Status Monitoring Widgets

### 1. OAuthStatusWidget

**Purpose**: Monitor OAuth token status with expiry countdown and cache location display.

**Features**:
- Token status indicator (Valid/Expiring/Expired/Missing)
- Time until expiry countdown (hours and minutes)
- Cache location display
- Color-coded status:
  - 🟢 Green: Valid token (>1 hour remaining)
  - 🟡 Yellow: Expiring soon (<1 hour remaining)
  - 🔴 Red: Expired or missing token
- Quick action: Press 'O' to clear OAuth cache

**Implementation Details**:
- Located at lines 79-192 in `tui.py`
- Reactive attributes: `token_cached`, `token_expired`, `cache_location`, `time_until_expiry`
- Auto-refreshes every 5 seconds
- Reads token from `~/.fastmcp/oauth-mcp-client-cache/`

### 2. ServerStatusWidget

**Purpose**: Display MCP server connection status with real-time latency monitoring.

**Features**:
- Connection status (Connected/Disconnected)
- Server endpoint display (auto-truncated if long)
- Real-time latency display (color-coded by performance)
- Last successful check timestamp
- Server version display (if available)
- Error message display when connection fails
- Color-coded latency:
  - 🟢 Green: <100ms (excellent)
  - 🟡 Yellow: 100-500ms (acceptable)
  - 🔴 Red: >500ms (slow)
- Quick action: Press Ctrl+H to run health check

**Implementation Details**:
- Located at lines 194-296 in `tui.py`
- Reactive attributes: `endpoint`, `connected`, `last_ping`, `latency_ms`, `server_version`, `error_message`
- Health check uses `list_tools()` as ping
- Auto-refreshes every 5 seconds

### 3. TunnelStatusWidget

**Purpose**: Monitor development tunnel status (ngrok, cloudflare, custom).

**Features**:
- Tunnel status (Active/Inactive)
- Tunnel type indicator (ngrok/cloudflare/custom)
- Public tunnel URL display
- Connection count (for ngrok)
- Uptime tracking
- Configuration hints when inactive

**Supported Tunnels**:
- **ngrok**: Auto-detects via http://localhost:4040/api/tunnels
- **cloudflare**: Placeholder for cloudflared integration
- **custom**: Manual URL configuration

**Implementation Details**:
- Located at lines 298-410 in `tui.py`
- Reactive attributes: `tunnel_active`, `tunnel_url`, `tunnel_type`, `connection_count`, `uptime`
- Auto-refreshes every 5 seconds
- ngrok detection requires ngrok API accessible

### 4. ResourceStatusWidget

**Purpose**: Monitor system resources (database, Redis, API limits, memory).

**Features**:
- Database connection status with latency
- Redis connection status with latency
- API rate limit tracking (remaining/total)
- Memory usage monitoring
- Active connections counter
- Color-coded indicators for all metrics

**Configurable Checks**:
- Database monitoring (optional)
- Redis monitoring (optional)
- API rate limits (optional)
- Memory usage (always on if psutil available)

**Implementation Details**:
- Located at lines 412-562 in `tui.py`
- Reactive attributes: `db_connected`, `redis_connected`, `api_rate_limit`, `memory_usage_mb`
- Auto-refreshes every 5 seconds
- Requires `psutil` for memory monitoring

## Dashboard Layout

The enhanced TUI uses a 4-column, 5-row grid layout:

```
┌─────────────────────────────────────────────────────────┐
│                    Header (Clock)                        │
├──────────┬──────────┬──────────┬─────────────────────────┤
│  OAuth   │  Server  │  Tunnel  │      Resources          │ Row 1: Status Bar
├──────────┴──────────┴──────────┴─────────────────────────┤
│                Test Summary (4 columns)                   │ Row 2: Summary
├───────────────────────────────────────┬───────────────────┤
│        Progress (3 cols)              │  Metrics (1 col)  │ Row 3: Progress
├───────────┬───────────┬───────────────┴───────────────────┤
│ Test Tree │  Output   │        Live Monitor               │ Row 4: Main View
├───────────┴───────────┼───────────────────────────────────┤
│      Logs (2 cols)    │     Team Visibility (1 col)       │ Row 5: Bottom
├───────────────────────┴───────────────────────────────────┤
│                    Footer (Shortcuts)                     │
└─────────────────────────────────────────────────────────┘
```

## Keyboard Shortcuts

### Status Monitoring
- `Ctrl+H` - Run health check (manually refresh all status widgets)
- `O` - Clear OAuth cache (forces re-authentication)

### Existing Shortcuts
- `H` or `?` - Show help with all shortcuts
- `R` - Run all tests
- `Q` or `Esc` - Quit application

## Configuration

### Basic Usage

```python
from tests.framework.oauth_cache import CachedOAuthClient
from tests.framework.tui import run_tui_dashboard

# Initialize OAuth client
oauth_client = CachedOAuthClient(
    mcp_url="https://mcp.example.com",
    client_name="My Test Suite"
)

# Run dashboard with status monitoring
run_tui_dashboard(
    endpoint="https://mcp.example.com",
    test_modules=["tests.test_example"],
    oauth_cache_client=oauth_client,
)
```

### Full Configuration

```python
# Configure tunnel monitoring
tunnel_config = {
    "type": "ngrok",  # or "cloudflare", "custom"
    "url": "https://custom.example.com",  # for custom tunnels
}

# Configure resource monitoring
resource_config = {
    "check_db": True,
    "db_config": {
        "host": "localhost",
        "port": 5432,
    },
    "check_redis": True,
    "redis_config": {
        "host": "localhost",
        "port": 6379,
    },
    "check_api_limits": True,
}

# Run with full monitoring
run_tui_dashboard(
    endpoint="https://mcp.example.com",
    test_modules=["tests.test_example"],
    oauth_cache_client=oauth_client,
    tunnel_config=tunnel_config,
    resource_config=resource_config,
    enable_live_reload=True,
    watch_paths=["tools/", "tests/"],
    enable_websocket=True,
)
```

### Local Development Configuration

```python
# Minimal config for local development
run_tui_dashboard(
    endpoint="http://localhost:8000",
    test_modules=["tests.test_example"],
    tunnel_config={"type": "ngrok"},
    enable_live_reload=True,
    watch_paths=["src/", "tests/"],
)
```

## Auto-Refresh Behavior

All status widgets automatically refresh every 5 seconds:

1. **OAuthStatusWidget**: Checks token file existence and expiry
2. **ServerStatusWidget**: Pings server with `list_tools()` call
3. **TunnelStatusWidget**: Checks ngrok API or custom tunnel config
4. **ResourceStatusWidget**: Monitors DB, Redis, API limits, memory

Manual refresh available via `Ctrl+H` (health check).

## Dependencies

### Required
- `textual` - TUI framework
- `fastmcp` - MCP client

### Optional
- `psutil` - Memory usage monitoring
- `requests` - ngrok API checks
- `asyncpg` or `psycopg2` - Database monitoring
- `redis` - Redis monitoring

## Error Handling

All status widgets gracefully degrade when:
- Dependencies are missing (show "Not configured")
- Services are unavailable (show error message)
- Configuration is incomplete (show configuration hints)

No widget failure will crash the TUI - errors are logged and displayed.

## Examples

See `example_tui_with_status.py` for complete working examples:
- Full featured dashboard with all monitoring
- Minimal dashboard (OAuth + Server only)
- Local development setup with ngrok

## Architecture

### Widget Lifecycle

1. **Initialization**: Widgets created with configuration in `compose()`
2. **Mount**: Initial status check on `on_mount()`
3. **Auto-refresh**: `set_interval(5.0, _refresh_status_widgets)` runs every 5s
4. **Manual refresh**: `action_health_check()` triggered by Ctrl+H
5. **Cleanup**: Widgets dispose on app unmount

### Reactive Attributes

All status widgets use Textual's reactive system:
- Changes to reactive attributes automatically trigger re-render
- No manual refresh calls needed in most cases
- Thread-safe updates via Textual's message queue

## Performance

- **Minimal overhead**: Status checks are async and non-blocking
- **Configurable**: Disable checks by not providing config
- **Efficient**: Only enabled widgets perform checks
- **Throttled**: 5-second intervals prevent API rate limiting

## Troubleshooting

### OAuth widget shows "Missing"
- Check if OAuth token file exists at `~/.fastmcp/oauth-mcp-client-cache/`
- Run test suite once to generate token
- Press 'O' to clear cache and re-authenticate

### Server widget shows "Disconnected"
- Verify endpoint URL is correct
- Check network connectivity
- Ensure MCP server is running
- Check firewall/proxy settings

### Tunnel widget shows "No tunnel active"
- For ngrok: Verify ngrok is running and API is accessible at localhost:4040
- For custom: Provide `url` in `tunnel_config`
- Check tunnel process is actually running

### Resource widget shows "No resources configured"
- Add `resource_config` parameter to `run_tui_dashboard()`
- Install required dependencies (psutil, redis, etc.)
- Enable specific checks in config

## Future Enhancements

Potential improvements:
- Configurable refresh interval (currently fixed at 5s)
- Historical graphs for latency/memory over time
- Alert thresholds with notifications
- Export status reports
- WebSocket broadcasting of status to team
- Custom health check endpoints
- Prometheus metrics export

## Contributing

When adding new status widgets:
1. Extend from `Static` class
2. Define reactive attributes
3. Implement `render()` method returning `Panel`
4. Implement `refresh_status()` async method
5. Add widget to grid in `compose()`
6. Add refresh call in `_refresh_status_widgets()`
7. Update keyboard shortcuts if applicable
8. Document in this guide

## License

Part of the Atoms MCP Test Framework.
