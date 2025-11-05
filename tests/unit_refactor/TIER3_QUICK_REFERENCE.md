# Tier 3 Tests - Quick Reference Guide

## Quick Start

### Run All Tier 3 Tests
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod
pytest tests/unit_refactor/test_*_adapter.py tests/unit_refactor/test_pheno_integration.py -v
```

### Run Individual Test Files
```bash
# Supabase (50 tests)
pytest tests/unit_refactor/test_supabase_adapter.py -v

# Vertex AI (45 tests)
pytest tests/unit_refactor/test_vertex_ai_adapter.py -v

# Redis (40 tests)
pytest tests/unit_refactor/test_redis_adapter.py -v

# Pheno (34 tests)
pytest tests/unit_refactor/test_pheno_integration.py -v
```

### Run Specific Test Class
```bash
pytest tests/unit_refactor/test_supabase_adapter.py::TestSupabaseConnectionManagement -v
pytest tests/unit_refactor/test_vertex_ai_adapter.py::TestEmbeddingGeneration -v
pytest tests/unit_refactor/test_redis_adapter.py::TestRedisCacheBasicOperations -v
pytest tests/unit_refactor/test_pheno_integration.py::TestPhenoTunnelSetup -v
```

### Run with Coverage
```bash
pytest tests/unit_refactor/test_*_adapter.py tests/unit_refactor/test_pheno_integration.py \
  --cov=src/atoms_mcp/adapters/secondary \
  --cov-report=html \
  --cov-report=term-missing
```

---

## Test File Structure

### 1. test_supabase_adapter.py (50 tests)

#### Test Classes
- `TestSupabaseConnectionManagement` (15 tests)
- `TestSupabaseRepositoryCRUD` (20 tests)
- `TestSupabaseErrorHandling` (10 tests)
- `TestSupabaseSerialization` (5 tests)

#### Key Mocks
- `MockSupabaseClient` - Full Redis client simulation
- `MockSupabaseQueryBuilder` - Fluent query interface
- `MockSupabaseResponse` - API responses

#### Run Examples
```bash
# All Supabase tests
pytest tests/unit_refactor/test_supabase_adapter.py -v

# Just connection tests
pytest tests/unit_refactor/test_supabase_adapter.py::TestSupabaseConnectionManagement -v

# Specific test
pytest tests/unit_refactor/test_supabase_adapter.py::TestSupabaseConnectionManagement::test_connection_initialization_success -v
```

---

### 2. test_vertex_ai_adapter.py (45 tests)

#### Test Classes
- `TestVertexAIClientInitialization` (10 tests)
- `TestEmbeddingGeneration` (15 tests)
- `TestLLMOperations` (10 tests)
- `TestConversationManagement` (5 tests)
- `TestVertexAIErrorHandling` (5 tests)

#### Key Mocks
- `MockVertexAIClient` - Client configuration
- `MockTextEmbeddingModel` - Embedding generation
- `MockGenerativeModel` - LLM text generation
- `MockChat` - Conversation sessions

#### Run Examples
```bash
# All Vertex AI tests
pytest tests/unit_refactor/test_vertex_ai_adapter.py -v

# Just embedding tests
pytest tests/unit_refactor/test_vertex_ai_adapter.py::TestEmbeddingGeneration -v

# Specific test
pytest tests/unit_refactor/test_vertex_ai_adapter.py::TestEmbeddingGeneration::test_generate_embedding_with_cache -v
```

---

### 3. test_redis_adapter.py (40 tests)

#### Test Classes
- `TestRedisCacheConnection` (8 tests)
- `TestRedisCacheBasicOperations` (10 tests)
- `TestRedisCacheBatchOperations` (6 tests)
- `TestRedisCacheClearOperations` (3 tests)
- `TestRedisCacheErrorHandling` (5 tests)
- `TestRedisCacheSerialization` (5 tests)
- `TestRedisCacheConnectionPool` (3 tests)

#### Key Mocks
- `MockRedisClient` - Complete Redis simulation
- `MockRedisPipeline` - Batch operations
- `MockConnectionPool` - Connection management

#### Run Examples
```bash
# All Redis tests
pytest tests/unit_refactor/test_redis_adapter.py -v

