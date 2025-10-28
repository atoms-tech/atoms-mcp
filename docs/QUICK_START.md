# Atoms MCP - Quick Start Guide

Get up and running with Atoms MCP in 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Supabase account and project
- WorkOS account (for authentication)

## 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd atoms-mcp-prod

# Install dependencies
uv sync

# Or with pip
pip install -e .
```

## 2. Environment Setup

Create a `.env` file in the project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_PROJECT_ID=your-project-id

# WorkOS Configuration (for authentication)
WORKOS_API_KEY=your-workos-api-key
WORKOS_CLIENT_ID=your-workos-client-id
WORKOS_REDIRECT_URI=http://localhost:8000/auth/complete

# Server Configuration
ATOMS_BASE_URL=http://localhost:8000
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_HOST=127.0.0.1
ATOMS_FASTMCP_PORT=8000
```

## 3. Start the Server

```bash
# Start the server
python -m server

# Or use the CLI shortcut
./atoms start
```

You should see output like:
```
🚀 Atoms MCP Server Starting
============================================================
   Host: 127.0.0.1
   Port: 8000
   Path: /api/mcp
============================================================

✅ Server started successfully
```

## 4. Test the Server

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "atoms-mcp",
  "version": "1.0.0"
}
```

### Service Information
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "service": "Atoms MCP Server",
  "version": "1.0.0",
  "endpoints": {
    "mcp": "/api/mcp",
    "health": "/health",
    "auth_start": "/auth/start",
    "auth_complete": "/auth/complete"
  },
  "status": "running"
}
```

## 5. Authentication

### Get Authentication Token

1. **Start OAuth Flow:**
```bash
curl -X POST http://localhost:8000/auth/start
```

2. **Complete Authentication:**
```bash
curl -X POST http://localhost:8000/auth/complete \
  -H "Content-Type: application/json" \
  -d '{"code": "your-auth-code", "state": "state-value"}'
```

3. **Use the returned token in subsequent requests:**
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"tool": "workspace_operation", "parameters": {...}}'
```

## 6. Your First API Call

Let's create a simple project:

```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "entity_operation",
    "parameters": {
      "operation": "create",
      "entity_type": "project",
      "data": {
        "name": "My First Project",
        "description": "Learning Atoms MCP",
        "organization_id": "your-org-id"
      }
    }
  }'
```

Expected response:
```json
{
  "success": true,
  "data": {
    "id": "proj-123",
    "name": "My First Project",
    "description": "Learning Atoms MCP",
    "organization_id": "your-org-id",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

## 7. Explore the Tools

### Create a Requirement
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "entity_operation",
    "parameters": {
      "operation": "create",
      "entity_type": "requirement",
      "data": {
        "title": "User Login",
        "description": "Users must be able to log in securely",
        "project_id": "proj-123",
        "priority": "high"
      }
    }
  }'
```

### Search for Content
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "data_query",
    "parameters": {
      "query_type": "search",
      "entities": ["requirement", "project"],
      "search_term": "login",
      "limit": 10
    }
  }'
```

### Run a Workflow
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "workflow_execute",
    "parameters": {
      "workflow": "setup_project",
      "parameters": {
        "name": "Complete Project Setup",
        "organization_id": "your-org-id",
        "description": "Automated project setup with requirements and tests"
      }
    }
  }'
```

## 8. Next Steps

### Learn More
- Read the [User Guide](USER_GUIDE.md) for detailed usage
- Check the [API Reference](API_REFERENCE.md) for all available tools
- Explore the [Developer Guide](DEVELOPER_GUIDE.md) for contributing

### Common Tasks

**List all projects:**
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "entity_operation",
    "parameters": {
      "operation": "list",
      "entity_type": "project",
      "limit": 20
    }
  }'
```

**Get project details:**
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "entity_operation",
    "parameters": {
      "operation": "read",
      "entity_type": "project",
      "entity_id": "proj-123"
    }
  }'
```

**Update a requirement:**
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "entity_operation",
    "parameters": {
      "operation": "update",
      "entity_type": "requirement",
      "entity_id": "req-456",
      "data": {
        "status": "completed",
        "notes": "Implemented and tested"
      }
    }
  }'
```

## Troubleshooting

### Common Issues

**1. "Authentication required" error**
- Make sure you have a valid Bearer token
- Check that the token is in the Authorization header

**2. "Entity not found" error**
- Verify the entity ID exists
- Check that you have permission to access the entity

**3. "Rate limit exceeded" error**
- Wait a moment before making more requests
- The limit is 120 requests per minute

**4. Server won't start**
- Check that all environment variables are set
- Verify Supabase and WorkOS credentials
- Check that port 8000 is available

### Getting Help

- Check the server logs for detailed error messages
- Review the [API Reference](API_REFERENCE.md) for parameter details
- See the [User Guide](USER_GUIDE.md) for comprehensive examples

### Debug Mode

Enable debug logging:
```bash
export ATOMS_LOG_LEVEL=DEBUG
python -m server
```

## Production Deployment

### Deploy to Vercel

1. **Connect your repository to Vercel**
2. **Set environment variables in Vercel dashboard**
3. **Deploy automatically on git push**

### Environment Variables for Production

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
WORKOS_API_KEY=your-workos-api-key
WORKOS_CLIENT_ID=your-workos-client-id
WORKOS_REDIRECT_URI=https://your-domain.com/auth/complete
ATOMS_BASE_URL=https://your-domain.com
```

### Health Monitoring

The server provides health check endpoints:
- `GET /health` - Basic health check
- `GET /` - Service information

Use these for monitoring and load balancer health checks.

## CLI Shortcuts

The project includes convenient CLI shortcuts:

```bash
# Start local server
./atoms start

# Deploy to production
./atoms deploy

# Deploy to development
./atoms deploy dev

# Run tests
./atoms test local cold

# Code statistics
./atoms stats cloc

# Check for unused code
./atoms stats vulture
```

## What's Next?

Now that you have Atoms MCP running, you can:

1. **Create your first project** and start adding requirements
2. **Set up test cases** and link them to requirements
3. **Use RAG search** to find relevant content across your knowledge base
4. **Run workflows** to automate complex multi-step processes
5. **Integrate with your existing tools** using the MCP protocol

Happy building! 🚀