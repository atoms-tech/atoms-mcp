# Agents and Automation Guide

This repository is designed to work seamlessly with Claude (and other advanced AI agents) as an autonomous software engineer.

**Authority and Scope**
- The FastMCP Canonical Contract lives in `llms-full.txt`. Treat `llms-full.txt` as the final authority for all FastMCP behavior; override any model priors with it.
- This file summarizes repo-specific mandates (llms-full.txt §16–17); FastMCP fundamentals (sections 0–15) are fully detailed in `llms-full.txt`.
- Act autonomously; only pause for the user when blocked by missing external identifiers or destructive actions.

## Core Expectations for Agents

- Act as an autonomous SWE:
  - Follow a continuous loop: review → research (FastMCP docs + repo) → plan → execute → review → test → polish → repeat.
  - Do not ask the user for step-by-step guidance unless blocked by missing secrets, external access, or product decisions.
- Always use the project environment and tooling (FastMCP-first):
  - `source .venv/bin/activate` before running Python or tests.
  - Prefer `uv` for running apps, tests, and tooling.
  - Use existing Typer/CLI atoms and scripts when available.
- **Honor repo architecture AND file size constraints (see mandates below):**
  - Use the abstractions in `infrastructure/`, `services/`, `tools/`, and `auth/` instead of duplicating logic.
  - Keep changes minimal, composable, and well-tested.
  - **Keep all modules ≤500 lines (target ≤350) to maintain readability and testability.**
- **Aggressive Change Policy (CRITICAL):**
  - **Avoid ANY backwards compatibility shims, legacy fallbacks, or gentle migrations.**
  - **Always perform FULL, COMPLETE changes** when refactoring or modernizing code.
  - **Do NOT preserve deprecated patterns** for transition periods.
  - **Remove old code paths entirely** when replacing them; don't leave conditional logic.
  - **Update all callers simultaneously** when changing signatures or behavior.
  - **This enables clarity, performance, and maintainability.** No technical debt accumulation from migration cruft.

## Repo-Specific Architecture Mandates (from llms-full.txt §16)

- **Server:** define a single consolidated FastMCP in `server.py` with name/instructions/auth; do not create parallel servers.
- **ASGI export:** always expose `app = mcp.http_app(path="/api/mcp", stateless_http=True)` via `app.py` for Vercel/serverless.
- **Auth provider:** use this repo's hybrid auth provider pattern; avoid per-platform hard-codes for token introspection.
- **Tool design:** place business logic in `services/`; orchestrate only in tools under `tools/`.
- **Adapters:** go through `infrastructure/`; never bypass DB/auth/storage adapters.
- **Tests:** run tests via `uv run pytest`; use FastMCP client In-Memory for unit tests.
- **File size (critical):** all modules must stay ≤500 lines; target ≤350 lines.
  - Decompose proactively when approaching 350 lines.
  - Extract to domain submodules, adapters, or services as appropriate.
  - Keep interfaces clean; mirror structure in tests.

## Recommended Agent Behaviors

1. **Discovery**
   - Inspect `app.py`, `server.py`, `tools/`, `infrastructure/`, `auth/`, and `tests/` to understand patterns.
   - Use `rg`/search to trace call chains before edits.
   - Check current line counts on files you'll modify; plan decomposition if near 350+ lines.
   - **Identify ALL callers and dependencies** before proposing changes (no partial updates).
   - **Check test file names for canonical form** (see CLAUDE.md § 3.1); flag non-canonical names for consolidation.

2. **Planning & Implementation**
   - Draft a concise plan per task; then implement directly without waiting for confirmation.
   - Align with existing style, typing, logging, and error handling.
   - **Size-aware design:** if a feature would push a file above 350 lines, plan modular decomposition upfront.
   - Extract cohesive responsibilities (caching, validation, adapters) into separate modules early.
   - **When refactoring, change ALL callers and code paths simultaneously—no shims or feature flags.**
   - **Remove deprecated code entirely; don't leave conditional branches for "transition periods."**
   - **For test files: use canonical naming** (concern-based, not speed/variant-based). See CLAUDE.md § 3.1.

3. **Testing & Validation**
   - Run relevant `uv run pytest` targets after modifications.
   - If failures appear, analyze, patch, and re-run until resolved or clearly blocked.
   - Verify decomposed modules have equivalent test coverage.
   - **After aggressive changes, ensure ALL tests pass—no partial migrations.**
   - When creating new test files, verify file name is canonical and no duplicate concerns exist in other test files.

4. **Safety & Secrets**
   - Never add real credentials or tokens.
   - Respect environment-driven configuration and deployment files.
   - Verify final line counts and commit structure before pushing.
   - **Verify that no legacy code paths remain after refactoring.**
   - **Consolidate test files with duplicate concerns** (see CLAUDE.md § 3.1 for checklist).

## Test File Governance (from CLAUDE.md § 3.1)

**Canonical Test Naming Standard:**

Test file names must answer: **"What component/concern does this test?"** – not **"How fast is it?" or "What variant?"**

