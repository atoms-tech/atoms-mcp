# Schema Synchronization System - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Supabase Database                          │
│                    (PostgreSQL 15 with pgvector)                    │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Tables     │  │    Enums     │  │  Constraints │            │
│  │              │  │              │  │              │            │
│  │ organizations│  │ org_type     │  │ Foreign Keys │            │
│  │ projects     │  │ project_status│  │ Unique Keys  │            │
│  │ requirements │  │ req_priority  │  │ Check Keys   │            │
│  │ ...          │  │ ...          │  │ ...          │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Supabase MCP Tools
                             │ - execute_sql
                             │ - list_tables  
                             │ - get_project
                             ▼
              ┌─────────────────────────────────┐
              │      Schema Sync System         │
              │   (scripts/sync_schema.py)      │
              │                                 │
              │  ┌───────────────────────────┐  │
              │  │  1. Query Database        │  │
              │  │     - Tables & columns    │  │
              │  │     - Enums & values      │  │
              │  │     - Constraints         │  │
              │  └───────────────────────────┘  │
              │                                 │
              │  ┌───────────────────────────┐  │
              │  │  2. Load Local Schemas    │  │
              │  │     - Parse enums.py      │  │
              │  │     - Parse entities.py   │  │
              │  │     - Parse relationships │  │
              │  └───────────────────────────┘  │
              │                                 │
              │  ┌───────────────────────────┐  │
              │  │  3. Compare & Analyze     │  │
              │  │     - Detect drift        │  │
              │  │     - Assign severity     │  │
              │  │     - Generate report     │  │
              │  └───────────────────────────┘  │
              │                                 │
              │  ┌───────────────────────────┐  │
              │  │  4. Generate Code         │  │
              │  │     - Enum classes        │  │
              │  │     - TypedDict defs      │  │
              │  │     - Type annotations    │  │
              │  └───────────────────────────┘  │
              │                                 │
              │  ┌───────────────────────────┐  │
              │  │  5. Update Version        │  │
              │  │     - Calculate hash      │  │
              │  │     - Update timestamp    │  │
              │  │     - Track differences   │  │
              │  └───────────────────────────┘  │
              └─────────────┬───────────────────┘
                            │
                            ▼
     ┌────────────────────────────────────────────────────┐
     │            Local Python Schemas                    │
     │                                                    │
     │  schemas/                                          │
     │  ├── __init__.py                                   │
     │  ├── schema_version.py  ← Auto-generated          │
     │  │   ├── SCHEMA_VERSION                           │
     │  │   ├── LAST_SYNC                                │
     │  │   ├── DB_HASH                                  │
     │  │   └── Statistics                               │
     │  │                                                │
     │  ├── enums.py          ← Manual integration       │
     │  │   ├── OrganizationType(str, Enum)             │
     │  │   ├── ProjectStatus(str, Enum)                │
     │  │   ├── RequirementPriority(str, Enum)          │
     │  │   └── ...                                      │
     │  │                                                │
     │  └── database/                                     │
     │      ├── entities.py   ← Manual integration       │
     │      │   ├── OrganizationRow(TypedDict)          │
     │      │   ├── ProjectRow(TypedDict)               │
     │      │   ├── RequirementRow(TypedDict)           │
     │      │   └── ...                                  │
     │      │                                            │
     │      └── relationships.py ← Manual integration    │
     │          ├── OrganizationMemberRow(TypedDict)    │
     │          ├── ProjectMemberRow(TypedDict)         │
     │          └── ...                                  │
     └────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Query Phase
```
Database → MCP Tools → sync_schema.py
                          │
                          ├─ Get all tables
                          ├─ Get all enums
                          ├─ Get table columns
                          └─ Get constraints
```

### 2. Comparison Phase
```
Database Schema    Local Schema
      │                 │
      ├─ Enums          ├─ Enum Classes
      │  ├─ org_type    │  └─ OrganizationType
      │  └─ status      │     └─ ProjectStatus
      │                 │
      ├─ Tables         ├─ TypedDict Classes
      │  ├─ orgs        │  └─ OrganizationRow
      │  └─ projects    │     └─ ProjectRow
      │                 │
      └─────────┬───────┘
                ▼
           Diff Engine
                │
                ├─ New items
                ├─ Removed items
                └─ Modified items
                        │
                        ▼
              Severity Assignment
                        │
                        ├─ CRITICAL
                        ├─ HIGH
                        ├─ MEDIUM
                        └─ LOW
```

