-- Working Vector RPC functions (without problematic test_req table)
-- Copy and paste this into your Supabase SQL Editor

-- Enable pgvector extension (run once)
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents matcher
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
  SELECT 
    d.id::text,
    COALESCE(d.description, d.name, 'No content')::text as content,
    jsonb_build_object(
      'name', d.name,
      'description', d.description,
      'project_id', d.project_id,
      'created_at', d.created_at
    ) as metadata,
    GREATEST(0, 1 - (d.embedding <=> query_embedding)) as similarity
  FROM public.documents d
  WHERE d.embedding IS NOT NULL
    AND COALESCE(d.is_deleted, false) = false
    AND GREATEST(0, 1 - (d.embedding <=> query_embedding)) >= similarity_threshold
    AND (
      filters IS NULL
      OR (
        (filters->>'project_id' IS NULL OR d.project_id::text = (filters->>'project_id'))
      )
    )
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
  SELECT 
    p.id::text,
    COALESCE(p.description, p.name, 'No content')::text as content,
    jsonb_build_object(
      'name', p.name,
      'description', p.description,
      'organization_id', p.organization_id,
      'status', p.status::text,
      'visibility', p.visibility::text,
      'created_at', p.created_at
    ) as metadata,
    GREATEST(0, 1 - (p.embedding <=> query_embedding)) as similarity
  FROM public.projects p
  WHERE p.embedding IS NOT NULL
    AND COALESCE(p.is_deleted, false) = false
    AND GREATEST(0, 1 - (p.embedding <=> query_embedding)) >= similarity_threshold
    AND (
      filters IS NULL
      OR (
        (filters->>'organization_id' IS NULL OR p.organization_id::text = (filters->>'organization_id'))
      )
    )
  ORDER BY similarity DESC
  LIMIT GREATEST(match_count, 1);
$$;

-- Requirements matcher
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
  SELECT 
    r.id::text,
    COALESCE(r.description, r.name, 'No content')::text as content,
    jsonb_build_object(
      'name', r.name,
      'description', r.description,
      'document_id', r.document_id,
      'status', r.status::text,
      'priority', r.priority::text,
      'created_at', r.created_at
    ) as metadata,
    GREATEST(0, 1 - (r.embedding <=> query_embedding)) as similarity
  FROM public.requirements r
  WHERE r.embedding IS NOT NULL
    AND COALESCE(r.is_deleted, false) = false
    AND GREATEST(0, 1 - (r.embedding <=> query_embedding)) >= similarity_threshold
    AND (
      filters IS NULL
      OR (
        (filters->>'document_id' IS NULL OR r.document_id::text = (filters->>'document_id'))
      )
    )
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
  SELECT 
    o.id::text,
    COALESCE(o.description, o.name, 'No content')::text as content,
    jsonb_build_object(
      'name', o.name,
      'description', o.description,
      'type', o.type::text,
      'status', o.status::text,
      'created_at', o.created_at
    ) as metadata,
    GREATEST(0, 1 - (o.embedding <=> query_embedding)) as similarity
  FROM public.organizations o
  WHERE o.embedding IS NOT NULL
    AND COALESCE(o.is_deleted, false) = false
    AND GREATEST(0, 1 - (o.embedding <=> query_embedding)) >= similarity_threshold
  ORDER BY similarity DESC
  LIMIT GREATEST(match_count, 1);
$$;

-- Dummy tests matcher (returns empty results to avoid errors)
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
  -- Return empty result set for now since test_req table has permission issues
  SELECT 
    ''::text as id,
    ''::text as content,
    '{}'::jsonb as metadata,
    0.0::float as similarity
  WHERE false;  -- This ensures no rows are returned
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.match_documents(vector, int, float, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_projects(vector, int, float, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_requirements(vector, int, float, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_organizations(vector, int, float, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_tests(vector, int, float, jsonb) TO anon, authenticated;

-- Test the functions (uncomment to test after deployment)
-- SELECT 'Documents function works' WHERE EXISTS (SELECT 1 FROM match_documents(array_fill(0, ARRAY[768])::vector(768), 1, 0.0, null));
-- SELECT 'Projects function works' WHERE EXISTS (SELECT 1 FROM match_projects(array_fill(0, ARRAY[768])::vector(768), 1, 0.0, null));

-- Optional: Create indexes for optimal performance (run after more embeddings are generated)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS documents_embedding_idx ON public.documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS projects_embedding_idx ON public.projects USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS requirements_embedding_idx ON public.requirements USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS organizations_embedding_idx ON public.organizations USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);