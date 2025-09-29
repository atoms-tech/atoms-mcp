-- Progressive Vector RPC functions that handle records without embeddings
-- These functions will include records without embeddings and mark them for processing

-- Documents matcher with progressive embedding support
CREATE OR REPLACE FUNCTION public.match_documents_progressive(
  query_embedding vector(768),
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.7,
  filters jsonb DEFAULT NULL,
  include_non_embedded boolean DEFAULT true
)
RETURNS TABLE(
  id text,
  content text,
  metadata jsonb,
  similarity float,
  needs_embedding boolean
) LANGUAGE sql STABLE AS $$
  WITH embedded_results AS (
    -- Get results from records that have embeddings
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
      GREATEST(0, 1 - (d.embedding <=> query_embedding)) as similarity,
      false as needs_embedding
    FROM public.documents d
    WHERE d.embedding IS NOT NULL
      AND COALESCE(d.is_deleted, false) = false
      AND (
        filters IS NULL
        OR (
          (filters->>'project_id' IS NULL OR d.project_id = (filters->>'project_id'))
          AND (filters->>'type' IS NULL OR d.type = (filters->>'type'))
        )
      )
      AND GREATEST(0, 1 - (d.embedding <=> query_embedding)) >= similarity_threshold
  ),
  non_embedded_results AS (
    -- Get records without embeddings (marked for processing)
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
      0.5::float as similarity,  -- Default similarity for non-embedded
      true as needs_embedding
    FROM public.documents d
    WHERE include_non_embedded 
      AND d.embedding IS NULL
      AND COALESCE(d.is_deleted, false) = false
      AND COALESCE(d.content, d.description, d.name) IS NOT NULL
      AND (
        filters IS NULL
        OR (
          (filters->>'project_id' IS NULL OR d.project_id = (filters->>'project_id'))
          AND (filters->>'type' IS NULL OR d.type = (filters->>'type'))
        )
      )
    ORDER BY d.updated_at DESC
    LIMIT GREATEST(match_count / 4, 5)  -- Include some non-embedded results
  ),
  combined AS (
    SELECT * FROM embedded_results
    UNION ALL
    SELECT * FROM non_embedded_results
  )
  SELECT id, content, metadata, similarity, needs_embedding
  FROM combined
  ORDER BY similarity DESC, needs_embedding ASC  -- Prioritize embedded results
  LIMIT GREATEST(match_count, 1);
$$;

-- Requirements matcher with progressive embedding support
CREATE OR REPLACE FUNCTION public.match_requirements_progressive(
  query_embedding vector(768),
  match_count int DEFAULT 10,
  similarity_threshold float DEFAULT 0.7,
  filters jsonb DEFAULT NULL,
  include_non_embedded boolean DEFAULT true
)
RETURNS TABLE(
  id text,
  content text,
  metadata jsonb,
  similarity float,
  needs_embedding boolean
) LANGUAGE sql STABLE AS $$
  WITH embedded_results AS (
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
      GREATEST(0, 1 - (r.embedding <=> query_embedding)) as similarity,
      false as needs_embedding
    FROM public.requirements r
    WHERE r.embedding IS NOT NULL
      AND COALESCE(r.is_deleted, false) = false
      AND (
        filters IS NULL
        OR (
          (filters->>'document_id' IS NULL OR r.document_id = (filters->>'document_id'))
          AND (filters->>'status' IS NULL OR r.status = (filters->>'status'))
          AND (filters->>'priority' IS NULL OR r.priority = (filters->>'priority'))
        )
      )
      AND GREATEST(0, 1 - (r.embedding <=> query_embedding)) >= similarity_threshold
  ),
  non_embedded_results AS (
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
      0.5::float as similarity,
      true as needs_embedding
    FROM public.requirements r
    WHERE include_non_embedded 
      AND r.embedding IS NULL
      AND COALESCE(r.is_deleted, false) = false
      AND COALESCE(r.content, r.description, r.name) IS NOT NULL
      AND (
        filters IS NULL
        OR (
          (filters->>'document_id' IS NULL OR r.document_id = (filters->>'document_id'))
          AND (filters->>'status' IS NULL OR r.status = (filters->>'status'))
          AND (filters->>'priority' IS NULL OR r.priority = (filters->>'priority'))
        )
      )
    ORDER BY r.updated_at DESC
    LIMIT GREATEST(match_count / 4, 5)
  ),
  combined AS (
    SELECT * FROM embedded_results
    UNION ALL
    SELECT * FROM non_embedded_results
  )
  SELECT id, content, metadata, similarity, needs_embedding
  FROM combined
  ORDER BY similarity DESC, needs_embedding ASC
  LIMIT GREATEST(match_count, 1);
