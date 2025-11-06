# Schemas Directory

This directory contains Pydantic models for the Atoms MCP system.

## Structure

```
schemas/
├── README.md              # This file
├── __init__.py           # Package exports
├── generated/            # Auto-generated models from Supabase
│   ├── __init__.py
│   └── models.py         # Generated Pydantic models
└── manual/               # Manual schema definitions (legacy)
    ├── enums.py          # Application-level enums
    └── validators.py     # Custom validators
```

## Generated Models

The `generated/` directory contains Pydantic models auto-generated from the Supabase database schema.

### Generating Models

**Prerequisites:**
- `SUPABASE_URL` environment variable
- `SUPABASE_SERVICE_KEY` environment variable (service role key)

**Generate models:**
```bash
# Using supabase-pydantic (recommended)
python scripts/generate_schemas.py

# Or using simple introspection
python scripts/generate_schemas_simple.py
```

**Output:**
- `schemas/generated/models.py` - All Pydantic models
- `schemas/generated/__init__.py` - Exports

### Using Generated Models

```python
from schemas.generated import Organization, Project, Document

# Create with validation
org = Organization(
    name="Acme Corp",
    slug="acme-corp",
    type="team"
)

# Validate data
project_data = {
    "name": "My Project",
    "organization_id": "123e4567-e89b-12d3-a456-426614174000"
}
project = Project(**project_data)

# Convert to dict
data = project.model_dump()
```

### Available Models

Generated from these tables:
- `Organization` (organizations)
- `Project` (projects)
- `Document` (documents)
- `Requirement` (requirements)
- `TestReq` (test_req)
- `Block` (blocks)
- `Property` (properties)
- `TraceLink` (trace_links)
- `Assignment` (assignments)
- `Profile` (profiles)
- `OrganizationMember` (organization_members)
- `ProjectMember` (project_members)
- `OrganizationInvitation` (organization_invitations)
- `RequirementTest` (requirement_tests)
- `AuditLog` (audit_logs)
- `Notification` (notifications)
- `ExternalDocument` (external_documents)
- `TestMatrixView` (test_matrix_views)
- `McpSession` (mcp_sessions)

## Manual Schemas (Legacy)

The `manual/` directory contains manually-defined schemas that are being phased out.

**DO NOT ADD NEW MANUAL SCHEMAS** - Use generated models instead.

## CI/CD Integration

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: generate-schemas
        name: Generate Pydantic schemas
        entry: python scripts/generate_schemas.py
        language: system
        pass_filenames: false
```

### GitHub Actions

Automatically regenerate schemas daily:
```yaml
# .github/workflows/generate-schemas.yml
name: Generate Schemas
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python scripts/generate_schemas.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
      - uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'chore: Update generated schemas'
```

## Migration Guide

### Migrating from Manual Schemas

**Before:**
```python
# tools/entity.py
def _get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
    schemas = {
        "organization": {
            "required_fields": ["name", "slug"],
            "auto_fields": ["id", "created_at"],
            # ... manual definition
        }
    }
    return schemas.get(entity_type.lower(), {})
```

**After:**
```python
# tools/entity.py
from schemas.generated import Organization

def _validate_entity(self, entity_type: str, data: Dict[str, Any]):
    """Validate entity data using Pydantic model."""
    models = {
        "organization": Organization,
        # ... other models
    }
    
    model = models.get(entity_type.lower())
    if model:
        validated = model(**data)
        return validated.model_dump()
    return data
```

## Benefits

✅ **Type Safety** - Full Pydantic validation
✅ **Auto-completion** - IDE support for all fields
✅ **Schema Sync** - Always matches database
✅ **Less Code** - No manual schema definitions
✅ **Catch Errors Early** - Type errors at development time

## Troubleshooting

### Schema generation fails

**Error**: `SUPABASE_SERVICE_KEY required`
**Fix**: Set environment variable with service role key

**Error**: `Table not found`
**Fix**: Check table name in `scripts/generate_schemas.py`

### Models out of sync

**Fix**: Regenerate models after database changes:
```bash
python scripts/generate_schemas.py
```

### Import errors

**Error**: `ModuleNotFoundError: No module named 'schemas.generated'`
**Fix**: Generate models first:
```bash
python scripts/generate_schemas.py
```

## Documentation

- **Setup Guide**: `SB_PYDANTIC_INTEGRATION_PLAN.md`
- **Migration Guide**: See "Migration Guide" section above
- **Pydantic Docs**: https://docs.pydantic.dev/
- **supabase-pydantic**: https://github.com/koxudaxi/supabase-pydantic

