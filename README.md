# Atoms MCP Server
**Model Context Protocol server with entity management, workflows, and collaboration**

---

## 🎯 **OVERVIEW**

Atoms MCP is a production-ready MCP server providing:
- **Entity Management** - Create, manage, and query entities
- **Relationship Tracking** - Define and navigate entity relationships
- **Workflow Orchestration** - Automate multi-step processes
- **Workspace Collaboration** - Team collaboration features
- **Vector Search** - Semantic search with embeddings

### Key Features
- ✅ **OAuth 2.0 PKCE + DCR** - Standards-compliant authentication via WorkOS AuthKit
- ✅ **Stateless Architecture** - Serverless-ready, no session storage
- ✅ **Row-Level Security** - Fine-grained data access control
- ✅ **Pheno-SDK Integration** - Reusable components from pheno-sdk
- ✅ **Comprehensive Testing** - 18 test files with parallel execution

---

## 🚀 **QUICK START**

### 1. Setup
```bash
# Clone repository
git clone https://github.com/atoms-tech/atoms-mcp.git
cd atoms-mcp

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 2. Run Server Locally
```bash
# Start local server with CloudFlare tunnel (for OAuth)
python start_server.py

# Server runs on: http://localhost:50002
# Public URL (via tunnel): https://atomcp.kooshapari.com
# MCP Endpoint: https://atomcp.kooshapari.com/api/mcp
```

### 3. Run Tests
```bash
# Run unit tests
pytest -m unit

# Run integration tests (requires server running)
pytest -m integration

# Run all tests in parallel
pytest -n auto
```

**For complete setup instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

---

## 📚 **DOCUMENTATION**

### Essential Guides
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - 3-tier deployment workflow
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[WORKOS_SETUP.md](WORKOS_SETUP.md)** - WorkOS AuthKit configuration
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing documentation

### Additional Resources
- **[docs/REFERENCE.md](docs/REFERENCE.md)** - API reference
- **[examples/](examples/)** - Usage examples
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 🔧 **REQUIREMENTS**

- **Python 3.11+**
- **WorkOS Account** - For AuthKit authentication
- **Supabase Account** - For data storage
- **Google Cloud Account** (optional) - For Vertex AI embeddings

---

## 🔐 **AUTHENTICATION**

### Stateless AuthKit Architecture

**IMPORTANT:** Atoms MCP uses **WorkOS AuthKit ONLY** for authentication.

- ✅ **Authentication:** WorkOS AuthKit (OAuth 2.0 PKCE + DCR)
- ✅ **Data Storage:** Supabase PostgreSQL with RLS
- ❌ **NOT USED:** Supabase Auth/JWT for authentication

### Environment Variables

```bash
# WorkOS AuthKit (Required)
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-domain.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=http://localhost:8000
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email
WORKOS_API_KEY=sk_test_YOUR_API_KEY
WORKOS_CLIENT_ID=client_YOUR_CLIENT_ID

# Supabase (Required - Data Storage Only)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...your-service-role-key

# Optional: Vertex AI Embeddings
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**For complete configuration, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

---

## 🚢 **DEPLOYMENT**

### 3-Tier Deployment Model

The Atoms MCP server uses a streamlined 3-tier deployment model:

```
Local Development → Dev/Preview → Production
  (CloudFlare tunnel)   (Vercel)     (Vercel)
```

| Environment | Deployment Method | URL |
|-------------|------------------|-----|
| **Local** | `python start_server.py` | https://atomcp.kooshapari.com (via tunnel) |
| **Dev/Preview** | `git push origin feature-branch` | https://devmcp.atoms.tech |
| **Production** | `git push origin main` | https://atomcp.kooshapari.com |

### Quick Deployment

```bash
# Deploy to Dev (preview environment)
git push origin feature-branch
# → Vercel auto-deploys to devmcp.atoms.tech

# Deploy to Production
git push origin main
# → Vercel auto-deploys to atomcp.kooshapari.com
```

**For complete deployment guide, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

---

## 🧪 **TESTING**

### Quick Start - Fast Tests

```bash
# Run fast unit tests (<1s per test)
pytest -m unit

# Run all tests (unit + integration)
pytest -m "unit or integration"

# Run tests in parallel (faster)
pytest -n auto
```

### Test Against Environments

```bash
# Test local server
pytest --base-url=http://localhost:50002

# Test dev environment
pytest --base-url=https://devmcp.atoms.tech

# Test production (smoke tests only)
pytest -m "unit and not slow" --base-url=https://atomcp.kooshapari.com
```

**For complete testing documentation, see [TESTING_GUIDE.md](TESTING_GUIDE.md)**

---

## 🛠️ **MCP TOOLS**

### Entity Management
- `create_entity`, `get_entity`, `update_entity`, `delete_entity`, `list_entities`

### Relationship Management
- `create_relationship`, `get_relationships`, `delete_relationship`

### Workflow Orchestration
- `create_workflow`, `execute_workflow`, `get_workflow_status`

### Workspace Collaboration
- `create_workspace`, `add_workspace_member`, `list_workspaces`

### Query & Search
- `query_entities`, `vector_search`

**For complete API reference, see [docs/REFERENCE.md](docs/REFERENCE.md)**

---

## 📊 **PROJECT STATUS**

### Consolidation Complete ✅

- **164 files archived** - All redundant files preserved
- **68% reduction** in root directory files
- **36% reduction** in test files
- **Clean architecture** - Clear separation of concerns

**For detailed changes, see [CHANGELOG.md](CHANGELOG.md)**

---

## 🏗️ **ARCHITECTURE**

```
MCP Clients → FastMCP Server → WorkOS AuthKit → MCP Tools → Services → Supabase
```

**For detailed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)**

---

## 📖 **EXAMPLES**

- [Login Flow](examples/login_flow.md)
- [MCP Client Auth](examples/mcp_client_auth_flow.md)
- [OAuth DCR](examples/mcp_oauth_dcr_flow.md)

---

## 📝 **LICENSE**

MIT License

---

## 🔗 **LINKS**

- [WorkOS Dashboard](https://dashboard.workos.com)
- [Supabase Dashboard](https://supabase.com/dashboard)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)

---

**For support, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
