#!/bin/bash
#
# Security, Validation, and Compliance Test Runner
#
# Usage:
#   ./run_security_tests.sh              # Run all tests
#   ./run_security_tests.sh validation   # Run input validation tests only
#   ./run_security_tests.sh integrity    # Run data integrity tests only
#   ./run_security_tests.sh compliance   # Run compliance tests only
#   ./run_security_tests.sh edge         # Run edge case tests only
#   ./run_security_tests.sh coverage     # Run with coverage report
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}Security & Compliance Test Suite${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Please install pytest: pip install pytest pytest-cov"
    exit 1
fi

# Navigate to project root
cd "$PROJECT_ROOT"

# Function to run tests
run_tests() {
    local test_file=$1
    local test_name=$2
    local test_count=$3

    echo -e "${YELLOW}Running ${test_name}...${NC}"
    echo -e "${BLUE}File: ${test_file}${NC}"
    echo -e "${BLUE}Expected: ${test_count} tests${NC}"
    echo ""

    pytest "$test_file" -v --tb=short

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ ${test_name} passed!${NC}"
    else
        echo -e "${RED}❌ ${test_name} had failures${NC}"
    fi
    echo ""

    return $exit_code
}

# Function to run with coverage
run_with_coverage() {
    echo -e "${YELLOW}Running all tests with coverage...${NC}"
    echo ""

    pytest tests/unit_refactor/test_input_validation.py \
           tests/unit_refactor/test_data_integrity.py \
           tests/unit_refactor/test_compliance.py \
           tests/unit_refactor/test_edge_cases.py \
           --cov=src/atoms_mcp \
           --cov-report=html:htmlcov \
           --cov-report=term-missing \
           --cov-report=xml:coverage.xml \
           -v

    local exit_code=$?

    echo ""
    echo -e "${GREEN}Coverage report generated:${NC}"
    echo -e "  HTML: ${BLUE}htmlcov/index.html${NC}"
    echo -e "  XML:  ${BLUE}coverage.xml${NC}"
    echo ""

    # Try to open HTML report
    if command -v open &> /dev/null; then
        echo -e "${YELLOW}Opening coverage report...${NC}"
        open htmlcov/index.html
    elif command -v xdg-open &> /dev/null; then
        echo -e "${YELLOW}Opening coverage report...${NC}"
        xdg-open htmlcov/index.html
    else
        echo -e "${YELLOW}To view coverage report, open:${NC} htmlcov/index.html"
    fi

    return $exit_code
}

# Parse command line argument
case "${1:-all}" in
    validation)
        run_tests "tests/unit_refactor/test_input_validation.py" \
                  "Input Validation Tests" \
                  "65"
        ;;

    integrity)
        run_tests "tests/unit_refactor/test_data_integrity.py" \
                  "Data Integrity Tests" \
                  "50"
        ;;

    compliance)
        run_tests "tests/unit_refactor/test_compliance.py" \
                  "Compliance Tests" \
                  "45"
        ;;

    edge)
        run_tests "tests/unit_refactor/test_edge_cases.py" \
                  "Edge Case Tests" \
                  "55"
        ;;

    coverage)
        run_with_coverage
        ;;

    all|*)
        echo -e "${YELLOW}Running all security and compliance tests...${NC}"
        echo -e "${BLUE}Total expected: 215 tests${NC}"
        echo ""

        # Run each suite
        failed=0

        run_tests "tests/unit_refactor/test_input_validation.py" \
                  "Input Validation Tests (65)" \
                  "65" || failed=$((failed + 1))

        run_tests "tests/unit_refactor/test_data_integrity.py" \
                  "Data Integrity Tests (50)" \
                  "50" || failed=$((failed + 1))

        run_tests "tests/unit_refactor/test_compliance.py" \
                  "Compliance Tests (45)" \
                  "45" || failed=$((failed + 1))

        run_tests "tests/unit_refactor/test_edge_cases.py" \
                  "Edge Case Tests (55)" \
                  "55" || failed=$((failed + 1))

        # Summary
        echo -e "${BLUE}=======================================${NC}"
        echo -e "${BLUE}Test Suite Summary${NC}"
        echo -e "${BLUE}=======================================${NC}"

        if [ $failed -eq 0 ]; then
            echo -e "${GREEN}✅ All test suites passed!${NC}"
            echo ""
            echo -e "${GREEN}Summary:${NC}"
            echo -e "  Input Validation:  65 tests"
            echo -e "  Data Integrity:    50 tests"
            echo -e "  Compliance:        45 tests"
            echo -e "  Edge Cases:        55 tests"
            echo -e "  ${GREEN}Total:             215 tests${NC}"
            exit 0
        else
            echo -e "${RED}❌ ${failed} test suite(s) had failures${NC}"
            echo ""
            echo -e "${YELLOW}To see detailed failures, run:${NC}"
            echo -e "  pytest tests/unit_refactor/test_*.py -v"
            exit 1
        fi
        ;;
esac

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}Test execution complete!${NC}"
echo -e "${BLUE}=======================================${NC}"
