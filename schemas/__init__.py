"""Pydantic schemas for Atoms MCP.

This package contains:
- generated/ - Auto-generated models from Supabase (use these!)
- validators.py - Consolidated Pydantic validators (replaces input_validator.py)
- manual/ - Legacy manual schemas (being phased out)

Usage:
    from schemas.generated import Organization, Project, Document
    from schemas.validators import OrganizationInput, ProjectInput

    org = Organization(name="Acme", slug="acme", type="team")
    org_input = OrganizationInput(name="Acme", slug="acme")
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

# Import validators
from .validators import (  # noqa: F401
    EntityInput,
    OrganizationInput,
    ProjectInput,
    DocumentInput,
    RequirementInput,
    TestInput,
    RelationshipInput,
    SearchInput,
    validate_required_fields,
    validate_entity_data,
    is_uuid_format,
)

__all__ = [
    "EntityInput",
    "OrganizationInput",
    "ProjectInput",
    "DocumentInput",
    "RequirementInput",
    "TestInput",
    "RelationshipInput",
    "SearchInput",
    "validate_required_fields",
    "validate_entity_data",
    "is_uuid_format",
]

if _has_generated:
    from .generated import __all__ as generated_all
    __all__.extend(generated_all)

