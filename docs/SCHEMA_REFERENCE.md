# Atoms MCP - Schema Reference

## Overview

This document provides a comprehensive reference for all database schemas, data models, and type definitions used in the Atoms MCP system.

## Database Schema

### Core Entities

#### Organizations

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    type organization_type NOT NULL,
    settings JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_organizations_type ON organizations(type);
CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_organizations_created_at ON organizations(created_at);
```

**Python Schema:**
```python
class OrganizationRow(TypedDict):
    id: str
    name: str
    description: str | None
    type: OrganizationType
    settings: Dict[str, Any]
    is_deleted: bool
    created_at: str
    updated_at: str
```

#### Projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    status project_status DEFAULT 'active',
    start_date DATE,
    end_date DATE,
    settings JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_projects_organization_id ON projects(organization_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_name ON projects(name);
```

**Python Schema:**
```python
class ProjectRow(TypedDict):
    id: str
    name: str
    description: str | None
    organization_id: str
    status: ProjectStatus
    start_date: str | None
    end_date: str | None
    settings: Dict[str, Any]
    is_deleted: bool
    created_at: str
    updated_at: str
```

#### Requirements

```sql
CREATE TABLE requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    project_id UUID NOT NULL REFERENCES projects(id),
    priority requirement_priority DEFAULT 'medium',
    status requirement_status DEFAULT 'draft',
    format requirement_format DEFAULT 'EARS',
    source TEXT,
    acceptance_criteria TEXT,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_requirements_project_id ON requirements(project_id);
CREATE INDEX idx_requirements_status ON requirements(status);
CREATE INDEX idx_requirements_priority ON requirements(priority);
CREATE INDEX idx_requirements_search ON requirements USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
```

**Python Schema:**
```python
class RequirementRow(TypedDict):
    id: str
    title: str
    description: str | None
    project_id: str
    priority: RequirementPriority
    status: RequirementStatus
    format: RequirementFormat
    source: str | None
    acceptance_criteria: str | None
    notes: str | None
    metadata: Dict[str, Any]
    is_deleted: bool
    created_at: str
    updated_at: str
```

#### Tests

```sql
CREATE TABLE tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    project_id UUID NOT NULL REFERENCES projects(id),
    type test_type DEFAULT 'functional',
    status test_status DEFAULT 'draft',
    priority test_priority DEFAULT 'medium',
    steps JSONB,
    expected_result TEXT,
    actual_result TEXT,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tests_project_id ON tests(project_id);
CREATE INDEX idx_tests_type ON tests(type);
CREATE INDEX idx_tests_status ON tests(status);
CREATE INDEX idx_tests_search ON tests USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
```

**Python Schema:**
```python
class TestRow(TypedDict):
    id: str
    name: str
    description: str | None
    project_id: str
    type: TestType
    status: TestStatus
    priority: TestPriority
    steps: List[Dict[str, Any]] | None
    expected_result: str | None
    actual_result: str | None
    notes: str | None
    metadata: Dict[str, Any]
    is_deleted: bool
    created_at: str
    updated_at: str
```

#### Documents

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT,
    project_id UUID NOT NULL REFERENCES projects(id),
    type document_type DEFAULT 'general',
    format document_format DEFAULT 'markdown',
    file_path TEXT,
    file_size INTEGER,
    mime_type TEXT,
    metadata JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_search ON documents USING gin(to_tsvector('english', title || ' ' || COALESCE(content, '')));
```

**Python Schema:**
```python
class DocumentRow(TypedDict):
    id: str
    title: str
    content: str | None
    project_id: str
    type: DocumentType
    format: DocumentFormat
    file_path: str | None
    file_size: int | None
    mime_type: str | None
    metadata: Dict[str, Any]
    is_deleted: bool
    created_at: str
    updated_at: str
```

#### Users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    role user_role DEFAULT 'member',
    settings JSONB DEFAULT '{}',
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_role ON users(role);
```

