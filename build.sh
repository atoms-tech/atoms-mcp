#!/bin/bash
# Build script for Vercel deployment
# This script is run during the build phase to prepare the environment
#
# Key actions:
# 1. Replace requirements.txt with requirements-prod.txt (no editable installs)
# 2. Ensure pheno_vendor/ directory exists (should be committed to git)
# 3. Ensure sitecustomize.py exists to load vendored packages
# 4. Verify vendored packages are present

set -e

echo "🔧 Preparing Vercel deployment..."

# Check if we're in a Vercel environment
if [ -n "$VERCEL" ]; then
    echo "📦 Detected Vercel environment"

    # CRITICAL: Replace requirements.txt with requirements-prod.txt
    # This removes editable installs like -e ../pheno-sdk/mcp-QA
    if [ -f "requirements-prod.txt" ]; then
        echo "✅ Replacing requirements.txt with requirements-prod.txt"
        echo "   (This removes editable installs that don't work in Vercel)"
        cp requirements-prod.txt requirements.txt
    else
        echo "❌ ERROR: requirements-prod.txt not found!"
        echo "   Run './atoms vendor setup' locally to generate it"
        exit 1
    fi

    # Verify vendored packages exist (should be committed to git)
    if [ ! -d "pheno_vendor" ]; then
        echo "❌ ERROR: pheno_vendor/ directory not found!"
        echo "   Run './atoms vendor setup' locally and commit pheno_vendor/ to git"
        exit 1
    fi

    echo "✅ Vendored packages found in pheno_vendor/"
    
    # List vendored packages
    echo "📦 Vendored packages:"
    ls -la pheno_vendor/ | head -20

    # Ensure sitecustomize.py is present for vendored packages
    if [ ! -f "sitecustomize.py" ]; then
        echo "⚠️  sitecustomize.py not found, creating it..."
        cat > sitecustomize.py << 'EOF'
"""
Site customization to add vendored pheno-sdk packages to sys.path.
This file is automatically loaded by Python on startup.
"""

import sys
from pathlib import Path

vendor_path = Path(__file__).parent / "pheno_vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))
    print(f"✅ Added {vendor_path} to sys.path")
EOF
    else
        echo "✅ sitecustomize.py already exists"
    fi

    # Verify requirements-prod.txt exists
    if [ ! -f "requirements-prod.txt" ]; then
        echo "❌ ERROR: requirements-prod.txt not found!"
        echo "   Run './atoms vendor setup' locally to generate it"
        exit 1
    fi

    echo "✅ requirements-prod.txt found"
else
    echo "📍 Not in Vercel environment, skipping deployment preparation"
fi

echo "✅ Build preparation complete"

