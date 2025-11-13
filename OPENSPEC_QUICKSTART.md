# OpenSpec Quick Start Guide

**Status:** ✅ OpenSpec initialized and configured  
**Date:** 2025-11-13

---

## ✅ What's Been Set Up

### 1. **OpenSpec Structure Created**

```
openspec/
  ├── AGENTS.md         # OpenSpec workflow instructions for AI agents
  ├── project.md        # Comprehensive project context (COMPLETED)
  ├── changes/          # Active change proposals (empty - ready for use)
  └── specs/            # Merged specifications (will accumulate over time)
```

### 2. **Comprehensive `project.md` Populated**

The `openspec/project.md` file now contains:
- ✅ **Purpose** - Atoms MCP Server overview, key goals
- ✅ **Tech Stack** - Complete technology breakdown (Python 3.12, FastMCP, Supabase, WorkOS, Upstash, Vertex AI)
- ✅ **Code Style** - Formatting rules, naming conventions, type hints
- ✅ **Architecture Patterns** - Layered architecture, adapter pattern, dependency injection, file size constraints
- ✅ **Testing Strategy** - Test organization, canonical naming, requirements, commands
- ✅ **Git Workflow** - Branching strategy, commit conventions, forward-only progression
- ✅ **Domain Context** - Atoms platform overview, 5 consolidated tools, auth model
- ✅ **Important Constraints** - Technical, deployment, quality, business constraints
- ✅ **External Dependencies** - Supabase, WorkOS, Upstash, Vertex AI details
- ✅ **Canonical Authority** - References to `llms-full.txt`, `AGENTS.md`, `CLAUDE.md`, `warp.md`
- ✅ **Session Documentation** - Living docs structure
- ✅ **Research-First Development** - Codebase research commands

**Total:** 370 lines of comprehensive project context

---

## 📖 OpenSpec Workflow (3 Phases)

### **Phase 1: Proposal (Spec-First, Before ANY Code)**

When starting a new feature:

```bash
# Navigate to project
cd /path/to/atoms-mcp-prod

# Create OpenSpec proposal
openspec init

# You'll be prompted for:
# - Change ID (e.g., "add-rate-limiting", "fix-auth-bug")
# - Description (brief summary)
```

This creates:
```
openspec/changes/<change-id>/
  ├── proposal.md    # Why, what, scope, alternatives, rollout plan
  ├── tasks.md       # Step-by-step implementation checklist
  └── specs/         # Delta showing spec changes (ADDED/MODIFIED/REMOVED)
      └── <domain>/spec.md
```

**AI Agent Behavior:**
1. Research FIRST (codebase + web if needed)
2. Document findings in `docs/sessions/<session-id>/01_RESEARCH.md`
3. Create OpenSpec proposal via `openspec init`
4. Write comprehensive `proposal.md` (no "TBD" or "TODO")
5. Break down `tasks.md` (atomic, testable steps)
6. Define spec deltas (ADDED/MODIFIED/REMOVED with scenarios)
7. Validate proposal: `openspec validate <change-id>`
8. Proceed to implementation autonomously

### **Phase 2: Apply (Implement According to Spec)**

Follow the tasks.md checklist:

```bash
# View active changes
openspec list

# Show change details
openspec show <change-id>

# As you implement:
# - Check off tasks in tasks.md
# - Test each task before moving to next
# - Update specs/ if requirements evolve
# - Document issues in docs/sessions/<session-id>/05_KNOWN_ISSUES.md
```

**Implementation Protocol:**
1. Follow tasks.md order (respect dependencies)
2. Check off tasks as completed
3. Test each task before moving to next
4. Update specs/ if requirements evolve
5. Document issues in session docs
6. No shortcuts - full production-grade implementation

### **Phase 3: Archive (Merge Specs After Completion)**

After all tasks complete and tests pass:

