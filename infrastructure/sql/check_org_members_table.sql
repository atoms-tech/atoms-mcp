-- Check if organization_members table exists and its structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'organization_members'
ORDER BY ordinal_position;
