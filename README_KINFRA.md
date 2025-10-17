# Atoms-MCP - KINFRA Integration Guide

**Service:** Atoms-MCP (Knowledge Management System)
**Port:** 8080
**Tunnel:** N/A (Internal Service)
**Status:** Production Ready

---

## Overview

The Atoms-MCP service uses KINFRA for infrastructure management, providing a multi-tenant knowledge management system with requirements tracking, test management, and AI-powered search capabilities. This guide covers Atoms-MCP-specific KINFRA configuration and operations.

## Port Configuration

### Primary Port: 8080

```yaml
# KINFRA port allocation
service_ports:
  atoms-mcp: 8080
  atoms: 8080
  atoms-server: 8080
```

### Port Allocation Strategy

KINFRA will attempt to allocate ports in this order:

1. **Preferred Port:** 8080
2. **Conflict Resolution:** Kill existing process on port 8080 (with confirmation)
3. **Fallback:** Allocate next available port in range 8081-8999
4. **Update:** Automatically update configuration with new port

### Environment Variables

```bash
# .env
ATOMS_PORT=8080
ATOMS_HOST=0.0.0.0

# Supabase configuration
SUPABASE_URL=https://ydogoylwenufckscqijp.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key
SUPABASE_ANON_KEY=your-anon-key

# WorkOS AuthKit (OAuth)
WORKOS_API_KEY=your-key
WORKOS_CLIENT_ID=your-client-id

# KINFRA integration
KINFRA_TUNNEL_ENABLED=false  # Internal service, no tunnel
KINFRA_AUTO_RESTART=true
KINFRA_HEALTH_CHECK_INTERVAL=10
```

---

## Tunnel Configuration

### Internal Service (No Public Tunnel)

Atoms-MCP is designed as an internal service and does not require a public tunnel by default. However, you can enable tunneling if needed:

```yaml
tunnel:
  service: atoms-mcp
  domain: atoms.kooshapari.com  # Optional
  local_port: 8080
  protocol: https
  tunnel_type: quick
  auto_start: false
  health_check: /health
  enabled: false  # Disabled by default
```

### Enable Tunnel (Optional)

If you need public access to Atoms-MCP:

```bash
# Enable tunnel in environment
export KINFRA_TUNNEL_ENABLED=true
export TUNNEL_DOMAIN=atoms.kooshapari.com

# Start with tunnel
python -m kinfra service start atoms-mcp --enable-tunnel

# Or configure in kinfra.yml
echo "tunnel:
  enabled: true
  domain: atoms.kooshapari.com" >> config/kinfra.yml
```

---

## Health Check

### Endpoint: /health

The Atoms-MCP service provides a health check endpoint at `/health`:

**Local:**
```bash
curl http://localhost:8080/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "atoms-mcp",
  "version": "1.0.0",
  "database": "connected",
  "supabase": "connected",
  "uptime": 12345,
  "timestamp": "2025-10-16T12:00:00Z"
}
```

### Additional Health Endpoints

```bash
# Database health
curl http://localhost:8080/health/db

# Supabase health
curl http://localhost:8080/health/supabase

# Full system status
curl http://localhost:8080/status
```

### Health Check Configuration

```python
# KINFRA health check settings
ServiceConfig(
    name="atoms-mcp",
    health_check_url="http://localhost:8080/health",
    health_check_interval=10.0,  # Check every 10 seconds
    restart_on_failure=True,
    max_restart_attempts=3,
    restart_delay=2.0
)
```

---

## Startup Instructions

### Option 1: Using KINFRA Orchestration

```bash
# Start Atoms-MCP with KINFRA
python -m kinfra service start atoms-mcp

# Or use orchestration script
cd /Users/kooshapari/temp-PRODVERCEL/485/kush
python scripts/orchestrate_services.py --start --services atoms-mcp
```

### Option 2: Using Atoms CLI

```bash
# Using Atoms CLI wrapper
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod
./atoms start

# With custom port
./atoms start --port 8081
```

### Option 3: Direct Python

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod

# Using start script
python start_server.py

# Or using uvicorn directly
python -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 8080 \
  --reload
```

### Option 4: Using start_atoms.sh

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod

# Make executable
chmod +x start_atoms.sh

# Start
./start_atoms.sh
```

---

## Fallback Configuration

### Service Down Fallback

When the Atoms-MCP service is down, KINFRA can serve a fallback page:

