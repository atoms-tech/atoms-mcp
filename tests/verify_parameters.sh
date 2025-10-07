#!/bin/bash
# Quick verification script to check parameter usage

echo "=== Parameter Verification Report ==="
echo ""

echo "✓ Checking workspace_tool set_context parameters:"
echo "  - context_type: $(grep -r 'context_type' test_workspace*.py | wc -l | tr -d ' ')"
echo "  - entity_id (set_context): $(grep -A5 '"operation": "set_context"' test_workspace*.py | grep 'entity_id' | wc -l | tr -d ' ')"

echo ""
echo "✓ Checking query_tool search parameters:"
echo "  - search_term: $(grep -r '"search_term"' test_query*.py | wc -l | tr -d ' ')"

echo ""
echo "✓ Checking format parameters:"
echo "  - format_type: $(grep -r 'format_type' framework/*.py | wc -l | tr -d ' ')"

echo ""
echo "❌ Checking for old parameters (should be 0):"
echo "  - Old 'format': $(grep -r '"format":' test_*.py framework/*.py 2>/dev/null | grep -v format_type | wc -l | tr -d ' ')"
echo "  - Old 'query': $(grep -r '"query":' test_*.py 2>/dev/null | wc -l | tr -d ' ')"
echo "  - fuzzy parameters: $(grep -r 'fuzzy_match\|fuzzy.*[:=]' test_*.py 2>/dev/null | grep -v 'test_fuzzy\|def.*fuzzy\|Test fuzzy' | wc -l | tr -d ' ')"

echo ""
echo "=== Verification Complete ==="
