-- Test session operations for mcp_sessions table
-- Run this to verify CRUD operations work correctly

-- Test 1: Insert a test session
DO $$
DECLARE
    test_session_id TEXT := 'test-' || gen_random_uuid()::TEXT;
    test_user_id UUID := gen_random_uuid();
BEGIN
    RAISE NOTICE '=== Test 1: Creating test session ===';

    INSERT INTO mcp_sessions (
        session_id,
        user_id,
        oauth_data,
        mcp_state,
        expires_at
    ) VALUES (
        test_session_id,
        test_user_id,
        jsonb_build_object(
            'access_token', 'test_token_123',
            'token_type', 'Bearer',
            'expires_in', 3600,
            'user', jsonb_build_object(
                'id', test_user_id,
                'email', 'test@example.com'
            )
        ),
        jsonb_build_object('workspace_id', 'test-workspace'),
        NOW() + INTERVAL '24 hours'
    );

    RAISE NOTICE 'Created session: %', test_session_id;
    RAISE NOTICE 'User ID: %', test_user_id;
END $$;

-- Test 2: Query active sessions
SELECT
    session_id,
    user_id,
    oauth_data->>'access_token' AS access_token,
    mcp_state,
    created_at,
    expires_at,
    expires_at - NOW() AS time_remaining
FROM mcp_sessions
WHERE session_id LIKE 'test-%'
ORDER BY created_at DESC
LIMIT 5;

-- Test 3: Update session (extend expiry and update MCP state)
DO $$
DECLARE
    test_session_id TEXT;
BEGIN
    RAISE NOTICE '=== Test 3: Updating session ===';

    -- Get the first test session
    SELECT session_id INTO test_session_id
    FROM mcp_sessions
    WHERE session_id LIKE 'test-%'
    ORDER BY created_at DESC
    LIMIT 1;

    IF test_session_id IS NOT NULL THEN
        UPDATE mcp_sessions
        SET
            expires_at = NOW() + INTERVAL '48 hours',
            mcp_state = mcp_state || jsonb_build_object(
                'last_activity', NOW(),
                'request_count', 1
            )
        WHERE session_id = test_session_id;

        RAISE NOTICE 'Updated session: %', test_session_id;
    ELSE
        RAISE NOTICE 'No test session found to update';
    END IF;
END $$;

-- Test 4: Verify updated session
SELECT
    session_id,
    mcp_state,
    expires_at,
    updated_at,
    expires_at - NOW() AS new_time_remaining
FROM mcp_sessions
WHERE session_id LIKE 'test-%'
ORDER BY created_at DESC
LIMIT 1;

-- Test 5: Test cleanup function
DO $$
DECLARE
    deleted_count INTEGER;
    expired_session_id TEXT := 'expired-' || gen_random_uuid()::TEXT;
BEGIN
    RAISE NOTICE '=== Test 5: Testing cleanup function ===';

    -- Create an expired session
    INSERT INTO mcp_sessions (
        session_id,
        user_id,
        oauth_data,
        expires_at
    ) VALUES (
        expired_session_id,
        gen_random_uuid(),
        '{"access_token": "expired"}'::jsonb,
        NOW() - INTERVAL '1 hour'  -- Already expired
    );

    RAISE NOTICE 'Created expired session: %', expired_session_id;

    -- Run cleanup
    SELECT cleanup_expired_mcp_sessions() INTO deleted_count;

    RAISE NOTICE 'Cleanup deleted % expired sessions', deleted_count;
END $$;

-- Test 6: Verify cleanup removed expired session
SELECT
    COUNT(*) FILTER (WHERE session_id LIKE 'expired-%') AS expired_sessions_remaining,
    COUNT(*) FILTER (WHERE session_id LIKE 'test-%') AS test_sessions_remaining
FROM mcp_sessions;

-- Test 7: Test active_mcp_sessions view
SELECT
    session_id,
    user_id,
    time_remaining,
    created_at
FROM active_mcp_sessions
WHERE session_id LIKE 'test-%'
ORDER BY created_at DESC;

-- Test 8: Test session ownership verification function
DO $$
DECLARE
    test_session_id TEXT;
    can_access BOOLEAN;
BEGIN
    RAISE NOTICE '=== Test 8: Testing session ownership ===';

    SELECT session_id INTO test_session_id
    FROM mcp_sessions
    WHERE session_id LIKE 'test-%'
    ORDER BY created_at DESC
    LIMIT 1;

    IF test_session_id IS NOT NULL THEN
        -- This will return false because we're not authenticated as the session's user
        SELECT verify_session_ownership(test_session_id) INTO can_access;
        RAISE NOTICE 'Session ownership check: %', can_access;
    END IF;
END $$;

-- Test 9: Performance test - create multiple sessions
DO $$
DECLARE
    i INTEGER;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    session_count INTEGER := 100;
BEGIN
    RAISE NOTICE '=== Test 9: Performance test ===';
    RAISE NOTICE 'Creating % sessions...', session_count;

    start_time := clock_timestamp();

    FOR i IN 1..session_count LOOP
        INSERT INTO mcp_sessions (
            session_id,
            user_id,
            oauth_data,
            expires_at
        ) VALUES (
            'perf-test-' || i || '-' || gen_random_uuid()::TEXT,
            gen_random_uuid(),
            jsonb_build_object('access_token', 'perf_test_' || i),
            NOW() + INTERVAL '24 hours'
        );
    END LOOP;

    end_time := clock_timestamp();

    RAISE NOTICE 'Created % sessions in % ms',
        session_count,
        EXTRACT(MILLISECONDS FROM (end_time - start_time));
END $$;

-- Test 10: Query performance with indexes
EXPLAIN ANALYZE
SELECT *
FROM mcp_sessions
WHERE user_id = (SELECT user_id FROM mcp_sessions LIMIT 1)
AND expires_at > NOW();

-- Cleanup: Remove all test sessions
DO $$
DECLARE
    deleted_count INTEGER;
BEGIN
    RAISE NOTICE '=== Cleanup: Removing test sessions ===';

    DELETE FROM mcp_sessions
    WHERE session_id LIKE 'test-%'
       OR session_id LIKE 'perf-test-%'
       OR session_id LIKE 'expired-%';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RAISE NOTICE 'Deleted % test sessions', deleted_count;
    RAISE NOTICE 'All tests complete!';
END $$;

-- Final summary
SELECT
    COUNT(*) AS total_sessions,
    COUNT(*) FILTER (WHERE expires_at > NOW()) AS active_sessions,
    COUNT(*) FILTER (WHERE expires_at <= NOW()) AS expired_sessions,
    pg_size_pretty(pg_total_relation_size('mcp_sessions'::regclass)) AS table_size
FROM mcp_sessions;