**Python Schema:**
```python
class UserRow(TypedDict):
    id: str
    email: str
    name: str | None
    organization_id: str
    role: UserRole
    settings: Dict[str, Any]
    last_login: str | None
    is_active: bool
    is_deleted: bool
    created_at: str
    updated_at: str
```

### Relationship Tables

#### Entity Relationships

```sql
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    relationship_type TEXT NOT NULL,
    source_entity_type TEXT NOT NULL,
    source_entity_id UUID NOT NULL,
    target_entity_type TEXT NOT NULL,
    target_entity_id UUID NOT NULL,
    metadata JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure valid relationship types
    CONSTRAINT valid_relationship_type CHECK (
        relationship_type IN (
            'project_organization',
            'requirement_project',
            'test_requirement',
            'document_project',
            'user_organization',
            'requirement_requirement'
        )
    )
);

-- Indexes
CREATE INDEX idx_relationships_source ON entity_relationships(source_entity_type, source_entity_id);
CREATE INDEX idx_relationships_target ON entity_relationships(target_entity_type, target_entity_id);
CREATE INDEX idx_relationships_type ON entity_relationships(relationship_type);
```

**Python Schema:**
```python
class EntityRelationshipRow(TypedDict):
    id: str
    relationship_type: str
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    metadata: Dict[str, Any]
    is_deleted: bool
    created_at: str
    updated_at: str
```

### Vector Search Tables

#### Document Embeddings

```sql
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- OpenAI embedding dimension
    model TEXT DEFAULT 'text-embedding-ada-002',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX idx_document_embeddings_vector ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**Python Schema:**
```python
class DocumentEmbeddingRow(TypedDict):
    id: str
    document_id: str
    content: str
    embedding: List[float]
    model: str
    created_at: str
```

## Enums

### Organization Types

```sql
CREATE TYPE organization_type AS ENUM (
    'enterprise',
    'startup',
    'nonprofit',
    'government',
    'educational',
    'individual'
);
```

**Python Enum:**
```python
class OrganizationType(str, Enum):
    ENTERPRISE = "enterprise"
    STARTUP = "startup"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"
    EDUCATIONAL = "educational"
    INDIVIDUAL = "individual"
```

### Project Status

```sql
CREATE TYPE project_status AS ENUM (
    'planning',
    'active',
    'on_hold',
    'completed',
    'cancelled'
);
```

**Python Enum:**
```python
class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

### Requirement Priority

```sql
CREATE TYPE requirement_priority AS ENUM (
    'critical',
    'high',
    'medium',
    'low'
);
```

**Python Enum:**
```python
class RequirementPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

### Requirement Status

```sql
CREATE TYPE requirement_status AS ENUM (
    'draft',
    'review',
    'approved',
    'implemented',
    'tested',
    'completed',
    'rejected'
);
```

**Python Enum:**
```python
class RequirementStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    COMPLETED = "completed"
    REJECTED = "rejected"
```

### Requirement Formats

```sql
CREATE TYPE requirement_format AS ENUM (
    'EARS',
    'INCOSE',
    'IEEE',
    'CUSTOM',
    'PLAIN_TEXT'
);
```

**Python Enum:**
```python
class RequirementFormat(str, Enum):
    EARS = "EARS"
    INCOSE = "INCOSE"
    IEEE = "IEEE"
    CUSTOM = "CUSTOM"
    PLAIN_TEXT = "PLAIN_TEXT"
```

### Test Types

```sql
CREATE TYPE test_type AS ENUM (
    'functional',
    'integration',
    'unit',
    'performance',
    'security',
    'usability',
    'regression',
    'smoke'
);
```

**Python Enum:**
```python
class TestType(str, Enum):
    FUNCTIONAL = "functional"
    INTEGRATION = "integration"
    UNIT = "unit"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    REGRESSION = "regression"
    SMOKE = "smoke"
