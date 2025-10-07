#!/bin/bash
# Run comprehensive MCP tests with live Vercel log capture

echo "================================================================================"
echo "ATOMS MCP TEST SUITE WITH LIVE LOG CAPTURE"
echo "================================================================================"
echo ""

# Create log file
LOG_FILE="test_logs_$(date +%Y%m%d_%H%M%S).txt"
VERCEL_LOG_FILE="vercel_logs_$(date +%Y%m%d_%H%M%S).txt"

echo "📡 Starting Vercel log stream in background..."
echo "   Logs will be saved to: $VERCEL_LOG_FILE"

# Start vercel logs in background and save to file
vercel logs https://mcp.atoms.tech > "$VERCEL_LOG_FILE" 2>&1 &
VERCEL_PID=$!

echo "   ✅ Vercel logs PID: $VERCEL_PID"
echo ""

# Wait a moment for log stream to initialize
sleep 2

echo "🧪 Running comprehensive test suite..."
echo "   Test output will be saved to: $LOG_FILE"
echo ""

# Run the test
source .venv/bin/activate
python tests/test_mcp_comprehensive.py 2>&1 | tee "$LOG_FILE"
TEST_EXIT_CODE=$?

echo ""
echo "================================================================================"
echo "TEST COMPLETE"
echo "================================================================================"
echo ""

# Stop vercel logs
echo "📡 Stopping Vercel log stream (PID: $VERCEL_PID)..."
kill $VERCEL_PID 2>/dev/null

# Wait a moment for logs to flush
sleep 1

echo ""
echo "📄 Output files:"
echo "   Test output: $LOG_FILE"
echo "   Vercel logs: $VERCEL_LOG_FILE"
echo ""

# Show relevant Vercel logs
echo "📊 Relevant Vercel logs (auth/complete, JWT, errors):"
echo "---"
grep -E "(auth/complete|🔧|❌|✅|JWT|Decoded|user_id)" "$VERCEL_LOG_FILE" | tail -30
echo "---"
echo ""

echo "💡 To see full Vercel logs: cat $VERCEL_LOG_FILE"
echo ""

exit $TEST_EXIT_CODE
