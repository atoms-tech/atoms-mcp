# Atoms MCP Configuration Guide

**Version:** 2.0  
**Date:** 2025-10-29  
**Status:** Production Ready

---

## Overview

Atoms MCP now supports **hybrid configuration** that automatically adapts to your environment:

- **Local Development:** Uses YAML files (`config.yml` + `secrets.yml`)
- **Vercel/Production:** Uses environment variables

This provides the best of both worlds: easy local development with YAML files, and secure production deployment with environment variables.

---

## Quick Start

### Local Development

```bash
# 1. Copy the secrets template
cp secrets.yml.example secrets.yml

# 2. Edit with your actual values
vim secrets.yml

# 3. Run the server
python atoms_server.py

# Configuration automatically loads from YAML files
```

### Vercel Deployment

```bash
# 1. Set environment variables in Vercel dashboard
ATOMS_SUPABASE_URL=https://your-project.supabase.co
ATOMS_SUPABASE_ANON_KEY=your-anon-key
ATOMS_DATABASE_URL=postgresql://...

# 2. Deploy
vercel deploy

# Configuration automatically loads from environment variables
```

---

## Configuration Files

### config.yml (Non-Sensitive Settings)

This file contains all non-sensitive application settings. It's safe to commit to git.

```yaml
# Application Settings
app:
  # Server configuration
  host: "localhost"
  port: 8080
  
  # MCP configuration
  mcp_server_name: "atoms-mcp"
  
  # Workspace configuration
  workspace_root: "~/atoms"
  
  # Feature flags
  enable_fastapi: true
  enable_supabase: true
  enable_google_ai: true
  enable_workos: true
  
  # Performance settings
  max_concurrent_requests: 100
  request_timeout: 30
  
  # Logging configuration
  log_level: "INFO"
  
  # Development settings
  debug: false
```

### secrets.yml (Sensitive Settings)

This file contains all sensitive configuration values. **NEVER commit to git.**

```yaml
# Supabase Configuration
supabase_url: "https://your-project.supabase.co"
supabase_anon_key: "your-anon-key-here"
supabase_service_key: "your-service-role-key-here"

# Database Configuration
database_url: "postgresql://user:password@host:port/database"

# Google AI Platform
google_ai_project: "your-gcp-project-id"
google_ai_credentials: |
  {
    "type": "service_account",
    "project_id": "your-project-id",
    ...
  }
google_ai_location: "us-central1"

# WorkOS Configuration
workos_client_id: "your-workos-client-id"
workos_api_key: "sk_live_your_api_key"
workos_webhook_secret: "your-webhook-secret"

# Authentication Secrets
jwt_secret: "your-jwt-secret-key-min-32-chars"
session_secret: "your-session-secret-key-min-32-chars"

# Webhook Configuration
webhook_secret: "your-webhook-signature-secret"
```

---

## Environment Variables

All settings can be overridden using environment variables with the `ATOMS_` prefix.

### Server Settings

```bash
ATOMS_HOST=localhost
ATOMS_PORT=8080
ATOMS_DEBUG=false
ATOMS_LOG_LEVEL=INFO
```

### MCP Settings

```bash
ATOMS_MCP_SERVER_NAME=atoms-mcp
ATOMS_WORKSPACE_ROOT=~/atoms
```

### Feature Flags

```bash
ATOMS_ENABLE_FASTAPI=true
ATOMS_ENABLE_SUPABASE=true
ATOMS_ENABLE_GOOGLE_AI=true
ATOMS_ENABLE_WORKOS=true
```

### Performance Settings

```bash
ATOMS_MAX_CONCURRENT_REQUESTS=100
ATOMS_REQUEST_TIMEOUT=30
```

### Supabase Settings

```bash
ATOMS_SUPABASE_URL=https://your-project.supabase.co
ATOMS_SUPABASE_ANON_KEY=your-anon-key
ATOMS_SUPABASE_SERVICE_KEY=your-service-role-key
```

