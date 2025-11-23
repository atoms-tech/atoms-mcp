# Internal Developer Documentation Template
## For Atoms MCP Development Team

---

## 📄 DEVELOPMENT.md (Root Level)

```markdown
# Atoms MCP - Internal Development Guide

**For**: Internal development team only  
**Status**: Active development  
**Last Updated**: 2025-11-23

## Table of Contents
1. Getting Started
2. Architecture Overview
3. Development Setup
4. Code Organization
5. Testing
6. Deployment
7. Debugging
8. Performance
9. Security
10. Troubleshooting

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+ (for frontend)

### Quick Setup
```bash
# Clone repository
git clone https://github.com/atoms-tech/atoms-mcp.git
cd atoms-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python cli.py db migrate

# Start development server
python cli.py server start
```

## Architecture Overview

### System Components
1. **MCP Server** (server.py)
   - FastMCP-based server
   - Handles tool discovery and invocation
   - Manages authentication

2. **Tools** (tools/)
   - 5 consolidated tools
   - Tool implementations
   - Parameter validation

3. **Services** (services/)
   - Business logic layer
   - Entity, relationship, workflow, query services
   - Domain logic

4. **Infrastructure** (infrastructure/)
   - Database adapter (Supabase)
   - Auth provider (OAuth + Bearer)
   - Cache adapter (Redis)
   - Storage adapter

5. **Auth** (auth/)
   - Session management
   - Token validation
   - Middleware

### Data Flow
```
Agent Request
    ↓
MCP Server (tool discovery/invocation)
    ↓
Tool Handler (parameter validation)
    ↓
Service Layer (business logic)
    ↓
Infrastructure Adapters (external services)
    ↓
Response
```

## Development Setup

### IDE Setup
- **VSCode**: Install Python, Pylance, Pytest extensions
- **PyCharm**: Professional edition recommended
- **Vim**: Use coc-python or pyright

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Environment Variables
```
# Database
DATABASE_URL=postgresql://user:pass@localhost/atoms_mcp

# Redis
REDIS_URL=redis://localhost:6379

# Auth
WORKOS_API_KEY=...
WORKOS_CLIENT_ID=...

# OAuth
OAUTH_CLIENT_ID=...
OAUTH_CLIENT_SECRET=...

# Server
MCP_SERVER_NAME=atoms-mcp
MCP_SERVER_VERSION=1.0.0
```

## Code Organization

### Directory Structure
```
atoms-mcp/
├── server.py          # MCP server entry point
├── app.py             # ASGI app for serverless
├── tools/             # MCP tools
├── services/          # Business logic
├── infrastructure/    # Adapters
├── auth/              # Authentication
├── tests/             # Test suite
└── docs/              # Documentation
```

### Module Responsibilities
- **tools/**: Tool implementations (no business logic)
- **services/**: Business logic (no database access)
- **infrastructure/**: Database, auth, cache (adapters only)
- **auth/**: Session, tokens, middleware

## Testing

### Running Tests
```bash
# Unit tests
python cli.py test run --scope unit

# Integration tests
python cli.py test run --scope integration

# All tests with coverage
python cli.py test run --coverage

# Specific test
python cli.py test run tests/unit/test_entity.py
```

### Test Organization
- **unit/**: Fast, isolated tests (no external services)
- **integration/**: Slower, real services

### Writing Tests
```python
import pytest
from atoms_mcp import AtomsMCP

@pytest.mark.asyncio
async def test_entity_creation():
    """Test creating an entity."""
    client = AtomsMCP()
    result = await client.call_tool(
        "entity_operation",
        {"operation": "create", "entity_type": "document"}
    )
    assert result['success'] is True
    assert 'id' in result['data']
```

## Deployment

### Staging
```bash
# Deploy to staging
git push origin develop

# Staging URL: https://staging.atoms.io
```

### Production
```bash
# Create release
git tag v1.0.0
git push origin v1.0.0

# Production URL: https://api.atoms.io
```

### Monitoring
- Logs: CloudWatch
- Metrics: Datadog
- Errors: Sentry
- Performance: New Relic

## Debugging

### Local Debugging
```bash
# Enable debug logging
export DEBUG=1
python cli.py server start

# Use debugger
import pdb; pdb.set_trace()
```

### Remote Debugging
```bash
# SSH into server
ssh user@staging.atoms.io