```bash
# Verify all tasks checked off
openspec show <change-id>

# Run full test suite
uv run pytest tests/

# Archive (non-interactive)
openspec archive <change-id> -y

# This:
# - Merges specs/changes/<change-id>/specs/ into openspec/specs/
# - Moves change folder to openspec/archive/
# - Updates CHANGELOG
```

**Archive Criteria:**
- ✅ All tasks in tasks.md checked off
- ✅ All tests passing
- ✅ Code reviewed (or self-reviewed if autonomous)
- ✅ Documentation complete
- ✅ No known critical bugs

---

## 🎯 When to Use OpenSpec

### **ALWAYS use OpenSpec for:**
- New features or capabilities
- Breaking changes or architecture shifts
- Cross-cutting concerns (auth, caching, monitoring)
- Performance or security improvements
- Database schema changes
- API contract changes

### **Optional for:**
- Bug fixes (unless significant behavior change)
- Documentation updates
- Minor refactoring (< 50 lines)

---

## 📝 OpenSpec + Session Documentation Integration

**Use both in parallel:**

### **OpenSpec** (Machine-Readable Specs)
```
openspec/changes/<change-id>/
  ├── proposal.md    # Feature specification
  ├── tasks.md       # Implementation checklist
  └── specs/         # Spec deltas
```

### **Session Docs** (Human Context)
```
docs/sessions/<session-id>/
  ├── 00_SESSION_OVERVIEW.md          # Goals, decisions
  ├── 01_RESEARCH.md                  # Research findings
  ├── 02_SPECIFICATIONS.md            # Extended context (links to OpenSpec)
  ├── 03_DAG_WBS.md                   # Dependencies, WBS
  ├── 04_IMPLEMENTATION_STRATEGY.md   # Technical approach
  ├── 05_KNOWN_ISSUES.md              # Bugs, workarounds
  └── 06_TESTING_STRATEGY.md          # Test plan
```

**Cross-references:**
- `02_SPECIFICATIONS.md` → Link to `openspec/changes/<change-id>/`
- `proposal.md` → Reference research in `01_RESEARCH.md`
- `05_KNOWN_ISSUES.md` → Track issues encountered during apply phase

---

## 💻 OpenSpec Commands Reference

```bash
# List active changes
openspec list

# View interactive dashboard
openspec view

# Show change details
openspec show <change-id>

# Validate spec format
openspec validate <change-id>

# Archive completed change (non-interactive)
openspec archive <change-id> -y

# Update AI tool integrations (when OpenSpec updates)
openspec update
```

---

## 🔧 Example: Complete Workflow

### **1. Research Phase**

```bash
# Find similar implementations
rg "rate.*limit" --type py -A 5

# Document findings
# Create docs/sessions/20251113-rate-limiting/01_RESEARCH.md
```

### **2. Create OpenSpec Proposal**

```bash
openspec init
# Change ID: add-distributed-rate-limiting
# Description: Add Redis-backed distributed rate limiting for MCP tools
```

### **3. Write Comprehensive Proposal**

Edit `openspec/changes/add-distributed-rate-limiting/proposal.md`:

```markdown
# Distributed Rate Limiting

## Summary
Add Redis-backed distributed rate limiting using Upstash to prevent API abuse and ensure fair usage across all MCP tool invocations.

## Motivation
- Current rate limiting is in-memory only (doesn't scale across serverless instances)
- Need distributed coordination for multi-instance deployments
- Upstash Redis is already integrated for caching

## Scope
**In scope:**
- Distributed rate limiter class using Upstash Redis
- Per-user rate limiting (100 requests/minute)
- Per-tool rate limiting (configurable limits)
- Rate limit middleware integration
- Comprehensive tests (unit + integration + load)

**Out of scope:**
- Dynamic rate limit adjustment (future work)
- Per-organization quotas (future work)

## Design Decisions
- **Token bucket algorithm** - Smooth rate limiting vs. fixed windows
- **Upstash Redis** - Serverless-compatible, already integrated
- **Middleware pattern** - Centralized enforcement at server level
- **Graceful degradation** - If Redis unavailable, fail open (log warnings)

## Rollout Plan
- Deploy to staging first
- Monitor Redis performance under load
- Gradual rollout to production (10% → 50% → 100%)
- Rollback: Remove middleware, Redis rate limiter still available for manual use
```

