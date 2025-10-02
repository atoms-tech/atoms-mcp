-- Auto-add creator as organization owner when org is created
-- This ensures RLS policies work correctly for project creation

-- Function to add creator as organization owner
CREATE OR REPLACE FUNCTION auto_add_org_owner()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
    -- Insert creator as owner in organization_members
    INSERT INTO organization_members (
        organization_id,
        user_id,
        role,
        status,
        is_deleted,
        created_by,
        updated_by
    ) VALUES (
        NEW.id,
        NEW.created_by,
        'owner',
        'active',
        false,
        NEW.created_by,
        NEW.created_by
    )
    ON CONFLICT (organization_id, user_id)
    DO UPDATE SET
        role = EXCLUDED.role,
        status = 'active',
        is_deleted = false,
        updated_at = now(),
        updated_by = EXCLUDED.updated_by;

    RETURN NEW;
END;
$$;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trigger_auto_add_org_owner ON organizations;

-- Create trigger
CREATE TRIGGER trigger_auto_add_org_owner
    AFTER INSERT ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION auto_add_org_owner();

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION auto_add_org_owner() TO authenticated;

-- Verify the trigger was created
SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_name = 'trigger_auto_add_org_owner';
