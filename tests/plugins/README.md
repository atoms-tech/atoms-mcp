# Atoms MCP Hybrid Test Runner

## Overview

The Atoms MCP Hybrid Test Runner combines the best of both worlds:

- **Fast execution** from pytest + FastHTTPClient (20x faster than traditional MCP client)
- **Rich features** from AtomsMCPTestRunner (progress display, reports, auth validation)

This is achieved through a pytest plugin (`atoms_pytest_plugin.py`) that hooks into pytest's lifecycle to provide AtomsMCPTestRunner features while keeping pytest's fast, reliable execution model.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Test Execution Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  test_main.py (CLI wrapper)                                 │
│       │                                                      │
│       ├─► pytest subprocess with custom flags               │
│       │                                                      │
│       └─► atoms_pytest_plugin.py (pytest plugin)            │
│             │                                                │
│             ├─► pytest_sessionstart: Auth validation        │
│             │   + Initialize progress display                │
│             │   + Setup reporters                            │
│             │                                                │
│             ├─► pytest_runtest_protocol: Track progress     │
│             │   + Update live stats                          │
│             │   + Display current test                       │
│             │                                                │
│             ├─► pytest_runtest_makereport: Capture results  │
│             │   + Record pass/fail/skip                      │
│             │   + Track performance metrics                  │
│             │                                                │
│             └─► pytest_sessionfinish: Generate reports      │
│                 + JSON report (machine-readable)             │
│                 + Markdown report (documentation)            │
│                 + Functionality Matrix (coverage)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Features Integrated

### From pytest (Fast Execution)
✅ **Fast HTTP client** - Direct HTTP calls instead of MCP SSE (20x faster)
✅ **Parallel execution** - pytest-xdist for multi-worker testing
✅ **Standard markers** - Use pytest's native markers (@pytest.mark.unit)
✅ **Native discovery** - Pytest's test discovery and collection
✅ **Better error reporting** - Pytest's detailed traceback and assertions

### From AtomsMCPTestRunner (Rich Features)
✅ **Rich progress display** - Live stats, current test, performance metrics
✅ **Multiple reporters** - JSON, Markdown, Console, FunctionalityMatrix
✅ **Auth validation** - Validate OAuth before running tests
✅ **Performance tracking** - Tests/sec, avg duration, cache hit rate
✅ **Category-based execution** - Filter tests by category
✅ **Cache management** - Skip unchanged tests

## Usage

### Basic Usage

Run tests with standard pytest:

```bash
pytest tests/unit/ -v
```

### With Rich Progress Display

```bash
pytest tests/unit/ -v --enable-rich-progress
```

This shows:
- Live pass/fail/skip/cache counters
- Current test name and tool
- Worker information (for parallel execution)
- Performance metrics (tests/sec, avg duration, cache hit rate)

### With Comprehensive Reports

```bash
pytest tests/unit/ -v --enable-reports
```

This generates:
- `tests/reports/test_results.json` - Machine-readable results
- `tests/reports/test_results.md` - Human-readable documentation
- `tests/reports/functionality_matrix.md` - Feature coverage matrix

### With Auth Validation

```bash
pytest tests/unit/ -v --validate-auth
```

Validates OAuth authentication before running tests. Useful for catching auth issues early.

### Full Featured Run

```bash
pytest tests/unit/ -v \
  --enable-rich-progress \
  --enable-reports \
  --validate-auth \
  -n 4  # 4 parallel workers
```

### Via test_main.py Wrapper

The `test_main.py` script provides a convenient CLI wrapper:

```bash
# Basic run
python tests/test_main.py

# With all features
python tests/test_main.py \
  --enable-rich-progress \
  --enable-reports \
  --validate-auth \
  --workers 4

# Filter by category
python tests/test_main.py \
  --categories entity query \
  --workers 4

# Verbose output
python tests/test_main.py \
  --verbose \
  --enable-rich-progress

# Clear caches
python tests/test_main.py --clear-cache
python tests/test_main.py --clear-oauth
```

## CLI Options

### Atoms MCP Options (via plugin)

| Option | Description |
|--------|-------------|
| `--enable-rich-progress` | Enable beautiful progress display with live stats |
| `--enable-reports` | Generate JSON, Markdown, and Matrix reports |
| `--validate-auth` | Validate OAuth before running tests |
| `--continue-on-auth-fail` | Continue even if auth validation fails |

### test_main.py Options

| Option | Description |
|--------|-------------|
| `--categories CATS [CATS ...]` | Test categories to run (e.g., core entity query) |
| `--coverage-level LEVEL` | Test coverage level (minimal/standard/comprehensive) |
| `--no-cache` | Disable test caching |
| `--clear-cache` | Clear test cache |
| `--clear-oauth` | Clear OAuth token cache |
| `--sequential` | Run tests sequentially (no parallel) |
| `--workers N` | Number of parallel workers |
| `--verbose` | Show verbose logging |

### Standard pytest Options

All standard pytest options work:

```bash
pytest tests/unit/ \
  -v \                    # Verbose
  -s \                    # Show print statements
  -k "entity" \           # Filter by keyword
  -m "unit" \             # Filter by marker
  -n 4 \                  # 4 parallel workers (pytest-xdist)
  --maxfail=5 \           # Stop after 5 failures
  --tb=short              # Short traceback
```

## Reports

### JSON Report (`test_results.json`)