# Just basic operations
pytest tests/unit_refactor/test_redis_adapter.py::TestRedisCacheBasicOperations -v

# Specific test
pytest tests/unit_refactor/test_redis_adapter.py::TestRedisCacheBasicOperations::test_set_and_get_value -v
```

---

### 4. test_pheno_integration.py (34 tests)

#### Test Classes
- `TestPhenoTunnelSetup` (8 tests)
- `TestPhenoTunnelContextManager` (3 tests)
- `TestPhenoGlobalTunnelManagement` (3 tests)
- `TestPhenoLoggerAdapter` (10 tests)
- `TestPhenoErrorHandling` (5 tests)
- `TestPhenoIntegrationConfiguration` (5 tests)

#### Key Mocks
- `MockPhenoTunnel` - Tunnel instance
- `MockTunnelProvider` - Tunnel management
- `MockPhenoLogger` - Logging with context

#### Run Examples
```bash
# All Pheno tests
pytest tests/unit_refactor/test_pheno_integration.py -v

# Just tunnel tests
pytest tests/unit_refactor/test_pheno_integration.py::TestPhenoTunnelSetup -v

# Specific test
pytest tests/unit_refactor/test_pheno_integration.py::TestPhenoLoggerAdapter::test_logger_with_context -v
```

---

## Common Test Patterns

### 1. Basic CRUD Test
```python
def test_save_and_get(self, repository, mock_entity_type):
    """
    Given: A new entity
    When: Saving and retrieving it
    Then: Same entity is returned
    """
    entity = mock_entity_type(id=str(uuid4()), name="Test", value=42)
    saved = repository.save(entity)
    result = repository.get(saved.id)

    assert result.id == entity.id
    assert result.name == entity.name
```

### 2. Error Handling Test
```python
def test_operation_error(self, adapter, mock_client):
    """
    Given: Client configured to fail
    When: Performing operation
    Then: Appropriate error is raised
    """
    mock_client.set_failure(True, APIError("Test error"))

    with pytest.raises(AdapterError, match="Test error"):
        adapter.operation()
```

### 3. Retry Test
```python
def test_retry_success(self, adapter):
    """
    Given: Operation that fails once then succeeds
    When: Calling with retry
    Then: Operation succeeds after retry
    """
    model = MockModel(should_fail=True, failure_count=1)

    with patch("time.sleep"):
        result = adapter.operation_with_retry()

        assert result is not None
        assert model.call_count == 2
```

### 4. Cache Test
```python
def test_caching(self, cache):
    """
    Given: Value stored in cache
    When: Retrieving multiple times
    Then: Cached value is returned
    """
    cache.set("key", "value", ttl=60)

    result1 = cache.get("key")
    result2 = cache.get("key")

    assert result1 == result2 == "value"
```

---

## Fixtures Quick Reference

### Supabase Fixtures
- `mock_client` - MockSupabaseClient instance
- `mock_settings` - Configuration mock
- `supabase_connection` - Connection with mocked client
- `mock_entity_type` - Test entity class
- `repository` - Repository with mocked backend

### Vertex AI Fixtures
- `mock_settings` - Vertex AI configuration
- `mock_aiplatform` - aiplatform module mock
- `mock_credentials` - Google credentials
- `vertex_client` - Client with mocked dependencies
- `mock_embedding_model` - Embedding model mock
- `mock_generative_model` - LLM model mock

### Redis Fixtures
- `mock_redis_client` - MockRedisClient instance
- `mock_redis_module` - Redis module mock
- `redis_cache` - Cache with mocked client

### Pheno Fixtures
- `mock_tunnel_provider` - Tunnel provider mock
- `mock_pheno_logger_class` - Logger class mock
- `mock_settings` - Pheno configuration

---

## Debugging Tests

### Run Single Test with Output
```bash
pytest tests/unit_refactor/test_supabase_adapter.py::test_name -v -s
```

### Run with PDB on Failure
```bash
pytest tests/unit_refactor/test_supabase_adapter.py --pdb
```

### Run with Warnings
```bash
pytest tests/unit_refactor/test_supabase_adapter.py -v -W all
```

### Run Failed Tests Only
```bash
pytest tests/unit_refactor/test_supabase_adapter.py --lf
```

---

## Coverage Commands

### Generate HTML Report
```bash
pytest tests/unit_refactor/test_*_adapter.py tests/unit_refactor/test_pheno_integration.py \
  --cov=src/atoms_mcp/adapters/secondary \
  --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Terminal Coverage Report
