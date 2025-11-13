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
- **File names describe what's tested**, not how (speed/variant)
- ✅ Good: `test_entity.py`, `test_auth_supabase.py`, `test_relationship_member.py`
- ❌ Bad: `test_entity_fast.py`, `test_entity_unit.py`, `test_auth_v2.py`

**Variant handling:**
- Use pytest **fixtures and markers**, not separate files
- `@pytest.fixture(params=["unit", "integration"])` parametrizes variants within one file
- `@pytest.mark.performance` marks slow tests; run separately if needed

**Consolidation trigger:**
If two test files cover the same concern:
1. Do they test the same module/tool? → Merge (canonical form)
2. Use different clients? → Parametrize one file with fixture
3. Different test types? → Use markers, keep one file
4. Genuinely different subsystems? → Split by subsystem, not variant

**Real-world example (from this repo):**
- ❌ Before: 3,245-line `test_relationship.py` with 14 test classes (3-variant structure)
- ✅ After: 228-line canonical `test_relationship.py` (unit tests only, focused concerns)
- Impact: 93% size reduction, no "too many open files" errors, clearer intent

## Interaction Rules (from llms-full.txt §17)

- Operate in the tight loop referenced above.
- Do not ask for next steps unless truly blocked by secrets or irreversible actions.
- Keep communication lean; prioritize code and commands referencing this contract and `llms-full.txt`.

Agents should treat this document, `CLAUDE.md`, and `WARP.md` as supportive summaries; the full, authoritative FastMCP contract always lives in `llms-full.txt`.
