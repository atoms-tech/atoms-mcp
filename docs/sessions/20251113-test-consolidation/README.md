# Test File Consolidation & Canonicalization Session

**Session ID:** 20251113-test-consolidation  
**Status:** 📋 Planning & Analysis Complete → Ready for Execution  
**Objective:** Consolidate 12 non-canonical test files into proper concern-based structure per AGENTS.md § Test File Governance

---

## 📚 Session Documents

### 1. **00_SESSION_OVERVIEW.md** ⭐ START HERE
- Session goals and success criteria
- High-level consolidation map (11 _extN files + 1 "working" file)
- Phases and timeline
- Known issues and next steps

### 2. **01_RESEARCH.md** (Deep Dive)
- Canonical naming standard explanation
- Current repository state analysis
- Why _extN naming is non-canonical
- Why "working" is semantic state (not concern-based)
- Variant testing strategy (fixtures vs separate files)
- File size analysis
- Dependency graph

### 3. **02_IMPLEMENTATION_STRATEGY.md** (Execution Guide)
- 6 phases with detailed steps
- Order of consolidation (dependency-based)
- Test running & validation strategy
- File decomposition guidelines
- Fixture dependency handling
- Git workflow
- Rollback plan
- Success criteria checklist

### 4. **CONSOLIDATION_SUMMARY.md** (Quick Reference)
- Problem statement
- Canonical standard (quick)
- 12-file consolidation map
- 6-phase execution overview
- Variant testing pattern conversion
- Execution checklist
- Expected outcomes

---

## 🎯 Quick Start

### What's the Problem?

```
12 non-canonical test files violate AGENTS.md § Test File Governance:

❌ 11 files with _extN naming (numeric metadata)
   test_entity_operations_ext12.py
   test_soft_delete_ext3.py
   test_error_handling_ext8.py
   ... (8 more)

❌ 1 file with semantic state naming
   test_working_extension.py ("working" = state, not component)
```

### What's the Solution?

```
✅ Consolidate all 12 files into canonical concern-based structure

test_working_extension.py + test_entity_operations_ext12.py 
    → merge into test_entity_core.py

test_soft_delete_ext3.py 
    → merge into test_soft_delete_consistency.py

test_error_handling_ext8.py 
    → merge into test_error_handling.py

... (8 more similar consolidations)

Result: 0 non-canonical files, clear structure ✓
```

### Why Does This Matter?

| Issue | Impact | Solution |
|-------|--------|----------|
| Duplicate test code | Same concern tested multiple times, harder to maintain | Use fixtures & markers |
| Numeric metadata | Violates canonical standard, unclear structure | Rename by concern |
| Semantic state | "working" vs "broken" doesn't describe component | Remove state descriptor |
| Test collection time | Extra files slow down pytest collection | Fewer files = faster |
| Discoverability | New developers don't know which test file to use | Clear, canonical names |

---

## 📋 Consolidation Map at a Glance

```
Phase 1: Core Entity Operations
├── test_working_extension.py         → test_entity_core.py
├── test_entity_operations_ext12.py   → test_entity_core.py (+ decompose)
└── [Delete 2 files]

Phase 2: Soft-Delete
├── test_soft_delete_ext3.py          → test_soft_delete_consistency.py
└── [Delete 1 file]

Phase 3: Tool-Specific (Parallel)
├── test_error_handling_ext8.py       → test_error_handling.py
├── test_audit_trails_ext7.py         → test_audit_trails.py
├── test_advanced_features_ext9.py    → test_advanced_features.py
├── test_workflows_ext10.py           → test_workflow_coverage.py
└── [Delete 4 files]

Phase 4: Infrastructure (Parallel)
├── test_permission_manager_ext2.py   → test_permissions.py
├── test_concurrency_ext4.py          → test_concurrency_manager.py
└── [Delete 2 files]

Phase 5: Relationships
├── test_relationship_cascading_ext6.py → test_relationship.py
└── [Delete 1 file]

Phase 6: Special Cases
├── test_multi_tenant_ext5.py         → Create test_multi_tenant.py
├── test_performance_ext11.py         → Use @pytest.mark.performance
└── [Delete 2 files]

TOTAL: Delete 12 non-canonical files
       Keep 0 non-canonical files (All consolidated)
```

---

## ✅ Canonical Naming Standard

### ✓ Good Examples (Concern-Based)
```
test_entity.py                   # Component: entity tool
test_entity_crud.py              # Concern: CRUD operations
test_soft_delete_consistency.py  # Concern: soft-delete behavior
test_auth_supabase.py            # Concern: Supabase auth integration
```

