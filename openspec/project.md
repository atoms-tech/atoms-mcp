# Project Context

## Purpose

**Atoms MCP Server** is a FastMCP-based Model Context Protocol server that provides comprehensive access to the Atoms platform API domains. It serves as the bridge between AI coding assistants (like Claude Code, Cursor, GitHub Copilot) and the Atoms knowledge management system.

**Key Goals:**
- Provide **5 consolidated high-level tools** that abstract away 80+ granular API endpoints
- Enable **authentication-first** operations via OAuth 2.0 PKCE + Dynamic Client Registration
- Support **dual deployment modes**: STDIO (local development) and HTTP (production/serverless)
- Maintain **stateless serverless compatibility** for Vercel/AWS Lambda deployments
- Ensure **production-grade quality**: full test coverage, comprehensive error handling, observability

## Tech Stack

### Core Framework
- **Python 3.12** (exact version requirement)
- **FastMCP 2.12+** - Model Context Protocol framework (canonical authority: `llms-full.txt`)
- **uv** - Package manager and task runner (preferred over pip)

### Database & Storage
- **Supabase** - PostgreSQL database with Row Level Security (RLS)
- **supabase-pydantic** - Schema generation and validation
- **Upstash Redis** - Serverless-compatible distributed caching and rate limiting

### Authentication & Security
- **WorkOS AuthKit** - OAuth 2.0 PKCE + Dynamic Client Registration
- **PyJWT** - JWT token handling
- **cryptography** - Cryptographic operations

### AI/ML
- **Google Vertex AI** (via REST API) - Lightweight embedding generation for semantic search
- **google-auth** - Google Cloud authentication

### HTTP & Async
- **aiohttp** - Async HTTP client
- **httpx** - Modern HTTP client with async support
- **mangum** - AWS Lambda/ASGI adapter

### Development & Testing
- **pytest** - Test framework with async support
- **pytest-asyncio** - Async test fixtures
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities
- **black** - Code formatting (100 char line length)
- **ruff** - Linting and static analysis
- **mypy** - Static type checking

### Deployment Targets
- **Vercel** - Serverless HTTP deployment (via `app.py`)
- **Google Cloud Run** - Containerized deployment (via `cloudrun.yaml`)
- **AWS Lambda** - Serverless deployment (via `lambda_handler.py` + mangum)
- **SST** - Infrastructure as Code (via `sst.config.ts`)

## Project Conventions

### Code Style

**Formatting:**
- **Line length:** 100 characters (enforced by black + ruff)
- **Python version:** 3.12 (target)
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Double quotes for strings
- **Imports:** Sorted with standard lib → third-party → local

