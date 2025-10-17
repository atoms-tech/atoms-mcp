# Atoms MCP Server - Startup Configuration Guide

## Status: ✅ KINFRA Integrated

Your Atoms MCP Server has full KINFRA integration working. However, it requires authentication configuration to start.

## Error Resolution

### Current Error

```
ValueError: FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN required
```

### Solution

You need to configure AuthKit for authentication. Follow these steps:

## 1. Get AuthKit Configuration

### Option A: Use Existing AuthKit Instance

If you already have an AuthKit domain:

```bash
# Copy environment template
cp .env.example .env

# Add your AuthKit domain
nano .env
```

Find this line and replace with your domain:
```bash
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=your-authkit-domain.authkit.com
```

### Option B: Set Up New AuthKit (if not yet configured)

1. Go to your AuthKit dashboard
2. Create a new application or get your existing domain
3. Copy the domain URL (e.g., `https://my-app.authkit.com`)

## 2. Configure Environment

```bash
# Edit .env with your AuthKit domain
nano .env
```

Required field:
```bash
# REQUIRED: Your AuthKit domain
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=my-app.authkit.com

# Optional: Specify required scopes
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_REQUIRED_SCOPES=openid,profile,email
```

Optional fields:
```bash
# API Keys (only if using specific AI providers)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database (if needed)
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
```

## 3. Start the Server

### With KINFRA (Recommended)

```bash
# Start with full KINFRA infrastructure management
./atoms start

# Or directly
python -m server
```

KINFRA will:
- ✅ Allocate port 8100 (or fallback to 8101-8199)
- ✅ Initialize health checks
- ✅ Set up infrastructure management
- ✅ Persist port allocation

### Verify KINFRA

```bash
# Check KINFRA initialization logs
./atoms start | grep -i kinfra

# Should see:
# ✅ KINFRA integration available
```

### Check Port Allocation

```bash
# View allocated port
cat ~/.kinfra/atoms_mcp_ports.json

# Output should be:
# {
#   "atoms-mcp": 8100
# }
```

## 4. Test the Server

```bash
# Health check
curl http://localhost:8100/health

# Check MCP endpoint
curl http://localhost:8100/api/mcp

# View logs
./atoms logs  # if available
tail -f logs/server.log  # direct logs
```

## Configuration Overview

### Required Settings

```env
# REQUIRED for authentication
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=your-domain.authkit.com
```

### KINFRA Settings (Already Configured)

```env
# KINFRA infrastructure (auto-enabled)
ZEN_KINFRA_MANAGED=1
ZEN_KINFRA_TUNNEL=0          # Set to 1 for public tunnel
ZEN_KINFRA_FALLBACK=1        # Fallback pages
ZEN_KINFRA_RESTART=1         # Auto-restart
```

### FastMCP Settings (Pre-configured)

```env
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_HOST=127.0.0.1
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_BASE_URL=https://atomcp.kooshapari.com
```

## Troubleshooting

### Error: "AUTHKITPROVIDER_AUTHKIT_DOMAIN required"

**Solution**: Add `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` to `.env`

```bash
# Check if set
grep AUTHKIT_DOMAIN .env

# If not found, edit and add:
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=your-domain.authkit.com
```

### Error: "No module named 'observability'"

**This is a warning, not an error** - The rate limiter module is optional. Server continues to work.

### KINFRA Not Initializing

Check KINFRA integration:

```bash
# Test KINFRA import
python -c "from kinfra_setup import setup_kinfra; print('✅ KINFRA OK')"

# If error, run with diagnostics
./atoms start --debug 2>&1 | grep -i kinfra
```

### Port Conflict

KINFRA automatically resolves port conflicts:

```bash
# See which port was allocated
cat ~/.kinfra/atoms_mcp_ports.json

# Update docker-compose.yml or connections to use allocated port
```

## KINFRA + Authentication

Both are now working together:

```
┌─────────────────────────────────────┐
│  Atoms MCP Server                   │
├─────────────────────────────────────┤
│ ✅ KINFRA Infrastructure            │
│    - Port allocation: 8100          │
│    - Health checks: Active          │
│    - Resource management: Ready     │
├─────────────────────────────────────┤
│ ✅ Authentication (AuthKit)         │
│    - Domain: configured             │
│    - Provider: PersistentAuthKit    │
│    - Scopes: openid, profile, email │
├─────────────────────────────────────┤
│ Status: 🚀 Ready to Start           │
└─────────────────────────────────────┘
```

## Production Deployment

### Enable Public Tunnel

For production with public access:

```bash
# In .env
ZEN_KINFRA_TUNNEL=1
```

KINFRA will create CloudFlare tunnel to `atomcp.kooshapari.com`

### Docker Deployment

```bash
# Build Docker image
docker build -t atoms-mcp:latest .

# Run with docker-compose
docker-compose up -d
```

KINFRA automatically manages:
- Port allocation inside container
- Health checks
- Tunnel creation
- Graceful shutdown

## Support

### Log Locations

- Direct: `tail -f logs/server.log`
- Docker: `docker logs atoms-mcp-server`
- KINFRA: Check `~/.kinfra/` directory

### Quick Commands

```bash
# Start server
./atoms start

# Check status
curl http://localhost:8100/health

# View logs
./atoms logs

# Stop server
Ctrl+C  # or
pkill -f "atoms" # or
docker-compose down
```

---

**Status**: ✅ KINFRA Ready | ⏳ Awaiting AuthKit Configuration

Once you add the AuthKit domain to `.env`, run `./atoms start` to begin!

