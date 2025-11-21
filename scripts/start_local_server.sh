#!/bin/bash
# Start local MCP server for E2E testing

set -e

echo "🚀 Starting local MCP server for E2E testing..."
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found. Run 'uv sync' first."
    exit 1
fi

# Set environment variables for HTTP transport
export ATOMS_FASTMCP_TRANSPORT=http
export ATOMS_FASTMCP_HOST=0.0.0.0
export ATOMS_FASTMCP_PORT=8000
export ATOMS_FASTMCP_HTTP_PATH=/api/mcp
export ATOMS_TEST_MODE=true

# Load Supabase credentials from .env if available
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env"
    set -a
    source .env
    set +a
fi

# Set Supabase credentials if available (for Supabase JWT verification)
if [ -n "$SUPABASE_URL" ] || [ -n "$NEXT_PUBLIC_SUPABASE_URL" ]; then
    SUPABASE_URL=${SUPABASE_URL:-$NEXT_PUBLIC_SUPABASE_URL}
    SUPABASE_KEY=${SUPABASE_ANON_KEY:-$NEXT_PUBLIC_SUPABASE_ANON_KEY}
    export SUPABASE_URL
    export SUPABASE_ANON_KEY=$SUPABASE_KEY
    echo "✅ Using Supabase URL: $SUPABASE_URL"
    echo "✅ Supabase JWT verification will be enabled"
else
    echo "⚠️  SUPABASE_URL not set - Supabase JWT verification disabled"
    echo "   Tests will use unsigned JWTs (requires ATOMS_TEST_MODE=true)"
fi

echo "📋 Server configuration:"
echo "   - Transport: $ATOMS_FASTMCP_TRANSPORT"
echo "   - Host: $ATOMS_FASTMCP_HOST"
echo "   - Port: $ATOMS_FASTMCP_PORT"
echo "   - Path: $ATOMS_FASTMCP_HTTP_PATH"
echo "   - Test Mode: $ATOMS_TEST_MODE"
if [ -n "$SUPABASE_URL" ]; then
    echo "   - Supabase URL: $SUPABASE_URL"
fi
echo ""
echo "🌐 Server will be available at: http://localhost:8000/api/mcp"
echo "🏥 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python server.py