```

### Test Status

```sql
CREATE TYPE test_status AS ENUM (
    'draft',
    'ready',
    'running',
    'passed',
    'failed',
    'blocked',
    'skipped'
);
```

**Python Enum:**
```python
class TestStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
```

### Test Priority

```sql
CREATE TYPE test_priority AS ENUM (
    'critical',
    'high',
    'medium',
    'low'
);
```

**Python Enum:**
```python
class TestPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

### Document Types

```sql
CREATE TYPE document_type AS ENUM (
    'general',
    'specification',
    'design',
    'user_guide',
    'api_documentation',
    'test_plan',
    'requirements',
    'architecture'
);
```

**Python Enum:**
```python
class DocumentType(str, Enum):
    GENERAL = "general"
    SPECIFICATION = "specification"
    DESIGN = "design"
    USER_GUIDE = "user_guide"
    API_DOCUMENTATION = "api_documentation"
    TEST_PLAN = "test_plan"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
```

### Document Formats

```sql
CREATE TYPE document_format AS ENUM (
    'markdown',
    'html',
    'pdf',
    'docx',
    'txt',
    'json',
    'yaml',
    'xml'
);
```

**Python Enum:**
```python
class DocumentFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
```

### User Roles

```sql
CREATE TYPE user_role AS ENUM (
    'admin',
    'manager',
    'member',
    'viewer'
);
```

