#!/bin/bash
# start_local.sh - Launch MCP server and Cloudflare tunnel with automatic cleanup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Atoms MCP Server (Local Mode)${NC}"
echo ""

# Step 1: Cleanup existing processes
echo -e "${YELLOW}📋 Step 1: Cleaning up existing processes...${NC}"

# Kill existing MCP server processes
if pgrep -f "python.*atoms_mcp" > /dev/null; then
    echo "  ⏹  Stopping existing MCP server processes..."
    pkill -f "python.*atoms_mcp" || true
    sleep 1
fi

# Kill existing Cloudflare tunnel
if pgrep -f "cloudflared.*tunnel.*run.*atoms-mcp" > /dev/null; then
    echo "  ⏹  Stopping existing Cloudflare tunnel..."
    pkill -f "cloudflared.*tunnel.*run.*atoms-mcp" || true
    sleep 1
fi

echo -e "${GREEN}  ✅ Cleanup complete${NC}"
echo ""

# Step 2: Start MCP server
echo -e "${YELLOW}📋 Step 2: Starting MCP server...${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "  📄 Loading environment from .env"
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Set environment variables for local development
export ENV=dev
export ATOMS_FASTMCP_TRANSPORT=http
export ATOMS_FASTMCP_HOST=127.0.0.1
export ATOMS_FASTMCP_PORT=8000
export ATOMS_FASTMCP_HTTP_PATH=/api/mcp
export ATOMS_FASTMCP_HTTP_AUTH_MODE=optional

# Start the server in the background
cd "$SCRIPT_DIR/.."
python3 -m atoms_mcp-old.server > /tmp/atoms_mcp.log 2>&1 &
MCP_PID=$!

# Wait for server to be ready
echo "  ⏳ Waiting for MCP server to start..."
sleep 2

# Check if server is running
if ! ps -p $MCP_PID > /dev/null; then
    echo -e "${RED}  ❌ Failed to start MCP server${NC}"
    echo -e "${RED}     Check logs at /tmp/atoms_mcp.log${NC}"
    exit 1
fi

# Test server health
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ MCP server started (PID: $MCP_PID)${NC}"
    echo -e "${GREEN}     Health check: http://127.0.0.1:8000/health${NC}"
else
    echo -e "${YELLOW}  ⚠️  MCP server started but health check failed${NC}"
    echo -e "${YELLOW}     Server may still be initializing...${NC}"
fi

echo ""

# Step 3: Start Cloudflare tunnel
echo -e "${YELLOW}📋 Step 3: Starting Cloudflare tunnel...${NC}"

# Start tunnel in the background
cloudflared tunnel run atoms-mcp > /tmp/cloudflared.log 2>&1 &
TUNNEL_PID=$!

# Wait for tunnel to connect
echo "  ⏳ Waiting for tunnel to connect..."
sleep 3

# Check if tunnel is running
if ! ps -p $TUNNEL_PID > /dev/null; then
    echo -e "${RED}  ❌ Failed to start Cloudflare tunnel${NC}"
    echo -e "${RED}     Check logs at /tmp/cloudflared.log${NC}"
    # Cleanup MCP server
    kill $MCP_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}  ✅ Cloudflare tunnel started (PID: $TUNNEL_PID)${NC}"
echo ""

# Step 4: Display status
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo ""
echo -e "${YELLOW}📊 Status:${NC}"
echo -e "  MCP Server:        http://127.0.0.1:8000/api/mcp"
echo -e "  Health Check:      http://127.0.0.1:8000/health"
echo -e "  Public Endpoint:   https://atomcp.kooshapari.com/api/mcp"
echo -e "  MCP Server PID:    $MCP_PID"
echo -e "  Tunnel PID:        $TUNNEL_PID"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "  MCP Server:        tail -f /tmp/atoms_mcp.log"
echo -e "  Cloudflare Tunnel: tail -f /tmp/cloudflared.log"
echo ""
echo -e "${YELLOW}⏹  To stop:${NC}"
echo -e "  pkill -f 'python.*atoms_mcp' && pkill -f 'cloudflared.*tunnel.*run.*atoms-mcp'"
echo ""

# Keep script running and monitor processes
echo -e "${GREEN}👀 Monitoring services (Ctrl+C to stop)...${NC}"
echo ""

# Trap Ctrl+C to cleanup
trap "echo ''; echo -e '${YELLOW}🛑 Shutting down...${NC}'; kill $MCP_PID $TUNNEL_PID 2>/dev/null || true; exit 0" INT TERM

# Monitor loop
while true; do
    if ! ps -p $MCP_PID > /dev/null; then
        echo -e "${RED}❌ MCP server stopped unexpectedly${NC}"
        kill $TUNNEL_PID 2>/dev/null || true
        exit 1
    fi

    if ! ps -p $TUNNEL_PID > /dev/null; then
        echo -e "${RED}❌ Cloudflare tunnel stopped unexpectedly${NC}"
        kill $MCP_PID 2>/dev/null || true
        exit 1
    fi

    sleep 5
done
