# Phase 3: RLS Policy Tests

Comprehensive test suite for Row-Level Security (RLS) policies and access control.

## Overview

This test suite validates that RLS policies correctly enforce security boundaries at the database level. Tests cover policy enforcement, access control scenarios, edge cases, and performance characteristics.

**Total Tests: 35**
- Policy Enforcement: 10 tests
- Access Control: 12 tests
- Edge Cases: 8 tests
- Performance: 5 tests

## Test Files

### 1. `test_policy_enforcement.py` (10 tests)

Tests core RLS policy enforcement mechanisms:

- ✅ Organization SELECT policy enforces membership
- ✅ Organization SELECT policy denies non-members
- ✅ Project SELECT policy uses current_user_id variable
- ✅ Project INSERT policy validates org_id variable
- ✅ Document policy enforces row-level filtering
- ✅ PolicyValidator routes to correct table policies
- ✅ Profile policy allows authenticated reads
- ✅ Project UPDATE policy enforces admin role
- ✅ Organization DELETE policy restricts to owner only
- ✅ Validate methods raise PermissionDeniedError

**Key Features:**
- Tests policy variables (current_user_id, org_id)
- Validates row-level filtering
- Checks role-based permissions
- Tests error handling

### 2. `test_access_control.py` (12 tests)

Tests real-world access control scenarios:

**Owner Access (3 tests):**
- ✅ Owner can read own organization
- ✅ Owner can update own organization
- ✅ Owner can delete own organization

**Workspace Member Access (4 tests):**
- ✅ Workspace member can access workspace data
- ✅ Workspace member can read workspace documents
- ✅ Workspace editor can create documents
- ✅ Workspace viewer cannot create documents

**Organization Member Access (3 tests):**
- ✅ Org member can access org data
- ✅ Org member can create projects in org
- ✅ Org member can access private org projects

**Cross-Boundary Access Denial (2 tests):**
- ✅ Cross-org access is denied
- ✅ Cross-org project access is denied
- ✅ Cross-workspace access is denied (unless public)
- ✅ Public projects allow cross-workspace access

**Key Features:**
- Tests ownership patterns
- Validates membership hierarchies
- Tests workspace isolation
- Verifies cross-boundary security

### 3. `test_edge_cases.py` (8 tests)

Tests edge cases and security scenarios:

**Null/Missing Scenarios (3 tests):**
- ✅ Null organization_id denies access
- ✅ Null project_id in document denies access
- ✅ Missing owner prevents deletion

**Deleted User Access (2 tests):**
- ✅ Deleted user cannot access organization
- ✅ Deleted member record denies project access

**Suspended User (1 test):**
- ✅ Suspended user cannot perform admin actions

**Permission Escalation (3 tests):**
- ✅ Member cannot escalate to admin role
- ✅ Editor cannot grant admin to others
- ✅ Profile update restricted to own profile
- ✅ Empty user_id denies all access

**Key Features:**
- Tests null safety
- Validates soft-delete handling
- Prevents privilege escalation
- Tests authentication edge cases

### 4. `test_policy_performance.py` (5 tests)

Tests RLS policy performance characteristics:

- ✅ Single policy check under 20ms overhead
- ✅ Complex policy check under threshold
- ✅ Bulk operations don't N+1
- ✅ Cached policy checks are faster
- ✅ Concurrent policy evaluations
- ✅ Policy evaluation scales linearly

**Performance Targets:**
- Single policy check: < 20ms
- Bulk operations (10 items): < 100ms
- Concurrent operations: 50 simultaneous checks
- Linear scaling: < 2x variance

**Key Features:**
- Measures policy overhead
- Tests caching effectiveness
- Validates concurrent performance
- Ensures linear scalability

## Running the Tests

### Run All RLS Tests
```bash
pytest tests/phase3/rls_policies/ -v
```

### Run Specific Test File
```bash
pytest tests/phase3/rls_policies/test_policy_enforcement.py -v
pytest tests/phase3/rls_policies/test_access_control.py -v
pytest tests/phase3/rls_policies/test_edge_cases.py -v
pytest tests/phase3/rls_policies/test_policy_performance.py -v
```

