# Atoms CLI Commands Reference

**Like npm scripts, but for your MCP server!**

> This document provides a comprehensive guide to all available CLI commands. Think of these like `npm run` scripts - each command is a powerful shortcut for common development workflows.

---

## 📋 Quick Command List

```bash
# Server Management
atoms run                 # Start server
atoms dev                 # Dev mode (auto-reload)
atoms health              # Check health
atoms version             # Show version

# Testing (like npm test)
atoms test                # Run all tests
atoms test:unit           # Unit tests only
atoms test:int            # Integration tests
atoms test:e2e            # End-to-end tests
atoms test:cov            # Tests with coverage
atoms test:story          # Tests by user story

# Code Quality (like npm run lint/format)
atoms lint                # Check code
atoms format              # Auto-format
atoms type-check          # Type checking
atoms check               # Run all checks

# Dependencies (like npm update)
atoms update              # Update deps
atoms deps                # Analyze deps

# Build & Deployment
atoms build               # Production build
atoms clean               # Clean artifacts

# Utilities
atoms docs                # Documentation
atoms logs                # View logs
atoms info                # Project info
```

---

## 🚀 Server Commands

### `atoms run`
**Start the Atoms MCP Server**

```bash
atoms run                           # Default: 0.0.0.0:8000
atoms run --host localhost         # Custom host
atoms run --port 8001              # Custom port
atoms run --debug                  # Debug mode
atoms run --port 8001 --debug      # Both options
```

**What it does:**
- Starts the FastMCP server
- Binds to specified host/port
- Enables debug logging if requested
- Provides access to all MCP tools

**When to use:**
- Starting server for development
- Testing client connections
- Running in production (recommended: use reverse proxy)

---

### `atoms dev`
**Development Mode with Auto-Reload**

```bash
atoms dev                    # Default port 8000
atoms dev --port 8001        # Custom port
```

**Features:**
- ✅ Auto-reloads on file changes
- ✅ Detailed error messages
- ✅ All debug logging enabled
- ✅ Perfect for development

**What's different from `atoms run`:**
- Uses uvicorn with reload
- Shows full tracebacks
- Watches filesystem

**When to use:**
- Active development
- Debugging issues
- Testing changes in real-time

---

### `atoms health`
**Check Server Health**

```bash
atoms health
```

**Output:**
```
✅ Server is healthy
```

**What it checks:**
- Server is running
- Health endpoint responds
- Status code is 200

**When to use:**
- Before running tests
- Verifying server started
- Monitoring in production

---

### `atoms version`
**Show Version Information**

```bash
atoms version
```

**Output:**
```
Atoms MCP Server v0.1.0
FastMCP-based consolidated MCP server
```

---

## 🧪 Testing Commands

### `atoms test`
**Run Full Test Suite**

```bash
atoms test                         # Run all
atoms test -v                      # Verbose
atoms test --cov                   # With coverage
atoms test -m unit                 # By marker
atoms test -k auth                 # By keyword
atoms test --cov -v                # Coverage + verbose
```

**Examples:**
```bash
# Run everything
atoms test

# Run with detailed output
atoms test -v

# Run only auth tests
atoms test -k auth

# Run only unit tests
atoms test -m unit

# Generate HTML coverage report
atoms test --cov
```

**Options:**
| Option | Meaning | Example |
|--------|---------|---------|
| `-v, --verbose` | Detailed output | `atoms test -v` |
| `--cov` | Generate coverage | `atoms test --cov` |
| `-m, --marker` | Filter by marker | `atoms test -m unit` |
| `-k, --keyword` | Filter by keyword | `atoms test -k auth` |

---

### `atoms test:unit`
**Run Unit Tests Only (Fast)**

```bash
atoms test:unit           # Default
atoms test:unit -v        # Verbose
```

**What's tested:**
- Core logic with mocks
- No external services
- No database calls
- Fastest (< 30 seconds)

**When to use:**
- Quick validation
- Before commits
- CI/CD pipeline

---

### `atoms test:int`
**Run Integration Tests**

