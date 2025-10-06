#!/bin/bash
# Comprehensive test runner for query_tool

set -e

echo "=================================="
echo "QUERY TOOL COMPREHENSIVE TEST SUITE"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if server is running
echo "Checking if MCP server is running..."
if ! curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${RED}ERROR: MCP server is not running on http://127.0.0.1:8000${NC}"
    echo "Please start the server first with: ./start_local.sh"
    exit 1
fi
echo -e "${GREEN}✓ Server is running${NC}"
echo ""

# Check environment
echo "Checking environment variables..."
if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ] || [ -z "$NEXT_PUBLIC_SUPABASE_ANON_KEY" ]; then
    echo -e "${RED}ERROR: Supabase environment variables not set${NC}"
    echo "Please ensure .env file is configured"
    exit 1
fi
echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Run tests with different verbosity levels
echo "Running comprehensive query tool tests..."
echo ""

# Test 1: Quick validation
echo -e "${YELLOW}[1/4] Running quick validation tests...${NC}"
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeSearch::test_search_single_entity -v

# Test 2: All query types
echo ""
echo -e "${YELLOW}[2/4] Testing all query types...${NC}"
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeSearch -v
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeAggregate -v
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeAnalyze -v
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeRelationships -v

# Test 3: RAG capabilities
echo ""
echo -e "${YELLOW}[3/4] Testing RAG search capabilities...${NC}"
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeRAGSearch -v
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeSimilarity -v
pytest tests/test_query_tool_comprehensive.py::TestRAGModeComparison -v

# Test 4: Error handling and performance
echo ""
echo -e "${YELLOW}[4/4] Testing error handling and performance...${NC}"
pytest tests/test_query_tool_comprehensive.py::TestErrorHandling -v
pytest tests/test_query_tool_comprehensive.py::TestPerformance -v

# Generate comprehensive report
echo ""
echo -e "${YELLOW}Generating comprehensive test report...${NC}"
pytest tests/test_query_tool_comprehensive.py::test_generate_comprehensive_report -v -s

# Run full suite with coverage
echo ""
echo -e "${YELLOW}Running full test suite with coverage...${NC}"
pytest tests/test_query_tool_comprehensive.py -v --tb=short

echo ""
echo -e "${GREEN}=================================="
echo "TEST SUITE COMPLETED"
echo "==================================${NC}"
echo ""

# Generate HTML report (optional)
if command -v pytest-html &> /dev/null; then
    echo "Generating HTML report..."
    pytest tests/test_query_tool_comprehensive.py --html=test_report_query_tool.html --self-contained-html
    echo -e "${GREEN}✓ HTML report generated: test_report_query_tool.html${NC}"
fi

echo ""
echo "All tests completed successfully!"
