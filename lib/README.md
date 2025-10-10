# Atoms MCP Library

Lightweight utilities for Atoms MCP operations. These modules are designed to be:
1. **Minimal** - Keep code weight low in atoms_mcp-old
2. **Reusable** - Can be moved to pheno-sdk in the future
3. **Self-contained** - Minimal dependencies

## Structure

```
lib/
├── __init__.py          # Package exports
├── deployment.py        # Deployment utilities
└── README.md           # This file
```

## Modules

### `deployment.py`

Deployment utilities for local and Vercel deployments.

**Functions:**

#### `deploy_to_vercel(environment, project_root=None, logger=None)`

Deploy to Vercel with environment-specific configuration.

```python
from lib.deployment import deploy_to_vercel

# Deploy to preview
deploy_to_vercel("preview")

# Deploy to production
deploy_to_vercel("production")
```

**Parameters:**
- `environment` (str): "preview" or "production"
- `project_root` (Path, optional): Project root directory
- `logger` (optional): Logger instance (uses print if None)

**Returns:**
- `int`: 0 on success, 1 on failure

**Features:**
- Environment-specific configuration (.env.preview, .env.production)
- Vercel CLI integration
- Health check verification
- Deployment summary

#### `start_local_server(port=None, verbose=False, no_tunnel=False, logger=None)`

Start local server with KInfra tunnel.

```python
from lib.deployment import start_local_server

# Start with defaults
start_local_server()

# Start on custom port
start_local_server(port=50003, verbose=True)
```

**Parameters:**
- `port` (int, optional): Port to run on (default: 50002)
- `verbose` (bool): Enable verbose logging
- `no_tunnel` (bool): Disable CloudFlare tunnel
- `logger` (optional): Logger instance

**Returns:**
- `int`: Exit code from start_server.py

**Features:**
- Delegates to start_server.py
- KInfra tunnel integration
- CloudFlare HTTPS access

## Usage in atoms-mcp.py

The unified CLI uses these utilities:

```python
# In atoms-mcp.py
from lib.deployment import deploy_to_vercel, start_local_server

def cmd_start(args):
    return start_local_server(
        port=args.port,
        verbose=args.verbose,
        no_tunnel=args.no_tunnel,
        logger=logger
    )

def cmd_deploy(args):
    if args.local:
        return cmd_start(args)
    else:
        return deploy_to_vercel(
            environment="preview" if args.preview else "production",
            logger=logger
        )
```

## Migration to pheno-sdk

These utilities are designed to be easily moved to pheno-sdk/deploy-kit:

### Current Structure (atoms_mcp-old)
```
atoms_mcp-old/
├── lib/
│   ├── deployment.py
│   └── __init__.py
└── atoms-mcp.py (uses lib.deployment)
```

### Future Structure (pheno-sdk)
```
pheno-sdk/
└── deploy-kit/
    └── deploy_kit/
        ├── vercel.py          # deploy_to_vercel()
        ├── local.py           # start_local_server()
        └── __init__.py

atoms_mcp-old/
└── atoms-mcp.py (uses deploy_kit)
```

### Migration Steps

1. **Copy to pheno-sdk:**
   ```bash
   cp lib/deployment.py ../pheno-sdk/deploy-kit/deploy_kit/vercel.py
   ```

2. **Update imports in atoms-mcp.py:**
   ```python
   # Before
   from lib.deployment import deploy_to_vercel
   
   # After
   from deploy_kit import deploy_to_vercel
   ```

3. **Remove lib/ directory:**
   ```bash
   rm -rf lib/
   ```

## Design Principles

### 1. Minimal Dependencies

Only use standard library where possible:
- `subprocess` - For running commands
- `pathlib` - For path handling
- `time` - For delays
- `urllib` - For health checks

### 2. Logger Agnostic

Accept optional logger parameter, fall back to print:

```python
def log_info(msg):
    if logger:
        logger.info(msg)
    else:
        print(f"INFO: {msg}")
```

### 3. Self-Contained

Each function should work independently:
- No shared state
- Clear parameters
- Explicit returns

### 4. Delegation Over Duplication

Delegate to existing tools where possible:
- `start_local_server()` delegates to `start_server.py`
- `deploy_to_vercel()` uses Vercel CLI
- Don't reimplement what already works

## Benefits

### ✅ Reduced Code Weight
- Extracted deployment logic from start_server.py
- Reusable across CLI and other tools
- ~200 lines vs duplicated code

### ✅ Better Organization
- Clear separation of concerns
- Easy to find and maintain
- Testable in isolation

### ✅ Future-Proof
- Easy to move to pheno-sdk
- Minimal refactoring needed
- Clear migration path

### ✅ Consistent Interface
- Same functions work in CLI and programmatically
- Logger-agnostic design
- Standard return codes

## Testing

Test the library functions:

```python
# Test deployment
from lib.deployment import deploy_to_vercel

result = deploy_to_vercel("preview")
assert result == 0, "Deployment failed"

# Test local server
from lib.deployment import start_local_server

result = start_local_server(port=50003, no_tunnel=True)
assert result == 0, "Server start failed"
```

## Future Enhancements

Potential additions to this library:

- [ ] `lib/testing.py` - Test runner utilities
- [ ] `lib/config.py` - Configuration management
- [ ] `lib/validation.py` - Setup validation
- [ ] `lib/health.py` - Health check utilities
- [ ] `lib/metrics.py` - Metrics collection

Each should follow the same principles:
- Minimal dependencies
- Logger agnostic
- Self-contained
- Easy to migrate to pheno-sdk

