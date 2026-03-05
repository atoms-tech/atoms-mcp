#!/bin/bash

# Tier 3 Secondary Adapter Tests - Quick Run Script
# This script runs all Tier 3 tests with various options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}Tier 3 Secondary Adapter Tests${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Function to run tests with specific options
run_tests() {
    local test_type=$1
    local pytest_args=$2

    echo -e "${YELLOW}Running: $test_type${NC}"
    echo "Command: pytest $pytest_args"
    echo ""

    if pytest $pytest_args; then
        echo -e "${GREEN}✓ $test_type completed successfully${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ $test_type failed${NC}"
        echo ""
        return 1
    fi
}

# Main menu
echo "Select test execution mode:"
echo "1) Run all Tier 3 tests (verbose)"
echo "2) Run with coverage report"
echo "3) Run individual test files"
echo "4) Quick validation (fast)"
echo "5) Full validation (with coverage)"
echo "6) Run specific test class"
echo "7) Exit"
echo ""
read -p "Enter choice [1-7]: " choice

case $choice in
    1)
        echo ""
        run_tests "All Tier 3 Tests" \
            "tests/unit_refactor/test_supabase_adapter.py \
             tests/unit_refactor/test_vertex_ai_adapter.py \
             tests/unit_refactor/test_redis_adapter.py \
             tests/unit_refactor/test_pheno_integration.py \
             -v"
        ;;

    2)
        echo ""
        run_tests "Tier 3 Tests with Coverage" \
            "tests/unit_refactor/test_supabase_adapter.py \
             tests/unit_refactor/test_vertex_ai_adapter.py \
             tests/unit_refactor/test_redis_adapter.py \
             tests/unit_refactor/test_pheno_integration.py \
             --cov=src/atoms_mcp/adapters/secondary \
             --cov-report=html \
             --cov-report=term-missing \
             -v"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
            echo "Open with: open htmlcov/index.html"
            echo ""
        fi
        ;;

    3)
        echo ""
        echo "Select test file:"
        echo "1) Supabase Adapter (50 tests)"
        echo "2) Vertex AI Adapter (45 tests)"
        echo "3) Redis Cache Adapter (40 tests)"
        echo "4) Pheno Integration (34 tests)"
        echo ""
        read -p "Enter choice [1-4]: " file_choice

        case $file_choice in
            1)
                run_tests "Supabase Adapter Tests" \
                    "tests/unit_refactor/test_supabase_adapter.py -v"
                ;;
            2)
                run_tests "Vertex AI Adapter Tests" \
                    "tests/unit_refactor/test_vertex_ai_adapter.py -v"
                ;;
            3)
                run_tests "Redis Cache Adapter Tests" \
                    "tests/unit_refactor/test_redis_adapter.py -v"
                ;;
            4)
                run_tests "Pheno Integration Tests" \
                    "tests/unit_refactor/test_pheno_integration.py -v"
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                exit 1
                ;;
        esac
        ;;

    4)
        echo ""
        echo -e "${YELLOW}Quick Validation (minimal output)${NC}"
        echo ""
        run_tests "Quick Validation" \
            "tests/unit_refactor/test_supabase_adapter.py \
             tests/unit_refactor/test_vertex_ai_adapter.py \
             tests/unit_refactor/test_redis_adapter.py \
             tests/unit_refactor/test_pheno_integration.py \
             -q"
        ;;

    5)
        echo ""
        echo -e "${YELLOW}Full Validation (with coverage and verbose output)${NC}"
        echo ""
        run_tests "Full Validation" \
            "tests/unit_refactor/test_supabase_adapter.py \
             tests/unit_refactor/test_vertex_ai_adapter.py \
             tests/unit_refactor/test_redis_adapter.py \
             tests/unit_refactor/test_pheno_integration.py \
             --cov=src/atoms_mcp/adapters/secondary \
             --cov-report=term-missing \
             --cov-fail-under=100 \
             -v"
        ;;

    6)
        echo ""
        echo "Enter test class name (e.g., TestSupabaseConnectionManagement):"
        read -p "Class name: " class_name

        if [ -z "$class_name" ]; then
            echo -e "${RED}Class name cannot be empty${NC}"
            exit 1
        fi

        # Try to find the class in test files
        found=false
        for test_file in tests/unit_refactor/test_*_adapter.py tests/unit_refactor/test_pheno_integration.py; do
            if grep -q "class $class_name" "$test_file"; then
                echo -e "${GREEN}Found in: $test_file${NC}"
                run_tests "Test Class: $class_name" \
                    "$test_file::$class_name -v"
                found=true
                break
            fi
        done

        if [ "$found" = false ]; then
            echo -e "${RED}Test class not found: $class_name${NC}"
            exit 1
        fi
        ;;

    7)
        echo "Exiting..."
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Summary
echo ""
echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}Test Execution Summary${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""
echo "Test Files:"
echo "  - test_supabase_adapter.py    (50 tests)"
echo "  - test_vertex_ai_adapter.py   (45 tests)"
echo "  - test_redis_adapter.py       (40 tests)"
echo "  - test_pheno_integration.py   (34 tests)"
echo ""
echo "Total: 169 tests"
echo ""
echo -e "${GREEN}For more information, see:${NC}"
echo "  - TIER3_TEST_SUMMARY.md (detailed documentation)"
echo "  - TIER3_QUICK_REFERENCE.md (quick reference)"
echo ""
