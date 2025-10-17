# Quick Start - Modernized Atoms MCP

## Installation

```bash
# Clone repository
git clone <repo-url>
cd atoms-mcp-prod

# Install with UV (recommended - 10-100x faster)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Configuration

### Default Configuration

All settings are defined in `config/config.yaml`:

```yaml
# config/config.yaml
server:
  port: 8000
  host: "127.0.0.1"
  transport: "http"

kinfra:
  enabled: true
  preferred_port: 8100

features:
  enable_rag: true
  enable_vector_search: true
```

### Environment Variables

Override any setting:

```bash
# Server
export PORT=9000
export HOST=0.0.0.0

# KINFRA
export KINFRA_ENABLED=false
export KINFRA_PREFERRED_PORT=8200

# Logging
export LOG_LEVEL=DEBUG

# Features
export FEATURES_ENABLE_RAG=false
```

### Custom Config File

```bash
# Use custom YAML
export ATOMS_SETTINGS_FILE=/path/to/my-config.yaml

# Start server
python -m atoms_cli
```

## Usage in Code

```python
from config.settings import get_settings

# Load settings (cached singleton)
settings = get_settings()

# Access nested settings
port = settings.server.port
kinfra_enabled = settings.kinfra.enabled
rag_enabled = settings.features.enable_rag

# Check database configuration
if settings.database.supabase.is_configured:
    url = settings.database.supabase.url
```

## Development

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update to latest versions
pre-commit autoupdate
```

### Linting & Formatting

```bash
# Check code with ruff
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Or use tox
tox -e lint
tox -e lint-fix
```

### Type Checking

```bash
# Check types with zuban
zuban .

# Or use tox
tox -e typecheck
```

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=lib --cov=tools --cov=config

# Or use tox
tox -e py311
tox -e coverage
```

### Security Checks

```bash
# Security scanning
tox -e security

# Individual tools
bandit -r lib tools config
safety check
pip-audit
```

### Code Quality

```bash
# Code quality metrics
tox -e quality

# Individual tools
radon cc lib tools config -a
vulture lib tools config
```

## Production Deployment

### Environment Setup

```bash
# Set production environment
export ENV=production

# Configure secrets (required)
export SUPABASE_SERVICE_ROLE_KEY=<key>
export WORKOS_API_KEY=<key>
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Optional overrides
export PORT=8080
export LOG_LEVEL=INFO
```

### Docker Build

```bash
# Build image (uses .dockerignore)
docker build -t atoms-mcp:latest .

# Run container
docker run -p 8000:8000 \
  -e SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY \
  -e WORKOS_API_KEY=$WORKOS_API_KEY \
  atoms-mcp:latest
```

### Vercel Deployment

```bash
# Deploy to Vercel
vercel deploy --prod

# Environment variables set via Vercel dashboard
```

## Verification

```bash
# Run verification script
python3 verify_modernization.py

# Should output:
# ✅ All verification checks passed!
```

## Tools & Commands

### Tox Environments

```bash
tox -e py311        # Unit tests
tox -e lint         # Linting
tox -e lint-fix     # Auto-fix linting
tox -e typecheck    # Type checking
tox -e security     # Security checks
tox -e docs         # Docstring coverage
tox -e quality      # Code quality
tox -e coverage     # Coverage with threshold
tox -e integration  # Integration tests
tox -e perf         # Performance benchmarks
tox -e build        # Build distribution
tox -e clean        # Clean artifacts
```

### Direct Tools

```bash
# Ruff (linter + formatter)
ruff check .
ruff check --fix .
ruff format .

# Zuban (type checker)
zuban .

# Pytest (testing)
pytest
pytest -v
pytest --cov

# Coverage (detailed reports)
coverage run -m pytest
coverage report
coverage html

# Bandit (security)
bandit -r lib tools config

# Vulture (dead code)
vulture lib tools config

# Radon (complexity)
radon cc lib tools config
```

## File Structure

```
atoms-mcp-prod/
├── config/
│   ├── schema.yaml        # Settings schema (documentation)
│   ├── config.yaml        # Default configuration
│   └── settings.py        # Pydantic settings models
├── pyproject.toml         # Project + tool configuration
├── tox.ini                # Test automation
├── .pre-commit-config.yaml # Pre-commit hooks
├── .gitignore             # Git ignore patterns
├── .dockerignore          # Docker ignore patterns
├── .clocignore            # CLOC ignore patterns
├── .vultureignore         # Vulture ignore patterns
├── .pylintignore          # Pylint ignore patterns
└── verify_modernization.py # Verification script
```

## Settings Priority

Settings are loaded in this order (later sources override earlier):

1. YAML defaults (`config/config.yaml`)
2. Environment variables
3. `.env` files
4. Programmatic overrides

## Common Tasks

### Add New Setting

1. Update `config/schema.yaml` (documentation)
2. Update `config/config.yaml` (default value)
3. Add field to appropriate Settings class in `config/settings.py`
4. Use in code: `settings.category.field_name`

### Change Default Value

1. Update `config/config.yaml`
2. Restart application (settings are cached)

### Override for Development

```bash
# Create .env.local
echo "DEBUG=true" >> .env.local
echo "LOG_LEVEL=DEBUG" >> .env.local
echo "PORT=9000" >> .env.local
```

### Override for Production

```bash
# Set via environment
export ENV=production
export LOG_LEVEL=INFO
export PORT=8080
```

## Troubleshooting

### Settings Not Loading

```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# Test settings load
python3 -c "from config.settings import get_settings; settings = get_settings(); print(settings)"
```

### Import Errors

```bash
# Reinstall in development mode
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

### Pre-commit Hook Failures

```bash
# Auto-fix issues
pre-commit run --all-files

# Or manually fix
ruff check --fix .
ruff format .
```

## Best Practices

1. **Never commit secrets** - Use environment variables
2. **Use type hints** - Enables IDE autocomplete
3. **Run pre-commit hooks** - Catches issues early
4. **Test before commit** - Run `tox` or `pytest`
5. **Document changes** - Update schema.yaml
6. **Use settings** - Don't hardcode values
7. **Validate config** - Run verification script

## Resources

- Settings Schema: `config/schema.yaml`
- Default Config: `config/config.yaml`
- Tool Config: `pyproject.toml`
- Test Config: `tox.ini`
- Verification: `python3 verify_modernization.py`
- Documentation: `MODERNIZATION_COMPLETE.md`
