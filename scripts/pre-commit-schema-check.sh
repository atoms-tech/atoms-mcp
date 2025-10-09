#!/bin/bash
# Pre-commit hook for schema drift detection
#
# Installation:
#   cp scripts/pre-commit-schema-check.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# Or create a symlink:
#   ln -s ../../scripts/pre-commit-schema-check.sh .git/hooks/pre-commit

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Checking for schema drift..."

# Check if schema sync script exists
if [ ! -f "scripts/sync_schema.py" ]; then
    echo -e "${YELLOW}Warning: Schema sync script not found. Skipping check.${NC}"
    exit 0
fi

# Check if Supabase credentials are available
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo -e "${YELLOW}Warning: Supabase credentials not set. Skipping schema check.${NC}"
    echo -e "${YELLOW}Set SUPABASE_URL and SUPABASE_SERVICE_KEY to enable schema checks.${NC}"
    exit 0
fi

# Run schema check
if python scripts/sync_schema.py --check; then
    echo -e "${GREEN}✓ No schema drift detected${NC}"
    exit 0
else
    echo -e "${RED}✗ Schema drift detected!${NC}"
    echo ""
    echo "The database schema has changed and local schemas are out of sync."
    echo ""
    echo "To see differences, run:"
    echo "  python scripts/sync_schema.py --diff"
    echo ""
    echo "To update local schemas, run:"
    echo "  python scripts/sync_schema.py --update"
    echo ""
    echo "To skip this check (not recommended), use:"
    echo "  git commit --no-verify"
    echo ""

    # Ask user if they want to see the diff
    read -p "Show diff now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python scripts/sync_schema.py --diff
    fi

    exit 1
fi