### **4. Define Tasks**

Edit `openspec/changes/add-distributed-rate-limiting/tasks.md`:

```markdown
## 1. Infrastructure Setup
- [ ] 1.1 Add Upstash rate limiter client to infrastructure/upstash_provider.py
  - Acceptance: Client can connect to Upstash, handle token bucket operations
  - Testing: Unit tests with mocked Redis
- [ ] 1.2 Add distributed rate limiter class to infrastructure/distributed_rate_limiter.py
  - Acceptance: Token bucket algorithm working correctly
  - Testing: Unit tests for token consumption, refill logic

## 2. Integration
- [ ] 2.1 Add rate limit middleware to server.py
  - Acceptance: Middleware intercepts all tool calls, enforces limits
  - Testing: Integration tests with real Redis
- [ ] 2.2 Configure per-user rate limits (100 req/min)
  - Acceptance: Users limited to 100 requests/minute
  - Testing: Integration tests with multiple users
- [ ] 2.3 Configure per-tool rate limits (configurable)
  - Acceptance: Tools can have custom rate limits
  - Testing: Unit tests for config parsing

## 3. Testing
- [ ] 3.1 Unit tests for rate limiter (mocked Redis)
  - Acceptance: 100% coverage of rate limiter logic
- [ ] 3.2 Integration tests with real Upstash Redis
  - Acceptance: Tests pass against live Redis
- [ ] 3.3 Load testing (1000 concurrent requests)
  - Acceptance: System handles load without errors

## 4. Documentation
- [ ] 4.1 Update README.md with rate limiting details
- [ ] 4.2 Add RATE_LIMITING.md guide
- [ ] 4.3 Update environment variables docs (UPSTASH_*)
```

### **5. Define Spec Deltas**

Edit `openspec/changes/add-distributed-rate-limiting/specs/rate_limiting/spec.md`:

```markdown
# Delta for Rate Limiting

## ADDED Requirements

### Requirement: Distributed Rate Limiting
The system MUST enforce distributed rate limits using Redis-backed token bucket algorithm.

#### Scenario: User exceeds rate limit
- GIVEN a user has consumed their rate limit tokens
- WHEN they make another request within the time window
- THEN the request is rejected with 429 Too Many Requests

#### Scenario: Rate limit token refill
- GIVEN a user has consumed some tokens
- WHEN sufficient time passes for token refill
- THEN new tokens become available for consumption

### Requirement: Per-User Rate Limits
The system MUST enforce per-user rate limits of 100 requests per minute.

#### Scenario: Normal usage within limits
- GIVEN a user makes 50 requests in one minute
- WHEN they make another request
- THEN the request succeeds

### Requirement: Graceful Degradation
The system MUST fail open if Redis is unavailable (log warnings but allow requests).

#### Scenario: Redis unavailable
- GIVEN Redis connection is down
- WHEN a user makes a request
- THEN the request succeeds with warning logged
```

### **6. Validate Proposal**

```bash
openspec validate add-distributed-rate-limiting
# ✅ Proposal is valid
```

### **7. Implement (Follow tasks.md)**

```bash
# Implement each task, check off as complete
# Update tasks.md after each completion
# Test each task before moving to next
```

### **8. Archive After Completion**

```bash
# Verify all tasks complete
openspec show add-distributed-rate-limiting

# Run tests
uv run pytest tests/

# Archive
openspec archive add-distributed-rate-limiting -y

# Commit
git add .
git commit -m "feat(infrastructure): add distributed rate limiting

Implements Redis-backed distributed rate limiting using Upstash.
- Token bucket algorithm for smooth rate limiting
- Per-user limits (100 req/min)
- Per-tool configurable limits
- Graceful degradation if Redis unavailable
- Full test coverage (unit + integration + load)

Closes openspec/changes/add-distributed-rate-limiting

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"
```

