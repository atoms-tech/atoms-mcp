# Migration Quick Reference: Test Consolidation

## TL;DR

✅ **All generic test utilities → `pheno_vendor/mcp_qa`**
✅ **Atoms-specific helpers → `tests/framework/atoms_helpers.py`**
✅ **Atoms pytest fixtures → `tests/fixtures/atoms_data.py`**

## Import Changes

### Before ❌
```python
from tests.framework.patterns import UserStoryPattern
from tests.framework.validators import ResponseValidator
from tests.framework.factories import TestFactory
from tests.fixtures.data import test_data_factory
from tests.fixtures.providers import authkit_provider
```

### After ✅
```python
# Generic patterns (from mcp_qa)
from mcp_qa.core.patterns import UserStoryPattern, ToolTestPattern
from mcp_qa.core.validators import ResponseValidator, FieldValidator
from mcp_qa.core.factories import TestFactory, TestSuiteFactory
from mcp_qa.core.data_generators import DataGenerator

# Atoms-specific (local)
from tests.framework.atoms_helpers import AtomsTestHelpers
from tests.fixtures.atoms_data import test_data_factory, sample_workspace_data

# OAuth providers (from mcp_qa)
from mcp_qa.oauth.oauth_automation.providers.authkit import AUTHKIT_FLOW
from mcp_qa.oauth.oauth_automation.providers.github import GITHUB_FLOW
```

### Backward Compatible (Still Works) ⚠️
```python
# Re-exported from tests/framework/__init__.py
from tests.framework import (
    UserStoryPattern,      # → mcp_qa.core.patterns
    ResponseValidator,     # → mcp_qa.core.validators
    TestFactory,           # → mcp_qa.core.factories
    AtomsTestHelpers,      # → tests.framework.atoms_helpers
)

# Re-exported from tests/fixtures/__init__.py
from tests.fixtures import (
    test_data_factory,     # → tests.fixtures.atoms_data
    DataGenerator,         # → mcp_qa.core.data_generators
)
```

## Common Operations

### 1. Enhanced Context Resolution (NEW!)

**Advanced nested path support:**
```python
from mcp_qa.core.patterns import UserStoryPattern

story = UserStoryPattern("Create and Link", steps=[
    {
        "tool": "entity_tool",
        "params": {"operation": "create", "data": {...}},
        "save_to_context": "org_response"
    },
    {
        "tool": "entity_tool",
        "params": {
            "operation": "create",
            # NOW SUPPORTS nested paths and array indices!
            "data": {
                "organization_id": "$context.org_response.data.id",      # Nested
                "tags": "$context.org_response.metadata.tags[0]"         # Array
            }
        }
    }
])
```

**Supported patterns:**
- `$context.field` - Direct field
- `$context.data.nested.field` - Nested dicts
- `$context.items[0]` - Array index
- `$context.results[0].data.id` - Combined

### 2. Atoms Entity Helpers

**Before:**
```python
from tests.framework.validators import ResponseValidator

# Manual parent ID resolution
org_id = await ResponseValidator.get_or_create_organization(client)
project_id = await ResponseValidator.get_or_create_project(client, org_id)
doc_id = await ResponseValidator.get_or_create_document(client, project_id)
```

**After:**
```python
from tests.framework.atoms_helpers import AtomsTestHelpers

# Same functionality, clearer naming
org_id = await AtomsTestHelpers.get_or_create_organization(client)
project_id = await AtomsTestHelpers.get_or_create_project(client, org_id)
doc_id = await AtomsTestHelpers.get_or_create_document(client, project_id)

# Auto-parent resolution (no need to pass parent IDs)
project_id = await AtomsTestHelpers.get_or_create_project(client)  # Auto-creates org
doc_id = await AtomsTestHelpers.get_or_create_document(client)     # Auto-creates project
```

### 3. Generic Data Generation

**Before:**
```python
from tests.framework.data_generators import DataGenerator

org_data = DataGenerator.organization_data()
project_data = DataGenerator.project_data(organization_id=org_id)
```

**After:**
```python
from mcp_qa.core.data_generators import DataGenerator

# Same API, now generic for all MCP servers
org_data = DataGenerator.organization_data()
project_data = DataGenerator.project_data(organization_id=org_id)
```

### 4. Pytest Fixtures (Atoms-specific)

**Before:**
```python
from tests.fixtures.data import (
    sample_workspace_data,
    test_data_factory,
    realistic_document_data
)
```

**After:**
```python
from tests.fixtures.atoms_data import (
    sample_workspace_data,
    test_data_factory,
    realistic_document_data,
    realistic_workspace_structure,  # NEW!
    bulk_test_data,                 # NEW!
    persistent_test_workspace       # NEW!
)
```

### 5. OAuth Providers

**Before:**
```python
from tests.fixtures.providers import authkit_provider

provider = authkit_provider()  # Dict config
```

**After:**
```python
from mcp_qa.oauth.oauth_automation.providers.authkit import AUTHKIT_FLOW

# Pre-configured flow with steps, MFA support, consent handling
flow = AUTHKIT_FLOW
```

## File Locations

