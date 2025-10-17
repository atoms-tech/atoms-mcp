#!/bin/bash
# Run Phase 3 RLS Policy Tests
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 3: RLS Policy Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo -e "${YELLOW}Installing pytest...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

# Parse command line arguments
MODE="${1:-all}"

case $MODE in
    "all")
        echo -e "${GREEN}Running all RLS policy tests (40 tests)${NC}"
        python -m pytest tests/phase3/rls_policies/ -v --tb=short
        ;;

    "enforcement")
        echo -e "${GREEN}Running policy enforcement tests (10 tests)${NC}"
        python -m pytest tests/phase3/rls_policies/test_policy_enforcement.py -v
        ;;

    "access")
        echo -e "${GREEN}Running access control tests (14 tests)${NC}"
        python -m pytest tests/phase3/rls_policies/test_access_control.py -v
        ;;

    "edge")
        echo -e "${GREEN}Running edge case tests (10 tests)${NC}"
        python -m pytest tests/phase3/rls_policies/test_edge_cases.py -v
        ;;

    "performance")
        echo -e "${GREEN}Running performance tests (6 tests)${NC}"
        python -m pytest tests/phase3/rls_policies/test_policy_performance.py -v -s
        ;;

    "coverage")
        echo -e "${GREEN}Running tests with coverage report${NC}"
        python -m pytest tests/phase3/rls_policies/ \
            --cov=schemas.rls \
            --cov-report=html \
            --cov-report=term \
            -v
        echo -e "${GREEN}Coverage report: htmlcov/index.html${NC}"
        ;;

    "quick")
        echo -e "${GREEN}Running quick validation (collect only)${NC}"
        python -m pytest tests/phase3/rls_policies/ --collect-only
        ;;

    "count")
        echo -e "${GREEN}Test count by file:${NC}"
        for file in tests/phase3/rls_policies/test_*.py; do
            count=$(grep -c "^async def test_" "$file")
            echo "  $(basename $file): $count tests"
        done
        echo ""
        total=$(grep -c "^async def test_" tests/phase3/rls_policies/test_*.py)
        echo -e "${GREEN}Total: $total tests${NC}"
        ;;

    "help")
        echo "Usage: ./run_tests.sh [mode]"
        echo ""
        echo "Modes:"
        echo "  all         - Run all RLS tests (default)"
        echo "  enforcement - Run policy enforcement tests only"
        echo "  access      - Run access control tests only"
        echo "  edge        - Run edge case tests only"
        echo "  performance - Run performance tests only"
        echo "  coverage    - Run with coverage report"
        echo "  quick       - Quick validation (collect only)"
        echo "  count       - Count tests per file"
        echo "  help        - Show this help message"
        ;;

    *)
        echo -e "${YELLOW}Unknown mode: $MODE${NC}"
        echo "Run './run_tests.sh help' for usage"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Test run complete${NC}"
echo -e "${BLUE}========================================${NC}"
