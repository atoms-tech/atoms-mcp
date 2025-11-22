# testing Specification

## Purpose
TBD - created by archiving change comprehensive-e2e-integration-tests. Update Purpose after archive.
## Requirements
### Requirement: Comprehensive E2E Test Coverage
The system SHALL provide end-to-end tests covering all 48 user stories with 95%+ code coverage across all MCP tools and infrastructure layers.

#### Scenario: Entity CRUD operations tested
- **WHEN** entity_tool is called with create/read/update/delete operations
- **THEN** all operations are tested with valid/invalid inputs and error cases

#### Scenario: Workspace context operations tested
- **WHEN** workspace_tool is called with context operations
- **THEN** all context switching and defaults are tested

#### Scenario: Relationship management tested
- **WHEN** relationship_tool is called with link/unlink operations
- **THEN** all relationship types and cascading behavior are tested

#### Scenario: Search and discovery tested
- **WHEN** data_query is called with search operations
- **THEN** keyword, semantic, and hybrid search are tested

#### Scenario: Workflow execution tested
- **WHEN** workflow_execute is called with multi-step workflows
- **THEN** transaction semantics and error recovery are tested

### Requirement: Canonical Test File Organization
The system SHALL organize test files using concern-based naming (not speed/variant-based) with fixture parametrization for test variants.

#### Scenario: Test files use canonical names
- **WHEN** test files are created
- **THEN** names describe "what's tested" (e.g., test_entity_crud.py, not test_entity_fast.py)

#### Scenario: Test variants use fixtures
- **WHEN** multiple test variants are needed (unit/integration/e2e)
- **THEN** @pytest.fixture(params=[...]) is used instead of separate files

### Requirement: Integration Test Coverage
The system SHALL provide integration tests for database, auth, caching, and infrastructure layers.

#### Scenario: Database integration tested
- **WHEN** database operations are performed
- **THEN** connection pooling, transactions, RLS, and performance are tested

#### Scenario: Auth integration tested
- **WHEN** authentication flows are executed
- **THEN** Supabase JWT, AuthKit OAuth, token refresh, and session lifecycle are tested

#### Scenario: Cache integration tested
- **WHEN** caching operations occur
- **THEN** hit/miss rates, invalidation, TTL, and fallback behavior are tested

### Requirement: Test Quality Standards
The system SHALL enforce test quality standards: no slow tests (>5s), no flaky tests, deterministic assertions.

#### Scenario: Slow tests marked appropriately
- **WHEN** tests take >5 seconds
- **THEN** they are marked with @pytest.mark.slow

#### Scenario: All tests pass consistently
- **WHEN** tests are run multiple times
- **THEN** they pass consistently without flakiness or retry logic

