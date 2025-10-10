# Atoms MCP - Unified CLI

## Quick Start

All functionality is accessible through the `./atoms` command:

```bash
./atoms --help              # Show all commands
./atoms start               # Start local server
./atoms deploy              # Deploy to preview (default)
./atoms schema check        # Check schema drift
./atoms vendor setup        # Vendor pheno-sdk packages
```

## Available Commands

### 🚀 Start Server
```bash
./atoms start                    # Start with CloudFlare tunnel
./atoms start --port 50003       # Start on custom port
./atoms start --no-tunnel        # Start without tunnel
```

### 🧪 Testing
```bash
./atoms test                     # Run tests against preview (default)
./atoms test --environment local       # Run against local server
./atoms test --environment production  # Run against production
```

### 🌐 Deployment
```bash
./atoms deploy                   # Deploy to Vercel preview (default)
./atoms deploy --environment local       # Deploy locally via KInfra tunnel
./atoms deploy --environment production  # Deploy to Vercel production
```

**Deployment URLs:**
- **Local**: https://atomcp.kooshapari.com (KInfra tunnel)
- **Preview**: https://devmcp.atoms.tech (Vercel)
- **Production**: https://mcp.atoms.tech (Vercel)

### 🗄️ Schema Management
```bash
./atoms schema check             # Check for schema drift
./atoms schema sync              # Sync schemas from database
./atoms schema diff              # Show detailed differences
./atoms schema report            # Generate drift report
```

### 📦 Vendor Management
```bash
./atoms vendor setup             # Vendor pheno-sdk packages
./atoms vendor setup --clean     # Clean and re-vendor
./atoms vendor verify            # Verify vendored packages
./atoms vendor clean             # Remove vendor directory
```

### 🔧 Configuration
```bash
./atoms config show              # Show configuration
./atoms config validate          # Validate configuration
./atoms validate                 # Validate configuration (alias)
./atoms verify                   # Verify system setup
```

### 🧬 Embeddings
```bash
./atoms embeddings backfill      # Generate embeddings
./atoms embeddings status        # Check embedding status
```

## Architecture

### Single Entry Point

All functionality is consolidated through `./atoms`:

```
./atoms (symlink to atoms-mcp.py)
    ├── start       → Start local server
    ├── test        → Run tests
    ├── deploy      → Deploy to environments
    ├── schema      → Manage database schemas
    ├── vendor      → Manage vendored packages
    ├── config      → Configuration management
    ├── validate    → Validate configuration
    ├── verify      → Verify system setup
    └── embeddings  → Manage vector embeddings
```

### Libraries (Not Scripts!)

All functionality is implemented as reusable Python libraries in `lib/`:

```
lib/
├── vendor_manager.py    # Pheno-SDK vendoring
└── schema_sync.py       # Database schema synchronization
```

**No more shell scripts!** Everything is pure Python, type-safe, and testable.

## Common Workflows

### Local Development

```bash
# Start local server with tunnel
./atoms start

# Check schema drift
./atoms schema check

# Run tests (preview by default)
./atoms test
```

### Deploying to Preview

```bash
# Vendor packages (if pheno-sdk updated)
./atoms vendor setup --clean

# Sync schemas (if database changed)
./atoms schema sync

# Deploy to preview
./atoms deploy
```

### Deploying to Production

```bash
# Verify everything
./atoms validate
./atoms schema check
./atoms vendor verify

# Deploy
./atoms deploy --environment production
```

### Updating Vendored Packages

```bash
# When pheno-sdk is updated
./atoms vendor setup --clean

# Commit changes
git add pheno_vendor/ requirements-prod.txt sitecustomize.py
git commit -m "Update vendored packages"
git push
```

### Syncing Database Schemas

```bash
# When database schema changes
./atoms schema sync

# Commit changes
git add schemas/generated/
git commit -m "Regenerate schemas from database"
git push
```

## Migration from Old Commands

### Old → New

