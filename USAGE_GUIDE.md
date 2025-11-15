# Atoms MCP Test CLI - Usage Guide

## Quick Reference

### Unit Tests (Local - Default)
```bash
atoms test                    # Unit tests only
atoms test:unit              # Unit tests (shorthand)
atoms test:cov               # Coverage report
atoms test -v                # Verbose output
```

### Integration Tests (Dev - Default)
```bash
atoms test:int               # Auto-targets: mcpdev.atoms.tech
atoms test:int --env local   # Override: use local server
atoms test:int --env prod    # Override: use production
```

### E2E Tests (Dev - Default)
```bash
atoms test:e2e               # Auto-targets: mcpdev.atoms.tech
atoms test:e2e --env local   # Override: use local server
atoms test:e2e --env prod    # Override: use production
```

## Common Commands

### Development (No Deployment Needed)
```bash
# Run unit tests while developing
atoms test

# Run unit tests with coverage report
atoms test:cov

# Run unit tests in verbose mode
atoms test -v
```

### Testing Against Deployment
```bash
# Test integration against dev deployment
atoms test:int

# Test E2E against dev deployment
atoms test:e2e

# Test both with verbose output
atoms test:int -v
atoms test:e2e -v
```

### Production Validation
```bash
# Test E2E against production
atoms test:e2e --env prod

# Test integration against production
atoms test:int --env prod
```

### Troubleshooting
```bash
# Test locally when deployment is unreachable
atoms test:int --env local
atoms test:e2e --env local

# Run specific tests only
atoms test -k "test_name"
atoms test -m "story"  # Run story-marked tests
```

## Environment Targets

| Command | Default Target | Type |
|---------|----------------|------|
| `atoms test` | Local | Unit tests |
| `atoms test:unit` | Local | Unit tests |
| `atoms test:cov` | Local | Unit tests (with coverage) |
| `atoms test:int` | Dev (mcpdev.atoms.tech) | Integration |
| `atoms test:e2e` | Dev (mcpdev.atoms.tech) | E2E |

## Override Options

Use `--env` flag to change the target:

```bash
--env local    # Use local server (http://127.0.0.1:8000)
--env dev      # Use dev deployment (https://mcpdev.atoms.tech)
--env prod     # Use production (https://mcp.atoms.tech)
```

Examples:
```bash
atoms test:int --env local   # Integration tests on local
atoms test:int --env prod    # Integration tests on production
atoms test:e2e --env prod    # E2E tests on production
```

## Environment Details

### Local (http://127.0.0.1:8000)
- **Timeout**: 10 seconds
- **Retries**: 3
- **Best For**: Development iteration
- **Database**: Local Supabase
- **Default For**: Unit tests

### Dev (https://mcpdev.atoms.tech)
- **Timeout**: 30 seconds (integration), 60 seconds (E2E)
- **Retries**: 5
- **Best For**: Testing deployed instance
- **Database**: Live Supabase
- **Default For**: Integration & E2E tests

### Prod (https://mcp.atoms.tech)
- **Timeout**: 60 seconds
- **Retries**: 5
- **Best For**: Production validation
- **Database**: Live Supabase
- **Default For**: Manual override only

## Common Mistakes

❌ **Wrong**: `atoms test local`  
✅ **Correct**: `atoms test --env local`

❌ **Wrong**: `atoms test dev`  
✅ **Correct**: `atoms test:int` (auto-targets dev)

❌ **Wrong**: `atoms test prod`  
✅ **Correct**: `atoms test:e2e --env prod`

The environment is specified with the `--env` flag, not as a positional argument.

## Workflow Examples

### Scenario 1: Daily Development
```bash
# Write code, run unit tests locally
atoms test

# Add a feature, test with coverage
atoms test:cov

# Check specific tests
atoms test -k "entity"
```

### Scenario 2: Integration Testing
```bash
# After feature complete, test against dev deployment
atoms test:int

# If failures, debug locally first
atoms test:int --env local

# Once passing locally, re-test on dev
atoms test:int
```

### Scenario 3: Release Validation
```bash
# Comprehensive E2E testing on production before release
atoms test:e2e --env prod

# If issues, test locally to isolate
atoms test:e2e --env local

# Once resolved, final production validation
atoms test:e2e --env prod
```

## CLI Help

Get help for any command:

```bash
atoms test --help           # Main test command help
atoms test:int --help       # Integration test help
atoms test:e2e --help       # E2E test help
atoms test:unit --help      # Unit test help
atoms test:cov --help       # Coverage help
```

## Environment Variables

The CLI sets these automatically (no manual configuration needed):

```
MCP_BASE_URL              # Base URL for MCP server
MCP_HEALTH_URL           # Health check endpoint
MCP_TIMEOUT              # Request timeout in seconds
MCP_RETRY_ATTEMPTS       # Number of retry attempts
MCP_INTEGRATION_BASE_URL # Used by integration fixtures
MCP_E2E_BASE_URL         # Used by E2E fixtures
```

## Health Checks

Verify each environment is responding:

```bash
# Local
curl http://127.0.0.1:8000/health

# Dev (mcpdev.atoms.tech)
curl https://mcpdev.atoms.tech/health

# Production (mcp.atoms.tech)
curl https://mcp.atoms.tech/health
```

## Verbose Output

Add `-v` flag to see more details:

```bash
atoms test -v              # Verbose unit tests
atoms test:int -v          # Verbose integration tests
atoms test:e2e -v          # Verbose E2E tests
```

## Coverage Report

Generate HTML coverage report:

```bash
atoms test:cov
# Opens: htmlcov/index.html
```

## Running Specific Tests

Use `-k` (keyword) to run specific tests:

```bash
atoms test -k "test_auth"           # Run tests matching "test_auth"
atoms test -k "entity and create"   # Match multiple keywords
atoms test -k "not slow"            # Exclude slow tests
```

Use `-m` (marker) to run marked tests:

```bash
atoms test -m "story"               # Run tests marked with @pytest.mark.story
atoms test -m "not performance"     # Exclude performance tests
```

## Status Indicators

The CLI shows which environment it's using:

```
🎯 Test Environment: Local Development
📝 Description: Local development with local Supabase
🔗 MCP URL: http://127.0.0.1:8000/api/mcp
⏱️  Timeout: 10s
🔄 Retries: 3
```

This confirms you're testing against the correct target.

## Troubleshooting

### "Connection refused" errors
Check which environment is being used (CLI prints it). If testing dev:
- Verify deployment is running: `curl https://mcpdev.atoms.tech/health`
- Override to local: `atoms test:int --env local`

### Timeout errors
Each environment has appropriate timeouts:
- Local: 10s (should be fast)
- Dev: 30s (network latency)
- Prod: 60s (full workflows)

If you need longer, you can test locally first: `atoms test:int --env local`

### Wrong environment being used
Check `atoms test:int --help` to see defaults. Remember:
- Unit tests ALWAYS use local
- Integration/E2E default to dev (override with `--env`)

## Summary

1. **Default behavior** - tests auto-select correct environment
2. **No configuration needed** - just run a command
3. **Easy overrides** - use `--env` flag to change targets
4. **Clear feedback** - CLI shows which environment it's using

That's it! Happy testing! 🚀
