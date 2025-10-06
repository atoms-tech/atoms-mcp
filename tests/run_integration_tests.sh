#!/bin/bash
# Integration Test Runner for Atoms MCP
# This script runs comprehensive integration tests and generates reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPORT_DIR="$SCRIPT_DIR/reports"
COVERAGE_DIR="$REPORT_DIR/coverage"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Atoms MCP Integration Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if MCP server is running
echo -e "${YELLOW}Checking MCP server status...${NC}"
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MCP server is running${NC}"
else
    echo -e "${RED}✗ MCP server is not running on http://127.0.0.1:8000${NC}"
    echo -e "${YELLOW}Please start the server first:${NC}"
    echo -e "  python -m server"
    exit 1
fi

# Check environment variables
echo -e "\n${YELLOW}Checking environment configuration...${NC}"
if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ]; then
    echo -e "${RED}✗ NEXT_PUBLIC_SUPABASE_URL not set${NC}"
    exit 1
fi

if [ -z "$NEXT_PUBLIC_SUPABASE_ANON_KEY" ]; then
    echo -e "${RED}✗ NEXT_PUBLIC_SUPABASE_ANON_KEY not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment configured${NC}"

# Create report directories
mkdir -p "$REPORT_DIR"
mkdir -p "$COVERAGE_DIR"

# Run integration tests
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  Running Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Activate virtual environment if it exists
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Run tests with coverage
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/integration_test_report_${TIMESTAMP}.json"
COVERAGE_FILE="$COVERAGE_DIR/coverage_${TIMESTAMP}.xml"
HTML_COVERAGE="$COVERAGE_DIR/htmlcov_${TIMESTAMP}"

echo -e "${YELLOW}Running tests with coverage tracking...${NC}\n"

# Run pytest with coverage
pytest "$SCRIPT_DIR/test_integration_workflows.py" \
    -v \
    -s \
    --tb=short \
    --maxfail=3 \
    --cov=tools \
    --cov-report=xml:"$COVERAGE_FILE" \
    --cov-report=html:"$HTML_COVERAGE" \
    --cov-report=term-missing \
    || TEST_EXIT_CODE=$?

# Check test results
if [ "${TEST_EXIT_CODE:-0}" -eq 0 ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  All Integration Tests Passed! ✓${NC}"
    echo -e "${GREEN}========================================${NC}\n"
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}  Some Tests Failed ✗${NC}"
    echo -e "${RED}========================================${NC}\n"
fi

# Display coverage summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Coverage Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Generate coverage report
if command -v coverage &> /dev/null; then
    coverage report --include="tools/*" || true
fi

# Check if JSON report was generated
if [ -f "$SCRIPT_DIR/integration_test_report.json" ]; then
    cp "$SCRIPT_DIR/integration_test_report.json" "$REPORT_FILE"
    echo -e "\n${GREEN}✓ Test report saved to: $REPORT_FILE${NC}"

    # Display report summary
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  Test Report Summary${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    if command -v jq &> /dev/null; then
        jq -r '
            "Total Scenarios: \(.summary.total_scenarios)",
            "Passed: \(.summary.passed_scenarios)",
            "Failed: \(.summary.failed_scenarios)",
            "Pass Rate: \(.summary.pass_rate)",
            "Total Duration: \(.summary.total_duration)",
            "Total Tool Calls: \(.summary.total_tool_calls)",
            "",
            "Data Consistency Checks:",
            "  Total: \(.data_consistency.total_checks)",
            "  Passed: \(.data_consistency.passed_checks)",
            "",
            "Performance:",
            "  Avg Duration: \(.performance.avg_scenario_duration)",
            "  Slowest: \(.performance.slowest_scenario)"
        ' "$REPORT_FILE"
    else
        cat "$REPORT_FILE" | python -m json.tool
    fi
fi

# Display coverage location
if [ -d "$HTML_COVERAGE" ]; then
    echo -e "\n${GREEN}✓ HTML coverage report: $HTML_COVERAGE/index.html${NC}"
fi

# Generate overall summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  Integration Test Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "Test Reports:     $REPORT_DIR"
echo -e "Coverage Reports: $COVERAGE_DIR"
echo -e "Latest Report:    $REPORT_FILE"

if [ -f "$COVERAGE_FILE" ]; then
    echo -e "Coverage XML:     $COVERAGE_FILE"
fi

echo -e "\n${BLUE}========================================${NC}\n"

# Exit with appropriate code
exit ${TEST_EXIT_CODE:-0}
