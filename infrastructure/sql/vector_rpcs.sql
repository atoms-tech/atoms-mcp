-- Supabase pgvector RPC templates for semantic search
-- Requires the pgvector extension and an embedding column of type vector(N)

-- Enable extension (run once per database)
-- create extension if not exists vector;

-- Example: documents table assumed to have columns:
--   id text primary key
--   content text
--   metadata jsonb
--   is_deleted boolean default false
--   embedding vector(<DIM>)  -- set to the embedding dimension for your model

-- Helper: normalize similarity to 0..1 from cosine distance (<=>)
-- For normalized embeddings, cosine distance is in [0, 2].
-- Similarity = 1 - distance/2 gives a value in [0,1].

-- Documents matcher
create or replace function public.match_documents(
  query_embedding vector,
  match_count int,
  similarity_threshold float,
  filters jsonb default null
)
returns table(
  id text,
  content text,
  metadata jsonb,
  similarity float
) language sql stable as $$
  with base as (
    select d.id,
           d.content,
           d.metadata,
           -- Convert cosine distance to similarity in [0,1]
           (1 - (d.embedding <=> query_embedding) / 2) as similarity
    from public.documents d
    where coalesce(d.is_deleted, false) = false
  ),
  filtered as (
    -- Optional simple equality filters passed as JSONB, e.g., {"project_id": "..."}
    select * from base
    where (
      filters is null
      or (
        select bool_and((base_row->>key) is not distinct from (filters->>key))
        from jsonb_object_keys(coalesce(filters, '{}')) as key,
             jsonb_build_object(
               'project_id', (select to_jsonb(d.project_id) from public.documents d where d.id = base.id)
             ) as base_row
      )
    )
  )
  select id, content, metadata, similarity
  from filtered
  where similarity >= similarity_threshold
  order by similarity desc
  limit greatest(match_count, 1);
$$;

-- Requirements matcher (adjust table/columns as needed)
create or replace function public.match_requirements(
  query_embedding vector,
  match_count int,
  similarity_threshold float,
  filters jsonb default null
)
returns table(
  id text,
  content text,
  metadata jsonb,
  similarity float
) language sql stable as $$
  select r.id,
         coalesce(r.content, r.description)::text as content,
         r.metadata,
         (1 - (r.embedding <=> query_embedding) / 2) as similarity
  from public.requirements r
  where coalesce(r.is_deleted, false) = false
    and (filters is null or true) -- extend with specific filter handling if needed
  order by similarity desc
  limit greatest(match_count, 1);
$$;

-- Repeat similar functions for tests, projects, organizations as needed
-- create or replace function public.match_tests(...)
-- create or replace function public.match_projects(...)
-- create or replace function public.match_organizations(...)

-- Permissions
-- Consider SECURITY DEFINER with a dedicated role if RLS prevents access, e.g.:
-- alter function public.match_documents(vector, int, float, jsonb) owner to postgres;
-- revoke all on function public.match_documents(vector, int, float, jsonb) from public;
-- grant execute on function public.match_documents(vector, int, float, jsonb) to anon, authenticated;
