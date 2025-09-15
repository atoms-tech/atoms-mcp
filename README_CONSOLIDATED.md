# Atoms FastMCP - Consolidated Agent-Optimized Tools

This refactored version of atoms_fastmcp transforms the original 100+ individual tools into 5 intelligent, agent-optimized tools while maintaining full backward compatibility.

## Architecture Overview

### Infrastructure Abstraction Layer
- **Adapters**: Abstract interfaces for auth, database, storage, and realtime services
- **Supabase Implementation**: Current implementation using Supabase
- **Future Ready**: Easy to swap for .NET, microservices, or hybrid architectures
- **Environment Detection**: Automatic adapter selection based on `ATOMS_BACKEND_TYPE`

### Consolidated Tools
1. **workspace_operation**: Context management and smart defaults
2. **entity_operation**: Unified CRUD for all entity types
3. **relationship_operation**: Manage entity associations
4. **workflow_execute**: Complex multi-step operations
5. **data_query**: Data exploration and analysis

### Authentication
- **Bearer Auth (Recommended)**: Validates Supabase JWTs using auth/v1/user endpoint
- **JWT Verification**: Direct Supabase JWT verification with JWKS endpoint  
- **Development Mode**: Disabled auth mode for development/testing
- **Simple Integration**: Works seamlessly with existing Supabase frontend authentication

## Usage

### Environment Variables
```bash
# Backend type (default: supabase)
ATOMS_BACKEND_TYPE=supabase

# Server mode (default: consolidated)
ATOMS_FASTMCP_MODE=consolidated  # or "legacy" or "compatible"

# Authentication mode (default: bearer)
ATOMS_FASTMCP_AUTH_MODE=bearer   # "bearer", "jwt", or "disabled"

# Transport (default: stdio)
ATOMS_FASTMCP_TRANSPORT=stdio  # or "http"

# Supabase configuration (required for bearer and JWT auth)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_key
```

### Running the Server

```bash
# Bearer Auth mode (recommended - validates tokens via Supabase auth/v1/user)
python -m atoms_fastmcp.new_server

# JWT authentication mode (validates JWTs via JWKS endpoint)
ATOMS_FASTMCP_AUTH_MODE=jwt python -m atoms_fastmcp.new_server

# Development mode with authentication disabled
ATOMS_FASTMCP_AUTH_MODE=disabled python -m atoms_fastmcp.new_server

# Legacy compatibility mode (includes both new and legacy tools)
python -m atoms_fastmcp.legacy.wrapper
```

## Authentication Setup Guide

### Supabase Bearer Authentication (Recommended)

The Bearer Auth mode validates Supabase JWTs by calling the `auth/v1/user` endpoint. This is the correct approach for Supabase integration since Supabase doesn't expose native OAuth 2.1 endpoints.

#### How It Works
1. **Frontend Login**: User authenticates with Supabase in your frontend application
2. **JWT Extraction**: Frontend extracts the JWT from Supabase session 
3. **Token Validation**: FastMCP server validates the JWT by calling Supabase's `auth/v1/user` endpoint
4. **Access Granted**: If valid, user information is extracted and access is granted

#### Setup Steps

1. **Configure Environment Variables**
```bash
# Default bearer mode
ATOMS_FASTMCP_AUTH_MODE=bearer

# Required Supabase configuration  
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key  # Optional but recommended
```

2. **Frontend Integration**
```javascript
// Get JWT from Supabase session
const { data: { session } } = await supabase.auth.getSession()
const jwt_token = session?.access_token

// Pass to MCP tools
const result = await entity_operation({
  auth_token: jwt_token,
  operation: "list",
  entity_type: "project"
})
```

3. **Validation Process**
The server automatically:
- Receives the Bearer token from the `Authorization: Bearer <token>` header
- Makes a request to `{SUPABASE_URL}/auth/v1/user` with the token
- Returns user information if token is valid
- Provides user ID, email, and metadata to your tools

#### No Additional Supabase Configuration Required
Unlike traditional OAuth setups, Bearer Auth works immediately with any Supabase project. No redirect URIs, client secrets, or dashboard configuration needed.

### Authentication Mode Comparison

| Feature | Bearer Auth | JWT Verification | Disabled |
|---------|-------------|------------------|----------|
| **Setup Complexity** | 🟢 Simple | 🟢 Simple | 🟢 None |
| **Supabase Integration** | ✅ Native auth/v1/user | ✅ JWKS validation | ❌ No auth |
| **User Information** | ✅ Full user data | ✅ JWT claims only | ❌ None |
| **Real-time Validation** | ✅ Always current | ⚠️ Until JWT expires | ❌ None |
| **Configuration Required** | ❌ None | ❌ None | ❌ None |
| **Production Ready** | ✅ Yes | ✅ Yes | ❌ Development only |

## Tool Examples

### 1. Workspace Management

```python
# Get current context
workspace_operation(
    auth_token="your_jwt_or_session_token",
    operation="get_context"
)

# Set active project
workspace_operation(
    auth_token="token",
    operation="set_context",
    context_type="project",
    entity_id="proj_123"
)

# List available workspaces
workspace_operation(
    auth_token="token", 
    operation="list_workspaces"
)
```

### 2. Entity Operations

```python
# Create project with smart defaults
entity_operation(
    auth_token="token",
    operation="create",
    entity_type="project",
    data={
        "name": "My Project",
        "organization_id": "auto"  # Uses workspace context
    }
)

# List requirements for a document
entity_operation(
    auth_token="token",
    operation="list", 
    entity_type="requirement",
    parent_type="document",
    parent_id="doc_123"
)

# Search across projects
entity_operation(
    auth_token="token",
    operation="search",
    entity_type="project",
    search_term="api",
    limit=10
)

# Batch create requirements
entity_operation(
    auth_token="token",
    operation="create",
    entity_type="requirement",
    batch=[
        {"name": "REQ-1", "document_id": "doc_123"},
        {"name": "REQ-2", "document_id": "doc_123"}
    ]
)
```

