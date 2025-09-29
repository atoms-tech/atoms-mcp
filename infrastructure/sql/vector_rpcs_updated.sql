-- Updated Supabase pgvector RPC functions for existing table structure
-- This assumes the tables already exist with an 'embedding' column of type vector(768)
-- Compatible with Vertex AI gemini-embeddings-001 (768 dimensions)

-- Enable extension (run once per database if not already enabled)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- First, ensure the embedding column exists in your tables
-- If not, add it with: ALTER TABLE table_name ADD COLUMN embedding vector(768);

-- Documents matcher - matches documents table
CREATE OR REPLACE FUNCTION public.match_documents(
  query_embedding vector(768),
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.7,
  filters jsonb DEFAULT NULL
)
RETURNS TABLE(
  id text,
  content text,
  metadata jsonb,
  similarity float
) LANGUAGE sql STABLE AS $$
  WITH base AS (
    SELECT 
      d.id::text,
      COALESCE(d.content, d.description, d.name)::text as content,
      jsonb_build_object(
        'name', d.name,
        'description', d.description,
        'project_id', d.project_id,
        'type', d.type,
        'created_at', d.created_at
      ) as metadata,
      -- Convert cosine distance to similarity in [0,1]
      GREATEST(0, 1 - (d.embedding <=> query_embedding)) as similarity
    FROM public.documents d
    WHERE d.embedding IS NOT NULL
      AND COALESCE(d.is_deleted, false) = false
  ),
  filtered AS (
    SELECT * FROM base
    WHERE (
      filters IS NULL
      OR (
        (filters->>'project_id' IS NULL OR (metadata->>'project_id') = (filters->>'project_id'))
        AND (filters->>'type' IS NULL OR (metadata->>'type') = (filters->>'type'))
      )
    )
  )
  SELECT id, content, metadata, similarity
  FROM filtered
  WHERE similarity >= similarity_threshold
  ORDER BY similarity DESC
  LIMIT GREATEST(match_count, 1);
$$;

-- Requirements matcher - matches requirements table  
CREATE OR REPLACE FUNCTION public.match_requirements(
  query_embedding vector(768),
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.7,
  filters jsonb DEFAULT NULL
)
RETURNS TABLE(
  id text,
  content text,
  metadata jsonb,
  similarity float
) LANGUAGE sql STABLE AS $$
  WITH base AS (
    SELECT 
      r.id::text,
      COALESCE(r.content, r.description, r.name)::text as content,
      jsonb_build_object(
        'name', r.name,
        'description', r.description,
        'document_id', r.document_id,
        'status', r.status,
        'priority', r.priority,
        'created_at', r.created_at
      ) as metadata,
      GREATEST(0, 1 - (r.embedding <=> query_embedding)) as similarity
    FROM public.requirements r
    WHERE r.embedding IS NOT NULL
      AND COALESCE(r.is_deleted, false) = false
  ),
  filtered AS (
    SELECT * FROM base
    WHERE (
      filters IS NULL
      OR (
        (filters->>'document_id' IS NULL OR (metadata->>'document_id') = (filters->>'document_id'))
        AND (filters->>'status' IS NULL OR (metadata->>'status') = (filters->>'status'))
        AND (filters->>'priority' IS NULL OR (metadata->>'priority') = (filters->>'priority'))
      )
    )
  )
  SELECT id, content, metadata, similarity
  FROM filtered
  WHERE similarity >= similarity_threshold
  ORDER BY similarity DESC
  LIMIT GREATEST(match_count, 1);
$$;

