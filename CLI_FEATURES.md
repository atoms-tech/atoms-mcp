# Atoms MCP CLI - Complete Feature Guide

## 🚀 Overview

The Atoms MCP CLI provides a modern, enterprise-grade command-line interface with rich visual output, progress tracking, and comprehensive dependency management.

## 📋 Available Commands

### 1. `atoms run` - Start the Server
Start the FastMCP server with optional configuration.

```bash
# Default (localhost:8000)
atoms run

# Custom host and port
atoms run --host 0.0.0.0 --port 8001

# Debug mode
atoms run --debug
```

**Features:**
- ✅ Configurable host and port
- ✅ Debug mode support
- ✅ Clear startup messages
- ✅ Automatic environment loading

---

### 2. `atoms health` - Check Server Status
Verify that the server is running and responsive.

```bash
atoms health
```

**Output:**
```
✅ Server is healthy
```

**Features:**
- ✅ Fast connectivity check (5s timeout)
- ✅ HTTP health endpoint detection
- ✅ Clear pass/fail status

---

### 3. `atoms version` - Show Version Info
Display version and product information.

```bash
atoms version
```

**Output:**
```
Atoms MCP Server v0.1.0
FastMCP-based consolidated MCP server
```

---

### 4. `atoms update` - Rich Dependency Management

The flagship command with enterprise-grade visualization, progress bars, and ASCII diagrams.

#### Usage Examples

```bash
# Preview all updates (dry-run)
atoms update --all --dry-run

# Update all dependencies interactively
atoms update --all

# Update production dependencies only
atoms update --deps

# Update development dependencies only
atoms update --dev

# Check for outdated packages
atoms update --outdated

# Verbose output
atoms update -v
atoms update --verbose
```

#### Features

**Visual Elements:**
```
╔═══════════════════════════════════════════════════════════════╗
║     📦 ATOMS MCP DEPENDENCY UPDATE MANAGER 🚀                 ║
║                                                               ║
║  Fast, Safe, Intelligent Dependency Management               ║
║  Powered by UV Package Manager                               ║
╚═══════════════════════════════════════════════════════════════╝
```

**Dependency Tree Diagram:**
```
📦 atoms-mcp (v0.1.0)
├── 🔵 fastmcp (≥2.12.2)
│   ├── pydantic (≥2.11.7)
│   └── starlette
├── 🟢 supabase (≥2.5.0)
│   ├── httpx (≥0.28.1)
│   └── python-dateutil
└── [... more dependencies]
```

**Dependency Matrix:**
```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Production Packages ┃ Dev Packages        ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ ✓ fastmcp           │ ✓ pytest            │
│ ✓ supabase          │ ✓ black             │
│ ✓ pydantic          │ ✓ ruff              │
│ [... more]          │ [... more]          │
└─────────────────────┴─────────────────────┘
```

**Progress Visualization:**
```
⠙ Analyzing dependencies... ████████████████████░░░░ 85.3% Complete
```

**Safety Checklist:**
```
╔═══════════════════════════════════════════════════════════════╗
║ ✓ Backup of pyproject.toml created                          ║
║ ✓ Compatibility checks completed                            ║
║ ✓ Test suite ready                                          ║
║ ✓ Lock file backup prepared                                ║
║ ✓ Network connectivity verified                            ║
╚═══════════════════════════════════════════════════════════════╝
```

**Update Strategy Tree:**
```
📋 UPDATE STRATEGY
├── Production Dependencies
│   ├── ✓ Update core packages
│   ├── ✓ Verify compatibility
│   └── ✓ Lock versions
└── Development Dependencies
    ├── ✓ Update dev tools
    ├── ✓ Check test compatibility
    └── ✓ Update lock file
```

**Completion Summary:**
```
╔═══════════════════════════════════════════════════════════════╗
║ ✓ Update Process Completed Successfully                      ║
║                                                               ║
║ 📊 Statistics:                                                ║
║   • Packages Processed: 47                                    ║
║   • Duration: 12.34 seconds                                  ║
║   • Success Rate: 100%                                       ║
║   • Lock File: Updated ✓                                     ║
║                                                               ║
║ ⏭️  Next Steps:                                                ║
║   1. Run: pytest - Verify tests pass                         ║
║   2. Run: atoms run - Start your server                      ║
║   3. Monitor: atoms health - Check health                    ║
╚═══════════════════════════════════════════════════════════════╝
```

#### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--all` | Update all dependencies | `atoms update --all` |
| `--deps` | Production deps only | `atoms update --deps` |
| `--dev` | Development deps only | `atoms update --dev` |
| `--check` | Preview without installing | `atoms update --check` |
| `--outdated` | Show outdated packages | `atoms update --outdated` |
| `--dry-run` | Simulate without changes | `atoms update --all --dry-run` |
| `-v, --verbose` | Verbose output | `atoms update -v` |
| `--help` | Show help | `atoms update --help` |

#### Error Handling

