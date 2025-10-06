-- Create Row Level Security (RLS) policies for mcp_sessions table
-- This ensures users can only access their own sessions

-- Enable RLS on the table
ALTER TABLE mcp_sessions ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (idempotent)
DROP POLICY IF EXISTS "Users can view own sessions" ON mcp_sessions;
DROP POLICY IF EXISTS "Users can create own sessions" ON mcp_sessions;
DROP POLICY IF EXISTS "Users can update own sessions" ON mcp_sessions;
DROP POLICY IF EXISTS "Users can delete own sessions" ON mcp_sessions;
DROP POLICY IF EXISTS "Service role has full access" ON mcp_sessions;
DROP POLICY IF EXISTS "Allow anonymous session creation" ON mcp_sessions;

-- Policy 1: Users can view their own sessions
CREATE POLICY "Users can view own sessions"
    ON mcp_sessions
    FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid()
        AND expires_at > NOW()  -- Only show active sessions
    );

-- Policy 2: Users can create sessions for themselves
-- Note: This is used when OAuth completes and creates a session
CREATE POLICY "Users can create own sessions"
    ON mcp_sessions
    FOR INSERT
    TO authenticated
    WITH CHECK (
        user_id = auth.uid()
        AND expires_at > NOW()
    );

-- Policy 3: Users can update their own active sessions
CREATE POLICY "Users can update own sessions"
    ON mcp_sessions
    FOR UPDATE
    TO authenticated
    USING (
        user_id = auth.uid()
        AND expires_at > NOW()
    )
    WITH CHECK (
        user_id = auth.uid()
        AND expires_at > NOW()
    );

-- Policy 4: Users can delete their own sessions (logout)
CREATE POLICY "Users can delete own sessions"
    ON mcp_sessions
    FOR DELETE
    TO authenticated
    USING (
        user_id = auth.uid()
    );

-- Policy 5: Service role has full access (for admin operations)
-- This is used by SessionManager when using service role key
CREATE POLICY "Service role has full access"
    ON mcp_sessions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy 6: Allow anonymous users to create sessions
-- This is needed for the OAuth flow before the user is authenticated
-- The session will be created with the user_id from OAuth response
CREATE POLICY "Allow anonymous session creation"
    ON mcp_sessions
    FOR INSERT
    TO anon
    WITH CHECK (
        session_id IS NOT NULL
        AND user_id IS NOT NULL
        AND oauth_data IS NOT NULL
        AND expires_at > NOW()
    );

-- Create a function to verify session ownership via custom JWT claim
-- This is used when AuthKit JWTs are used instead of Supabase JWTs
CREATE OR REPLACE FUNCTION verify_session_ownership(p_session_id TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    session_user_id UUID;
    current_user_id UUID;
BEGIN
    -- Get the user_id from the session
    SELECT user_id INTO session_user_id
    FROM mcp_sessions
    WHERE session_id = p_session_id;

    -- Get current user from auth context
    current_user_id := auth.uid();

    -- Return true if they match
    RETURN session_user_id = current_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION verify_session_ownership(TEXT) TO authenticated, anon;

-- Create view for active sessions only (optional, for convenience)
CREATE OR REPLACE VIEW active_mcp_sessions AS
SELECT
    session_id,
    user_id,
    oauth_data,
    mcp_state,
    created_at,
    updated_at,
    expires_at,
    (expires_at - NOW()) AS time_remaining
FROM mcp_sessions
WHERE expires_at > NOW()
ORDER BY created_at DESC;

-- Grant access to the view
GRANT SELECT ON active_mcp_sessions TO authenticated;
GRANT SELECT ON active_mcp_sessions TO service_role;

-- Add comments for documentation
COMMENT ON POLICY "Users can view own sessions" ON mcp_sessions IS
    'Users can only view their own active sessions';

COMMENT ON POLICY "Users can create own sessions" ON mcp_sessions IS
    'Users can create sessions for themselves via OAuth flow';

COMMENT ON POLICY "Users can update own sessions" ON mcp_sessions IS
    'Users can update their own active sessions (e.g., extend expiry, update MCP state)';

COMMENT ON POLICY "Users can delete own sessions" ON mcp_sessions IS
    'Users can delete their own sessions (logout functionality)';

COMMENT ON POLICY "Service role has full access" ON mcp_sessions IS
    'Service role has full CRUD access for admin operations and cleanup';

COMMENT ON POLICY "Allow anonymous session creation" ON mcp_sessions IS
    'Allow OAuth flow to create sessions before user authentication';

COMMENT ON FUNCTION verify_session_ownership(TEXT) IS
    'Verify that the current user owns the specified session';

COMMENT ON VIEW active_mcp_sessions IS
    'View showing only active (non-expired) sessions with time remaining';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'RLS policies created successfully for mcp_sessions!';
    RAISE NOTICE 'Security features enabled:';
    RAISE NOTICE '  ✓ Users can only access their own sessions';
    RAISE NOTICE '  ✓ Service role has full access for admin operations';
    RAISE NOTICE '  ✓ Anonymous users can create sessions via OAuth flow';
    RAISE NOTICE '  ✓ Expired sessions are hidden from users';
    RAISE NOTICE '  ✓ Helper function verify_session_ownership() available';
    RAISE NOTICE 'Next: Run test_session_operations.sql to verify functionality';
END $$;
