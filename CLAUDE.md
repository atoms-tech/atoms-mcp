# Claude Usage Guide

This repository is optimized for Claude (and similar LLM agents) acting as an autonomous senior software engineer for the Atoms MCP / FastMCP server.

**Core rules (non-optional):**
- Always activate the project environment: `source .venv/bin/activate` before running Python/uv.
- Prefer `uv` for all Python execution and dependency operations (`uv run`, `uv pip`, `uvx`) in alignment with FastMCP and this repo's tooling.
- Use existing Typer-based CLI atoms and scripts instead of ad-hoc commands when available.
- Follow the closed-loop workflow: review → research (code/web/reasoning) → plan → execute → test → polish → repeat.
- Do not ask the user what to do next unless blocked by missing secrets, external access, or true ambiguity.
- Respect repo architecture, abstractions, auth, and env conventions at all times.
- **Keep all modules ≤500 lines; target ≤350 lines. Decompose proactively to maintain clarity.**
- **Avoid backwards compatibility shims, legacy fallbacks, or gentle migrations. Always perform FULL, COMPLETE changes.**

## 1. Repository Mental Model for Claude

Understand these as first-class constraints before editing:
- Runtime: Python 3.12, FastMCP-based consolidated MCP server.
- Key modules:
  - `server.py` / `create_consolidated_server`: core MCP server wiring, auth, rate limiting.
  - `app.py`: ASGI entrypoint for Vercel/stateless HTTP.
  - `infrastructure/`: adapters (Supabase, auth, storage, monitoring, security, rate limiting).
  - `services/`: higher-level domain logic (embeddings, search, auth helpers).
  - `tools/`: consolidated tools (workspace, entity, relationship, workflow, query).
  - `auth/`: session, middleware, hybrid auth provider integration.
  - `tests/`: structured into unit, integration, e2e, performance, coverage helpers.
- Style: typed where practical, 100-char line length, Ruff/Black-compatible, clear logging, explicit error handling.
- **File size constraint: all modules ≤500 lines (target ≤350). Larger modules must be decomposed.**

Claude must:
- Reuse these layers instead of bypassing them.
- Keep changes minimal, composable, and driven by tests and call sites.
- Proactively decompose files approaching 350 lines into well-structured submodules.

## 2. File Size & Modularity Mandate (Critical)

**Hard constraint: All modules must stay ≤500 lines; target ≤350 lines.**

Before adding features to any file, check its current line count. If it approaches 350+ lines:
1. **Identify cohesive responsibilities** (caching, validation, adapters, domain logic).
2. **Extract into separate modules** following this hierarchy:
   - Domain logic → new `services/<domain>/` submodule
   - Adapters/clients → new `infrastructure/` submodule
   - Tool orchestration → split by feature within `tools/`
   - Helpers/utilities → new `utils/` or domain-specific modules
   - Tests mirror the production structure: `tests/<path>/__init__.py` + test files
3. **Update imports** in all callers; test each change with `uv run pytest`.
4. **Keep interfaces narrow**: expose only what's needed; hide internals.

**Aggressive Change Policy:**
- **When refactoring, update ALL callers and code paths simultaneously.** No partial migrations.
- **Remove old implementations entirely.** Don't leave deprecated code behind with conditional logic.
- **No feature flags, shims, or backwards compatibility layers.** Clean breaks enable clarity and performance.
- **All tests must pass after refactoring.** No "this part is still migrating."

### Decomposition Patterns

**Pattern 1: Service Submodule**
```
# Before: services/embedding_factory.py (400+ lines)
# After:
services/embedding/
  __init__.py        (exports public API)
  factory.py         (core creation logic)
  cache.py           (caching layer)
  validators.py      (input validation)
  types.py           (shared types)
```

**Pattern 2: Adapter Extraction**
```
# Before: infrastructure/adapters.py (500+ lines)
# After:
infrastructure/
  supabase_adapter.py      (DB operations)
  auth_adapter.py          (auth integration)
  rate_limiter_adapter.py  (rate limiting)
```

**Pattern 3: Tool Decomposition**
```
# Before: tools/entity.py (400+ lines)
# After:
tools/entity/
  __init__.py        (exports tool)
  handler.py         (main tool logic)
  validators.py      (entity validation)
  queries.py         (DB query helpers)
```

## 3. Standard Operating Loop (SWE Autopilot)

For every task (bug, feature, infra, test):
1. **Review**
   - Read the issue/error, relevant code, and existing tests.
   - Use search (rg/Glob/Read tools) to map usages before editing.
   - Check line counts on affected files; note decomposition needs.
