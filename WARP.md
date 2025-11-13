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

**Critical**: Test file names must describe **what's being tested**, not how it's tested or when it was written.

### **The Core Principle**

A test file name should answer: **"What component/concern does this test?"**

NOT:
- "How fast is it?" (speed/performance)
- "What variant?" (unit/integration/e2e)
- "How mature is it?" (old/new/final/draft/v2)
- "What phase of testing?" (smoke/integration/e2e)

### **Examples with Detailed Rationale**

✅ **Good (canonical - concern-based):**
```
test_entity.py                 # Tests entity tool; all entity operations belong here
test_entity_validation.py      # Tests validation concern within entity (narrower scope)
test_auth_supabase.py          # Tests Supabase integration (different provider = different concern)
test_auth_authkit.py           # Tests AuthKit integration (different provider, separate file)
test_relationship_member.py    # Tests member relationship type (specific domain)
test_database_adapter.py       # Tests database adapter (component/infrastructure concern)
test_embedding_factory.py      # Tests embedding factory (component concern)
```

**Why each is canonical:**
- Each name describes the **component** (entity, auth, relationship) or **integration point** (supabase, authkit)
- Two files with overlapping names signal consolidation opportunity
- File name and responsibility are tightly coupled
- Adding tests to this component naturally extends the existing file

❌ **Bad (metadata-based - avoid):**
```
test_entity_fast.py            # ❌ "fast" is performance trait, not content
                               # Use: @pytest.mark.performance or same file with markers

test_entity_unit.py            # ❌ "unit" is execution scope, not what's tested
                               # Use: conftest fixtures (mcp_client_inmemory)

test_entity_integration.py     # ❌ "integration" is client type, not component
                               # Use: fixture parametrization in same file

test_entity_e2e.py             # ❌ "e2e" is test phase, not concern
                               # Use: markers + fixtures in same file

test_auth_v2.py                # ❌ Versioning belongs in git history (branch/tag), not names
                               # If truly different code: name by concern (test_auth_authkit.py)
                               # If refactored version: delete old, just commit as update

test_entity_old.py             # ❌ Temporal metadata; indicates abandoned code
test_entity_new.py             # ❌ "new" is also temporal; just refactor
test_entity_draft.py           # ❌ "draft" suggests WIP; either finish or delete
test_entity_final.py           # ❌ "final" is vague and temporal; what's "final" to you is not to others

test_api_integration.py        # ❌ Redundant; file is already in tests/
                               # Better: test_api_google.py or test_api_openai.py (specific integration)
```

**Recognition checklist:**
- Does suffix describe *how fast/slow*? → Bad (use markers)
- Does suffix describe *execution scope* (unit/integration/e2e)? → Bad (use fixtures)
- Does suffix describe *development phase* (old/new/draft/final)? → Bad (refactor/delete)
- Does suffix describe *temporal state*? → Bad (use commit history instead)
- Does suffix describe *test stage*? → Bad (use markers or fixtures)
- Could two files with similar names be testing the same thing? → Yes = merge them

### **Why Canonical Naming Matters**

1. **Prevents accidental duplication**
   - `test_entity_unit.py` + `test_entity_integration.py` both test entity → obvious merge candidate
   - `test_entity_fast.py` + `test_entity_comprehensive.py` might test same thing but you won't notice
   - Canonical naming makes duplication *visible*

2. **Enables discovery**
   - Maintainer scans `tests/unit/tools/` → sees `test_entity.py`, `test_query.py`, `test_workspace.py`
   - Immediately knows what's covered without opening files
   - Non-canonical: `test_entity_fast.py`, `test_query_slow.py`, `test_workspace_draft.py` → confusing

3. **Supports intelligent consolidation**
   - Same component? → Same file. Merge `test_entity.py` + `test_entity_crud.py` if both exist
   - Different components? → Different files. Keep `test_auth_supabase.py` separate from `test_auth_authkit.py`
   - Use decision tree (see § 5.1 below) to determine merge vs. separate