### 3. Code Generation Phase
```
Detected Changes
       │
       ├─ New Enum → Generate Enum Class
       │              class NewEnum(str, Enum):
       │                  VALUE_1 = "value_1"
       │                  VALUE_2 = "value_2"
       │
       └─ New Table → Generate TypedDict
                      class NewTableRow(TypedDict, total=False):
                          id: str
                          name: str
                          created_at: str
```

## CI/CD Integration

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions                       │
│                                                         │
│  Triggers:                                              │
│  ├─ Pull Request (on schema changes)                   │
│  ├─ Daily Schedule (9 AM UTC)                          │
│  └─ Manual Dispatch                                     │
│                                                         │
│  Jobs:                                                  │
│  ├─ 1. Check Schema Drift                              │
│  │     ├─ Run sync_schema.py --check                   │
│  │     ├─ Exit 0: Continue                             │
│  │     └─ Exit 1: Generate report & fail               │
│  │                                                      │
│  ├─ 2. Validate Migrations                             │
│  │     ├─ Check SQL syntax                             │
│  │     ├─ Validate naming                              │
│  │     └─ Check for unsafe operations                  │
│  │                                                      │
│  └─ 3. Update Docs (main branch only)                  │
│        ├─ Run sync_schema.py --update                  │
│        ├─ Commit schema_version.py                     │
│        └─ Skip CI on commit                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  PR Status      │
                 │                 │
                 │  ✅ Pass        │
                 │  ❌ Fail        │
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Artifacts      │
                 │                 │
                 │  - Drift report │
                 │  - Test results │
                 └─────────────────┘
```

## Pre-commit Hook Flow

```
┌─────────────────────────────────────────────────────────┐
│                Developer Workflow                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  git commit     │
                 └────────┬────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │    Pre-commit Hook            │
          │  (pre-commit-schema-check.sh) │
          └───────────────┬───────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Check drift    │
                 │  (--check)      │
                 └────────┬────────┘
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
         ┌─────────────┐    ┌─────────────┐
         │  No Drift   │    │ Drift Found │
         │  ✅ Pass    │    │  ❌ Fail    │
         └──────┬──────┘    └──────┬──────┘
                │                   │
                ▼                   ▼
         Commit Proceeds    Commit Blocked
                                    │
                                    ▼
                            Show Diff Options
                                    │
                                    ├─ View diff
                                    ├─ Update schemas
                                    └─ Force commit (--no-verify)
```

## Type Conversion Architecture

```
┌─────────────────────────────────────────────────────────┐
│              SQL to Python Type Mapping                 │
└─────────────────────────────────────────────────────────┘

Database Type          →    Python Type
─────────────────────────────────────────
uuid                   →    str
text, varchar          →    str
integer, bigint        →    int
boolean                →    bool
timestamp              →    str (ISO 8601)
jsonb, json            →    dict
ARRAY                  →    list[element_type]
numeric, decimal       →    float
interval               →    str
USER-DEFINED (enum)    →    str

Nullable Handling:
is_nullable = 'YES'    →    Optional[T]
is_nullable = 'NO'     →    T

Examples:
─────────────────────────────────────────
id uuid NOT NULL       →    id: str
email text NULL        →    email: Optional[str]
count integer NOT NULL →    count: int
tags text[] NULL       →    tags: Optional[list[str]]
metadata jsonb NULL    →    metadata: Optional[dict]
```

## Naming Convention Flow

```
┌─────────────────────────────────────────────────────────┐
│                Database → Python                        │
└─────────────────────────────────────────────────────────┘

Enums:
database_name          →    PythonClassName
─────────────────────────────────────────────
organization_type      →    OrganizationType
project_status         →    ProjectStatus
user_role_type         →    UserRoleType
billing_plan           →    BillingPlanType

Tables:
database_name          →    PythonClassName
─────────────────────────────────────────────
organizations          →    OrganizationRow
projects               →    ProjectRow
properties             →    PropertyRow
table_rows             →    TableRowsRow

Special Plurals:
─────────────────────────────────────────────
properties             →    property        →    PropertyRow
entries                →    entry           →    EntryRow
analyses               →    analysis        →    AnalysisRow
```

## Version Tracking

```
┌─────────────────────────────────────────────────────────┐
│              Schema Version Tracking                    │
└─────────────────────────────────────────────────────────┘