# View logs
tail -f /var/log/atoms-mcp/server.log

# Check status
systemctl status atoms-mcp
```

## Performance

### Profiling
```bash
# Profile function
import cProfile
cProfile.run('function()')

# Memory profiling
pip install memory-profiler
python -m memory_profiler script.py
```

### Optimization Tips
- Use batch operations
- Cache frequently accessed data
- Use async/await properly
- Profile before optimizing

## Security

### Best Practices
- Never commit secrets
- Use environment variables
- Validate all inputs
- Use parameterized queries
- Implement rate limiting
- Log security events

### Security Checklist
- [ ] No hardcoded secrets
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] CORS configured
- [ ] Rate limiting enabled
- [ ] Audit logging enabled

## Troubleshooting

### Common Issues

**Database Connection Error**
```
Error: could not connect to server
Solution: Check DATABASE_URL, ensure PostgreSQL is running
```

**Redis Connection Error**
```
Error: Connection refused
Solution: Check REDIS_URL, ensure Redis is running
```

**Authentication Failure**
```
Error: Invalid token
Solution: Check token expiration, refresh token
```

### Getting Help
- Check logs: `tail -f logs/server.log`
- Check status: `python cli.py server status`
- Ask team: #dev-help Slack channel
```

---

## 📄 ARCHITECTURE.md (Root Level)

```markdown
# Atoms MCP - Architecture Overview

## System Design

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Agents (Claude, Cursor)              │
└────────────────────────┬────────────────────────────────┘
                         │
                    MCP Protocol
                         │
┌────────────────────────▼────────────────────────────────┐
│              Atoms MCP Server (FastMCP)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Tool Discovery & Invocation                     │  │
│  │  - workspace_operation                           │  │
│  │  - entity_operation                              │  │
│  │  - relationship_operation                        │  │
│  │  - workflow_execute                              │  │
│  │  - data_query                                    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    Services         Infrastructure    Auth
    ┌────────┐        ┌────────┐      ┌────────┐
    │Entity  │        │Database│      │OAuth   │
    │Rel.    │        │Cache   │      │Bearer  │
    │Workflow│        │Storage │      │Session │
    │Query   │        └────────┘      └────────┘
    └────────┘
        │
    ┌───┴────────────────────────────────┐
    │                                    │
┌───▼────┐                        ┌─────▼──┐
│Supabase│                        │ Redis  │
└────────┘                        └────────┘
```

### Component Responsibilities

**MCP Server**
- Tool discovery
- Tool invocation
- Parameter validation
- Response formatting

**Tools**
- Parameter validation
- Tool-specific logic
- Service orchestration

**Services**
- Business logic
- Data transformation
- Validation rules

**Infrastructure**
- Database operations
- Cache operations
- External service calls

**Auth**
- Token validation
- Session management
- Permission checking

## Data Flow

### Tool Invocation Flow
```
1. Agent calls tool
2. MCP Server receives request
3. Tool handler validates parameters
4. Service layer processes request
5. Infrastructure adapters execute
6. Response formatted and returned
```

### Authentication Flow
```
1. Agent authenticates (OAuth PKCE or Bearer token)
2. Auth provider validates credentials
3. Session created/validated
4. Token stored in session
5. Subsequent requests use token
```

## Performance Considerations

### Caching Strategy
- Cache frequently accessed entities
- Cache relationship graphs
- Cache search results
- TTL: 5 minutes default

### Database Optimization
- Index on entity_id, entity_type
- Index on relationships
- Batch operations for bulk updates
- Connection pooling

### Async/Await
- All I/O operations async
- Proper error handling
- Timeout management

## Security Model

### Authentication
- OAuth 2.0 PKCE flow
- Bearer token validation
- Session management
- Token refresh

### Authorization
- Role-based access control
- Resource-level permissions
- Audit logging

### Data Protection
- Encryption at rest
- Encryption in transit
- Input validation
- SQL injection prevention
```

---

## 📄 Module README Templates

Each module (tools/, services/, infrastructure/, auth/) should have README.md:

```markdown
# Module Name

Brief description of module.

## Components
- Component 1: Description
- Component 2: Description

## Architecture
[Diagram or description]

## Usage
```python
from module import component
result = component.function()
```

## Testing
```bash
python cli.py test run tests/unit/test_module.py
```

## Adding New Components
[Instructions]
```