4. **Reduces directory clutter**
   - Canonical names → no `_old`, `_new`, `_draft`, `_v2`, `_final`, `_test`, `_backup` suffixes
   - One source of truth per concern
   - Old code: refactor/delete via PR, not stored as separate files

5. **Enables automation**
   - CI/CD can identify which tests to run based on changed component
   - Tools can scan test directory and suggest consolidation automatically
   - Agents (like Claude) can make intelligent decisions about test organization

### **Variant Handling: Fixtures + Markers, NOT Separate Files**

The **single most important decision** in test file organization:

❌ **Bad**: Create separate files for variants
```python
# tests/unit/tools/test_entity.py (10 tests × 3 = 30 lines)
async def test_entity_creation(mcp_client_inmemory):
    ...

# tests/integration/tools/test_entity.py (same 10 tests, 30 lines)
async def test_entity_creation(mcp_client_http):  # Same test name!
    ...

# tests/e2e/tools/test_entity.py (same 10 tests, 30 lines)
async def test_entity_creation(mcp_client_e2e):  # Same test name again!
    ...

# Total: 90 lines of code duplication
# Maintenance nightmare: change test → update 3 places
```

✅ **Good**: Use fixtures + parametrization
```python
# tests/unit/tools/test_entity.py (10 tests, 30 lines)
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """Parametrized client: tests run 3x, once per variant."""
    if request.param == "unit":
        return InMemoryMcpClient()
    elif request.param == "integration":
        return HttpMcpClient(...)
    elif request.param == "e2e":
        return DeploymentMcpClient(...)

async def test_entity_creation(mcp_client):
    """Runs 3 times automatically: unit, integration, e2e."""
    ...

# Total: 30 lines (same logic, no duplication)
# Change test once → all variants update
# Add new variant → just update fixture
```

**Benefits:**
- Single source of truth
- Same logic runs across variants
- No code duplication
- Easier maintenance
- Same coverage with less code

### **Consolidation Decision Tree**

When you find test files with overlapping concerns:

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

## 7. Session Documentation Management (Critical - Prevent Doc Proliferation)

**Problem:** Agent-generated documentation frequently proliferates in repo roots and subdirectories, creating noise and making it difficult to locate current, relevant information.

**Solution:** Structured session-based documentation with aggressive consolidation policies.

### **7.1 Session Documentation Structure**

All agent-generated documentation for a work session MUST be placed in:

```
docs/sessions/<session-id>/
```

Where `<session-id>` follows the pattern: `YYYYMMDD-<descriptive-name>`

Example structure:
```
docs/
  sessions/
    20251113-oauth-implementation/
      00_SESSION_OVERVIEW.md          # Session goals, context, decisions
      01_RESEARCH.md                  # External docs, API research, findings
      02_SPECIFICATIONS.md            # Full feature specs with ARUs
      03_DAG_WBS.md                   # Dependency graph, work breakdown
      04_IMPLEMENTATION_STRATEGY.md   # Technical approach, patterns used
      05_KNOWN_ISSUES.md              # Bugs found, workarounds, future work
      06_TESTING_STRATEGY.md          # Test plan, coverage goals
      artifacts/                      # Generated files, diagrams, exports
    20251112-rate-limiting/
      ...
```

### **7.2 Core Session Documents (Required)**

Every non-trivial session MUST maintain these living documents:

1. **`00_SESSION_OVERVIEW.md`**
   - High-level goals and success criteria
   - Key decisions and rationale
   - Links to related PRs, issues, discussions

2. **`02_SPECIFICATIONS.md`**
   - Full feature specifications
   - Acceptance criteria
   - **ARUs (Assumptions, Risks, Uncertainties)** with mitigation plans
   - API contracts and data models

3. **`03_DAG_WBS.md`**
   - Dependency graph (DAG) of all tasks
   - Work breakdown structure (WBS) with time estimates
   - Critical path analysis
   - Task dependencies and blockers

