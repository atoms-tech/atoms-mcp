# Schema Sync Quick Start Guide

Get started with the schema synchronization system in 5 minutes.

## Prerequisites

- Python 3.11+
- Supabase project with MCP access
- Environment variables configured

## Step 1: Set Up Environment Variables

```bash
# Required
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-role-key"
export SUPABASE_PROJECT_ID="your-project-id"

# Optional
export SUPABASE_ANON_KEY="your-anon-key"
```

Add these to your `.env` file:

```bash
echo "SUPABASE_URL=$SUPABASE_URL" >> .env
echo "SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY" >> .env
echo "SUPABASE_PROJECT_ID=$SUPABASE_PROJECT_ID" >> .env
```

## Step 2: Install Dependencies

```bash
uv sync
```

## Step 3: Run Your First Schema Check

```bash
# Check for drift
python scripts/sync_schema.py --check
```

Expected output:
- ✅ `✓ No schema drift detected` - Schemas are in sync
- ❌ `⚠️ Schema drift detected!` - Action required

## Step 4: View Differences (if drift detected)

```bash
# Show detailed differences
python scripts/sync_schema.py --diff
```

This displays:
- New/removed enums and tables
- Modified columns and enum values
- Severity level for each change

## Step 5: Update Local Schemas

```bash
# Update local schema files
python scripts/sync_schema.py --update
```

This will:
1. Generate code for new enums/tables
2. Update `schemas/schema_version.py`
3. Output code snippets for manual integration

## Step 6: Integrate Generated Code

Copy generated code into appropriate files:

### For New Enums
```python
# Copy to schemas/enums.py
class NewStatusType(str, Enum):
    """Auto-generated from database"""
    ACTIVE = "active"
    PENDING = "pending"
```

### For New Tables
```python
# Copy to schemas/database/entities.py or relationships.py
class NewTableRow(TypedDict, total=False):
    """Auto-generated from database"""
    id: str
    name: str
    created_at: str
```

## Step 7: Set Up CI/CD (Optional)

### GitHub Actions

The workflow is already created at `.github/workflows/schema-check.yml`.

Add these secrets to your GitHub repository:
1. Go to Settings → Secrets and variables → Actions
2. Add:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `SUPABASE_PROJECT_ID`

### Pre-commit Hook

```bash
# Install pre-commit hook
cp scripts/pre-commit-schema-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Or create a symlink:
```bash
ln -s ../../scripts/pre-commit-schema-check.sh .git/hooks/pre-commit
```

## Common Commands

### Check for drift (exit 1 if found)
```bash
python scripts/sync_schema.py --check
```

### Show detailed diff
```bash
python scripts/sync_schema.py --diff
```

### Update local schemas
```bash
python scripts/sync_schema.py --update
```

### Generate markdown report
```bash
python scripts/sync_schema.py --report
```

### Specify custom project ID
```bash
python scripts/sync_schema.py --check --project-id prj_abc123
```

## Understanding Output

### Severity Levels

- **CRITICAL**: Removed enums/tables (breaking change)
- **HIGH**: Modified enums, removed columns
- **MEDIUM**: Added columns, modified fields
- **LOW**: Minor additions

### Example Output

```
[HIGH] ENUM: project_status
  Change: modified
  Added values: on_hold
  Removed values: draft

[MEDIUM] TABLE: organizations
  Change: modified
  Added columns: billing_cycle
```

## Troubleshooting

### "Cannot connect to Supabase"
- Verify environment variables are set
- Check network connectivity
- Validate service role key permissions

### "Import errors after update"
- Check generated code syntax
- Add missing imports
- Resolve naming conflicts

### "False positive drift"
- Review enum/table name mappings
- Update special cases in config
- Check pluralization rules

## Next Steps

1. **Read Full Documentation**: See `docs/SCHEMA_SYNC_README.md`
2. **Run Tests**: `pytest tests/test_schema_sync.py -v`
3. **Generate Schema Docs**: `python scripts/mcp_schema_query.py --export-docs docs/schema`
4. **Configure Notifications**: Edit `scripts/schema_sync_config.json`
5. **Set Up Monitoring**: Enable drift history tracking

## Quick Reference

### File Structure
```
schemas/
├── __init__.py
├── schema_version.py        # Auto-generated version
├── enums.py                 # Enum definitions
├── database/
│   ├── entities.py         # Entity tables
│   └── relationships.py    # Relationship tables
scripts/
├── sync_schema.py          # Main sync tool
├── mcp_schema_query.py     # MCP-based queries
└── pre-commit-schema-check.sh
.github/workflows/
└── schema-check.yml        # CI/CD workflow
```

### Environment Variables
```bash
SUPABASE_URL              # Required
SUPABASE_SERVICE_KEY      # Required
SUPABASE_PROJECT_ID       # Required
SUPABASE_ANON_KEY         # Optional
```

### Key Files
- **Version tracking**: `schemas/schema_version.py`
- **Sync tool**: `scripts/sync_schema.py`
- **MCP queries**: `scripts/mcp_schema_query.py`
- **Configuration**: `scripts/schema_sync_config.json`
- **Tests**: `tests/test_schema_sync.py`

## Support

- 📖 Full docs: `docs/SCHEMA_SYNC_README.md`
- 🧪 Run tests: `pytest tests/test_schema_sync.py -v`
- 🐛 Report issues: Create GitHub issue
- 💬 Questions: Check documentation first

## Best Practices

1. **Run checks frequently**: Before commits, deploys, after migrations
2. **Review diffs carefully**: Understand impact before updating
3. **Test after updates**: Run full test suite
4. **Document changes**: Update migration notes
5. **Keep CI/CD enabled**: Catch drift automatically

---

**Ready to sync?** Run `python scripts/sync_schema.py --check` to get started!
