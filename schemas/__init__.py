"""Pydantic schemas for Atoms MCP.

This package contains:
- generated/ - Auto-generated models from Supabase (use these!)
- manual/ - Legacy manual schemas (being phased out)

Usage:
    from schemas.generated import Organization, Project, Document
    
    org = Organization(name="Acme", slug="acme", type="team")
"""

# Try to import generated models
try:
    from .generated import *  # noqa: F401, F403
    _has_generated = True
except ImportError:
    _has_generated = False
    import warnings
    warnings.warn(
        "Generated schemas not found. Run: python scripts/generate_schemas.py",
        UserWarning
    )

__all__ = []

if _has_generated:
    from .generated import __all__ as generated_all
    __all__.extend(generated_all)