$$;

-- Helper function to get embedding coverage stats
CREATE OR REPLACE FUNCTION public.get_embedding_coverage(
  table_name text DEFAULT NULL
)
RETURNS TABLE(
  entity_type text,
  total_records bigint,
  embedded_records bigint,
  missing_embeddings bigint,
  coverage_percentage numeric
) LANGUAGE sql STABLE AS $$
  WITH table_stats AS (
    SELECT 
      'documents' as table_name,
      COUNT(*) as total,
      COUNT(embedding) as embedded
    FROM public.documents 
    WHERE COALESCE(is_deleted, false) = false
    
    UNION ALL
    
    SELECT 
      'requirements' as table_name,
      COUNT(*) as total,
      COUNT(embedding) as embedded
    FROM public.requirements 
    WHERE COALESCE(is_deleted, false) = false
    
    UNION ALL
    
    SELECT 
      'test_req' as table_name,
      COUNT(*) as total,
      COUNT(embedding) as embedded
    FROM public.test_req 
    WHERE COALESCE(is_deleted, false) = false
    
    UNION ALL
    
    SELECT 
      'projects' as table_name,
      COUNT(*) as total,
      COUNT(embedding) as embedded
    FROM public.projects 
    WHERE COALESCE(is_deleted, false) = false
    
    UNION ALL
    
    SELECT 
      'organizations' as table_name,
      COUNT(*) as total,
      COUNT(embedding) as embedded
    FROM public.organizations 
    WHERE COALESCE(is_deleted, false) = false
  )
  SELECT 
    s.table_name::text as entity_type,
    s.total as total_records,
    s.embedded as embedded_records,
    (s.total - s.embedded) as missing_embeddings,
    CASE 
      WHEN s.total > 0 THEN ROUND((s.embedded::numeric / s.total::numeric) * 100, 2)
      ELSE 0
    END as coverage_percentage
  FROM table_stats s
  WHERE table_name IS NULL OR s.table_name = get_embedding_coverage.table_name
  ORDER BY s.table_name;
$$;

-- Function to mark records for embedding generation
CREATE OR REPLACE FUNCTION public.queue_embedding_generation(
  entity_type text,
  record_ids text[] DEFAULT NULL,
  limit_count int DEFAULT 50
)
RETURNS TABLE(
  queued_count int,
  record_ids_queued text[]
) LANGUAGE plpgsql AS $$
DECLARE
  target_table text;
  query_text text;
  queued_ids text[];
  result_count int;
BEGIN
  -- Map entity type to table name
  target_table := CASE entity_type
    WHEN 'document' THEN 'documents'
    WHEN 'requirement' THEN 'requirements'
    WHEN 'test' THEN 'test_req'
    WHEN 'project' THEN 'projects'
    WHEN 'organization' THEN 'organizations'
    ELSE NULL
  END;
  
  IF target_table IS NULL THEN
    RAISE EXCEPTION 'Invalid entity type: %', entity_type;
  END IF;
  
  -- Build query to get records needing embeddings
  IF record_ids IS NOT NULL THEN
    -- Specific records
    query_text := format(
      'SELECT array_agg(id) FROM %I WHERE id = ANY($1) AND embedding IS NULL AND COALESCE(is_deleted, false) = false',
      target_table
    );
    EXECUTE query_text USING record_ids INTO queued_ids;
  ELSE
    -- Recent records without embeddings
    query_text := format(
      'SELECT array_agg(id) FROM (SELECT id FROM %I WHERE embedding IS NULL AND COALESCE(is_deleted, false) = false ORDER BY updated_at DESC LIMIT $1) t',
      target_table
    );
    EXECUTE query_text USING limit_count INTO queued_ids;
  END IF;
  
  queued_ids := COALESCE(queued_ids, ARRAY[]::text[]);
  result_count := array_length(queued_ids, 1);
  result_count := COALESCE(result_count, 0);
  
  RETURN QUERY SELECT result_count, queued_ids;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.match_documents_progressive(vector, int, float, jsonb, boolean) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_requirements_progressive(vector, int, float, jsonb, boolean) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_embedding_coverage(text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.queue_embedding_generation(text, text[], int) TO anon, authenticated;