**Location:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/static/fallback.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Atoms-MCP Service - Maintenance</title>
</head>
<body>
    <h1>Atoms-MCP Service Temporarily Unavailable</h1>
    <p>The knowledge management system is currently undergoing maintenance.</p>
    <p>Please try again in a few moments.</p>
    <p>Status: <a href="/health">Check Health</a></p>
    <h2>Features</h2>
    <ul>
        <li>Multi-tenant organization management</li>
        <li>Requirements tracking (INCOSE/EARS)</li>
        <li>Test management and traceability</li>
        <li>Vector semantic search</li>
        <li>Full-text search</li>
    </ul>
</body>
</html>
```

### Fallback Configuration

```yaml
# KINFRA fallback settings
fallback:
  enabled: true
  page: static/fallback.html
  status_code: 503
  retry_after: 60  # seconds
```

---

## Logs & Monitoring

### Log Locations

| Log Type | Location | Purpose |
|----------|----------|---------|
| Application | `atoms-mcp-prod/logs/atoms.log` | Service logs |
| Access | `atoms-mcp-prod/logs/access.log` | HTTP request logs |
| Error | `atoms-mcp-prod/logs/error.log` | Error logs |
| Database | `atoms-mcp-prod/logs/db.log` | Database query logs |
| KINFRA | `~/.kinfra/logs/atoms-mcp.log` | KINFRA management logs |

### View Logs

```bash
# Application logs
tail -f /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/logs/atoms.log

# Error logs
tail -f /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/logs/error.log

# Database logs
tail -f /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/logs/db.log