2. **Research**
   - Check related modules and patterns in-repo.
   - When external APIs/libraries are involved, consult their official docs via web search.
3. **Plan**
   - Formulate a short, concrete plan (in your reasoning, keep user-facing text concise).
   - Ensure the plan aligns with existing abstractions and auth/infra patterns.
   - If any file will exceed 350 lines, include decomposition in the plan.
4. **Execute**
   - Implement in small, verifiable increments.
   - Match coding style, respect typing and logging conventions.
   - Decompose proactively; don't wait until a file hits 500 lines.
5. **Test**
   - Run targeted tests via `uv run pytest …` relevant to the change.
   - Start with focused suites; only widen scope if risk is broader.
   - Verify decomposed modules have equivalent test coverage.
   - For new test files: follow canonical naming (§ 3.1 below).
6. **Review & Polish**
   - Re-read diffs mentally; simplify, remove dead code, align naming with repo norms.
   - Verify all files stay ≤500 lines (ideally ≤350).
7. **Repeat**
   - If tests or behavior fail, loop without waiting for user direction.

## 3.1 Test File Naming & Organization (Canonical Standard)

**Critical principle**: Test files must use **canonical naming** that reflects their content's concern, not speed, variant, or development phase.

The name of a test file should answer: **"What component/concern does this test?"** not **"How fast is it?" or "What variant is it?"**

### **Naming Rules with Detailed Rationale**

✅ **Good (canonical - concern-based):**
- `test_entity.py` – tests the entity tool; any implementation detail for entity operations belongs here
- `test_entity_crud.py` – tests CREATE/READ/UPDATE/DELETE operations; separated by operation domain
- `test_entity_validation.py` – tests entity validation logic; separated by technical concern (validation)
- `test_auth_supabase.py` – tests Supabase-specific auth; separated by provider (integration point)
- `test_auth_authkit.py` – tests AuthKit integration; different provider, different concern
- `test_relationship_member.py` – tests member relationship type; separated by relationship domain
- `test_relationship_assignment.py` – tests assignment relationship type; separate domain, can be merged if overlap grows
- `test_database_adapter.py` – all database adapter tests; adapter is the concern
- `test_embedding_factory.py` – all embedding factory tests; factory is the component

**Why each is canonical:**
- Each name describes *what's being tested* (the component, tool, domain, or integration point)
- Two files with same test names would indicate duplication → consolidate
- File name and implementation are tightly coupled; changing implementation invites consolidation review

❌ **Bad (not canonical - metadata-based):**
- `test_entity_fast.py` – ❌ "fast" describes *speed*, not *content*. Use `@pytest.mark.performance` or `@pytest.mark.smoke` instead
- `test_entity_slow.py` – ❌ "slow" describes *duration*, not *concern*. Use markers in the same file
- `test_entity_unit.py` – ❌ "unit" describes *execution scope*, not *what's tested*. Use conftest fixtures (`mcp_client_inmemory`)
- `test_entity_integration.py` – ❌ "integration" describes *client type*, not *component*. Use fixture parametrization
- `test_entity_e2e.py` – ❌ "e2e" describes *test stage*, not *concern*. Use fixtures and markers instead
- `test_auth_final.py` – ❌ "final" is vague and temporal; adds no semantic information. Remove or name by concern
- `test_auth_v2.py` – ❌ Versioning belongs in git history (branch/tag), not file names. If truly different code, name by concern
- `test_entity_old.py`, `test_entity_new.py` – ❌ Temporal metadata. Refactor, merge, or delete instead
- `test_api_integration.py` – ❌ "integration" is redundant; file is in `tests/`. Name by *which API* is integrated

**How to recognize bad naming:**
- Does the suffix describe *how* to run the test? → Bad (use markers/fixtures)
- Does the suffix describe *when* it was written? → Bad (belongs in commit message)
- Does the suffix describe *temporal state*? (old/new/final/draft) → Bad (refactor instead)
- Does the suffix describe *test execution speed*? → Bad (use markers)
- Could two files have the same test name if they tested slightly different concerns? → They should consolidate

### **Why Canonical Naming Matters**

1. **Prevents accidental duplication**: When two test files have *nearly canonical* names, it signals they should be merged.
   - Example: `test_entity_unit.py` + `test_entity_integration.py` both test entity → merge, parametrize with fixtures
   - Non-canonical names hide duplication: `test_entity_fast.py` + `test_entity_comprehensive.py` might test the same thing but you won't notice

