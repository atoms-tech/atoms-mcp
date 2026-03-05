"""
Atoms MCP Test Framework

A comprehensive testing infrastructure that integrates with pheno-sdk/mcp-qa
shared components while maintaining Atoms-specific implementations.

This module provides a hybrid approach with:
- Shared infrastructure from pheno-sdk
- Atoms-specific implementations
- Fallback strategies for missing components
- Advanced test modes and patterns
"""

# Core framework components
from .adapters import AtomsMCPClientAdapter
from .atoms_unified_runner import AtomsTestRunner

# Data generators and decorators
from .data_generators import DataGenerator, EntityFactory

try:
    from .decorators import cascade_flow
except (ImportError, AttributeError):
    cascade_flow = None

try:
    from .harmful import harmful
except (ImportError, AttributeError):
    harmful = None

try:
    from .dependencies import setup_test_dependencies
except ImportError:
    setup_test_dependencies = None

try:
    from .oauth_session import OAuthSessionManager
except ImportError:
    OAuthSessionManager = None

try:
    from .parallel_clients import ParallelClientManager
except ImportError:
    ParallelClientManager = None

try:
    from .runner import TestRunner
except ImportError:
    TestRunner = None

try:
    from .test_modes import TestMode, get_test_mode
except ImportError:
    TestMode = None
    get_test_mode = None

try:
    from .user_story_pattern import UserStoryPattern
except ImportError:
    UserStoryPattern = None

try:
    from .validators import TestValidator
except ImportError:
    TestValidator = None

# Re-export commonly used components
__all__ = [
    "AtomsMCPClientAdapter",
    "AtomsTestRunner",
    "DataGenerator",
    "EntityFactory",
    "OAuthSessionManager",
    "ParallelClientManager",
    "TestMode",
    "TestRunner",
    "TestValidator",
    "UserStoryPattern",
    "cascade_flow",
    "get_test_mode",
    "harmful",
    "setup_test_dependencies",
]
