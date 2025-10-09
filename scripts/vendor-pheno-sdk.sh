#!/bin/bash
set -e

# ============================================================================
# Pheno-SDK Vendoring Script for Atoms MCP
# ============================================================================
# Purpose: Copy pheno-sdk packages into pheno_vendor/ for production deployments
# Usage: ./scripts/vendor-pheno-sdk.sh [--clean] [--verify]
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PHENO_SDK_ROOT="${PHENO_SDK_ROOT:-$(dirname "$PROJECT_ROOT")/pheno-sdk}"
VENDOR_DIR="$PROJECT_ROOT/pheno_vendor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Package list for Atoms MCP - smaller subset focused on needed packages
PACKAGES=(
    "mcp-QA"
    "pydevkit"
    "db-kit"
    "deploy-kit"
    "observability-kit"
    "cli-builder-kit"
    "filewatch-kit"
    "authkit-client"
    "adapter-kit"
    "vector-kit"
    "workflow-kit"
)

# Package name mappings (directory -> Python package name)
declare -A PACKAGE_NAMES=(
    ["mcp-QA"]="mcp_qa"
    ["pydevkit"]="pydevkit"
    ["db-kit"]="db_kit"
    ["deploy-kit"]="deploy_kit"
    ["observability-kit"]="observability_kit"
    ["cli-builder-kit"]="cli_builder"
    ["filewatch-kit"]="filewatch_kit"
    ["authkit-client"]="authkit_client"
    ["adapter-kit"]="adapter_kit"
    ["vector-kit"]="vector_kit"
    ["workflow-kit"]="workflow_kit"
)

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    if [ ! -d "$PHENO_SDK_ROOT" ]; then
        log_error "Pheno-SDK not found at: $PHENO_SDK_ROOT"
        log_info "Set PHENO_SDK_ROOT environment variable or ensure pheno-sdk is in expected location"
        exit 1
    fi

    log_success "Pheno-SDK found at: $PHENO_SDK_ROOT"
}

clean_vendor() {
    if [ -d "$VENDOR_DIR" ]; then
        log_info "Cleaning existing vendor directory..."
        rm -rf "$VENDOR_DIR"
        log_success "Vendor directory cleaned"
    fi
}

create_vendor_structure() {
    log_info "Creating vendor directory structure..."
    mkdir -p "$VENDOR_DIR"

    # Create __init__.py to make it a package
    cat > "$VENDOR_DIR/__init__.py" << 'EOF'
"""
Vendored pheno-sdk packages for production deployment.

This directory contains copies of pheno-sdk packages to avoid
dependency on relative paths in production environments.
"""

__version__ = "1.0.0"
EOF

    log_success "Vendor structure created"
}

