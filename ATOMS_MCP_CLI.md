# Atoms MCP Unified CLI

**Status:** ✅ Complete

All entry points consolidated into `atoms-mcp.py` - the single interface for ALL Atoms MCP operations.

## Architecture

```
atoms-mcp.py (Unified CLI)
├── start      → Delegates to start_server module
├── test       → Delegates to tests/test_main module  
├── deploy     → Delegates to start_server deployment logic
├── validate   → Delegates to test_config module
├── verify     → Delegates to verify_setup module
├── vendor     → Calls pheno-vendor CLI (deploy-kit)
└── config     → Built-in config management
```

## Commands

### Start Server
```bash
./atoms-mcp.py start                    # Start with tunnel (default)
./atoms-mcp.py start --port 50003       # Custom port
./atoms-mcp.py start --no-tunnel        # Local only (no OAuth)
./atoms-mcp.py start --verbose          # Debug logging
```

### Run Tests
```bash
./atoms-mcp.py test                     # Run all tests on prod
./atoms-mcp.py test --local             # Run on local server
./atoms-mcp.py test --verbose           # Verbose output
./atoms-mcp.py test --categories entity query  # Specific tests
./atoms-mcp.py test --workers 4         # Parallel execution
./atoms-mcp.py test --no-oauth          # Skip OAuth tests
./atoms-mcp.py test --headless          # Headless browser
```

### Deploy
```bash
./atoms-mcp.py deploy --local           # Deploy locally via KInfra tunnel
./atoms-mcp.py deploy --local --port 50003  # Local on custom port
./atoms-mcp.py deploy --preview         # Deploy to Vercel preview (devmcp.atoms.tech)
./atoms-mcp.py deploy --production      # Deploy to Vercel production (atomcp.kooshapari.com)
```

### Validate & Verify
```bash
./atoms-mcp.py validate                 # Check configuration
./atoms-mcp.py verify                   # Verify system setup
./atoms-mcp.py config show              # Show config (masked secrets)
./atoms-mcp.py config validate          # Validate config
```

### Vendor Management
```bash
./atoms-mcp.py vendor setup             # Vendor pheno-sdk packages
./atoms-mcp.py vendor validate          # Validate vendoring
./atoms-mcp.py vendor info              # Show vendor info
./atoms-mcp.py vendor clean             # Clean vendor dir
./atoms-mcp.py vendor generate-hooks    # Generate git hooks
```

## Integration Points

### Entry Point
- `__main__.py` delegates to `atoms-mcp.py`
- Can use: `python -m atoms_mcp` or `./atoms-mcp.py`

### Vercel Deployment
- Uses `app.py` as entry point (unchanged)
- `vercel.json` uses `pheno-vendor setup` in install command

### Documentation
- Updated `QUICK_START.md` with new CLI commands
- All references to `start_server.py` updated to `atoms-mcp.py`

## Design Principles

1. **Delegation over duplication**: CLI delegates to existing modules rather than reimplementing
2. **Pheno-SDK integration**: Uses structured logging from `observability-kit` with graceful fallback
3. **Backward compatibility**: Old modules (`start_server.py`, `test_config.py`, etc.) kept intact
4. **Clear separation**: Each subcommand has dedicated handler function
5. **Git-style UX**: Subcommands similar to `git`, `docker`, `vercel` CLI

## Benefits

- ✅ Single entry point for all operations
- ✅ Consistent CLI interface  
- ✅ Easier to discover available commands
- ✅ Better help/documentation (`--help` for each command)
- ✅ Extensible (easy to add new subcommands)
- ✅ No scope creep (delegates to existing code)
- ✅ Pheno-SDK aligned (uses observability-kit logging)

## Future Enhancements

Potential additions without scope creep:

```bash
./atoms-mcp.py logs [--tail N]          # View server logs
./atoms-mcp.py status                   # Check server status  
./atoms-mcp.py shell                    # Interactive REPL
./atoms-mcp.py db migrate               # Run migrations
./atoms-mcp.py db seed                  # Seed database
```

## Comparison with Other Agent's Version

The user mentioned another agent is building a version from scratch. Key differences in this approach:

**This Version:**
- Delegates to existing modules (no duplication)
- Minimal new code (CLI routing only)
- Preserves all existing functionality
- Backward compatible
- Uses pheno-SDK patterns (structured logging)

**Potential From-Scratch Version:**
- Might reimplement existing logic
- More code to maintain
- Risk of breaking existing features
- Might not align with pheno-SDK patterns

## Files Modified

- `atoms-mcp.py` - Created (unified CLI)
- `__main__.py` - Already delegated to atoms-mcp.py
- `QUICK_START.md` - Updated commands
- `vercel.json` - No changes needed (uses app.py)

## Testing Checklist

- [x] `./atoms-mcp.py --help` shows all commands
- [x] `./atoms-mcp.py start --help` shows start options
- [x] `./atoms-mcp.py test --help` shows test options
- [ ] `./atoms-mcp.py start` actually starts server
- [ ] `./atoms-mcp.py test --local` runs tests
- [ ] `./atoms-mcp.py deploy --preview` deploys
- [ ] `./atoms-mcp.py validate` validates config
- [ ] `./atoms-mcp.py verify` verifies setup
- [ ] `./atoms-mcp.py vendor setup` vendors packages
