-- Check if mcp_sessions table exists and display its schema
-- Run this to verify the table structure before migration

-- Check if table exists
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE tablename = 'mcp_sessions';

-- Display table schema if it exists
SELECT
    column_name,
    data_type,
    character_maximum_length,
    column_default,
    is_nullable,
    udt_name
FROM information_schema.columns
WHERE table_name = 'mcp_sessions'
ORDER BY ordinal_position;

-- Check indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'mcp_sessions';

-- Check constraints
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'mcp_sessions'::regclass;

-- Check RLS policies
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'mcp_sessions';

-- Check table size and row count
SELECT
    pg_size_pretty(pg_total_relation_size('mcp_sessions'::regclass)) AS table_size,
    (SELECT count(*) FROM mcp_sessions) AS row_count;

-- Check for expired sessions that need cleanup
SELECT
    count(*) AS expired_sessions,
    count(*) FILTER (WHERE expires_at > NOW()) AS active_sessions
FROM mcp_sessions;