| Old Command | New Command |
|-------------|-------------|
| `python start_server.py` | `./atoms start` |
| `python start_server.py --deploy-dev` | `./atoms deploy` |
| `python start_server.py --deploy-prod` | `./atoms deploy --environment production` |
| `python tests/test_main.py --local` | `./atoms test --environment local` |
| `python test_config.py` | `./atoms validate` |
| `python verify_setup.py` | `./atoms verify` |
| `./scripts/vendor-pheno-sdk.sh` | `./atoms vendor setup` |
| `./scripts/vendor-pheno-sdk.sh --clean` | `./atoms vendor setup --clean` |
| `python scripts/sync_schema.py --check` | `./atoms schema check` |
| `python scripts/sync_schema.py --regenerate` | `./atoms schema sync` |
| `python scripts/backfill_embeddings.py` | `./atoms embeddings backfill` |

## Requirements Files

Only 2 requirements files:

1. **`requirements.txt`** - Development
   - Contains editable installs (`-e ../pheno-sdk/...`)
   - For local development only

2. **`requirements-prod.txt`** - Production
   - No editable installs
   - Uses vendored packages from `pheno_vendor/`
   - Auto-generated by `./atoms vendor setup`
   - For Vercel deployment

## Environment Variables

Set in `.env` file:

```bash
# Database
DB_URL=postgresql://...
SUPABASE_DB_PASSWORD=...

# Supabase
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# WorkOS
WORKOS_API_KEY=...
WORKOS_CLIENT_ID=...

# Google Cloud
GOOGLE_CLOUD_PROJECT=...
GOOGLE_CLOUD_LOCATION=...
```

## Directory Structure

```
atoms_mcp-old/
├── atoms                 # Main CLI (symlink to atoms-mcp.py)
├── atoms-mcp.py          # CLI implementation
├── app.py                # Vercel entry point
├── server.py             # Server module
│
├── lib/                  # Reusable libraries
│   ├── vendor_manager.py
│   └── schema_sync.py
│
├── pheno_vendor/         # Vendored pheno-sdk packages
├── schemas/              # Database schemas
│   └── generated/
│       └── fastapi/
│           └── schema_public_latest.py
│
├── scripts/              # Utility scripts (called via ./atoms)
├── tests/                # Test suite
├── tools/                # MCP tools
│
├── requirements.txt      # Dev dependencies
├── requirements-prod.txt # Prod dependencies (auto-generated)
├── sitecustomize.py      # Vendor loader (auto-generated)
│
└── archive/              # Archived files
    ├── old_entry_points/
    └── old_scripts/
```

## Troubleshooting

### Command not found: atoms

```bash
# Ensure symlink exists
ln -sf atoms-mcp.py atoms
chmod +x atoms-mcp.py atoms
```

### Schema drift detected

```bash
# Sync schemas from database
./atoms schema sync

# Or check what changed
./atoms schema diff
```

### Vendor packages outdated

```bash
# Re-vendor packages
./atoms vendor setup --clean

# Verify
./atoms vendor verify
```

### Deployment fails

```bash
# Verify setup
./atoms verify
./atoms validate

# Check vendored packages
./atoms vendor verify

# Check schema sync
./atoms schema check
```

## Development

### Adding New Commands

1. Add command function to `atoms-mcp.py`:
   ```python
   def cmd_mycommand(args):
       """My command description."""
       # Implementation
   ```

2. Add parser in `main()`:
   ```python
   mycommand_parser = subparsers.add_parser("mycommand", help="...")
   mycommand_parser.set_defaults(func=cmd_mycommand)
   ```

3. Test:
   ```bash
   ./atoms mycommand --help
   ```

### Creating Libraries

1. Create library in `lib/`:
   ```python
   # lib/my_manager.py
   class MyManager:
       def do_something(self):
           pass
   ```

2. Use in command:
   ```python
   def cmd_mycommand(args):
       from lib.my_manager import MyManager
       mgr = MyManager()
       mgr.do_something()
   ```

## Best Practices

1. **Always use `./atoms`** - Don't call scripts directly
2. **Vendor before deploying** - Run `./atoms vendor setup --clean`
3. **Check schema drift** - Run `./atoms schema check` before deploying
4. **Test locally first** - Use `./atoms test --environment local`
5. **Use libraries, not scripts** - Create reusable Python libraries in `lib/`

## Support

For issues or questions:
1. Check `./atoms <command> --help`
2. Review this documentation
3. Check archived files in `archive/` for old implementations
4. Contact the team

---

**All functionality through `./atoms` - One command to rule them all!** 🚀
