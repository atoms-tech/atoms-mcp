#!/usr/bin/env python3
"""
Test script to verify DB constraint error formatting
"""
import sys
sys.path.insert(0, "/Users/kooshapari/temp-PRODVERCEL/485/kush/pheno-sdk/mcp-QA")

from mcp_qa.reporters import DetailedErrorReporter

# Simulate a DB constraint violation test result
db_constraint_result = {
    "test_name": "test_create_organization",
    "tool_name": "workspace_tool",
    "success": False,
    "duration_ms": 751.37,
    "error": "DB_CONSTRAINT_VIOLATION: Database check constraint failed: valid_slug",
    "response": {
        "success": False,
        "error": "DB_CONSTRAINT_VIOLATION: {'message': 'new row for relation \"organizations\" violates check constraint \"valid_slug\"', 'code': '23514'}",
        "operation": "create",
        "entity_type": "organization"
    },
    "request_params": {
        "entity_type": "organization",
        "operation": "create",
        "data": {
            "name": "Test Org 20251007_212341",
            "slug": "test-org-20251007_212341",
            "description": "Test organization"
        }
    }
}

# Simulate a regular error
regular_error_result = {
    "test_name": "test_permission_denied",
    "tool_name": "entity_tool",
    "success": False,
    "duration_ms": 125.5,
    "error": "PERMISSION_DENIED: You don't have access to this resource",
    "response": {
        "success": False,
        "error": "PERMISSION_DENIED: Missing required permissions"
    }
}

reporter = DetailedErrorReporter(verbose=True)

print("=" * 80)
print("TESTING DB CONSTRAINT VIOLATION FORMATTING (should be YELLOW/ORANGE)")
print("=" * 80)
reporter._print_rich_error(db_constraint_result, 1, 2)

print("\n" + "=" * 80)
print("TESTING REGULAR ERROR FORMATTING (should be RED)")
print("=" * 80)
reporter._print_rich_error(regular_error_result, 2, 2)

print("\n✅ Test complete! DB constraints should show in YELLOW/ORANGE, regular errors in RED")