### 3. Relationship Management

```python
# Add user to organization
relationship_operation(
    auth_token="token",
    operation="link",
    relationship_type="member",
    source={"type": "organization", "id": "org_123"},
    target={"type": "user", "id": "user_456"},
    metadata={"role": "admin"}
)

# List project members
relationship_operation(
    auth_token="token",
    operation="list",
    relationship_type="member",
    source={"type": "project", "id": "proj_123"}
)

# Link requirement to test
relationship_operation(
    auth_token="token",
    operation="link",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req_123"},
    target={"type": "test", "id": "test_456"},
    metadata={"coverage_level": "full"}
)
```

### 4. Workflow Execution

```python
# Setup new project with structure
workflow_execute(
    auth_token="token",
    workflow="setup_project",
    parameters={
        "name": "My New Project",
        "organization_id": "org_123",
        "initial_documents": ["Requirements", "Design"],
        "add_creator_as_admin": True
    }
)

# Import requirements from external source
workflow_execute(
    auth_token="token",
    workflow="import_requirements",
    parameters={
        "document_id": "doc_123",
        "requirements": [
            {"name": "REQ-1", "description": "User login"},
            {"name": "REQ-2", "description": "Data validation"}
        ]
    }
)

# Bulk status update
workflow_execute(
    auth_token="token",
    workflow="bulk_status_update",
    parameters={
        "entity_type": "requirement",
        "entity_ids": ["req_1", "req_2", "req_3"],
        "new_status": "approved"
    }
)
```

### 5. Data Query and Analysis

```python
# Search across multiple entity types
data_query(
    auth_token="token",
    query_type="search",
    entities=["project", "document", "requirement"],
    search_term="authentication"
)

# Get aggregate statistics
data_query(
    auth_token="token",
    query_type="aggregate",
    entities=["organization", "project"],
    conditions={"is_deleted": False}
)

# Deep analysis of requirements
data_query(
    auth_token="token", 
    query_type="analyze",
    entities=["requirement"],
    conditions={"status": "active"}
)

# Relationship analysis
data_query(
    auth_token="token",
    query_type="relationships",
    entities=["organization", "project", "user"]
)
```

## Migration Guide

### From Legacy Tools

#### Old Approach (100+ tools):
```python
# Multiple tool calls required
organizations = list_organizations(session_token="token")
projects = list_projects_by_org(session_token="token", organization_id="org_123")
documents = list_documents(session_token="token", project_id="proj_456")
requirements = list_requirements_by_document(session_token="token", document_id="doc_789")
```

#### New Approach (1 tool):
```python
# Single tool with intelligent parameters
entity_operation(
    auth_token="token",
    operation="list",
    entity_type="requirement", 
    parent_type="document",
    parent_id="doc_789",
    include_relations=True  # Includes related data
)
```

### Authentication Migration

#### Legacy: Multiple Authentication Approaches
```python
# Old system used session tokens from login endpoints
session_token = "legacy_session_token"
result = legacy_tool(session_token=session_token, ...)
```

#### New: Unified JWT Authentication
```python
# Frontend gets Supabase JWT from authentication
const { data: { session } } = await supabase.auth.getSession()
const jwt_token = session?.access_token

# Pass JWT directly to all tools
result = entity_operation(auth_token=jwt_token, ...)

# Development mode (no auth required)
result = entity_operation(auth_token="any_value", ...)  # When ATOMS_FASTMCP_AUTH_MODE=disabled
```

## Benefits

1. **Agent Optimization**: 
   - Fewer tools to learn and manage
   - More intuitive, higher-level operations
   - Smart defaults and context awareness

2. **Performance**:
   - Batch operations reduce round trips
   - Context caching improves efficiency
   - Parallel execution for workflows

3. **Maintainability**:
   - Centralized business logic
   - Consistent error handling
   - Easier testing and debugging

4. **Extensibility**:
   - Infrastructure abstraction layer
   - Easy to add new backends
   - Workflow system for complex operations

5. **Backward Compatibility**:
   - Legacy tools still available
   - Gradual migration path
   - Compatible mode for transition

## Testing

Run the test suite:
```bash
python atoms_fastmcp/test_consolidated.py
```

## Architecture Decisions

### Why 5 Tools Instead of 100+?

1. **Cognitive Load**: Agents can better understand and use 5 intelligent tools vs 100+ specific ones
2. **Flexibility**: Each tool handles multiple related operations with smart parameters
3. **Context**: Tools share context and can make intelligent defaults
4. **Transactions**: Workflows can span multiple operations atomically
5. **Analysis**: Query tool provides data exploration capabilities

### Why Infrastructure Abstraction?

1. **Future Proofing**: Easy migration to .NET or other backends
2. **Testing**: Mock adapters for unit testing
3. **Hybrid Architectures**: Mix and match services (e.g., Supabase auth + .NET API)
4. **Performance**: Adapter-specific optimizations

### Why Maintain Legacy Compatibility?

1. **Migration**: Existing integrations continue working
2. **Gradual Adoption**: Teams can migrate incrementally 
3. **Fallback**: Safety net during transition
4. **Documentation**: Examples of mapping old to new patterns

## Next Steps

1. **Test with Real Data**: Configure Supabase and test with actual database
2. **Frontend Integration**: Update frontend to use new consolidated tools
3. **Performance Tuning**: Optimize adapters and add caching
4. **.NET Backend**: Implement .NET adapters when ready
5. **Deprecation**: Plan timeline for removing legacy tools