Machine-readable format for CI/CD integration:

```json
{
  "generated_at": "2025-10-09T01:06:06.792632",
  "metadata": {
    "endpoint": "https://mcp.atoms.tech/api/mcp",
    "auth_status": "validated",
    "duration_seconds": 45.2,
    "pytest_version": "8.4.2"
  },
  "summary": {
    "total": 136,
    "passed": 120,
    "failed": 5,
    "skipped": 11,
    "cached": 0,
    "pass_rate": 96.0,
    "avg_duration_ms": 250.5
  },
  "results": [...]
}
```

### Markdown Report (`test_results.md`)

Human-readable documentation:

```markdown
# Atoms MCP Test Report

**Generated**: 2025-10-09T01:06:06.792632
**Endpoint**: https://mcp.atoms.tech/api/mcp
**Auth**: validated

## Summary
- Total: 136
- Passed: ✅ 120
- Failed: ❌ 5
- Skipped: ⏭️  11
- Pass Rate: 96.0%

## Results
| Tool | Test | Status | Duration |
|------|------|--------|----------|
| entity_tool | test_create_organization | ✅ Pass | 245.32ms |
| entity_tool | test_list_projects | ✅ Pass | 189.21ms |
...
```

### Functionality Matrix (`functionality_matrix.md`)

Comprehensive feature coverage:

```markdown
# ATOMS MCP FUNCTIONALITY MATRIX

## workspace_tool
**Workspace context management for organizing work**

| Operation | Status | Time (ms) | User Story |
|-----------|--------|-----------|------------|
| list_workspaces | ✅ Pass | 150 | see all my workspaces |
| get_context | ✅ Pass | 80 | know my current context |
| set_context | ✅ Pass | 120 | switch workspaces |
...
```

## Integration with Existing Tests

The plugin automatically works with existing pytest tests. No changes needed!

```python
# Your existing test
@pytest.mark.unit
async def test_entity_creation(fast_http_client):
    result = await fast_http_client.call_tool("create_entity", {
        "name": "Test Entity",
        "type": "document"
    })
    assert result["success"] == True
```

The plugin will:
- Track this test in the progress display
- Record results for reporting
- Calculate performance metrics
- Include in JSON/Markdown/Matrix reports

## Performance Comparison

| Feature | AtomsMCPTestRunner | Hybrid Runner |
|---------|-------------------|---------------|
| Test execution | Custom runner | pytest (faster) |
| HTTP client | MCP SSE | Direct HTTP POST |
| Parallel execution | Custom pool | pytest-xdist |
| Progress display | ✅ | ✅ (via plugin) |
| Reports | ✅ | ✅ (via plugin) |
| Auth validation | ✅ | ✅ (via plugin) |
| Cache management | ✅ | pytest cache |
| **Speed** | 1x | **20x faster** |

## File Structure

```
tests/
├── plugins/
│   ├── __init__.py                 # Plugin package
│   ├── atoms_pytest_plugin.py      # Main plugin implementation
│   └── README.md                   # This file
├── conftest.py                     # Register plugin + fixtures
├── test_main.py                    # CLI wrapper
└── reports/                        # Generated reports
    ├── test_results.json
    ├── test_results.md
    └── functionality_matrix.md
```

## How It Works

### Plugin Registration

The plugin is registered in `conftest.py`:

```python
pytest_plugins = ["pytest_asyncio", "tests.plugins.atoms_pytest_plugin"]
```

### Pytest Hooks

The plugin uses pytest's hook system:

1. **pytest_configure** - Add custom CLI options
2. **pytest_sessionstart** - Initialize progress display, validate auth
3. **pytest_runtest_protocol** - Track progress during test execution
4. **pytest_runtest_makereport** - Capture test results
5. **pytest_sessionfinish** - Generate reports

### Progress Display

Uses Rich library for terminal UI:

- Spinner animation
- Progress bar with time estimates
- Live stats (pass/fail/skip/cache)
- Current test information
- Performance metrics

### Reporters

Reuses `tests/framework/reporters.py`:

- `ConsoleReporter` - Terminal output
- `JSONReporter` - Machine-readable
- `MarkdownReporter` - Documentation
- `FunctionalityMatrixReporter` - Coverage matrix

## Troubleshooting

### Progress display not showing

Make sure Rich is installed:

```bash
pip install rich
```

### Reports not being generated

Check that `--enable-reports` flag is passed:

```bash
pytest tests/unit/ --enable-reports
```

### Auth validation failing

Clear OAuth cache and re-authenticate:

```bash
python tests/test_main.py --clear-oauth
```

### Parallel execution not working

Install pytest-xdist:

```bash
pip install pytest-xdist
```

## Future Enhancements

Potential improvements:

- [ ] Real-time streaming progress to web dashboard
- [ ] Integration with CI/CD systems (GitHub Actions, GitLab CI)
- [ ] Historical trend tracking (pass rate over time)
- [ ] Automatic test categorization based on code analysis
- [ ] Intelligent test selection based on code changes
- [ ] Performance regression detection
- [ ] Test coverage visualization

## Contributing

To add new features to the plugin:

1. Edit `tests/plugins/atoms_pytest_plugin.py`
2. Add new pytest hooks as needed
3. Update CLI options in `pytest_addoption()`
4. Document in this README

## License

MIT License - see LICENSE file for details.