schema_version.py:
├── SCHEMA_VERSION      = "2025-10-09"
├── LAST_SYNC          = "2025-10-09T15:32:00Z"
├── DB_HASH            = "sha256_hash..."
├── TABLES_COUNT       = 42
├── ENUMS_COUNT        = 24
└── LAST_SYNC_DIFFERENCES = 3

Hash Calculation:
Database Schema (JSON) → Sort Keys → JSON Dump → SHA256 → Hash

Version History:
v1: Initial schema
v2: Added billing tables
v3: Modified project status enum
...

Tracking Benefits:
✅ Detect when database changed
✅ Prevent stale schema usage
✅ Track drift over time
✅ Rollback capability
```

## Error Handling

```
┌─────────────────────────────────────────────────────────┐
│                Error Handling Flow                      │
└─────────────────────────────────────────────────────────┘

sync_schema.py
      │
      ├─ Connection Error
      │     └─→ Fallback to mock schema
      │         └─→ Continue with demo
      │
      ├─ Query Error
      │     └─→ Log error
      │         └─→ Return empty result
      │
      ├─ Comparison Error
      │     └─→ Log detailed error
      │         └─→ Continue with partial diff
      │
      └─ Code Generation Error
            └─→ Log error
                └─→ Show manual code snippet
                    └─→ Continue
```

## Security Considerations

```
┌─────────────────────────────────────────────────────────┐
│                  Security Model                         │
└─────────────────────────────────────────────────────────┘

Environment Variables:
├── SUPABASE_URL            (required)
├── SUPABASE_SERVICE_KEY    (required, sensitive)
└── SUPABASE_PROJECT_ID     (required)

Access Control:
├── Service role key needed for schema queries
├── Read-only operations only
└── No data access (schema only)

CI/CD Secrets:
├── GitHub Secrets (encrypted)
├── Never logged
└── Scoped to workflow only

Pre-commit Hook:
├── Checks credentials exist
├── Warns if missing
└── Skips check gracefully
```

## Performance Optimization

```
┌─────────────────────────────────────────────────────────┐
│              Performance Characteristics                │
└─────────────────────────────────────────────────────────┘

Query Performance:
├── Database queries: ~100-500ms
├── Schema parsing: ~50-100ms
├── Comparison: ~10-50ms
└── Total: ~200-700ms

Caching:
├── No persistent cache (intentional)
├── Fresh query each run
└── Ensures accuracy

Optimization:
├── Parallel queries where possible
├── Minimal data fetching
├── Efficient comparison algorithms
└── Lazy code generation

Scalability:
├── Handles 50+ tables efficiently
├── Supports 100+ enums
└── Processes 1000+ columns
```

## File Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                Dependency Graph                         │
└─────────────────────────────────────────────────────────┘

sync_schema.py
├── depends on:
│   ├── schemas/enums.py
│   ├── schemas/database/entities.py
│   ├── schemas/database/relationships.py
│   └── supabase_client.py (optional)
│
├── generates:
│   └── schemas/schema_version.py
│
└── produces:
    ├── Enum code snippets
    ├── TypedDict code snippets
    └── Markdown reports

mcp_schema_query.py
├── depends on:
│   └── Supabase MCP tools
│
└── produces:
    ├── Schema documentation
    ├── Complexity metrics
    └── Export files

test_schema_sync.py
├── depends on:
│   ├── sync_schema.py
│   └── schemas/*
│
└── validates:
    ├── Drift detection
    ├── Code generation
    └── Type conversion
```

## Extension Points

```
┌─────────────────────────────────────────────────────────┐
│              Customization & Extensions                 │
└─────────────────────────────────────────────────────────┘

1. Custom Type Mappings:
   Edit: scripts/sync_schema.py
   Method: _sql_to_python_type()

2. Custom Name Conversions:
   Edit: scripts/sync_schema.py
   Methods:
   ├── _convert_class_to_enum_name()
   ├── _convert_class_to_table_name()
   ├── _enum_name_to_class()
   └── _table_name_to_class()

3. Custom Severity Rules:
   Edit: scripts/schema_sync_config.json
   Section: sync_rules.severity_levels

4. Custom Notifications:
   Edit: scripts/schema_sync_config.json
   Sections:
   ├── notifications.slack
   └── notifications.email

5. Custom Templates:
   Create: schemas/templates/*.j2
   Reference in: schema_sync_config.json
```

---

**Architecture designed for reliability, maintainability, and extensibility.**
