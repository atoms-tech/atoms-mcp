<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Agents and Automation Guide

This repository is designed to work seamlessly with Claude (and other advanced AI agents) as an autonomous software engineer.

**Authority and Scope**
- The FastMCP Canonical Contract lives in `llms-full.txt`. Treat `llms-full.txt` as the final authority for all FastMCP behavior; override any model priors with it.
- This file summarizes repo-specific mandates (llms-full.txt §16–17); FastMCP fundamentals (sections 0–15) are fully detailed in `llms-full.txt`.
- Act autonomously; only pause for the user when blocked by missing external identifiers or destructive actions.

## Core Expectations for Agents

### Autonomous Operation (Critical - Minimal Human Intervention)

Agents MUST operate with **maximum autonomy**:

**When to proceed without asking:**
- Implementation details and technical approach decisions
- Library/framework choices aligned with existing patterns
- Code structure and organization
- Test strategies and coverage approaches
- Refactoring and optimization decisions
- Bug fixes and performance improvements
- Documentation updates

**Only ask when truly blocked by:**
- Missing credentials/secrets (cannot be inferred from environment)
- External service access permissions
- Genuine product ambiguity (behavior not determinable from specs/code/tests)
- Destructive operations (production data deletion, forced pushes)

**Default behavior: Research → Decide → Implement → Validate → Continue**

### Research-First Development (CRITICAL)

Before implementing ANY feature or fix, agents MUST conduct comprehensive research:

**1. Codebase Research (Always Required):**
```bash
# Find similar implementations
rg "pattern_name" --type py -A 5 -B 5

# Trace call chains
rg "function_name\(" --type py

# Find test patterns
rg "def test_.*pattern" tests/ -A 10

# Check architecture patterns
rg "class.*Adapter\|class.*Factory\|class.*Provider" --type py
```

**2. Web Research (When Needed):**
- External API documentation (WorkOS, Supabase, FastMCP)
- Library usage patterns (when introducing new dependencies)
- Best practices for performance/security patterns
- Debugging rare errors or edge cases

**3. Research Documentation:**
- Document findings in `docs/sessions/<session-id>/01_RESEARCH.md`
- Include URLs, code examples, and decision rationale
- Update continuously as new information discovered

**Research Protocol:**
1. **Search codebase first** - 90% of patterns already exist
2. **Web search for external docs** - API contracts, library patterns
3. **Document decisions** - Why this approach over alternatives
4. **No guessing** - Research until confident, then implement

### Autonomous SWE Loop

- Follow continuous loop: **research → plan → execute → validate → polish → repeat**
- Do not ask for step-by-step guidance unless blocked by secrets/external access
- Make decisions based on:
  - Existing codebase patterns
  - FastMCP canonical contract (`llms-full.txt`)
  - Research findings (documented in session)
  - Test results and validation

### Environment & Tooling (FastMCP-First)

- Always activate project environment: `source .venv/bin/activate`
- Prefer `uv` for Python execution: `uv run`, `uv pip`, `uvx`
- Use existing Typer/CLI atoms and scripts when available
- Respect repo architecture abstractions:
  - `infrastructure/` - adapters (DB, auth, storage, monitoring)
  - `services/` - domain logic
  - `tools/` - orchestration only
  - `auth/` - session, middleware, providers

### File Size & Modularity Constraints

**Hard constraint: All modules ≤500 lines (target ≤350)**

- Check line count before adding features
- If file approaches 350+ lines → decompose immediately
- Extract cohesive responsibilities (caching, validation, adapters)
- Use clear, narrow interfaces
- Update imports in all callers; test thoroughly

### Aggressive Change Policy (CRITICAL)

**NO backwards compatibility. NO gentle migrations. NO MVP-grade implementations.**

- **Avoid ANY backwards compatibility shims or legacy fallbacks**
- **Always perform FULL, COMPLETE changes** when refactoring
- **Do NOT preserve deprecated patterns** for transition periods
- **Remove old code paths entirely** when replacing them
- **Update ALL callers simultaneously** when changing signatures
- **This enables clarity, performance, and maintainability**

**Forward-Only Progression:**
- NO `git revert` or `git reset` (fix forward instead)
- NO haphazard delete-and-rewrite cycles
- Push forward to clean, working states via incremental fixes
- If broken: fix with targeted changes, not rollbacks
- Document issues in `05_KNOWN_ISSUES.md`, resolve systematically