2. **Aids discovery**: File name immediately tells what's being tested without opening the file.
   - Maintainer looking at `test_auth_supabase.py` knows: "ah, this is Supabase auth integration"
   - Maintainer looking at `test_auth_v2.py` knows: ???

3. **Supports consolidation**: When refactoring, canonical names make it obvious which files should merge.
   - Same component? → Same concern → Same file. If `test_entity.py` and `test_entity_crud.py` both exist, merge.
   - Different components? → Different concerns → Different files. `test_auth_supabase.py` and `test_auth_authkit.py` have different integration points, keep separate (unless they converge later)

4. **Reduces clutter**: No `_old`, `_new`, `_backup`, `_temp`, `_draft` suffixes cluttering the tree.
   - Canonical names → code review → merge or delete. Not: save old versions as separate files
   - One source of truth per concern

5. **Enables automation**: Tools and scripts can scan test/ directory and understand structure.
   - CI/CD can identify which tests to run based on changed component (if naming is consistent)
   - Agents (like Claude) can suggest consolidation automatically (if naming is canonical)

### **Variant Testing (Unit/Integration/E2E)**

**Core principle**: Use **fixtures and markers**, NOT separate files, to handle test variants.

**Why?**
- One file = one concern = one source of truth
- Fixtures parametrize execution without duplication
- Markers categorize tests for selective runs
- Reduces code duplication dramatically

#### **Pattern 1: Fixture Parametrization (Recommended)**

```python
# ✅ GOOD: One file, fixture parametrization determines variant
# tests/unit/tools/test_entity.py

@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """Parametrized client fixture.
    
    Provides different clients based on test location:
    - tests/unit/ → unit (in-memory client)
    - tests/integration/ → integration (HTTP client)
    - tests/e2e/ → e2e (full deployment client)
    
    All tests in this file run 3 times, once per variant.
    """
    if request.param == "unit":
        return InMemoryMcpClient()  # Fast, deterministic
    elif request.param == "integration":
        return HttpMcpClient(...)   # Live database
    elif request.param == "e2e":
        return DeploymentMcpClient(...)  # Production setup
    
    return get_client(request.param)

async def test_entity_creation(mcp_client):
    """Test entity creation across all variants.
    
    This test runs 3 times:
    1. With in-memory client (unit)
    2. With HTTP client (integration)
    3. With deployment client (e2e)
    """
    result = await mcp_client.call_tool("entity_tool", {...})
    assert result.success
```

**Benefits:**
- Single file, not three
- Same test logic runs across variants automatically
- Adding new variant only requires updating fixture
- Test collection finds all variants at once

#### **Pattern 2: Markers (For Test Categorization)**

```python
# ✅ GOOD: Markers for categorizing tests within one file

@pytest.mark.asyncio
@pytest.mark.performance
async def test_entity_creation_performance(mcp_client):
    """Performance test: measure entity creation speed.
    
    Run with: pytest -m performance
    Skip with: pytest -m "not performance"
    """
    ...

@pytest.mark.asyncio
@pytest.mark.smoke
async def test_entity_basic_creation(mcp_client):
    """Smoke test: quick sanity check.
    
    Run with: pytest -m smoke  # <1 second
    """
    ...

@pytest.mark.asyncio
@pytest.mark.integration
async def test_entity_with_real_database(mcp_client):
    """Integration test: requires real database.
    
    Run with: pytest -m integration
    Skip in CI with: pytest -m "not integration"
    """
    ...
```

**CI/CD Usage:**
```bash
# Quick smoke tests only
pytest -m smoke  # 5 seconds

# All unit + smoke tests
pytest tests/unit -m "not integration and not performance"  # 30 seconds

# Full suite including integration + performance
pytest tests/ -m ""  # 5 minutes

# Only performance tests
pytest -m performance  # 2 minutes (run separately)
```

#### **❌ BAD Pattern: Separate Files for Variants**

```python
# ❌ BAD: Three files with redundant test code
# tests/unit/tools/test_entity.py
async def test_entity_creation(mcp_client_inmemory):
    ...

# tests/integration/tools/test_entity.py
async def test_entity_creation(mcp_client_http):  # Same test name!
    ...

# tests/e2e/tools/test_entity.py
async def test_entity_creation(mcp_client_e2e):  # Same test name again!
    ...
```

**Problems:**
- Code duplication (test logic repeated 3 times)
- Maintenance burden (change test → update in 3 places)
- Confusing directory structure
- Easy to miss a variant when adding tests
- Larger code footprint = harder to maintain