### Database Settings

```bash
ATOMS_DATABASE_URL=postgresql://user:password@host:port/database
```

### Google AI Settings

```bash
ATOMS_GOOGLE_AI_PROJECT=your-gcp-project-id
ATOMS_GOOGLE_AI_CREDENTIALS='{"type":"service_account",...}'
ATOMS_GOOGLE_AI_LOCATION=us-central1
```

### WorkOS Settings

```bash
ATOMS_WORKOS_CLIENT_ID=your-workos-client-id
ATOMS_WORKOS_API_KEY=sk_live_your_api_key
ATOMS_WORKOS_WEBHOOK_SECRET=your-webhook-secret
```

### Authentication Settings

```bash
ATOMS_JWT_SECRET=your-jwt-secret-key-min-32-chars
ATOMS_SESSION_SECRET=your-session-secret-key-min-32-chars
```

---

## How It Works

### Automatic Environment Detection

The configuration system automatically detects your environment:

```python
from settings.combined import AtomsSettings

# Automatically detects environment and loads appropriate config
settings = AtomsSettings()

# Check which source was used
print(settings.source)  # "yaml" or "environment"
```

### Environment Detection Logic

```python
def is_vercel_environment() -> bool:
    """Check if running in Vercel environment."""
    return bool(os.getenv('VERCEL') or os.getenv('VERCEL_ENV'))
```

If `VERCEL` or `VERCEL_ENV` environment variables are set, configuration loads from environment variables. Otherwise, it loads from YAML files.

### Manual Override (for Testing)

```python
# Force YAML loading (for testing)
settings = AtomsSettings(force_yaml=True)

# Force environment loading (for testing)
settings = AtomsSettings(force_env=True)
```

---

## Usage Examples

### Basic Usage

```python
from settings.combined import get_settings

# Get settings instance
settings = get_settings()

# Access app settings
print(settings.app.host)
print(settings.app.port)
print(settings.app.debug)

# Access secrets (if configured)
if settings.secrets.has_supabase_config():
    supabase_url = settings.secrets.get_supabase_url()
    supabase_key = settings.secrets.get_supabase_anon_key()
```

### Server Configuration

```python
from settings.combined import get_settings

settings = get_settings()

# Get server configuration
server_config = settings.get_server_config()
# Returns: {'host': 'localhost', 'port': 8080, 'url': 'http://localhost:8080'}

# Get MCP configuration
mcp_config = settings.get_mcp_config()
# Returns: {'name': 'atoms-mcp', 'server_url': 'http://localhost:8080'}
```

### Database Configuration

```python
from settings.combined import get_settings

settings = get_settings()

# Get database URL
db_url = settings.get_database_config()
# Returns: "postgresql://..." or "sqlite://atoms.db" (default)
```

### Integration Configuration

```python
from settings.combined import get_settings

settings = get_settings()

# Get Supabase configuration
supabase_config = settings.get_supabase_config()
if supabase_config:
    print(f"Supabase URL: {supabase_config['url']}")
    print(f"Anon Key: {supabase_config['anon_key']}")

# Get Google AI configuration
google_config = settings.get_google_ai_config()
if google_config:
    print(f"Project: {google_config['project']}")
    print(f"Location: {google_config['location']}")

# Get WorkOS configuration
workos_config = settings.get_workos_config()
if workos_config:
    print(f"Client ID: {workos_config['client_id']}")
```

### Safe Serialization

```python
from settings.combined import get_settings

settings = get_settings()

# Get safe dictionary (no secrets exposed)
safe_dict = settings.to_dict_safe()
print(safe_dict)
# Returns:
# {
#   'app': {...},
#   'has_secrets': {
#     'supabase': True,
#     'google_ai': True,
#     'workos': True,
#     ...
#   },
#   'features': {
#     'fastapi': True,
#     'supabase': True,
#     ...
#   }
# }
```

---

## Migration Guide

### From Old Configuration