**Full Production-Grade Implementation:**
- NO minimal implementations or MVPs
- NO "we'll add this later" placeholder code
- Every feature: production-ready, fully tested, documented
- Complete error handling, edge cases, logging, monitoring
- Full test coverage (unit + integration + e2e where applicable)
- No TODO comments without immediate resolution plan

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

## OpenSpec Spec-Driven Development (CRITICAL - Use For All Features)

**OpenSpec is INSTALLED and MUST be used for all non-trivial feature work.**

### When to Use OpenSpec

**ALWAYS use OpenSpec for:**
- New features or capabilities
- Breaking changes or architecture shifts
- Cross-cutting concerns (auth, caching, monitoring)
- Performance or security improvements
- Database schema changes
- API contract changes

**Optional for:**
- Bug fixes (unless significant behavior change)
- Documentation updates
- Minor refactoring (< 50 lines)

### OpenSpec Workflow (3 Phases)

#### Phase 1: Proposal (Spec-First, Before ANY Code)

```bash
# Agent creates proposal BEFORE writing code
openspec init

# This creates:
# openspec/changes/<change-id>/
#   proposal.md    # Why, what, scope, alternatives
#   tasks.md       # Step-by-step implementation checklist
#   specs/         # Delta showing spec changes (ADDED/MODIFIED/REMOVED)
#     <domain>/spec.md
```

**Proposal Structure (`proposal.md`):**
```markdown
# <Feature Name>

## Summary
One-paragraph overview of the change.

## Motivation
Why is this change needed? What problem does it solve?

## Scope
- What IS included in this change
- What is NOT included (out of scope)
- Dependencies and prerequisites

## Design Decisions
- Approach chosen and why
- Alternatives considered and rejected
- Trade-offs and implications

## Implementation Tasks
See tasks.md for detailed checklist.

## Rollout Plan
- Deployment strategy
- Migration path (if applicable)
- Rollback plan
```

**Tasks Structure (`tasks.md`):**
```markdown
## 1. <Phase Name>
- [ ] 1.1 Specific atomic task
- [ ] 1.2 Another atomic task
  - Acceptance: What "done" looks like
  - Testing: How to verify

## 2. <Next Phase>
- [ ] 2.1 Task
...
```

**Spec Delta Format (`specs/<domain>/spec.md`):**
```markdown
# Delta for <Domain>

## ADDED Requirements
### Requirement: <Name>
The system MUST/SHALL <behavior>.

#### Scenario: <situation>
- GIVEN <preconditions>
- WHEN <action>
- THEN <expected outcome>

## MODIFIED Requirements
### Requirement: <Name>
(Include complete updated text, not just changes)

## REMOVED Requirements
### Requirement: <Name>
(Explain deprecation rationale)
```

**Agent Behavior During Proposal:**
1. **Research FIRST** (codebase + web if needed)
2. **Document findings** in `01_RESEARCH.md`
3. **Create OpenSpec proposal** via `openspec init`
4. **Write comprehensive proposal.md** (no "TBD" or "TODO")
5. **Break down tasks.md** (atomic, testable steps)
6. **Define spec deltas** (ADDED/MODIFIED/REMOVED with scenarios)
7. **Validate proposal** via `openspec validate <change-id>`
8. **Proceed to implementation** autonomously (no approval needed unless destructive)

#### Phase 2: Apply (Implement According to Spec)

```bash
# Agent follows tasks.md checklist
# Check off tasks as completed
# Update specs/ if requirements evolve during implementation
```

