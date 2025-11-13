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

**Critical principle**: Test files must use **canonical naming** that reflects their content's concern, not speed or variant.

### **Naming Rules**

✅ **Good (canonical):**
- `test_entity.py` – tests the entity tool
- `test_entity_crud.py` – tests CREATE/READ/UPDATE/DELETE operations
- `test_entity_validation.py` – tests entity validation logic
- `test_auth_supabase.py` – tests Supabase-specific auth
- `test_auth_authkit.py` – tests AuthKit integration
- `test_relationship_member.py` – tests member relationship type
- `test_relationship_assignment.py` – tests assignment relationship type

❌ **Bad (not canonical):**
- `test_entity_fast.py` – "fast" is about performance, not content (use `@pytest.mark.performance` instead)
- `test_entity_slow.py` – same issue; use markers
- `test_entity_unit.py` – "unit" is about execution scope, not content (use conftest fixtures)
- `test_entity_integration.py` – "integration" is about client type, not content
- `test_auth_final.py` – "final" adds no semantic information
- `test_auth_v2.py` – versioning belongs in commit history, not file names

### **Why Canonical Naming Matters**

1. **Prevents accidental duplication**: Two files with different concerns never use same test names
2. **Aids discovery**: File name immediately tells what's being tested
3. **Supports consolidation**: When refactoring, canonical names make it obvious which files should merge
4. **Reduces clutter**: No `_old`, `_new`, `_backup`, `_temp` suffixes cluttering the tree

### **Variant Testing (Unit/Integration/E2E)**

Use **fixtures and markers**, NOT file names:

```python
# ✅ GOOD: One file, fixture parametrization determines variant
@pytest.fixture(params=["unit", "integration", "e2e"])
def client(request):
    return get_client(request.param)

@pytest.mark.parametrize("variant", ["unit", "integration"])
async def test_entity_creation(client, variant):
    ...

# ❌ BAD: Three separate files with redundant tests
# test_entity_unit.py, test_entity_integration.py, test_entity_e2e.py
```

### **Consolidation Checklist**

When multiple test files cover the same concern:

1. **Do they test the same component?** → Merge into single canonical file
2. **Do they use different clients?** → Use fixture parametrization instead of separate files
3. **Are they different test types (slow perf tests vs quick unit tests)?** → Use markers (`@pytest.mark.performance`)
4. **Do they test genuinely different subsystems?** → Split by subsystem, not speed/variant

**Example: Relationship Tests Refactoring**
- **Before**: 3,245-line monolithic file with 14 test classes
- **Problem**: File too large, caused "too many open files" errors, complex 3-variant structure
- **After**: Single 228-line canonical `test_relationship.py` with focused unit tests
- **Solution**: Removed variant duplication, simplified to canonical form
- **Result**: 93% size reduction, faster collection, no resource errors

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