If you're migrating from the old configuration system:

1. **Copy your existing settings:**
   ```bash
   # Backup old config
   cp atoms.config.yaml atoms.config.yaml.backup
   cp atoms.secrets.yaml atoms.secrets.yaml.backup
   ```

2. **Create new config.yml:**
   ```bash
   # Use the new structure
   cp config.yml.example config.yml
   # Edit with your settings
   vim config.yml
   ```

3. **Create new secrets.yml:**
   ```bash
   # Use the template
   cp secrets.yml.example secrets.yml
   # Copy your secrets from old atoms.secrets.yaml
   vim secrets.yml
   ```

4. **Test the configuration:**
   ```bash
   python test_hybrid_config.py
   ```

5. **Update your code (if needed):**
   ```python
   # Old way (still works!)
   from config.settings import get_settings
   settings = get_settings()
   
   # New way (recommended)
   from settings.combined import get_settings
   settings = get_settings()
   ```

---

## Security Best Practices

### 1. Never Commit Secrets

```bash
# Ensure secrets.yml is in .gitignore
echo "secrets.yml" >> .gitignore
echo ".secrets.yml" >> .gitignore
```

### 2. Use SecretStr for Sensitive Values

The configuration system automatically uses `SecretStr` for sensitive values, preventing accidental logging:

```python
# Secrets are protected
print(settings.secrets.supabase_anon_key)
# Output: SecretStr('**********')

# Get actual value when needed
actual_key = settings.secrets.get_supabase_anon_key()
```

### 3. Use Environment Variables in Production

For production deployments (Vercel, Docker, etc.), always use environment variables instead of YAML files.

### 4. Rotate Secrets Regularly

Update your secrets regularly and never reuse secrets across environments.

---

## Troubleshooting

### Configuration Not Loading

```python
# Check which source is being used
from settings.combined import get_settings
settings = get_settings()
print(f"Configuration source: {settings.source}")
```

### Missing Secrets

```python
# Check if secrets are configured
from settings.combined import get_settings
settings = get_settings()

if not settings.secrets.has_supabase_config():
    print("Supabase not configured")
    
if not settings.secrets.has_google_ai_config():
    print("Google AI not configured")
```

### Validation Errors

```python
# Pydantic will raise validation errors for invalid values
try:
    from settings.app import AppSettings
    settings = AppSettings(port=99999)
except ValueError as e:
    print(f"Validation error: {e}")
    # Output: Port must be between 1 and 65535
```

---

## Testing

### Run Configuration Tests

```bash
# Run the comprehensive test suite
python test_hybrid_config.py

# Expected output:
# ✅ Local YAML loading
# ✅ Environment variable loading
# ✅ Vercel environment detection
# ✅ Automatic environment selection
# ✅ Settings validation
# ✅ Convenience methods
```

### Test Specific Scenarios

```python
# Test YAML loading
from settings.combined import AtomsSettings
settings = AtomsSettings(force_yaml=True)
assert settings.source == "yaml"

# Test environment loading
settings = AtomsSettings(force_env=True)
assert settings.source == "environment"
```

---

## FAQ

### Q: Can I use both YAML and environment variables?

A: Environment variables always take precedence over YAML values when using pydantic-settings.

### Q: What happens if secrets.yml is missing?

A: The system will still work, but integrations requiring secrets will be disabled. Check `settings.is_configured()` to verify.

### Q: Can I use this in Docker?

A: Yes! Set environment variables in your Dockerfile or docker-compose.yml, and the system will automatically use them.

### Q: How do I add a new setting?

A: Add it to `settings/app.py` (non-sensitive) or `settings/secrets.py` (sensitive), then update `config.yml` or `secrets.yml.example`.

---

## Support

For issues or questions:
1. Check this guide
2. Run `python test_hybrid_config.py`
3. Check the logs for configuration errors
4. Review `settings/combined.py` for implementation details

---

**End of Configuration Guide**

