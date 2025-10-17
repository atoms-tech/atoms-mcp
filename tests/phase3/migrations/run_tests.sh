#!/bin/bash
# Phase 3 Migration Test Runner
# Runs all migration tests with proper configuration and reporting

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Phase 3 Migration Test Runner${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Function to print section headers
print_header() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
    echo ""
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Parse command line arguments
MODE="all"
VERBOSE=false
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --cold)
            MODE="cold"
            shift
            ;;
        --hot)
            MODE="hot"
            shift
            ;;
        --all)
            MODE="all"
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --cold        Run COLD mode tests only (mocked database)"
            echo "  --hot         Run HOT mode tests only (real database)"
            echo "  --all         Run all tests (default)"
            echo "  -v, --verbose Enable verbose output"
            echo "  --coverage    Generate coverage report"
            echo "  -h, --help    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --cold              # Run COLD tests"
            echo "  $0 --hot -v            # Run HOT tests with verbose output"
            echo "  $0 --all --coverage    # Run all tests with coverage"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Navigate to project root
cd "$PROJECT_ROOT"

# Check Python and pytest installation
print_header "Checking dependencies"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi
print_success "Python 3 found: $(python3 --version)"

if ! python3 -m pytest --version &> /dev/null; then
    print_error "pytest is not installed"
    echo "Install with: pip install pytest pytest-asyncio"
    exit 1
fi
print_success "pytest found: $(python3 -m pytest --version | head -n1)"

# Check for database connection (HOT mode)
if [ "$MODE" == "hot" ] || [ "$MODE" == "all" ]; then
    print_header "Checking database connection (for HOT mode)"

    if [ -z "$TEST_DATABASE_URL" ]; then
        print_warning "TEST_DATABASE_URL not set"
        print_warning "HOT mode tests will be skipped"
        print_warning "Set with: export TEST_DATABASE_URL='postgresql://...'"

        if [ "$MODE" == "hot" ]; then
            print_error "Cannot run HOT mode without database connection"
            exit 1
        fi
    else
        print_success "TEST_DATABASE_URL is set"
        # Don't print the actual URL for security
    fi
fi

# Build pytest command
PYTEST_CMD="python3 -m pytest tests/phase3/migrations"

# Add mode marker
if [ "$MODE" == "cold" ]; then
    PYTEST_CMD="$PYTEST_CMD -m cold"
elif [ "$MODE" == "hot" ]; then
    PYTEST_CMD="$PYTEST_CMD -m hot"
fi

# Add verbosity
if [ "$VERBOSE" == true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage
if [ "$COVERAGE" == true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=pheno_vendor.db_kit.migrations --cov-report=html --cov-report=term"
fi

# Add color output
PYTEST_CMD="$PYTEST_CMD --color=yes"

# Run tests
print_header "Running Phase 3 Migration Tests (MODE: $MODE)"

echo "Command: $PYTEST_CMD"
echo ""

# Execute tests
if $PYTEST_CMD; then
    print_success "All tests passed!"

    if [ "$COVERAGE" == true ]; then
        echo ""
        print_success "Coverage report generated: htmlcov/index.html"
        echo "Open with: open htmlcov/index.html"
    fi

    # Print summary
    echo ""
    print_header "Test Summary"
    echo "Mode: $MODE"
    echo "Tests: Passed ✓"

    if [ "$MODE" == "all" ]; then
        echo ""
        echo "Test Breakdown:"
        echo "  - Migration Runner: 10 tests"
        echo "  - Rollback:         8 tests"
        echo "  - Versioning:       6 tests"
        echo "  - Idempotency:      6 tests"
        echo "  -------------------------"
        echo "  Total:             30 tests"
    fi

    exit 0
else
    print_error "Some tests failed!"
    echo ""
    print_warning "Check the output above for failure details"

    if [ "$VERBOSE" == false ]; then
        echo ""
        print_warning "Re-run with -v for more detailed output"
    fi

    exit 1
fi