### Generic (mcp_qa)
```
pheno_vendor/mcp_qa/core/
├── patterns.py           # UserStoryPattern, ToolTestPattern, IntegrationPattern
├── validators.py         # ResponseValidator, FieldValidator
├── factories.py          # TestFactory, TestSuiteFactory, ParameterPermutationFactory
└── data_generators.py    # DataGenerator (generic)

pheno_vendor/mcp_qa/oauth/oauth_automation/providers/
├── authkit.py           # AUTHKIT_FLOW
├── github.py            # GITHUB_FLOW
├── google.py            # GOOGLE_FLOW
└── azure_ad.py          # AZURE_AD_FLOW
```

### Atoms-specific
```
tests/framework/
└── atoms_helpers.py     # AtomsTestHelpers (entity helpers)

tests/fixtures/
└── atoms_data.py        # Pytest fixtures (sample_workspace_data, test_data_factory, etc.)
```

### Archived (for reference)
```
archive/old_test_framework/
├── patterns.py          # → mcp_qa (enhanced)
├── validators.py        # → atoms_helpers.py
├── factories.py         # → mcp_qa (duplicate)
├── data.py             # → atoms_data.py
└── providers.py        # → mcp_qa (superseded)
```

## Code Examples

### Complete Test Migration

**Before:**
```python
import pytest
from tests.framework.patterns import UserStoryPattern
from tests.framework.validators import ResponseValidator
from tests.framework.data_generators import DataGenerator

@pytest.mark.asyncio
async def test_create_project_workflow(client):
    # Get org ID
    org_id = await ResponseValidator.get_or_create_organization(client)

    # Create project
    project_data = DataGenerator.project_data(organization_id=org_id)
    story = UserStoryPattern("Create Project", steps=[...])
    result = await story.execute(client)
    assert result["success"]
```

**After:**
```python
import pytest
from mcp_qa.core.patterns import UserStoryPattern
from mcp_qa.core.data_generators import DataGenerator
from tests.framework.atoms_helpers import AtomsTestHelpers

@pytest.mark.asyncio
async def test_create_project_workflow(client):
    # Get org ID (auto-creates if needed)
    org_id = await AtomsTestHelpers.get_or_create_organization(client)

    # Create project
    project_data = DataGenerator.project_data(organization_id=org_id)
    story = UserStoryPattern("Create Project", steps=[...])
    result = await story.execute(client)
    assert result["success"]
```

### Using Enhanced Context Resolution

```python
from mcp_qa.core.patterns import UserStoryPattern

story = UserStoryPattern("E2E Workflow", steps=[
    {
        "tool": "entity_tool",
        "params": {"operation": "list", "entity_type": "organization", "limit": 1},
        "save_to_context": "org_list"
    },
    {
        "tool": "entity_tool",
        "params": {
            "operation": "create",
            "entity_type": "project",
            "data": {
                # ENHANCED: Deep nested path with array index
                "organization_id": "$context.org_list.data[0].id",
                "name": "New Project"
            }
        },
        "save_to_context": "project"
    },
    {
        "tool": "entity_tool",
        "params": {
            "operation": "read",
            # ENHANCED: Reference previous step's nested field
            "entity_id": "$context.project.data.id"
        }
    }
])
```

## Breaking Changes

### ❌ None! All imports are backward compatible

The old import paths still work via re-exports in:
- `tests/framework/__init__.py`
- `tests/fixtures/__init__.py`

### ⚠️ Deprecated (but still functional)
- `from tests.framework.patterns import *` (use `mcp_qa.core.patterns`)
- `from tests.framework.validators import *` (use `mcp_qa.core.validators` + `AtomsTestHelpers`)
- `from tests.framework.factories import *` (use `mcp_qa.core.factories`)

## Recommended Migration

### Low Priority (Optional)
Update imports to new paths for clarity:
```python
# Old (works)
from tests.framework import UserStoryPattern

# New (clearer)
from mcp_qa.core.patterns import UserStoryPattern
```

### Medium Priority (Recommended)
Use `AtomsTestHelpers` for Atoms entity operations:
```python
# Old
from tests.framework.validators import ResponseValidator
org_id = await ResponseValidator.get_or_create_organization(client)

# New (clearer naming)
from tests.framework.atoms_helpers import AtomsTestHelpers
org_id = await AtomsTestHelpers.get_or_create_organization(client)
```

### High Priority (Do This!)
Leverage enhanced context resolution:
```python
# Before: Manual field extraction
result1 = await client.call_tool("list", {...})
org_id = result1["response"]["data"][0]["id"]
result2 = await client.call_tool("create", {"data": {"organization_id": org_id}})

# After: Automatic context resolution
story = UserStoryPattern("Create", steps=[
    {"tool": "list", "params": {...}, "save_to_context": "list_result"},
    {"tool": "create", "params": {
        "data": {"organization_id": "$context.list_result.data[0].id"}
    }}
])
```

## Questions?

See full documentation in:
- `PHASE_2_CONSOLIDATION_COMPLETE.md` - Detailed analysis
- `pheno_vendor/mcp_qa/README.md` - mcp_qa documentation
- `tests/framework/atoms_helpers.py` - Atoms helper source
- `tests/fixtures/atoms_data.py` - Atoms fixture source