### Run with Coverage
```bash
pytest tests/phase3/rls_policies/ --cov=schemas.rls --cov-report=html
```

### Run Performance Tests Only
```bash
pytest tests/phase3/rls_policies/test_policy_performance.py -v -m performance
```

### Run Security Tests Only
```bash
pytest tests/phase3/rls_policies/ -v -m security
```

## Test Structure

Each test follows the Given-When-Then pattern:

```python
@pytest.mark.asyncio
async def test_organization_select_policy_enforces_membership(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given a user who is a member of an organization
    When the SELECT policy is evaluated
    Then access is granted
    """
    # Given: Setup test conditions
    policy = OrganizationPolicy(test_user_id, mock_db_adapter)
    mock_db_adapter.get_single.return_value = {...}

    # When: Execute the operation
    can_read = await policy.can_select({"id": test_org_id})

    # Then: Verify expected outcome
    assert can_read is True
```

## Fixtures

### Common Fixtures (from conftest.py)

- `mock_db_adapter`: Basic mock database adapter
- `configured_db_adapter`: Pre-configured with test data
- `test_users`: Set of users with different roles
- `test_organizations`: Test organizations
- `test_projects`: Test projects (private/public)
- `make_membership`: Factory for creating memberships
- `performance_db_adapter`: Mock with realistic latency

### Test-Specific Fixtures

Each test file defines its own specific fixtures:
- User IDs (owner, member, external)
- Organization IDs
- Project IDs

## Coverage Goals

### Line Coverage
- Target: 100% of schemas/rls.py
- Current: Tracks all policy methods
- Missing: Error handling edge cases

### Branch Coverage
- Target: 100% of conditional logic
- Tests both success and failure paths
- Validates all role combinations

### Function Coverage
- Target: 100% of public API
- All policy classes tested
- All helper functions covered

## Error Handling

All tests verify proper error handling:

1. **PermissionDeniedError**: Raised with clear messages
2. **Null Safety**: Gracefully handles null/missing values
3. **Invalid Input**: Rejects malformed requests
4. **Database Errors**: Logged but don't expose internals

## Performance Monitoring

Performance tests track:

1. **Policy Overhead**: < 20ms per check
2. **Query Efficiency**: No N+1 problems
3. **Caching**: Reduces duplicate queries
4. **Concurrency**: Handles 50+ simultaneous checks
5. **Scalability**: Linear performance scaling

## Security Considerations

These tests validate critical security boundaries:

1. **Organization Isolation**: Users can't access other orgs
2. **Project Isolation**: Users can't access unauthorized projects
3. **Workspace Isolation**: Users can't access other workspaces
4. **Role Enforcement**: Roles correctly limit operations
5. **Ownership**: Only owners can perform destructive operations
6. **Privilege Escalation**: Users can't grant themselves permissions

## Continuous Integration

### Pre-commit Hooks
```bash
# Run RLS tests before commit
pytest tests/phase3/rls_policies/ --tb=short
```

### CI Pipeline
```yaml
test-rls-policies:
  runs-on: ubuntu-latest
  steps:
    - name: Run RLS Policy Tests
      run: |
        pytest tests/phase3/rls_policies/ \
          --cov=schemas.rls \
          --cov-fail-under=95 \
          --tb=short
```

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure schemas module is in path
export PYTHONPATH="${PYTHONPATH}:."
```

**Async Errors:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

**Performance Test Failures:**
- May fail on slow systems
- Adjust thresholds in test file
- Run with `--tb=short` for details

### Debug Mode

Run with verbose output:
```bash
pytest tests/phase3/rls_policies/ -vv -s
```

Run specific test with debugging:
```bash
pytest tests/phase3/rls_policies/test_policy_enforcement.py::test_organization_select_policy_enforces_membership -vv -s
```

## Contributing

When adding new RLS tests:

1. Follow Given-When-Then structure
2. Include docstring explaining test purpose
3. Use descriptive test names
4. Add to appropriate test file
5. Update this README if adding new categories
6. Ensure performance tests have realistic thresholds

## Related Documentation

- [RLS Policy Implementation](../../../schemas/rls.py)
- [Database Schema](../../../schemas/)
- [Security Documentation](../../../docs/security/)
- [Testing Guidelines](../../README.md)
