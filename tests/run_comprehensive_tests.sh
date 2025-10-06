#!/bin/bash
# Comprehensive Entity Tool Test Runner
# This script runs the comprehensive entity tool tests and generates a detailed report

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Entity Tool Comprehensive Test Suite${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if server is running
echo -e "${YELLOW}Checking if MCP server is running...${NC}"
if ! curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${RED}ERROR: MCP server is not running on http://127.0.0.1:8000${NC}"
    echo -e "${YELLOW}Please start the server with: python -m uvicorn server:app --port 8000${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Server is running${NC}\n"

# Check environment variables
echo -e "${YELLOW}Checking environment variables...${NC}"
if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ] || [ -z "$NEXT_PUBLIC_SUPABASE_ANON_KEY" ]; then
    echo -e "${RED}ERROR: Supabase environment variables not set${NC}"
    echo -e "${YELLOW}Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Environment variables configured${NC}\n"

# Run the comprehensive tests
echo -e "${BLUE}Running comprehensive entity tool tests...${NC}\n"

# Run tests with pytest
pytest tests/test_entity_tool_comprehensive.py \
    -v \
    -s \
    --tb=short \
    --color=yes \
    --html=tests/entity_tool_test_report.html \
    --self-contained-html \
    2>&1 | tee tests/entity_tool_test_output.log

# Check test results
TEST_EXIT_CODE=${PIPESTATUS[0]}

echo -e "\n${BLUE}========================================${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests completed successfully!${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed or encountered issues${NC}"
fi
echo -e "${BLUE}========================================${NC}\n"

# Display report locations
echo -e "${BLUE}Test Reports Generated:${NC}"
echo -e "  - Test Matrix: ${GREEN}tests/entity_tool_test_matrix_report.md${NC}"
echo -e "  - HTML Report: ${GREEN}tests/entity_tool_test_report.html${NC}"
echo -e "  - Text Output: ${GREEN}tests/entity_tool_test_output.log${NC}\n"

# Display the matrix report if it exists
if [ -f "tests/entity_tool_test_matrix_report.md" ]; then
    echo -e "${BLUE}Test Matrix Report:${NC}\n"
    cat tests/entity_tool_test_matrix_report.md
fi

exit $TEST_EXIT_CODE