### **Consolidation Checklist**

When multiple test files cover overlapping concerns, use this decision tree:

**Question 1: Do they test the same component/tool?**
- **Yes** → They should be one file
- **No** → Proceed to Q2

**Question 2: Do they use different clients?**
- **Yes** → Use fixture parametrization (see Pattern 1 above), same file
- **No** → Proceed to Q3

**Question 3: Are they fundamentally different test types?**
- **Yes** (e.g., slow perf tests vs quick unit tests) → Use markers (see Pattern 2), same file
- **No** → Proceed to Q4

**Question 4: Do they test genuinely different subsystems?**
- **Yes** → Split by subsystem concern, keep separate
- **No** → Merge them; they have duplicate concerns

**Action Items:**
| Scenario | Decision | Implementation |
|----------|----------|-----------------|
| Same tool, different clients | Merge | Use `@pytest.fixture(params=[...])` |
| Same tool, different speeds | Merge | Use `@pytest.mark.performance`, `@pytest.mark.smoke` |
| Same tool, same everything | Definitely merge | Delete duplicate, consolidate |
| Different tools, same concern | Merge by concern | Rename file canonically by concern |
| Different tools, different concerns | Keep separate | Ensure each file has canonical name |

**Real-World Example: How We Fixed test_relationship.py**

| Aspect | Before | After | Action |
|--------|--------|-------|--------|
| **Lines** | 3,245 | 228 | Removed 3-variant duplication |
| **Test Classes** | 14 | 8 | Consolidated redundant classes |
| **Variants** | 3 (unit/integration/e2e) | 1 (unit via fixtures) | Removed file duplication, used fixtures |
| **Errors** | "too many open files" | None | Smaller file, no resource exhaustion |
| **Readability** | Complex | Clear | Focused on core functionality |

**Key insight**: The original file had the *same test logic* repeated across 3 variants. By using fixtures instead of separate files, we eliminated duplication while maintaining variant coverage.

## 3.2 Test File Organization Principles

**Organize test files by:** what's being tested (module/component concern)

**Do NOT organize test files by:** speed, variant, version, or other metadata

```
tests/
  unit/
    tools/
      test_entity.py                    # All entity tool tests (canonical)
      test_query.py                     # All query tool tests
      test_relationship.py              # All relationship tool tests
      test_workspace.py                 # All workspace tool tests
    infrastructure/
      test_auth_adapter.py              # All auth adapter tests
      test_database_adapter.py          # All database adapter tests
      test_storage_adapter.py           # All storage adapter tests
    services/
      test_embedding_factory.py         # All embedding factory tests
```

**Markers and fixtures** handle variants within files; file names describe content only.

## 4. Commands Claude Should Prefer

Environment:
- `source .venv/bin/activate`

Core checks:
- `uv run pytest -q` for quick validation.
- `uv run pytest tests/unit` for unit-only.
- `uv run pytest tests/integration` for integration.
- `uv run pytest tests/e2e` or specific files when touching workflows/endpoints.

Quality gates (when configured):
- `uv run ruff check`
- `uv run mypy`

Line count verification:
- `rg --line-number "^" <file> | tail -1` (show total lines in a file)

Server / runtime (examples, adjust per env vars):
- `uv run python app.py` (ASGI / Vercel-style entry).
- `uv run python server.py` or documented Typer/CLI entrypoints for MCP.

## 5. Behavioral Constraints for Claude

- Never introduce real secrets, keys, or tokens; use env vars and placeholders.
- Do not modify git config or push without explicit instruction.
- Prefer consolidated tools (workspace/entity/relationship/workflow/query) over direct DB/HTTP where adapters exist.
- Avoid speculative refactors unless required to fix a real issue.
- Keep explanations concise; focus tokens on accurate code and commands.
- **Always respect the 350-line target (500-line hard limit).** Decompose early, test thoroughly.
- **When refactoring, identify ALL callers and update them simultaneously.** No staggered migrations.
- **Remove old code paths entirely when replaced.** Zero tolerance for legacy conditionals or shims.

## 6. When Claude Must Ask

Only pause for user input when:
- Credentials, domains, or external IDs are required and cannot be inferred.
- There is a genuine product/behavior ambiguity not answered by code/tests/docs.
- An operation may be destructive (data deletion, production migrations, forced pushes).

Otherwise, proceed autonomously following this guide and AGENTS.md as the contract.
