# Atoms MCP SDK Symlinks
## Avoiding Duplication via Symlinks

**Created:** 2025-10-08  
**Purpose:** Link atoms_mcp-old to all centralized SDKs in `/485/kush/`

---

## Symlink Structure

All SDKs are symlinked from `/Users/kooshapari/temp-PRODVERCEL/485/kush/` to avoid code duplication.

### Active Symlinks (12 SDKs)

| SDK | Symlink Path | Target Path |
|-----|--------------|-------------|
| pydevkit | `lib-sdks/pydevkit` | `../pheno-sdk/pydevkit` |
| adapter-kit | `lib-sdks/adapter-kit` | `../pheno-sdk/adapter-kit` |
| observability-kit | `lib-sdks/observability-kit` | `../pheno-sdk/observability-kit` |
| orchestrator-kit | `lib-sdks/orchestrator-kit` | `../pheno-sdk/orchestrator-kit` |
| workflow-kit | `lib-sdks/workflow-kit` | `../pheno-sdk/workflow-kit` |
| stream-kit | `lib-sdks/stream-kit` | `../pheno-sdk/stream-kit` |
| db-kit | `lib-sdks/db-kit` | `../pheno-sdk/db-kit` |
| deploy-kit | `lib-sdks/deploy-kit` | `../pheno-sdk/deploy-kit` |
| tui-kit | `lib-sdks/tui-kit` | `../pheno-sdk/tui-kit` |
| build-analyzer-kit | `lib-sdks/build-analyzer-kit` | `../pheno-sdk/build-analyzer-kit` |
| cli-builder-kit | `lib-sdks/cli-builder-kit` | `../pheno-sdk/cli-builder-kit` |
| filewatch-kit | `lib-sdks/filewatch-kit` | `../pheno-sdk/filewatch-kit` |

---

## Usage in Atoms MCP

### Importing SDKs

```python
# From atoms_mcp-old, import SDKs via symlinks
import sys
sys.path.insert(0, '/Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/lib-sdks')

# Now import any SDK
from pydevkit import config, http, security
from observability import Metrics, Tracer, StructuredLogger
from workflow_kit import Workflow, WorkflowEngine, saga
from orchestrator_kit import HybridOrchestrator, AgentCapability
from db_kit import Database, SupabaseAdapter
from stream_kit import Stream, EventBus
from deploy_kit import Deploy, NVMSConfig
```

### Example: Using Workflow-Kit in Atoms

```python
from lib_sdks.workflow_kit import workflow, WorkflowEngine
from lib_sdks.orchestrator_kit import HybridOrchestrator

@workflow
class AtomsSyncWorkflow:
    async def sync_requirements(self, ctx):
        return await ctx.call_service("atoms", "sync_requirements", ctx.inputs)
    
    async def update_entities(self, ctx):
        return await ctx.call_service("atoms", "update_entities", ctx.inputs)

# Execute workflow
engine = WorkflowEngine(orchestrator=HybridOrchestrator())
result = await engine.execute(AtomsSyncWorkflow, {"project_id": "123"})
```

### Example: Using DB-Kit for Supabase

```python
from lib_sdks.db_kit.platforms import SupabaseAdapter
from lib_sdks.db_kit import Database

# Use Supabase adapter (already configured in atoms)
db = Database(
    adapter=SupabaseAdapter(
        url=os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
        anon_key=os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"),
        service_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
)

# RLS-aware queries
async with db.auth_context(user_jwt):
    users = await db.from_("users").select("*").execute()
```

---

## Benefits

### 1. Single Source of Truth
- All SDKs maintained in one location (`485/kush/`)
- Changes propagate automatically to atoms
- No code duplication

### 2. Development Efficiency
- Update SDK once, affects all projects
- Easier testing and debugging
- Consistent versioning

### 3. Disk Space Savings
- No duplicated code
- Symlinks are tiny (< 1KB each)

### 4. Version Control
- Single git history for each SDK
- Easier to track changes
- Simplified CI/CD

---

## Verification

```bash
# Verify all symlinks are valid
cd /Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/lib-sdks
ls -la

# Should show 12 symlinks, all pointing to 485/kush/

# Test imports
python3 -c "
import sys
sys.path.insert(0, 'lib-sdks/pydevkit')
sys.path.insert(0, 'lib-sdks/observability-kit')
from pydevkit import __version__ as pydev_ver
from observability import __version__ as obs_ver
print(f'pydevkit: {pydev_ver}')
print(f'observability-kit: {obs_ver}')
"
```

---

## Maintenance

### Adding New SDK
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/lib-sdks
ln -s /Users/kooshapari/temp-PRODVERCEL/485/kush/new-kit new-kit
```

### Removing SDK
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/lib-sdks
rm new-kit  # Only removes symlink, not actual SDK
```

### Updating SDK
```bash
# Just update in the source location
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/pydevkit
# Make changes...
# atoms_mcp-old will see changes immediately via symlink
```

---

## Migration from Duplicated Code

If atoms previously had duplicated code, migrate as follows:

### 1. Identify Duplicated Modules
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old

# Find what can be replaced with SDKs
# Example: infrastructure/sql/ → db-kit
# Example: auth/ patterns → pydevkit.security
# Example: tools/ patterns → orchestrator-kit
```

### 2. Update Imports
```python
# Old (duplicated code)
from infrastructure.sql import pool, rls

# New (via symlink)
from lib_sdks.db_kit.core import pool
from lib_sdks.db_kit.tenancy import rls
```

### 3. Remove Duplicated Code
```bash
# After verifying symlink works
rm -rf infrastructure/sql/
# Keep only atoms-specific code
```

---

## Status

✅ All 12 core SDKs symlinked  
✅ Accessible from atoms via `lib-sdks/`  
✅ Zero duplication  
✅ Ready for development

---

**Next:** Use these SDKs throughout atoms_mcp-old to replace duplicated code and leverage shared functionality!