### ✗ Bad Examples (Metadata-Based)
```
test_entity_unit.py              # ❌ Describes scope (unit) not concern
test_entity_integration.py       # ❌ Describes variant (integration) not concern
test_entity_fast.py              # ❌ Describes speed not concern
test_entity_ext1.py              # ❌ Numeric metadata not concern
test_working_extension.py        # ❌ Semantic state not concern
```

**Key Rule:** File name answers "What component/concern?" NOT "How fast?" or "What variant?"

---

## 🔄 Variant Testing Strategy

### Old Pattern ❌ (Separate Files - Duplicated)
```python
# test_entity_unit.py
async def test_entity_creation(unit_client):
    ...

# test_entity_integration.py
async def test_entity_creation(integration_client):  # Same test, written AGAIN
    ...

# test_entity_e2e.py
async def test_entity_creation(e2e_client):         # Same test, written AGAIN
    ...

# Problem: Same test code in 3 files = maintenance nightmare
```

### New Pattern ✅ (Fixtures + Markers - DRY)
```python
# test_entity.py (single file)

@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """Returns different clients based on variant."""
    if request.param == "unit":
        return InMemoryMcpClient()     # fast
    elif request.param == "integration":
        return HttpMcpClient()          # live DB
    else:
        return DeploymentMcpClient()    # production

async def test_entity_creation(mcp_client):
    """Runs 3 times automatically: unit, integration, e2e"""
    result = await mcp_client.call_tool(...)
    assert result.success

@pytest.mark.performance
async def test_bulk_performance(mcp_client):
    """Performance test marked separately"""
    ...

# Benefit: One file, no duplication, clear intent ✓
```

---

## 🚀 Execution Steps

### 1. Review Planning Documents ✓
- [ ] Read `00_SESSION_OVERVIEW.md`
- [ ] Review `01_RESEARCH.md` for context
- [ ] Skim `02_IMPLEMENTATION_STRATEGY.md` for phases

### 2. Execute Phase 1 (Entity Core)
```bash
# Run current tests (baseline)
python cli.py test run --scope unit

# Merge test_working_extension.py + test_entity_operations_ext12.py
# Into test_entity_core.py
# (Follow detailed steps in 02_IMPLEMENTATION_STRATEGY.md)

# Verify tests still pass
python cli.py test run --scope unit --path tests/unit/tools/test_entity*.py

# Commit
git commit -m "test: Consolidate working_extension and entity_operations tests"
```

### 3. Execute Phases 2-6
- Follow same pattern for each phase
- Test after each consolidation
- Delete source files as consolidations complete

### 4. Verify Final State
```bash
# All tests pass
python cli.py test run --coverage

# No non-canonical files
find tests -name "*_ext*.py"  # Should be empty
find tests -name "*working*.py" # Should be empty

# All canonical
ls tests/unit/tools/test_*.py  # All concern-based names
```

---

## 📊 Expected Timeline

| Phase | Duration | Risk |
|-------|----------|------|
| 1: Entity Core | 1-2 hours | Low |
| 2: Soft-Delete | 1 hour | Low |
| 3: Tool-Specific (4 files, parallel) | 1-2 hours | Low |
| 4: Infrastructure (2 files, parallel) | 1 hour | Low |
| 5: Relationships | 30 min | Low |
| 6: Special Cases | 1 hour | Medium |
| **Total** | **4-8 hours** | - |

---

## 📈 Success Metrics

After consolidation:

```
❌ Before:     12 non-canonical files
                - 11 with _extN naming
                - 1 with semantic state

✅ After:      0 non-canonical files
                - All consolidated into canonical structure
                - All tests passing
                - Coverage maintained or improved
```

### Checklist

- [ ] 0 files with _extN suffix
- [ ] 0 files with semantic state names
- [ ] All test names are concern-based
- [ ] All tests pass (unit + integration)
- [ ] Coverage metrics maintained
- [ ] No duplicate test logic
- [ ] Files ≤500 lines (ideally ≤350)
- [ ] Fixtures properly use parametrization
- [ ] Markers used for categorization
- [ ] Session docs complete
- [ ] PR ready for merge

---

## 🔗 Related Documentation

- **AGENTS.md § Test File Governance** - Canonical naming standard authority
- **AGENTS.md § OpenSpec** - For planning large changes (optional here)
- **CLAUDE.md § 3.1** - Test file naming & organization principles
- **Repository:** Atoms MCP Server (FastMCP-based consolidation)

---

## 📞 Questions?

Refer to the detailed session documents:
1. Quick clarification → `CONSOLIDATION_SUMMARY.md`
2. Detailed explanation → `01_RESEARCH.md`
3. Step-by-step execution → `02_IMPLEMENTATION_STRATEGY.md`
4. Full context → `00_SESSION_OVERVIEW.md`

---

**Created:** 2025-11-13  
**Status:** Ready for Execution  
**Priority:** High (Improves maintainability, follows AGENTS.md standard)
