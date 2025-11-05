# Atoms-MCP-Prod: Refactor Documentation Index

## 📖 Complete Documentation Suite

This directory contains a comprehensive refactor plan to transform atoms-mcp-prod from a sprawling 248-file codebase into a clean, maintainable 80-file hexagonal architecture.

---

## 🎯 Start Here

**New to this refactor?** Read these in order:

1. **[REFACTOR_OVERVIEW.md](REFACTOR_OVERVIEW.md)** ⭐ START HERE
   - Executive summary
   - Quick stats and transformation summary
   - Before/after comparison
   - **Read time: 5 minutes**

2. **[REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)**
   - Detailed metrics and improvements
   - Dependency changes
   - Architecture principles
   - **Read time: 10 minutes**

3. **[COMPREHENSIVE_REFACTOR_PLAN.md](COMPREHENSIVE_REFACTOR_PLAN.md)**
   - Complete refactor plan (1400+ lines)
   - Phase-by-phase breakdown
   - File-by-file migration plan
   - **Read time: 30 minutes**

---

## 📚 Detailed Documentation

### Visual Guides

**[REFACTOR_VISUAL_GUIDE.md](REFACTOR_VISUAL_GUIDE.md)**
- Architecture diagrams (before/after)
- Dependency flow visualization
- Configuration consolidation
- CLI consolidation
- Pheno-SDK adapter pattern
- Test consolidation

### Implementation

**[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)**
- Step-by-step code examples
- Domain layer implementation
- Application layer implementation
- Adapter layer implementation
- Configuration setup
- Pheno-SDK adapter with fallback

### Execution

**[REFACTOR_CHECKLIST.md](REFACTOR_CHECKLIST.md)**
- Day-by-day checklist (18 days)
- Week-by-week breakdown
- Verification commands
- Success criteria

---

## 🎯 Quick Reference

### Key Metrics

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Python Files | 248 | 80 | **68%** ↓ |
| Lines of Code | 55,946 | 22,000 | **61%** ↓ |
| Config Files | 8 | 1 | **88%** ↓ |
| CLI Files | 4 | 1 | **75%** ↓ |
| Test Files | 100+ | 15 | **85%** ↓ |
| Dependencies | 30+ | 12 | **60%** ↓ |

### Key Changes

1. **Configuration:** 8 files → 1 file (90% reduction)
2. **CLI:** 4 implementations → 1 file (92% reduction)
3. **Pheno-SDK:** 50+ imports → 1 adapter (98% reduction)
4. **Tests:** 100+ files → 15 files (85% reduction)
5. **Architecture:** Scattered → Hexagonal (ports & adapters)

### Timeline

- **Week 1:** Domain layer (pure Python)
- **Week 2:** Application layer (use cases)
- **Week 3:** Adapters (external integration)
- **Week 4:** Migration & cleanup
- **Week 5:** Polish & deploy

---

## 🔧 Tools & Technologies

### Replaced

- ❌ mypy → ✅ pyright (via zuban)
- ❌ black, isort, flake8, pylint → ✅ ruff
- ❌ Multiple config systems → ✅ Single Pydantic settings

### Required Dependencies (10 core)

```toml
dependencies = [
    "fastmcp>=2.13.0.1",              # MCP framework
    "pydantic>=2.11.7,<3.0.0",        # Validation
    "pydantic-settings>=2.3.0",       # Config
    "supabase>=2.5.0",                # Database
    "httpx>=0.28.1,<1.0.0",           # HTTP
    "typer>=0.9.0",                   # CLI
    "rich>=13.0.0",                   # Terminal UI
    "google-cloud-aiplatform>=1.49.0", # Vertex AI (REQUIRED)
    "workos>=1.0.0",                  # Auth (REQUIRED)
    "PyYAML>=6.0",                    # Config
]
```

### Optional Dependencies (2 groups)

```toml
[project.optional-dependencies]
infra = ["pheno_sdk"]  # Infrastructure helpers (optional)
sst = []               # Future: SST Python SDK
```

---

## 📁 New Directory Structure

```
atoms-mcp-prod/
├── src/atoms_mcp/              # Core application
│   ├── domain/                 # Business logic (pure Python)
│   │   ├── models/             # Entity, Relationship, Workspace, Workflow
│   │   ├── services/           # Business services
│   │   └── ports/              # Interfaces (Repository, Cache, Embeddings)
│   │
│   ├── application/            # Use cases
│   │   ├── commands/           # Write operations
│   │   ├── queries/            # Read operations
│   │   └── workflows/          # Complex operations
│   │
│   ├── adapters/               # External integrations
│   │   ├── primary/            # Inbound (MCP, CLI)
│   │   └── secondary/          # Outbound (Supabase, Vertex, Pheno, Cache)
│   │
│   └── infrastructure/         # Cross-cutting
│       ├── config/             # Single settings file
│       ├── logging/
│       ├── errors/
│       └── di.py               # Dependency injection
│
├── tests/                      # Consolidated tests
│   ├── unit/                   # Domain & application
│   ├── integration/            # Adapters
│   └── performance/            # Load tests
│
├── scripts/                    # Utility scripts
├── schemas/                    # Database schemas
├── docs/                       # Documentation
├── pyproject.toml              # Simplified dependencies
└── fastmcp.json                # FastMCP config
```

---

## ✅ Success Criteria

- [ ] **68% reduction in files** (248 → 80)
- [ ] **61% reduction in LOC** (56K → 22K)
- [ ] **Hexagonal architecture** (clear separation)
- [ ] **Pheno-SDK adapter** (optional, not required)
- [ ] **Single configuration** (1 file vs 8)
- [ ] **Consolidated CLI** (1 file vs 4)
- [ ] **DRY principles** (no duplication)
- [ ] **SOLID principles** (dependency inversion)
- [ ] **>80% test coverage**
- [ ] **Modern tooling** (ruff, pyright/zuban)

---

## 🚀 Getting Started

1. **Read:** [REFACTOR_OVERVIEW.md](REFACTOR_OVERVIEW.md) (5 min)
2. **Review:** [COMPREHENSIVE_REFACTOR_PLAN.md](COMPREHENSIVE_REFACTOR_PLAN.md) (30 min)
3. **Execute:** Follow [REFACTOR_CHECKLIST.md](REFACTOR_CHECKLIST.md) day-by-day
4. **Reference:** Use [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for code examples
5. **Track:** Check off items in the checklist as you complete them

---

## 📞 Questions?

- Architecture questions? See [COMPREHENSIVE_REFACTOR_PLAN.md](COMPREHENSIVE_REFACTOR_PLAN.md) Phase 3
- Implementation questions? See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- Visual diagrams? See [REFACTOR_VISUAL_GUIDE.md](REFACTOR_VISUAL_GUIDE.md)
- Quick stats? See [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)

---

**Ready to transform chaos into clean architecture? Let's go! 🎯**

