-- Minimal version: Auto-add creator as organization owner
-- Run check_org_members_table.sql first to verify table structure

-- Create function
CREATE OR REPLACE FUNCTION auto_add_org_owner()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Minimal insert - adjust columns based on actual table structure
    INSERT INTO organization_members (
        organization_id,
        user_id,
        role,
        status
    ) VALUES (
        NEW.id,
        NEW.created_by,
        'owner',
        'active'
    )
    ON CONFLICT (organization_id, user_id) DO NOTHING;

    RETURN NEW;
END;
$$;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_auto_add_org_owner ON organizations;
CREATE TRIGGER trigger_auto_add_org_owner
    AFTER INSERT ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION auto_add_org_owner();