4. **`04_IMPLEMENTATION_STRATEGY.md`**
   - Technical approach and patterns
   - Architecture decisions
   - Code organization rationale
   - Performance/security considerations

5. **`05_KNOWN_ISSUES.md`**
   - Current bugs and their impact
   - Workarounds and fixes applied
   - Technical debt introduced
   - Future work recommendations

### **7.3 Documentation Update Protocol**

**When to Update Session Docs:**
- New information discovered → update `01_RESEARCH.md`
- Requirements change → update `02_SPECIFICATIONS.md` and `03_DAG_WBS.md`
- Implementation approach shifts → update `04_IMPLEMENTATION_STRATEGY.md`
- Bug found/fixed → update `05_KNOWN_ISSUES.md`

**Update Frequency:**
- After each significant discovery or decision
- Before context switches (end of work session)
- When blocked by uncertainty (document in ARUs)

**Prefer Updates Over New Files:**
- ✅ Update `02_SPECIFICATIONS.md` with new requirements
- ❌ Create `SPECIFICATIONS_V2.md` or `NEW_SPECS.md`

### **7.4 Documentation Consolidation Policy (Aggressive)**

**When encountering doc proliferation elsewhere in repo:**

1. **Identify orphaned/redundant docs**
   - Run: `find . -name "*.md" -type f | grep -E "(SUMMARY|STATUS|REPORT|COMPLETE|FINAL)"`
   - Flag files with temporal suffixes (`_FINAL`, `_V2`, `_OLD`, `_NEW`)

2. **Consolidation decision tree**
   ```
   Is doc still relevant?
   ├─ NO  → Delete immediately
   └─ YES → Is it session-specific?
          ├─ YES → Move to docs/sessions/<session-id>/
          └─ NO  → Is it canonical repo doc?
                 ├─ YES → Keep in docs/ (examples: README.md, ARCHITECTURE.md)
                 └─ NO  → Merge into existing canonical doc or delete
   ```

3. **Consolidation actions**
   ```bash
   # Example: Found OAUTH_COMPLETION_SUMMARY.md in root
   # Decision: Session-specific, still relevant
   mv OAUTH_COMPLETION_SUMMARY.md docs/sessions/20251110-oauth-implementation/06_COMPLETION_SUMMARY.md
   
   # Example: Found TEST_STATUS_FINAL.md in tests/
   # Decision: Temporal doc, information now in 05_KNOWN_ISSUES.md
   rm tests/TEST_STATUS_FINAL.md  # Delete after extracting any unique info
   
   # Example: Found three similar guides
   # Decision: Consolidate into single canonical guide
   cat GUIDE_V1.md GUIDE_V2.md GUIDE_FINAL.md > docs/CONSOLIDATED_GUIDE.md
   rm GUIDE_V1.md GUIDE_V2.md GUIDE_FINAL.md
   ```

### **7.5 Canonical Repo Documentation (Exceptions to Session Rule)**

These docs live in `docs/` root and are maintained across sessions:

- **`docs/README.md`** - Project overview, getting started
- **`docs/ARCHITECTURE.md`** - System architecture, design patterns
- **`docs/API_REFERENCE.md`** - Tool/API documentation
- **`docs/DEPLOYMENT.md`** - Deployment guides, infrastructure
- **`docs/TESTING.md`** - Testing philosophy, frameworks, patterns
- **`docs/TROUBLESHOOTING.md`** - Common issues, debugging guides

**Update Protocol:**
- Session-specific details → session folder
- Permanent architectural/API changes → canonical docs in `docs/`
- When unsure → start in session folder, promote to canonical if universally relevant

### **7.6 Detection and Cleanup Commands**

**Find doc proliferation:**
```bash
# Find temporal/status docs (candidates for deletion/consolidation)
find . -name "*.md" -type f | grep -E "(SUMMARY|STATUS|REPORT|COMPLETE|FINAL|CHECKLIST|V[0-9]|_OLD|_NEW|_DRAFT)"

# Count docs in problematic locations
ls -1 *.md 2>/dev/null | wc -l          # Root (should be <10)
ls -1 tests/*.md 2>/dev/null | wc -l    # Tests (should be <5)
```

