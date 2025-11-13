# OpenSpec Integration & Aggressive Autonomous Agent Enhancements

**Date:** 2025-11-13  
**Status:** ✅ Complete  
**Files Updated:** `AGENTS.md` (665 lines, +353 lines added)

---

## Overview

Comprehensive integration of **OpenSpec spec-driven development** methodology with **aggressive autonomous agent behaviors**, enabling agents to operate with minimal human intervention while following rigorous research-first, forward-only progression patterns.

---

## Key Enhancements Added

### 1. **Autonomous Operation Guidelines** ✅

**Location:** `AGENTS.md` § "Autonomous Operation (Critical - Minimal Human Intervention)"

**What was added:**
- Clear boundaries for when agents should proceed vs. when to ask
- Default behavior: Research → Decide → Implement → Validate → Continue
- Agents empowered to make technical decisions autonomously

**When to proceed without asking:**
- Implementation details and technical approach decisions
- Library/framework choices aligned with existing patterns
- Code structure and organization
- Test strategies and coverage approaches
- Refactoring and optimization decisions
- Bug fixes and performance improvements
- Documentation updates

**Only ask when blocked by:**
- Missing credentials/secrets (cannot be inferred)
- External service access permissions
- Genuine product ambiguity (not determinable from specs/code/tests)
- Destructive operations (production data deletion, forced pushes)

---

### 2. **Research-First Development Protocol** ✅

**Location:** `AGENTS.md` § "Research-First Development (CRITICAL)"

**What was added:**
- Mandatory codebase research before ANY implementation
- Web research protocols for external docs/APIs
- Research documentation requirements
- Concrete `rg` command examples for codebase exploration

**Research Protocol (enforced):**
1. **Search codebase first** - 90% of patterns already exist
2. **Web search for external docs** - API contracts, library patterns
3. **Document decisions** - Why this approach over alternatives
4. **No guessing** - Research until confident, then implement

**Codebase Research Commands:**
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

**Documentation:**
- All findings go in `docs/sessions/<session-id>/01_RESEARCH.md`
- Include URLs, code examples, decision rationale
- Update continuously as new information discovered

---

### 3. **OpenSpec Spec-Driven Development Integration** ✅

**Location:** `AGENTS.md` § "OpenSpec Spec-Driven Development (CRITICAL - Use For All Features)"

