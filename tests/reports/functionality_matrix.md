# ATOMS MCP FUNCTIONALITY MATRIX

## Overview

Complete validation of all Atoms MCP tools covering:
- **Functionality**: What the tool does
- **User Stories**: Why users need it
- **Data Coverage**: All data items returned
- **Test Results**: Pass/fail status with performance

---

## workspace_tool
**Workspace context management for organizing work**

| Operation | Status | Time (ms) | User Story |
|-----------|--------|-----------|------------|
| list_workspaces | ⏭️ Not Tested | - | see all my workspaces |
| get_context | ⏭️ Not Tested | - | know my current context |
| set_context | ⏭️ Not Tested | - | switch workspaces |
| get_defaults | ⏭️ Not Tested | - | see default settings |

## entity_tool
**CRUD operations for all Atoms entities**

| Operation | Status | Time (ms) | User Story |
|-----------|--------|-----------|------------|
| list_organizations | ⏭️ Not Tested | - | see all my organizations |
| list_projects | ⏭️ Not Tested | - | see all my projects |
| list_documents | ⏭️ Not Tested | - | browse documents |
| list_requirements | ⏭️ Not Tested | - | see all requirements |
| create_organization | ⏭️ Not Tested | - | create organizations |
| read_by_id | ⏭️ Not Tested | - | view entity details |
| update | ⏭️ Not Tested | - | modify entities |
| fuzzy_match | ⏭️ Not Tested | - | As a user, I want flexible search |

## query_tool
**Search and analytics across all entities**

| Operation | Status | Time (ms) | User Story |
|-----------|--------|-----------|------------|
| search_projects | ⏭️ Not Tested | - | find projects |
| search_documents | ⏭️ Not Tested | - | find documents |
| search_multi | ⏭️ Not Tested | - | search everything |
| aggregate | ⏭️ Not Tested | - | As a user, I want summary stats |
| rag_search_semantic | ⏭️ Not Tested | - | As a user, I want intelligent search |
| rag_search_keyword | ⏭️ Not Tested | - | As a user, I want enhanced keyword search |
| rag_search_hybrid | ⏭️ Not Tested | - | As a user, I want best of both searches |

## relationship_tool
**Manage relationships between entities**

| Operation | Status | Time (ms) | User Story |
|-----------|--------|-----------|------------|
| list_relationships | ⏭️ Not Tested | - | see connections |
| link | ⏭️ Not Tested | - | connect entities |
| unlink | ⏭️ Not Tested | - | remove connections |
| check | ⏭️ Not Tested | - | verify connections |
| update | ⏭️ Not Tested | - | modify connections |

## workflow_tool
**Automated workflows and bulk operations**

| Operation | Status | Time (ms) | User Story |
|-----------|--------|-----------|------------|
| setup_project | ⏭️ Not Tested | - | As a user, I want quick project creation |
| import_requirements | ⏭️ Not Tested | - | bulk import requirements |
| setup_test_matrix | ⏭️ Not Tested | - | As a user, I want automated test setup |
| bulk_status_update | ⏭️ Not Tested | - | update multiple items |
| organization_onboarding | ⏭️ Not Tested | - | As a user, I want guided org setup |