```bash
atoms test:int           # Default
atoms test:int -v        # Verbose
```

**What's tested:**
- HTTP API calls
- Database operations
- External service mocks
- Moderate speed (~2 minutes)

**When to use:**
- Before merges
- After infrastructure changes
- Weekly runs

---

### `atoms test:e2e`
**Run End-to-End Tests**

```bash
atoms test:e2e           # Default
atoms test:e2e -v        # Verbose
```

**What's tested:**
- Full system flows
- Real workflows
- All components together
- Slowest (~5 minutes)

**When to use:**
- Before releases
- Major feature testing
- Pre-deployment verification

---

### `atoms test:cov`
**Run Tests with Coverage Report**

```bash
atoms test:cov
```

**Output:**
```
htmlcov/index.html - Interactive coverage report
```

**What it generates:**
- HTML coverage report
- Terminal summary
- Coverage metrics
- Missing line identification

**When to use:**
- Measuring test coverage
- Identifying gaps
- Improving code quality

---

### `atoms test:story`
**Run Tests by User Story Mapping**

```bash
atoms test:story                    # All stories
atoms test:story -e Security        # Epic filter
atoms test:story -e Organization    # Another epic
```

**Available Epics:**
- Organization
- Project
- Document
- Requirements
- Test Case
- Workspace
- Relationships
- Search
- Workflow
- Data
- Security

**When to use:**
- Testing specific features
- Epic-based validation
- User story completion

---

## 🔍 Code Quality Commands

### `atoms lint`
**Check Code with Ruff**

```bash
atoms lint
```

**What it checks:**
- Syntax errors
- Unused imports
- Naming conventions
- Code complexity

**When to use:**
- Before commits
- In CI/CD
- Regular code reviews

---

### `atoms format`
**Auto-Format Code with Black**

```bash
atoms format
```

**What it does:**
- Formats to Black standard
- Line length: 100 chars
- Sorts imports with isort
- Updates all files in-place

**When to use:**
- Before commits
- Start of workday
- After merges

---

### `atoms type-check`
**Type Check with mypy**

```bash
atoms type-check
```

**What it checks:**
- Type annotations
- Type consistency
- Missing return types
- Generic types

**When to use:**
- Code reviews
- Before merges
- Building confidence

---

### `atoms check`
**Run All Quality Checks**

```bash
atoms check
```

**Runs in order:**
1. Format (black)
2. Lint (ruff)
3. Type-check (mypy)

**When to use:**
- Pre-commit hook
- Before creating PR
- Final verification

---

## 📦 Dependency Commands

### `atoms update`
**Update Dependencies (Like npm update)**

```bash
atoms update                      # Interactive
atoms update --all                # All deps
atoms update --deps               # Production only
atoms update --dev                # Dev only
atoms update --all --dry-run      # Preview
atoms update -v                   # Verbose
```

**Examples:**
```bash
# Preview what would be updated
atoms update --all --dry-run

# Update production dependencies
atoms update --deps

# Update dev dependencies
atoms update --dev

# Update everything with verbose output
atoms update --all -v
```

**What it does:**
- Updates pyproject.toml
- Updates uv.lock
- Shows progress bars
- Displays dependency tree
- Generates safety checklist

---

### `atoms deps`
**Analyze Project Dependencies**

```bash
atoms deps
```

**Output:**
```
📦 Analyzing dependencies...

📊 Dependency Summary:
  Production: 25 packages
  Development: 18 packages
  Total: 43 packages

🔒 Lock File:
  Lines: 1,250
  Size: 2.45MB
```

**When to use:**
- Understanding project scope
- Identifying dependency bloat
- Tracking package growth

---

## 🏗️ Build & Deployment Commands

### `atoms build`
**Build for Production**

```bash
atoms build
```

**Steps:**
1. Run code formatting
2. Run linting
3. Run full test suite
4. Build distribution packages
5. Generate documentation

**When to use:**
- Release preparation
- Pre-deployment
- CI/CD pipeline

---

