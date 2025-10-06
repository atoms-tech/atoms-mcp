-- Create mcp_sessions table for persistent OAuth session storage
-- This enables stateless serverless MCP deployments

-- Drop table if exists (be careful in production!)
-- DROP TABLE IF EXISTS mcp_sessions CASCADE;

-- Create table
CREATE TABLE IF NOT EXISTS mcp_sessions (
    -- Unique session identifier (UUID format recommended)
    session_id TEXT PRIMARY KEY,

    -- User identifier from OAuth/Supabase auth
    user_id UUID NOT NULL,

    -- OAuth tokens and user information
    -- Structure: {
    --   "access_token": "...",
    --   "refresh_token": "...",
    --   "expires_in": 3600,
    --   "token_type": "Bearer",
    --   "user": {"id": "...", "email": "..."}
    -- }
    oauth_data JSONB NOT NULL,

    -- MCP connection state (for stateful tool operations)
    -- Can store workspace context, last query, etc.
    mcp_state JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Session expiry (auto-cleanup after this time)
    expires_at TIMESTAMPTZ NOT NULL,

    -- Constraints
    CONSTRAINT valid_session_id CHECK (length(session_id) > 0),
    CONSTRAINT valid_oauth_data CHECK (jsonb_typeof(oauth_data) = 'object'),
    CONSTRAINT valid_mcp_state CHECK (jsonb_typeof(mcp_state) = 'object'),
    CONSTRAINT expires_after_creation CHECK (expires_at > created_at)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_user_id
    ON mcp_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_mcp_sessions_expires_at
    ON mcp_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_mcp_sessions_created_at
    ON mcp_sessions(created_at DESC);

-- Create partial index for active sessions only (performance optimization)
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_active
    ON mcp_sessions(user_id, expires_at)
    WHERE expires_at > NOW();

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_mcp_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mcp_sessions_updated_at
    BEFORE UPDATE ON mcp_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_mcp_sessions_updated_at();

-- Create function for automatic cleanup of expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_mcp_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM mcp_sessions
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust based on your setup)
-- For public access with RLS:
GRANT SELECT, INSERT, UPDATE, DELETE ON mcp_sessions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON mcp_sessions TO anon;

-- For service role full access:
GRANT ALL ON mcp_sessions TO service_role;

-- Add comments for documentation
COMMENT ON TABLE mcp_sessions IS 'Persistent OAuth session storage for stateless MCP server deployments';
COMMENT ON COLUMN mcp_sessions.session_id IS 'Unique session identifier (UUID format)';
COMMENT ON COLUMN mcp_sessions.user_id IS 'Supabase/OAuth user identifier';
COMMENT ON COLUMN mcp_sessions.oauth_data IS 'OAuth tokens and user info (encrypted at rest by Supabase)';
COMMENT ON COLUMN mcp_sessions.mcp_state IS 'MCP connection state for stateful operations';
COMMENT ON COLUMN mcp_sessions.expires_at IS 'Session expiry timestamp for automatic cleanup';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'mcp_sessions table created successfully!';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Run create_session_rls_policies.sql to add security policies';
    RAISE NOTICE '2. Run test_session_operations.sql to verify functionality';
    RAISE NOTICE '3. Configure MCP_SESSION_TTL_HOURS environment variable';
END $$;
