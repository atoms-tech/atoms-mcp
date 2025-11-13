#!/bin/bash
# Validate SQL Migrations Syntax
# Checks all migration files for basic syntax errors

set -e

echo "="
echo "SQL Migration Validation"
echo "=================================================================="

MIGRATION_DIR="infrastructure/sql"
MIGRATIONS=(
    "006_user_id_mapping.sql"
    "007_member_soft_delete.sql"
    "008_performance_indexes.sql"
    "009_fix_all_supabase_advisories.sql"
)

PASSED=0
FAILED=0

for migration in "${MIGRATIONS[@]}"; do
    file="$MIGRATION_DIR/$migration"

    if [ ! -f "$file" ]; then
        echo "❌ File not found: $file"
        FAILED=$((FAILED + 1))
        continue
    fi

    echo "Checking $migration..."

    # Basic syntax checks
    errors=""

    # Check for balanced BEGIN/COMMIT
    begins=$(grep -c "^BEGIN" "$file" || true)
    commits=$(grep -c "^COMMIT" "$file" || true)
    if [ "$begins" != "$commits" ]; then
        errors="$errors\n  - Unbalanced BEGIN/COMMIT ($begins begins, $commits commits)"
    fi

    # Check for common syntax errors
    if grep -q "entity_type" "$file" && grep -q "embedding_queue" "$file"; then
        if ! grep -q "table_name" "$file"; then
            errors="$errors\n  - Uses entity_type but table has table_name column"
        fi
    fi

    # Check for unclosed quotes
    single_quotes=$(grep -o "'" "$file" | wc -l)
    if [ $((single_quotes % 2)) != 0 ]; then
        errors="$errors\n  - Unclosed single quotes detected"
    fi

    if [ -n "$errors" ]; then
        echo "❌ $migration - FAILED"
        echo -e "$errors"
        FAILED=$((FAILED + 1))
    else
        echo "✅ $migration - PASSED"
        PASSED=$((PASSED + 1))
    fi
    echo ""
done

echo "=================================================================="
echo "VALIDATION SUMMARY"
echo "=================================================================="
echo "Total migrations: ${#MIGRATIONS[@]}"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "=================================================================="

if [ $FAILED -eq 0 ]; then
    echo "✅ All migrations passed validation!"
    exit 0
else
    echo "❌ Some migrations failed validation"
    exit 1
fi
