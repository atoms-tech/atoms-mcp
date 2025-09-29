-- Add embedding columns to existing tables for vector search
-- This is safe to run multiple times - will only add columns if they don't exist

-- Enable pgvector extension (run once per database)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding columns to tables (using 768 dimensions for Vertex AI gemini-embeddings-001)
-- These will be NULL initially and populated by the backfill script

-- Documents table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'documents' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE public.documents ADD COLUMN embedding vector(768);
        COMMENT ON COLUMN public.documents.embedding IS 'Vector embedding for semantic search (Vertex AI gemini-embeddings-001)';
    END IF;
END $$;

-- Requirements table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'requirements' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE public.requirements ADD COLUMN embedding vector(768);
        COMMENT ON COLUMN public.requirements.embedding IS 'Vector embedding for semantic search (Vertex AI gemini-embeddings-001)';
    END IF;
END $$;

-- Test_req table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'test_req' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE public.test_req ADD COLUMN embedding vector(768);
        COMMENT ON COLUMN public.test_req.embedding IS 'Vector embedding for semantic search (Vertex AI gemini-embeddings-001)';
    END IF;
END $$;

-- Projects table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'projects' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE public.projects ADD COLUMN embedding vector(768);
        COMMENT ON COLUMN public.projects.embedding IS 'Vector embedding for semantic search (Vertex AI gemini-embeddings-001)';
    END IF;
END $$;

-- Organizations table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'organizations' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE public.organizations ADD COLUMN embedding vector(768);
        COMMENT ON COLUMN public.organizations.embedding IS 'Vector embedding for semantic search (Vertex AI gemini-embeddings-001)';
    END IF;
END $$;

-- Create indexes for better performance (these will be created even if data exists)
-- Using CONCURRENTLY to avoid locking tables in production
CREATE INDEX CONCURRENTLY IF NOT EXISTS documents_embedding_idx 
ON public.documents USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX CONCURRENTLY IF NOT EXISTS requirements_embedding_idx 
ON public.requirements USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX CONCURRENTLY IF NOT EXISTS test_req_embedding_idx 
ON public.test_req USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX CONCURRENTLY IF NOT EXISTS projects_embedding_idx 
ON public.projects USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX CONCURRENTLY IF NOT EXISTS organizations_embedding_idx 
ON public.organizations USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Show which tables now have embedding columns
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND column_name = 'embedding'
  AND table_name IN ('documents', 'requirements', 'test_req', 'projects', 'organizations')
ORDER BY table_name;