**Python Enum:**
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"
```

## Row-Level Security (RLS) Policies

### Organizations

```sql
-- Users can only access organizations they belong to
CREATE POLICY "Users can access their organizations"
ON organizations
FOR ALL
TO authenticated
USING (
    id IN (
        SELECT organization_id 
        FROM users 
        WHERE id = auth.uid()
    )
);
```

### Projects

```sql
-- Users can only access projects in their organizations
CREATE POLICY "Users can access projects in their organizations"
ON projects
FOR ALL
TO authenticated
USING (
    organization_id IN (
        SELECT organization_id 
        FROM users 
        WHERE id = auth.uid()
    )
);
```

### Requirements

```sql
-- Users can only access requirements in their organization's projects
CREATE POLICY "Users can access requirements in their organization's projects"
ON requirements
FOR ALL
TO authenticated
USING (
    project_id IN (
        SELECT p.id 
        FROM projects p
        JOIN users u ON p.organization_id = u.organization_id
        WHERE u.id = auth.uid()
    )
);
```

### Tests

```sql
-- Users can only access tests in their organization's projects
CREATE POLICY "Users can access tests in their organization's projects"
ON tests
FOR ALL
TO authenticated
USING (
    project_id IN (
        SELECT p.id 
        FROM projects p
        JOIN users u ON p.organization_id = u.organization_id
        WHERE u.id = auth.uid()
    )
);
```

### Documents

```sql
-- Users can only access documents in their organization's projects
CREATE POLICY "Users can access documents in their organization's projects"
ON documents
FOR ALL
TO authenticated
USING (
    project_id IN (
        SELECT p.id 
        FROM projects p
        JOIN users u ON p.organization_id = u.organization_id
        WHERE u.id = auth.uid()
    )
);
```

### Entity Relationships

```sql
-- Users can only access relationships for entities they can access
CREATE POLICY "Users can access relationships for their entities"
ON entity_relationships
FOR ALL
TO authenticated
USING (
    -- Source entity access check
    (source_entity_type = 'organization' AND source_entity_id IN (
        SELECT organization_id FROM users WHERE id = auth.uid()
    )) OR
    (source_entity_type = 'project' AND source_entity_id IN (
        SELECT p.id FROM projects p
        JOIN users u ON p.organization_id = u.organization_id
        WHERE u.id = auth.uid()
    )) OR
    (source_entity_type = 'requirement' AND source_entity_id IN (
        SELECT r.id FROM requirements r
        JOIN projects p ON r.project_id = p.id
        JOIN users u ON p.organization_id = u.organization_id
        WHERE u.id = auth.uid()
    )) OR
    (source_entity_type = 'test' AND source_entity_id IN (
        SELECT t.id FROM tests t
        JOIN projects p ON t.project_id = p.id
        JOIN users u ON p.organization_id = u.organization_id
        WHERE u.id = auth.uid()
    )) OR
    (source_entity_type = 'document' AND source_entity_id IN (
        SELECT d.id FROM documents d
        JOIN projects p ON d.project_id = p.id
        JOIN users u ON p.organization_id = u.organization_id
        WHERE u.id = auth.uid()
    ))
);
```

## Database Functions

### Search Functions

#### Full-Text Search

```sql
CREATE OR REPLACE FUNCTION search_entities(
    search_term TEXT,
    entity_types TEXT[] DEFAULT ARRAY['requirement', 'test', 'document'],
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    entity_type TEXT,
    entity_id UUID,
    title TEXT,
    content TEXT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'requirement'::TEXT,
        r.id,
        r.title,
        COALESCE(r.description, ''),
        ts_rank(to_tsvector('english', r.title || ' ' || COALESCE(r.description, '')), plainto_tsquery('english', search_term))
    FROM requirements r
    WHERE to_tsvector('english', r.title || ' ' || COALESCE(r.description, '')) @@ plainto_tsquery('english', search_term)
    AND r.is_deleted = FALSE
    AND 'requirement' = ANY(entity_types)
    
    UNION ALL
    
    SELECT 
        'test'::TEXT,
        t.id,
        t.name,
        COALESCE(t.description, ''),
        ts_rank(to_tsvector('english', t.name || ' ' || COALESCE(t.description, '')), plainto_tsquery('english', search_term))
    FROM tests t
    WHERE to_tsvector('english', t.name || ' ' || COALESCE(t.description, '')) @@ plainto_tsquery('english', search_term)
    AND t.is_deleted = FALSE
    AND 'test' = ANY(entity_types)
    
    UNION ALL
    
    SELECT 
        'document'::TEXT,
        d.id,
        d.title,
        COALESCE(d.content, ''),
        ts_rank(to_tsvector('english', d.title || ' ' || COALESCE(d.content, '')), plainto_tsquery('english', search_term))
    FROM documents d
    WHERE to_tsvector('english', d.title || ' ' || COALESCE(d.content, '')) @@ plainto_tsquery('english', search_term)
    AND d.is_deleted = FALSE
    AND 'document' = ANY(entity_types)
    
    ORDER BY rank DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
```

#### Vector Similarity Search

```sql
CREATE OR REPLACE FUNCTION search_similar_content(
    query_embedding VECTOR(1536),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    document_id UUID,
    title TEXT,
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.document_id,
        d.title,
        de.content,
        1 - (de.embedding <=> query_embedding) AS similarity
    FROM document_embeddings de
    JOIN documents d ON de.document_id = d.id
    WHERE d.is_deleted = FALSE
    AND 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
```

### Utility Functions

#### Get Entity Statistics

```sql
CREATE OR REPLACE FUNCTION get_entity_statistics(
    organization_id UUID
)
RETURNS TABLE (
    entity_type TEXT,
    total_count BIGINT,
    active_count BIGINT,
    completed_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'projects'::TEXT,
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'active'),
        COUNT(*) FILTER (WHERE status = 'completed')
    FROM projects p
    WHERE p.organization_id = get_entity_statistics.organization_id
    AND p.is_deleted = FALSE
    
    UNION ALL
    
    SELECT 
        'requirements'::TEXT,
        COUNT(*),
        COUNT(*) FILTER (WHERE status IN ('draft', 'review', 'approved')),
        COUNT(*) FILTER (WHERE status = 'completed')
    FROM requirements r
    JOIN projects p ON r.project_id = p.id
    WHERE p.organization_id = get_entity_statistics.organization_id
    AND r.is_deleted = FALSE
    
    UNION ALL
    
    SELECT 
        'tests'::TEXT,
        COUNT(*),
        COUNT(*) FILTER (WHERE status IN ('draft', 'ready')),
        COUNT(*) FILTER (WHERE status = 'passed')
    FROM tests t
    JOIN projects p ON t.project_id = p.id
    WHERE p.organization_id = get_entity_statistics.organization_id
    AND t.is_deleted = FALSE;
END;
$$ LANGUAGE plpgsql;
```

## API Response Schemas

### Standard Response Format

```python
class APIResponse(TypedDict):
    success: bool
    data: Any
    metadata: ResponseMetadata

class ResponseMetadata(TypedDict):
    timestamp: str
    execution_time_ms: float
    request_id: str
    pagination: PaginationInfo | None

class PaginationInfo(TypedDict):
    limit: int
    offset: int
    total: int
    has_more: bool
```

### Entity Response Schemas

```python
class EntityResponse(TypedDict):
    success: bool
    data: EntityData
    metadata: ResponseMetadata

class EntityData(TypedDict):
    id: str
    # ... entity-specific fields
    created_at: str
    updated_at: str

class EntityListResponse(TypedDict):
    success: bool
    data: List[EntityData]
    pagination: PaginationInfo
    metadata: ResponseMetadata
```

### Search Response Schemas

```python
class SearchResponse(TypedDict):
    success: bool
    data: SearchResults
    metadata: SearchMetadata

class SearchResults(TypedDict):
    query_type: str
    results: List[SearchResult]
    total_results: int

class SearchResult(TypedDict):
    entity_type: str
    entity_id: str
    title: str
    content: str
    similarity_score: float | None
    rank: float | None

class SearchMetadata(TypedDict):
    search_time_ms: float
    rag_mode: str | None
    similarity_threshold: float | None
    total_results: int
```

### Workflow Response Schemas

```python
class WorkflowResponse(TypedDict):
    success: bool
    data: WorkflowData
    metadata: ResponseMetadata

class WorkflowData(TypedDict):
    workflow: str
    status: str
    steps: List[WorkflowStep]
    summary: WorkflowSummary

class WorkflowStep(TypedDict):
    step: str
    status: str
    result: Any
    duration_ms: float | None

class WorkflowSummary(TypedDict):
    total_steps: int
    completed_steps: int
    failed_steps: int
    duration_ms: float
```

## Validation Schemas

### Input Validation

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any

class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    organization_id: str = Field(..., regex=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)
    start_date: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}-\d{2}$')
    end_date: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}-\d{2}$')
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v

class SearchRequest(BaseModel):
    query_type: str = Field(..., regex=r'^(search|aggregate|analyze|relationships|rag_search|similarity)$')
    entities: List[str] = Field(..., min_items=1)
    search_term: Optional[str] = Field(None, min_length=1, max_length=500)
    limit: int = Field(default=100, ge=1, le=1000)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    @validator('entities')
    def validate_entities(cls, v):
        valid_entities = {'organization', 'project', 'requirement', 'test', 'document', 'user'}
        for entity in v:
            if entity not in valid_entities:
                raise ValueError(f'Invalid entity type: {entity}')
        return v
```

## Migration Scripts

### Schema Versioning

```sql
-- Schema version tracking
CREATE TABLE schema_versions (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT,
    checksum TEXT
);

-- Insert initial version
INSERT INTO schema_versions (version, description) 
VALUES ('2024-01-01', 'Initial schema');
```

### Example Migration

```sql
-- Migration: Add vector search support
-- Version: 2024-01-15

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document embeddings table
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    model TEXT DEFAULT 'text-embedding-ada-002',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vector index
CREATE INDEX idx_document_embeddings_vector ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Update schema version
INSERT INTO schema_versions (version, description) 
VALUES ('2024-01-15', 'Added vector search support');
```

This schema reference provides a comprehensive guide to all data structures, types, and relationships used in the Atoms MCP system, ensuring consistency and type safety across the entire application.