-- Tests matcher - matches test_req table (based on tools/base.py mapping)
CREATE OR REPLACE FUNCTION public.match_tests(
  query_embedding vector(768),
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.7,
  filters jsonb DEFAULT NULL
)
RETURNS TABLE(
  id text,
  content text,
  metadata jsonb,
  similarity float
) LANGUAGE sql STABLE AS $$
  WITH base AS (
    SELECT 
      t.id::text,
      COALESCE(t.content, t.description, t.name)::text as content,
      jsonb_build_object(
        'name', t.name,
        'description', t.description,
        'status', t.status,
        'created_at', t.created_at
      ) as metadata,
      GREATEST(0, 1 - (t.embedding <=> query_embedding)) as similarity
    FROM public.test_req t
    WHERE t.embedding IS NOT NULL
      AND COALESCE(t.is_deleted, false) = false
  ),
  filtered AS (
    SELECT * FROM base
    WHERE (
      filters IS NULL
      OR (
        (filters->>'status' IS NULL OR (metadata->>'status') = (filters->>'status'))
      )
    )
  )
  SELECT id, content, metadata, similarity
  FROM filtered
  WHERE similarity >= similarity_threshold
  ORDER BY similarity DESC
  LIMIT GREATEST(match_count, 1);
$$;

-- Projects matcher
CREATE OR REPLACE FUNCTION public.match_projects(
  query_embedding vector(768),
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.7,
  filters jsonb DEFAULT NULL
)
RETURNS TABLE(
  id text,
  content text,
  metadata jsonb,
  similarity float
) LANGUAGE sql STABLE AS $$
  WITH base AS (
    SELECT 
      p.id::text,
      COALESCE(p.description, p.name)::text as content,
      jsonb_build_object(
        'name', p.name,
        'description', p.description,
        'organization_id', p.organization_id,
        'status', p.status,
        'created_at', p.created_at
      ) as metadata,
      GREATEST(0, 1 - (p.embedding <=> query_embedding)) as similarity
    FROM public.projects p
    WHERE p.embedding IS NOT NULL
      AND COALESCE(p.is_deleted, false) = false
  ),
  filtered AS (
    SELECT * FROM base
    WHERE (
      filters IS NULL
      OR (
        (filters->>'organization_id' IS NULL OR (metadata->>'organization_id') = (filters->>'organization_id'))
        AND (filters->>'status' IS NULL OR (metadata->>'status') = (filters->>'status'))
      )
    )
  )
  SELECT id, content, metadata, similarity
  FROM filtered
  WHERE similarity >= similarity_threshold
  ORDER BY similarity DESC
  LIMIT GREATEST(match_count, 1);
$$;

-- Organizations matcher
CREATE OR REPLACE FUNCTION public.match_organizations(
  query_embedding vector(768),
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.7,
  filters jsonb DEFAULT NULL
)
RETURNS TABLE(
  id text,
  content text,
  metadata jsonb,
  similarity float
) LANGUAGE sql STABLE AS $$
  WITH base AS (
    SELECT 
      o.id::text,
      COALESCE(o.description, o.name)::text as content,
      jsonb_build_object(
        'name', o.name,
        'description', o.description,
        'type', o.type,
        'created_at', o.created_at
      ) as metadata,
      GREATEST(0, 1 - (o.embedding <=> query_embedding)) as similarity
    FROM public.organizations o
    WHERE o.embedding IS NOT NULL
      AND COALESCE(o.is_deleted, false) = false
  ),
  filtered AS (
    SELECT * FROM base
    WHERE (
      filters IS NULL
      OR (
        (filters->>'type' IS NULL OR (metadata->>'type') = (filters->>'type'))
      )
    )
  )
  SELECT id, content, metadata, similarity
  FROM filtered
  WHERE similarity >= similarity_threshold
  ORDER BY similarity DESC
  LIMIT GREATEST(match_count, 1);
$$;

-- Permissions for functions
-- Grant execute permissions to your user roles
GRANT EXECUTE ON FUNCTION public.match_documents(vector, int, float, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_requirements(vector, int, float, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_tests(vector, int, float, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_projects(vector, int, float, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_organizations(vector, int, float, jsonb) TO anon, authenticated;

-- Index creation for optimal performance
-- Create indexes on the embedding columns if they don't exist
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS documents_embedding_idx ON public.documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS requirements_embedding_idx ON public.requirements USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS test_req_embedding_idx ON public.test_req USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS projects_embedding_idx ON public.projects USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS organizations_embedding_idx ON public.organizations USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);