#!/bin/bash
# Script to run comprehensive workspace_tool tests with detailed reporting

set -e

echo "=========================================="
echo "Atoms Workspace Tool Comprehensive Testing"
echo "=========================================="
echo ""

# Check if MCP server is running
echo "Checking if MCP server is running..."
if ! curl -s -f http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "ERROR: MCP server is not running on http://127.0.0.1:8000"
    echo "Please start the server first using: python -m atoms_mcp"
    exit 1
fi
echo "✓ MCP server is running"
echo ""

# Check environment variables
echo "Checking environment variables..."
if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ] || [ -z "$NEXT_PUBLIC_SUPABASE_ANON_KEY" ]; then
    echo "ERROR: Supabase environment variables not set"
    echo "Please ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are configured"
    exit 1
fi
echo "✓ Environment variables configured"
echo ""

# Run tests with detailed output
echo "Running workspace_tool comprehensive tests..."
echo ""

# Run with coverage if available
if command -v pytest-cov &> /dev/null; then
    pytest tests/test_workspace_tool_comprehensive.py \
        -v \
        -s \
        --tb=short \
        --cov=atoms_mcp \
        --cov-report=term-missing \
        --cov-report=html:coverage_workspace_tool \
        --durations=10 \
        --junitxml=test-results-workspace-tool.xml \
        2>&1 | tee workspace_test_output.log
else
    pytest tests/test_workspace_tool_comprehensive.py \
        -v \
        -s \
        --tb=short \
        --durations=10 \
        --junitxml=test-results-workspace-tool.xml \
        2>&1 | tee workspace_test_output.log
fi

echo ""
echo "=========================================="
echo "Test Execution Complete"
echo "=========================================="
echo ""
echo "Results saved to:"
echo "  - Test output: workspace_test_output.log"
echo "  - JUnit XML: test-results-workspace-tool.xml"

if [ -d "coverage_workspace_tool" ]; then
    echo "  - Coverage report: coverage_workspace_tool/index.html"
fi

echo ""
echo "Summary:"
grep -E "(PASSED|FAILED|ERROR|test session starts)" workspace_test_output.log | tail -20
