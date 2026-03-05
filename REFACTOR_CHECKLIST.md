# Atoms-MCP-Prod: Refactor Checklist

## Pre-Flight Checks

- [ ] Backup current codebase: `git checkout -b backup/pre-refactor`
- [ ] Create feature branch: `git checkout -b refactor/hexagonal-architecture`
- [ ] Document current behavior (run all tests, save output)
- [ ] Measure current metrics (LOC, files, startup time, memory)

## Week 1: Domain Layer (Pure Python)

### Day 1: Setup
- [ ] Create new directory structure (see IMPLEMENTATION_GUIDE.md)
- [ ] Create all `__init__.py` files
- [ ] Set up new `pyproject.toml` with updated dependencies

### Day 2-3: Domain Models & Services
- [ ] Create `domain/models/entity.py`
- [ ] Create `domain/models/relationship.py`
- [ ] Create `domain/models/workspace.py`
- [ ] Create `domain/models/workflow.py`
- [ ] Create `domain/ports/repository.py`
- [ ] Create `domain/ports/cache.py`
- [ ] Create `domain/ports/embeddings.py`
- [ ] Create `domain/services/entity_service.py`
- [ ] Create `domain/services/relationship_service.py`
- [ ] Create `domain/services/workspace_service.py`
- [ ] Write unit tests for domain layer (100% coverage)
- [ ] Verify: `pytest tests/unit/domain -v --cov=src/atoms_mcp/domain`

## Week 2: Application Layer (Use Cases)

### Day 4-5: Commands & Queries
- [ ] Create `application/commands/create_entity.py`
- [ ] Create `application/commands/update_entity.py`
- [ ] Create `application/commands/delete_entity.py`
- [ ] Create `application/queries/get_entity.py`
- [ ] Create `application/queries/search_entities.py`
- [ ] Create `application/queries/rag_query.py`
- [ ] Create `application/workflows/project_setup.py`
- [ ] Create `application/workflows/bulk_import.py`
- [ ] Write unit tests for application layer (>90% coverage)
- [ ] Verify: `pytest tests/unit/application -v --cov=src/atoms_mcp/application`

## Week 3: Adapters (External Integration)

### Day 6: Infrastructure
- [ ] Create `infrastructure/config/settings.py` (SINGLE config file)
- [ ] Create `infrastructure/logging/setup.py`
- [ ] Create `infrastructure/errors/exceptions.py`
- [ ] Create `infrastructure/di.py` (dependency injection)
- [ ] Delete old config files (8 files)
- [ ] Verify: Settings load correctly from environment

### Day 7: Secondary Adapters (Outbound)
- [ ] Create `adapters/secondary/supabase/repository.py`
- [ ] Create `adapters/secondary/supabase/client.py`
- [ ] Create `adapters/secondary/vertex/embeddings.py`
- [ ] Create `adapters/secondary/pheno/__init__.py` (with fallback)
- [ ] Create `adapters/secondary/cache/memory.py`
- [ ] Write integration tests for adapters
- [ ] Verify: `pytest tests/integration/adapters -v`

### Day 8: Primary Adapters (Inbound)
- [ ] Create `adapters/primary/mcp/server.py`
- [ ] Create `adapters/primary/mcp/tools.py`
- [ ] Create `adapters/primary/mcp/auth.py`
- [ ] Create `adapters/primary/cli/commands.py` (SINGLE CLI)
- [ ] Delete old CLI files (4 files: atoms, atoms_cli.py, atoms_cli_enhanced.py, atoms_server.py)
- [ ] Update `fastmcp.json` to point to new server
- [ ] Verify: `atoms serve --help` works

## Week 4: Migration & Cleanup

### Day 9-10: Test Migration
- [ ] Create `tests/conftest.py` with shared fixtures
- [ ] Migrate essential tests to new structure
- [ ] Delete phase-based test directories (tests/phase1-9/)
- [ ] Delete duplicate test files (comprehensive_test_*.py)
- [ ] Delete manual tests (tests/manual/)
- [ ] Move performance tests to tests/performance/
- [ ] Verify: `pytest tests -v --cov=src/atoms_mcp`
- [ ] Target: >80% coverage

### Day 11-12: File Cleanup
- [ ] Delete old server files (8 files in server/)
- [ ] Delete old tools files (4 files in tools/)
- [ ] Delete old lib files (10 files in lib/)
- [ ] Delete old utils files (3 files in utils/)
- [ ] Delete old infrastructure files (2 files)
- [ ] Delete old settings files (5 files in settings/)
- [ ] Delete old config files (3 files in config/)
- [ ] Total deleted: ~120 files
- [ ] Verify: No broken imports

### Day 13: Dependency Cleanup
- [ ] Update `pyproject.toml` with new dependencies
- [ ] Remove unused dependencies (20+ packages)
- [ ] Add pyright and zuban for type checking
- [ ] Remove mypy configuration
- [ ] Run: `uv sync` or `pip install -e ".[dev]"`
- [ ] Verify: `ruff check .` passes
- [ ] Verify: `zuban check .` passes (pyright)

## Week 5: Polish & Deploy

### Day 14: Documentation
- [ ] Update README.md with new architecture
- [ ] Create/update ARCHITECTURE.md (hexagonal guide)
- [ ] Update API_REFERENCE.md
- [ ] Update DEPLOYMENT.md
- [ ] Create migration guide for team
- [ ] Delete old documentation (22 files)

### Day 15: Performance Testing
- [ ] Measure startup time (target: <1s)
- [ ] Measure memory usage (target: <100MB)
- [ ] Run load tests: `pytest tests/performance -v`
- [ ] Compare with baseline metrics
- [ ] Optimize if needed

### Day 16: Security & Quality
- [ ] Run security audit: `ruff check . --select S`
- [ ] Check for secrets in code
- [ ] Verify all secrets use SecretStr
- [ ] Run full test suite: `pytest tests -v --cov`
- [ ] Verify coverage >80%

### Day 17: Staging Deployment
- [ ] Deploy to staging environment
- [ ] Run smoke tests on staging
- [ ] Monitor for errors (24 hours)
- [ ] Performance testing on staging
- [ ] Get team approval

### Day 18: Production Deployment
- [ ] Final review of changes
- [ ] Merge feature branch to main
- [ ] Deploy to production
- [ ] Monitor for issues (48 hours)
- [ ] Celebrate! 🎉

## Verification Commands

```bash
# File count
find src/atoms_mcp -name "*.py" | wc -l  # Should be ~50

# Line count
cloc src/atoms_mcp --exclude-dir=__pycache__  # Should be ~10K LOC

# Test coverage
pytest tests -v --cov=src/atoms_mcp --cov-report=term-missing

# Type checking
zuban check src/atoms_mcp  # Should pass with no errors

# Linting
ruff check .  # Should pass with no errors

# Formatting
ruff format --check .  # Should pass

# Startup time
time atoms serve --help  # Should be <1s

# Build package
python -m build  # Should succeed

# Install and test
pip install -e ".[dev]"
atoms serve --transport stdio  # Should start successfully
```

## Success Criteria

- [ ] **Files:** 248 → 80 (68% reduction) ✅
- [ ] **LOC:** 56K → 22K (61% reduction) ✅
- [ ] **Tests:** All passing, >80% coverage ✅
- [ ] **Performance:** <1s startup, <100MB memory ✅
- [ ] **Type Safety:** Pyright passes with no errors ✅
- [ ] **Documentation:** Complete and up-to-date ✅
- [ ] **Deployment:** Successfully deployed to production ✅