**Automated consolidation check:**
```bash
# Run before committing to detect proliferation
./scripts/check_doc_proliferation.sh   # (TODO: create this script)
```

### **7.7 Agent Behavioral Rules**

**When starting a new session:**
1. Create `docs/sessions/<session-id>/` directory
2. Initialize with `00_SESSION_OVERVIEW.md`
3. Reference canonical docs; don't duplicate them

**During session work:**
1. Update session docs continuously (living documents)
2. Never create "FINAL" or "COMPLETE" suffixed docs
3. Consolidate discoveries into existing session docs

**Before ending session:**
1. Review all session docs for completeness
2. Scan repo for orphaned docs created during session
3. Move/consolidate any docs created outside session folder
4. Update canonical docs if permanent architectural changes made

**When finding doc proliferation:**
1. Immediately flag for consolidation
2. Apply decision tree (§ 7.4)
3. Delete temporal/redundant docs without hesitation
4. Move relevant session-specific docs to appropriate session folder

### **7.8 Benefits of Session-Based Documentation**

- **Discoverability**: All session artifacts in one place
- **Context preservation**: Full work history without clutter
- **Easier cleanup**: Old sessions can be archived/deleted cleanly
- **Prevents duplication**: Clear home for session-specific docs
- **Enforces living docs**: Update existing docs instead of creating new ones
- **Reduces noise**: Root/tests directories stay clean

### **7.9 Real-World Example: Before/After**

**Before (proliferation state):**
```
.
├── OAUTH_COMPLETION_SUMMARY.md
├── OAUTH_IMPLEMENTATION_SUMMARY.md
├── OAUTH_DOCUMENTATION_INDEX.md
├── OAUTH_MOCK_USAGE_GUIDE.md
├── TEST_FIX_COMPLETION_SUMMARY.md
├── TEST_INFRASTRUCTURE_FINAL_STATUS.md
├── TESTING_COMPLETE.md
├── FINAL_ASSESSMENT.md
├── VERIFICATION_CHECKLIST.md
└── tests/
    ├── COMPREHENSIVE_TEST_PLAN.md
    ├── IMPLEMENTATION_GUIDE.md
    ├── PHASE_2_COMPLETION_REPORT.md
    └── (46+ more .md files)
```

**After (session-based structure):**
```
docs/
  sessions/
    20251110-oauth-implementation/
      00_SESSION_OVERVIEW.md           # Goals: OAuth + mock clients
      01_RESEARCH.md                   # WorkOS docs, FastMCP patterns
      02_SPECIFICATIONS.md             # OAuth flow, mock client design
      03_DAG_WBS.md                    # Task breakdown, dependencies
      04_IMPLEMENTATION_STRATEGY.md    # Adapter pattern, persistent auth
      05_KNOWN_ISSUES.md               # CORS issues, session persistence edge cases
      06_COMPLETION_SUMMARY.md         # Final status, lessons learned
    20251112-test-infrastructure/
      00_SESSION_OVERVIEW.md           # Goals: Canonical test patterns
      02_SPECIFICATIONS.md             # Test naming standard, fixture design
      03_DAG_WBS.md                    # Test refactoring plan
      04_IMPLEMENTATION_STRATEGY.md    # Parametrization approach
      05_KNOWN_ISSUES.md               # test_relationship.py collection errors
  README.md                            # Permanent project overview
  ARCHITECTURE.md                      # Permanent architecture guide
```

**Impact:**
- Root: 37 .md files → 4 .md files (AGENTS.md, CLAUDE.md, warp.md, README.md)
- tests/: 49 .md files → 1 .md file (README.md)
- All session artifacts organized, discoverable, cleanly separated

Configure Warp so the canonical flows are a keystroke away, aligned with this guide and the full contract in `llms-full.txt`.
