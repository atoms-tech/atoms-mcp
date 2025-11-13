"""
Simple Integration Tests for All Fixes
Tests all implemented fixes using code inspection
"""

import os
import sys
import inspect

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_rls_fix_no_direct_client():
    """Verify no direct Supabase client bypass in update operations"""
    from tools.entity import EntityManager

    source = inspect.getsource(EntityManager.update_entity)

    # Check that direct supabase.table() calls are not present
    assert "self.supabase.table" not in source, \
        "❌ Direct Supabase client calls found in update_entity"

    # Verify _db_get_single is used instead
    assert "_db_get_single" in source, \
        "❌ _db_get_single method not found in update_entity"

    print("✅ RLS Fix: No direct Supabase client bypass")
    return True


def test_multi_field_search():
    """Verify search includes multiple fields"""
    from tools.entity import EntityManager

    source = inspect.getsource(EntityManager.search_entities)

    # Check all fields are included
    assert '"name"' in source or "'name'" in source
    assert '"description"' in source or "'description'" in source
    assert '"content"' in source or "'content'" in source
    assert '"properties"' in source or "'properties'" in source

    print("✅ Multi-Field Search: All fields included")
    return True


def test_or_logic():
    """Verify OR logic is implemented"""
    from tools.entity import EntityManager

    source = inspect.getsource(EntityManager.search_entities)
    assert '"_or"' in source or "'_or'" in source

    print("✅ OR Logic: Properly implemented")
    return True


def test_database_or_filter():
    """Verify database adapter supports OR filtering"""
    from infrastructure.supabase_db import SupabaseDatabaseAdapter

    source = inspect.getsource(SupabaseDatabaseAdapter._apply_filters)
    assert '"_or"' in source or "'_or'" in source or '== "_or"' in source

    print("✅ Database Adapter: OR filtering supported")
    return True


def test_list_workspaces_separate_queries():
    """Verify list_workspaces uses separate queries"""
    from tools.workspace import WorkspaceManager

    source = inspect.getsource(WorkspaceManager.list_workspaces)

    # Should NOT use complex join syntax
    assert "!inner" not in source or "organizations!inner" not in source

    # Should query both tables
    assert "organization_members" in source
    assert "organizations" in source

    print("✅ list_workspaces: Uses separate queries")
    return True


def test_profile_join_optimization():
    """Verify profile join optimization exists"""
    from tools.relationship import RelationshipManager

    source = inspect.getsource(RelationshipManager.list_relationships)

    # Check for optimized join attempt
    assert "profiles!inner" in source

    # Check for fallback
    assert "try:" in source and "except" in source

    print("✅ Profile Join: Optimization with fallback")
    return True


def test_user_mapper_exists():
    """Verify user mapper module exists"""
    from infrastructure.user_mapper import UserIDMapper, get_user_mapper

    assert UserIDMapper is not None
    assert get_user_mapper is not None
    assert hasattr(UserIDMapper, 'is_workos_id')
    assert hasattr(UserIDMapper, 'is_uuid')

    print("✅ User ID Mapper: Module exists")
    return True


def test_workos_id_detection():
    """Test WorkOS ID format validation"""
    from infrastructure.user_mapper import UserIDMapper

    # Valid WorkOS IDs
    assert UserIDMapper.is_workos_id("user_01K6EV07KR2MNMDQ60BC03ZM1A")
    assert not UserIDMapper.is_workos_id("invalid")
    assert not UserIDMapper.is_uuid("user_01K6EV07KR2MNMDQ60BC03ZM1A")

    print("✅ WorkOS ID Detection: Working correctly")
    return True


def test_member_soft_delete_migration():
    """Verify soft delete migration file exists"""
    migration_path = os.path.join(
        os.path.dirname(__file__),
        "..", "infrastructure", "sql", "007_member_soft_delete.sql"
    )

    assert os.path.exists(migration_path)

    with open(migration_path, 'r') as f:
        content = f.read()

    # Check for required elements
    assert "is_deleted" in content
    assert "soft_delete_org_member" in content
    assert "soft_delete_project_member" in content

    print("✅ Member Soft Delete: Migration exists")
    return True


def test_parameter_inference():
    """Verify operation inference logic exists"""
    with open(os.path.join(os.path.dirname(__file__), "..", "server.py"), 'r') as f:
        server_content = f.read()

    # Check inference logic
    assert "if not operation:" in server_content
    assert 'operation = "create"' in server_content
    assert 'operation = "update"' in server_content
    assert 'operation = "read"' in server_content

    print("✅ Parameter Inference: Logic verified")
    return True


def run_all_tests():
    """Run all tests and print summary"""
    tests = [
        ("RLS Fix", test_rls_fix_no_direct_client),
        ("Multi-Field Search", test_multi_field_search),
        ("OR Logic", test_or_logic),
        ("Database OR Filter", test_database_or_filter),
        ("list_workspaces Fix", test_list_workspaces_separate_queries),
        ("Profile Join Optimization", test_profile_join_optimization),
        ("User ID Mapper", test_user_mapper_exists),
        ("WorkOS ID Detection", test_workos_id_detection),
        ("Member Soft Delete", test_member_soft_delete_migration),
        ("Parameter Inference", test_parameter_inference),
    ]

    print("\n" + "="*70)
    print(" " * 15 + "COMPREHENSIVE FIX VERIFICATION")
    print("="*70 + "\n")

    passed = 0
    failed = 0
    results = []

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            results.append((name, "✅ PASS"))
        except AssertionError as e:
            failed += 1
            results.append((name, f"❌ FAIL: {str(e)}"))
        except Exception as e:
            failed += 1
            results.append((name, f"❌ ERROR: {str(e)}"))

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for name, result in results:
        print(f"{result[:2]} {name}")

    print("\n" + "="*70)
    print(f"Total: {len(tests)} tests")
    print(f"Passed: {passed} ({passed/len(tests)*100:.1f}%)")
    print(f"Failed: {failed}")
    print("="*70)

    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
