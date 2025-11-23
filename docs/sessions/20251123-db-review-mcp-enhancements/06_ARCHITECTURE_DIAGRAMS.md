# Architecture Diagrams & System Design

## Current MCP Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastMCP Server                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ workspace_tool   │  │ entity_tool      │               │
│  │ (context mgmt)   │  │ (CRUD + search)  │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │relationship_tool │  │workflow_execute  │               │
│  │ (associations)   │  │ (complex flows)  │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌──────────────────┐                                      │
│  │ data_query       │ (legacy, consolidating)             │
│  │ (search/agg)     │                                      │
│  └──────────────────┘                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────────────────────────────────────────────────┐
    │         Infrastructure Adapters                     │
    ├─────────────────────────────────────────────────────┤
    │ • SupabaseDatabaseAdapter                           │
    │ • WorkflowStorageAdapter                            │
    │ • AdvancedFeaturesAdapter                           │
    │ • PermissionManager                                 │
    └─────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────┐
    │         Supabase Database                           │
    ├─────────────────────────────────────────────────────┤
    │ • 12 existing tables (org, project, requirement...) │
    │ • 7 new tables (workflow, search, export, perm...)  │
    │ • Row-level security on all tables                  │
    │ • 30+ performance indexes                           │
    └─────────────────────────────────────────────────────┘
```

## Enhanced MCP Architecture (Proposed)

```
┌──────────────────────────────────────────────────────────────┐
│                    FastMCP Server                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │workspace_tool    │  │entity_tool       │                │
│  │(context + search)│  │(CRUD + enhanced) │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │relationship_tool │  │workflow_execute  │                │
│  │(associations)    │  │(complex flows)   │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │search_discovery  │  │data_transfer     │ (NEW)          │
│  │(FTS + facets)    │  │(import/export)   │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │permission_control│  │workflow_mgmt     │ (NEW)          │
│  │(access control)  │  │(workflow CRUD)   │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
    │         │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼         ▼
┌──────────────────────────────────────────────────────────────┐
│         Infrastructure Adapters (Enhanced)                   │
├──────────────────────────────────────────────────────────────┤
│ • SupabaseDatabaseAdapter                                    │
│ • WorkflowStorageAdapter                                     │
│ • AdvancedFeaturesAdapter                                    │
│ • SearchIndexAdapter (NEW)                                   │
│ • ExportImportAdapter (NEW)                                  │
│ • PermissionAdapter (NEW)                                    │
│ • WorkflowManagementAdapter (NEW)                            │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│         Supabase Database (19 Tables)                        │
├──────────────────────────────────────────────────────────────┤
│ Core Tables (12):                                            │
│ • organizations, projects, documents, requirements           │
│ • test_req, blocks, properties, trace_links                  │
│ • assignments, profiles, org_members, project_members       │
│                                                              │
│ New Tables (7):                                              │
│ • workflows, workflow_versions, workflow_executions          │
│ • search_index, export_jobs, import_jobs                     │
│ • entity_permissions                                         │
│                                                              │
│ Features:                                                    │
│ • Row-level security (RLS) on all tables                     │
│ • 30+ performance indexes (GIN, B-tree)                      │
│ • Automatic triggers for timestamps & search vectors        │
│ • Foreign keys with CASCADE/SET NULL                         │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow: Search Operation

```
Client Request
    │
    ▼
search_discovery(
  operation="search",
  query="api auth",
  entity_type="requirement"
)
    │
    ▼
┌─────────────────────────────────┐
│ search_discovery Tool           │
│ • Validate auth                 │
│ • Get workspace context         │
│ • Route to adapter              │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ SearchIndexAdapter              │
│ • Build FTS query               │
│ • Execute search                │
│ • Rank results                  │
│ • Apply filters                 │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ SupabaseDatabaseAdapter         │
│ • Execute FTS query             │
│ • Apply pagination              │
│ • Return results                │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ Supabase Database               │
│ • search_index table            │
│ • GIN index on search_vector    │
│ • Return ranked results         │
└─────────────────────────────────┘
    │
    ▼
Response: {
  "success": true,
  "data": [...results...],
  "metrics": {"total_ms": 145}
}
```

## Data Flow: Export Operation

```
Client Request
    │
    ▼
data_transfer(
  operation="export",
  entity_type="requirement",
  format="csv"
)
    │
    ▼
┌─────────────────────────────────┐
│ data_transfer Tool              │
│ • Validate auth                 │
│ • Create job record             │
│ • Queue async processing        │
└─────────────────────────────────┘
    │
    ├─────────────────────────────────────┐
    │ (Immediate Response)                │ (Background Processing)
    │                                     │
    ▼                                     ▼
Return Job ID                    ExportImportAdapter
                                 • Fetch entities
                                 • Format data
                                 • Save file
                                 • Update job status
                                 │
                                 ▼
                            Supabase Database
                            • export_jobs table
                            • Update status
                            • Store file path
```

## Tool Integration Matrix

```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Tool             │ Primary Use      │ Integrates With  │ New Adapters     │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ entity_operation │ CRUD + search    │ All tools        │ Enhanced         │
│ search_discovery │ FTS + discovery  │ entity_tool      │ SearchIndex      │
│ data_transfer    │ Import/export    │ entity_tool      │ ExportImport     │
│ permission_ctrl  │ Access control   │ entity_tool      │ Permission       │
│ workflow_mgmt    │ Workflow CRUD    │ workflow_execute │ WorkflowMgmt     │
│ workspace_tool   │ Context mgmt     │ All tools        │ Enhanced         │
│ relationship_op  │ Associations     │ entity_tool      │ No change        │
│ workflow_execute │ Complex flows    │ All tools        │ No change        │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

## Adapter Dependency Graph

```
SupabaseDatabaseAdapter (Base)
    │
    ├─► WorkflowStorageAdapter
    │
    ├─► AdvancedFeaturesAdapter
    │
    ├─► SearchIndexAdapter (NEW)
    │   └─► search_discovery tool
    │
    ├─► ExportImportAdapter (NEW)
    │   └─► data_transfer tool
    │
    ├─► PermissionAdapter (NEW)
    │   └─► permission_control tool
    │
    └─► WorkflowManagementAdapter (NEW)
        └─► workflow_management tool
```