copy_package() {
    local pkg_dir=$1
    local pkg_name=${PACKAGE_NAMES[$pkg_dir]}
    local source_path="$PHENO_SDK_ROOT/$pkg_dir"
    local dest_path="$VENDOR_DIR/$pkg_name"

    if [ ! -d "$source_path" ]; then
        log_warning "Package not found: $pkg_dir (skipping)"
        return 0
    fi

    log_info "Vendoring $pkg_dir -> $pkg_name..."

    # Find the actual Python package directory
    if [ -f "$source_path/setup.py" ] || [ -f "$source_path/pyproject.toml" ]; then
        local python_pkg_path="$source_path/$pkg_name"

        if [ ! -d "$python_pkg_path" ]; then
            python_pkg_path="$source_path/src/$pkg_name"
            if [ ! -d "$python_pkg_path" ]; then
                python_pkg_path="$source_path"
                log_warning "Using entire directory for $pkg_dir"
            fi
        fi

        # Copy the package
        if [ -d "$python_pkg_path" ] && [ "$python_pkg_path" != "$source_path" ]; then
            cp -r "$python_pkg_path" "$dest_path"
        else
            mkdir -p "$dest_path"
            if [ -d "$source_path/$pkg_name" ]; then
                cp -r "$source_path/$pkg_name"/* "$dest_path/"
            else
                find "$source_path" -maxdepth 1 -name "*.py" -exec cp {} "$dest_path/" \;
                find "$source_path" -maxdepth 1 -type d -name "[!.]*" ! -name "tests" ! -name "docs" ! -name "examples" -exec cp -r {} "$dest_path/" \;
            fi
        fi

        # Copy metadata files
        for meta_file in setup.py setup.cfg pyproject.toml README.md LICENSE; do
            if [ -f "$source_path/$meta_file" ]; then
                cp "$source_path/$meta_file" "$dest_path/"
            fi
        done

        # Clean up unwanted files
        find "$dest_path" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find "$dest_path" -type f -name "*.pyc" -delete 2>/dev/null || true
        find "$dest_path" -type f -name "*.pyo" -delete 2>/dev/null || true
        find "$dest_path" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        find "$dest_path" -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
        find "$dest_path" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

        log_success "Vendored $pkg_dir"
    else
        log_warning "No setup.py or pyproject.toml found for $pkg_dir (skipping)"
        return 0
    fi
}

handle_kinfra() {
    local kinfra_source="$PHENO_SDK_ROOT/KInfra/libraries/python"
    local kinfra_dest="$VENDOR_DIR/kinfra"

    if [ -d "$kinfra_source" ]; then
        log_info "Vendoring KInfra..."

        if [ -L "$PHENO_SDK_ROOT/KInfra" ]; then
            local real_kinfra=$(readlink "$PHENO_SDK_ROOT/KInfra")
            kinfra_source="$real_kinfra/libraries/python"
        fi

        if [ -d "$kinfra_source" ]; then
            mkdir -p "$kinfra_dest"

            if [ -d "$kinfra_source/kinfra" ]; then
                cp -r "$kinfra_source/kinfra"/* "$kinfra_dest/"
            else
                cp -r "$kinfra_source"/* "$kinfra_dest/"
            fi

            for meta_file in setup.py setup.cfg pyproject.toml README.md LICENSE; do
                if [ -f "$kinfra_source/$meta_file" ]; then
                    cp "$kinfra_source/$meta_file" "$kinfra_dest/"
                fi
            done

            find "$kinfra_dest" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
            find "$kinfra_dest" -type f -name "*.pyc" -delete 2>/dev/null || true

            log_success "Vendored KInfra"
        else
            log_warning "KInfra Python library not found at $kinfra_source"
        fi
    else
        log_warning "KInfra not found (skipping)"
    fi
}

create_requirements_prod() {
    log_info "Creating requirements-prod.txt..."

    local req_file="$PROJECT_ROOT/requirements-prod.txt"
    local dev_req="$PROJECT_ROOT/requirements.txt"

    if [ ! -f "$dev_req" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi

    cat > "$req_file" << 'EOF'
# ============================================================================
# Production Requirements for Atoms MCP
# ============================================================================
# This file uses VENDORED pheno-sdk packages from pheno_vendor/
# For development, use requirements.txt with editable installs
# Generated by scripts/vendor-pheno-sdk.sh
# ============================================================================

EOF

    grep -v "^-e.*pheno-sdk" "$dev_req" | grep -v "^#.*PHENO-SDK" | grep -v "^$" >> "$req_file"

    log_success "Created requirements-prod.txt"
}

create_sitecustomize() {
    log_info "Creating sitecustomize.py for vendored packages..."

    cat > "$PROJECT_ROOT/sitecustomize.py" << 'EOF'
"""
Site customization to add vendored pheno-sdk packages to sys.path.
"""

import sys
from pathlib import Path

vendor_path = Path(__file__).parent / "pheno_vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))
EOF

    log_success "Created sitecustomize.py"
}

verify_vendored_packages() {
    log_info "Verifying vendored packages..."

    local errors=0

    for pkg_dir in "${PACKAGES[@]}"; do
        local pkg_name=${PACKAGE_NAMES[$pkg_dir]}
        local pkg_path="$VENDOR_DIR/$pkg_name"

        if [ ! -d "$pkg_path" ]; then
            log_warning "Package not vendored: $pkg_name"
            continue
        fi

        local py_files=$(find "$pkg_path" -name "*.py" | wc -l)
        if [ "$py_files" -eq 0 ]; then
            log_error "No Python files found in $pkg_name"
            ((errors++))
        else
            log_success "Verified $pkg_name ($py_files Python files)"
        fi
    done

    if [ -d "$VENDOR_DIR/kinfra" ]; then
        local kinfra_py=$(find "$VENDOR_DIR/kinfra" -name "*.py" | wc -l)
        if [ "$kinfra_py" -eq 0 ]; then
            log_error "No Python files found in kinfra"
            ((errors++))
        else
            log_success "Verified kinfra ($kinfra_py Python files)"
        fi
    fi

    if [ $errors -gt 0 ]; then
        log_error "Verification failed with $errors errors"
        exit 1
    fi

    log_success "All vendored packages verified"
}

generate_manifest() {
    log_info "Generating VENDOR_MANIFEST.txt..."

    local manifest="$VENDOR_DIR/VENDOR_MANIFEST.txt"

    cat > "$manifest" << EOF
Pheno-SDK Vendored Packages Manifest (Atoms MCP)
Generated: $(date)
Source: $PHENO_SDK_ROOT

Packages:
EOF

    for pkg_dir in "${PACKAGES[@]}"; do
        local pkg_name=${PACKAGE_NAMES[$pkg_dir]}
        local pkg_path="$VENDOR_DIR/$pkg_name"

        if [ -d "$pkg_path" ]; then
            local files=$(find "$pkg_path" -type f | wc -l)
            local size=$(du -sh "$pkg_path" | cut -f1)
            echo "  - $pkg_name ($files files, $size)" >> "$manifest"
        fi
    done

    if [ -d "$VENDOR_DIR/kinfra" ]; then
        local files=$(find "$VENDOR_DIR/kinfra" -type f | wc -l)
        local size=$(du -sh "$VENDOR_DIR/kinfra" | cut -f1)
        echo "  - kinfra ($files files, $size)" >> "$manifest"
    fi

    echo "" >> "$manifest"
    echo "Total size: $(du -sh "$VENDOR_DIR" | cut -f1)" >> "$manifest"

    log_success "Generated manifest"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local clean=false
    local verify=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean)
                clean=true
                shift
                ;;
            --verify)
                verify=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --clean   Remove existing vendor directory before vendoring"
                echo "  --verify  Run verification tests"
                echo "  --help    Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    echo ""
    echo "======================================================================"
    echo "  Pheno-SDK Vendoring Script (Atoms MCP)"
    echo "======================================================================"
    echo ""

    check_prerequisites

    if [ "$clean" = true ]; then
        clean_vendor
    fi

    create_vendor_structure

    for pkg in "${PACKAGES[@]}"; do
        copy_package "$pkg"
    done

    handle_kinfra
    create_requirements_prod
    create_sitecustomize
    generate_manifest
    verify_vendored_packages

    echo ""
    echo "======================================================================"
    log_success "Vendoring complete!"
    echo "======================================================================"
    echo ""
    echo "Vendored packages location: $VENDOR_DIR"
    echo "Production requirements: $PROJECT_ROOT/requirements-prod.txt"
    echo ""
}

main "$@"
