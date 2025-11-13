# Warp Usage Guide

Warp is the primary terminal UX for operating on this repo. Use it with a tight, automated SWE loop.

**Authority**
- The FastMCP Canonical Contract lives in `llms-full.txt`. Treat `llms-full.txt` as final override for any FastMCP behavior. This file reflects repo-specific mandates (llms-full.txt §16–17). Refer to `llms-full.txt` for anything FastMCP-fundamental.

## 1. Environment & Tooling

- Always start sessions by activating the virtualenv:
  - `source .venv/bin/activate`
- Prefer `uv` for Python execution and dependency tasks:
  - `uv run python app.py`
  - `uv run pytest`
  - `uv pip install <pkg>` (when modifications are explicitly required)
- Use existing Typer/CLI entrypoints ("atoms" CLIs) and scripts instead of ad-hoc commands.

## 2. File Size & Modularity Mandate (Critical)

**Hard constraint: All modules must stay ≤500 lines; target ≤350 lines.**

- **Before adding features**, check the affected file's current line count.
- **If a file approaches 350+ lines**, decompose it immediately:
  - Extract cohesive responsibilities into separate modules.
  - Use clear, narrow interfaces between pieces.
  - Update imports in callers; test decomposition with `uv run pytest`.
- **Patterns for decomposition:**
  - Domain logic → new `services/` module
  - Adapters/clients → new `infrastructure/` module
  - Tool orchestration → keep in `tools/` but split by feature
  - Shared helpers → new `utils/` or domain-specific submodules
  - Tests stay close to code; mirror structure in `tests/`

**Example:** If `services/embedding_factory.py` exceeds 350 lines, split into:
- `services/embedding/factory.py` (core logic)
- `services/embedding/cache.py` (caching)
- `services/embedding/__init__.py` (public API)

This keeps complexity bounded and makes reviewing/testing straightforward.

**Aggressive Change Policy (CRITICAL):**
- **Avoid ANY backwards compatibility shims, legacy fallbacks, or gentle migrations.**
- **When refactoring, update ALL callers and code paths simultaneously.** No partial migrations.
- **Remove old code entirely.** Don't leave conditional branches for "transition periods."
- **This ensures clarity, performance, and zero technical debt accumulation from migration cruft.**

## 3. Recommended Warp Workflows

Create reusable Warp commands/snippets for:

- Quick status & line checks
  - `git status`
  - `uv run pytest -q`
  - `rg --line-number "^" <file> | tail -1` (check line count)

- Focused test runs
  - `uv run pytest tests/unit`
  - `uv run pytest tests/integration`
  - `uv run pytest tests/e2e`

- Lint/type checks (if configured)
  - `uv run ruff check`
  - `uv run mypy`

- Local MCP/HTTP server
  - `uv run python app.py`
  - `uv run python server.py`

Ensure Warp commands assume the venv is active and never hard-code secrets; rely on `.env`/env vars.

## 4. Operational Loop in Warp

For any debugging or change session executed via Warp:
1. **Review**: read the failure/requirement, inspect relevant code and tests.
2. **Research**: use `rg`, `uv run`, and FastMCP docs (llms-full.txt) as needed.
3. **Plan**: jot a brief plan (in notes or comments), then execute directly.
4. **Execute**: small, reviewable changes matching existing patterns.
5. **Size-check**: if any edited file nears 350 lines, plan decomposition.
6. **Identify all callers/dependencies** before proposing changes—no partial updates.
7. **Test**: use `uv run pytest` (targeted first, then broader if needed).
8. **Test naming**: when creating test files, ensure **canonical naming** (concern-based, not speed/variant-based). See CLAUDE.md § 3.1.

## 5. Test File Naming Convention (Canonical Standard)

**Critical**: Test file names must describe **what's being tested**, not how it's tested.

### **Examples**

✅ **Good (canonical - concern-based):**
```
test_entity.py                 # Tests the entity tool
test_entity_validation.py      # Tests entity validation (specific concern)
test_auth_supabase.py          # Tests Supabase auth integration
test_relationship_member.py    # Tests member relationship type
```

❌ **Bad (metadata-based - avoid):**
```
test_entity_fast.py            # "fast" is performance trait, not content
test_entity_unit.py            # "unit" is execution scope, not content
test_auth_v2.py                # Versioning belongs in git history, not names
test_relationship_final.py     # "final" adds no semantic info
test_api_integration.py        # File is already in tests/; "integration" belongs in fixtures
```

### **Why This Matters**

1. **Prevents accidental test duplication**: If two files have same name pattern, they should probably be merged
2. **Enables auto-discovery**: Maintainers can scan test/ directory and understand what's covered at a glance
3. **Supports intelligent consolidation**: When refactoring, canonical names highlight redundancy
4. **Reduces directory clutter**: No `_old`, `_new`, `_backup`, `_test`, `_draft` suffixes

### **When to Consolidate Test Files**

Ask these questions about test files with overlapping concerns:

**Q1: Do they test the same component?**
- Yes → Merge into single canonical file
- No → Go to Q2

**Q2: Do they use different clients/fixtures?**
- Yes → Use `@pytest.fixture(params=[...])` parametrization in single file
- No → Go to Q3

**Q3: Are they different test types (slow performance vs quick unit)?**
- Yes → Use `@pytest.mark.performance` or similar; keep in one file
- No → Go to Q4

**Q4: Do they test genuinely different subsystems?**
- Yes → Split by subsystem concern, not by speed/variant
- No → Merge them; likely duplicate

### **Example: How We Fixed test_relationship.py**

**Problem State:**
- File: 3,245 lines, 14 test classes
- Issue: 3-variant structure (unit/integration/e2e) with redundant test code
- Result: "too many open files" errors, slow collection, hard to maintain

**Refactoring:**
- Removed 3-variant duplication (kept unit tests only via fixtures)
- Simplified to canonical form (focused on core relationship tool functionality)
- Reduced to 228 lines

**Outcome:**
- ✅ 93% size reduction
- ✅ No file handle errors
- ✅ Faster collection
- ✅ Clearer test purposes
- ✅ Fewer tests (13 passing, all valuable)

**Key insight**: Fewer, well-named tests > many redundant tests
   - Ensure ALL tests pass after changes—no "partial migration" status.
   - Verify no legacy code paths remain after refactoring.
8. **Polish**: adjust naming, logs, and structure for clarity.
9. **Repeat**: continue until clean; do not pause for manual confirmation unless blocked.

## 5. Safety Practices

- Never commit from Warp without reviewing `git diff` and `git status`.
- Check for secrets before committing.
- Avoid global/system-level changes; keep all actions scoped to this repo.
- Verify line counts and modularity before committing large changes.

## 6. Repo-Specific Architecture Mandates (from llms-full.txt §16)

- Server: single consolidated FastMCP in `server.py`; no parallel servers.
- ASGI export: always `app = mcp.http_app(path="/api/mcp", stateless_http=True)` via `app.py`.
- Auth provider: use repo's hybrid auth pattern; avoid per-platform hard-codes.
- Tool design: business logic in `services/`; orchestrate only in `tools/`.
- Adapters: go through `infrastructure/`; never bypass DB/auth/storage.
- Tests: run via `uv run pytest`; use FastMCP client In-Memory for unit tests.
- **File size: keep all modules ≤500 lines (target ≤350) to maintain clarity and testability.**

Configure Warp so the canonical flows are a keystroke away, aligned with this guide and the full contract in `llms-full.txt`.
