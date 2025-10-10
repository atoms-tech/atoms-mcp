"""
MCP-QA: Shared Testing Library for MCP Servers

A unified testing infrastructure that provides:
- OAuth credential management with .env persistence
- Playwright automation with inline progress
- Interactive TUI dashboards
- Comprehensive test reporting
- Health checks and validation
"""

__version__ = "0.1.0"

# Core imports - New base classes
from mcp_qa.core.base.test_runner import BaseTestRunner
from mcp_qa.core.base.client_adapter import BaseClientAdapter

# Backward compatibility aliases (deprecated - use base classes in new code)
# Import from core which now re-exports from base
from mcp_qa.core import TestRunner, MCPClientAdapter

# OAuth imports
from mcp_qa.oauth.credential_broker import UnifiedCredentialBroker, CapturedCredentials

# Reporter imports - Use modular reporters package
from mcp_qa.reporters import ConsoleReporter, JSONReporter

# Adapter imports - FastHTTPClient for ecosystem-wide reuse
from mcp_qa.adapters import FastHTTPClient

__all__ = [
    # New base classes (recommended)
    "BaseTestRunner",
    "BaseClientAdapter",
    # Legacy aliases (deprecated but still supported)
    "TestRunner",
    "MCPClientAdapter",
    # OAuth
    "UnifiedCredentialBroker",
    "CapturedCredentials",
    # Reporters
    "ConsoleReporter",
    "JSONReporter",
    # Adapters
    "FastHTTPClient",
]