**Implementation Protocol:**
1. **Follow tasks.md order** (respect dependencies)
2. **Check off tasks** as completed (update tasks.md)
3. **Test each task** before moving to next
4. **Update specs/** if requirements evolve
5. **Document issues** in `05_KNOWN_ISSUES.md`
6. **No shortcuts** - full production-grade implementation

**Task Completion Criteria:**
- Code written and tested
- All callers updated (if signature changed)
- Tests passing (unit + integration where applicable)
- Documentation updated
- No breaking changes without migration path

#### Phase 3: Archive (Merge Specs After Completion)

```bash
# After ALL tasks complete and tests pass
openspec archive <change-id>

# This merges specs/changes/<change-id>/specs/ into openspec/specs/
# Archives change folder to openspec/archive/
```

**Archive Criteria:**
- ✅ All tasks in tasks.md checked off
- ✅ All tests passing (`uv run pytest`)
- ✅ Code reviewed (or self-reviewed if autonomous)
- ✅ Documentation complete
- ✅ No known critical bugs

**Agent Behavior During Archive:**
1. **Verify all tasks complete** - no unchecked items
2. **Run full test suite** - `uv run pytest tests/`
3. **Update specs/** if any final adjustments
4. **Run `openspec archive <change-id>`**
5. **Commit changes** with descriptive message
6. **Update session docs** (`06_COMPLETION_SUMMARY.md`)

### OpenSpec + Session Documentation Integration

**Parallel structures (both required):**

```
openspec/changes/<change-id>/       # OpenSpec structure
  proposal.md                        # Feature specification
  tasks.md                           # Implementation checklist
  specs/<domain>/spec.md             # Spec deltas

docs/sessions/<session-id>/         # Session documentation
  00_SESSION_OVERVIEW.md             # Goals, decisions
  01_RESEARCH.md                     # Research findings
  02_SPECIFICATIONS.md               # Extended context (link to OpenSpec)
  03_DAG_WBS.md                      # Dependencies, WBS
  04_IMPLEMENTATION_STRATEGY.md      # Technical deep-dive
  05_KNOWN_ISSUES.md                 # Bugs, workarounds
  06_TESTING_STRATEGY.md             # Test approach
```

**How they relate:**
- **OpenSpec** = Machine-readable specs, tasks, and validation
- **Session Docs** = Human context, research, decisions, issues

**Cross-references:**
- `02_SPECIFICATIONS.md` → Link to `openspec/changes/<change-id>/`
- `proposal.md` → Reference research in `01_RESEARCH.md`
- `05_KNOWN_ISSUES.md` → Track issues encountered during apply phase

### OpenSpec Commands Reference

```bash
# List active changes
openspec list

# View dashboard
openspec view

# Show change details
openspec show <change-id>

# Validate spec format
openspec validate <change-id>

# Archive completed change (non-interactive)
openspec archive <change-id> -y
```

### OpenSpec Best Practices

1. **Proposal before code** - Always create OpenSpec proposal first
2. **Atomic tasks** - Each task should be independently testable
3. **Comprehensive scenarios** - Every requirement needs scenario blocks
4. **Update during implementation** - If requirements evolve, update specs/
5. **Validate frequently** - Run `openspec validate` before commits
6. **Archive promptly** - Don't leave completed changes unarchived

### Example: Adding Rate Limiting Feature

```bash
# 1. Research (codebase + web)
rg "rate.*limit" --type py -A 5
# (Document findings in docs/sessions/20251113-rate-limiting/01_RESEARCH.md)

# 2. Create OpenSpec proposal
openspec init
# Change ID: add-distributed-rate-limiting

# 3. Write comprehensive proposal
# openspec/changes/add-distributed-rate-limiting/proposal.md
# (See structure above - full production-grade spec)

# 4. Define tasks
# openspec/changes/add-distributed-rate-limiting/tasks.md
## 1. Infrastructure Setup
- [ ] 1.1 Add Upstash Redis adapter
- [ ] 1.2 Add distributed rate limiter class
- [ ] 1.3 Add rate limit middleware

## 2. Integration
- [ ] 2.1 Integrate into server.py
- [ ] 2.2 Add per-tool rate limits
- [ ] 2.3 Add per-user rate limits

## 3. Testing
- [ ] 3.1 Unit tests for rate limiter
- [ ] 3.2 Integration tests with Redis
- [ ] 3.3 Load testing

## 4. Documentation
- [ ] 4.1 Update README.md
- [ ] 4.2 Add RATE_LIMITING.md guide
- [ ] 4.3 Update environment variables docs

# 5. Implement (follow tasks, check off as done)
# (Full production-grade implementation - no MVPs)

# 6. Archive after completion
openspec archive add-distributed-rate-limiting -y
```

## Session Documentation Management (Critical - Prevent Doc Proliferation)

**Problem:** Agent-generated documentation accumulates rapidly, creating noise in repository roots and subdirectories. This makes it difficult to locate current, relevant information and obscures architectural intent.

**Solution:** Strict session-based documentation structure with aggressive consolidation policies.

### Session Documentation Structure

All agent-generated work artifacts MUST be placed in:

```
docs/sessions/<YYYYMMDD-descriptive-name>/
```

**Required core session documents:**

1. **`00_SESSION_OVERVIEW.md`** - Goals, decisions, PR/issue links
2. **`01_RESEARCH.md`** - External documentation, API findings, precedents
3. **`02_SPECIFICATIONS.md`** - Full feature specs with **ARUs (Assumptions, Risks, Uncertainties)**
4. **`03_DAG_WBS.md`** - Dependency graph (DAG) and work breakdown structure (WBS)
5. **`04_IMPLEMENTATION_STRATEGY.md`** - Technical approach, architecture decisions
6. **`05_KNOWN_ISSUES.md`** - Current bugs, workarounds, technical debt, future work
7. **`06_TESTING_STRATEGY.md`** - Test plan, coverage goals, acceptance criteria

### Documentation Update Protocol

**Update triggers (prefer updating over creating new files):**
- New information → update `01_RESEARCH.md`
- Requirements change → update `02_SPECIFICATIONS.md` and `03_DAG_WBS.md`
- Implementation pivots → update `04_IMPLEMENTATION_STRATEGY.md`
- Bug discovered/fixed → update `05_KNOWN_ISSUES.md`

**Never create:** `FINAL`, `COMPLETE`, `V2`, `_NEW`, `_OLD`, `_DRAFT` suffixed documents.

### Documentation Consolidation Policy (Aggressive)

**When encountering doc proliferation:**

1. **Detect orphaned docs**
   ```bash
   find . -name "*.md" -type f | grep -E "(SUMMARY|STATUS|REPORT|COMPLETE|FINAL|CHECKLIST|V[0-9]|_OLD|_NEW)"
   ```

2. **Apply decision tree**
   ```
   Is doc still relevant?
   ├─ NO  → Delete immediately
   └─ YES → Is it session-specific?
          ├─ YES → Move to docs/sessions/<session-id>/
          └─ NO  → Is it canonical repo doc?
                 ├─ YES → Keep in docs/ (README, ARCHITECTURE, etc.)
                 └─ NO  → Merge into canonical doc or delete
   ```

3. **Consolidate aggressively**
   - Extract unique information from temporal docs
   - Merge into existing session documents
   - Delete redundant files without hesitation
   - Move session artifacts to appropriate session folder

### Canonical Repository Documentation (Exceptions)

These live in `docs/` root and persist across sessions:
- `docs/README.md` - Project overview
- `docs/ARCHITECTURE.md` - System design patterns
- `docs/API_REFERENCE.md` - Tool/API contracts
- `docs/DEPLOYMENT.md` - Infrastructure guides
- `docs/TESTING.md` - Test philosophy and frameworks
- `docs/TROUBLESHOOTING.md` - Common issues and debugging

**Update protocol:**
- Session-specific details → session folder
- Permanent architectural changes → canonical docs
- When uncertain → start in session folder, promote if universally relevant

### Agent Behavioral Rules

**Session start:**
1. Create `docs/sessions/<session-id>/` directory
2. Initialize with `00_SESSION_OVERVIEW.md`
3. Reference (don't duplicate) canonical docs

**During session:**
1. Update session docs continuously (living documents)
2. Never create temporal suffixed docs (`_FINAL`, `_V2`, etc.)
3. Consolidate discoveries into existing session docs

**Session end:**
1. Review all session docs for completeness
2. Scan repo for orphaned docs created during session
3. Move/consolidate docs outside session folder
4. Update canonical docs if permanent changes made

**When finding proliferation:**
1. Flag immediately for consolidation
2. Apply decision tree (above)
3. Delete temporal/redundant docs
4. Move session-specific docs to appropriate folder

### Expected Outcomes

**Before (proliferation state):**
- Root: 37+ .md files (STATUS, SUMMARY, FINAL, etc.)
- tests/: 49+ .md files (GUIDE, REPORT, CHECKLIST, etc.)
- Impossible to find current information

**After (session-based structure):**
- Root: ~4 .md files (AGENTS.md, CLAUDE.md, warp.md, README.md)
- tests/: 1 .md file (README.md)
- All session artifacts in `docs/sessions/<date-name>/`
- Clear separation of concerns
- Easy cleanup (archive old sessions)

## Interaction Rules (from llms-full.txt §17)

- Operate in the tight loop referenced above.
- Do not ask for next steps unless truly blocked by secrets or irreversible actions.
- Keep communication lean; prioritize code and commands referencing this contract and `llms-full.txt`.
- **Document work in session folders; consolidate aggressively to prevent proliferation.**

Agents should treat this document, `CLAUDE.md`, and `WARP.md` as supportive summaries; the full, authoritative FastMCP contract always lives in `llms-full.txt`.
