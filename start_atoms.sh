#!/bin/bash
# Start Atoms MCP Server with proper configuration
# This script sets up the environment and starts the server with CloudFlare tunnel

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Atoms MCP Server Startup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading environment from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}✗${NC} .env file not found"
    exit 1
fi

# Configuration
PORT=${PORT:-50002}
SRVC=${SRVC:-atoms-mcp}
TUNNEL_DOMAIN=${TUNNEL_DOMAIN:-kooshapari.com}
PUBLIC_URL=${PUBLIC_URL:-https://atomcp.kooshapari.com}

echo -e "${BLUE}Configuration:${NC}"
echo -e "  Port: ${GREEN}${PORT}${NC}"
echo -e "  Service: ${GREEN}${SRVC}${NC}"
echo -e "  Domain: ${GREEN}${TUNNEL_DOMAIN}${NC}"
echo -e "  Public URL: ${GREEN}${PUBLIC_URL}${NC}"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}✗${NC} cloudflared not found"
    echo "  Install with: brew install cloudflared"
    exit 1
fi

echo -e "${GREEN}✓${NC} cloudflared is installed"

# Check if tunnel config exists
TUNNEL_CONFIG="$HOME/.cloudflared/config-atomcp.yml"
if [ ! -f "$TUNNEL_CONFIG" ]; then
    echo -e "${RED}✗${NC} CloudFlare tunnel config not found: $TUNNEL_CONFIG"
    exit 1
fi

echo -e "${GREEN}✓${NC} Tunnel configuration found"

# Kill any existing processes
echo ""
echo -e "${BLUE}Cleaning up existing processes...${NC}"

# Kill existing server processes
pkill -f "python.*server.py" 2>/dev/null || true
pkill -f "atoms_mcp" 2>/dev/null || true

# Kill existing cloudflared processes
pkill -f "cloudflared.*tunnel" 2>/dev/null || true

sleep 2

# Start CloudFlare tunnel
echo ""
echo -e "${BLUE}Starting CloudFlare tunnel...${NC}"
cloudflared tunnel --config "$TUNNEL_CONFIG" run &
TUNNEL_PID=$!

# Wait for tunnel to be ready
sleep 5

if ps -p $TUNNEL_PID > /dev/null; then
    echo -e "${GREEN}✓${NC} CloudFlare tunnel started (PID: $TUNNEL_PID)"
else
    echo -e "${RED}✗${NC} Failed to start CloudFlare tunnel"
    exit 1
fi

# Start the MCP server
echo ""
echo -e "${BLUE}Starting MCP server...${NC}"
echo -e "  Local: ${GREEN}http://localhost:${PORT}${NC}"
echo -e "  Public: ${GREEN}${PUBLIC_URL}${NC}"
echo ""

# Export environment variables for server
export PORT=$PORT
export ATOMS_FASTMCP_PORT=$PORT
export ATOMS_FASTMCP_HOST=127.0.0.1
export ATOMS_FASTMCP_TRANSPORT=http
export PUBLIC_URL=$PUBLIC_URL

# Run the server
python3 server.py

# Cleanup on exit
trap "echo ''; echo 'Shutting down...'; kill $TUNNEL_PID 2>/dev/null; exit" INT TERM