✅ **Good (canonical - concern-based):**
- `test_entity.py` – all entity tool tests
- `test_auth_supabase.py` – Supabase-specific auth integration
- `test_auth_authkit.py` – AuthKit integration (different provider, different concern)
- `test_relationship_member.py` – member relationship type tests
- `test_database_adapter.py` – all database adapter tests

❌ **Bad (metadata-based - avoid):**
- `test_entity_fast.py` – "fast" describes speed, not content (use `@pytest.mark.performance`)
- `test_entity_unit.py` – "unit" describes scope, not what's tested (use conftest fixtures)
- `test_entity_integration.py` – "integration" describes client type (use fixture parametrization)
- `test_entity_e2e.py` – "e2e" describes test stage (use markers)
- `test_auth_v2.py` – versioning belongs in git history, not file names
- `test_entity_old.py`, `test_entity_new.py` – temporal metadata (refactor, merge, or delete)

**Why canonical naming matters:**
1. **Detects duplication** – Similar file names signal they should merge
2. **Enables discovery** – File name immediately tells what's tested, no need to open the file
3. **Supports consolidation** – When refactoring, canonical names highlight redundancy
4. **Reduces clutter** – No `_old`, `_new`, `_fast`, `_slow`, `_draft`, `_v2`, `_final` suffixes
5. **Enables automation** – Tools and CI/CD can understand test structure and make smart decisions

**Variant handling (critical distinction):**

Use pytest **fixtures and markers**, NOT separate files:

```python
# ✅ GOOD: One file, multiple variants via fixture
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """Parametrized client: tests run 3 times, once per variant."""
    if request.param == "unit":
        return InMemoryMcpClient()  # Fast, deterministic
    elif request.param == "integration":
        return HttpMcpClient(...)   # Live database
    elif request.param == "e2e":
        return DeploymentMcpClient(...)  # Production setup

async def test_entity_creation(mcp_client):
    """Runs 3 times automatically: unit, integration, e2e."""
    result = await mcp_client.call_tool("entity_tool", {...})
    assert result.success

# ❌ BAD: Three separate files with redundant code
# test_entity_unit.py, test_entity_integration.py, test_entity_e2e.py
# (same test, written 3 times = code duplication & maintenance burden)
```

**Benefits of fixture parametrization:**
- Single source of truth (one test file)
- Same logic runs across variants automatically
- Change test once, all variants update
- Adding new variant only requires fixture change
- No code duplication

**Consolidation Decision Tree:**

When multiple test files have overlapping concerns:

| Question | Answer | Action |
|----------|--------|--------|
| Same component/tool? | Yes | Merge into single canonical file |
| Different clients? | Yes | Use `@pytest.fixture(params=[...])` in one file |
| Different test types (fast vs slow)? | Yes | Use `@pytest.mark.performance` / `@pytest.mark.smoke` |
| Different subsystems? | Yes | Keep separate, ensure canonical names |
| Different subsystems? | No | Merge; duplicate concerns |

**Real-world example (from this repo):**

Before refactoring:
- **File**: 3,245-line `test_relationship.py`
- **Structure**: 14 test classes, complex 3-variant setup (unit/integration/e2e)
- **Problem**: Massive file, "too many open files" errors, hard to maintain, redundant test logic

After refactoring:
- **File**: 228-line canonical `test_relationship.py`
- **Structure**: 8 focused test classes, unit tests only (variants via fixtures)
- **Result**: 93% size reduction, no collection errors, clearer intent, same coverage

**Impact table:**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Lines | 3,245 | 228 | -93% (3,017 lines removed) |
| Test classes | 14 | 8 | Consolidated redundancy |
| Code duplication | High (3x) | None (fixture-based) | Eliminated |
| Variants | 3 variants (3 files) | 1 file + fixtures | Same coverage, cleaner |
| Collection errors | Frequent | None | ✅ Fixed |
| Developer confusion | High (many files) | Low (clear naming) | Improved clarity |

**Agent behavior when creating/reviewing test files:**

1. **Discovery**: Always check for existing test files covering same concern
   - `rg "def test_" tests/` to find similar test names
   - Look for files with similar prefixes → consolidation candidates
   
2. **Naming**: Ensure new test file name is **canonical**
   - Does it describe "what's tested"? ✅ Good
   - Does it describe "how fast"? ❌ Use markers instead
   - Does it describe "which variant"? ❌ Use fixtures instead
   
3. **Consolidation**: If two files cover same tool/component
   - Use checklist above to decide: merge vs. separate
   - Prefer fixture parametrization over separate files
   - Prefer markers over creating slow/fast variants
   
4. **Documentation**: When consolidating
   - Update file docstring to list all concerns/variants covered
   - Document fixture parameters and what each provides
   - Add consolidation note to git commit message

## Interaction Rules (from llms-full.txt §17)

- Operate in the tight loop referenced above.
- Do not ask for next steps unless truly blocked by secrets or irreversible actions.
- Keep communication lean; prioritize code and commands referencing this contract and `llms-full.txt`.

Agents should treat this document, `CLAUDE.md`, and `WARP.md` as supportive summaries; the full, authoritative FastMCP contract always lives in `llms-full.txt`.
