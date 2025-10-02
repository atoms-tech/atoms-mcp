-- Auto-add creator as organization owner when org is created
-- CORRECTED VERSION - matches actual organization_members table structure

-- Drop existing trigger and function if they exist
DROP TRIGGER IF EXISTS trigger_auto_add_org_owner ON organizations;
DROP FUNCTION IF EXISTS auto_add_org_owner();

-- Create function to add creator as organization owner
CREATE FUNCTION auto_add_org_owner()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Insert creator as owner in organization_members
    -- Using actual columns from the table (no created_by, only updated_by)
    INSERT INTO organization_members (
        organization_id,
        user_id,
        role,
        status,
        is_deleted,
        updated_by
    ) VALUES (
        NEW.id,
        NEW.created_by,
        'owner'::user_role_type,
        'active'::user_status,
        false,
        NEW.created_by
    )
    ON CONFLICT (organization_id, user_id)
    DO UPDATE SET
        role = 'owner'::user_role_type,
        status = 'active'::user_status,
        is_deleted = false,
        updated_at = timezone('utc'::text, now()),
        updated_by = EXCLUDED.updated_by;

    RETURN NEW;
END;
$$;

-- Create trigger
CREATE TRIGGER trigger_auto_add_org_owner
    AFTER INSERT ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION auto_add_org_owner();

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION auto_add_org_owner() TO authenticated;
