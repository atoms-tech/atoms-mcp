# MCP-QA: Shared Testing Library for MCP Servers

A unified testing infrastructure shared between Zen MCP Server and Atoms MCP implementations.

## Structure

```
mcp-QA/
├── core/           # Core testing framework
│   ├── test_runner.py
│   ├── test_registry.py
│   └── adapters.py
├── oauth/          # OAuth & credential management
│   ├── credential_broker.py
│   ├── playwright_adapter.py
│   ├── session_manager.py
│   └── cache.py
├── tui/            # Terminal UI components
│   ├── dashboard.py
│   ├── progress.py
│   └── widgets.py
├── reporters/      # Test reporters
│   ├── console.py
│   ├── json.py
│   └── markdown.py
└── utils/          # Utilities
    ├── health_checks.py
    └── helpers.py
```

## Installation

```bash
# From Zen MCP Server
cd /path/to/zen-mcp-server
pip install -e /path/to/mcp-QA

# From Atoms MCP
cd /path/to/atoms_mcp-old
pip install -e /path/to/mcp-QA
```

## Usage

```python
# In any MCP test suite
from mcp_qa.oauth import UnifiedCredentialBroker
from mcp_qa.core import TestRunner
from mcp_qa.reporters import ConsoleReporter, JSONReporter

# Get authenticated client with credentials
broker = UnifiedCredentialBroker("https://mcp.example.com/api/mcp")
client, credentials = await broker.get_authenticated_client()

# Run tests
runner = TestRunner(
    client_adapter=adapter,
    reporters=[ConsoleReporter(), JSONReporter()]
)
await runner.run_all()
```

## Features

### Unified OAuth Flow
- Single credential prompt with .env persistence
- Playwright automation with inline progress
- Token capture for direct HTTP calls
- Session management and caching

### Interactive TUI
- Real-time test progress
- OAuth status widgets
- Live test runner
- WebSocket broadcasting

### Comprehensive Reporting
- Console output with color
- JSON reports
- Markdown summaries
- Functionality matrices

### Health Checks
- Pre-test validation
- Server connectivity
- Tool availability
- OAuth session status

## Design Principles

1. **DRY**: Single source of truth for common functionality
2. **Backward Compatible**: Works with existing test suites
3. **Modular**: Import only what you need
4. **Well Tested**: Self-testing infrastructure
5. **Documented**: Clear API and examples