**What was added:**
- Complete OpenSpec 3-phase workflow (Proposal → Apply → Archive)
- Detailed file structure templates (proposal.md, tasks.md, specs/*.md)
- Integration with existing session documentation structure
- Concrete examples and command reference

#### **Phase 1: Proposal (Spec-First, Before ANY Code)**

Agents MUST create OpenSpec proposals before writing code:

```bash
openspec init
# Creates:
# openspec/changes/<change-id>/
#   proposal.md    # Why, what, scope, alternatives
#   tasks.md       # Step-by-step implementation checklist
#   specs/         # Delta showing spec changes (ADDED/MODIFIED/REMOVED)
```

**proposal.md structure:**
- Summary: One-paragraph overview
- Motivation: Why needed, problem solved
- Scope: What IS/ISN'T included, dependencies
- Design Decisions: Approach chosen, alternatives rejected, trade-offs
- Rollout Plan: Deployment, migration, rollback

**tasks.md structure:**
- Atomic, independently testable tasks
- Acceptance criteria per task
- Testing approach per task

**specs/<domain>/spec.md delta format:**
- `## ADDED Requirements` - New capabilities
- `## MODIFIED Requirements` - Changed behavior (complete text)
- `## REMOVED Requirements` - Deprecated features
- Every requirement needs `#### Scenario:` blocks (GIVEN/WHEN/THEN)

#### **Phase 2: Apply (Implement According to Spec)**

Implementation protocol:
1. Follow tasks.md order (respect dependencies)
2. Check off tasks as completed (update tasks.md)
3. Test each task before moving to next
4. Update specs/ if requirements evolve
5. Document issues in `05_KNOWN_ISSUES.md`
6. No shortcuts - full production-grade implementation

#### **Phase 3: Archive (Merge Specs After Completion)**

```bash
openspec archive <change-id> -y
# Merges specs/changes/<change-id>/specs/ into openspec/specs/
# Archives change folder to openspec/archive/
```

**Archive criteria:**
- ✅ All tasks checked off
- ✅ All tests passing
- ✅ Code reviewed (or self-reviewed if autonomous)
- ✅ Documentation complete
- ✅ No known critical bugs

---

### 4. **OpenSpec + Session Documentation Integration** ✅

**Parallel structures (both required):**

```
openspec/changes/<change-id>/       # OpenSpec structure (machine-readable)
  proposal.md                        # Feature specification
  tasks.md                           # Implementation checklist
  specs/<domain>/spec.md             # Spec deltas

docs/sessions/<session-id>/         # Session documentation (human context)
  00_SESSION_OVERVIEW.md             # Goals, decisions
  01_RESEARCH.md                     # Research findings
  02_SPECIFICATIONS.md               # Extended context (link to OpenSpec)
  03_DAG_WBS.md                      # Dependencies, WBS
  04_IMPLEMENTATION_STRATEGY.md      # Technical deep-dive
  05_KNOWN_ISSUES.md                 # Bugs, workarounds
  06_TESTING_STRATEGY.md             # Test approach
```

**How they relate:**
- **OpenSpec** = Machine-readable specs, tasks, validation
- **Session Docs** = Human context, research, decisions, issues

**Cross-references:**
- `02_SPECIFICATIONS.md` → Link to `openspec/changes/<change-id>/`
- `proposal.md` → Reference research in `01_RESEARCH.md`
- `05_KNOWN_ISSUES.md` → Track issues encountered during apply phase

---

### 5. **Forward-Only Progression Mandate** ✅

**Location:** `AGENTS.md` § "Aggressive Change Policy (CRITICAL)"

**What was added:**
- NO `git revert` or `git reset` (fix forward instead)
- NO haphazard delete-and-rewrite cycles
- Push forward to clean, working states via incremental fixes
- If broken: fix with targeted changes, not rollbacks
- Document issues in `05_KNOWN_ISSUES.md`, resolve systematically

**Philosophy:**
- Rollbacks hide problems; forward fixes reveal understanding
- Git history should show problem-solving progression
- Issues are learning opportunities, not erasure candidates

---

### 6. **Full Production-Grade Implementation Standards** ✅

**Location:** `AGENTS.md` § "Aggressive Change Policy (CRITICAL)"

**What was added:**
- NO minimal implementations or MVPs
- NO "we'll add this later" placeholder code
- Every feature: production-ready, fully tested, documented
- Complete error handling, edge cases, logging, monitoring
- Full test coverage (unit + integration + e2e where applicable)
- No TODO comments without immediate resolution plan

**NO backwards compatibility:**
- NO backwards compatibility shims or legacy fallbacks
- Always perform FULL, COMPLETE changes when refactoring
- Do NOT preserve deprecated patterns for transition periods
- Remove old code paths entirely when replacing them
- Update ALL callers simultaneously when changing signatures

---

## OpenSpec Commands Reference

**Added to AGENTS.md:**

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

---

## Concrete Example Added

**Example: Adding Rate Limiting Feature**

Complete workflow demonstrating:
1. Research phase (codebase search + documentation)
2. OpenSpec proposal creation
3. Task breakdown (4 phases: Infrastructure, Integration, Testing, Documentation)
4. Implementation (following tasks.md)
5. Archive after completion

Shows full production-grade approach with no shortcuts.

---

## When to Use OpenSpec

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

---

## Impact Summary

### **File Changes**

| File | Before | After | Added | Change |
|------|--------|-------|-------|--------|
| `AGENTS.md` | 312 lines | 665 lines | +353 lines | +113% |

### **New Sections Added to AGENTS.md**

1. **Autonomous Operation** (19 lines) - When to ask vs. proceed
2. **Research-First Development** (35 lines) - Mandatory research protocols
3. **Autonomous SWE Loop** (9 lines) - Continuous improvement cycle
4. **Environment & Tooling** (9 lines) - FastMCP-first approach
5. **File Size & Modularity** (7 lines) - 350/500 line constraints
6. **Aggressive Change Policy** (24 lines) - Forward-only, full production-grade
7. **OpenSpec Spec-Driven Development** (258 lines) - Complete workflow integration
   - When to Use OpenSpec (13 lines)
   - 3-Phase Workflow (186 lines)
     - Phase 1: Proposal (97 lines)
     - Phase 2: Apply (25 lines)
     - Phase 3: Archive (20 lines)
   - OpenSpec + Session Docs Integration (28 lines)
   - Commands Reference (18 lines)
   - Best Practices (8 lines)
   - Concrete Example (42 lines)

### **Key Behaviors Enforced**

✅ **Autonomy**: Agents proceed without asking unless truly blocked  
✅ **Research-First**: No guessing; codebase + web research before implementation  
✅ **Spec-Driven**: OpenSpec proposal before any code  
✅ **Forward-Only**: No git revert/reset; fix forward  
✅ **Production-Grade**: No MVPs, no TODOs, full implementations  
✅ **Aggressive Changes**: No backwards compatibility, update all callers  

---

## Benefits

### **For Agents**

1. **Clear decision boundaries** - Know when to ask vs. proceed
2. **Research protocols** - Concrete commands for codebase exploration
3. **Spec-driven workflow** - Machine-readable proposals, tasks, specs
4. **Validation checkpoints** - `openspec validate` before commits
5. **Archive automation** - Clean separation of active vs. completed work

### **For Development Process**

1. **Predictable outcomes** - Specs define behavior before code
2. **Full context preservation** - Research + specs + implementation strategy
3. **No technical debt** - Aggressive changes, no legacy shims
4. **Forward progression** - Issues resolved, not hidden
5. **Production quality** - Every feature fully complete, tested, documented

### **For Maintainability**

1. **Discoverable specs** - `openspec/specs/` contains merged specifications
2. **Traceable changes** - `openspec/archive/` contains historical proposals
3. **Living documentation** - Session docs + OpenSpec specs stay current
4. **Clear history** - Git log shows problem-solving progression, not erasures

---

## Next Steps (Optional Enhancements)

The current integration is complete and production-ready. Optional future enhancements:

1. **Add OpenSpec integration to CLAUDE.md** - Mirror AGENTS.md guidance
2. **Add OpenSpec integration to warp.md** - Warp-specific workflows
3. **Create OpenSpec templates** - Pre-filled proposal/tasks/specs templates
4. **Add OpenSpec pre-commit hook** - Validate specs on commit
5. **Create doc proliferation checker script** - `scripts/check_doc_proliferation.sh`

---

## Conclusion

Agents now have comprehensive guidance for:
- Operating autonomously with minimal human intervention
- Conducting thorough research before implementation
- Following OpenSpec spec-driven development workflow
- Pushing forward to clean states (no rollbacks)
- Implementing full production-grade features (no MVPs)

**The result:** Predictable, high-quality, fully-documented development with maximum agent autonomy.
