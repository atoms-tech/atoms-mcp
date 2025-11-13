# sb-pydantic Integration Plan

## Overview

Integrate `supabase-pydantic` (sb-pydantic) to auto-generate Pydantic models from Supabase database schema.

## Current State

### Manual Schema Definitions

**tools/entity.py** - Manual schema dictionaries:
```python
schemas = {
    "organization": {
        "required_fields": ["name", "slug"],
        "auto_fields": ["id", "created_at", "updated_at"],
        "default_values": {"is_deleted": False, "type": "team"},
        "relationships": ["members", "projects", "invitations"]
    },
    # ... 15+ entity types manually defined
}
```

**tools/base.py** - Manual table mappings:
```python
entity_table_map = {
    "organization": "organizations",
    "project": "projects",
    "document": "documents",
    # ... 20+ mappings
}
```

**build/lib/schemas/enums.py** - Manual enums:
```python
class EntityType(str, Enum):
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"
    # ... manual definitions
```

### Problems

1. ❌ **Schema drift** - Manual schemas can get out of sync with database
2. ❌ **No type safety** - Using Dict[str, Any] everywhere
3. ❌ **Maintenance burden** - Every DB change requires manual updates
4. ❌ **No auto-completion** - IDEs can't help with field names
5. ❌ **Error-prone** - Typos in field names only caught at runtime

## Target State

### Auto-Generated Pydantic Models

```python
# schemas/generated/models.py (auto-generated)
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class Organization(BaseModel):
    id: UUID
    name: str
    slug: str
    type: OrganizationType
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
    
    class Config:
        from_attributes = True

class Project(BaseModel):
    id: UUID
    name: str
    slug: str
    organization_id: UUID
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    # ... all fields from database
```

### Benefits

1. ✅ **Type safety** - Full Pydantic validation
2. ✅ **Auto-completion** - IDE support for all fields
3. ✅ **Schema sync** - Always matches database
4. ✅ **Less code** - No manual schema definitions
5. ✅ **Catch errors early** - Type errors at development time

## Implementation Plan

### Phase 1: Setup sb-pydantic

#### Step 1: Install dependencies

```bash
# Add to requirements.txt
supabase-pydantic>=0.13.0
```

#### Step 2: Create generation script

```python
# scripts/generate_schemas.py
"""Generate Pydantic models from Supabase schema."""

import os
from supabase_pydantic import create_client

def generate_schemas():
    """Generate Pydantic models from Supabase."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")  # Need service key for schema access
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
    
    # Generate models
    client = create_client(supabase_url, supabase_key)
    
    # Generate for all tables
    tables = [
        "organizations",
        "projects",
        "documents",
        "requirements",
        "test_req",
        "blocks",
        "properties",
        "trace_links",
        "assignments",
        "profiles",
        "organization_members",
        "project_members",
        "organization_invitations",
        "requirement_tests",
        "audit_logs",
        "notifications",
        "external_documents",
        "test_matrix_views",
        "mcp_sessions",
    ]
    
    output_dir = "schemas/generated"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate models
    for table in tables:
        print(f"Generating model for {table}...")
        # sb-pydantic will introspect the table and generate Pydantic model
    
    print(f"✅ Generated models in {output_dir}/")

if __name__ == "__main__":
    generate_schemas()
```

#### Step 3: Add to package

```python
# schemas/__init__.py
"""Auto-generated Pydantic models from Supabase."""

from .generated.models import (
    Organization,
    Project,
    Document,
    Requirement,
    TestReq,
    Block,
    Property,
    TraceLink,
    Assignment,
    Profile,
    OrganizationMember,
    ProjectMember,
    OrganizationInvitation,
    RequirementTest,
    AuditLog,
    Notification,
    ExternalDocument,
    TestMatrixView,
    McpSession,
)

__all__ = [
    "Organization",
    "Project",
    "Document",
    "Requirement",
    "TestReq",
    # ... all models
]
```

### Phase 2: Update Tools

#### Step 1: Replace manual schemas

**Before (tools/entity.py)**:
```python
def _get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
    schemas = {
        "organization": {
            "required_fields": ["name", "slug"],
            # ... manual definition
        }
    }
    return schemas.get(entity_type.lower(), {})
```

**After**:
```python
from schemas import Organization, Project, Document

def _get_entity_model(self, entity_type: str):
    """Get Pydantic model for entity type."""
    models = {
        "organization": Organization,
        "project": Project,
        "document": Document,
        # ... all models
    }
    return models.get(entity_type.lower())

def _validate_entity_data(self, entity_type: str, data: Dict[str, Any]):
    """Validate entity data using Pydantic model."""
    model = self._get_entity_model(entity_type)
    if model:
        # Pydantic validation
        validated = model(**data)
        return validated.model_dump()
    return data
```

#### Step 2: Update create/update operations

```python
async def create_entity(
    self,
    entity_type: str,
    data: Dict[str, Any],
    include_relations: bool = False
) -> Dict[str, Any]:
    """Create a new entity with Pydantic validation."""
    # Validate with Pydantic model
    validated_data = self._validate_entity_data(entity_type, data)
    
    # Get table name
    table = self._resolve_entity_table(entity_type)
    
    # Create entity
    result = await self._db_insert(table, validated_data, returning="*")
    
    return result
```

### Phase 3: CI/CD Integration

#### Step 1: Add to pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: generate-schemas
        name: Generate Pydantic schemas from Supabase
        entry: python scripts/generate_schemas.py
        language: system
        pass_filenames: false
```

#### Step 2: Add to GitHub Actions

```yaml
# .github/workflows/generate-schemas.yml
name: Generate Schemas

on:
  schedule:
    - cron: '0 0 * * *'  # Daily
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/generate_schemas.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
      - uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'chore: Update generated Pydantic schemas'
          title: 'Update Pydantic schemas from Supabase'
```

## Timeline

### Week 1: Setup
- [ ] Install sb-pydantic
- [ ] Create generation script
- [ ] Generate initial models
- [ ] Test models locally

### Week 2: Integration
- [ ] Update tools/entity.py
- [ ] Update tools/base.py
- [ ] Add validation to CRUD operations
- [ ] Test all operations

### Week 3: Cleanup
- [ ] Remove manual schemas
- [ ] Update tests
- [ ] Add CI/CD integration
- [ ] Documentation

## Next Steps

1. Install supabase-pydantic
2. Create generation script
3. Generate models
4. Test integration
5. Deploy