**Rich Error Panel:**
```
╔═══════════════════════════════════════════════════════════════╗
║ ❌ UPDATE FAILED                                              ║
║                                                               ║
║ Error:                                                        ║
║ Failed to load pyproject.toml                                ║
║                                                               ║
║ Recovery Steps:                                              ║
║ Ensure pyproject.toml exists in project root                ║
║                                                               ║
║ Support:                                                      ║
║ Run: atoms health to diagnose your system                    ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 🎨 CLI Architecture

### Core Modules

**`cli.py` (Main CLI)**
- Typer application setup
- Command routing
- Basic commands (run, health, version)
- Update command orchestration

**`cli_update.py` (Rich Visualization)**
- `DependencyAnalyzer`: Parse pyproject.toml
- `PackageInfo`: Package metadata
- Visual functions:
  - `print_header()` - Formatted header
  - `print_ascii_diagram()` - Dependency tree
  - `show_update_plan()` - Update planning
  - `show_package_matrix()` - Dependency table
  - `show_update_strategy()` - Strategy tree
  - `show_safety_checklist()` - Pre-update checks
  - `show_completion_summary()` - Results
  - `show_error_state()` - Error reporting
  - `execute_update_with_visualization()` - Full flow

### Dependencies

**Required:**
- `typer` - CLI framework
- `rich` - Advanced terminal formatting (auto-installs)

**Optional:**
- Falls back to basic text output if Rich not available

---

## 📊 Visualization Features

### Rich Library Integration

✅ **Progress Bars**
- Real-time update progress
- ETA calculation
- Percentage completion
- Smooth animations

✅ **Colored Output**
- Errors: Red 🔴
- Warnings: Yellow 🟡
- Success: Green 🟢
- Information: Cyan 🔵
- Magenta for headers: Magenta 🟣

✅ **Structured Panels**
- Bordered content boxes
- Title formatting
- Padding and alignment
- Color-coded sections

✅ **ASCII Diagrams**
- Dependency tree with visual hierarchy
- Box drawing for tables
- Tree structures for strategies
- Clear visual separation

✅ **Tables**
- Formatted columns
- Aligned content
- Custom styling
- Summary statistics

---

## 🔄 Update Workflow

### Step-by-Step Flow

1. **Load Dependencies**
   - Parse `pyproject.toml`
   - Separate prod/dev deps
   - Validate format

2. **Show Summary**
   - Display current versions
   - Show lock file stats
   - List dependency counts

3. **Plan Updates**
   - Show what will be updated
   - Display dry-run preview
   - List safety checks

4. **Execute**
   - Run with progress visualization
   - Update packages
   - Refresh lock file

5. **Report Results**
   - Show statistics
   - List updated packages
   - Provide next steps

---

## 💡 Usage Patterns

### Daily Development
```bash
# Check for updates
atoms update --outdated

# Preview changes
atoms update --all --dry-run

# Apply updates
atoms update --all

# Run tests
pytest

# Start server
atoms run --debug
```

### CI/CD Pipeline
```bash
# Automated updates in CI
atoms update --all --dry-run
atoms update --all

# Verify
atoms health
pytest
```

### Production Updates
```bash
# Safe preview first
atoms update --all --dry-run

# Review changes
git diff uv.lock

# Apply in controlled environment
atoms update --all
pytest
atoms health
```

---

## 🛠️ Configuration

### Environment Variables

Set in `.env` file:

```bash
# Server
ATOMS_FASTMCP_HOST=0.0.0.0
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_DEBUG=false

# Database
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

### Rich Customization

The Rich library respects terminal capabilities:
- Auto-detects terminal color support
- Disables colors on non-TTY output
- Adapts to terminal width
- Works in CI/CD environments

---

## 📈 Advanced Features

### Dry-Run Safety
```bash
atoms update --all --dry-run
# Shows what WOULD be updated
# Makes NO changes to your system
# Use to preview before committing
```

### Verbose Logging
```bash
atoms update --all -v
# Shows detailed operation logs
# Useful for debugging issues
# Full dependency resolution details
```

### Dependency Analysis
```bash
atoms update --outdated
# Lists outdated packages
# Shows available versions
# Table format with color coding
```

---

## 🎯 Best Practices

1. **Always Dry-Run First**
   ```bash
   atoms update --all --dry-run
   git diff --stat uv.lock
   atoms update --all
   ```

2. **Separate Prod/Dev Updates**
   ```bash
   atoms update --deps  # Core deps
   atoms update --dev   # Dev tools
   ```

3. **Verify After Update**
   ```bash
   atoms health    # Check server
   pytest          # Run tests
   pytest --cov    # Coverage report
   ```

4. **Use Verbose on Errors**
   ```bash
   atoms update --all -v  # Full debug output
   ```

---

## 🚀 Future Enhancements

Possible future additions:
- Package update recommendations
- Dependency conflict resolution
- Security vulnerability scanning
- Performance impact analysis
- Custom update scheduling
- Integration with CI/CD platforms

---

## 📞 Support

For issues:
1. Run `atoms health` to diagnose
2. Check logs: `atoms run --debug`
3. Dry-run first: `atoms update --all --dry-run`
4. Review changes: `git diff`

---

**Status**: ✅ Production Ready  
**Version**: 0.1.0  
**Last Updated**: November 13, 2024  