### `atoms clean`
**Clean Cache and Build Artifacts**

```bash
atoms clean
```

**Removes:**
- `__pycache__` directories
- `.pyc` files
- `.coverage` data
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`
- `build/` and `dist/` directories
- `htmlcov/`
- `*.egg-info`

**When to use:**
- Fresh start needed
- Disk space cleanup
- Before building
- After major refactors

---

## 📚 Utility Commands

### `atoms docs`
**View Documentation**

```bash
atoms docs
```

**Shows:**
- Available documentation files
- User story mappings
- CLI reference
- Generated documentation

---

### `atoms logs`
**Tail Server Logs**

```bash
atoms logs                 # Last 50 lines
atoms logs -n 100          # Last 100 lines
atoms logs -f              # Follow in real-time
```

**When to use:**
- Debugging issues
- Monitoring server
- Tracking errors

---

### `atoms info`
**Show Project Information**

```bash
atoms info
```

**Displays:**
```
ℹ️  Project Information:

📦 Project:
  Name: Atoms MCP
  Version: 0.1.0

🐍 Python: 3.12.11

📚 Dependencies:
  Production: 25
  Development: 18

🌿 Git: working-deployment
```

**When to use:**
- Setup verification
- CI environment check
- Quick project overview

---

## 💡 Workflow Examples

### Daily Development Workflow

```bash
# Start your day
atoms dev --port 8001           # Start in dev mode

# In another terminal
atoms lint                      # Check code
atoms format                    # Auto-format
atoms test:unit -v              # Quick tests

# Before committing
atoms check                     # All checks
atoms test --cov                # Full coverage

# Clean up
atoms clean                     # Remove artifacts
```

### Pre-Release Workflow

```bash
# Prepare release
atoms update --all --dry-run    # Preview updates
atoms update --all              # Apply updates
atoms build                     # Full build
atoms clean                     # Clean artifacts

# Verify
atoms health                    # Check health
atoms info                      # Project info
```

### CI/CD Pipeline

```bash
# In continuous integration
atoms lint                      # Code quality
atoms format                    # Auto-format
atoms test --cov                # Full coverage
atoms build                     # Production build
```

### Testing Strategy

```bash
# Quick validation (pre-commit)
atoms test:unit                 # Fast: 30s

# Before merge request
atoms test --cov                # Medium: 2min

# Before release
atoms test:e2e                  # Full: 5min
atoms test:story                # Story validation
```

---

## 📊 Command Categories Summary

| Category | Commands | Purpose |
|----------|----------|---------|
| **Server** | `run`, `dev`, `health`, `version` | Running & monitoring |
| **Testing** | `test`, `test:unit`, `test:int`, `test:e2e`, `test:cov`, `test:story` | Validation |
| **Quality** | `lint`, `format`, `type-check`, `check` | Code standards |
| **Deps** | `update`, `deps` | Dependency management |
| **Build** | `build`, `clean` | Production readiness |
| **Utils** | `docs`, `logs`, `info` | Utilities |

---

## ⚡ Quick Tips

1. **Before committing:** `atoms check`
2. **Before merging:** `atoms test --cov`
3. **Before releasing:** `atoms build`
4. **Quick validation:** `atoms test:unit`
5. **Full validation:** `atoms test:e2e`
6. **Coverage check:** `atoms test:cov`
7. **Project status:** `atoms info`
8. **Epic testing:** `atoms test:story -e Security`

---

## 🎯 Alias Suggestions

For frequently used commands, add shell aliases:

```bash
# ~/.zshrc or ~/.bashrc
alias amock='atoms test:unit'           # Quick unit tests
alias atest='atoms test --cov'          # Full tests with coverage
alias acheck='atoms check'              # All checks
alias afmt='atoms format && atoms lint' # Format then lint
alias adev='atoms dev'                  # Development mode
alias ainfo='atoms info'                # Quick info
```

---

**Status**: ✅ Production Ready  
**Commands**: 20+ comprehensive commands  
**Compatibility**: Like npm run scripts  
**Latest Update**: November 13, 2024