```bash
pytest tests/unit_refactor/test_*_adapter.py tests/unit_refactor/test_pheno_integration.py \
  --cov=src/atoms_mcp/adapters/secondary \
  --cov-report=term-missing
```

### Coverage for Specific Module
```bash
# Just Supabase
pytest tests/unit_refactor/test_supabase_adapter.py \
  --cov=src/atoms_mcp/adapters/secondary/supabase \
  --cov-report=term-missing

# Just Vertex AI
pytest tests/unit_refactor/test_vertex_ai_adapter.py \
  --cov=src/atoms_mcp/adapters/secondary/vertex \
  --cov-report=term-missing
```

---

## Test Markers (if configured)

### Run by Category
```bash
# Unit tests only
pytest tests/unit_refactor/ -m unit

# Slow tests
pytest tests/unit_refactor/ -m slow

# Skip slow tests
pytest tests/unit_refactor/ -m "not slow"
```

---

## Common Issues and Solutions

### Issue: ImportError for mock modules
**Solution**: Mocks are self-contained in test files, no additional imports needed

### Issue: Tests running slowly
**Solution**: All tests use mocks and should run fast. Check for actual network calls.

### Issue: Fixtures not found
**Solution**: Check conftest.py in tests/unit_refactor/ directory

### Issue: Coverage not 100%
**Solution**: Review uncovered lines with `--cov-report=term-missing`

---

## Test Statistics Summary

| File | Tests | Classes | Lines | Time |
|------|-------|---------|-------|------|
| test_supabase_adapter.py | 50 | 4 | 1,100 | ~3s |
| test_vertex_ai_adapter.py | 45 | 5 | 900 | ~3s |
| test_redis_adapter.py | 40 | 7 | 800 | ~2s |
| test_pheno_integration.py | 34 | 6 | 700 | ~2s |
| **TOTAL** | **169** | **22** | **3,500** | **~10s** |

---

## File Locations

```
tests/unit_refactor/
├── test_supabase_adapter.py      # 37KB - Supabase tests
├── test_vertex_ai_adapter.py     # 30KB - Vertex AI tests
├── test_redis_adapter.py         # 25KB - Redis tests
├── test_pheno_integration.py     # 20KB - Pheno tests
├── TIER3_TEST_SUMMARY.md         # Detailed documentation
└── TIER3_QUICK_REFERENCE.md      # This file
```

---

## Next Actions

### After Creating Tests
1. ✅ Run all tests to verify they pass
2. ✅ Check coverage meets 100% target
3. ✅ Review test output for any warnings
4. ✅ Add to CI/CD pipeline

### Regular Maintenance
1. Run tests before commits
2. Update tests when adapters change
3. Add tests for new features
4. Monitor for flaky tests

---

## Support Resources

- **Detailed Documentation**: See TIER3_TEST_SUMMARY.md
- **Test Examples**: Review existing tests in each file
- **Mock Patterns**: Check mock implementations at top of files
- **Pytest Docs**: https://docs.pytest.org/

---

*Quick Reference Guide - Tier 3 Tests*
*Last Updated: 2025-10-30*