# All logs
tail -f /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/logs/*.log
```

### Log Configuration

```yaml
logging:
  level: INFO
  file_path: logs/atoms.log
  max_file_size: 10485760  # 10MB
  backup_count: 5
  enable_file: true
  enable_console: true
```

---

## Restart Procedures

### Graceful Restart

```bash
# Using KINFRA
python -m kinfra service restart atoms-mcp --graceful

# Using orchestration
python scripts/orchestrate_services.py --restart atoms-mcp

# Using Atoms CLI
cd atoms-mcp-prod
./atoms restart

# Using systemctl (if installed as service)
sudo systemctl restart atoms-mcp
```

### Force Restart

```bash
# Using KINFRA
python -m kinfra service restart atoms-mcp --force

# Manual
pkill -9 -f "atoms"
./atoms start
```

### Auto-Restart on Failure

KINFRA automatically restarts the Atoms-MCP service on failure:

```python
# Auto-restart configuration
ServiceConfig(
    name="atoms-mcp",
    restart_on_failure=True,
    max_restart_attempts=3,
    restart_delay=2.0,
    health_check_interval=10.0
)
```

**Restart Behavior:**
1. Health check fails 3 consecutive times
2. Service marked as unhealthy
3. Graceful shutdown (SIGTERM)
4. Wait 5 seconds
5. Force kill if needed (SIGKILL)
6. Restart service
7. Wait 2 seconds
8. Verify health and database connection
9. Increment restart counter

---

## Troubleshooting

### Issue: Port 8080 Already in Use

**Symptom:**
```
ERROR: Port 8080 is already in use by process 12345
```

**Solution:**
```bash
# Option A: Let KINFRA kill the process
python -m kinfra service start atoms-mcp --force-kill

# Option B: Manual kill
lsof -ti:8080 | xargs kill -9

# Option C: Use different port
export ATOMS_PORT=8081
./atoms start
```

### Issue: Supabase Connection Failed

**Symptom:**
```
ERROR: Could not connect to Supabase at https://ydogoylwenufckscqijp.supabase.co
```

**Solution:**
```bash
# Check Supabase URL
echo $SUPABASE_URL

# Check service role key
echo $SUPABASE_SERVICE_ROLE_KEY | wc -c

# Test connection
curl -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  $SUPABASE_URL/rest/v1/

# Verify credentials in .env
cat atoms-mcp-prod/.env | grep SUPABASE

# Test with Python
python -c "
from supabase import create_client
import os
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
client = create_client(url, key)
print('Connection OK')
"
```

### Issue: Health Check Failing

**Symptom:**
```
WARNING: Health check failed for atoms-mcp (3/3)
```

**Solution:**
```bash
# Manual health check
curl -v http://localhost:8080/health

# Check service status
ps aux | grep atoms

# Check logs
tail -f atoms-mcp-prod/logs/error.log

# Check database connection
curl http://localhost:8080/health/db

# Restart service
python -m kinfra service restart atoms-mcp
```

### Issue: Dependencies Missing

**Symptom:**
```
ModuleNotFoundError: No module named 'fastmcp'
```

**Solution:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod

# Install dependencies
uv sync --group dev

# Verify installation
python -c "import fastmcp; print('OK')"

# Install KINFRA
cd ~/KInfra/libraries/python
pip install -e .
```

### Issue: Schema Sync Failed

**Symptom:**
```
ERROR: Schema validation failed - mismatch with database
```

**Solution:**
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod

# Check schema sync status
python scripts/sync_schema.py --check

# Update schema
python scripts/sync_schema.py --update

# View differences
python scripts/sync_schema.py --diff

# Force sync (caution: may lose data)
python scripts/sync_schema.py --force
```

---

## Configuration Reference

### Complete KINFRA Configuration

```yaml
# atoms-mcp-prod/config/kinfra.yml

service:
  name: atoms-mcp
  port: 8080
  host: 0.0.0.0
  auto_start: true

networking:
  port_strategy: preferred
  preferred_port: 8080
  fallback_ports: [8081, 8082, 8083]

tunnel:
  enabled: false  # Internal service
  domain: atoms.kooshapari.com
  type: quick
  auto_start: false
  health_check: /health

health_check:
  enabled: true
  url: http://localhost:8080/health
  interval: 10
  timeout: 5
  max_failures: 3
  check_database: true
  check_supabase: true

restart:
  on_failure: true
  max_attempts: 3
  delay: 2
  backoff: exponential

logging:
  level: INFO
  file: logs/atoms.log
  max_size: 10485760
  backup_count: 5
  enable_console: true

monitoring:
  metrics_enabled: true
  metrics_port: 9092
  metrics_endpoint: /metrics

database:
  provider: supabase
  check_on_startup: true
  migration_on_startup: false
  pool_size: 10
```

---

## Database & Schema Management

### Schema Sync

```bash
# Check schema status
python scripts/sync_schema.py --check

# View differences
python scripts/sync_schema.py --diff

# Update schema
python scripts/sync_schema.py --update

# Dry run
python scripts/sync_schema.py --dry-run
```

### Database Health

```bash
# Check Supabase connection
curl http://localhost:8080/health/db

# Test queries
python -c "
from supabase import create_client
import os
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)
result = client.table('organizations').select('*').limit(1).execute()
print(f'Database OK: {len(result.data)} rows')
"

# Check RLS policies
python scripts/check_rls.py

# Test authentication
python scripts/test_auth.py
```

---

## Quick Reference

### Common Commands

```bash
# Start service
./atoms start

# Stop service
pkill -f atoms

# Restart service
python -m kinfra service restart atoms-mcp

# Check status
curl http://localhost:8080/health

# View logs
tail -f logs/atoms.log

# Sync schema
python scripts/sync_schema.py --check

# Run tests
pytest tests/ -v
```

### Ports & URLs

| Type | Value | Purpose |
|------|-------|---------|
| Local Port | 8080 | Development/internal access |
| Health Check | http://localhost:8080/health | Health monitoring |
| Database Health | http://localhost:8080/health/db | Database monitoring |
| Supabase Health | http://localhost:8080/health/supabase | Supabase monitoring |
| Metrics | http://localhost:9092/metrics | Prometheus metrics |

### Environment Variables

```bash
# Required
SUPABASE_URL=https://ydogoylwenufckscqijp.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key

# Optional
ATOMS_PORT=8080
ATOMS_HOST=0.0.0.0
WORKOS_API_KEY=your-key
WORKOS_CLIENT_ID=your-client-id

# KINFRA
KINFRA_TUNNEL_ENABLED=false
KINFRA_AUTO_RESTART=true
KINFRA_LOG_LEVEL=INFO
```

---

## Testing

### Unit Tests

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_schema.py -v

# Run specific test
pytest tests/test_schema.py::test_schema_validation -v
```

### Integration Tests

```bash
# Test database connection
python tests/test_integration.py

# Test Supabase RLS
python tests/test_rls.py

# Test authentication flow
python tests/test_auth.py

# Full integration test suite
pytest tests/integration/ -v
```

---

## Additional Resources

- [Main KINFRA Documentation](../docs/KINFRA_INTEGRATION.md)
- [Atoms-MCP README](README.md)
- [Quick Start Guide](QUICK_START.md)
- [Testing Guide](TESTING_GUIDE.md)
- [Complete Schema System](COMPLETE_SCHEMA_SYSTEM.md)
- [Schema Documentation](docs/schema/)
- [Deployment Guides](docs/deployment/)
- [KINFRA Core Documentation](~/KInfra/libraries/python/README.md)
- [Supabase Documentation](https://supabase.com/docs)

---

**Service:** Atoms-MCP
**Port:** 8080
**Tunnel:** N/A (Internal)
**Status:** Production Ready
**Last Updated:** 2025-10-16