**Naming Conventions:**
- **Files:** `snake_case.py`
- **Classes:** `PascalCase` (e.g., `SupabaseDatabaseAdapter`, `WorkspaceOperationTool`)
- **Functions/methods:** `snake_case` (e.g., `create_entity`, `get_adapter`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private methods:** `_leading_underscore` (e.g., `_sanitize_entity`)
- **Async functions:** Always `async def`, never `def` with `asyncio.coroutine`

**Type Hints:**
- Use type hints for function signatures (parameters + return types)
- Use `Optional[T]` for nullable types
- Use `dict[str, Any]` (lowercase) for Python 3.12+
- Avoid `typing.Dict`, `typing.List` (use builtin generics)

### Architecture Patterns

**Layered Architecture (Strict Separation):**

```
tools/                    # Orchestration only (no business logic)
  ├── base.py             # Base tool class (auth, sanitization)
  ├── entity.py           # Entity CRUD operations
  ├── workspace.py        # Org/project management
  ├── relationship.py     # Trace links
  ├── workflow.py         # Multi-step processes
  └── query.py            # Advanced search

services/                 # Domain logic (no direct DB access)
  ├── embedding_*.py      # Embedding generation/caching
  ├── vector_search.py    # Semantic search
  └── auth/               # Auth helpers

infrastructure/           # Adapters (external systems)
  ├── supabase_*.py       # DB, auth, storage, realtime
  ├── mock_*.py           # Mock adapters for testing
  ├── upstash_*.py        # Redis, rate limiting
  ├── factory.py          # Dependency injection
  └── adapters.py         # Base adapter interfaces

auth/                     # Session management
  ├── session_manager.py          # Supabase-backed sessions
  ├── session_middleware.py       # ASGI middleware
  └── persistent_authkit_provider.py  # Custom FastMCP auth provider
```

**Key Patterns:**
1. **Adapter Pattern**: All external systems accessed via adapters (`infrastructure/`)
2. **Dependency Injection**: Use `factory.py` to get adapters (never instantiate directly)
3. **Base Tool Pattern**: All tools inherit from `BaseTool` (`tools/base.py`)
4. **Sanitization**: Large responses auto-sanitized to prevent token overflow
5. **Mock Mode**: Live/mock switching via environment variable (`USE_MOCK_CLIENTS`)

**File Size Constraint:**
- **Hard limit**: ≤500 lines per file
- **Target**: ≤350 lines per file
- **Decompose proactively** when approaching 350 lines

### Testing Strategy

**Test Organization:**
```
tests/
  ├── unit/              # Unit tests (fast, isolated, mocked)
  │   ├── tools/         # Tool tests with InMemoryMcpClient
  │   ├── infrastructure/  # Adapter tests
  │   ├── services/      # Service layer tests
  │   └── auth/          # Auth tests
  ├── integration/       # Integration tests (live DB/services)
  ├── e2e/               # End-to-end tests (full workflows)
  ├── performance/       # Load/stress tests
  └── framework/         # Test utilities and fixtures
```

**Test Naming Convention (Canonical):**
- Test file names describe **what's being tested**, not **how**
- ✅ Good: `test_entity.py`, `test_auth_supabase.py`, `test_database_adapter.py`
- ❌ Bad: `test_entity_fast.py`, `test_entity_unit.py`, `test_entity_final.py`
- Use **pytest markers** for speed/variant categorization (not file names)
- Use **fixture parametrization** for unit/integration/e2e variants (not separate files)

**Test Requirements:**
- All tools must have unit tests (with `InMemoryMcpClient`)
- Integration tests for database/auth operations
- Full test coverage for new features (unit + integration + e2e where applicable)
- No "TODO" tests without immediate implementation

**Running Tests:**
```bash
# Quick validation (unit only)
uv run pytest tests/unit -q

# Full suite
uv run pytest tests/

# With coverage
uv run pytest tests/ --cov --cov-report=html

# Specific markers
uv run pytest -m "not integration and not performance"
```

### Git Workflow

**Branching Strategy:**
- **main** - Production-ready code
- **working-deployment** - Current active development branch
- Feature branches: `feature/<descriptive-name>`
- Bugfix branches: `fix/<issue-description>`

**Commit Conventions:**
- **Format**: `<type>(<scope>): <subject>`
- **Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- **Scope**: module or area (e.g., `auth`, `tools`, `infrastructure`)
- **Co-authorship**: Include `Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>` for AI-assisted commits

**Forward-Only Progression (CRITICAL):**
- **NO `git revert` or `git reset`** (fix forward instead)
- **NO haphazard delete-and-rewrite cycles**
- Push forward to clean states via incremental fixes
- If broken: fix with targeted changes, not rollbacks
- Document issues in `05_KNOWN_ISSUES.md`, resolve systematically

## Domain Context

**Atoms Platform Overview:**

Atoms is a knowledge management platform for organizing entities (documents, requirements, properties, actions, connections) and their relationships. The MCP server provides AI assistants with structured access to this knowledge graph.

**Key Concepts:**

1. **Workspaces**: Organizations and projects that contain entities
2. **Entities**: Core objects with properties, content, and relationships
   - Documents, Requirements, Properties, Actions, Connections, etc.
3. **Relationships**: Typed links between entities (trace links, assignments, memberships)
4. **Workflows**: Multi-step operations with transaction support
5. **Semantic Search**: Vector embeddings enable intelligent discovery

**Tool Abstraction:**

Instead of exposing 80+ granular API endpoints, we provide **5 consolidated tools**:
- `workspace_operation` - Org/project management, members
- `entity_operation` - CRUD for documents, requirements, properties
- `relationship_operation` - Trace links, entity relationships
- `workflow_execute` - Multi-step business processes with transactions
- `data_query` - Advanced search, filtering, semantic queries

**Authentication Model:**
- All operations require explicit authentication via session tokens
- OAuth 2.0 PKCE flow + Dynamic Client Registration (WorkOS AuthKit)
- Session persistence via Supabase `mcp_sessions` table
- Stateless HTTP mode for serverless compatibility

## Important Constraints

### Technical Constraints

1. **Python Version**: Exactly 3.12.* (specified in `pyproject.toml`)
2. **Line Length**: 100 characters (black + ruff enforced)
3. **File Size**: ≤500 lines hard limit, ≤350 target
4. **Async-First**: Use `async def` for all I/O operations
5. **Type Hints**: Required for public APIs
6. **Supabase RLS**: All DB operations respect Row Level Security policies

### Deployment Constraints

1. **Stateless HTTP**: Must support serverless deployment (no persistent connections)
2. **Environment Variables**: All config via env vars (no hardcoded secrets)
3. **Cold Start Performance**: Minimize initialization time for serverless
4. **Memory Limits**: Serverless functions have memory constraints (optimize accordingly)

### Quality Constraints

1. **No MVP-Grade Code**: Every feature must be production-ready
2. **No TODO Comments**: Without immediate resolution plan
3. **No Backwards Compatibility Shims**: Clean, aggressive refactoring
4. **Full Test Coverage**: Unit + integration + e2e for all features
5. **Comprehensive Error Handling**: All error paths covered

### Business Constraints

1. **Security-First**: All auth operations via WorkOS AuthKit
2. **Data Privacy**: Respect user permissions (RLS policies)
3. **Rate Limiting**: Distributed rate limiting via Upstash Redis
4. **Observability**: Comprehensive logging and monitoring

## External Dependencies

### Core Services

1. **Supabase** (PostgreSQL + Auth + Storage)
   - **Database**: PostgreSQL with Row Level Security (RLS)
   - **Auth**: User authentication and JWT management
   - **Storage**: File storage for attachments
   - **Realtime**: Subscription-based updates (used sparingly)
   - **Environment Variables**: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

2. **WorkOS AuthKit** (OAuth 2.0 Provider)
   - **OAuth Flow**: PKCE + Dynamic Client Registration
   - **Session Management**: Token introspection and validation
   - **Environment Variables**: `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN`, `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL`

3. **Upstash Redis** (Serverless Cache)
   - **Rate Limiting**: Distributed token bucket algorithm
   - **Caching**: Embedding cache, session cache
   - **Health Monitoring**: Redis connection health checks
   - **Environment Variables**: `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`

4. **Google Vertex AI** (Embeddings)
   - **Semantic Search**: Generate embeddings for vector search
   - **Model**: `text-embedding-005` (lightweight REST API)
   - **Authentication**: Google Cloud service account JSON
   - **Environment Variables**: `GOOGLE_APPLICATION_CREDENTIALS`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`

### Development Tools

1. **FastMCP CLI**
   - `fastmcp run <module>` - Start server
   - `fastmcp dev <module>` - Start with MCP Inspector
   - `fastmcp inspect <url>` - Query running server

2. **OpenSpec CLI** (Spec-Driven Development)
   - `openspec init` - Initialize project
   - `openspec list` - View active changes
   - `openspec validate <change-id>` - Validate specs
   - `openspec archive <change-id>` - Archive completed changes

3. **pytest** (Testing Framework)
   - `uv run pytest tests/unit` - Unit tests
   - `uv run pytest tests/integration` - Integration tests
   - `uv run pytest -m "not integration"` - Skip integration tests

### Deployment Platforms

1. **Vercel** (Primary Serverless Platform)
   - ASGI via `app.py`
   - Environment variables via Vercel dashboard
   - Automatic deployments from GitHub

2. **Google Cloud Run** (Containerized Deployment)
   - Dockerfile or buildpacks
   - Configuration via `cloudrun.yaml`

3. **AWS Lambda** (Serverless Alternative)
   - Handler via `lambda_handler.py`
   - Adapter via `mangum`

## Canonical Authority

**FastMCP Contract:** All FastMCP behavior is authoritatively defined in `llms-full.txt`. When in doubt, consult `llms-full.txt` § sections 0-15.

**Repository Guidance:**
- `AGENTS.md` - Agent behavior, OpenSpec workflow, session documentation
- `CLAUDE.md` - Claude-specific usage guide, operational loop
- `warp.md` - Warp terminal workflows, session documentation

**Aggressive Change Policy:**
- NO backwards compatibility shims
- Always FULL, COMPLETE changes
- Update ALL callers simultaneously
- Remove old code paths entirely
- Forward-only progression (no git revert)

## Session Documentation (Living Docs)

All work must be documented in structured session folders:

```
docs/sessions/<YYYYMMDD-descriptive-name>/
  00_SESSION_OVERVIEW.md           # Goals, decisions
  01_RESEARCH.md                   # Codebase + web research
  02_SPECIFICATIONS.md             # Full specs (links to OpenSpec)
  03_DAG_WBS.md                    # Dependency graph, work breakdown
  04_IMPLEMENTATION_STRATEGY.md    # Technical approach
  05_KNOWN_ISSUES.md               # Bugs, workarounds, tech debt
  06_TESTING_STRATEGY.md           # Test plan, coverage
```

**OpenSpec Integration:**
- Use OpenSpec for all non-trivial features
- Create proposals BEFORE code (`openspec init`)
- Follow 3-phase workflow: Proposal → Apply → Archive
- Archive completed changes (`openspec archive <change-id> -y`)

## Research-First Development

**Before implementing ANY feature:**
1. **Codebase research** (use `rg` to find patterns)
2. **Web research** (external API docs, library patterns)
3. **Document findings** in `01_RESEARCH.md`
4. **No guessing** - research until confident

**Research Commands:**
```bash
# Find similar implementations
rg "pattern_name" --type py -A 5 -B 5

# Trace call chains
rg "function_name\(" --type py

# Find test patterns
rg "def test_.*pattern" tests/ -A 10

# Check architecture patterns
rg "class.*Adapter\|class.*Factory\|class.*Provider" --type py
```
