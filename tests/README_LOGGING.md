# Test Logging Guide

## Quick Start

### Running Tests with Clean Output (Default)
```bash
python tests/test_comprehensive_new.py
```

This will show:
- ✅ Progress bars and visual indicators
- ✅ Natural language status messages
- ✅ Only errors and critical issues
- ❌ No verbose INFO logs

### Running Tests with Verbose Logging (Debugging)
```bash
python tests/test_comprehensive_new.py --verbose
```

This will show:
- ✅ All INFO, DEBUG, WARNING logs
- ✅ Detailed HTTP requests
- ✅ OAuth flow details
- ✅ Internal library logs

## For Test Developers

### Using the Logging Utilities

```python
from tests.framework.test_logging_setup import (
    configure_test_logging,
    suppress_deprecation_warnings,
    QuietLogger,
    get_test_logger,
)

# Configure logging at start of test suite
configure_test_logging(verbose=False)  # Quiet mode
suppress_deprecation_warnings()

# Get a logger for your test module
logger = get_test_logger(__name__, verbose=False)

# Temporarily suppress logs for noisy operations
with QuietLogger():
    await oauth_flow()
    await playwright_automation()
```

### Writing Clean Test Output

**DO** ✅:
```python
# Use natural language and emojis
print("✅ Authentication complete")
print("🔌 Creating client pool...")
print("📋 Running CORE tests")

# Use progress bars (rich library)
from rich.progress import Progress
with Progress() as progress:
    task = progress.add_task("Running tests", total=100)
    # ...
```

**DON'T** ❌:
```python
# Don't use logger.info() for progress updates
logger.info("Running test 1/100")
logger.info("Running test 2/100")

# Don't print raw data structures
print(f"Result: {result}")  # Bad if result is huge dict

# Don't use print() for errors
print(f"Error: {e}")  # Use logger.error() instead
```

### Logging Levels

| Level | When to Use | Visible in Quiet Mode? |
|-------|-------------|----------------------|
| `logger.debug()` | Detailed debugging info | ❌ No |
| `logger.info()` | General information | ❌ No |
| `logger.warning()` | Warnings that don't stop execution | ❌ No |
| `logger.error()` | Errors that should be visible | ✅ Yes |
| `logger.critical()` | Critical failures | ✅ Yes |
| `print()` | User-facing messages | ✅ Yes (always) |

### Best Practices

1. **Use `print()` for user-facing messages**:
   ```python
   print("✅ Tests completed successfully")
   print(f"📊 Results: {passed}/{total} passed")
   ```

2. **Use `logger.error()` for errors**:
   ```python
   logger.error("Failed to connect to server", exc_info=True)
   ```

3. **Use `logger.info()` for internal details**:
   ```python
   logger.info("Fetching data from API", endpoint=url)
   ```

4. **Wrap noisy operations**:
   ```python
   with QuietLogger():
       # This won't spam logs
       await playwright_browser.goto(url)
   ```

5. **Respect the verbose flag**:
   ```python
   if verbose:
       print(f"🔧 Debug info: {details}")
   ```

## Suppressed Libraries (Quiet Mode)

The following libraries are automatically set to ERROR level in quiet mode:

- **MCP**: `mcp`, `fastmcp`, `mcp.client`, `mcp.server`
- **HTTP**: `httpx`, `httpcore`, `urllib3`
- **OAuth**: `mcp_qa.oauth`, `mcp_qa.auth`
- **Browser**: `playwright`
- **WebSockets**: `websockets`, `uvicorn`
- **Async**: `asyncio`

## Troubleshooting

### "I don't see any logs!"
- You're in quiet mode (default). Use `--verbose` to see all logs.

### "I see too many logs!"
- Remove `--verbose` flag to use quiet mode.

### "Deprecation warnings still showing"
- Make sure `suppress_deprecation_warnings()` is called at the start.

### "My test output is messy"
- Use progress bars instead of print statements in loops.
- Use `QuietLogger()` context manager for noisy operations.

## Examples

### Example 1: Clean Test Suite
```python
#!/usr/bin/env python3
import asyncio
from tests.framework.test_logging_setup import (
    configure_test_logging,
    suppress_deprecation_warnings,
)

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    
    # Configure logging
    configure_test_logging(verbose=args.verbose)
    suppress_deprecation_warnings()
    
    # Run tests
    print("🧪 Running test suite...")
    # ... test code ...
    print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Using QuietLogger
```python
from tests.framework.test_logging_setup import QuietLogger

async def test_oauth_flow():
    print("🔐 Starting OAuth flow...")
    
    # Suppress noisy OAuth logs
    with QuietLogger():
        await oauth_client.authenticate()
        await playwright_browser.fill_form()
    
    print("✅ OAuth complete")
```

### Example 3: Conditional Verbose Output
```python
def run_tests(verbose: bool = False):
    if verbose:
        print("🔧 Verbose mode enabled")
        print(f"   Config: {config}")
        print(f"   Environment: {env}")
    
    print("🧪 Running tests...")
    # ... test code ...
```

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run tests (quiet mode)
  run: python tests/test_comprehensive_new.py

- name: Run tests (verbose on failure)
  if: failure()
  run: python tests/test_comprehensive_new.py --verbose
```

### Local Development
```bash
# Quick check (quiet)
python tests/test_comprehensive_new.py

# Debug failures (verbose)
python tests/test_comprehensive_new.py --verbose --categories core
```

## See Also

- `LOGGING_CLEANUP_SUMMARY.md` - Detailed implementation notes
- `tests/framework/test_logging_setup.py` - Source code
- `tests/framework/reporters.py` - Reporter implementations