---

## 🎓 Learning the OpenSpec Workflow

### **From `openspec/AGENTS.md`:**

The `openspec/AGENTS.md` file contains:
- **Spec-Driven Development** principles
- **3-Phase Workflow** (Proposal → Apply → Archive)
- **Delta Format** (ADDED/MODIFIED/REMOVED requirements)
- **Scenario Blocks** (GIVEN/WHEN/THEN format)
- **Best Practices** for writing proposals, tasks, and specs

### **Key Principles:**

1. **Spec-First**: Write specifications before code
2. **Atomic Tasks**: Each task independently testable
3. **Comprehensive Scenarios**: Every requirement needs scenario blocks
4. **Update During Implementation**: If requirements evolve, update specs/
5. **Validate Frequently**: Run `openspec validate` before commits
6. **Archive Promptly**: Don't leave completed changes unarchived

### **Integration with This Project:**

- OpenSpec proposals link to session documentation
- Research findings documented in `docs/sessions/<id>/01_RESEARCH.md`
- Implementation strategy in `docs/sessions/<id>/04_IMPLEMENTATION_STRATEGY.md`
- Known issues tracked in `docs/sessions/<id>/05_KNOWN_ISSUES.md`
- Both structures maintained in parallel (machine-readable + human context)

---

## 🚀 Next Steps

### **Immediate Actions:**

1. **Start your first change proposal:**
   ```bash
   openspec init
   # Example: "add-health-endpoints" or "fix-auth-edge-case"
   ```

2. **Read OpenSpec workflow:**
   ```bash
   cat openspec/AGENTS.md
   # Understand 3-phase workflow, delta format, scenario blocks
   ```

3. **Review project context:**
   ```bash
   cat openspec/project.md
   # Comprehensive project details are now available
   ```

### **When Working with AI Agents:**

**Prompts to use:**

1. **Feature request:**
   > "I want to add [FEATURE]. Please create an OpenSpec change proposal following the 3-phase workflow. Research the codebase first, then create comprehensive proposal.md, tasks.md, and specs/ with GIVEN/WHEN/THEN scenarios."

2. **Implementation:**
   > "Please implement the tasks in openspec/changes/[change-id]/tasks.md. Follow each task in order, test before moving to next, check off as complete. Update specs/ if requirements evolve."

3. **Bug fix:**
   > "There's a bug in [MODULE]. Research the codebase first, then create an OpenSpec proposal if it's a significant behavior change. Otherwise, fix directly and document in session notes."

4. **Review workflow:**
   > "Please explain the OpenSpec workflow from openspec/AGENTS.md and how we should work together on this project. Reference the research-first, spec-driven, forward-only progression patterns."

---

## 📚 Reference Documentation

- **`openspec/project.md`** - Comprehensive project context (370 lines)
- **`openspec/AGENTS.md`** - OpenSpec workflow instructions
- **`AGENTS.md`** (repo root) - Agent behavior, session documentation, research protocols (665 lines)
- **`CLAUDE.md`** - Claude-specific usage guide, operational loop
- **`warp.md`** - Warp terminal workflows
- **`llms-full.txt`** - FastMCP canonical contract (authoritative)

---

## ✅ Summary

**OpenSpec is now fully configured for this project:**

✅ **Structure created** - `openspec/changes/`, `openspec/specs/`  
✅ **Project context populated** - Comprehensive `openspec/project.md` (370 lines)  
✅ **AI agent guidance** - `openspec/AGENTS.md` workflow instructions  
✅ **Integration documented** - OpenSpec + session docs parallel structure  
✅ **Commands available** - `list`, `show`, `validate`, `archive`  
✅ **Examples provided** - Complete workflow demonstration  

**You're ready to start using OpenSpec for spec-driven development!** 🎉
